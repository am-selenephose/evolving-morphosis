"""V3 authority tests exercise real service commands and persisted replay."""
import asyncio
import importlib.util
import json
import sqlite3
from pathlib import Path

import pytest


def api():
    assert importlib.util.find_spec('morphosis.os') is not None, 'V3 canonical application is missing'
    from morphosis.os.application import MorphosisApplication
    return MorphosisApplication


def app(tmp_path):
    return api()(tmp_path / 'state.sqlite', clock=lambda: '2026-09-15T00:00:00Z')


def bootstrap(a, **overrides):
    return a.command('bootstrap', {'model':'future-model-x','provider':'reference','endpoint':'reference://echo',
        'claims':['future.semantic_patch.v1'], **overrides})


def proven(a, **overrides):
    s=bootstrap(a, **overrides)
    result=a.command('evaluate', {'surface_id':s['surface_id']})
    return s, result


def test_v3_service_exists():
    api()


def test_arbitrary_claims_stay_unknown_and_surface_fingerprint_scoped(tmp_path):
    a=app(tmp_path)
    claims=[f'vendor.2030.feature_{i}.v1' for i in range(40)]
    one=bootstrap(a, claims=claims)
    two=bootstrap(a, endpoint='reference://other')
    assert one['surface_id'] != two['surface_id']
    states=a.snapshot()['capabilities']
    assert len(states)==41 and all(x['status']=='UNKNOWN' for x in states)


def test_known_fast_path_and_unknown_path_converge(tmp_path):
    a=app(tmp_path)
    assert bootstrap(a,model='reference-native')['lane']=='KNOWN_FAST_PATH'
    assert bootstrap(a)['lane']=='UNKNOWN_BOOTSTRAP'


@pytest.mark.parametrize('key,value',[('policy',{'allow_source':True}),('observations',[{'passed':True}]),
    ('evaluator','candidate'),('secrets',['TOKEN']),('approval','AUTO_APPLY_RUNTIME')])
def test_candidate_cannot_write_authority(tmp_path,key,value):
    a=app(tmp_path)
    before=a.snapshot()
    with pytest.raises(ValueError): bootstrap(a,**{key:value})
    assert a.snapshot()==before


def test_unbound_provider_does_not_become_observed(tmp_path):
    a=app(tmp_path); s=bootstrap(a,provider='future-real-provider',endpoint='https://future.invalid/v1')
    r=a.command('evaluate',{'surface_id':s['surface_id']})
    assert r['decision']['outcome']=='HOLD'
    assert all(x['status']=='UNKNOWN' for x in a.snapshot()['capabilities'])


def test_multiple_independent_probes_and_separate_adapter_proof(tmp_path):
    a=app(tmp_path); s,r=proven(a)
    assert len(r['probe_runs']) >= 2
    assert r['adaptation_verification']['passed']
    assert r['adaptation']['mode']=='ADAPTED'
    assert r['decision']['outcome']=='PROMOTE_TO_SHADOW'
    assert len({p['family'] for p in r['probe_runs']})>=2
    assert a.snapshot()['capabilities'][0]['status']=='SUPPORTED'


@pytest.mark.parametrize('field,value',[('network',True),('secrets',('TOKEN',)),('source_write',True),('timeout_ms',0),('memory_mb',0)])
def test_unsafe_probe_rejected_before_execution(tmp_path,field,value):
    a=app(tmp_path); s=bootstrap(a)
    with pytest.raises(ValueError):
        a.command('propose_probe', {'surface_id':s['surface_id'],'capability_id':'future.semantic_patch.v1',field:value})
    assert not a.snapshot()['probe_runs']


def test_candidate_probe_alone_cannot_certify(tmp_path):
    a=app(tmp_path); s=bootstrap(a)
    p=a.command('propose_probe',{'surface_id':s['surface_id'],'capability_id':'future.semantic_patch.v1'})
    a.command('run_probe',{'probe_id':p['probe_id']})
    assert a.snapshot()['capabilities'][0]['confidence'] < .9


