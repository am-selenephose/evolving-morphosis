"""RED tests for the future-model evolution protocol."""
from __future__ import annotations

import dataclasses

import morphosis


def api(name: str):
    value = getattr(morphosis, name, None)
    assert value is not None, f"missing Morphosis v2 API: {name}"
    return value


def test_known_model_uses_preoptimized_fast_lane() -> None:
    registry_cls = api("KnownAdapterRegistry")
    bootstrap = api("bootstrap_candidate")
    registry = registry_cls({("aws-bedrock", "known-model"): "bedrock-converse"})
    identity = bootstrap("known-model", "aws-bedrock", "bedrock://known-model", registry)
    assert identity.lane == "KNOWN_FAST_PATH"
    assert identity.adapter == "bedrock-converse"


def test_unknown_future_model_needs_no_hardcoded_adapter() -> None:
    registry_cls = api("KnownAdapterRegistry")
    bootstrap = api("bootstrap_candidate")
    identity = bootstrap("future-model-x", "future-provider", "https://future.invalid/v1", registry_cls({}))
    assert identity.lane == "UNKNOWN_BOOTSTRAP"
    assert identity.adapter is None
    assert len(identity.candidate_fingerprint) == 64


def test_self_reported_novel_capability_starts_unverified() -> None:
    registry_cls = api("CapabilityRegistry")
    registry = registry_cls()
    updated = registry.register_claim("future.semantic_patch.v1", claimed_supported=True, source="candidate-self-report")
    record = updated.get("future.semantic_patch.v1")
    assert record.status == "UNKNOWN"
    assert record.proof_state == "UNVERIFIED"


def test_verified_probe_can_register_capability_not_in_original_schema() -> None:
    registry_cls = api("CapabilityRegistry")
    proposal_cls = api("ProbeProposal")
    verify = api("verify_probe_proposal")
    registry = registry_cls().register_claim("future.semantic_patch.v1", True, "candidate-self-report")
    proposal = proposal_cls(
        probe_id="semantic-patch-roundtrip",
        capability_id="future.semantic_patch.v1",
        kind="fixture_roundtrip",
        timeout_ms=1000,
        network_access=False,
        source_write=False,
    )
    result = verify(proposal, observed_output={"valid": True, "score": 0.97})
    updated = registry.apply_probe_result(result)
    record = updated.get("future.semantic_patch.v1")
    assert record.status == "SUPPORTED"
    assert record.proof_state == "OBSERVED"
    assert record.score == 0.97


def test_unsafe_candidate_probe_is_rejected_before_execution() -> None:
    proposal_cls = api("ProbeProposal")
    verify = api("verify_probe_proposal")
    proposal = proposal_cls(
        probe_id="bad-probe",
        capability_id="future.semantic_patch.v1",
        kind="fixture_roundtrip",
        timeout_ms=1000,
        network_access=True,
        source_write=True,
    )
    result = verify(proposal, observed_output={"valid": True, "score": 1.0})
    assert result.accepted is False
    assert result.status == "UNKNOWN"


def test_portable_fallback_is_labeled_adapted_not_native() -> None:
    compile_adaptation = api("compile_adaptation")
    plan = compile_adaptation(
        capability_id="structured_output",
        native_supported=False,
        fallback="prompted-json+validator",
    )
    assert plan.mode == "ADAPTED"
    assert plan.native is False
    assert plan.transforms == ("prompted-json+validator",)


def test_runtime_bundle_auto_apply_requires_rollback() -> None:
    change_cls = api("EvolutionChange")
    build_bundle = api("build_evolution_bundle")
    change = change_cls(kind="runtime", description="switch schema transform", rollback="restore:v12")
    bundle = build_bundle(
        candidate_fingerprint="a" * 64,
        parent_hash="b" * 64,
        changes=(change,),
        tests_passed=True,
        invariants_passed=True,
        recommendation="PROMOTE",
    )
    assert bundle.approval == "AUTO_APPLY"
    no_rollback = dataclasses.replace(change, rollback="")
    blocked = build_bundle(
        candidate_fingerprint="a" * 64,
        parent_hash="b" * 64,
        changes=(no_rollback,),
        tests_passed=True,
        invariants_passed=True,
        recommendation="PROMOTE",
    )
    assert blocked.approval == "HUMAN_APPROVAL_REQUIRED"


def test_source_patch_always_requires_human_merge() -> None:
    change_cls = api("EvolutionChange")
    build_bundle = api("build_evolution_bundle")
    bundle = build_bundle(
        candidate_fingerprint="c" * 64,
        parent_hash="d" * 64,
        changes=(change_cls(kind="source", description="add adapter", rollback="git-revert:abc"),),
        tests_passed=True,
        invariants_passed=True,
        recommendation="PROMOTE",
    )
    assert bundle.approval == "HUMAN_APPROVAL_REQUIRED"


def test_bundle_hash_is_deterministic_and_tamper_evident() -> None:
    change_cls = api("EvolutionChange")
    build_bundle = api("build_evolution_bundle")
    change = change_cls(kind="runtime", description="route candidate", rollback="restore:v12")
    kwargs = dict(
        candidate_fingerprint="e" * 64,
        parent_hash="f" * 64,
        changes=(change,),
        tests_passed=True,
        invariants_passed=True,
        recommendation="PROMOTE",
    )
    first = build_bundle(**kwargs)
    second = build_bundle(**kwargs)
    assert first.bundle_hash == second.bundle_hash
    changed = build_bundle(**{**kwargs, "recommendation": "HOLD"})
    assert changed.bundle_hash != first.bundle_hash


def test_failed_evolution_keeps_incumbent_hash_unchanged() -> None:
    outcome_fn = api("apply_evolution")
    result = outcome_fn(
        incumbent_hash="1" * 64,
        bundle_hash="2" * 64,
        recommendation="REJECT",
        approval="HUMAN_APPROVAL_REQUIRED",
    )
    assert result.applied is False
    assert result.active_hash == "1" * 64


def test_drift_triggers_requalification() -> None:
    needs = api("needs_requalification")
    assert needs(baseline_score=0.95, observed_score=0.84, max_drift=0.05) is True
    assert needs(baseline_score=0.95, observed_score=0.93, max_drift=0.05) is False
