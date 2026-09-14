const state={
  view:'overview',candidate:'hot',pipeline:4,logPaused:false,animation:true,
  activeModel:'Claude 3.5 Sonnet'
};

const models=[
  {name:'GPT-4o',meta:'Reasoning · Multimodal · Tool Use',status:'ACTIVE',icon:'◉'},
  {name:'Claude 3.5 Sonnet',meta:'Analysis · Long Context · Safe',status:'ACTIVE',icon:'✦'},
  {name:'Llama 3.1 70B',meta:'Open · Customizable · On-Prem',status:'TESTING',icon:'∞'},
  {name:'Gemini 1.5 Pro',meta:'Multimodal · Long Context · Native Tools',status:'ACTIVE',icon:'✦'}
];
const recent=[
  {title:'Agent: Researcher v2.3',sub:'Improved tool use & citation grounding',status:'PROMOTED',time:'2h ago',icon:'◌'},
  {title:'Model: Llama 3.1 70B',sub:'Higher reasoning consistency',status:'TESTING',time:'5h ago',icon:'∞'},
  {title:'Agent: CodeGen v1.8',sub:'Regression in multi-file editing',status:'REJECTED',time:'8h ago',icon:'⊘'},
  {title:'Model: Gemini 1.5 Pro',sub:'Evaluation on long-context tasks',status:'HOLD',time:'12h ago',icon:'◇'},
  {title:'Agent: Analyst v2.1',sub:'Better data synthesis, lower hallucination',status:'PROMOTED',time:'1d ago',icon:'▣'}
];
const candidates={
  hot:{
    name:'new-hot-model',provider:'future-provider',verdict:'REJECT',delta:'+0.147 aggregate',
    reason:'Required capability failed: authorization. A higher average score cannot buy permission to violate the human-authority boundary.',
    hash:'6f28a13995b2a29348f84da1a64acf7c396eb9274bc26b4dbdfb675078307a77',
    metrics:[['Tool use',1.00,.90],['Structured output',1.00,.95],['Task quality',.99,.80],['Authorization',.72,1],['Evidence lineage',1,1]],
    traces:[['DISCOVER','Provider metadata','unverified'],['PROBE','Tool + schema','pass'],['EVAL','Workload quality','0.99'],['POLICY','Authorization','FAIL'],['COMPARE','Regression gate','blocked'],['DECIDE','Promotion','REJECT']]
  },
  future:{
    name:'future-qualified-model',provider:'aws-bedrock-compatible',verdict:'PROMOTE',delta:'+0.058 workload score',
    reason:'All required capabilities and hard invariants pass. The candidate materially improves the workload score within cost and latency budgets.',
    hash:'f352c368e5b1d707fee81c34eda4b41bbe1569f79145b4c102103f032b09efbe',
    metrics:[['Tool use',.99,.90],['Structured output',.99,.95],['Task quality',.96,.80],['Authorization',1,1],['Evidence lineage',1,1]],
    traces:[['DISCOVER','Bedrock-compatible surface','unverified'],['PROBE','Tool + schema','pass'],['EVAL','Workload quality','0.96'],['POLICY','Hard invariants','pass'],['COMPARE','vs incumbent','+0.058'],['DECIDE','Promotion','PROMOTE']]
  }
};
const contract=[
  ['Tool use','≥ 0.90'],['Structured output','≥ 0.95'],['Task quality','≥ 0.80'],
  ['Authorization','hard invariant = 1.00'],['Evidence lineage','hard invariant = 1.00'],['Budgets','cost + latency bounded']
];
const pipeline=[
  ['1. PROPOSE','New candidate or behavior','⌁'],['2. EVALUATE','Auto + human evaluation','∑'],
  ['3. ADAPT','Refine via feedback','⌘'],['4. GATE','Safety, alignment, performance','△'],
  ['5. DEPLOY','Promote to ecosystem','◈']
];
let logs=[
  ['14:27:11','INFO','Agent(Researcher) completed evaluation run (score: 0.842)'],
  ['14:27:03','INFO','Model(Llama 3.1 70B) entered testing phase'],
  ['14:26:47','WARN','Output drift detected in CodeGen v1.8 (delta: +12.4%)'],
  ['14:26:32','INFO','Running safety checks...'],
  ['14:25:18','INFO','Agent(Analyst) promoted to production'],
  ['14:25:04','INFO','New candidate generated from evolutionary search'],
  ['14:25:11','INFO','Evaluation batch completed']
];
const agents=[
  ['ActionQueue','Professional opportunity triage','Human authorization','Healthy'],
  ['Researcher','Evidence synthesis and citation','Source lineage','Healthy'],
  ['Analyst','Structured analysis workflows','Schema fidelity','Testing'],
  ['Ops Assistant','Operational support','Approval gates','Healthy']
];

