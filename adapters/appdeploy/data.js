import { api, ws } from '@appdeploy/client';

export const navItems=[['overview','Overview'],['evolution','Evolution Lab'],['models','Model Ecosystem'],['agents','Agents'],['evaluation','Evaluation'],['deployments','Deployments'],['observability','Observability'],['datasets','Datasets'],['infrastructure','Infrastructure'],['settings','Settings']];

const contract={workload_id:'professional-opportunity-triage-v1',version:'v0.3',required_capabilities:['tool_use','structured_output','task_quality'],hard_invariants:['authorization','evidence_lineage'],promotion_margin:'backend settings',source_authority:'HUMAN_APPROVAL_REQUIRED'};
const datasets=[
 {name:'morphosis_contract.json',kind:'Workload contract',hash:'repository-fixture',preview:['required capabilities','hard invariants','promotion margin','latency / cost budgets']},
 {name:'morphosis_candidates.json',kind:'Candidate fixtures',hash:'repository-fixture',preview:['incumbent-v1','new-hot-model','future-qualified-model']},
 {name:'future_model_x.json',kind:'Unknown future model',hash:'repository-fixture',preview:['future.semantic_patch.v1','bounded probe','adaptation proposal','runtime/source changes']},
 {name:'opportunities.json',kind:'Workload fixtures',hash:'repository-fixture',preview:['source evidence','triage records','authorization boundary']}
];
const pipeline=[
 {name:'DISCOVER',description:'Normalize identity and untrusted claims'},
 {name:'EVALUATE',description:'Run workload contract and hard invariants'},
 {name:'ADAPT',description:'Compile and independently verify compatibility'},
 {name:'GATE',description:'Split runtime authority from source authority'},
 {name:'DEPLOY',description:'Admit only rollback-backed runtime changes'}
];

const statusOutcome=value=>{
 const v=String(value||'').toUpperCase();
 if(v==='PROMOTED'||v==='ACTIVE'||v==='AUTO_APPLY')return 'PROMOTE';
 if(v==='REJECTED'||v==='REJECT'||v==='FAIL'||v==='FAILED'||v==='BLOCKED')return 'REJECT';
 if(v==='HOLD'||v==='UNVERIFIED')return 'HOLD';
 return v||null;
};
const iso=value=>new Date(Number(value)||Date.now()).toISOString();

function architectureFrom(info,events){
 const stages=info?.stages||[
  ['DISCOVERY','candidate identity + claims','MODEL PROPOSAL'],
  ['EVALUATION','workload contract + hard invariants','INDEPENDENT EVALUATION'],
  ['MORPHOGENESIS','compatibility adaptation proof','INDEPENDENT VERIFICATION'],
  ['BUNDLE','evidence + rollback + lineage','SYSTEM COMPILED'],
  ['PROMOTION','runtime gate / source gate split','HUMAN SOURCE AUTHORITY']
 ];
 const nodes=stages.map((stage,i)=>({id:'stage-'+i,label:stage[0],purpose:stage[1],plane:i<2?'agentic':i<4?'domain':'runtime',trust:stage[2],status:'ACTIVE',x:90+i*215,y:110+(i%2)*120,evidence:[]}));
 const ui={id:'ui',label:'Canonical projection UI',purpose:'Render persisted control-plane state without owning decisions',plane:'frontend',trust:'PRESENTATION ONLY',status:'ACTIVE',x:90,y:390,evidence:[]};
 const rt={id:'realtime',label:'Realtime projection stream',purpose:'Push backend state changes to every connected console',plane:'runtime',trust:'BACKEND AUTHORITY',status:'ACTIVE',x:305,y:390,evidence:[]};
 nodes.push(ui,rt);
 const edges=[];
 for(let i=0;i<stages.length-1;i++)edges.push({from:'stage-'+i,to:'stage-'+(i+1)});
 edges.push({from:'stage-4',to:'realtime'},{from:'realtime',to:'ui'});
 return {nodes,edges,trace:events.map(e=>e.event_id)};
}

