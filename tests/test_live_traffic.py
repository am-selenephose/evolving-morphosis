import pytest

from morphosis.os.application import MorphosisApplication
from morphosis.os.deployment import TrafficPolicy
from morphosis.os.probes import LocalReferenceSandbox


def bootstrap_and_promote(app, model, endpoint="reference://echo"):
    surface=app.command("bootstrap",{
        "model":model,"provider":"reference","endpoint":endpoint,
        "claims":["future.semantic_patch.v1"],
    })
    app.command("evaluate",{"surface_id":surface["surface_id"]})
    bundle=app.command("bundle",{"surface_id":surface["surface_id"],"rollback":True})
    tid=bundle["transaction"]["transaction_id"]
    for _ in range(7):
        app.command("advance",{"transaction_id":tid})
    return surface,bundle


def start_upgrade(app, model, endpoint="reference://echo"):
    surface=app.command("bootstrap",{
        "model":model,"provider":"reference","endpoint":endpoint,
        "claims":["future.semantic_patch.v1"],
    })
    app.command("evaluate",{"surface_id":surface["surface_id"]})
    bundle=app.command("bundle",{"surface_id":surface["surface_id"],"rollback":True})
    tid=bundle["transaction"]["transaction_id"]
    for _ in range(4):
        tx=app.command("advance",{"transaction_id":tid})
    assert tx["stage"]=="SHADOW"
    return surface,bundle


def policy(**overrides):
    values={
        "enabled":True,"canary_fraction":1.0,"ramp_fraction":1.0,
        "min_shadow_samples":2,"min_canary_samples":2,"min_ramp_samples":2,
        "max_mismatch_rate":0.0,
    }
    values.update(overrides)
    return TrafficPolicy(**values)


def test_live_traffic_samples_gate_shadow_canary_and_ramp(tmp_path):
    app=MorphosisApplication(tmp_path/"traffic.db",traffic_policy=policy(),clock=lambda:"2026-09-22T00:00:00Z")
    first,_=bootstrap_and_promote(app,"incumbent","reference://native")
    second,bundle=start_upgrade(app,"candidate","reference://echo")
    tid=bundle["transaction"]["transaction_id"]

    with pytest.raises(ValueError,match="SHADOW requires 2 live traffic samples"):
        app.command("advance",{"transaction_id":tid})

    value={"tool":"search","arguments":{"query":"real traffic gate"}}
    one=app.command("serve",{"transaction_id":tid,"request_id":"shadow-1","value":value})
    two=app.command("serve",{"transaction_id":tid,"request_id":"shadow-2","value":value})
    assert one["output"]==two["output"]==value
    assert one["traffic"]["candidate_selected"] is False
    assert one["traffic"]["served_bundle"]!=bundle["bundle"]["bundle_id"]
    assert one["traffic"]["request_hash"]
    assert "value" not in one["traffic"]

    assert app.command("advance",{"transaction_id":tid})["stage"]=="CANARY"
    for i in range(2):
        result=app.command("serve",{"transaction_id":tid,"request_id":f"canary-{i}","value":value})
        assert result["traffic"]["candidate_selected"] is True
        assert result["traffic"]["served_bundle"]==bundle["bundle"]["bundle_id"]
        assert result["traffic"]["matched"] is True
    assert app.command("advance",{"transaction_id":tid})["stage"]=="RAMP"

    for i in range(2):
        result=app.command("serve",{"transaction_id":tid,"request_id":f"ramp-{i}","value":value})
        assert result["traffic"]["served_bundle"]==bundle["bundle"]["bundle_id"]
    assert app.command("advance",{"transaction_id":tid})["stage"]=="PROMOTED"
    snapshot=app.snapshot()
    assert len(snapshot["traffic_samples"])==6
    assert snapshot["deployment"]["active_bundle"]==bundle["bundle"]["bundle_id"]
    app.close()


class FailingCandidateExecutor(LocalReferenceSandbox):
    def __init__(self):
        super().__init__();self.fail_echo=False;self.last_latency=1.0;self.last_cost=0.0

    def execute(self,spec,transport,value):
        if self.fail_echo and transport=="json-text":
            raise ValueError("candidate runtime failure")
        return super().execute(spec,transport,value)

    def metrics(self,transport):
        return self.last_latency,self.last_cost

    def provenance(self,transport):
        return "live-traffic-test"


def test_canary_failure_serves_incumbent_and_blocks_progression(tmp_path):
    executor=FailingCandidateExecutor()
    app=MorphosisApplication(
        tmp_path/"fallback.db",traffic_policy=policy(min_shadow_samples=1,min_canary_samples=1,min_ramp_samples=1),
        executor=executor,clock=lambda:"2026-09-22T00:00:00Z"
    )
    bootstrap_and_promote(app,"incumbent","reference://native")
    _,bundle=start_upgrade(app,"candidate","reference://echo")
    tid=bundle["transaction"]["transaction_id"];value={"tool":"search","arguments":{"q":"fallback"}}

    app.command("serve",{"transaction_id":tid,"request_id":"shadow-ok","value":value})
    assert app.command("advance",{"transaction_id":tid})["stage"]=="CANARY"

    executor.fail_echo=True
    result=app.command("serve",{"transaction_id":tid,"request_id":"canary-fail","value":value})
    assert result["output"]==value
    assert result["traffic"]["fallback_used"] is True
    assert result["traffic"]["candidate_ok"] is False
    rolled=app.command("advance",{"transaction_id":tid})
    assert rolled["stage"]=="ROLLBACK"
    assert app.snapshot()["deployment"]["active_bundle"] is not None
    app.close()


def test_live_traffic_split_requires_incumbent_and_unique_request_id(tmp_path):
    app=MorphosisApplication(tmp_path/"first.db",traffic_policy=policy(min_shadow_samples=1,min_canary_samples=1,min_ramp_samples=1),clock=lambda:"2026-09-22T00:00:00Z")
    surface=app.command("bootstrap",{"model":"first","provider":"reference","endpoint":"reference://echo","claims":["future.semantic_patch.v1"]})
    app.command("evaluate",{"surface_id":surface["surface_id"]})
    bundle=app.command("bundle",{"surface_id":surface["surface_id"]})
    tid=bundle["transaction"]["transaction_id"]
    for _ in range(4):app.command("advance",{"transaction_id":tid})
    with pytest.raises(ValueError,match="requires a qualified incumbent"):
        app.command("serve",{"transaction_id":tid,"request_id":"x","value":{"tool":"x","arguments":{}}})
    # First deployment is not deadlocked by split policy because no incumbent exists.
    assert app.command("advance",{"transaction_id":tid})["stage"]=="CANARY"
    app.close()