const $=(q,root=document)=>root.querySelector(q);
const $$=(q,root=document)=>[...root.querySelectorAll(q)];
function badgeClass(status){return status.toLowerCase().replace(/\s+/g,'-')}
function nowTime(){return new Date().toLocaleTimeString('en-GB',{hour12:false})}

function switchView(view){
  state.view=view;
  $$('.view').forEach(v=>v.classList.toggle('active',v.id===`view-${view}`));
  $$('.nav-item').forEach(b=>b.classList.toggle('active',b.dataset.view===view));
  if(view==='observability') drawTelemetry();
  window.scrollTo({top:0,behavior:'smooth'});
}

function renderModels(){
  $('#modelList').innerHTML=models.map(m=>`<div class="model-row"><div class="model-icon">${m.icon}</div><div><strong>${m.name}</strong><small>${m.meta}</small></div><span class="badge ${badgeClass(m.status)}">${m.status}</span></div>`).join('');
  $('#modelCards').innerHTML=models.map((m,i)=>`<article class="info-card"><div class="card-icon">${m.icon}</div><h3>${m.name}</h3><p>${m.meta}. ${i===1?'Current incumbent for the ActionQueue workload.':'Available to the qualification control plane as evidence allows.'}</p><footer><span>${m.status}</span><span>${i===2?'candidate':'registered'}</span></footer></article>`).join('');
}
function renderRecent(){
  $('#recentList').innerHTML=recent.map(r=>`<div class="recent-item"><div class="event-icon">${r.icon}</div><div><strong>${r.title}</strong><small>${r.sub}</small></div><span class="badge ${badgeClass(r.status)}">${r.status}</span><time>${r.time}</time></div>`).join('');
}
function renderPipeline(){
  $('#pipeline').innerHTML=pipeline.map((p,i)=>`<div class="pipe-step ${i===state.pipeline?'active':''}" data-step="${i}"><div class="circle">${p[2]}</div><b>${p[0]}</b><small>${p[1]}</small></div>`).join('');
  $$('.pipe-step').forEach(el=>el.onclick=()=>{state.pipeline=+el.dataset.step;renderPipeline();pushLog('EVAL',`Pipeline focus moved to ${pipeline[state.pipeline][0]}`)});
}
function renderLog(){
  $('#liveLog').innerHTML=logs.slice(0,7).map(l=>`<div class="logline"><time>${l[0]}</time><span class="level ${l[1].toLowerCase()}">${l[1]}</span>${l[2]}</div>`).join('');
}
function pushLog(level,text){logs.unshift([nowTime(),level,text]);renderLog()}
function renderContract(){
  $('#contractMetrics').innerHTML=contract.map(c=>`<div class="contract-metric"><strong>${c[0]}</strong><span>${c[1]}</span></div>`).join('');
}
function renderCandidate(){
  const c=candidates[state.candidate];
  $('#candidateMetrics').innerHTML=c.metrics.map(m=>`<div class="metric-line ${m[1]<m[2]?'danger':''}"><b>${m[0]}</b><div class="track"><div class="fill" style="width:${Math.round(m[1]*100)}%"></div></div><span>${m[1].toFixed(2)}</span></div>`).join('');
  $('#decisionCard').innerHTML=`<div class="verdict ${c.verdict==='PROMOTE'?'promote':''}">${c.verdict}<small style="display:block;font-size:8px;margin-top:8px;color:#9f798a">${c.delta}</small></div><div><p>${c.reason}</p><code>${c.hash}</code></div>`;
  $('#evidenceTrace').innerHTML=c.traces.map(t=>`<div class="trace-node"><b>${t[0]}</b><span>${t[1]}<br><small>${t[2]}</small></span></div>`).join('');
  $$('[data-candidate]').forEach(b=>b.classList.toggle('active',b.dataset.candidate===state.candidate));
}
function renderAgents(){
  $('#agentCards').innerHTML=agents.map((a,i)=>`<article class="info-card"><div class="card-icon">${['⌘','⌕','◫','◉'][i]}</div><h3>${a[0]}</h3><p>${a[1]}. Durable boundary: ${a[2]}.</p><footer><span>${a[3]}</span><span>workload skin</span></footer></article>`).join('');
}
function renderGates(){
  const gates=[['Tool selection',98],['Structured schema',99],['Task quality',96],['Authorization invariant',100],['Evidence lineage',100]];
  $('#qualityGates').innerHTML=gates.map(g=>`<div class="gate-row"><b>${g[0]}</b><div class="gatebar"><span style="width:${g[1]}%"></span></div><em>${g[1]}%</em></div>`).join('');
  $('#miniChart').innerHTML='<svg viewBox="0 0 500 130" preserveAspectRatio="none" width="100%" height="100%"><defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#ff4f8c" stop-opacity=".4"/><stop offset="1" stop-color="#ff4f8c" stop-opacity="0"/></linearGradient></defs><path d="M0,105 C45,102 58,85 92,91 S145,69 179,76 S228,54 260,61 S310,42 340,51 S392,28 500,22 L500,130 L0,130Z" fill="url(#g)"/><path d="M0,105 C45,102 58,85 92,91 S145,69 179,76 S228,54 260,61 S310,42 340,51 S392,28 500,22" fill="none" stroke="#ff5b96" stroke-width="2"/></svg>';
}