def test_evidence_expiry_and_surface_separation(tmp_path):
    a=app(tmp_path); s,r=proven(a)
    bootstrap(a,endpoint='reference://other')
    a.clock=lambda:'2027-01-01T00:00:00Z'
    assert all(x['status']=='UNKNOWN' for x in a.snapshot()['capabilities'])
    assert a.command('qualify',{'surface_id':s['surface_id']})['outcome']=='HOLD'


def test_graph_conflicts_dependencies_and_tamper_validation():
    api()
    from morphosis.os.graph import CapabilityGraph
    from morphosis.os.schemas import CapabilityObservation
    g=CapabilityGraph()
    base=dict(surface_id='s',capability_id='x.new.v1',probe_id='p1',run_id='r1',family='roundtrip',
              status='SUPPORTED',confidence=.9,score=1,observed_at='2026-09-15T00:00:00Z',expires_at='2026-09-16T00:00:00Z')
    first=CapabilityObservation(**base); second=CapabilityObservation(**{**base,'probe_id':'p2','run_id':'r2','status':'UNSUPPORTED'})
    state=g.derive('s','x.new.v1',[first,second],now='2026-09-15T01:00:00Z')
    assert state.status=='CONFLICTED'
    assert g.derive('other','x.new.v1',[first],now='2026-09-15T01:00:00Z').status=='UNKNOWN'
    assert first.digest()!=second.digest()
    with pytest.raises(Exception): first.status='SUPPORTED'


@pytest.mark.parametrize('budget,value,reason',[('max_cost_usd',0,'COST_BUDGET'),('max_latency_ms',0,'LATENCY_BUDGET')])
def test_budget_failure_blocks_promotion(tmp_path,budget,value,reason):
    api()
    from morphosis.os.schemas import WorkloadContract
    a=api()(tmp_path/'s.db',contract=WorkloadContract(**{budget:value}),clock=lambda:'2026-09-15T00:00:00Z')
    _,r=proven(a)
    assert r['decision']['outcome']=='REJECT' and reason in r['decision']['reasons']


def test_hard_invariant_dominates_quality():
    api()
    from morphosis.os.qualifier import qualify
    from morphosis.os.schemas import WorkloadContract, ObjectiveMeasurements
    r=qualify(WorkloadContract(),ObjectiveMeasurements(quality=1,safety=0,confidence=1),(),adapter_passed=True)
    assert r.outcome=='REJECT' and 'HARD_INVARIANT' in r.reasons


def test_uncertainty_holds():
    api()
    from morphosis.os.qualifier import qualify
    from morphosis.os.schemas import WorkloadContract, ObjectiveMeasurements
    assert qualify(WorkloadContract(),ObjectiveMeasurements(confidence=.4),(),adapter_passed=True).outcome=='HOLD'


def test_compiler_executes_transform_and_rejects_source():
    api()
    from morphosis.os.compiler import compile_ir
    from morphosis.os.schemas import MorphIR, TransformNode
    ir=MorphIR(surface_id='s',capability_id='x.y.v1',nodes=(TransformNode(op='parse_json'),))
    adapter=compile_ir(ir)
    assert adapter('{"tool":"search","arguments":{"q":"evidence"}}')['tool']=='search'
    with pytest.raises(ValueError): compile_ir(MorphIR(surface_id='s',capability_id='x.y.v1',nodes=(TransformNode(op='eval'),)))


def test_bad_adaptation_separately_fails(tmp_path):
    a=app(tmp_path); s,r=proven(a)
    a.command('compile',{'surface_id':s['surface_id'],'nodes':[{'op':'identity'}]})
    r=a.command('verify_adaptation',{'surface_id':s['surface_id']})
    assert not r['passed']
    assert a.command('qualify',{'surface_id':s['surface_id']})['outcome']=='REJECT'
    assert a.snapshot()['capabilities'][0]['status']=='SUPPORTED'


def transaction(a,source_patch=None,rollback=True):
    s,r=proven(a)
    return a.command('bundle',{'surface_id':s['surface_id'],'source_patch':source_patch,'rollback':rollback})


def test_source_patch_never_auto_applies(tmp_path):
    a=app(tmp_path); b=transaction(a,source_patch='proposed diff')
    assert b['bundle']['policy']['outcome']=='REQUIRE_HUMAN_APPROVAL'
    with pytest.raises(ValueError): a.command('advance',{'transaction_id':b['transaction']['transaction_id']})
    assert a.snapshot()['deployment']['active_bundle'] is None


