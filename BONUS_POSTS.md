# Evolving Morphosis — builder.aws bonus post drafts

These drafts are written for the Agents for Humans hackathon bonus. Publish each as a separate public builder.aws post and keep **Agents for Humans** in every title.

---

# Agents for Humans: Why a Newer Model Should Have to Earn Its Way Into Your Agent

AI models are improving quickly, but production agents are not just models. They are workflows with tools, schemas, budgets, evidence requirements, and human authorization boundaries.

That creates an uncomfortable problem: when a new model appears, how do you know it is actually an upgrade for *your* agent?

A provider can tell you that a model supports tool calling. A benchmark can tell you that its general reasoning improved. Neither proves that the model will select the right tool for your workload, preserve your structured output contract, remain within your latency and cost budget, or respect the policy boundary that matters to your users.

That is the problem behind **Evolving Morphosis**, my Agents for Humans Professional Agents project.

Morphosis treats every new model as an untrusted candidate. The professional agent declares a versioned **workload contract**: required capabilities, quality thresholds, latency and cost budgets, plus hard invariants that may never regress. Runtime probes and evaluations are converted into evidence-bearing capability records. Morphosis then compares candidate and incumbent and emits an auditable **PROMOTE, HOLD, or REJECT** decision.

The important rule is simple: **metadata is a prior; observed workload behavior is proof.**

In the reference demo, one synthetic “new hot model” performs extremely well on ordinary capability measures but fails the authorization invariant. Morphosis rejects it. A second candidate passes the same contract and materially improves the workload score, so it is promoted.

The implementation uses the Strands Agents SDK for the agent/tool loop and keeps qualification deterministic and reproducible. Every decision receives a SHA-256 evidence hash. The first workload is Evolving Morphosis, a professional opportunity-triage agent whose consequential actions remain human-authorized.

This architecture is intentionally model-generation resilient. The agent is not written for GPT-N, Claude-N, or one Bedrock model family. A future candidate only needs an adapter capable of producing evidence against the same workload contract.

That is the idea I want professional agents to inherit: **new model, same contract, proof before promotion.**

Project: Evolving Morphosis
Live demo: https://light-mindset-9rn4u6e.shipstatic.com
Source: https://gitlab.com/am.statementforge/evolving-morphosis

---

# Agents for Humans: The Workload Contract Is More Durable Than the Model Name

Most agent architectures begin with a model choice. I think that order is backwards.

A professional workflow usually knows what it needs before it knows which future model will satisfy those needs. It may require reliable tool calls, valid structured output, a minimum task-success rate, an upper latency limit, a cost ceiling, evidence lineage, or explicit human authorization before a consequential action.

Those requirements should outlive the model underneath them.

For my Agents for Humans project, **Evolving Morphosis**, I turned that idea into a small executable abstraction called a **workload contract**.

A workload contract answers five questions:

1. Which capabilities are required?
2. What quality level is acceptable?
3. Which regressions are tolerable?
4. What cost and latency budgets apply?
5. Which invariants are non-negotiable?

The first Morphosis workload is professional opportunity triage. It requires tool use, structured output, and task quality, while treating authorization and evidence lineage as hard invariants.

This changes how model upgrades work. Instead of asking “Is Model B better than Model A?”, Morphosis asks a narrower and more useful question:

**“Is Model B better for this workload, through this serving surface, without breaking any invariant?”**

That distinction matters because the same underlying model can behave differently across providers, endpoints, tool schemas, or runtime configuration. Static capability flags are useful discovery evidence, but they are not sufficient authorization evidence.

Morphosis therefore records observed capability evidence, hashes the resulting manifest, compares candidate and incumbent, and only promotes the candidate if the workload contract is satisfied.

This also keeps adaptation from becoming policy drift. Morphosis may eventually change routing, provider selection, context strategy, or fallback behavior automatically. It may not silently decide that a hard authorization rule is inconvenient and remove it.

The system can evolve. The contract remains the stable boundary.

That is why I think the workload contract is a more durable abstraction than any current model name.

Project: Evolving Morphosis
Live demo: https://light-mindset-9rn4u6e.shipstatic.com
Source: https://gitlab.com/am.statementforge/evolving-morphosis

---

# Agents for Humans: Building a Reproducible Strands Agent Without Requiring Judge Credentials

Hackathon demos often depend on a very specific API key, provider account, region, or model entitlement. That can make a real agent unnecessarily difficult for a reviewer to reproduce.

For **Evolving Morphosis**, my Agents for Humans entry, I wanted the Strands agent loop itself to be verifiable without asking a judge to provide model credentials.

The solution was a credential-free deterministic model adapter that still drives the real Strands Agents SDK event loop.

The adapter does not replace Strands or bypass the agent. It acts as a deterministic model boundary for the checked-in fixtures. The Strands agent receives the request, selects the bounded Morphosis qualification tool, executes it through the normal tool loop, and returns the resulting decision.

That gives the repository two useful properties:

**Reproducibility.** The same fixture produces the same evidence and decision hashes. A reviewer can clone the repository, install the documented dependencies, and run `./verify.sh` without an AWS key or paid model account.

**Honest separation of concerns.** The deterministic demo is not presented as a production intelligence model. It exists to prove orchestration, tool execution, policy behavior, and evidence handling. A live AWS deployment could swap the model/provider boundary while keeping the workload contract and qualification logic unchanged.

The current verifier runs 11 tests on Python 3.12 and Strands Agents SDK 1.55.1. It covers the Morphosis decision engine, the original Evolving Morphosis professional workload, both credential-free Strands tool loops, the authorization boundary, and both the REJECT and PROMOTE candidate paths.

I like this pattern because it avoids a common demo trap: either requiring external credentials or mocking so much of the framework that the framework is no longer actually being exercised.

For agent systems, reproducibility is part of trust. A judge—or a future maintainer—should be able to see exactly what the system did and why.

Project: Evolving Morphosis
Live demo: https://light-mindset-9rn4u6e.shipstatic.com
Source: https://gitlab.com/am.statementforge/evolving-morphosis
