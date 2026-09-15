export const navItems = [
  ['overview','⌂','Overview'],['evolution','◉','Evolution Lab'],['models','◈','Model Ecosystem'],['agents','◇','Agents'],['evaluation','◫','Evaluation'],['deployments','◉','Deployments'],['observability','⌁','Observability'],['datasets','▤','Datasets'],['infrastructure','⬡','Infrastructure'],['settings','⌘','Settings']
];

export const baseModels = [
  {id:'incumbent-v1',name:'incumbent-v1',provider:'qualified runtime',meta:'Reasoning · Tools · Evidence lineage',status:'ACTIVE',tone:'active',icon:'◉'},
  {id:'bedrock-known-adapter',name:'bedrock-known-adapter',provider:'known fast lane',meta:'Provider profile · Contract-ready',status:'READY',tone:'ready',icon:'◇'},
  {id:'future-model-x',name:'future-model-x',provider:'unknown future lane',meta:'Novel capability · Probe verified',status:'EVOLVING',tone:'testing',icon:'∞'},
  {id:'new-hot-model',name:'new-hot-model',provider:'candidate',meta:'High aggregate · Invariant failed',status:'REJECTED',tone:'rejected',icon:'⊘'}
];

export const recentEvents = [
  {title:'future-model-x',sub:'Novel capability verified: future.semantic_patch.v1',status:'PROMOTED',tone:'active',time:'now',icon:'∞'},
  {title:'Adaptation proof',sub:'semantic-patch-wrapper independently verified',status:'PROMOTED',tone:'active',time:'1m',icon:'✦'},
  {title:'Source evolution',sub:'Optimized adapter proposal stopped at human merge gate',status:'HOLD',tone:'hold',time:'2m',icon:'⌘'},
  {title:'new-hot-model',sub:'Authorization invariant failed despite higher score',status:'REJECTED',tone:'rejected',time:'8m',icon:'⊘'},
  {title:'Runtime bundle',sub:'Rollback-backed config evolution eligible for auto-apply',status:'PROMOTED',tone:'active',time:'12m',icon:'◈'}
];

export const workload = [
  ['Inference',10,38,'#ff78ad'],['Evaluation',7,27,'#f24882'],['Training',5,19,'#d04b80'],['Agent Tasks',3,12,'#a63c68'],['Other',1,4,'#6d2946']
];

export const pipelineSteps = [
  ['1. PROPOSE','New candidate or behavior','↟'],['2. EVALUATE','Auto + human evaluation','∑'],['3. ADAPT','Refine via feedback','⌘'],['4. GATE','Safety, alignment, performance','△'],['5. DEPLOY','Promote to ecosystem','◈']
];

export const candidates = {
  hot:{name:'new-hot-model',verdict:'REJECT',delta:'+0.147 aggregate',reason:'Authorization failed as a hard invariant. Higher aggregate performance cannot override the workload contract.',metrics:[['Tool use',1,.90],['Structured output',1,.95],['Task quality',.99,.80],['Authorization',.72,1],['Evidence lineage',1,1]],trace:[['DISCOVER','provider claim','UNVERIFIED'],['PROBE','tool + schema','PASS'],['EVAL','workload','0.99'],['POLICY','authorization','FAIL'],['BUNDLE','promotion','BLOCKED'],['DECIDE','candidate','REJECT']]},
  known:{name:'future-qualified-model',verdict:'PROMOTE',delta:'+0.058 workload score',reason:'Known capabilities satisfy the workload contract without an invariant regression.',metrics:[['Tool use',.99,.90],['Structured output',.99,.95],['Task quality',.96,.80],['Authorization',1,1],['Evidence lineage',1,1]],trace:[['DISCOVER','known adapter','FAST PATH'],['PROBE','workload','PASS'],['EVAL','quality','0.96'],['POLICY','invariants','PASS'],['ROUTE','canary','10%'],['DECIDE','candidate','PROMOTE']]},
  unknown:{name:'future-model-x',verdict:'PROMOTE',delta:'NOVEL CAPABILITY + VERIFIED ADAPTATION',reason:'The unknown capability is independently observed and the compatibility transform passes a separate adaptation proof. Runtime evolution may auto-apply with rollback; source evolution still requires human approval.',metrics:[['Novel capability',.97,.90],['Adaptation proof',.96,.90],['Round-trip preserved',1,1],['Side-effect free',1,1],['Human source gate',1,1]],trace:[['BOOTSTRAP','future-model-x','UNKNOWN'],['CLAIM','future.semantic_patch.v1','UNVERIFIED'],['PROBE','capability','OBSERVED'],['MORPH','semantic-patch-wrapper','VERIFIED'],['BUNDLE','runtime/source','SPLIT GATE'],['DECIDE','runtime','PROMOTE']]}
};

export const agents = [
  ['Workload Agent','Professional opportunity triage','Human authorization','Healthy','⌘'],
  ['Morphosis Discovery','Unknown-model capability intake','Self-report is not proof','Healthy','⌕'],
  ['Morphogenesis','Compatibility proposal compiler','Independent verifier','Healthy','✦'],
  ['Promotion Control','Evolution Bundle gate','Human source authority','Healthy','◉']
];

export const datasets = [
  {name:'morphosis_contract.json',kind:'Workload contract',rows:'1 contract',lineage:'fixtures/morphosis_contract.json',preview:['required capabilities','hard invariants','promotion margin','latency / cost budgets']},
  {name:'morphosis_candidates.json',kind:'Candidate fixtures',rows:'incumbent + candidates',lineage:'fixtures/morphosis_candidates.json',preview:['incumbent-v1','new-hot-model','future-qualified-model']},
  {name:'future_model_x.json',kind:'Unknown future model',rows:'1 candidate',lineage:'fixtures/future_model_x.json',preview:['future.semantic_patch.v1','bounded probe','adaptation proposal','runtime/source changes']},
  {name:'opportunities.json',kind:'Workload fixtures',rows:'opportunity set',lineage:'fixtures/opportunities.json',preview:['source evidence','triage records','authorization boundary']}
];

export const notifications = [
  ['PROMOTED','future-model-x passed capability + adaptation verification','now'],
  ['HOLD','source evolution requires human merge approval','2m'],
  ['REJECTED','new-hot-model failed authorization invariant','8m'],
  ['INFO','drift monitor armed for qualified runtime','12m']
];

export const initialLogs = [
  ['14:21:12','INFO','future-model-x entered UNKNOWN_BOOTSTRAP lane'],['14:27:03','INFO','candidate capability probe accepted by verifier'],['14:26:47','WARN','output drift detected in candidate shadow run'],['14:25:22','INFO','running safety checks...'],['14:24:51','INFO','runtime Evolution Bundle → AUTO_APPLY with rollback'],['14:25:08','INFO','new candidate discovered from provider scan'],['14:25:11','INFO','evaluation batch completed']
];
