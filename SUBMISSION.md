# Devpost submission packet — Evolving Morphosis

## Project name

Evolving Morphosis

## Tagline

Models evolve. Your agents should evolve with them.

## Track

Professional Agents

## What it does

Evolving Morphosis is a Strands-based model-qualification control plane for durable professional agents. When a new model or provider appears, Morphosis does not trust static capability claims. It evaluates the candidate against the agent's actual workload contract, preserves evidence for every observation, compares it with the incumbent, and emits an auditable **PROMOTE / HOLD / REJECT** decision.

The first workload is ActionQueue, a professional opportunity-triage agent. The workload declares required tool use, structured output, task quality, cost and latency budgets, plus hard invariants for human authorization and evidence lineage. A candidate can outperform the incumbent on ordinary capability scores and still be rejected if it breaks one of those invariants.

## Inspiration

AI teams repeatedly rebuild and retune agents whenever a new model generation arrives. A model may advertise better reasoning, tools, context, or cost, yet regress on a specific production workflow or violate a critical policy boundary. Static provider metadata helps discover models, but it cannot prove that a model is safe or better for a particular agent.

Morphosis treats model migration as an evidence-backed professional workflow: **model metadata is a prior; observed workload behavior is proof.**

## How we built it

A real Strands Agents SDK 1.55.1 agent invokes a bounded `qualify_candidate` tool. The deterministic qualification engine parses a versioned workload contract, builds evidence-bearing capability manifests, enforces required capabilities and hard invariants, detects regressions, applies cost/latency budgets, and compares the candidate with the incumbent.

Every decision receives a stable SHA-256 evidence hash. The provider boundary is intentionally neutral: the same workload contract can qualify a Bedrock-served model, another hosted provider, or a local/future model as long as an adapter can produce the evidence contract. After qualification, approved candidates can be handed to a router such as Strands ModelRouter.

For reproducibility, the repository includes a credential-free deterministic Strands model and synthetic fixtures. The demo proves two paths through the same contract: a flashy candidate that is **REJECTED** for breaking authorization, and a qualified future candidate that is **PROMOTED** because it improves the workload without violating invariants.

## Challenges

The hardest design problem was separating three things that are often conflated: what a model claims to support, what a provider actually exposes, and what the model reliably does on this specific workload. A flat `supports_tools=true` flag is not enough for a durable agent runtime.

The second challenge was allowing the system to evolve without allowing it to rewrite its own safety boundary. Morphosis can adapt model selection and compatibility strategy, but a higher average score cannot weaken a hard authorization or evidence-lineage invariant.

## Accomplishments

- Provider-neutral workload contracts
- Evidence-backed capability manifests
- PROMOTE / HOLD / REJECT lifecycle
- Regression and hard-invariant blocking
- Cost and latency budget enforcement
- Stable SHA-256 decision evidence
- Real Strands Agents SDK tool execution
- Compatibility verified on Strands Agents SDK 1.55.1
- 11/11 local tests passing
- Interactive live browser demo
- ActionQueue retained as a concrete professional-agent workload

## What we learned

The durable abstraction is not a model name. It is the contract between an agent and the capabilities it requires. New models should earn access to a workload through evidence rather than inherit trust from their release date or benchmark reputation.

## What's next

Next we would add live model discovery, Bedrock candidate adapters, Strands/AgentCore evaluation feeds, shadow/canary qualification, OpenTelemetry evidence ingestion, and additional workload contracts. The deeper goal is for an agent to adopt future model generations without being rewritten while keeping its critical invariants stable.

## Built with

- Python 3.12
- Strands Agents SDK 1.55.1
- SHA-256 evidence lineage
- pytest
- GitLab
- FFmpeg
- Static browser demo
- AWS Bedrock / AgentCore-compatible extension boundary

## Responsible AI and privacy

- Demo fixtures are synthetic.
- No external side effects are implemented.
- Hard invariants cannot be traded away for a higher aggregate score.
- Provider/model marketing claims never override observed failures.
- Decisions preserve evidence hashes for audit and reproduction.
- ActionQueue's consequential actions remain explicitly human-authorized.
- The project does not claim a live AgentCore deployment that does not exist.

## Verification

Clone the public repository, install `requirements.txt`, and run `./verify.sh`. The canonical verification path runs all 11 tests, both real credential-free Strands tool loops, ActionQueue approval-gate checks, and Morphosis REJECT/PROMOTE qualification paths.

## Submission assets

- Public repository: https://gitlab.com/am.statementforge/actionqueue-agents-for-humans
- Live demo: https://light-mindset-9rn4u6e.shipstatic.com
- Architecture diagram: `architecture.svg`
- Devpost upload PNG: `/home/nur/Downloads/Evolving_Morphosis_Architecture.png`
- Demo video file: `/home/nur/Downloads/Evolving_Morphosis_DEMO.mp4`
- Demo video public URL: **upload to public YouTube/Vimeo before final submission**
- License: MIT
- AWS Builder ID email: `am.statementforge@gmail.com` if that is the email shown in the entrant's AWS Builder ID profile
