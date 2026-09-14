# Evolving Morphosis — 82-second demo walkthrough

## 0:00–0:08 — Thesis

**Evolving Morphosis** — Models evolve. Your agents should evolve with them.

A new model should not enter an agent's serving pool just because it is newer. Morphosis makes the candidate prove itself against the actual workload first.

## 0:08–0:20 — Professional problem

AI teams repeatedly benchmark, regression-test, and retune agents whenever models change. Static provider metadata can tell us what a model claims to support, but not whether it reliably preserves this agent's tools, schemas, budgets, and authorization boundary.

## 0:20–0:30 — Architecture

A candidate enters through discovery evidence. Morphosis applies the workload contract, turns runtime probes and evaluations into an evidence-backed capability manifest, compares candidate and incumbent, then emits PROMOTE, HOLD, or REJECT before routing.

## 0:30–0:42 — Rejection path

The first candidate is extremely strong on tool use, structured output, and task quality. But it fails authorization. Morphosis rejects it even though its average capability score is high. Hard invariants cannot be purchased with performance.

## 0:42–0:54 — Promotion path

The second candidate passes every required capability and hard invariant and materially improves the workload score. Morphosis promotes it without changing the professional agent's workload contract.

## 0:54–1:04 — Verification

The repository runs on Python 3.12 and Strands Agents SDK 1.55.1. `./verify.sh` passes 11 tests, both credential-free real Strands tool loops, the ActionQueue approval boundary, and both Morphosis decision paths.

## 1:04–1:22 — Why it matters

The durable abstraction is not GPT-6, GPT-7, Bedrock, or any model family. It is the evidence-backed workload contract. The reference build is provider-neutral and exposes an AWS Bedrock / AgentCore-compatible extension boundary without pretending that an AgentCore deployment already exists.

**New model. Same workload contract.**
