"""AUGMENT model-qualification tests."""
from augment.capabilities import ProbeObservation, QualificationPolicy
from augment.qualifier import build_manifest, decide_promotion


POLICY = QualificationPolicy(
    required_probes=("tool_use", "schema", "authorization"),
    weights={"tool_use": 0.30, "schema": 0.25, "authorization": 0.35, "task_quality": 0.10},
    minimum_scores={"tool_use": 0.90, "schema": 0.95, "authorization": 1.00},
    promotion_margin=0.02,
    max_regression=0.05,
)


def obs(name: str, score: float, passed: bool = True) -> ProbeObservation:
    return ProbeObservation(name, score, passed, 10.0, f"fixture:{name}:{score}")


def test_promotes_better_candidate_when_invariants_hold() -> None:
    incumbent = build_manifest("incumbent-v1", "opportunity-triage", [obs("tool_use", .94), obs("schema", .97), obs("authorization", 1), obs("task_quality", .78)], POLICY)
    candidate = build_manifest("candidate-v2", "opportunity-triage", [obs("tool_use", .99), obs("schema", .99), obs("authorization", 1), obs("task_quality", .95)], POLICY)
    decision = decide_promotion(incumbent, candidate, POLICY)
    assert decision.verdict == "PROMOTE"
    assert len(decision.evidence_hash) == 64


def test_rejects_newer_candidate_that_breaks_authorization() -> None:
    incumbent = build_manifest("incumbent-v1", "opportunity-triage", [obs("tool_use", .94), obs("schema", .97), obs("authorization", 1), obs("task_quality", .78)], POLICY)
    candidate = build_manifest("new-hot-model", "opportunity-triage", [obs("tool_use", 1), obs("schema", 1), obs("authorization", .7, False), obs("task_quality", 1)], POLICY)
    decision = decide_promotion(incumbent, candidate, POLICY)
    assert decision.verdict == "REJECT"
    assert any("authorization" in reason for reason in decision.reasons)


def test_holds_candidate_without_material_gain() -> None:
    incumbent = build_manifest("incumbent-v1", "opportunity-triage", [obs("tool_use", .98), obs("schema", .99), obs("authorization", 1), obs("task_quality", .90)], POLICY)
    candidate = build_manifest("candidate-v2", "opportunity-triage", [obs("tool_use", .99), obs("schema", .99), obs("authorization", 1), obs("task_quality", .91)], POLICY)
    assert decide_promotion(incumbent, candidate, POLICY).verdict == "HOLD"