function project(overview){
 const models=(overview?.models||[]).map(m=>({
  surface_id:m.model_id||m.id||m.name,model:m.name||m.model_id,provider:m.provider||'unknown provider',
  status:m.status||'UNVERIFIED',lane:m.provider||'candidate',api_surface:m.endpoint||'registered surface',
  capability:m.capability||null,observed_at:iso(m.created_at)
 }));
 const rawEvents=[...(overview?.events||[])].sort((a,b)=>(a.created_at||0)-(b.created_at||0));
 const events=rawEvents.map((e,i)=>({
  event_id:'evt-'+String(e.created_at||i)+'-'+i,sequence:i+1,timestamp:iso(e.created_at),
  event_type:e.event_type||'DomainEvent',aggregate_id:e.run_id||e.title||'system',
  payload:{message:e.sub||e.title||'Domain event',mutation:{value:{status:e.status||null,outcome:statusOutcome(e.status)}}}
 }));
 const runs=(overview?.runs||[]).map(r=>({
  surface_id:r.model_id,run_id:r.run_id,outcome:r.verdict,reasons:[r.reason],
  measurements:{runtime_gate:r.runtime_gate,source_gate:r.source_gate,rollback_ready:r.rollback_ready},
  observed_at:iso(r.created_at)
 }));
 const evidence=(overview?.evidence||[]).map((e,i)=>({
  surface_id:e.model_id,run_id:e.run_id,capability_id:e.kind,kind:e.kind,status:e.status,source:e.source,
  detail:e.detail,score:e.score,passed:/PASS|OBSERVED|VERIFIED/i.test(e.status||''),evidence_hash:e.id||('evidence-'+i),observed_at:iso(e.created_at)
 }));
 const bundles=(overview?.bundles||[]).map(b=>({
  bundle_id:b.bundle_id,surface_id:b.model_id,run_id:b.run_id,rollback_ready:b.rollback_ready,
  policy:{outcome:b.runtime_gate},runtime_gate:b.runtime_gate,source_gate:b.source_gate,observed_at:iso(b.created_at)
 }));
 const transactions=bundles.map(b=>({transaction_id:b.bundle_id,surface_id:b.surface_id,stage:b.runtime_gate,rollback_ready:b.rollback_ready,checks:{source_gate:b.source_gate,run_id:b.run_id}}));
 const agents=(overview?.agents||[]).map(a=>({name:a.name,role:a.role,implementation:'AppDeploy backend stage',status:a.status||'HEALTHY',boundary:a.boundary}));
 const workload=(overview?.workload||[]).map(w=>Array.isArray(w)?{name:w[0],count:w[1],percent:w[2]}:w);
 const adaptations=evidence.filter(e=>/adaptation/i.test(e.kind)).map(e=>({surface_id:e.surface_id,run_id:e.run_id,implementation:'semantic-patch-wrapper',status:e.status,evidence_hash:e.evidence_hash}));
 const verifications=evidence.filter(e=>/adaptation|invariant|rollback/i.test(e.kind)).map(e=>({surface_id:e.surface_id,run_id:e.run_id,passed:e.passed,status:e.status,evidence_hash:e.evidence_hash}));
 const telemetry=runs.slice(0,8).map(r=>({surface_id:r.surface_id,event_type:'QualificationTelemetry',outcome:r.outcome,runtime_gate:r.measurements.runtime_gate,observed_at:r.observed_at}));
 const requalifications=events.filter(e=>/Requalification/i.test(e.event_type)||/Requalification/i.test(e.payload?.message||'')).map(e=>({surface_id:e.aggregate_id,status:e.payload?.mutation?.value?.status||'RECORDED',observed_at:e.timestamp}));
 const architecture=architectureFrom(overview?.infrastructure,events);
 return {
  sequence:events.length+(overview?.runs?.length||0)+(overview?.evidence?.length||0),
  ledger_head:events.at(-1)?.event_id||null,
  metrics:{evidence:evidence.length,surfaces:models.length,contracts:1},
  models,events,contracts:[contract],qualifications:runs,evidence,adaptations,verifications,
  probe_runs:evidence,probes:evidence,agents,datasets,architecture,bundles,transactions,telemetry,requalifications,
  workload,pipeline,service:{version:overview?.version||'0.3.0',mode:overview?.mode||'appdeploy-adapter',verification:overview?.verification||null},deployment:{runtime_pool:models.filter(m=>/ACTIVE|READY|PROOF_PASSED/.test(m.status)),source_authority:'HUMAN_APPROVAL_REQUIRED'}
 };
}