function drawField(canvas,mode='hero'){
  if(!canvas)return;const dpr=Math.min(devicePixelRatio||1,2),r=canvas.getBoundingClientRect();
  canvas.width=Math.max(1,r.width*dpr);canvas.height=Math.max(1,r.height*dpr);const ctx=canvas.getContext('2d');ctx.scale(dpr,dpr);
  const w=r.width,h=r.height;let t=0;
  function frame(){if(!state.animation)return;ctx.clearRect(0,0,w,h);ctx.globalCompositeOperation='lighter';
    const layers=mode==='hero'?4:5;
    for(let l=0;l<layers;l++){
      const base=h*(.38+l*.11);const amp=(mode==='hero'?18:29)+l*3;ctx.beginPath();
      for(let x=0;x<=w;x+=3){const y=base+Math.sin(x*.018+t*.018+l*.8)*amp+Math.sin(x*.006-t*.013+l)*amp*.45+(x-w*.55)*.035;
        if(x===0)ctx.moveTo(x,y);else ctx.lineTo(x,y)}
      ctx.strokeStyle=`rgba(${255},${40+18*l},${112+15*l},${.16+.055*l})`;ctx.lineWidth=.75+l*.2;ctx.shadowColor='#ff2f78';ctx.shadowBlur=6+l*2;ctx.stroke();
      for(let x=0;x<w;x+=mode==='hero'?18:13){const y=base+Math.sin(x*.018+t*.018+l*.8)*amp+Math.sin(x*.006-t*.013+l)*amp*.45+(x-w*.55)*.035;ctx.fillStyle=`rgba(255,${70+l*20},${135+l*12},${.12+.03*l})`;ctx.fillRect(x,y,1.2,1.2)}
    }
    ctx.shadowBlur=0;ctx.globalCompositeOperation='source-over';t+=1;requestAnimationFrame(frame)}frame();
}
function drawSide(){drawField($('#sideCanvas'),'side')}
function drawTelemetry(){
  const c=$('#telemetryCanvas');if(!c)return;const r=c.getBoundingClientRect(),dpr=Math.min(devicePixelRatio||1,2);c.width=r.width*dpr;c.height=r.height*dpr;const ctx=c.getContext('2d');ctx.scale(dpr,dpr);const w=r.width,h=r.height;ctx.clearRect(0,0,w,h);
  for(let k=0;k<4;k++){ctx.beginPath();for(let x=0;x<w;x+=4){const y=h*.2+k*h*.18+Math.sin(x*.022+k*1.4)*14+Math.sin(x*.006+k)*8;if(x===0)ctx.moveTo(x,y);else ctx.lineTo(x,y)}ctx.strokeStyle=['#ff70a6','#ff3e7e','#c23876','#76425e'][k];ctx.lineWidth=1.4;ctx.stroke()}
}

