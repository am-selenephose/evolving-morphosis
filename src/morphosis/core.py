"""Core qualification engine for Evolving Morphosis.

Static provider metadata is treated as a prior, never as proof. Promotion depends on
observed, workload-scoped evidence and hard invariants.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Mapping


VALID_STATUS = {"SUPPORTED", "UNSUPPORTED", "UNKNOWN"}


@dataclass(frozen=True)
class CapabilityEvidence:
    capability: str
    status: str
    score: float
    passed: bool
    source: str
    evidence: str
    confidence: float = 1.0
    latency_ms: float = 0.0
    cost_usd: float = 0.0

    def __post_init__(self) -> None:
        if self.status not in VALID_STATUS:
            raise ValueError(f"invalid capability status: {self.status}")
        for name, value in (("score", self.score), ("confidence", self.confidence)):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")
        if self.latency_ms < 0 or self.cost_usd < 0:
            raise ValueError("latency and cost cannot be negative")


@dataclass(frozen=True)
class WorkloadContract:
    workload_id: str
    required: tuple[str, ...]
    hard_invariants: tuple[str, ...]
    weights: Mapping[str, float]
    minimum_scores: Mapping[str, float] = field(default_factory=dict)
    promotion_margin: float = 0.02
    max_regression: float = 0.05
    max_cost_usd: float | None = None
    max_latency_ms: float | None = None


@dataclass(frozen=True)
class CandidateProfile:
    model_id: str
    provider: str
    endpoint: str
    workload_id: str
    evidence: tuple[CapabilityEvidence, ...]
    workload_score: float
    total_latency_ms: float
    total_cost_usd: float
    evidence_hash: str


@dataclass(frozen=True)
class PromotionDecision:
    verdict: str
    reasons: tuple[str, ...]
    incumbent_score: float
    candidate_score: float
    evidence_hash: str


def _stable_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_profile(
    *,
    model_id: str,
    provider: str,
    endpoint: str,
    contract: WorkloadContract,
    evidence: list[CapabilityEvidence],
) -> CandidateProfile:
    by_name = {item.capability: item for item in evidence}
    weights = {name: contract.weights.get(name, 0.0) for name in by_name}
    denominator = sum(weights.values()) or 1.0
    score = sum(by_name[name].score * weights[name] for name in by_name) / denominator
    ordered = tuple(sorted(evidence, key=lambda item: item.capability))
    payload = {
        "model_id": model_id,
        "provider": provider,
        "endpoint": endpoint,
        "workload_id": contract.workload_id,
        "evidence": [asdict(item) for item in ordered],
        "score": round(score, 6),
    }
    return CandidateProfile(
        model_id=model_id,
        provider=provider,
        endpoint=endpoint,
        workload_id=contract.workload_id,
        evidence=ordered,
        workload_score=round(score, 6),
        total_latency_ms=round(sum(item.latency_ms for item in evidence), 3),
        total_cost_usd=round(sum(item.cost_usd for item in evidence), 6),
        evidence_hash=_stable_hash(payload),
    )


def decide_candidate(
    incumbent: CandidateProfile,
    candidate: CandidateProfile,
    contract: WorkloadContract,
) -> PromotionDecision:
    if incumbent.workload_id != candidate.workload_id or candidate.workload_id != contract.workload_id:
        raise ValueError("profiles and contract must target the same workload")

    old = {item.capability: item for item in incumbent.evidence}
    new = {item.capability: item for item in candidate.evidence}
    reasons: list[str] = []

    for name in contract.required:
        item = new.get(name)
        if item is None:
            reasons.append(f"missing required capability: {name}")
        elif item.status != "SUPPORTED" or not item.passed:
            reasons.append(f"required capability failed: {name}")
        elif item.score < contract.minimum_scores.get(name, 0.0):
            reasons.append(f"below minimum score: {name}")

    for name in contract.hard_invariants:
        item = new.get(name)
        if item is None or item.status != "SUPPORTED" or not item.passed or item.score < 1.0:
            reasons.append(f"hard invariant failed: {name}")

    for name, prior in old.items():
        current = new.get(name)
        if current and prior.score - current.score > contract.max_regression:
            reasons.append(f"regression exceeds limit: {name}")

    if contract.max_cost_usd is not None and candidate.total_cost_usd > contract.max_cost_usd:
        reasons.append("candidate exceeds workload cost budget")
    if contract.max_latency_ms is not None and candidate.total_latency_ms > contract.max_latency_ms:
        reasons.append("candidate exceeds workload latency budget")

    improvement = candidate.workload_score - incumbent.workload_score
    if reasons:
        verdict = "REJECT"
    elif improvement >= contract.promotion_margin:
        verdict = "PROMOTE"
        reasons.append(f"workload score improved by {improvement:.3f}")
    else:
        verdict = "HOLD"
        reasons.append(f"improvement {improvement:.3f} below promotion margin")

    decision_hash = _stable_hash({
        "candidate": candidate.evidence_hash,
        "incumbent": incumbent.evidence_hash,
        "verdict": verdict,
        "reasons": reasons,
    })
    return PromotionDecision(
        verdict=verdict,
        reasons=tuple(reasons),
        incumbent_score=incumbent.workload_score,
        candidate_score=candidate.workload_score,
        evidence_hash=decision_hash,
    )
