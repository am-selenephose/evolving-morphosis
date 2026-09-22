import asyncio
from types import SimpleNamespace

from morphosis.demo_model import DeterministicFutureModel
from morphosis.os.application import MorphosisApplication
from morphosis.os.serving import (
    MorphosisAdmissionStrategy,
    build_strands_model_router,
    serving_manifest,
)


def promote(app, model):
    surface=app.command("bootstrap",{
        "model":model,
        "provider":"reference",
        "endpoint":"reference://echo",
        "claims":["future.semantic_patch.v1"],
    })
    app.command("evaluate",{"surface_id":surface["surface_id"]})
    bundle=app.command("bundle",{"surface_id":surface["surface_id"],"rollback":True})
    tid=bundle["transaction"]["transaction_id"]
    for _ in range(7):
        app.command("advance",{"transaction_id":tid})
    return surface,bundle


def router_model(entry):
    model=DeterministicFutureModel({},entry["surface_id"])
    model.config={"model_id":"router-test-"+entry["surface_id"][:12]}
    return model


def test_serving_manifest_contains_only_current_active_and_qualified_fallback(tmp_path):
    app=MorphosisApplication(tmp_path/"serving.db",clock=lambda:"2026-09-22T00:00:00Z")
    first,_=promote(app,"first-qualified")
    second,_=promote(app,"second-qualified")
    manifest=serving_manifest(app,"tool-roundtrip")
    assert [row["surface_id"] for row in manifest]==[second["surface_id"],first["surface_id"]]
    assert [row["role"] for row in manifest]==["active","fallback"]
    assert all(row["qualification"]=="PROMOTE_TO_SHADOW" for row in manifest)
    app.close()


def test_strands_router_is_constructed_from_morphosis_admission_only(tmp_path):
    app=MorphosisApplication(tmp_path/"router.db",clock=lambda:"2026-09-22T00:00:00Z")
    first,_=promote(app,"first-qualified")
    second,_=promote(app,"second-qualified")
    router=build_strands_model_router(app,"tool-roundtrip",model_factory=router_model,max_switches=1)
    assert len(router.candidates)==2

    strategy=MorphosisAdmissionStrategy(
        app,
        "tool-roundtrip",
        (second["surface_id"],first["surface_id"]),
    )
    context=SimpleNamespace(candidates=router.candidates,attempts=())
    selected=asyncio.run(strategy.select(context))
    assert selected is router.candidates[0]

    # Drift revokes the current candidate and restores the previously qualified bundle.
    app.command("telemetry",{"surface_id":second["surface_id"],"schema_failures":1})
    selected_after_drift=asyncio.run(strategy.select(context))
    assert selected_after_drift is router.candidates[1]
    manifest=serving_manifest(app,"tool-roundtrip")
    assert [row["surface_id"] for row in manifest]==[first["surface_id"]]
    app.close()


def test_router_strategy_never_retries_attempted_or_revoked_candidate(tmp_path):
    app=MorphosisApplication(tmp_path/"attempts.db",clock=lambda:"2026-09-22T00:00:00Z")
    first,_=promote(app,"first-qualified")
    second,_=promote(app,"second-qualified")
    router=build_strands_model_router(app,"tool-roundtrip",model_factory=router_model,max_switches=1)
    strategy=MorphosisAdmissionStrategy(app,"tool-roundtrip",(second["surface_id"],first["surface_id"]))
    attempted=SimpleNamespace(candidate=router.candidates[0])
    context=SimpleNamespace(candidates=router.candidates,attempts=(attempted,))
    assert asyncio.run(strategy.select(context)) is router.candidates[1]

    app.command("telemetry",{"surface_id":first["surface_id"],"schema_failures":1})
    # first was fallback and is now stale; candidate zero is attempted, candidate one revoked.
    assert asyncio.run(strategy.select(context)) is None
    app.close()
