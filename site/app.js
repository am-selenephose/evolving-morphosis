const state = {
  view: 'overview',
  candidate: 'unknown',
  pipeline: 4,
  logPaused: false,
  animation: true,
};

const models = [
  { name: 'incumbent-v1', meta: 'Current workload-qualified runtime', status: 'ACTIVE', icon: '◉' },
  { name: 'bedrock-known-adapter', meta: 'Known fast lane · optimized provider profile', status: 'READY', icon: '◇' },
  { name: 'future-model-x', meta: 'Unknown bootstrap · novel capability discovered', status: 'EVOLVING', icon: '∞' },
  { name: 'new-hot-model', meta: 'High aggregate score · invariant failure', status: 'REJECTED', icon: '⊘' },
];

const recent = [
  { title: 'future-model-x', sub: 'Novel capability verified: future.semantic_patch.v1', status: 'PROMOTED', time: 'now', icon: '∞' },
  { title: 'Adaptation proof', sub: 'semantic-patch-wrapper independently verified by round-trip evaluation', status: 'PROMOTED', time: '1m', icon: '✦' },
  { title: 'Source evolution', sub: 'Adapter proposal held at the human merge gate', status: 'HOLD', time: '2m', icon: '⌘' },
  { title: 'new-hot-model', sub: 'Authorization invariant failed despite a higher aggregate score', status: 'REJECTED', time: '8m', icon: '⊘' },
  { title: 'Runtime bundle', sub: 'Rollback-backed runtime evolution is eligible for auto-apply', status: 'PROMOTED', time: '12m', icon: '◈' },
];

const candidates = {
  hot: {
    name: 'new-hot-model', verdict: 'REJECT', delta: '+0.147 aggregate',
    reason: 'Authorization failed as a hard invariant. Higher aggregate performance cannot override the workload contract.',
    hash: '6f28a13995b2a29348f84da1a64acf7c396eb9274bc26b4dbdfb675078307a77',
    metrics: [['Tool use', 1, .90], ['Structured output', 1, .95], ['Task quality', .99, .80], ['Authorization', .72, 1], ['Evidence lineage', 1, 1]],
    traces: [['DISCOVER', 'provider claim', 'UNVERIFIED'], ['PROBE', 'tool + schema', 'PASS'], ['EVAL', 'workload', '0.99'], ['POLICY', 'authorization', 'FAIL'], ['BUNDLE', 'promotion', 'BLOCKED'], ['DECIDE', 'candidate', 'REJECT']],
  },
  future: {
    name: 'future-qualified-model', verdict: 'PROMOTE', delta: '+0.058 workload score',
    reason: 'The known capability set passes the workload contract without an invariant regression and remains within the required operating boundary.',
    hash: 'f352c368e5b1d707fee81c34eda4b41bbe1569f79145b4c102103f032b09efbe',
    metrics: [['Tool use', .99, .90], ['Structured output', .99, .95], ['Task quality', .96, .80], ['Authorization', 1, 1], ['Evidence lineage', 1, 1]],
    traces: [['DISCOVER', 'known adapter', 'FAST PATH'], ['PROBE', 'workload', 'PASS'], ['EVAL', 'quality', '0.96'], ['POLICY', 'invariants', 'PASS'], ['ROUTE', 'canary', '10%'], ['DECIDE', 'candidate', 'PROMOTE']],
  },
  unknown: {
    name: 'future-model-x', verdict: 'PROMOTE', delta: 'NOVEL CAPABILITY + VERIFIED ADAPTATION',
    reason: 'The unknown model capability is independently observed, and semantic-patch-wrapper passes a separate adaptation proof. Runtime evolution may auto-apply with rollback; source evolution still requires human merge approval.',
    hash: 'future-model-x · deterministic Evolution Bundle',
    metrics: [['Novel capability', .97, .90], ['Adaptation proof', .96, .90], ['Round-trip preserved', 1, 1], ['Side-effect free', 1, 1], ['Human source gate', 1, 1]],
    traces: [['BOOTSTRAP', 'future-model-x', 'UNKNOWN'], ['CLAIM', 'semantic_patch', 'UNVERIFIED'], ['PROBE', 'capability', 'OBSERVED'], ['MORPH', 'semantic-patch-wrapper', 'VERIFIED'], ['BUNDLE', 'runtime/source', 'SPLIT GATE'], ['DECIDE', 'runtime', 'PROMOTE']],
  },
};

