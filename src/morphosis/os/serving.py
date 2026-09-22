"""Policy-gated Strands model routing built only from Morphosis admissions.

Strands may choose/fail over within the immutable router candidate set, but this
strategy revalidates Morphosis admission before every selection so stale or
revoked candidates cannot be resurrected by router health history.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from .schemas import digest
from .transports import BedrockConverseBinding

QUALIFIED_OUTCOMES=frozenset(("PROMOTE_TO_SHADOW","PROMOTE_TO_CANARY","PROMOTE"))


def serving_manifest(application, workload_id: str) -> list[dict[str, Any]]:
    snapshot=application.snapshot()
    deployment=snapshot["deployment"]
    ordered=[deployment.get("active_bundle"),deployment.get("fallback_bundle")]
    seen=set();manifest=[]
    models={row["surface_id"]:row for row in snapshot["models"]}
    transactions=snapshot["transactions"]
    for bundle_id in ordered:
        if not bundle_id or bundle_id in seen:
            continue
        seen.add(bundle_id)
        bundle=application.revision(bundle_id)
        contract=bundle["workload_contract"]
        if contract["workload_id"]!=workload_id:
            continue
        if any(t["bundle_id"]==bundle_id and t["stage"] in ("ROLLBACK","REJECT") for t in transactions):
            continue
        sid=bundle["surface_id"]
        command_id="serving-revalidate-"+digest([bundle_id,workload_id,snapshot["ledger_head"]])
        try:
            decision=application.command(
                "qualify",
                {"surface_id":sid,"workload_id":workload_id},
                command_id=command_id,
            )
        except ValueError:
            continue
        if decision["outcome"] not in QUALIFIED_OUTCOMES:
            continue
        surface=models.get(sid)
        if not surface:
            continue
        manifest.append({
            "bundle_id":bundle_id,
            "surface_id":sid,
            "model":surface["model"],
            "provider":surface["provider"],
            "endpoint":surface["endpoint"],
            "qualification":decision["outcome"],
            "workload_id":workload_id,
            "role":"active" if bundle_id==deployment.get("active_bundle") else "fallback",
        })
    return manifest


@dataclass(slots=True)
class MorphosisAdmissionStrategy:
    application: Any
    workload_id: str
    surface_ids: tuple[str,...]
    bundle_ids: tuple[str,...]=()
    telemetry_recorder: Any=None
    _recorded_failures: set[tuple[int,int]]=field(default_factory=set,init=False,repr=False)

    async def select(self, context, **kwargs):
        if len(context.candidates)!=len(self.surface_ids):
            raise ValueError("Strands router candidate set diverged from Morphosis admission manifest")
        if self.telemetry_recorder is not None and len(self.bundle_ids)!=len(self.surface_ids):
            raise ValueError("telemetry bundle mapping diverged from Morphosis admission manifest")
        if self.telemetry_recorder is not None:
            mapping={id(candidate):(surface_id,bundle_id) for candidate,surface_id,bundle_id in zip(context.candidates,self.surface_ids,self.bundle_ids)}
            for attempt in context.attempts:
                if attempt.exception is None or id(attempt.candidate) not in mapping:
                    continue
                key=(id(attempt.candidate),id(attempt.exception))
                if key in self._recorded_failures:
                    continue
                self._recorded_failures.add(key)
                surface_id,bundle_id=mapping[id(attempt.candidate)]
                self.telemetry_recorder.record(
                    surface_id=surface_id,
                    workload_id=self.workload_id,
                    bundle_id=bundle_id,
                    success=False,
                    error_kind="model",
                )
        allowed={row["surface_id"] for row in serving_manifest(self.application,self.workload_id)}
        attempted={id(attempt.candidate) for attempt in context.attempts}
        for candidate,surface_id in zip(context.candidates,self.surface_ids):
            if surface_id in allowed and id(candidate) not in attempted:
                return candidate
        return None


def _bedrock_model_factory(application, entry):
    if entry["provider"]!="bedrock":
        raise ValueError("default Strands serving factory only supports qualified Bedrock surfaces")
    binding=application.transports.get((entry["provider"],entry["endpoint"]))
    if not isinstance(binding,BedrockConverseBinding):
        raise ValueError("qualified Bedrock surface lacks exact host-owned Converse binding")
    from strands.models import BedrockModel
    return BedrockModel(
        model_id=binding.model_id,
        region_name=binding.region_name,
        temperature=0,
    )


def build_strands_model_router(
    application,
    workload_id: str,
    *,
    model_factory: Callable[[dict[str,Any]],Any] | None=None,
    max_switches: int=1,
    telemetry_recorder=None,
):
    if not isinstance(max_switches,int) or isinstance(max_switches,bool) or max_switches<0:
        raise ValueError("max_switches must be a non-negative integer")
    manifest=serving_manifest(application,workload_id)
    if not manifest:
        raise ValueError("no currently qualified Morphosis serving candidates")
    factory=model_factory or (lambda entry:_bedrock_model_factory(application,entry))
    models=[factory(entry) for entry in manifest]
    from strands.models import ModelRouter
    strategy=MorphosisAdmissionStrategy(
        application=application,
        workload_id=workload_id,
        surface_ids=tuple(entry["surface_id"] for entry in manifest),
        bundle_ids=tuple(entry["bundle_id"] for entry in manifest),
        telemetry_recorder=telemetry_recorder,
    )
    return ModelRouter(models=models,strategy=strategy,max_switches=max_switches)


def build_strands_serving_agent(
    application,
    workload_id: str,
    *,
    model_factory: Callable[[dict[str,Any]],Any] | None=None,
    max_switches: int=1,
    telemetry_window_size: int=50,
    telemetry_min_samples: int=20,
    hooks=None,
    **agent_kwargs,
):
    from strands import Agent
    from .serving_telemetry import ServingTelemetryRecorder,StrandsServingTelemetryHook

    recorder=ServingTelemetryRecorder(application,window_size=telemetry_window_size,min_samples=telemetry_min_samples)
    router=build_strands_model_router(
        application,
        workload_id,
        model_factory=model_factory,
        max_switches=max_switches,
        telemetry_recorder=recorder,
    )
    manifest=serving_manifest(application,workload_id)
    if len(router.candidates)!=len(manifest):
        raise ValueError("serving router changed while telemetry bindings were created")
    candidate_bindings={
        id(candidate):(entry["surface_id"],entry["bundle_id"])
        for candidate,entry in zip(router.candidates,manifest)
    }
    telemetry_hook=StrandsServingTelemetryHook(
        recorder=recorder,
        workload_id=workload_id,
        candidate_bindings=candidate_bindings,
    )
    all_hooks=[telemetry_hook,*list(hooks or ())]
    return Agent(model=router,hooks=all_hooks,**agent_kwargs)
