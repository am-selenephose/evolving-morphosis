"""Single application boundary used by HTTP, CLI, Strands and static export.

Candidate requests carry proposals and IDs only. Evidence, evaluator, contracts,
transport bindings and deployment checks are configured by the host, not requests.
"""
from __future__ import annotations
import json
from datetime import datetime,timedelta,timezone
from pathlib import Path
from uuid import uuid4
from .schemas import *
from .storage import SQLiteLedger
from .kernel import PolicyKernel
from .graph import CapabilityGraph,date
from .probes import ProbeSynthesizer,LocalReferenceSandbox,run_probe
from .compiler import compile_ir,verify_adapter
from .qualifier import qualify
from .deployment import ReferenceDeploymentController,STAGES


def utcnow():return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')

def fields(data,allowed,required=()):
    if not isinstance(data,dict) or set(data)-set(allowed):raise ValueError('unsupported command fields')
    if set(required)-set(data):raise ValueError('missing required command fields')


class MorphosisApplication:
    def __init__(self,path=':memory:',*,contract=None,clock=utcnow,executor=None,controller=None,transports=None,capability_contracts=None,contracts=None,discoverers=None):
        self.ledger=SQLiteLedger(path);self.clock=clock;self.kernel=PolicyKernel()
        self.executor=executor or LocalReferenceSandbox();self.controller=controller or ReferenceDeploymentController()
        installed={('reference','reference://echo'):'json-text',('reference','reference://native'):'native-json',('reference','reference://broken'):'broken-json'}
        installed.update(dict(transports or {}));self.transports=installed
        self.discoverers=dict(discoverers or {})
        self.graph=CapabilityGraph();self.synthesizer=ProbeSynthesizer()
        requested_contracts=tuple(contracts or ())
        self._contract=contract or (requested_contracts[0] if requested_contracts else WorkloadContract())
        self._capability_contracts=dict(capability_contracts or {'future.semantic_patch.v1':'json-patch-v1','core.tool_use.v1':'json-tool-v1'})
        if set(self._capability_contracts.values())-{'json-patch-v1','json-tool-v1'}:raise ValueError('semantic evaluator extension must be installed by host')
        # Persist host contract; reconnecting cannot silently revise its version/content.
        with self.ledger.transaction():
            existing=self.ledger.connection.execute("SELECT hash FROM artifacts WHERE hash=?",(self._contract.digest(),)).fetchone()
            contracts=self.ledger.replay().get('contracts',{})
            if contracts and self._contract.digest() not in contracts:
                if contract is not None:raise ValueError('persisted workload contract differs; explicit new store/version required')
                self._contract=WorkloadContract.model_validate(next(iter(contracts.values())))
            elif not existing:
                h=self.ledger.put(self._contract.json_value())
                self.ledger.append('WorkloadContractRegistered',h,{'message':'Host workload contract registered',
                    'mutation':{'collection':'contracts','id':h,'value':self._contract.json_value()}},self.clock(),'host-initialization',(h,))
            stored_defs=self.ledger.replay().get('definitions',{})
            if stored_defs:
                persisted={d['capability_id']:d['contract'] for d in stored_defs.values()}
                if capability_contracts is not None and persisted!=self._capability_contracts:raise ValueError('semantic contracts cannot change silently')
                self._capability_contracts=persisted
            else:
                for cap,semantic in self._capability_contracts.items():
                    definition=CapabilityDefinition(capability_id=cap,contract=semantic)
                    h=self.ledger.put(definition.json_value())
                    self.ledger.append('CapabilityDefinitionRegistered',h,{'message':'Host semantic evaluator contract registered',
                        'mutation':{'collection':'definitions','id':h,'value':definition.json_value()}},self.clock(),'host-initialization',(h,))
            for additional in requested_contracts:
                h=additional.digest()
                if h not in self.ledger.replay().get('contracts',{}):
                    prior=[c for c in self.ledger.replay().get('contracts',{}).values() if c['workload_id']==additional.workload_id and c['version']==additional.version]
                    if prior:raise ValueError('workload version already has different content')
                    self.ledger.put(additional.json_value())
                    self.ledger.append('WorkloadContractRegistered',h,{'message':'Host workload contract registered',
                        'mutation':{'collection':'contracts','id':h,'value':additional.json_value()}},self.clock(),'host-initialization',(h,))
        self._default_contract=self._contract

    def command(self,name,payload,command_id=None):
        if name.startswith('_') or name not in ('discover','bootstrap','evaluate','propose_probe','run_probe','compile','verify_adaptation','qualify','bundle','advance','rollback','telemetry','requalify'):
            raise ValueError('unknown application command')
        payload=json.loads(json.dumps(payload,allow_nan=False))
        command_id=command_id or str(uuid4());input_hash=digest([name,payload])
        with self.ledger.transaction():
            row=self.ledger.connection.execute('SELECT input_hash,result FROM commands WHERE id=?',(command_id,)).fetchone()
            if row:
                if row[0]!=input_hash:raise ValueError('command id reused with different input')
                return json.loads(row[1])
            self._state=self.ledger.replay();self._now=self.clock()
            # Correlation derives from command content and ledger position, preserving fixture replay.
            self._correlation=digest([input_hash,len(self.ledger.events())])
            self._contract=self._default_contract
            if 'workload_id' in payload:
                if name not in ('evaluate','qualify','bundle','requalify','propose_probe'):raise ValueError('command has no workload selector')
                workload_id=payload.pop('workload_id')
                matching=[c for c in self._state.get('contracts',{}).values() if c['workload_id']==workload_id]
                if len(matching)!=1:raise ValueError('workload selector missing or ambiguous')
                self._contract=WorkloadContract.model_validate(matching[0])
            if name in ('advance','rollback') and payload.get('transaction_id') in self._state.get('transactions',{}):
                selected=self._state['transactions'][payload['transaction_id']]
                self._contract=WorkloadContract.model_validate(self._state['bundles'][selected['bundle_id']]['workload_contract'])
            result=getattr(self,'_'+name)(payload)
            result=result.json_value() if isinstance(result,Record) else result
            self.ledger.connection.execute('INSERT INTO commands VALUES(?,?,?)',(command_id,input_hash,json.dumps(result,allow_nan=False)))
            return result

    def _emit(self,event_type,collection,key,value,message,evidence=()):
        value=value.json_value() if isinstance(value,Record) else value
        artifact=self.ledger.put(value)
        self.ledger.append(event_type,key,{'message':message,'mutation':{'collection':collection,'id':key,'value':value}},
            self._now,self._correlation,tuple(dict.fromkeys((artifact,*evidence))))
        self._state.setdefault(collection,{})[key]=value
        return value

    def _get(self,collection,key):
        try:return self._state[collection][key]
        except KeyError:raise ValueError(f'{collection} record not found') from None

    def _surface(self,key):return ModelSurface.model_validate(self._get('models',key))
    def _transport(self,surface):return self.transports.get((surface.provider,surface.endpoint))
    def _claims(self,sid):return [x for x in self._state.get('claims',{}).values() if x['surface_id']==sid]
    def _observations(self):return [CapabilityObservation.model_validate(x) for x in self._state.get('evidence',{}).values()]
    def _states(self,sid,now,workload_hash=None):
        invalid=self._state.get('requalifications',{}).get(sid)
        observations=self._observations()
        if workload_hash is not None:observations=[o for o in observations if o.workload_hash==workload_hash]
        if invalid:
            observations=[o for o in observations if o.surface_id!=sid or date(o.observed_at)>date(invalid['timestamp'])]
        return [self.graph.derive(sid,c['capability_id'],observations,now=now) for c in self._claims(sid)]

    def _register_discovered_surface(self,data,claim_source):
        allowed=('model','provider','endpoint','claims','api_surface','model_version','inference_config','tool_protocol')
        fields(data,allowed,('model','provider','endpoint','claims'))
        if not isinstance(data['claims'],(list,tuple)) or not 1<=len(data['claims'])<=100:
            raise ValueError('1–100 capability claims required')
        raw={k:v for k,v in data.items() if k!='claims'}
        raw.update(
            api_surface=data.get('api_surface','provider-catalog-v1'),
            adapter=None,
            model_version=data.get('model_version','unspecified'),
            inference_config=tuple(tuple(x) for x in data.get('inference_config',())),
            tool_protocol=data.get('tool_protocol','unbound'),
            lane='UNKNOWN_BOOTSTRAP',
        )
        sid=digest(raw);surface=ModelSurface(**raw,surface_id=sid,observed_at=self._now)
        if sid not in self._state.get('models',{}):
            self._emit('ProviderSurfaceDiscovered','models',sid,surface,f'{surface.model} discovered from {surface.provider} catalog')
        else:
            surface=self._surface(sid)
        for cap in data['claims']:
            claim=CapabilityClaim(surface_id=sid,capability_id=cap,source=claim_source)
            if claim.digest() not in self._state.get('claims',{}):
                self._emit('CapabilityClaimRegistered','claims',claim.digest(),claim,f'{surface.model}: {cap} is UNKNOWN / UNVERIFIED')
        return surface

    def _discover(self,data):
        fields(data,('provider',),('provider',))
        provider=data['provider']
        discoverer=self.discoverers.get(provider)
        if discoverer is None:
            raise ValueError(f'{provider} discoverer is not installed by host')
        records=discoverer.discover()
        if not isinstance(records,list) or len(records)>5000:
            raise ValueError('provider discovery returned invalid result set')
        surfaces=[]
        for record in records:
            if not isinstance(record,dict) or record.get('provider')!=provider:
                raise ValueError('provider discovery returned invalid candidate')
            surfaces.append(self._register_discovered_surface(record,'provider-catalog-metadata'))
        return [surface.json_value() for surface in surfaces]

    def _bootstrap(self,data):
        allowed=('model','provider','endpoint','claims','api_surface','model_version','inference_config','tool_protocol')
        fields(data,allowed,('model','provider','endpoint','claims'))
        if not isinstance(data['claims'],list) or not 1<=len(data['claims'])<=100:raise ValueError('1–100 capability claims required')
        from urllib.parse import urlparse
        endpoint=urlparse(data['endpoint'])
        if endpoint.scheme not in ('http','https','reference') or not endpoint.netloc or endpoint.username or endpoint.password:raise ValueError('credential-free endpoint required')
        known=data['model']=='reference-native' and data['provider']=='reference' and data['endpoint'] in ('reference://native','reference://echo')
        # The declared timestamp is evidence metadata, not part of stable surface identity.
        raw={k:v for k,v in data.items() if k!='claims'}
        raw.update(api_surface=data.get('api_surface','json-request-response-v1'),adapter='reference-json-v1' if known else None,
            model_version=data.get('model_version','unspecified'),inference_config=data.get('inference_config',()),tool_protocol=data.get('tool_protocol','json-tool-v1'),
            lane='KNOWN_FAST_PATH' if known else 'UNKNOWN_BOOTSTRAP')
        sid=digest(raw);surface=ModelSurface(**raw,surface_id=sid,observed_at=self._now)
        if sid not in self._state.get('models',{}):self._emit('CandidateBootstrapped','models',sid,surface,f'{surface.model} entered {surface.lane}')
        else:surface=self._surface(sid)
        for cap in data['claims']:
            claim=CapabilityClaim(surface_id=sid,capability_id=cap)
            if claim.digest() not in self._state.get('claims',{}):self._emit('CapabilityClaimRegistered','claims',claim.digest(),claim,f'{surface.model}: {cap} is UNKNOWN / UNVERIFIED')
        return surface

    def _propose_probe(self,data):
        fields(data,('surface_id','capability_id','family','timeout_ms','memory_mb','network','source_write','secrets','tools','filesystem','seed'),('surface_id','capability_id'))
        self._surface(data['surface_id'])
        if data['capability_id'] not in [c['capability_id'] for c in self._claims(data['surface_id'])]:raise ValueError('capability claim required')
        semantic=self._capability_contracts.get(data['capability_id'])
        if semantic is None:raise ValueError('no independent semantic contract for capability')
        spec=ProbeSpec(**data,probe_id=digest([data,'candidate-proposed']),source='candidate-proposed',input_contract=semantic,workload_hash=self._contract.digest())
        policy=self.kernel.probe(spec)
        if policy.outcome!='ALLOW_PROBE':raise ValueError('unsafe probe rejected before execution')
        return self._emit('ProbeAccepted','probes',spec.probe_id,spec,'Candidate probe accepted as supplemental evidence only')

    def _run_probe(self,data):
        fields(data,('probe_id',),('probe_id',))
        spec=ProbeSpec.model_validate(self._get('probes',data['probe_id']))
        if spec.workload_hash:
            self._contract=WorkloadContract.model_validate(self._get('contracts',spec.workload_hash))
        surface=self._surface(spec.surface_id);transport=self._transport(surface)
        if self._capability_contracts.get(spec.capability_id)!=spec.input_contract:raise ValueError('semantic evaluator contract mismatch')
        if transport is None:raise ValueError('no host-bound transport: claims remain unverified')
        if self.kernel.probe(spec).outcome!='ALLOW_PROBE':raise ValueError('probe denied')
        result=run_probe(spec,transport,self.executor,self._now)
        rh=self.ledger.put(result.json_value())
        self._emit('ProbeRunCompleted','probe_runs',result.run_id,result,f'{surface.model}: {spec.family} probe completed',(rh,))
        expiry=(date(self._now)+timedelta(seconds=self._contract.evidence_ttl_seconds)).isoformat().replace('+00:00','Z')
        obs=CapabilityObservation(sample_count=result.sample_count,passed_count=result.passed_count,workload_hash=self._contract.digest(),surface_id=surface.surface_id,capability_id=spec.capability_id,probe_id=spec.probe_id,run_id=result.run_id,
            family=spec.family,status='SUPPORTED' if result.passed else 'UNSUPPORTED',confidence=.99 if spec.source!='candidate-proposed' else .5,
            score=1 if result.passed else 0,observed_at=self._now,expires_at=expiry,
            source='independent-evaluator' if spec.source!='candidate-proposed' else 'candidate-proposed',evidence_hash=rh)
        self._emit('CapabilityObserved','evidence',obs.digest(),obs,f'{spec.capability_id}: {obs.status}',(rh,))
        return result

    def _compile(self,data):
        fields(data,('surface_id','nodes','mode','capability_id'),('surface_id',))
        sid=data['surface_id'];s=self._surface(sid)
        cap=data.get('capability_id',self._claims(sid)[0]['capability_id'])
        nodes=tuple(TransformNode.model_validate(n) for n in data.get('nodes',[{'op':'parse_json'}]))
        mode=data.get('mode','ADAPTED')
        if mode=='NATIVE':
            if self._transport(s)!='native-json' or not all(x.status=='SUPPORTED' for x in self._states(sid,self._now)):raise ValueError('native surface not evidenced')
        ir=MorphIR(surface_id=sid,capability_id=cap,mode=mode,nodes=nodes)
        compile_ir(ir)
        return self._emit('AdaptationCompiled','adaptations',sid,ir,f'{s.model}: {ir.mode} runtime adapter compiled')

    def _verify_adaptation(self,data):
        fields(data,('surface_id',),('surface_id',));sid=data['surface_id']
        surface=self._surface(sid);transport=self._transport(surface)
        if transport is None:raise ValueError('no host-bound transport')
        ir=MorphIR.model_validate(self._get('adaptations',sid))
        result=verify_adapter(ir,transport,self.executor,self._now)
        return self._emit('AdaptationVerified' if result.passed else 'AdaptationRejected','verifications',sid,result,
            f'{surface.model}: separate adaptation verification {"passed" if result.passed else "failed"}')

    def _qualify(self,data):
        fields(data,('surface_id',),('surface_id',));sid=data['surface_id'];surface=self._surface(sid)
        states=self._states(sid,self._now,self._contract.digest());by={c.capability_id:c for c in states}
        required=self._contract.required
        missing=[c for c in required if c not in by or by[c].status=='UNKNOWN']
        verification=self._state.get('verifications',{}).get(sid)
        adaptation=self._state.get('adaptations',{}).get(sid)
        adapter_matches=verification and adaptation and verification['adaptation_id']==MorphIR.model_validate(adaptation).digest()
        current=[by[c] for c in required if c in by]
        failure=any(x.status in ('UNSUPPORTED','DEGRADED','CONFLICTED') for x in current)
        selected_evidence={h for state in current for h in state.evidence}
        selected_runs={o.run_id for o in self._observations() if o.digest() in selected_evidence}
        runs=[x for x in self._state.get('probe_runs',{}).values() if x['run_id'] in selected_runs]
        latest={x['probe_id']:x for x in runs};runs=list(latest.values())
        check_map=dict(verification['checks']) if adapter_matches else {}
        m=ObjectiveMeasurements(safety=1 if check_map.get('security_boundary') and check_map.get('side_effect_free') else 0,
            determinism=1 if check_map.get('deterministic_replay') else 0,correctness=1 if check_map.get('semantic_preservation') else 0,quality=0 if failure else 1,confidence=min((x.confidence for x in current),default=0),
            latency_ms=sum(r['latency_ms'] for r in runs),cost_usd=sum(r['cost_usd'] for r in runs),
            reliability=0 if failure else 1,tool_fidelity=1 if not failure and check_map.get('tool_call_fidelity') else 0,
            adaptation_complexity=len(adaptation['nodes']) if adaptation else 0)
        evidence=tuple(sorted({h for x in current for h in x.evidence}))
        # Missing unbound evidence is HOLD, not a fabricated failed empirical run.
        if missing or not self._transport(surface):
            decision=QualificationDecision(outcome='HOLD',reasons=('MISSING_OR_STALE_EVIDENCE',),measurements=m,evidence=evidence,
                uncertainty=1-m.confidence,regression=0,workload_version=self._contract.version)
        else:
            decision=qualify(self._contract,m,evidence,adapter_passed=bool(adapter_matches and verification['passed']),
                provider_allowed=surface.provider in self._contract.allowed_providers)
        value={**decision.json_value(),'surface_id':sid,'workload_id':self._contract.workload_id}
        self._emit('WorkloadQualificationRecorded','workload_qualifications',sid+':'+self._contract.digest(),value,f'Workload-scoped decision: {self._contract.workload_id}')
        return self._emit('QualificationCompleted','qualifications',sid,value,f'{surface.model}: {decision.outcome}')

    def _evaluate(self,data):
        fields(data,('surface_id',),('surface_id',));sid=data['surface_id'];surface=self._surface(sid)
        if self._transport(surface) is None:
            return {'surface_id':sid,'decision':self._qualify(data),'probe_runs':[],'adaptation':None,'adaptation_verification':None}
        runs=[]
        for claim in self._claims(sid):
            semantic=self._capability_contracts.get(claim['capability_id'])
            if semantic is None:continue
            for spec in self.synthesizer.synthesize(sid,claim['capability_id'],semantic,self._contract.digest()):
                self._emit('ProbeProposed','probes',spec.probe_id,spec,f'{surface.model}: independent {spec.family} probe synthesized')
                runs.append(self._run_probe({'probe_id':spec.probe_id}).json_value())
        if not runs:return {'surface_id':sid,'decision':self._qualify(data),'probe_runs':[],'adaptation':None,'adaptation_verification':None}
        native=self._transport(surface)=='native-json'
        ir=self._compile({'surface_id':sid,'mode':'NATIVE' if native else 'ADAPTED','nodes':[] if native else [{'op':'parse_json'}]})
        verification=self._verify_adaptation(data)
        decision=self._qualify(data)
        return {'surface_id':sid,'decision':decision,'probe_runs':runs,'adaptation':ir,'adaptation_verification':verification}

    def _bundle(self,data):
        fields(data,('surface_id','source_patch','rollback'),('surface_id',));sid=data['surface_id'];self._surface(sid)
        if not isinstance(data.get('rollback',True),bool):raise ValueError('rollback must be boolean')
        if data.get('source_patch') is not None and (not isinstance(data['source_patch'],str) or len(data['source_patch'])>65536):raise ValueError('source proposal too large')
        result=self._qualify({'surface_id':sid})
        decision=QualificationDecision.model_validate({k:v for k,v in result.items() if k not in ('surface_id','workload_id')})
        verification=AdaptationVerification.model_validate(self._get('verifications',sid))
        ir=MorphIR.model_validate(self._get('adaptations',sid))
        deployment=self._state.get('deployment',{}).get('current',DeploymentState().json_value());prior=deployment['active_bundle']
        rollback=('restore:'+prior if prior else 'restore:empty-qualified-pool') if data.get('rollback',True) else ''
        policy=self.kernel.evolution(decision,verification,source_patch=data.get('source_patch'),rollback=rollback,contract=self._contract)
        probes=[r for r in self._state.get('probe_runs',{}).values() if r['surface_id']==sid]
        artifact_hashes=tuple(self.ledger.put(x) for x in [ir.json_value(),verification.json_value(),decision.json_value(),policy.json_value()])
        kwargs=dict(surface_id=sid,workload_contract=self._contract,parent_revisions=(prior,) if prior else (),capability_evidence=decision.evidence,
            probe_runs=tuple(sorted(self.ledger.put(x) for x in probes)),adaptation=ir,adaptation_verification=verification,qualification=decision,policy=policy,
            runtime_changes=(('adapter_hash',ir.digest()),),source_patch=data.get('source_patch'),rollback_recipe=rollback,dependencies=(self._contract.digest(),),
            artifact_hashes=artifact_hashes,created_at=self._now)
        provisional=EvolutionBundle(bundle_id='',**kwargs);bid=digest(provisional.model_dump(mode='json',exclude={'bundle_id'}))
        bundle=EvolutionBundle(bundle_id=bid,**kwargs)
        self._emit('EvolutionBundleCreated','bundles',bid,bundle,f'Evolution Bundle v3 {bid[:12]} created',artifact_hashes)
        tx=EvolutionTransaction(transaction_id=digest([bid,'transaction']),bundle_id=bid,previous_bundle=prior)
        self._emit('EvolutionTransactionAdvanced','transactions',tx.transaction_id,tx,'Evolution transaction PROPOSED')
        return {'bundle':bundle.json_value(),'transaction':tx.json_value()}

    def _valid_bundle(self,bundle):
        if digest(bundle.model_dump(mode='json',exclude={'bundle_id'}))!=bundle.bundle_id:raise ValueError('bundle tampered')
        for h in (*bundle.capability_evidence,*bundle.probe_runs,*bundle.artifact_hashes,*bundle.dependencies):self.ledger.get(h)
        if bundle.source_patch is not None or bundle.policy.outcome!='AUTO_APPLY_RUNTIME':raise ValueError('bundle not authorized for runtime auto-apply')
        if not bundle.rollback_recipe:raise ValueError('rollback required')
        current=self._qualify({'surface_id':bundle.surface_id})
        if current['outcome']!='PROMOTE_TO_SHADOW':raise ValueError('current evidence no longer qualifies')
        if tuple(current['evidence'])!=bundle.capability_evidence:raise ValueError('bundle evidence differs from current qualification')
        if not bundle.adaptation_verification.passed or bundle.adaptation_verification.adaptation_id!=bundle.adaptation.digest():raise ValueError('bundle adapter unverified')

    def _advance(self,data):
        fields(data,('transaction_id',),('transaction_id',));tid=data['transaction_id']
        tx=EvolutionTransaction.model_validate(self._get('transactions',tid))
        if tx.stage not in STAGES or tx.stage=='PROMOTED':raise ValueError('transaction is terminal')
        bundle=EvolutionBundle.model_validate(self._get('bundles',tx.bundle_id));self._valid_bundle(bundle)
        deployment=self._state.get('deployment',{}).get('current',DeploymentState().json_value())
        if deployment['active_bundle']!=tx.previous_bundle:raise ValueError('incumbent changed; transaction must be rebased')
        target=STAGES[STAGES.index(tx.stage)+1]
        checks=tx.checks
        if target in ('SANDBOXED','SHADOW','CANARY','RAMP','PROMOTED'):
            surface=self._surface(bundle.surface_id);transport_name=self._transport(surface)
            spec=ProbeSpec(probe_id='deployment-reference',surface_id=surface.surface_id,capability_id=bundle.adaptation.capability_id)
            def transport(value):return self.executor.execute(spec,transport_name,value)
            record=self.controller.check(bundle,target,compile_ir(bundle.adaptation),transport)
            h=self.ledger.put(record);checks=(*checks,h)
            self._emit('DeploymentCheckCompleted','deployment_checks',h,record,f'{target}: independent reference deployment check')
            if not record['passed']:return self._rollback({'transaction_id':tid},reason=f'{target}_FAILED')
        updated=EvolutionTransaction(transaction_id=tid,bundle_id=tx.bundle_id,stage=target,previous_bundle=tx.previous_bundle,checks=checks)
        event={'SHADOW':'ShadowStarted','CANARY':'CanaryStarted','PROMOTED':'CandidatePromoted'}.get(target,'EvolutionTransactionAdvanced')
        self._emit(event,'transactions',tid,updated,f'Transaction advanced to {target}')
        if target=='PROMOTED':
            dep=DeploymentState(active_bundle=tx.bundle_id,fallback_bundle=tx.previous_bundle,admitted=(bundle.surface_id,))
            self._emit('RoutingAdmissionGranted','deployment','current',dep,'Verified reference bundle admitted to workload routing pool')
        return updated

    def _rollback(self,data,reason='OPERATOR_ROLLBACK'):
        fields(data,('transaction_id',),('transaction_id',));tid=data['transaction_id'];tx=EvolutionTransaction.model_validate(self._get('transactions',tid))
        if tx.stage in ('ROLLBACK','REJECT'):raise ValueError('transaction already terminal')
        updated=EvolutionTransaction(transaction_id=tid,bundle_id=tx.bundle_id,stage='ROLLBACK',previous_bundle=tx.previous_bundle,checks=tx.checks)
        self._emit('RollbackStarted','transactions',tid,updated,f'Rollback requested: {reason}')
        current=self._state.get('deployment',{}).get('current',DeploymentState().json_value())
        # A stale rollback cannot overwrite a newer incumbent.
        if current['active_bundle']==tx.bundle_id:
            prior=self._state.get('bundles',{}).get(tx.previous_bundle)
            restore_id=tx.previous_bundle
            if prior:
                prior_transactions=[t for t in self._state.get('transactions',{}).values() if t['bundle_id']==restore_id]
                prior_qualification=self._qualify({'surface_id':prior['surface_id']})
                if prior_qualification['outcome']!='PROMOTE_TO_SHADOW' or any(t['stage'] in ('ROLLBACK','REJECT') for t in prior_transactions):
                    prior=None;restore_id=None
            admitted=(prior['surface_id'],) if prior else ()
            dep=DeploymentState(active_bundle=restore_id,admitted=admitted)
            self._emit('RoutingAdmissionRevoked','deployment','current',dep,'Previous qualified revision restored')
        self._emit('RollbackCompleted','transactions',tid,updated,f'Rollback completed: {reason}')
        self._emit('FailureArchived','archive',digest([tid,reason]),{'transaction_id':tid,'reason':reason,'bundle_id':tx.bundle_id},'Failure recorded for future proposal retrieval')
        return updated

    def _telemetry(self,data):
        t=TelemetryEvent.model_validate(data);surface=self._surface(t.surface_id)
        self._emit('TelemetryObserved','telemetry',t.digest(),t,'Telemetry recorded (caller-reported signal; never promotion proof)')
        reasons=[]
        if t.schema_failures:reasons.append('SCHEMA_FAILURE')
        if t.tool_failures:reasons.append('TOOL_FAILURE')
        if t.policy_failures:reasons.append('POLICY_FAILURE')
        if t.latency_ms>self._contract.max_latency_ms:reasons.append('LATENCY_DRIFT')
        if t.cost_usd>self._contract.max_cost_usd:reasons.append('COST_DRIFT')
        if self._contract.incumbent_quality-t.quality>self._contract.max_regression:reasons.append('QUALITY_DRIFT')
        if t.fingerprint and t.fingerprint!=surface.surface_id:reasons.append('SURFACE_CHANGED')
        if reasons:return self._request_requalification(t.surface_id,tuple(reasons))
        return {'surface_id':t.surface_id,'required':False,'capabilities':[]}

    def _request_requalification(self,sid,reasons):
        self._surface(sid)
        record={'surface_id':sid,'required':True,'reasons':list(reasons),'capabilities':[c['capability_id'] for c in self._claims(sid)],'timestamp':self._now}
        self._emit('DriftDetected','requalifications',sid,record,'Evidence invalidated: '+', '.join(reasons))
        current=self._state.get('deployment',{}).get('current',DeploymentState().json_value())
        active=self._state.get('bundles',{}).get(current['active_bundle'])
        if active and active['surface_id']==sid:
            for t in list(self._state.get('transactions',{}).values()):
                if t['bundle_id']==active['bundle_id'] and t['stage']=='PROMOTED':self._rollback({'transaction_id':t['transaction_id']},reason='REQUALIFICATION_REQUIRED')
        self._emit('RequalificationRequested','requalifications',sid,record,'Targeted probes required for changed or degraded surface')
        return record

    def _requalify(self,data):
        fields(data,('surface_id',),('surface_id',));sid=data['surface_id']
        self._request_requalification(sid,('OPERATOR_REQUEST',))
        # Evidence is a new qualification epoch, even with a deterministic clock.
        self._now=(date(self._now)+timedelta(microseconds=1)).isoformat().replace('+00:00','Z')
        return self._evaluate({'surface_id':sid})

    def events(self,after=0):return self.ledger.events(after)
    def close(self):self.ledger.close()
    def health(self):return self.ledger.health()
    def revision(self,bundle_id):
        with self.ledger.lock:
            state=self.ledger.replay()
            if bundle_id not in state.get('bundles',{}):raise ValueError('revision not found')
            return state['bundles'][bundle_id]

    def snapshot(self):
        with self.ledger.lock:
            self._state=self.ledger.replay();now=self.clock()
            events=self.ledger.events();collections=('evidence','probes','probe_runs','adaptations','verifications','qualifications','bundles','transactions','telemetry','requalifications','contracts')
            result={name:list(self._state.get(name,{}).values()) for name in collections}
            models=[];capabilities=[]
            for sid,surface in self._state.get('models',{}).items():
                states=self._states(sid,now);capabilities.extend(c.json_value() for c in states)
                qual=self._state.get('qualifications',{}).get(sid)
                txs=[t for t in result['transactions'] if self._state['bundles'][t['bundle_id']]['surface_id']==sid]
                status=txs[-1]['stage'] if txs else qual['outcome'] if qual else 'UNKNOWN'
                if not states or any(c.status=='UNKNOWN' for c in states):status='UNKNOWN'
                models.append({**surface,'status':status,'capabilities':[c.capability_id for c in states]})
            counts=[('Probes',len(result['probe_runs'])),('Verification',len(result['verifications'])),('Qualification',len(result['qualifications'])),
                ('Deployment',len(self._state.get('deployment_checks',{}))),('Discovery',len(models))]
            total=sum(n for _,n in counts)
            result.update(schema_version='3.0',mode='EVOLUTION OS',sequence=events[-1]['sequence'] if events else 0,
                ledger_head=events[-1]['event_hash'] if events else '0'*64,models=models,capabilities=capabilities,events=events,
                deployment=self._state.get('deployment',{}).get('current',DeploymentState().json_value()),
                metrics={'surfaces':len(models),'evidence':len(result['evidence']),'contracts':len(result['contracts'])},
                workload=[{'name':name,'count':n,'percent':round(n/total*100) if total else 0} for name,n in counts],
                agents=[{'name':'Morphosis Orchestrator','role':'Proposes commands through shared Strands tools','status':'CANONICAL TOOL LOOP','implementation':'src/morphosis/os/agents.py'},
                    {'name':'Opportunity Workload','role':'Evidence-backed opportunity triage with human action gates','status':'CANONICAL WORKLOAD','implementation':'src/actionqueue/agent.py'}],
                pipeline=[{'name':name,'description':desc,'status':'ACTIVE'} for name,desc in [('DISCOVER','Surface + claims'),('PROVE','Independent probes'),('MORPH','Verify adapter'),('GATE','Contract + kernel'),('SERVE','Shadow · canary · promote')]])
            from .topology import topology
            result['architecture']=topology(result)
            root=Path(__file__).resolve().parents[3]
            result['datasets']=[]
            for path in sorted((root/'fixtures').glob('*.json')):
                value=json.loads(path.read_text());result['datasets'].append({'name':path.name,'kind':'Synthetic repository fixture','hash':digest(value),'preview':value})
            return result
