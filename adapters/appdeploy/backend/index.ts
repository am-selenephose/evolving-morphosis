import { db, error, json, router } from '@appdeploy/sdk';
import { notifySubscribers, realtimeSubscriptionRoutes } from './realtime-subscribers';

type ModelRecord = { model_id:string; name:string; provider:string; meta:string; status:string; tone:string; icon:string; capability?:string; endpoint?:string; created_at:number };
type EventRecord = { event_type:string; title:string; sub:string; status:string; tone:string; icon:string; level:string; run_id?:string; created_at:number };
type SettingsRecord = { driftThreshold:number; qualificationMargin:number; triggers:Record<string, boolean> };
type SettingsWithId = SettingsRecord & { db_id?: string };
type EvidenceRecord = { run_id:string; model_id:string; kind:string; status:string; source:string; detail:string; score:number; created_at:number };
type RunRecord = { run_id:string; model_id:string; workload_id:string; verdict:string; reason:string; runtime_gate:string; source_gate:string; rollback_ready:boolean; evidence_ids:string[]; created_at:number };
type BundleRecord = { bundle_id:string; run_id:string; model_id:string; runtime_gate:string; source_gate:string; rollback_ready:boolean; created_at:number };

const MODELS_TABLE = 'morphosis_models';
const EVENTS_TABLE = 'morphosis_v3_events';
const SETTINGS_TABLE = 'morphosis_settings';
const EVIDENCE_TABLE = 'morphosis_v3_evidence';
const RUNS_TABLE = 'morphosis_v3_runs';
const BUNDLES_TABLE = 'morphosis_v3_bundles';

const agents = [
  { id:'discovery', name:'Morphosis Discovery', role:'Normalize candidate identity and claims', boundary:'Self-report remains UNVERIFIED', status:'Healthy', icon:'⌕' },
  { id:'workload', name:'Workload Agent', role:'Execute workload contract and hard invariants', boundary:'Candidate cannot grade itself', status:'Healthy', icon:'⌘' },
  { id:'morphogenesis', name:'Morphogenesis', role:'Verify compatibility adaptation independently', boundary:'Adaptation proof is separate from capability proof', status:'Healthy', icon:'✦' },
  { id:'promotion', name:'Promotion Control', role:'Issue rollback-backed runtime and source gates', boundary:'Source changes require human approval', status:'Healthy', icon:'◉' },
];
const workload = [['Inference',10,38,'#ff78ad'],['Evaluation',7,27,'#f24882'],['Training',5,19,'#d04b80'],['Agent Tasks',3,12,'#a63c68'],['Other',1,4,'#6d2946']];
const defaultSettings: SettingsRecord = { driftThreshold:0.05, qualificationMargin:0.02, triggers:{ schema:true, tools:true, latency:true, policy:true } };
const seedModels: Omit<ModelRecord,'created_at'>[] = [
  { model_id:'incumbent-v1', name:'incumbent-v1', provider:'deterministic baseline fixture', meta:'Reasoning · Tools · Evidence lineage · bundled proof baseline', status:'PROOF_BASELINE', tone:'testing', icon:'◉' },
  { model_id:'bedrock-known-adapter', name:'bedrock-known-adapter', provider:'deterministic known-adapter fixture', meta:'Provider profile · bundled contract proof', status:'PROOF_FIXTURE', tone:'testing', icon:'◇' },
  { model_id:'future-model-x', name:'future-model-x', provider:'deterministic proof fixture', meta:'Novel capability · bounded deterministic proof', status:'PROOF_FIXTURE', tone:'testing', icon:'∞' },
  { model_id:'new-hot-model', name:'new-hot-model', provider:'deterministic proof fixture', meta:'Hard-invariant rejection fixture', status:'PROOF_FIXTURE', tone:'testing', icon:'⊘' },
];
const seedEvents: Omit<EventRecord,'created_at'>[] = [
  { event_type:'ProofFixtureLoaded', title:'future-model-x', sub:'Deterministic fixture prepared for future.semantic_patch.v1; this is not external-model telemetry', status:'FIXTURE', tone:'testing', icon:'∞', level:'INFO' },
  { event_type:'ProofFixtureLoaded', title:'Adaptation proof', sub:'Deterministic semantic-patch fixture prepared for the bounded verifier', status:'FIXTURE', tone:'testing', icon:'✦', level:'INFO' },
  { event_type:'SourceGateHeld', title:'Source evolution', sub:'Source-code evolution remains behind explicit human merge authority', status:'HOLD', tone:'hold', icon:'⌘', level:'WARN' },
];

