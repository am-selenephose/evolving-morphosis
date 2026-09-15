# Devpost submission packet — Evolving Morphosis

## Project name

Evolving Morphosis

## Tagline

Models evolve. Your agents should evolve with them.

## Track

Professional Agents

## What it does

Evolving Morphosis is a Strands-based model-evolution control plane for professional AI and agent teams. It automates the repetitive migration work created by every new model generation: capability discovery, compatibility analysis, workload regression testing, adaptation, promotion, rollback, and requalification.

Known models can take an optimized adapter fast path. A model that does **not exist yet** can enter through a minimal bootstrap path with no hard-coded model entry. Its self-reported capabilities begin as unverified claims. Morphosis can dynamically register novel namespaced capabilities, evaluate bounded candidate-proposed probes, consume candidate-proposed compatibility transforms, independently verify the resulting behavior, and package the change into an evidence-hashed Evolution Bundle.

A reversible runtime/config change may be marked `AUTO_APPLY` only after tests and hard invariants pass and rollback metadata exists. A source-code patch proposed by a model always stops at `HUMAN_APPROVAL_REQUIRED`.

## Inspiration

AI platform engineers repeatedly do the same work whenever OpenAI, Anthropic, Google, AWS, an open-weight lab, or a future provider releases a new model: read release notes, inspect API differences, check tools and schemas, patch adapters, replay evaluations, compare against the incumbent, select a canary, and watch for regressions.

Generic model routing only answers which already-known candidate should handle a request. We wanted an agent that handles the work **before routing**: decide whether a new model deserves access to a workload, learn how the runtime must adapt around it, and preserve the agent's contract while the underlying intelligence changes.

Our rule is: **metadata and self-report are priors; observed workload behavior is proof.**

## How we built it

A real Strands Agents SDK 1.55.1 agent invokes bounded Morphosis tools. Deterministic policy code outside model authority owns the evidence and promotion boundary.

The v2 pipeline has two entry paths:

1. **Known-model fast path** — optimized provider/model adapters accelerate candidates we already understand.
2. **Unknown future-model bootstrap** — arbitrary future endpoints can enter without a pre-existing model name or closed capability enum.

Both converge into an extensible capability evidence graph. Candidate claims are stored as `UNKNOWN / UNVERIFIED`. Candidate-proposed probes are rejected before execution if they request forbidden network/source-write behavior or exceed the bounded probe contract. Independent observations can upgrade a capability to `SUPPORTED / OBSERVED` and attach stable SHA-256 evidence.

The Morphogenesis Engine then compiles candidate-proposed compatibility changes such as schema transforms, tool mappings, context strategies, or portable fallbacks. Every proposed evolution becomes an immutable Evolution Bundle containing candidate identity, parent lineage, changes, test/invariant state, rollback metadata, recommendation, approval class, and deterministic hash.

The first real workload is Evolving Morphosis's professional opportunity-triage workload, with required tool use, structured output, task quality, cost/latency budgets, and hard invariants for human authorization and evidence lineage.

## Future-model demo

The repository contains a synthetic `future-model-x` with a capability the stable core never knew beforehand:

`future.semantic_patch.v1`

The demo shows:

- no hard-coded model adapter exists;
- the capability enters as an unverified self-report;
- the candidate proposes a bounded probe;
- Morphosis independently verifies the observation;
- the new capability is added dynamically without changing the stable core schema;
- the candidate proposes `semantic-patch-wrapper` as its compatibility transform;
- Morphosis records that path honestly as `ADAPTED`, not native;
- the reversible runtime Evolution Bundle becomes `AUTO_APPLY` after all gates pass;
- the candidate's source-adapter proposal remains `HUMAN_APPROVAL_REQUIRED`.

The model can help teach the runtime how to integrate it. It cannot certify itself or rewrite its evaluator.

## Challenges

The hardest problem was designing for model capabilities that cannot be enumerated in advance. A closed `supports_tools / supports_json` table would become obsolete as soon as a future model exposed a capability we had never named. We therefore made capability identifiers extensible and namespaced while keeping universal evidence semantics stable.