def test_no_rollback_blocks_runtime(tmp_path):
    a=app(tmp_path); b=transaction(a,rollback=False)
    assert b['bundle']['policy']['outcome']=='HOLD'


def test_transaction_promotes_only_after_real_stage_checks_and_reconstructs(tmp_path):
    a=app(tmp_path); b=transaction(a); tid=b['transaction']['transaction_id']
    seen=[]
    for _ in range(7):
        t=a.command('advance',{'transaction_id':tid}); seen.append(t['stage'])
    assert seen==['VALIDATED','SANDBOXED','QUALIFIED','SHADOW','CANARY','RAMP','PROMOTED']
    assert a.snapshot()['deployment']['active_bundle']==b['bundle']['bundle_id']
    assert a.ledger.verify()
    reopened=api()(tmp_path/'state.sqlite',clock=a.clock)
    assert reopened.snapshot()==a.snapshot()
    assert reopened.revision(b['bundle']['bundle_id'])==b['bundle']


@pytest.mark.parametrize('stage',['SHADOW','CANARY'])
def test_failed_deployment_preserves_incumbent_and_records_rollback(tmp_path,stage):
    api()
    from morphosis.os.deployment import ReferenceDeploymentController
    class FailingController(ReferenceDeploymentController):
        def check(self,bundle,at_stage,adapter,transport):
            record=super().check(bundle,at_stage,adapter,transport)
            return {**record,'passed':False} if at_stage==stage else record
    a=api()(tmp_path/'s.db',controller=FailingController(),clock=lambda:'2026-09-15T00:00:00Z')
    b=transaction(a); tid=b['transaction']['transaction_id']
    for _ in range(7):
        t=a.command('advance',{'transaction_id':tid})
        if t['stage']=='ROLLBACK':break
    assert t['stage']=='ROLLBACK' and a.snapshot()['deployment']['active_bundle'] is None
    assert any(e['event_type']=='RollbackCompleted' for e in a.events())


def test_client_cannot_supply_passed_stage_or_incumbent(tmp_path):
    a=app(tmp_path); b=transaction(a)
    with pytest.raises(ValueError): a.command('advance',{'transaction_id':b['transaction']['transaction_id'],'passed':True})


def test_drift_removes_routing_admission_and_triggers_requalification(tmp_path):
    a=app(tmp_path); b=transaction(a); tid=b['transaction']['transaction_id']
    for _ in range(7):a.command('advance',{'transaction_id':tid})
    sid=b['bundle']['surface_id']
    r=a.command('telemetry',{'surface_id':sid,'schema_failures':1,'latency_ms':20,'fingerprint':'changed'})
    assert r['required'] and r['capabilities']
    assert a.snapshot()['deployment']['active_bundle'] is None
    assert any(x['event_type']=='RequalificationRequested' for x in a.events())


def test_bundles_and_export_are_deterministic(tmp_path):
    a=app(tmp_path); b=transaction(a)
    other=api()(tmp_path/'other.db',clock=a.clock); c=transaction(other)
    assert b['bundle']==c['bundle']


def test_ledger_detects_tampering(tmp_path):
    a=app(tmp_path); bootstrap(a)
    con=sqlite3.connect(tmp_path/'state.sqlite')
    con.execute("UPDATE events SET body='{}' WHERE sequence=1");con.commit();con.close()
    assert not a.ledger.verify()
    with pytest.raises(ValueError): a.snapshot()


def test_command_idempotency_and_event_replay(tmp_path):
    a=app(tmp_path); payload={'model':'x','provider':'reference','endpoint':'reference://echo','claims':['x.y.v1']}
    x=a.command('bootstrap',payload,command_id='one'); n=len(a.events())
    assert a.command('bootstrap',payload,command_id='one')==x and len(a.events())==n
    with pytest.raises(ValueError):a.command('bootstrap',{**payload,'model':'different'},command_id='one')
    assert [e['sequence'] for e in a.events()]==list(range(1,n+1))
    assert len({e['event_id'] for e in a.events()})==n