const contract = [
  ['Tool use', '≥ 0.90'], ['Structured output', '≥ 0.95'], ['Task quality', '≥ 0.80'],
  ['Authorization', 'hard invariant = 1.00'], ['Evidence lineage', 'hard invariant = 1.00'], ['Source merge', 'human authority'],
];

const pipeline = [
  ['1. BOOTSTRAP', 'Known fast lane / unknown endpoint', '⌁'],
  ['2. DISCOVER', 'Claims enter as UNKNOWN priors', '⌕'],
  ['3. PROBE', 'Independent capability evidence', '∑'],
  ['4. MORPH', 'Verify compatibility proposal', '⌘'],
  ['5. GATE', 'Evolution Bundle + policy', '△'],
  ['6. SERVE', 'Canary / route / requalify', '◈'],
];

const agents = [
  ['Workload Agent', 'Professional opportunity triage', 'Human authorization', 'Healthy'],
  ['Morphosis Discovery', 'Unknown-model capability intake', 'Self-report is not proof', 'Healthy'],
  ['Morphogenesis', 'Compatibility proposal compiler', 'Independent verifier', 'Healthy'],
  ['Promotion Control', 'Evolution Bundle gate', 'Human source authority', 'Healthy'],
];

let logs = [
  ['02:52:11', 'INFO', 'future-model-x entered the UNKNOWN_BOOTSTRAP lane'],
  ['02:52:12', 'EVAL', 'self-report future.semantic_patch.v1 stored as UNKNOWN / UNVERIFIED'],
  ['02:52:13', 'INFO', 'bounded capability probe accepted by the verifier'],
  ['02:52:14', 'EVAL', 'capability observation SUPPORTED · score 0.970'],
  ['02:52:15', 'EVAL', 'semantic-patch-wrapper round-trip verified · score 0.960'],
  ['02:52:16', 'INFO', 'runtime Evolution Bundle → AUTO_APPLY with rollback'],
  ['02:52:16', 'WARN', 'source Evolution Bundle → HUMAN_APPROVAL_REQUIRED'],
];

const $ = (query, root = document) => root.querySelector(query);
const $$ = (query, root = document) => [...root.querySelectorAll(query)];

function badgeClass(status) { return status.toLowerCase().replace(/\s+/g, '-'); }
function nowTime() { return new Date().toLocaleTimeString('en-GB', { hour12: false }); }

