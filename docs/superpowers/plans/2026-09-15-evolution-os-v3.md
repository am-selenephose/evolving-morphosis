# Evolution OS v3 implementation plan

Goal: one Python authority and event ledger, a reference-faithful live projection, and reproducible proof.
Spec: user-supplied architecture + Addenda A–D (2026-09-15). These supersede v2 frontend simulation specifications.
Baseline: public main 4b882a5, local tree identical; 26 pytest tests pass.

## Audit
- core.py: workload-qualified scalar decision; keep compatibility imports.
- evolution.py: one observation per capability, name-only transforms, booleans for apply; retain as explicitly legacy fixture API, exclude from v3 command authority.
- future_flow.py: candidate envelope includes evaluator observations; never expose this fixture API through v3.
- tools.py: qualification implementation belongs in shared application service.
- augment/qualifier.py: older duplicated scoring, compatibility adapter required.
- site/data.js: hand-authored decisions, health, workload and deployment claims.
- site/app.js: timer qualification, random logs, browser-owned candidates and policy controls.
- site/visuals.js: frame-dependent Canvas2D ribbons, no domain event input.
- storage/API/events: absent. No v3 transactional semantics.

## Execution / boundaries
1. Lock Pydantic immutable serializable v3 records; test candidate input rejection, evidence scope/freshness/conflict, kernel authority, adapters, budgets, rollback and ledger tampering before implementation.
2. Implement cohesive v3 package under src/morphosis/os/ (existing evolution.py precludes a conflicting evolution package). Modules: schemas, kernel, graph, probes, compiler, qualifier, storage, application, deployment, topology.
3. Shared commands via MorphosisApplication.command(name,payload,command_id); service-owned evaluator and deployment harness. SQLite atomic event commits and hash-addressed artifacts. Live API, CLI, bound Strands tools use exactly this boundary. Static export uses same service.
4. Replace site app/data/styles/visuals with projection-only client, locked geometry, generated fixtures and shader motion. No local domain mutations. Static mode is backend-generated replay, arbitrary commands require live backend.
5. Generate architecture.svg and interactive topology from same Python node metadata.
6. Execute legacy + v3 + transport contracts, frontend tests, deterministic reference comparison, interaction QA, CLI and verify.sh. Record actual failures and limitations.

### Task 1: Shader motion engine
Files owned: site/visuals.js, tests/frontend/visuals.test.mjs only.
Read the attached visual and Addendum A. Implement VisualEngine API: constructor(getSettings), register(id,type), resize(), start(), stop(), dispose(), consume(event), setProjection(projection).
Canvas IDs heroCanvas/workspaceCanvas/sidebarCanvas. Settings {motion,reducedMotion,quality:'high'|'balanced'|'reduced',visualTest:boolean}. Projection read-only; typed events feed visual impulses and never decisions. One RAF coordinator, delta timestamp, hidden/offscreen pause, DPR <=1.5, ResizeObserver, reused GPU geometry/buffers, deterministic visualTest fixed time. Native WebGL is acceptable to avoid network dependencies. Thick 5–8 folded translucent 3D mesh layers in workspace, dense filament/particle fabric hero and sidebar; reference-like hot pink ridges and concentrated node glow, near-black dominates. No screenshot background, no flat sine-curve substitute. Expose development performance counters only with ?debug=1. Reduced motion preserves composition. Write and execute meaningful tests first (event mapping, deterministic geometry, time step) then implement. Do not edit app/html/styles or other files. No subagents. No commits (root coordinates shared tree). Report work and commands to work/motion-report.md.
