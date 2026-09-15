# Reference-Faithful Evolving Morphosis UI Rebuild Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the rushed layered frontend with a single coherent, reference-faithful interactive dashboard that matches the approved 1672×941 screenshot while surfacing only capabilities already implemented in the Morphosis Python codebase.

**Architecture:** Keep the Python core unchanged. Replace the `site/` frontend load path with one HTML shell, one stylesheet, one state/controller module, one demo-data projection, and one shared canvas animation engine. Build on the isolated branch `rebuild/reference-faithful-ui`; merge and deploy only after Python verification, static JS checks, route smoke tests, interaction checks, and screenshot comparison pass.

**Tech Stack:** Static ES modules, HTML5 Canvas 2D, CSS Grid/Flexbox, localStorage, existing Python 3.12 + Strands Agents backend/demo semantics, GitLab, AppDeploy.

**Spec:** `docs/superpowers/specs/2026-09-15-reference-faithful-ui-rebuild-design.md`

## Global Constraints
- Reference screenshot `/mnt/data/ChatGPT Image Sep 15, 2026, 06_01_41 AM.png` is the visual source of truth.
- Preserve the existing public AppDeploy app ID and URL.
- Do not claim production AgentCore deployment, real training/fine-tuning, or live provider integrations.
- Desktop operational text minimum is 11px; body/rows 13–15px; panel titles 14–16px.
- Hero and workspace must use clearly visible moving thick filled ribbons plus fine filaments and particles.
- Every sidebar page must render meaningful content and working interactions.
- Existing Python semantics and tests must remain untouched and green.

---

### Task 1: Establish the clean frontend architecture
- Replace `site/index.html`; create `site/styles.css`, `site/data.js`, `site/visuals.js`; replace `site/app.js`.
- Retire `site/app.css`, `site/v2.css`, `site/fidelity.css`, `site/fidelity.js` from the page load path.
- Run `node --check site/app.js`, `node --check site/data.js`, `node --check site/visuals.js`.

### Task 2: Rebuild the Overview to the accepted reference
- Encode the reference geometry and typography tokens.
- Match hero composition, quote, metrics, black/raspberry palette, panel density and card rhythm.
- Implement 3–5 thick filled moving hero ribbons + fine filaments + particles across the full hero.
- Implement a denser thick organic Evolution Workspace field.
- Populate Model Ecosystem, Recent Evolutions, Current Workload, five-stage pipeline, and Live Evolution Log.
- Capture at the reference aspect ratio and fix visible drift.

### Task 3: Build functional Evolution Lab and model lifecycle flows
- Render Workload Contract, hard invariants, capability evidence, adaptation proof and evidence trace.
- Implement hot-model rejection, known-model promotion and unknown future-model split gate.
- Implement Add Model validation + localStorage persistence; custom candidates remain UNVERIFIED until evaluated.

### Task 4: Rebuild every secondary page in the same visual system
- Agents: durable runtime boundaries.
- Evaluation: quality gates, invariants, comparison, regression, evidence hash.
- Deployments: runtime pool, canary, rollback, AUTO_APPLY / HUMAN MERGE GATE.
- Observability: animated telemetry, toggles, drift threshold, Run Requalification.
- Datasets: real fixture lineage/previews.
- Infrastructure: Strands, adapters, provider-neutral boundary, deterministic demo, architecture trace.
- Settings: motion/reduced motion/log streaming/thresholds/reset with local persistence.

### Task 5: Finish global product interactions
- Functional global search overlay with keyboard shortcut and navigation.
- Notification drawer.
- Requalification trigger interactions.
- Accessibility, keyboard, Escape-close and reduced-motion handling.

### Task 6: Functional and visual verification
- JS syntax checks.
- Existing `./verify.sh` unchanged.
- Smoke all ten routes and core interactions.
- Native-size fidelity comparison with a written ledger covering shell/layout, typography, palette/glow, thick waves, panel spacing/density, icon/nav alignment and above-fold copy.
- Responsive smoke at desktop/tablet/mobile sizes.

### Task 7: Merge and redeploy the exact verified snapshot
- MR from `rebuild/reference-faithful-ui` to `main`.
- Re-run JS + Python verification against exact branch head.
- Merge only after verification passes.
- Deploy the exact merged `site/` snapshot to existing AppDeploy app `evolving-morphosis-t84odc` without changing the URL.
- Production smoke Overview + Evolution Lab + Observability + Datasets + Settings and verify no deployment errors.
