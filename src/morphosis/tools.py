"""Strands tool boundary for Evolving Morphosis."""
from __future__ import annotations

from typing import Any

from strands import tool

from .core import CapabilityEvidence, WorkloadContract, build_profile, decide_candidate


def _contract(data: dict[str, Any]) -> WorkloadContract:
    return WorkloadContract(
        workload_id=data["workload_id"],
        required=tuple(data["required"]),
        hard_invariants=tuple(data["hard_invariants"]),
        weights=data["weights"],
        minimum_scores=data.get("minimum_scores", {}),
        promotion_margin=float(data.get("promotion_margin", 0.02)),
        max_regression=float(data.get("max_regression", 0.05)),
        max_cost_usd=data.get("max_cost_usd"),
        max_latency_ms=data.get("max_latency_ms"),
    )


def _evidence(rows: list[dict[str, Any]]) -> list[CapabilityEvidence]:
    return [CapabilityEvidence(**row) for row in rows]


@tool
async def qualify_candidate(
    contract: dict[str, Any],
    incumbent: dict[str, Any],
    candidate: dict[str, Any],
) -> dict[str, Any]:
    """Qualify a candidate model against a workload contract and incumbent.

    The tool never promotes a model based on name or provider metadata alone; all
    decisions are derived from supplied observed evidence and hard invariants.
    """
    policy = _contract(contract)
    old = build_profile(
        model_id=incumbent["model_id"],
        provider=incumbent["provider"],
        endpoint=incumbent["endpoint"],
        contract=policy,
        evidence=_evidence(incumbent["evidence"]),
    )
    new = build_profile(
        model_id=candidate["model_id"],
        provider=candidate["provider"],
        endpoint=candidate["endpoint"],
        contract=policy,
        evidence=_evidence(candidate["evidence"]),
    )
    decision = decide_candidate(old, new, policy)
    return {
        "workload_id": policy.workload_id,
        "incumbent": old.model_id,
        "candidate": new.model_id,
        "verdict": decision.verdict,
        "reasons": list(decision.reasons),
        "incumbent_score": decision.incumbent_score,
        "candidate_score": decision.candidate_score,
        "candidate_evidence_hash": new.evidence_hash,
        "decision_evidence_hash": decision.evidence_hash,
    }
