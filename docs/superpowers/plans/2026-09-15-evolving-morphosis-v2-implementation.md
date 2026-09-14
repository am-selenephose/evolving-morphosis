# Evolving Morphosis v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a hackathon-ready Evolving Morphosis that supports optimized known-model adapters and can safely learn how to integrate unknown future models and novel capabilities.

**Architecture:** A known-model fast lane and unknown-model bootstrap lane converge into an evidence-backed capability registry. Candidate-authored probes/adaptations are sandbox-gated, independently evaluated, packaged as deterministic Evolution Bundles, and promoted through a boundary where reversible runtime/config changes may auto-apply but source changes always require human merge approval.

**Tech Stack:** Python 3.12+, Strands Agents 1.55.1, pytest, static HTML/CSS/JS, SHA-256 evidence hashes.

**Spec:** `docs/superpowers/specs/2026-09-15-evolving-morphosis-v2-hackathon-design.md`

## Global Constraints
- Unknown never means supported.
- Self-report never equals proof.
- Candidate cannot decide its own pass/fail.
- Failed evolution never mutates the incumbent.
- Automatic changes require rollback metadata.
- Source-code evolution always requires human approval.
- Stable core schema must accept namespaced capabilities that did not exist when the repository was written.
- Public build must not expose private AM/Animantum internals or proprietary optimization heuristics.

---

### Task 1: Future-model protocol and Evolution Bundle

**Files:**
- Create: `src/morphosis/evolution.py`
- Modify: `src/morphosis/__init__.py`
- Create: `tests/test_morphosis_v2.py`
- Create: `fixtures/future_model_x.json`

**Interfaces:**
- Produces: `KnownAdapterRegistry`, `bootstrap_candidate`, `CapabilityRegistry`, `ProbeProposal`, `verify_probe_proposal`, `compile_adaptation`, `EvolutionBundle`, `build_evolution_bundle`, `needs_requalification`.

- [ ] Write failing tests for known fast path, unknown bootstrap, novel capability registration, unverified self-report, unsafe probe rejection, adapted-vs-native fallback, runtime/source approval boundaries, deterministic bundle hash, incumbent immutability, and drift requalification.
- [ ] Run the focused suite and verify RED because v2 interfaces do not exist.
- [ ] Implement the minimal pure-Python protocol and evidence hashing.
- [ ] Run focused tests and existing Morphosis tests; require GREEN.
- [ ] Commit the protocol slice.

### Task 2: Strands future-model discovery/evolution loop

**Files:**
- Create: `src/morphosis/evolution_agent.py`
- Modify: `src/morphosis/tools.py`
- Modify: `src/morphosis/agent.py`
- Test: `tests/test_morphosis_v2.py`

**Interfaces:**
- Consumes Task 1 protocol.
- Produces a real Strands tool loop that can bootstrap a synthetic unknown future model, qualify a novel capability, and return an Evolution Bundle while verifier authority stays outside the candidate.

- [ ] Add a failing Strands integration test for `future-model-x`.
- [ ] Verify RED.
- [ ] Implement bounded Strands tools and deterministic demo model behavior.
- [ ] Verify GREEN together with all prior tests.
- [ ] Commit the Strands slice.

### Task 3: Raspberry console and advanced architecture

**Files:**
- Modify: `site/index.html`
- Modify: `site/app.css`
- Modify: `site/app.js`
- Modify: `architecture.svg`

**Interfaces:**
- Presents Known Fast Lane + Unknown Future Lane → Capability Evidence Graph → Morphogenesis Engine → Sandbox → Evolution Bundle → Gate → Strands ModelRouter → Agent → Requalification.

- [ ] Preserve the approved near-black / radiant raspberry design while tightening typography, contrast, and panel hierarchy.
- [ ] Add Evolution Lab states for UNVERIFIED claim, probe verification, novel capability extension, source-vs-runtime gates, and PROMOTE/HOLD/REJECT.
- [ ] Replace the basic architecture with an expanded living-system map and explicit MODEL-WRITABLE vs INDEPENDENT GOVERNANCE zones.
- [ ] Verify JS syntax and render/click QA when a browser/device is available.
- [ ] Commit the UI slice.

### Task 4: Submission evidence and narrative

**Files:**
- Modify: `README.md`
- Modify: `SUBMISSION.md`
- Modify: `DEMO_SCRIPT.md`
- Modify: `verify.sh`
- Modify: `SHA256SUMS`

**Interfaces:**
- Produces truthful reproducibility instructions and the final hackathon story.

- [ ] Document known-adapter fast path plus unknown-future-model bootstrap without claiming foundation-model retraining.
- [ ] Disclose pre-existing Autonomous Morphology research direction while identifying the hackathon implementation as newly built.
- [ ] Make `./verify.sh` run all v2 tests and deterministic demos.
- [ ] Run canonical verification and capture exact pass count/output.
- [ ] Generate/update architecture and demo assets only after verification.
- [ ] Merge only after the full branch is green and submission claims match evidence.
