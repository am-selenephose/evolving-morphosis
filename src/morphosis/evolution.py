"""Future-model adaptation primitives for Evolving Morphosis.

The stable core does not need to know every future capability name. Candidate claims
remain unverified until independent probe evidence upgrades them.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Mapping, Sequence

_ALLOWED_PROBE_KINDS = {"fixture_roundtrip", "tool_call", "json_schema", "text_roundtrip"}
_CHANGE_KINDS = {"runtime", "config", "source"}


def _stable_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class KnownAdapterRegistry:
    adapters: Mapping[tuple[str, str], str] = field(default_factory=dict)

    def resolve(self, provider: str, model_id: str) -> str | None:
        return self.adapters.get((provider, model_id))


@dataclass(frozen=True)
class CandidateIdentity:
    model_id: str
    provider: str
    endpoint: str
    lane: str
    adapter: str | None
    candidate_fingerprint: str


def bootstrap_candidate(
    model_id: str,
    provider: str,
    endpoint: str,
    registry: KnownAdapterRegistry,
) -> CandidateIdentity:
    adapter = registry.resolve(provider, model_id)
    lane = "KNOWN_FAST_PATH" if adapter is not None else "UNKNOWN_BOOTSTRAP"
    fingerprint = _stable_hash({
        "model_id": model_id,
        "provider": provider,
        "endpoint": endpoint,
        "lane": lane,
        "adapter": adapter,
    })
    return CandidateIdentity(model_id, provider, endpoint, lane, adapter, fingerprint)


@dataclass(frozen=True)
class CapabilityRecord:
    capability_id: str
    status: str
    proof_state: str
    claimed_supported: bool
    source: str
    score: float = 0.0
    evidence_hash: str = ""


@dataclass(frozen=True)
class ProbeProposal:
    probe_id: str
    capability_id: str
    kind: str
    timeout_ms: int
    network_access: bool = False
    source_write: bool = False


@dataclass(frozen=True)
class ProbeResult:
    probe_id: str
    capability_id: str
    accepted: bool
    status: str
    score: float
    evidence_hash: str
    reason: str


@dataclass(frozen=True)
class CapabilityRegistry:
    records: tuple[CapabilityRecord, ...] = ()

    def get(self, capability_id: str) -> CapabilityRecord:
        for record in self.records:
            if record.capability_id == capability_id:
                return record
        raise KeyError(capability_id)

    def register_claim(
        self,
        capability_id: str,
        claimed_supported: bool,
        source: str,
    ) -> "CapabilityRegistry":
        record = CapabilityRecord(
            capability_id=capability_id,
            status="UNKNOWN",
            proof_state="UNVERIFIED",
            claimed_supported=claimed_supported,
            source=source,
        )
        kept = tuple(r for r in self.records if r.capability_id != capability_id)
        return CapabilityRegistry(kept + (record,))

    def apply_probe_result(self, result: ProbeResult) -> "CapabilityRegistry":
        existing = None
        try:
            existing = self.get(result.capability_id)
        except KeyError:
            pass
        claimed = existing.claimed_supported if existing else False
        source = existing.source if existing else "runtime-probe"
        proof_state = "OBSERVED" if result.accepted else "UNVERIFIED"
        record = CapabilityRecord(
            capability_id=result.capability_id,
            status=result.status,
            proof_state=proof_state,
            claimed_supported=claimed,
            source=source,
            score=result.score,
            evidence_hash=result.evidence_hash,
        )
        kept = tuple(r for r in self.records if r.capability_id != result.capability_id)
        return CapabilityRegistry(kept + (record,))


def verify_probe_proposal(
    proposal: ProbeProposal,
    *,
    observed_output: Mapping[str, object],
) -> ProbeResult:
    unsafe = (
        proposal.kind not in _ALLOWED_PROBE_KINDS
        or proposal.timeout_ms <= 0
        or proposal.timeout_ms > 5000
        or proposal.network_access
        or proposal.source_write
    )
    if unsafe:
        payload = {"proposal": asdict(proposal), "accepted": False, "reason": "unsafe-probe"}
        return ProbeResult(
            proposal.probe_id,
            proposal.capability_id,
            False,
            "UNKNOWN",
            0.0,
            _stable_hash(payload),
            "unsafe probe rejected before execution",
        )
    valid = bool(observed_output.get("valid", False))
    score_raw = observed_output.get("score", 0.0)
    score = float(score_raw) if isinstance(score_raw, (int, float)) else 0.0
    score = min(1.0, max(0.0, score))
    status = "SUPPORTED" if valid else "UNSUPPORTED"
    payload = {
        "proposal": asdict(proposal),
        "observed": dict(observed_output),
        "status": status,
        "score": score,
    }
    return ProbeResult(
        proposal.probe_id,
        proposal.capability_id,
        True,
        status,
        score,
        _stable_hash(payload),
        "independent bounded probe observation",
    )


@dataclass(frozen=True)
class AdaptationPlan:
    capability_id: str
    mode: str
    native: bool
    transforms: tuple[str, ...] = ()


def compile_adaptation(
    *,
    capability_id: str,
    native_supported: bool,
    fallback: str | None = None,
) -> AdaptationPlan:
    if native_supported:
        return AdaptationPlan(capability_id, "NATIVE", True, ())
    if fallback:
        return AdaptationPlan(capability_id, "ADAPTED", False, (fallback,))
    return AdaptationPlan(capability_id, "UNSUPPORTED", False, ())


@dataclass(frozen=True)
class EvolutionChange:
    kind: str
    description: str
    rollback: str

    def __post_init__(self) -> None:
        if self.kind not in _CHANGE_KINDS:
            raise ValueError(f"invalid evolution change kind: {self.kind}")


@dataclass(frozen=True)
class EvolutionBundle:
    candidate_fingerprint: str
    parent_hash: str
    changes: tuple[EvolutionChange, ...]
    tests_passed: bool
    invariants_passed: bool
    recommendation: str
    approval: str
    bundle_hash: str


def build_evolution_bundle(
    *,
    candidate_fingerprint: str,
    parent_hash: str,
    changes: Sequence[EvolutionChange],
    tests_passed: bool,
    invariants_passed: bool,
    recommendation: str,
) -> EvolutionBundle:
    frozen_changes = tuple(changes)
    source_change = any(change.kind == "source" for change in frozen_changes)
    rollback_missing = any(not change.rollback.strip() for change in frozen_changes)
    if recommendation != "PROMOTE" or not tests_passed or not invariants_passed:
        approval = "BLOCKED"
    elif source_change or rollback_missing:
        approval = "HUMAN_APPROVAL_REQUIRED"
    else:
        approval = "AUTO_APPLY"
    payload = {
        "candidate_fingerprint": candidate_fingerprint,
        "parent_hash": parent_hash,
        "changes": [asdict(change) for change in frozen_changes],
        "tests_passed": tests_passed,
        "invariants_passed": invariants_passed,
        "recommendation": recommendation,
        "approval": approval,
    }
    bundle_hash = _stable_hash(payload)
    return EvolutionBundle(
        candidate_fingerprint,
        parent_hash,
        frozen_changes,
        tests_passed,
        invariants_passed,
        recommendation,
        approval,
        bundle_hash,
    )


@dataclass(frozen=True)
class EvolutionOutcome:
    applied: bool
    active_hash: str
    previous_hash: str


def apply_evolution(
    *,
    incumbent_hash: str,
    bundle_hash: str,
    recommendation: str,
    approval: str,
) -> EvolutionOutcome:
    applied = recommendation == "PROMOTE" and approval == "AUTO_APPLY"
    return EvolutionOutcome(applied, bundle_hash if applied else incumbent_hash, incumbent_hash)


def needs_requalification(
    *,
    baseline_score: float,
    observed_score: float,
    max_drift: float,
) -> bool:
    if max_drift < 0:
        raise ValueError("max_drift cannot be negative")
    return baseline_score - observed_score > max_drift
