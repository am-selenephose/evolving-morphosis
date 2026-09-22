"""Policy-gated Strands model routing built only from Morphosis admissions.

Strands may choose/fail over within the immutable router candidate set, but this
strategy revalidates Morphosis admission before every selection so stale or
revoked candidates cannot be resurrected by router health history.
"""
from __future__ import annotations

from dataclasses import dataclass
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

    async def select(self, context, **kwargs):
        allowed={row["surface_id"] for row in serving_manifest(self.application,self.workload_id)}
        attempted={id(attempt.candidate) for attempt in context.attempts}
        if len(context.candidates)!=len(self.surface_ids):
            raise ValueError("Strands router candidate set diverged from Morphosis admission manifest")
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
    )
    return ModelRouter(models=models,strategy=strategy,max_switches=max_switches)