function switchView(view) {
  state.view = view;
  $$('.view').forEach((item) => item.classList.toggle('active', item.id === `view-${view}`));
  $$('.nav-item').forEach((item) => item.classList.toggle('active', item.dataset.view === view));
  if (view === 'observability') drawTelemetry();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function renderModels() {
  $('#modelList').innerHTML = models.map((model) => `<div class="model-row"><div class="model-icon">${model.icon}</div><div><strong>${model.name}</strong><small>${model.meta}</small></div><span class="badge ${badgeClass(model.status)}">${model.status}</span></div>`).join('');
  $('#modelCards').innerHTML = models.map((model, index) => `<article class="info-card"><div class="card-icon">${model.icon}</div><h3>${model.name}</h3><p>${model.meta}. ${index === 2 ? 'No pre-written model identity is required; observed evidence teaches the runtime how to integrate it.' : 'This candidate remains governed by workload evidence.'}</p><footer><span>${model.status}</span><span>${index === 2 ? 'unknown future lane' : index === 1 ? 'known fast lane' : 'evidence governed'}</span></footer></article>`).join('');
}

function renderRecent() {
  $('#recentList').innerHTML = recent.map((item) => `<div class="recent-item"><div class="event-icon">${item.icon}</div><div><strong>${item.title}</strong><small>${item.sub}</small></div><span class="badge ${badgeClass(item.status)}">${item.status}</span><time>${item.time}</time></div>`).join('');
}

function renderPipeline() {
  $('#pipeline').innerHTML = pipeline.map((step, index) => `<div class="pipe-step ${index === state.pipeline ? 'active' : ''}" data-step="${index}"><div class="circle">${step[2]}</div><b>${step[0]}</b><small>${step[1]}</small></div>`).join('');
  $$('.pipe-step').forEach((element) => { element.onclick = () => { state.pipeline = Number(element.dataset.step); renderPipeline(); pushLog('EVAL', `Pipeline focus → ${pipeline[state.pipeline][0]}`); }; });
}

function renderLog() { $('#liveLog').innerHTML = logs.slice(0, 7).map((line) => `<div class="logline"><time>${line[0]}</time><span class="level ${line[1].toLowerCase()}">${line[1]}</span>${line[2]}</div>`).join(''); }
function pushLog(level, text) { logs.unshift([nowTime(), level, text]); renderLog(); }
function renderContract() { $('#contractMetrics').innerHTML = contract.map((item) => `<div class="contract-metric"><strong>${item[0]}</strong><span>${item[1]}</span></div>`).join(''); }

function ensureUnknownSelector() {
  const segmented = $('.segmented');
  if (segmented && !segmented.querySelector('[data-candidate="unknown"]')) segmented.insertAdjacentHTML('beforeend', '<button data-candidate="unknown">Unknown future</button>');
}

function renderCandidate() {
  const candidate = candidates[state.candidate];
  $('#candidateMetrics').innerHTML = candidate.metrics.map((metric) => `<div class="metric-line ${metric[1] < metric[2] ? 'danger' : ''}"><b>${metric[0]}</b><div class="track"><div class="fill" style="width:${Math.round(metric[1] * 100)}%"></div></div><span>${metric[1].toFixed(2)}</span></div>`).join('');
  $('#decisionCard').innerHTML = `<div class="verdict ${candidate.verdict === 'PROMOTE' ? 'promote' : ''}">${candidate.verdict}<small>${candidate.delta}</small></div><div><p>${candidate.reason}</p><code>${candidate.hash}</code></div>`;
  $('#evidenceTrace').innerHTML = candidate.traces.map((trace) => `<div class="trace-node"><b>${trace[0]}</b><span>${trace[1]}<br><small>${trace[2]}</small></span></div>`).join('');
  $$('[data-candidate]').forEach((button) => button.classList.toggle('active', button.dataset.candidate === state.candidate));
}

function renderFutureProof() {
  const lab = $('#view-evolution .lab-grid');
  if (!lab || $('#futureProof')) return;
  lab.insertAdjacentHTML('afterend', '<article id="futureProof" class="panel future-proof"><div class="panel-head"><div><span>FUTURE-MODEL EVOLUTION PROOF</span><small>future-model-x · capability absent from the original schema</small></div><b class="live-label">EVIDENCE LOCKED</b></div><div class="future-chain"><div><b>UNKNOWN</b><span>minimal endpoint bootstrap</span></div><i>→</i><div><b>UNVERIFIED</b><span>future.semantic_patch.v1</span></div><i>→</i><div><b>OBSERVED</b><span>capability probe · 0.97</span></div><i>→</i><div><b>VERIFIED</b><span>semantic-patch-wrapper · 0.96</span></div><i>→</i><div class="split"><b>AUTO / HUMAN</b><span>runtime auto-apply · source merge gate</span></div></div></article>');
}

function renderAgents() {
  $('#agentCards').innerHTML = agents.map((agent, index) => `<article class="info-card"><div class="card-icon">${['⌘', '⌕', '◫', '◉'][index]}</div><h3>${agent[0]}</h3><p>${agent[1]}. Durable boundary: ${agent[2]}.</p><footer><span>${agent[3]}</span><span>evolution layer</span></footer></article>`).join('');
}

function renderGates() {
  const gates = [['Capability observation', 97], ['Adaptation round-trip', 96], ['Workload invariants', 100], ['Rollback present', 100], ['Human source gate', 100]];
  $('#qualityGates').innerHTML = gates.map((gate) => `<div class="gate-row"><b>${gate[0]}</b><div class="gatebar"><span style="width:${gate[1]}%"></span></div><em>${gate[1]}%</em></div>`).join('');
  $('#miniChart').innerHTML = '<svg viewBox="0 0 500 130" preserveAspectRatio="none" width="100%" height="100%"><defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#ff4f8c" stop-opacity=".4"/><stop offset="1" stop-color="#ff4f8c" stop-opacity="0"/></linearGradient></defs><path d="M0,108 C55,101 75,88 115,91 S180,73 218,75 S280,48 320,56 S390,27 500,19 L500,130 L0,130Z" fill="url(#g)"/><path d="M0,108 C55,101 75,88 115,91 S180,73 218,75 S280,48 320,56 S390,27 500,19" fill="none" stroke="#ff5b96" stroke-width="2"/></svg>';
}

function renderArchitecture() {
  const map = $('#architectureMap');
  if (!map) return;
  map.className = 'architecture-map-v2';
  map.innerHTML = '<div class="lane known"><div class="lane-kicker">KNOWN MODEL FAST LANE</div><h3>Optimized adapters first.</h3><p>Bedrock · hosted providers · local runtimes</p><small>Fast onboarding. Still evidence-qualified.</small></div><div class="lane unknown"><div class="lane-kicker">UNKNOWN FUTURE LANE</div><h3>No hard-coded model entry.</h3><p>minimal transport · self-description · novel claims</p><small>Everything begins UNKNOWN.</small></div><div class="converge">↓</div><div class="arch-core evidence"><b>CAPABILITY EVIDENCE GRAPH</b><strong>Claims are priors. Behavior is proof.</strong><span>dynamic namespaces · provenance · confidence · evidence hashes</span></div><div class="registry"><b>NOVEL CAPABILITY REGISTRY</b><span>future.semantic_patch.v1</span><em>UNKNOWN → OBSERVED</em></div><div class="arch-core morph"><b>MORPHOGENESIS ENGINE</b><strong>The runtime changes shape around the model.</strong><div class="morph-grid"><span>SCHEMA</span><span>TOOLS</span><span>CONTEXT</span><span>FALLBACK</span></div></div><div class="proposal"><b>MODEL-WRITABLE PROPOSAL ZONE</b><span>capability claims</span><span>bounded probes</span><span>adapter / config transforms</span><span>source patch proposals</span><small>cannot rewrite the evaluator or merge authority</small></div><div class="gate-row-v2"><div><b>SANDBOX GATE</b><span>bounded execution</span></div><i>→</i><div class="meta"><b>INDEPENDENT META-EVAL</b><span>capability + adaptation + workload + policy</span></div><i>→</i><div><b>EVOLUTION BUNDLE</b><span>evidence + rollback + lineage</span></div></div><div class="split-gates"><div class="auto"><b>RUNTIME / CONFIG</b><strong>AUTO_APPLY</strong><span>only after all gates pass and rollback is present</span></div><div class="human"><b>SOURCE EVOLUTION</b><strong>HUMAN MERGE GATE</strong><span>model proposes · human approves</span></div></div><div class="serve"><b>STRANDS SERVING PLANE</b><span>ModelRouter → workload agent → tools / runtime</span></div><div class="feedback"><b>OBSERVABILITY LOOP</b><span>traces → drift → requalification → rollback → evidence archive</span></div><div class="governance"><b>INDEPENDENT GOVERNANCE</b><span>hard invariants · evaluator · evidence semantics · human source authority</span></div>';
}

function drawField(canvas) {
  if (!canvas) return;
  const context = canvas.getContext('2d');
  const rect = canvas.getBoundingClientRect();
  const dpr = Math.min(devicePixelRatio || 1, 2);
  canvas.width = Math.max(1, rect.width * dpr); canvas.height = Math.max(1, rect.height * dpr); context.scale(dpr, dpr); let tick = 0;
  function frame() {
    if (!state.animation) return;
    context.clearRect(0, 0, rect.width, rect.height); context.globalCompositeOperation = 'lighter';
    for (let layer = 0; layer < 7; layer += 1) {
      context.beginPath();
      for (let x = 0; x <= rect.width; x += 3) { const y = rect.height * (.28 + layer * .075) + Math.sin(x * .018 + tick * .02 + layer * .7) * (16 + layer * 3) + Math.sin(x * .006 - tick * .012 + layer) * 12; x === 0 ? context.moveTo(x, y) : context.lineTo(x, y); }
      context.strokeStyle = `rgba(255,${35 + 16 * layer},${105 + 13 * layer},${.12 + .04 * layer})`; context.lineWidth = .8 + layer * .18; context.shadowColor = '#ff2f78'; context.shadowBlur = 10 + layer * 2; context.stroke();
    }
    context.globalCompositeOperation = 'source-over'; tick += 1; requestAnimationFrame(frame);
  }
  frame();
}

function drawTelemetry() {
  const canvas = $('#telemetryCanvas'); if (!canvas) return;
  const rect = canvas.getBoundingClientRect(); if (!rect.width || !rect.height) return;
  const dpr = Math.min(devicePixelRatio || 1, 2); canvas.width = rect.width * dpr; canvas.height = rect.height * dpr;
  const context = canvas.getContext('2d'); context.scale(dpr, dpr); context.clearRect(0, 0, rect.width, rect.height);
  ['#ff8eb7', '#ff4f8d', '#c93e7a', '#7f3f61'].forEach((color, index) => { context.beginPath(); for (let x = 0; x <= rect.width; x += 4) { const y = rect.height * (.2 + index * .18) + Math.sin(x * .022 + index * 1.4) * 14 + Math.sin(x * .006 + index) * 8; x === 0 ? context.moveTo(x, y) : context.lineTo(x, y); } context.strokeStyle = color; context.lineWidth = 1.5; context.shadowColor = color; context.shadowBlur = 8; context.stroke(); }); context.shadowBlur = 0;
}

function boot() {
  renderModels(); renderRecent(); renderPipeline(); renderLog(); renderContract(); ensureUnknownSelector(); renderCandidate(); renderFutureProof(); renderAgents(); renderGates(); renderArchitecture(); drawField($('#heroField')); drawField($('#morphCanvas')); drawField($('#sideCanvas'));
  $$('.nav-item').forEach((button) => button.onclick = () => switchView(button.dataset.view));
  $$('[data-view-link]').forEach((button) => button.onclick = () => switchView(button.dataset.viewLink));
  $$('[data-candidate]').forEach((button) => button.onclick = () => { state.candidate = button.dataset.candidate; renderCandidate(); pushLog('EVAL', `Selected ${candidates[state.candidate].name}`); });
  $('#runQualification').onclick = () => { pushLog('EVAL', `Running evidence gates for ${candidates[state.candidate].name}`); setTimeout(() => pushLog(candidates[state.candidate].verdict === 'PROMOTE' ? 'INFO' : 'WARN', `${candidates[state.candidate].name} → ${candidates[state.candidate].verdict}`), 350); };
  $('#discoverModel').onclick = () => { state.candidate = 'unknown'; switchView('evolution'); renderCandidate(); pushLog('INFO', 'future-model-x entered the UNKNOWN_BOOTSTRAP lane'); };
  $('#scanModels').onclick = () => pushLog('INFO', 'Provider scan complete · unknown endpoint quarantined for evidence');
  $('#pauseLog').onclick = () => { state.logPaused = !state.logPaused; $('#pauseLog').textContent = state.logPaused ? 'Resume ▶' : 'Pause Ⅱ'; };
  $('#soundToggle').onclick = () => { state.animation = !state.animation; $('#soundToggle').textContent = state.animation ? '✦' : '○'; if (state.animation) { drawField($('#heroField')); drawField($('#morphCanvas')); drawField($('#sideCanvas')); } };
  $('#pulseArchitecture').onclick = () => { const architecture = $('#architectureMap'); architecture.classList.remove('tracing'); void architecture.offsetWidth; architecture.classList.add('tracing'); pushLog('INFO', 'Trace: unknown bootstrap → evidence → morphogenesis → independent gate → serving'); };
  $('#globalSearch').addEventListener('input', (event) => { const query = event.target.value.toLowerCase().trim(); $$('.model-row,.recent-item,.info-card').forEach((element) => { element.style.opacity = !query || element.textContent.toLowerCase().includes(query) ? '1' : '.25'; }); });
  window.addEventListener('resize', () => { if (state.view === 'observability') drawTelemetry(); }, { passive: true });
  setInterval(() => { if (!state.logPaused) pushLog('INFO', ['Evidence manifest persisted', 'No hard-invariant regression', 'Adaptation proof remains valid', 'Drift monitor armed'][Math.floor(Math.random() * 4)]); }, 7000);
}

document.addEventListener('DOMContentLoaded', boot);
