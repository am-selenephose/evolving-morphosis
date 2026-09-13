# ActionQueue

ActionQueue is a Strands Agents SDK professional-work agent that turns noisy opportunity packets into a deduplicated, evidence-backed action queue. It prepares reversible work and makes every consequential step—applying, publishing, sending, signing, spending, or submitting—an explicit human approval gate.

## Why it exists

Professionals lose time re-checking duplicate listings, expired calls, unverifiable claims, and unclear next actions. ActionQueue preserves source URLs and content hashes, rejects invalid records, ranks what remains, and produces a compact review artifact without impersonating the user or acting externally.

## Run the verified offline demo

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
PYTHONPATH=src .venv/bin/python -m actionqueue.cli fixtures/opportunities.json \
  --now 2026-08-26T00:00:00Z --output demo-output/report.md
```

The included `DeterministicDemoModel` is a credential-free model adapter that drives the real Strands agent loop through the custom analysis tool. It exists so reviewers can reproduce tool selection and outputs byte-for-byte without AWS credentials. The model boundary is replaceable with Bedrock or another Strands provider for live deployments; the approval policy remains in deterministic tools.

## Verify

```bash
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

Tests cover validation, expiry, deduplication, evidence hashes, risk gates, replay stability, and a full Strands tool loop.

## Safety and privacy

- No external side effects are implemented.
- Fixture data is synthetic and contains no private records.
- Consequential verbs are default-deny and surfaced for human approval.
- Reference time is explicit, making expiry and ranking reproducible.
- Every accepted item retains its source and a SHA-256 evidence fingerprint.

## Architecture

![ActionQueue architecture](architecture.svg)

## Demo and submission packet

- `DEMO_SCRIPT.md` contains the concise walkthrough and reproduction commands.
- `build-demo-video.sh` reproducibly renders the 56-second demo to `demo/actionqueue-demo.mp4`.
- `SUBMISSION.md` contains the complete Devpost copy and final authorized-publication checklist.

## Project status and disclosure

Created during the 2026 Agents for Humans submission period. AI coding assistance was used to draft and review code and copy. The opportunity policy, synthetic fixture, tests, architecture, and verification are original to this project. No pre-existing product code is incorporated beyond standard libraries and the Strands Agents SDK.

## License

MIT
