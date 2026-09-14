"""End-to-end deterministic future-model evolution test."""
from __future__ import annotations

import json
from pathlib import Path

import morphosis

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / "fixtures/future_model_x.json").read_text())


def test_unknown_future_model_can_teach_runtime_how_to_integrate_it() -> None:
    evolve = getattr(morphosis, "evaluate_future_candidate", None)
    assert evolve is not None, "missing Morphosis v2 API: evaluate_future_candidate"
    report = evolve(FIXTURE, parent_hash="9" * 64)

    assert report.identity.lane == "UNKNOWN_BOOTSTRAP"
    assert report.claimed_capability.status == "UNKNOWN"
    assert report.claimed_capability.proof_state == "UNVERIFIED"
    assert report.observed_capability.capability_id == "future.semantic_patch.v1"
    assert report.observed_capability.status == "SUPPORTED"
    assert report.observed_capability.proof_state == "OBSERVED"
    assert report.adaptation.mode == "ADAPTED"
    assert report.runtime_bundle.approval == "AUTO_APPLY"
    assert report.source_bundle.approval == "HUMAN_APPROVAL_REQUIRED"
    assert report.runtime_bundle.bundle_hash != report.source_bundle.bundle_hash
