"""End-to-end deterministic evolution flow for unknown future models."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .evolution import (
    AdaptationPlan,
    CandidateIdentity,
    CapabilityRecord,
    CapabilityRegistry,
    EvolutionBundle,
    EvolutionChange,
    KnownAdapterRegistry,
    ProbeProposal,
    bootstrap_candidate,
    build_evolution_bundle,
    compile_adaptation,
    verify_probe_proposal,
)


@dataclass(frozen=True)
class FutureEvolutionReport:
    identity: CandidateIdentity
    claimed_capability: CapabilityRecord
    observed_capability: CapabilityRecord
    adaptation: AdaptationPlan
    runtime_bundle: EvolutionBundle
    source_bundle: EvolutionBundle


def evaluate_future_candidate(
    candidate: Mapping[str, object],
    *,
    parent_hash: str,
    known_adapters: KnownAdapterRegistry | None = None,
) -> FutureEvolutionReport:
    """Qualify an unknown model and build runtime/source Evolution Bundles.

    Candidate claims and candidate-authored probe descriptions are inputs only. The
    verifier owns pass/fail, and the candidate never controls promotion authority.
    """
    adapters = known_adapters or KnownAdapterRegistry({})
    identity = bootstrap_candidate(
        str(candidate["model_id"]),
        str(candidate["provider"]),
        str(candidate["endpoint"]),
        adapters,
    )

    claims = candidate.get("self_reported_capabilities")
    if not isinstance(claims, list) or not claims or not isinstance(claims[0], dict):
        raise ValueError("candidate must self-report at least one capability claim")
    claim = claims[0]
    registry = CapabilityRegistry().register_claim(
        str(claim["capability_id"]),
        bool(claim.get("claimed_supported", False)),
        str(claim.get("source", "candidate-self-report")),
    )
    claimed = registry.get(str(claim["capability_id"]))

    probe_data = candidate.get("candidate_probe")
    observation = candidate.get("independent_observation")
    if not isinstance(probe_data, dict) or not isinstance(observation, dict):
        raise ValueError("candidate probe and independent observation are required")
    proposal = ProbeProposal(
        probe_id=str(probe_data["probe_id"]),
        capability_id=str(probe_data["capability_id"]),
        kind=str(probe_data["kind"]),
        timeout_ms=int(probe_data["timeout_ms"]),
        network_access=bool(probe_data.get("network_access", False)),
        source_write=bool(probe_data.get("source_write", False)),
    )
    probe_result = verify_probe_proposal(proposal, observed_output=observation)
    observed_registry = registry.apply_probe_result(probe_result)
    observed = observed_registry.get(proposal.capability_id)

    adaptation = compile_adaptation(
        capability_id=proposal.capability_id,
        native_supported=False,
        fallback="compatibility-wrapper",
    )

    runtime_data = candidate.get("runtime_change")
    source_data = candidate.get("source_change")
    if not isinstance(runtime_data, dict) or not isinstance(source_data, dict):
        raise ValueError("runtime and source change proposals are required")
    runtime_change = EvolutionChange(
        kind=str(runtime_data["kind"]),
        description=str(runtime_data["description"]),
        rollback=str(runtime_data.get("rollback", "")),
    )
    source_change = EvolutionChange(
        kind=str(source_data["kind"]),
        description=str(source_data["description"]),
        rollback=str(source_data.get("rollback", "")),
    )

    gates_pass = observed.status == "SUPPORTED" and observed.proof_state == "OBSERVED"
    recommendation = "PROMOTE" if gates_pass else "REJECT"
    runtime_bundle = build_evolution_bundle(
        candidate_fingerprint=identity.candidate_fingerprint,
        parent_hash=parent_hash,
        changes=(runtime_change,),
        tests_passed=probe_result.accepted and probe_result.status == "SUPPORTED",
        invariants_passed=gates_pass,
        recommendation=recommendation,
    )
    source_bundle = build_evolution_bundle(
        candidate_fingerprint=identity.candidate_fingerprint,
        parent_hash=parent_hash,
        changes=(source_change,),
        tests_passed=probe_result.accepted and probe_result.status == "SUPPORTED",
        invariants_passed=gates_pass,
        recommendation=recommendation,
    )

    return FutureEvolutionReport(
        identity=identity,
        claimed_capability=claimed,
        observed_capability=observed,
        adaptation=adaptation,
        runtime_bundle=runtime_bundle,
        source_bundle=source_bundle,
    )
