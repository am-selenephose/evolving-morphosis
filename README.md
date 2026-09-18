# Evolving Morphosis

**Models evolve. Your agents should evolve with them.**

Evolving Morphosis is a Strands-based **model-evolution control plane for professional AI/agent teams**. It automates the repetitive work that begins every time a new model generation appears: capability discovery, compatibility analysis, workload regression testing, adaptation, promotion, rollback, and requalification.

Morphosis has two ingress lanes:

- **Known-model fast path** — optimized adapters/profiles for models and providers we already understand.
- **Unknown future-model path** — a model that did not exist when Morphosis was written can enter through a minimal transport boundary, describe novel capabilities, propose bounded probes and compatibility changes, and teach the runtime how it needs to be integrated.

Neither lane inherits trust. **Metadata and self-report are priors; observed workload behavior is proof.**

## The future-model proof

The repository includes a synthetic `future-model-x` that advertises a capability that is absent from Morphosis's stable core schema:

`future.semantic_patch.v1`

Morphosis does not need a hard-coded model entry or closed capability enum. The flow is:

1. Bootstrap the unknown endpoint into `UNKNOWN_BOOTSTRAP`.
2. Record the self-reported novel capability as `UNKNOWN / UNVERIFIED`.
3. Accept a bounded candidate-proposed probe description, but not its verdict.
4. Independently verify the observation and register the novel namespaced capability dynamically.
5. Consume the model's proposed compatibility transform (`semantic-patch-wrapper`).
6. Compile it as an **ADAPTED** capability rather than falsely calling it native.
7. Build deterministic SHA-256 **Evolution Bundles** containing change intent, evidence, rollback metadata, lineage, and promotion state.
8. Mark a reversible runtime/config bundle `AUTO_APPLY` only after gates pass.
9. Mark the same model's source-code adapter proposal `HUMAN_APPROVAL_REQUIRED` even when all tests pass.

The candidate can help evolve the integration around itself. It cannot grade itself, weaken hard invariants, rewrite evidence semantics, or merge its own source changes.

## Why it exists

Agent code is often coupled to one model generation's assumptions about tool calling, structured output, context, reasoning controls, latency, cost, or provider quirks. AI platform engineers repeatedly inspect release notes, compare API surfaces, patch adapters, rerun evaluations, select canaries, and monitor regressions whenever the model landscape changes.

A generic router solves a different problem: **which known candidate should handle this invocation?** Strands already provides `ModelRouter` for that serving layer.

Morphosis operates one level above routing: **which model deserves to become a candidate, what must change around it, and can that evolution be promoted without breaking the agent contract?**

## Architecture

![Evolving Morphosis v3 architecture](architecture.svg)

The public reference implementation separates these boundaries:

1. **Known Model Fast Lane** — optimized adapters accelerate models we already know.
2. **Unknown Future Lane** — minimal bootstrap for arbitrary future endpoints; no hard-coded model name required.
3. **Capability Evidence Graph** — namespaced capabilities with provenance, confidence, status, and evidence hashes.
4. **Novel Capability Registry** — unknown capability identifiers can be added without editing the stable core schema.
5. **Morphogenesis Engine** — candidate-proposed schema/tool/context/fallback adaptations are compiled around the model.
6. **Sandbox / Independent Meta-Eval** — candidate proposals are tested outside candidate-controlled promotion logic.
7. **Evolution Bundle** — content-addressed change + evidence + rollback + lineage + recommendation.
8. **Promotion Boundary** — reversible runtime/config evolution may auto-apply; source evolution always stops for human merge approval.
9. **Serving Plane** — qualified candidates can enter a Strands ModelRouter/runtime pool without rewriting the workload contract.
10. **Observability Loop** — drift can trigger requalification or rollback.

## Real Strands integration

This project uses **Strands Agents SDK 1.55.1** directly. Credential-free deterministic model adapters drive real Strands tool-use loops for both:

- incumbent-versus-candidate workload qualification; and
- unknown future-model onboarding through the `evolve_future_model` tool.

The deterministic policy/evidence engine remains outside model authority. Strands orchestrates the tool loop; Morphosis owns the qualification boundary.

## First professional workload: Evolving Morphosis

Evolving Morphosis includes a concrete professional opportunity-triage workload that turns noisy opportunity packets into evidence-backed action queues while keeping consequential actions human-authorized.

This matters because Morphosis is not a benchmark dashboard. Its model evolution is evaluated against a real agent contract containing required capabilities, weighted quality targets, cost/latency budgets, regression tolerance, authorization, and evidence lineage.

A model can score better overall and still be **REJECTED** if it breaks authorization. A qualified model can be **PROMOTED** when it improves the workload without violating those invariants.

## AWS / Bedrock compatibility

The hackathon implementation is provider-neutral but AWS-native by design:

- Amazon Bedrock can sit behind the known-model fast lane.
- Strands is the real agent/orchestration layer used by this repository.
- Qualified candidates are designed to feed a serving layer such as Strands ModelRouter.
- The sandbox/evaluation boundaries map naturally to Amazon Bedrock AgentCore Code Interpreter and AgentCore Evaluations.
- MCP/A2A-compatible tool and agent discovery can extend the same evidence model beyond foundation models.

This repository **does not claim a live AgentCore deployment that is not present**. Those AgentCore components are documented extension boundaries, while the submitted Strands paths are reproducible without cloud credentials.

## Reproduce

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
./verify.sh
```

To run the future-model proof directly:

```bash
PYTHONPATH=src .venv/bin/python -m morphosis.cli \
  --future-model fixtures/future_model_x.json
```

To run the canonical live control plane (frontend + Python authority + resumable SSE ledger):

```bash
PYTHONPATH=src .venv/bin/python -m morphosis.os.api --seed-reference --port 8765
# open http://127.0.0.1:8765/?live=1
```

The browser is a projection client only. It sends strict commands to `/api/v1/commands`, reloads canonical snapshots from `/api/v1/system`, and follows `/api/v1/events`; qualification, evidence, promotion, rollback and requalification remain Python-owned.

Expected future-model evidence includes:

- `Future model lane: UNKNOWN_BOOTSTRAP`
- `Novel capability: future.semantic_patch.v1`
- `Observed status: SUPPORTED`
- `Adaptation: ADAPTED`
- `Runtime gate: AUTO_APPLY`
- `Source gate: HUMAN_APPROVAL_REQUIRED`

The same CLI without `--future-model` reproduces the ordinary candidate paths, including a flashy high-scoring candidate rejected for an authorization failure and a workload-qualified candidate promoted over the incumbent.

## Hard boundaries

- Unknown never means supported.
- Self-report never equals proof.
- Candidate cannot decide its own pass/fail.
- A higher aggregate score cannot compensate for a hard-invariant failure.
- Failed evolution never mutates the incumbent.
- Automatic changes require rollback metadata.
- Source-code changes generated/proposed by a model always require explicit human merge approval.
- Evaluator logic, evidence semantics, hard invariants, and source-merge authority are outside the auto-writable surface.
- Fixtures are synthetic and the demo performs no unapproved external side effects.

## Pre-existing work disclosure

The broader **Autonomous Morphology** research direction and name existed before this hackathon. The **Evolving Morphosis implementation submitted here** — including its Strands tool loops, future-model bootstrap, extensible capability registry, candidate-proposed compatibility path, Evolution Bundle protocol, Evolving Morphosis workload integration, tests, interface, architecture, and reproducible demo — was built during the 2026 Agents for Humans submission period.

The public repository intentionally excludes private AM/Animantum identity architecture, proprietary long-term optimization heuristics, and private cross-agent memory/research systems.

## Project status

AI coding assistance was used to draft, implement, test, and review code and documentation. The project uses the open-source Strands Agents SDK and standard Python libraries.

## License

MIT