export class ProjectionClient{
 constructor({live=true}={}){this.live=live;this.snapshot=null;this.sequence=0;this.onSnapshot=()=>{};this.onEvent=()=>{};this.onStatus=()=>{};this.connection=null;this.previousEventIds=new Set();}
 apply(snapshot){this.snapshot=snapshot;this.sequence=Number(snapshot?.sequence)||0;this.previousEventIds=new Set((snapshot?.events||[]).map(e=>e.event_id));this.onSnapshot(snapshot);return snapshot;}
 async refresh(){const response=await api.get('/api/overview');const next=project(response.data);if(this.snapshot){const old=new Set(this.previousEventIds);for(const event of next.events||[]){if(!old.has(event.event_id))this.onEvent(event);}}return this.apply(next);}
 async load(){return this.refresh();}
 async command(name,payload){
  let response;
  if(name==='evaluate'||name==='bundle')response=await api.post('/api/evolution/run',{candidate_id:payload.surface_id});
  else if(name==='bootstrap')response=await api.post('/api/models',{name:payload.model,provider:payload.provider,endpoint:payload.endpoint,capability:(payload.claims||[])[0]||'unknown.capability'});
  else if(name==='requalify')response=await api.post('/api/requalification',{});
  else if(name==='rollback')return {status:'RECORDED',message:'Rollback metadata is preserved by the live bundle. Manual execution is intentionally not exposed by this AppDeploy control-plane adapter.'};
  else if(name==='advance')return {status:'RECORDED',message:'Runtime admission is policy-driven; manual stage advancement is intentionally not exposed by this AppDeploy control-plane adapter.'};
  else throw new Error('Unsupported live command: '+name);
  await this.refresh();
  return response.data?.result||response.data?.model||response.data;
 }
 async connect(){
  if(!this.live||this.connection)return;
  const connection=ws.connect();this.connection=connection;
  connection.onMessage(message=>{if(message?.type==='entity.update'&&message?.payload?.entity_type==='system'&&message?.payload?.entity_id==='global'){const next=project(message.payload.data);const old=new Set(this.previousEventIds);for(const event of next.events||[]){if(!old.has(event.event_id))this.onEvent(event);}this.apply(next);}});
  connection.onOpen(()=>this.onStatus('MORPHOSIS V0.3 STREAM'));
  connection.onClose(()=>this.onStatus('RECONNECTING · last projection retained'));
  connection.onError(()=>this.onStatus('STREAM DEGRADED · last projection retained'));
  await connection.ready;
  if(connection.connectionId)await api.post('/api/subscriptions',{entity_type:'system',entity_id:'global',connection_id:connection.connectionId});
 }
 dispose(){
  const connection=this.connection;if(!connection)return;
  const id=connection.connectionId;
  if(id)api.post('/api/subscriptions/remove',{entity_type:'system',entity_id:'global',connection_id:id}).catch(()=>{});
  connection.disconnect();this.connection=null;
 }
}

export function humanize(value){return String(value??'').replace(/([a-z0-9])([A-Z])/g,'$1 $2').replace(/([A-Z])([A-Z][a-z])/g,'$1 $2').replace(/[_-]+/g,' ');}
export function presentEvent(event){const value=event?.payload?.mutation?.value||{};return {title:humanize(event?.event_type||'Domain event'),status:value.outcome??value.stage??value.status??(typeof value.passed==='boolean'?(value.passed?'PASSED':'FAILED'):null)};}
