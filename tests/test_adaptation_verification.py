"""Adaptation proposals must prove the transform, not only the capability."""
from __future__ import annotations

import json
from pathlib import Path

import morphosis

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / "fixtures/future_model_x.json").read_text())


def test_candidate_authored_transform_requires_independent_verification() -> None:
    report = morphosis.evaluate_future_candidate(FIXTURE, parent_hash="9" * 64)
    assert report.adaptation.transforms == ("semantic-patch-wrapper",)
    assert report.adaptation_verification.accepted is True
    assert report.adaptation_verification.proof_state == "OBSERVED"
    assert report.adaptation_verification.score == 0.96
    assert len(report.adaptation_verification.evidence_hash) == 64
    assert report.runtime_bundle.approval == "AUTO_APPLY"


def test_failed_adaptation_verification_blocks_runtime_auto_apply() -> None:
    candidate = json.loads(json.dumps(FIXTURE))
    candidate["adaptation_observation"] = {
        "valid": False,
        "score": 0.99,
        "roundtrip_preserved": False,
        "side_effect_free": True
    }
    report = morphosis.evaluate_future_candidate(candidate, parent_hash="9" * 64)
    assert report.observed_capability.status == "SUPPORTED"
    assert report.adaptation_verification.accepted is False
    assert report.runtime_bundle.recommendation == "REJECT"
    assert report.runtime_bundle.approval == "BLOCKED"
