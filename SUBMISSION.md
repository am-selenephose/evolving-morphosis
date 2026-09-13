# Devpost submission packet — ActionQueue

## Project name

ActionQueue

## Tagline

Evidence in. Accountable decisions out.

## Track

Professional Agents

## What it does

ActionQueue is a Strands Agents SDK professional-work agent that converts noisy opportunity packets into a deduplicated, evidence-backed action queue. It rejects expired and incomplete records, preserves source URLs and SHA-256 evidence fingerprints, ranks viable work, and proposes safe preparation steps. Consequential actions—apply, publish, send, sign, spend, and submit—are always default-deny and require explicit human approval.

## The problem

Professionals repeatedly inspect duplicate listings, discover expired calls late, and lose the evidence behind a decision. Existing automation can also cross an accountability boundary by acting under a person's identity. ActionQueue separates evidence preparation from consequential action.

## How it works

1. A Strands agent receives a packet of opportunities.
2. The agent invokes the `analyze_opportunity_packet` tool.
3. Deterministic policy code validates schemas, rejects expired items, deduplicates records, ranks viable work, and hashes evidence.
4. A compact Markdown report preserves sources, deadlines, rewards, evidence fingerprints, and reversible next steps.
5. Risk-bearing verbs are surfaced as human approval gates, never executed.

The included credential-free `DeterministicDemoModel` drives the real Strands event loop so judges can reproduce tool use and output byte-for-byte. The model boundary can be replaced with Amazon Bedrock for a live deployment without changing the deterministic policy and approval layer.

## Built with

- Python 3.12
- Strands Agents SDK 1.26.0
- Deterministic SHA-256 evidence lineage
- `unittest` verification
- FFmpeg demo pipeline

## Responsible AI and privacy

- The checked-in fixture is synthetic.
- No external side effects are implemented.
- Provider output cannot bypass deterministic validation or approval policy.
- Every accepted item retains its source and evidence fingerprint.
- Applying, publishing, sending, signing, spending, and submitting require a human.

## Verification

`./verify.sh` runs validation, expiry, deduplication, approval-gate, replay-stability, and full Strands tool-loop tests. Three consecutive verification runs produced the same report and passed all tests.

## Submission assets

- Public repository URL: **add after authorized GitHub publication**
- Demo video URL: **add after authorized video publication**
- Architecture diagram: `architecture.svg`
- Demo video file: `demo/actionqueue-demo.mp4`
- License: MIT
- AWS Builder ID: **enter using the authorized entrant identity**

## Final human checklist

1. Review official eligibility and rules using truthful entrant facts.
2. Sign in with the authorized GitHub identity and publish this repository publicly.
3. Publish the verified demo video and insert both public URLs above.
4. Enter the authorized AWS Builder ID.
5. Review declarations and submit exactly once before 2026-09-14 17:00 PDT.
