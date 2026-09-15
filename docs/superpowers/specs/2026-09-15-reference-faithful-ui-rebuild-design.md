# Evolving Morphosis — Reference-Faithful UI Rebuild

## Goal
Rebuild the entire static frontend so the public application matches the supplied 1672×941 reference composition as closely as practical while remaining truthful to the actual Morphosis codebase and keeping the existing live AppDeploy URL.

This is a replacement of the current frontend architecture, not another overlay patch.

## Non-negotiable visual requirements
- Preserve the reference composition: 244px-class left rail, slim top bar, large serif hero, three-column dashboard body, two-row lower dashboard, black base, radiant raspberry/rose borders and glow.
- The hero waveform must be full-width, clearly visible behind the hero copy, and continuously animated.
- The central Evolution Workspace must use a thicker luminous organic ribbon/mesh field, not sparse sine lines.
- Typography must be readable everywhere. No 7–9px operational text on desktop.
- All pages must use the same display serif / UI sans / mono-label hierarchy as the first page.
- Every route must feel like the same product, not a different template.
- No moon or unrelated decorative objects.
- The reference screenshot is the visual source of truth for spacing, density, glow, card rhythm, and proportions.

## Truthfulness requirements
The UI may visualize deterministic demo data, but it must not claim backend capabilities that do not exist.

The implementation already supports and may surface:
- Workload contracts and hard invariants.
- PROMOTE / HOLD / REJECT qualification decisions.
- Provider metadata as priors, never proof.
- Known-model fast-path adapters.
- Unknown future-model bootstrap.
- Novel capability claims stored as UNKNOWN / UNVERIFIED.
- Bounded capability probes with independent observation.
- Compatibility adaptation plans.
- Independent adaptation verification.
- Evolution Bundles with rollback and evidence lineage.
- Runtime/config AUTO_APPLY only after all gates pass.
- Source evolution behind HUMAN_APPROVAL_REQUIRED.
- Requalification on observed drift.
- Real Strands agent assembly around the qualification tools.

The UI must not claim:
- Real production AgentCore deployment.
- Training/fine-tuning models unless implemented.
- Live provider integrations that are not connected.
- Real user/agent counts unless derived from demo state.

## Frontend architecture
Replace the overlapping `app.css` + `v2.css` + `fidelity.css` stack with one coherent design system.

Target files:
- `site/index.html` — stable shell and semantic page containers.
- `site/styles.css` — the only visual stylesheet.
- `site/app.js` — app state, navigation, user interactions, qualification simulation.
- `site/visuals.js` — one shared requestAnimationFrame loop for hero, sidebar, workspace, and telemetry canvases.
- `site/data.js` — demo entities derived from repository fixtures and Morphosis semantics.

Retire from the page load path:
- `site/app.css`
- `site/v2.css`
- `site/fidelity.css`
- `site/fidelity.js`

The old files may be deleted after the replacement is verified.

## Design system
Desktop target: 1672×941 reference.

### Layout
- Sidebar: 244px at wide desktop, sticky full-height.
- Top bar: 46–48px.
- Content horizontal padding: 18–22px.
- Overview hero: about 300px tall.
- Main dashboard columns: approximately 1.0 / 1.55 / 1.18.
- Panel gaps: 10–12px.
- Panel header height: 38–42px.
- Responsive breakpoints must preserve hierarchy instead of simply shrinking everything.

### Typography
- Display: Georgia / Times-compatible serif stack.
- UI: system sans stack.
- Technical labels/logs: system monospace.
- Desktop minimum readable operational size: 11px.
- Body / row text: 13–15px.
- Panel titles: 14–16px.
- Secondary page headers: same visual family as the overview hero.
- Hero title: clamp around 58–68px at reference width.

### Palette
- Base: near-black / true-black.
- Primary glow: raspberry `#ff2f78` family.
- Highlight: rose / pale pink.
- Status colors only for semantic state: mint, blue, amber, reject-red.
- Borders should glow selectively, not every surface equally.

## Motion system
Use one shared animation loop. Cap DPR and particle counts for performance.

### Hero field
Create a full-width animated field behind the copy using:
- 3–5 thick filled translucent ribbon bands.
- 30–60 thinner luminous filaments.
- Sparse particles/nodes near the right and center.
- Left-side opacity attenuation only enough to keep copy readable; never fade the field away.
- Slow continuous phase motion.

### Evolution Workspace field
Create a denser organic stack with:
- Multiple translucent filled ribbons.
- Internal filament lines.
- Bright anchor nodes.
- Subtle parallax drift.
- Stronger glow than the hero field.

### Sidebar field
A smaller cropped version of the same visual language.

### Telemetry
Animate actual trend lines and trigger markers, not a blank canvas.

Respect `prefers-reduced-motion` and expose a UI animation toggle.

## Page map
The reference sidebar is the navigation source of truth.

