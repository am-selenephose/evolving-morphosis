"""Deterministic workload-scoped qualification and promotion decisions."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .capabilities import CapabilityManifest, ProbeObservation, QualificationPolicy


@dataclass(frozen=True)
class PromotionDecision:
    verdict: str
    reasons: tuple[str, ...]
    candidate_score: float
    incumbent_score: float
    evidence_hash: str


def _hash(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode()).hexdigest()


def build_manifest(model_id: str, workload: str, observations: list[ProbeObservation], policy: QualificationPolicy) -> CapabilityManifest:
    by_name = {o.name: o for o in observations}
    total_weight = sum(policy.weights.get(name, 0.0) for name in by_name) or 1.0
    weighted = sum(by_name[name].score * policy.weights.get(name, 0.0) for name in by_name) / total_weight
    payload = {
        "model_id": model_id,
        "workload": workload,
        "observations": [o.__dict__ for o in sorted(observations, key=lambda x: x.name)],
        "workload_score": round(weighted, 6),
    }
    return CapabilityManifest(
        model_id=model_id,
        workload=workload,
        observations=tuple(sorted(observations, key=lambda x: x.name)),
        workload_score=round(weighted, 6),
        total_latency_ms=round(sum(o.latency_ms for o in observations), 3),
        total_cost_usd=round(sum(o.cost_usd for o in observations), 6),
        evidence_hash=_hash(payload),
    )


def decide_promotion(incumbent: CapabilityManifest, candidate: CapabilityManifest, policy: QualificationPolicy) -> PromotionDecision:
    if incumbent.workload != candidate.workload:
        raise ValueError("manifests must target the same workload")
    cand = {o.name: o for o in candidate.observations}
    inc = {o.name: o for o in incumbent.observations}
    reasons: list[str] = []

    for name in policy.required_probes:
        obs = cand.get(name)
        if obs is None:
            reasons.append(f"missing required probe: {name}")
        elif not obs.passed:
            reasons.append(f"required probe failed: {name}")
        elif obs.score < policy.minimum_scores.get(name, 0.0):
            reasons.append(f"below minimum score: {name}")

    for name, old in inc.items():
        new = cand.get(name)
        if new and old.score - new.score > policy.max_regression:
            reasons.append(f"regression exceeds limit: {name}")

    improvement = candidate.workload_score - incumbent.workload_score
    if reasons:
        verdict = "REJECT"
    elif improvement >= policy.promotion_margin:
        verdict = "PROMOTE"
        reasons.append(f"workload score improved by {improvement:.3f}")
    else:
        verdict = "HOLD"
        reasons.append(f"improvement {improvement:.3f} below promotion margin")

    decision_payload = {
        "candidate": candidate.evidence_hash,
        "incumbent": incumbent.evidence_hash,
        "verdict": verdict,
        "reasons": reasons,
    }
    return PromotionDecision(
        verdict=verdict,
        reasons=tuple(reasons),
        candidate_score=candidate.workload_score,
        incumbent_score=incumbent.workload_score,
        evidence_hash=_hash(decision_payload),
    )