def test_unknown_semantics_cannot_be_certified_by_generic_echo(tmp_path):
    a=app(tmp_path);s=bootstrap(a,claims=['vendor.2030.cure_all.v1'])
    result=a.command('evaluate',{'surface_id':s['surface_id']})
    assert result['decision']['outcome']=='HOLD'
    assert a.snapshot()['capabilities'][0]['status']=='UNKNOWN'
    assert not a.snapshot()['probe_runs']


def test_semantic_patch_probe_applies_actual_patch_instead_of_echo():
    api()
    from morphosis.os.probes import corpus,expected_output
    value=corpus('roundtrip',17,'json-patch-v1')
    assert value['document'] != expected_output(value,'json-patch-v1')
    assert expected_output(value,'json-patch-v1')['status']=='evolved'


def test_rollback_does_not_restore_invalidated_prior(tmp_path):
    a=app(tmp_path)
    first=transaction(a);tid=first['transaction']['transaction_id']
    for _ in range(7):a.command('advance',{'transaction_id':tid})
    prior_sid=first['bundle']['surface_id']
    s=bootstrap(a,model='next-model');a.command('evaluate',{'surface_id':s['surface_id']})
    second=a.command('bundle',{'surface_id':s['surface_id']});tid2=second['transaction']['transaction_id']
    for _ in range(7):a.command('advance',{'transaction_id':tid2})
    a.command('telemetry',{'surface_id':prior_sid,'schema_failures':1})
    a.command('rollback',{'transaction_id':tid2})
    assert a.snapshot()['deployment']['active_bundle'] is None


def test_hard_invariants_require_evaluator_check_records(tmp_path):
    a=app(tmp_path);s,r=proven(a)
    assert r['adaptation_verification']['checks']
    assert r['decision']['measurements']['safety']==1
    # A new transform invalidates the previously observed verification identity.
    a.command('compile',{'surface_id':s['surface_id'],'nodes':[{'op':'identity'}]})
    decision=a.command('qualify',{'surface_id':s['surface_id']})
    assert decision['measurements']['safety']==0
    assert decision['measurements']['determinism']==0


def test_workload_evidence_is_not_automatic_proof_for_second_contract(tmp_path):
    from morphosis.os.schemas import WorkloadContract
    one=WorkloadContract();two=WorkloadContract(workload_id='strict-workload',version='3.1')
    a=api()(tmp_path/'multi.db',contracts=(one,two),clock=lambda:'2026-09-15T00:00:00Z')
    s,r=proven(a)
    assert a.command('qualify',{'surface_id':s['surface_id'],'workload_id':'strict-workload'})['outcome']=='HOLD'
    second=a.command('evaluate',{'surface_id':s['surface_id'],'workload_id':'strict-workload'})
    assert second['decision']['outcome']=='PROMOTE_TO_SHADOW'
    assert len(a.snapshot()['contracts'])==2


def test_host_can_register_new_namespace_with_explicit_semantic_contract(tmp_path):
    from morphosis.os.schemas import WorkloadContract
    cap='vendor.2030.transform.v7'
    a=api()(tmp_path/'novel.db',contract=WorkloadContract(required=(cap,)),capability_contracts={cap:'json-patch-v1'},clock=lambda:'2026-09-15T00:00:00Z')
    s=bootstrap(a,claims=[cap]);r=a.command('evaluate',{'surface_id':s['surface_id']})
    assert r['decision']['outcome']=='PROMOTE_TO_SHADOW'


def test_qualified_router_executes_compiled_admitted_adapter(tmp_path):
    from morphosis.os.deployment import QualifiedRouter
    a=app(tmp_path);b=transaction(a)
    for _ in range(7):a.command('advance',{'transaction_id':b['transaction']['transaction_id']})
    value={'tool':'search','arguments':{'query':'shared authority'}}
    assert QualifiedRouter(a).invoke('tool-roundtrip',value)==value


def test_qualification_confidence_is_derived_from_sample_counts(tmp_path):
    a=app(tmp_path);s,result=proven(a)
    assert sum(r['sample_count'] for r in result['probe_runs'])>=48
    confidence=result['decision']['measurements']['confidence']
    assert .90<confidence<.99
    assert all(r['passed_count']==r['sample_count'] for r in result['probe_runs'])