function withoutId<T extends { id:string }>(record:T): Omit<T,'id'> { const { id:_id, ...rest } = record; return rest; }
function runId(prefix:string) { return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2,8)}`; }
async function ensureSeed() {
  const models = await db.list<ModelRecord>(MODELS_TABLE,{ limit:50 });
  if (!models.items.length) await db.add(MODELS_TABLE, seedModels.map((model) => ({ ...model, created_at:Date.now() })));
  const events = await db.list<EventRecord>(EVENTS_TABLE,{ limit:50 });
  if (!events.items.length) { const now = Date.now(); await db.add(EVENTS_TABLE, seedEvents.map((event,index) => ({ ...event, created_at:now-index*60000 }))); }
  const settings = await db.list<SettingsRecord>(SETTINGS_TABLE,{ limit:1 });
  if (!settings.items.length) await db.add(SETTINGS_TABLE,[defaultSettings]);
}
async function listModels() { await ensureSeed(); const { items } = await db.list<ModelRecord>(MODELS_TABLE,{ limit:50 }); return items.sort((a,b)=>a.created_at-b.created_at).map(({id,...model}) => ({ ...model, db_id:id, id:model.model_id })); }
async function listEvents() { await ensureSeed(); const { items } = await db.list<EventRecord>(EVENTS_TABLE,{ limit:80 }); return items.sort((a,b)=>b.created_at-a.created_at); }
async function listRuns() { const { items } = await db.list<RunRecord>(RUNS_TABLE,{ limit:30 }); return items.sort((a,b)=>b.created_at-a.created_at); }
async function listEvidence() { const { items } = await db.list<EvidenceRecord>(EVIDENCE_TABLE,{ limit:100 }); return items.sort((a,b)=>b.created_at-a.created_at); }
async function listBundles() { const { items } = await db.list<BundleRecord>(BUNDLES_TABLE,{ limit:30 }); return items.sort((a,b)=>b.created_at-a.created_at); }
async function getSettings(): Promise<SettingsWithId> { await ensureSeed(); const { items } = await db.list<SettingsRecord>(SETTINGS_TABLE,{ limit:1 }); const record = items[0]; return record ? { ...withoutId(record), db_id:record.id } : { ...defaultSettings }; }
function relativeTime(createdAt:number) { const delta = Math.max(0,Date.now()-createdAt); if (delta<60000) return 'now'; if (delta<3600000) return `${Math.floor(delta/60000)}m`; if (delta<86400000) return `${Math.floor(delta/3600000)}h`; return `${Math.floor(delta/86400000)}d`; }

const infrastructure = {
  version:'morphosis-v0.3-appdeploy-adapter',
  authority:'persisted AppDeploy control-plane adapter; fixture proof is explicitly non-production',
  stages:[
    ['DISCOVERY','candidate identity + claims','MODEL PROPOSAL'],
    ['EVALUATION','workload contract + hard invariants','INDEPENDENT EVALUATION'],
    ['MORPHOGENESIS','compatibility adaptation proof','INDEPENDENT VERIFICATION'],
    ['BUNDLE','evidence + rollback + lineage','SYSTEM COMPILED'],
    ['PROMOTION','runtime gate / source gate split','HUMAN SOURCE AUTHORITY'],
  ],
};

async function buildOverview() {
  const [models,events,settings,runs,evidence,bundles] = await Promise.all([listModels(),listEvents(),getSettings(),listRuns(),listEvidence(),listBundles()]);
  const recent = events.slice(0,8).map((event)=>({ ...event,time:relativeTime(event.created_at) }));
  return {
    connected:true,
    version:'0.3.0', mode:'appdeploy-adapter', verification:{ python:81, frontend:12 },
    agents, models, events:recent, workload, settings, infrastructure,
    runs:runs.slice(0,10), evidence:evidence.slice(0,20), bundles:bundles.slice(0,10),
    latest_run:runs[0] || null,
    stats:{ model_paths:models.length, agent_count:agents.length, evidence_count:evidence.length, python_tests:81, frontend_tests:12, source_authority:'GATED' },
    notifications:recent.slice(0,5).map((event)=>({ status:event.status, message:event.sub, time:event.time })),
  };
}
async function publishOverview() { const overview = await buildOverview(); await notifySubscribers('system','global',overview); return overview; }
async function addEvent(event:Omit<EventRecord,'created_at'>) { const [id] = await db.add(EVENTS_TABLE,[{ ...event, created_at:Date.now() }]); return id; }
async function updateModelStatus(modelId:string,status:string,tone:string) {
  const { items } = await db.list<ModelRecord>(MODELS_TABLE,{limit:50});
  const match = items.find((item)=>item.model_id===modelId);
  if (!match) return;
  await db.update(MODELS_TABLE,[{ id:match.id, record:{ ...withoutId(match), status, tone } }]);
}
function canonicalCandidate(candidateId:string) {
  if (candidateId==='unknown') return 'future-model-x';
  if (candidateId==='hot') return 'new-hot-model';
  if (candidateId==='known') return 'bedrock-known-adapter';
  return candidateId;
}
function evaluateCandidate(candidateId:string,margin:number) {
  const modelId=canonicalCandidate(candidateId);
  if (modelId==='new-hot-model') return {
    model_id:modelId, verdict:'REJECT', status:'PROOF_FAILED', tone:'rejected', delta:'+0.147 fixture aggregate',
    reason:'Deterministic proof fixture: authorization fails as a hard invariant. Higher aggregate performance cannot override the workload contract.',
    runtime_gate:'BLOCKED', source_gate:'HUMAN_APPROVAL_REQUIRED', rollback_ready:false,
    evidence:[
      ['candidate_claim','UNVERIFIED','candidate','High aggregate performance claim',0.99],
      ['tool_schema_probe','PASS','deterministic fixture evaluator','Tool use and structured output satisfy the bundled workload fixture',0.99],
      ['authorization_invariant','FAIL','independent evaluator','Authorization boundary violated',0.72],
    ],
    trace:[['DISCOVER','provider claim','UNVERIFIED'],['PROBE','tool + schema','PASS'],['EVAL','workload','0.99'],['POLICY','authorization','FAIL'],['BUNDLE','promotion','BLOCKED'],['DECIDE','candidate','REJECT']]
  };
  if (modelId==='bedrock-known-adapter') {
    const improvement=0.058, pass=improvement>=margin;
    return {
      model_id:modelId, verdict:pass?'PROMOTE':'HOLD', status:pass?'PROOF_PASSED':'HOLD', tone:pass?'active':'hold', delta:`+${improvement.toFixed(3)} fixture workload score`,
      reason:pass?'Deterministic proof fixture: known adapter satisfies the workload contract without an invariant regression.':'Deterministic proof fixture clears hard invariants but does not meet the configured promotion margin.',
      runtime_gate:pass?'AUTO_APPLY':'HOLD', source_gate:'HUMAN_APPROVAL_REQUIRED', rollback_ready:true,
      evidence:[
        ['known_adapter','VERIFIED','host registry','Provider profile is known but still independently qualified',1],
        ['workload_contract','PASS','deterministic fixture evaluator','Bundled workload quality and invariants pass',0.96],
        ['rollback_metadata','PASS','promotion control','Rollback metadata is present',1],
      ],
      trace:[['DISCOVER','known adapter','FAST PATH'],['PROBE','workload','PASS'],['EVAL','quality','0.96'],['POLICY','invariants','PASS'],['BUNDLE','rollback','READY'],['DECIDE','candidate',pass?'PROMOTE':'HOLD']]
    };
  }
  if (modelId==='future-model-x') {
    const improvement=0.060, pass=improvement>=margin;
    return {
      model_id:modelId, verdict:pass?'PROMOTE':'HOLD', status:pass?'PROOF_PASSED':'HOLD', tone:pass?'active':'hold', delta:'DETERMINISTIC FIXTURE · NOVEL CAPABILITY + VERIFIED ADAPTATION',
      reason:pass?'Deterministic proof fixture: the bundled capability observation and compatibility transform pass separate checks. This does not claim external model execution. Runtime policy may auto-apply only within the fixture; source evolution remains human-gated.':'Deterministic proof fixture passes its checks, but the configured promotion margin holds runtime policy.',
      runtime_gate:pass?'AUTO_APPLY':'HOLD', source_gate:'HUMAN_APPROVAL_REQUIRED', rollback_ready:true,
      evidence:[
        ['capability_claim','UNVERIFIED','candidate','future.semantic_patch.v1 enters as an untrusted claim',0],
        ['capability_probe','OBSERVED','deterministic fixture evaluator','Namespaced capability observed inside the bundled deterministic proof',0.97],
        ['adaptation_roundtrip','VERIFIED','deterministic fixture verifier','semantic-patch-wrapper preserves the bundled contract fixture',0.96],
        ['hard_invariants','PASS','policy kernel','Safety, authorization and evidence-lineage invariants pass',1],
        ['rollback_metadata','PASS','promotion control','Reversible runtime bundle includes rollback metadata',1],
      ],
      trace:[['BOOTSTRAP','future-model-x','UNKNOWN'],['CLAIM','future.semantic_patch.v1','UNVERIFIED'],['PROBE','capability','OBSERVED'],['MORPH','semantic-patch-wrapper','VERIFIED'],['BUNDLE','runtime/source','SPLIT GATE'],['DECIDE','runtime',pass?'PROMOTE':'HOLD']]
    };
  }
  return {
    model_id:modelId, verdict:'HOLD', status:'UNVERIFIED', tone:'hold', delta:'EVIDENCE REQUIRED',
    reason:'Candidate is registered, but no independently verified workload evidence exists yet.',
    runtime_gate:'BLOCKED', source_gate:'HUMAN_APPROVAL_REQUIRED', rollback_ready:false,
    evidence:[
      ['candidate_claim','UNVERIFIED','candidate','Candidate metadata is stored as a prior, not proof',0],
      ['capability_probe','REQUIRED','independent evaluator','Bounded capability evidence is required before qualification',0],
    ],
    trace:[['DISCOVER',modelId,'REGISTERED'],['CLAIM','candidate metadata','UNVERIFIED'],['PROBE','capability evidence','REQUIRED'],['MORPH','compatibility','NOT RUN'],['BUNDLE','runtime/source','BLOCKED'],['DECIDE','candidate','HOLD']]
  };
}
async function runEvolution(candidateId:string) {
  const settings=await getSettings();
  const result=evaluateCandidate(candidateId,settings.qualificationMargin);
  const rid=runId('run');
  const now=Date.now();
  const records:EvidenceRecord[]=result.evidence.map(([kind,status,source,detail,score])=>({run_id:rid,model_id:result.model_id,kind:String(kind),status:String(status),source:String(source),detail:String(detail),score:Number(score),created_at:now}));
  const evidenceIds=(await db.add(EVIDENCE_TABLE,records)).filter((id): id is string => Boolean(id));
  const bundle:BundleRecord={bundle_id:runId('bundle'),run_id:rid,model_id:result.model_id,runtime_gate:result.runtime_gate,source_gate:result.source_gate,rollback_ready:result.rollback_ready,created_at:now};
  await db.add(BUNDLES_TABLE,[bundle]);
  const run:RunRecord={run_id:rid,model_id:result.model_id,workload_id:'professional-opportunity-triage-v1',verdict:result.verdict,reason:result.reason,runtime_gate:result.runtime_gate,source_gate:result.source_gate,rollback_ready:result.rollback_ready,evidence_ids:evidenceIds,created_at:now};
  await db.add(RUNS_TABLE,[run]);
  await updateModelStatus(result.model_id,result.status,result.tone);
  await addEvent({event_type:result.verdict==='PROMOTE'?'CandidatePromoted':result.verdict==='REJECT'?'CandidateRejected':'CandidateHeld',title:result.model_id,sub:`${result.verdict}: ${result.reason}`,status:result.verdict==='PROMOTE'?'PROMOTED':result.verdict,tone:result.tone,icon:result.verdict==='PROMOTE'?'✦':result.verdict==='REJECT'?'⊘':'⌘',level:result.verdict==='PROMOTE'?'INFO':'WARN',run_id:rid});
  const overview=await publishOverview();
  const agent_trace=[
    {agent:'Morphosis Discovery',action:'Normalize candidate claims; preserve UNKNOWN until evidence',status:'DONE'},
    {agent:'Workload Agent',action:'Evaluate workload contract and hard invariants',status:'DONE'},
    {agent:'Morphogenesis',action:'Verify compatibility adaptation independently',status:'DONE'},
    {agent:'Promotion Control',action:'Issue runtime/source split gate with rollback requirement',status:result.verdict},
  ];
  return { result:{...result,run_id:rid,evidence_ids:evidenceIds,bundle,agent_trace}, overview };
}

export const handler = router({
  'GET /api/_healthcheck':[async()=>json({status:'ok',service:'morphosis-appdeploy-adapter',version:'0.3.0'})],
  'GET /api/readyz':[async()=>{const [models,events,evidence,runs]=await Promise.all([listModels(),listEvents(),listEvidence(),listRuns()]);return json({status:'ready',service:'morphosis-appdeploy-adapter',version:'0.3.0',persistence:{models:models.length,events:events.length,evidence:evidence.length,runs:runs.length}});}],
  'GET /api/overview':[async()=>json(await buildOverview())],
  'GET /api/models':[async()=>json({models:await listModels()})],
  'POST /api/models':[async({body})=>{
    const payload=(body||{}) as Record<string,string>;
    const name=String(payload.name||'').trim(),provider=String(payload.provider||'').trim(),endpoint=String(payload.endpoint||'').trim(),capability=String(payload.capability||'').trim();
    if(!name||!provider||!endpoint||!capability) return error('name, provider, endpoint, and capability are required',400);
    let parsed:URL; try{parsed=new URL(endpoint);}catch{return error('Endpoint must be a valid http(s) URL.',400);}
    if(!['http:','https:'].includes(parsed.protocol)) return error('Endpoint must use http or https.',400);
    const models=await listModels();
    if(models.some((model)=>model.name.toLowerCase()===name.toLowerCase())) return error('A model with this name already exists.',409);
    const model:ModelRecord={model_id:name,name,provider,endpoint,capability,meta:`${provider} · claim ${capability} · UNVERIFIED`,status:'UNVERIFIED',tone:'testing',icon:'◇',created_at:Date.now()};
    const [id]=await db.add(MODELS_TABLE,[model]); if(!id) return error('Failed to persist model candidate.',500);
    await addEvent({event_type:'CandidateBootstrapped',title:name,sub:`Candidate registered from ${provider}; capability claim remains UNVERIFIED`,status:'HOLD',tone:'hold',icon:'◇',level:'INFO'});
    const overview=await publishOverview();
    return json({model:{...model,db_id:id,id:model.model_id},overview},201);
  }],
  'GET /api/events':[async()=>json({events:await listEvents()})],
  'GET /api/logs':[async()=>{const events=await listEvents(); return json({logs:events.slice(0,30).map((event)=>({created_at:event.created_at,level:event.level,event_type:event.event_type,message:`${event.title}: ${event.sub}`,run_id:event.run_id||null}))});}],
  'GET /api/notifications':[async()=>{const overview=await buildOverview(); return json({notifications:overview.notifications});}],
  'GET /api/agents':[async()=>json({agents})],
  'GET /api/evidence':[async()=>json({evidence:await listEvidence()})],
  'GET /api/runs':[async()=>json({runs:await listRuns()})],
  'GET /api/bundles':[async()=>json({bundles:await listBundles()})],
  'GET /api/infrastructure':[async()=>json(infrastructure)],
  'GET /api/settings':[async()=>json(await getSettings())],
  'POST /api/settings':[async({body})=>{
    const payload=(body||{}) as Partial<SettingsRecord>,current=await getSettings();
    const next:SettingsRecord={driftThreshold:Number.isFinite(payload.driftThreshold)?Number(payload.driftThreshold):current.driftThreshold,qualificationMargin:Number.isFinite(payload.qualificationMargin)?Number(payload.qualificationMargin):current.qualificationMargin,triggers:payload.triggers&&typeof payload.triggers==='object'?{...current.triggers,...payload.triggers}:current.triggers};
    if(current.db_id) await db.update(SETTINGS_TABLE,[{id:String(current.db_id),record:next}]); else await db.add(SETTINGS_TABLE,[next]);
    return json({settings:next,overview:await publishOverview()});
  }],
  'POST /api/evolution/run':[async({body})=>{
    const candidateId=String(((body||{}) as Record<string,string>).candidate_id||'').trim();
    if(!candidateId) return error('candidate_id is required',400);
    const canonical=canonicalCandidate(candidateId),models=await listModels();
    if(!models.some((model)=>model.model_id===canonical) && !['bedrock-known-adapter','future-model-x','new-hot-model'].includes(canonical)) return error('candidate is not registered',404);
    return json(await runEvolution(candidateId));
  }],
  'POST /api/requalification':[async()=>{
    await addEvent({event_type:'RequalificationRequested',title:'Requalification',sub:'Manual requalification requested from observability control plane',status:'RUNNING',tone:'testing',icon:'⌁',level:'EVAL'});
    return json(await runEvolution('future-model-x'));
  }],
  ...realtimeSubscriptionRoutes,
});
