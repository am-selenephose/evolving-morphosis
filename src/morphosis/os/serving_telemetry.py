"""Host-owned serving observations and bounded failure-budget aggregation.

This module is deliberately outside the public command whitelist. Serving facts
come from host framework hooks, are ledgered as observations, and only invalidate
prior qualification after a minimum sample window breaches the workload policy.
"""
from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any

from .schemas import (
    DeploymentState,
    ServingObservation,
    ServingWindow,
    WorkloadContract,
    digest,
)


@dataclass(slots=True)
class ServingTelemetryRecorder:
    application: Any
    window_size: int = 50
    min_samples: int = 20

    def __post_init__(self) -> None:
        if not isinstance(self.window_size, int) or isinstance(self.window_size, bool) or not 1 <= self.window_size <= 1000:
            raise ValueError("serving window size must be 1-1000")
        if not isinstance(self.min_samples, int) or isinstance(self.min_samples, bool) or not 1 <= self.min_samples <= self.window_size:
            raise ValueError("serving min samples must be within serving window")

    def _window(self, surface_id: str, workload_id: str, contract: WorkloadContract) -> ServingWindow:
        rows = [
            ServingObservation.model_validate(value)
            for value in self.application._state.get("serving_observations", {}).values()
            if value["surface_id"] == surface_id and value["workload_id"] == workload_id
        ][-self.window_size :]
        count = len(rows)
        failures = sum(not row.success for row in rows)

        def rate(kind: str) -> float:
            return sum(row.error_kind == kind for row in rows) / count if count else 0.0

        costs = [row.cost_usd for row in rows if row.cost_usd is not None]
        average_latency = sum(row.latency_ms for row in rows) / count if count else 0.0
        average_cost = sum(costs) / len(costs) if costs else None
        reasons: list[str] = []
        if count >= self.min_samples:
            if failures / count > contract.failure_budget:
                reasons.append("SERVING_FAILURE_BUDGET")
            if rate("schema") > contract.failure_budget:
                reasons.append("SERVING_SCHEMA_FAILURE_BUDGET")
            if rate("tool") > contract.failure_budget:
                reasons.append("SERVING_TOOL_FAILURE_BUDGET")
            if rate("policy") > contract.failure_budget:
                reasons.append("SERVING_POLICY_FAILURE_BUDGET")
            if average_latency > contract.max_latency_ms:
                reasons.append("SERVING_LATENCY_BUDGET")
            if len(costs) >= self.min_samples and average_cost is not None and average_cost > contract.max_cost_usd:
                reasons.append("SERVING_COST_BUDGET")
        return ServingWindow(
            surface_id=surface_id,
            workload_id=workload_id,
            sample_count=count,
            failure_count=failures,
            failure_rate=failures / count if count else 0.0,
            schema_failure_rate=rate("schema"),
            tool_failure_rate=rate("tool"),
            policy_failure_rate=rate("policy"),
            average_latency_ms=average_latency,
            known_cost_samples=len(costs),
            average_cost_usd=average_cost,
            window_size=self.window_size,
            min_samples=self.min_samples,
            breached=bool(reasons),
            reasons=tuple(reasons),
        )

    def record(
        self,
        *,
        surface_id: str,
        workload_id: str,
        bundle_id: str,
        success: bool,
        error_kind: str = "none",
        latency_ms: float = 0.0,
        cost_usd: float | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
    ) -> dict[str, Any]:
        app = self.application
        with app.ledger.transaction():
            app._state = app.ledger.replay()
            app._now = app.clock()
            app._correlation = digest([
                "host-serving-observation",
                surface_id,
                workload_id,
                bundle_id,
                len(app.ledger.events()),
            ])
            bundle = app._state.get("bundles", {}).get(bundle_id)
            if not bundle or bundle["surface_id"] != surface_id or bundle["workload_contract"]["workload_id"] != workload_id:
                raise ValueError("serving observation does not match a known workload bundle")
            deployment = app._state.get("deployment", {}).get("current", DeploymentState().json_value())
            if bundle_id not in (deployment.get("active_bundle"), deployment.get("fallback_bundle")):
                raise ValueError("serving observation bundle is not in the current serving set")
            if not isinstance(success, bool):
                raise ValueError("serving success must be boolean")
            if success and error_kind != "none":
                raise ValueError("successful serving observation cannot carry an error kind")
            if not success and error_kind == "none":
                raise ValueError("failed serving observation requires an error kind")

            provisional = dict(
                surface_id=surface_id,
                workload_id=workload_id,
                bundle_id=bundle_id,
                success=success,
                error_kind=error_kind,
                latency_ms=latency_ms,
                cost_usd=cost_usd,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                observed_at=app._now,
                source="host-serving-hook",
            )
            observation_id = digest([provisional, len(app._state.get("serving_observations", {}))])
            observation = ServingObservation(observation_id=observation_id, **provisional)
            app._emit(
                "ServingObservationRecorded",
                "serving_observations",
                observation_id,
                observation,
                f"{surface_id[:12]}: host serving observation recorded",
            )
            app._state = app.ledger.replay()
            contract = WorkloadContract.model_validate(bundle["workload_contract"])
            window = self._window(surface_id, workload_id, contract)
            app._emit(
                "ServingWindowUpdated",
                "serving_windows",
                surface_id + ":" + workload_id,
                window,
                f"{surface_id[:12]}: serving window {window.sample_count}/{window.window_size}",
            )

            app._state = app.ledger.replay()
            requalification = None
            if window.breached:
                prior_contract = app._contract
                app._contract = contract
                try:
                    states = app._states(surface_id, app._now, contract.digest())
                    required = {
                        state.capability_id: state
                        for state in states
                        if state.capability_id in contract.required
                    }
                    still_valid = bool(required) and all(state.status != "UNKNOWN" for state in required.values())
                    if still_valid:
                        requalification = app._request_requalification(surface_id, window.reasons)
                finally:
                    app._contract = prior_contract
            return {
                "observation": observation.json_value(),
                "window": window.json_value(),
                "requalification": requalification,
            }


@dataclass(slots=True)
class StrandsServingTelemetryHook:
    recorder: ServingTelemetryRecorder
    workload_id: str
    candidate_bindings: dict[int, tuple[str, str]]
    clock: Any = perf_counter

    def __post_init__(self) -> None:
        self._starts: dict[tuple[int, int], float] = {}

    def register_hooks(self, registry, **kwargs) -> None:
        from strands.hooks import BeforeModelCallEvent, AfterModelCallEvent
        registry.add_callback(BeforeModelCallEvent, self.before_model)
        registry.add_callback(AfterModelCallEvent, self.after_model)

    def _binding(self, event) -> tuple[str, str] | None:
        model = getattr(event.agent, "model", None)
        return self.candidate_bindings.get(id(model))

    def before_model(self, event) -> None:
        binding = self._binding(event)
        if binding is not None:
            self._starts[(id(event.agent), id(event.agent.model))] = self.clock()

    def after_model(self, event) -> None:
        binding = self._binding(event)
        if binding is None or event.exception is not None:
            return
        surface_id, bundle_id = binding
        key = (id(event.agent), id(event.agent.model))
        started = self._starts.pop(key, self.clock())
        self.recorder.record(
            surface_id=surface_id,
            workload_id=self.workload_id,
            bundle_id=bundle_id,
            success=True,
            latency_ms=max(0.0, (self.clock() - started) * 1000),
        )
