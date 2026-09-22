import asyncio

from morphosis.demo_model import DeterministicFutureModel, _text
from morphosis.os.application import MorphosisApplication
from morphosis.os.serving import build_strands_serving_agent
from morphosis.os.serving_telemetry import ServingTelemetryRecorder


def promote(app, model):
    surface = app.command(
        "bootstrap",
        {
            "model": model,
            "provider": "reference",
            "endpoint": "reference://echo",
            "claims": ["future.semantic_patch.v1"],
        },
    )
    app.command("evaluate", {"surface_id": surface["surface_id"]})
    packaged = app.command("bundle", {"surface_id": surface["surface_id"], "rollback": True})
    tid = packaged["transaction"]["transaction_id"]
    for _ in range(7):
        app.command("advance", {"transaction_id": tid})
    return surface, packaged["bundle"]


class SuccessfulServingModel(DeterministicFutureModel):
    async def stream(self, messages, tool_specs=None, system_prompt=None, **kwargs):
        async for event in _text("served by fallback"):
            yield event


class FailingServingModel(DeterministicFutureModel):
    async def stream(self, messages, tool_specs=None, system_prompt=None, **kwargs):
        raise RuntimeError("synthetic serving failure")
        yield


def test_single_transient_serving_failure_is_observed_without_immediate_rollback(tmp_path):
    app = MorphosisApplication(tmp_path / "transient.db", clock=lambda: "2026-09-22T00:00:00Z")
    surface, bundle = promote(app, "transient-model")
    recorder = ServingTelemetryRecorder(app, window_size=3, min_samples=3)
    try:
        result = recorder.record(
            surface_id=surface["surface_id"],
            workload_id="tool-roundtrip",
            bundle_id=bundle["bundle_id"],
            success=False,
            error_kind="model",
            latency_ms=25,
        )
        assert result["window"]["sample_count"] == 1
        assert result["window"]["breached"] is False
        assert result["requalification"] is None
        assert app.snapshot()["deployment"]["active_bundle"] == bundle["bundle_id"]
        state = app.ledger.replay()
        assert len(state["serving_observations"]) == 1
        assert len(state["serving_windows"]) == 1
    finally:
        app.close()


def test_rolling_failure_budget_invalidates_active_and_restores_qualified_fallback(tmp_path):
    app = MorphosisApplication(tmp_path / "failure-budget.db", clock=lambda: "2026-09-22T00:00:00Z")
    first, first_bundle = promote(app, "qualified-fallback")
    second, second_bundle = promote(app, "active-candidate")
    recorder = ServingTelemetryRecorder(app, window_size=3, min_samples=3)
    try:
        for _ in range(2):
            result = recorder.record(
                surface_id=second["surface_id"],
                workload_id="tool-roundtrip",
                bundle_id=second_bundle["bundle_id"],
                success=True,
                latency_ms=25,
            )
            assert result["requalification"] is None

        result = recorder.record(
            surface_id=second["surface_id"],
            workload_id="tool-roundtrip",
            bundle_id=second_bundle["bundle_id"],
            success=False,
            error_kind="model",
            latency_ms=25,
        )
        assert result["window"]["failure_rate"] == 1 / 3
        assert "SERVING_FAILURE_BUDGET" in result["window"]["reasons"]
        assert result["requalification"]["required"] is True
        assert app.snapshot()["deployment"]["active_bundle"] == first_bundle["bundle_id"]
        assert app.command("qualify", {"surface_id": second["surface_id"]})["outcome"] == "HOLD"
    finally:
        app.close()


def test_latency_and_known_cost_budgets_require_minimum_samples(tmp_path):
    app = MorphosisApplication(tmp_path / "latency-budget.db", clock=lambda: "2026-09-22T00:00:00Z")
    surface, bundle = promote(app, "slow-expensive")
    recorder = ServingTelemetryRecorder(app, window_size=3, min_samples=3)
    try:
        for index in range(3):
            result = recorder.record(
                surface_id=surface["surface_id"],
                workload_id="tool-roundtrip",
                bundle_id=bundle["bundle_id"],
                success=True,
                latency_ms=7001,
                cost_usd=0.06,
            )
            if index < 2:
                assert result["window"]["breached"] is False
        assert set(result["window"]["reasons"]) == {
            "SERVING_LATENCY_BUDGET",
            "SERVING_COST_BUDGET",
        }
    finally:
        app.close()


def test_real_strands_router_records_failed_active_then_successful_fallback(tmp_path):
    app = MorphosisApplication(tmp_path / "strands-serving.db", clock=lambda: "2026-09-22T00:00:00Z")
    fallback, fallback_bundle = promote(app, "router-fallback")
    active, active_bundle = promote(app, "router-active")

    def factory(entry):
        cls = FailingServingModel if entry["role"] == "active" else SuccessfulServingModel
        model = cls({}, "")
        model.config = {"model_id": "telemetry-" + entry["surface_id"][:12]}
        return model

    agent = build_strands_serving_agent(
        app,
        "tool-roundtrip",
        model_factory=factory,
        max_switches=1,
        telemetry_window_size=1,
        telemetry_min_samples=1,
    )
    try:
        result = asyncio.run(agent.invoke_async("serve this request"))
        assert result.stop_reason == "end_turn"
        state = app.ledger.replay()
        observations = list(state["serving_observations"].values())
        assert len(observations) == 2
        failed = next(row for row in observations if not row["success"])
        succeeded = next(row for row in observations if row["success"])
        assert failed["surface_id"] == active["surface_id"]
        assert failed["bundle_id"] == active_bundle["bundle_id"]
        assert failed["error_kind"] == "model"
        assert succeeded["surface_id"] == fallback["surface_id"]
        assert succeeded["bundle_id"] == fallback_bundle["bundle_id"]
        assert app.snapshot()["deployment"]["active_bundle"] == fallback_bundle["bundle_id"]
    finally:
        app.close()
