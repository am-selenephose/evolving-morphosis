"""Evolving Morphosis deterministic qualification tests."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from morphosis.core import CapabilityEvidence, WorkloadContract, build_profile, decide_candidate

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_DATA = json.loads((ROOT / "fixtures/morphosis_contract.json").read_text())
MODELS = json.loads((ROOT / "fixtures/morphosis_candidates.json").read_text())


def contract() -> WorkloadContract:
    return WorkloadContract(
        workload_id=CONTRACT_DATA["workload_id"],
        required=tuple(CONTRACT_DATA["required"]),
        hard_invariants=tuple(CONTRACT_DATA["hard_invariants"]),
        weights=CONTRACT_DATA["weights"],
        minimum_scores=CONTRACT_DATA["minimum_scores"],
        promotion_margin=CONTRACT_DATA["promotion_margin"],
        max_regression=CONTRACT_DATA["max_regression"],
        max_cost_usd=CONTRACT_DATA["max_cost_usd"],
        max_latency_ms=CONTRACT_DATA["max_latency_ms"],
    )


def profile(data: dict, policy: WorkloadContract):
    return build_profile(
        model_id=data["model_id"], provider=data["provider"], endpoint=data["endpoint"],
        contract=policy, evidence=[CapabilityEvidence(**row) for row in data["evidence"]]
    )


class MorphosisTests(unittest.TestCase):
    def test_rejects_stronger_model_that_breaks_hard_invariant(self) -> None:
        policy = contract()
        incumbent = profile(MODELS["incumbent"], policy)
        candidate = profile(MODELS["candidates"][0], policy)
        decision = decide_candidate(incumbent, candidate, policy)
        self.assertEqual(decision.verdict, "REJECT")
        self.assertTrue(any("authorization" in reason for reason in decision.reasons))

    def test_promotes_future_model_when_workload_contract_passes(self) -> None:
        policy = contract()
        incumbent = profile(MODELS["incumbent"], policy)
        candidate = profile(MODELS["candidates"][1], policy)
        decision = decide_candidate(incumbent, candidate, policy)
        self.assertEqual(decision.verdict, "PROMOTE")
        self.assertGreater(decision.candidate_score, decision.incumbent_score)
        self.assertEqual(len(decision.evidence_hash), 64)

    def test_manifest_is_stable_for_same_evidence(self) -> None:
        policy = contract()
        first = profile(MODELS["incumbent"], policy)
        second = profile(MODELS["incumbent"], policy)
        self.assertEqual(first, second)
        self.assertEqual(len(first.evidence_hash), 64)


if __name__ == "__main__":
    unittest.main()