The second challenge was allowing meaningful self-evolution without allowing a candidate to rewrite the authority judging it. Morphosis exposes a model-writable proposal zone for probes, adapters, transforms, context strategies, and source patches, but hard invariants, evaluation semantics, evidence rules, and merge authority remain independently governed.

A third challenge was separating native capability from compatibility. If a model lacks a native surface but a verified portable fallback satisfies the workload, Morphosis records the result as adapted rather than pretending every provider behaves identically.

## Accomplishments

- Known-model optimized adapter fast path
- Unknown-future-model bootstrap with no hard-coded model entry
- Extensible namespaced capability registry
- `UNKNOWN / UNVERIFIED` self-report semantics
- Bounded candidate-proposed probes with independent verification
- Candidate-proposed compatibility transforms
- Native vs adapted capability distinction
- Deterministic SHA-256 Evolution Bundles
- Runtime/config auto-apply only with passing gates and rollback
- Human-required source-code merge gate
- Incumbent-preserving failed evolution
- Drift-triggered requalification primitive
- Real Strands Agents SDK tool-use loops
- Evolving Morphosis professional workload integration
- Interactive raspberry/black browser console

## What we learned

Future-proofing an agent does not mean predicting GPT-7, GPT-8, or every provider that may exist. It means keeping a small stable contract around evidence, provenance, constraints, rollback, and evaluation while allowing the capability vocabulary and compatibility layer to grow around new models.

The durable abstraction is not the model name. It is the workload contract and the evidence required to earn access to it.

## What's next

The next production step is connecting real Amazon Bedrock candidate discovery to the known-model lane and using Amazon Bedrock AgentCore Code Interpreter / Evaluations as sandbox and evaluation substrates while preserving the same deterministic promotion boundary. Qualified candidates can then feed a Strands ModelRouter pool for shadow/canary serving, with OpenTelemetry/production drift triggering requalification.

Longer term, the same capability-evidence model can extend through MCP and A2A from models to tools and whole agents: any intelligent component can describe what it claims to do, but it must earn trust through evidence.

## Built with

- Python 3.12+
- Strands Agents SDK 1.55.1
- SHA-256 evidence lineage
- pytest
- GitLab
- HTML / CSS / JavaScript
- AWS Bedrock / AgentCore-compatible extension boundaries

## Responsible AI and privacy

- Synthetic fixtures; no sensitive user data is needed for the demo.
- Unknown never means supported.
- Candidate self-report never equals proof.
- Candidate cannot decide its own pass/fail.
- Hard invariants cannot be traded away for a higher aggregate score.
- Failed evolution does not mutate the incumbent.
- Runtime auto-apply requires rollback metadata.
- Source evolution always requires explicit human merge approval.
- No fabricated AgentCore deployment is claimed.

## Pre-existing work disclosure

The broader **Autonomous Morphology** research direction and name existed before the hackathon. The submitted **Evolving Morphosis** implementation — Strands loops, future-model bootstrap, extensible capability registry, candidate-proposed compatibility path, Evolution Bundle protocol, Evolving Morphosis workload integration, tests, UI, architecture, and reproducible demo — was built during the 2026 Agents for Humans submission period.

Private AM/Animantum identity architecture, private long-term optimization heuristics, and private cross-agent memory/research systems are not part of this public submission.

## Verification

Clone the repository, install `requirements.txt`, and run:

```bash
./verify.sh
```

Direct future-model path:

```bash
PYTHONPATH=src .venv/bin/python -m morphosis.cli --future-model fixtures/future_model_x.json
```

Expected evidence includes `UNKNOWN_BOOTSTRAP`, `future.semantic_patch.v1`, `Observed status: SUPPORTED`, `Adaptation: ADAPTED`, `Runtime gate: AUTO_APPLY`, and `Source gate: HUMAN_APPROVAL_REQUIRED`.

## Submission assets

- Public repository: https://gitlab.com/am.statementforge/evolving-morphosis
- Architecture source: `architecture.svg`
- Devpost architecture PNG: regenerate from the v2 SVG before final upload
- Demo video public URL: upload the final v2 demo to **Public** YouTube or Vimeo before submission
- License: MIT
- AWS Builder ID: enter the email actually shown in the entrant's AWS Builder ID profile