### Overview
Reproduce the reference composition while using truthful Morphosis data.
- Hero copy, metrics, quote.
- Model Ecosystem list.
- Evolution Workspace.
- Recent Evolutions.
- Current Workload.
- Five-stage public pipeline.
- Live Evolution Log.

Use code-derived or demo-grounded metrics instead of unsupported fake operational numbers. Suggested hero metrics: verified tests, model paths, gate health.

### Evolution Lab
Functional candidate qualification.
- New hot model rejection.
- Known qualified model promotion.
- Unknown future model bootstrap.
- Workload Contract.
- Capability evidence.
- Adaptation proof.
- Evolution Bundle split gate.
- Run qualification button must visibly change state/logs.

### Model Ecosystem
- Known/unknown model cards.
- Search/filter.
- Add / Discover Model opens a real modal.
- Added demo candidates persist in localStorage.
- Candidate claims remain explicitly UNVERIFIED until evaluated.

### Agents
- Workload Agent.
- Morphosis Discovery.
- Morphogenesis.
- Promotion Control.
- Show durable boundaries and current runtime/model binding.

### Evaluation
- Quality gates.
- Hard invariants.
- Candidate comparison.
- Regression chart.
- Evidence hash display.

### Deployments
- Runtime pool.
- Canary percentage.
- Rollback status.
- Runtime/config auto-apply state.
- Source changes must visibly remain human-gated.

### Observability
- Animated telemetry.
- Requalification triggers with readable spacing.
- Trigger controls that actually toggle in the demo state.
- Run requalification action that appends a log event and routes to the Evolution Lab result.

### Datasets
This page is new but grounded in real repository fixtures.
Surface:
- `fixtures/morphosis_contract.json`
- `fixtures/morphosis_candidates.json`
- `fixtures/future_model_x.json`
- `fixtures/opportunities.json`

Provide dataset cards, lineage/type metadata, and expandable previews. Do not imply a remote dataset service.

### Infrastructure
Ground this in actual code boundaries:
- Strands Agents SDK.
- KnownAdapterRegistry.
- Provider-neutral endpoint boundary.
- Bedrock-compatible path where applicable.
- Deterministic demo model path.
- Runtime / source evolution split.
- Architecture trace as a sub-view so the public sidebar can stay faithful to the reference.

### Settings
Functional demo/session controls:
- Animation on/off.
- Reduced motion.
- Log streaming.
- Qualification threshold display.
- Requalification drift threshold.
- Persist user-facing display/session settings in localStorage.

Settings must be labelled as demo/session controls unless they directly map to backend configuration.

## Top bar interactions
- Global search opens a results overlay across models, agents, datasets, pages, and recent evolutions.
- Notification bell opens a drawer populated by promotion/rejection/requalification events.
- Account area remains non-authenticated demo identity; do not imply login.

## Data flow
1. `data.js` defines the static demo projection of repository-backed entities and fixtures.
2. `app.js` owns state transitions and user interactions.
3. `visuals.js` reads animation settings only; it does not own product state.
4. Qualification controls update frontend demo state using the same semantic rules already demonstrated by the Python engine.
5. Datasets / infrastructure pages display repository-grounded information, not fabricated external services.
6. localStorage stores user-added demo candidates and UI settings only.

## Failure / empty states
- Every page must render useful content on first visit.
- No empty card grids.
- Search with no result shows an explicit empty state.
- Invalid Add Model input shows validation.
- Qualification failures explain the failing invariant.
- Animation errors must not block navigation or content.

## Testing
Before updating production:
- Run existing Python verification (`./verify.sh`) to prove core semantics remain untouched.
- Add or update AppDeploy E2E workflows for:
  1. Unknown future model qualification.
  2. Hard-invariant rejection.
  3. Observability trigger toggle + requalification.
  4. Dataset preview + global search.
  5. Add demo model + persistence / settings.
- Smoke every sidebar route.
- Capture wide desktop screenshots at approximately the reference aspect ratio.
- Compare overview screenshot against the supplied reference for layout, hierarchy, glow, and waveform visibility.
- Verify mobile/tablet breakpoints after desktop fidelity is locked.

## Deployment
- Keep existing AppDeploy app ID and public URL.
- Build and validate on a feature branch first.
- Update GitLab and AppDeploy from the same final source snapshot.
- Do not mutate the submitted URL.

## Acceptance criteria
The rebuild is complete only when:
- Overview visually follows the supplied reference rather than merely sharing its colors.
- Thick hero and workspace waves visibly move.
- No desktop text is microscopically small.
- All sidebar pages work and have meaningful content.
- Datasets, Infrastructure, and Settings are real interactive frontend pages grounded in repository data/configuration.
- Evolution Lab remains faithful to the implemented future-model qualification semantics.
- Search, notifications, Add Model, requalification triggers, and settings controls work.
- Existing Python tests still pass.
- Live AppDeploy URL and GitLab frontend are in sync.
