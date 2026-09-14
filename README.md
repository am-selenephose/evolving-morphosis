# Evolving Morphosis

**Models evolve. Your agents should evolve with them.**

Evolving Morphosis is a Strands-based model-qualification control plane for durable agents. Instead of trusting a new model because it is newer, larger, cheaper, or advertised as more capable, Morphosis tests candidate behavior against the agent's actual workload contract and returns an auditable **PROMOTE / HOLD / REJECT** decision.

The core idea is simple: **model metadata is a prior; observed workload behavior is proof.**

## Why it exists

Agent code is often coupled to assumptions about one model generation: tool calling, schema behavior, context handling, latency, cost, or safety. When a new model arrives, teams manually benchmark it, regression-test it, retune routing, and hope that a capability improvement did not break a critical invariant.

Morphosis makes that migration a repeatable agent workflow.

## What is implemented

- Typed, provider-neutral capability evidence with `SUPPORTED / UNSUPPORTED / UNKNOWN` state.
- Workload contracts defining required capabilities, weighted quality targets, cost/latency budgets, and hard invariants.
- Stable SHA-256 evidence manifests for reproducibility and audit.
- Deterministic candidate comparison with **PROMOTE / HOLD / REJECT** outcomes.
- Regression blocking: a candidate cannot hide a serious loss behind a higher aggregate score.
- Hard-invariant blocking: authorization and evidence-lineage failures force rejection.
- A real Strands Agents SDK tool loop around the qualification engine.
- Credential-free synthetic fixtures so judges can reproduce both a rejected flashy candidate and a promoted qualified candidate.
- ActionQueue retained as the first professional workload proving that the runtime is useful above a concrete agent rather than as a benchmark-only toy.

## Architecture

![Evolving Morphosis architecture](architecture.svg)

The reference implementation separates five layers:

1. **Discovery evidence** — provider/model metadata can introduce a candidate, but cannot authorize it.
2. **Workload contract** — the agent declares what it actually needs and what must never regress.
3. **Qualification** — observed probes/evals produce evidence-bearing capability records.
4. **Promotion control** — Morphosis compares the candidate with the incumbent and emits PROMOTE, HOLD, or REJECT.
5. **Agent runtime** — qualified candidates can then be handed to a router such as Strands ModelRouter or another provider/runtime adapter.

## AWS compatibility

The hackathon build uses the Strands Agents SDK directly. The control-plane contract is provider-neutral so an AWS deployment can use Amazon Bedrock as the model surface and Strands/AgentCore evaluation and runtime services around it without changing the workload contract or promotion logic.

**Important:** this repository does not claim a live AgentCore deployment. The included demo is intentionally credential-free and reproducible. AWS/Bedrock integration is an extension boundary, not a fabricated deployment claim.

## Reproduce the demo

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
PYTHONPATH=src .venv/bin/python -m morphosis.cli
```

Expected behavior:

- `new-hot-model` scores extremely well on ordinary capabilities but violates the authorization invariant → **REJECT**.
- `future-qualified-model` passes the same workload contract and materially improves the workload score → **PROMOTE**.

Run every test:

```bash
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

The suite covers the Morphosis decision engine, deterministic evidence hashes, both promotion and rejection paths, real Strands tool invocation, plus the original ActionQueue workload tests.

## Workload contract

`fixtures/morphosis_contract.json` demonstrates the contract for professional opportunity triage. It declares required tool use, structured output, task quality, authorization, evidence lineage, weighted scoring, regression tolerance, latency, and cost limits.

A future model does not need to be known when the agent is written. It only needs an adapter capable of producing the same evidence contract. That is the durability boundary: **new model, same workload contract.**

## Safety and privacy

- Hard invariants cannot be traded away by a higher average score.
- No external side effects are implemented in the demo.
- Fixtures are synthetic.
- Candidate/provider marketing claims never override observed failures.
- Decisions preserve content-addressed evidence hashes.
- ActionQueue's consequential actions remain human-authorized.

## Project status

Created during the 2026 Agents for Humans submission period. AI coding assistance was used to draft and review code and documentation. Evolving Morphosis, its workload contract, fixtures, qualification policy, tests, architecture, and demo are original to this project. The project uses the open-source Strands Agents SDK and standard Python libraries.

## License

MIT