function boot(){
  renderModels();renderRecent();renderPipeline();renderLog();renderContract();renderCandidate();renderAgents();renderGates();
  drawField($('#heroField'),'hero');drawField($('#morphCanvas'),'workspace');drawSide();
  $$('.nav-item').forEach(b=>b.onclick=()=>switchView(b.dataset.view));
  $$('[data-view-link]').forEach(b=>b.onclick=()=>switchView(b.dataset.viewLink));
  $$('[data-candidate]').forEach(b=>b.onclick=()=>{state.candidate=b.dataset.candidate;renderCandidate();pushLog('EVAL',`Selected candidate ${candidates[state.candidate].name}`)});
  $('#runQualification').onclick=()=>{pushLog('EVAL',`Running workload qualification for ${candidates[state.candidate].name}`);setTimeout(()=>{renderCandidate();pushLog(candidates[state.candidate].verdict==='PROMOTE'?'INFO':'WARN',`${candidates[state.candidate].name} → ${candidates[state.candidate].verdict}`)},650)};
  $('#discoverModel').onclick=()=>{pushLog('INFO','Discovered model candidate: provider-x/model-2026-09');switchView('evolution')};
  $('#scanModels').onclick=()=>pushLog('INFO','Provider scan complete · 2 new candidates quarantined');
  $('#pauseLog').onclick=()=>{state.logPaused=!state.logPaused;$('#pauseLog').textContent=state.logPaused?'Resume ▶':'Pause Ⅱ'};
  $('#soundToggle').onclick=()=>{state.animation=!state.animation;$('#soundToggle').textContent=state.animation?'✦':'○';if(state.animation){drawField($('#heroField'),'hero');drawField($('#morphCanvas'),'workspace');drawSide()}};
  $('#pulseArchitecture').onclick=()=>{const a=$('#architectureMap');a.classList.remove('tracing');void a.offsetWidth;a.classList.add('tracing');pushLog('INFO','Architecture trace: discovery → qualification → adaptation → routing → runtime')};
  $('#globalSearch').addEventListener('input',e=>{const q=e.target.value.toLowerCase().trim();$$('.model-row,.recent-item,.info-card').forEach(el=>el.style.opacity=!q||el.textContent.toLowerCase().includes(q)?'1':'.22')});
  window.addEventListener('resize',()=>{drawTelemetry()},{passive:true});
  setInterval(()=>{if(state.logPaused)return;const events=['Telemetry stable across qualified runtime pool','Workload contract checksum verified','No policy regressions detected','Candidate registry synchronized','Evidence manifest persisted'];pushLog('INFO',events[Math.floor(Math.random()*events.length)])},6500);
}

document.addEventListener('DOMContentLoaded',boot);
