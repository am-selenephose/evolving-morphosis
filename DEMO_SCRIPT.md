# ActionQueue demo script (about 55 seconds)

## 0:00–0:06 — Promise

ActionQueue turns noisy professional opportunities into an evidence-backed review queue while keeping consequential actions under human control.

## 0:06–0:15 — Input

The demo uses a synthetic packet containing valid, duplicated, expired, and incomplete opportunities. No private data or credentials are required.

## 0:15–0:26 — Strands agent

The real Strands Agents SDK loop selects the analysis tool. Deterministic policy code validates records, rejects expired items, deduplicates them, ranks viable work, and hashes retained evidence.

## 0:26–0:39 — Result

The resulting report keeps source URLs, deadlines, listed rewards, evidence fingerprints, and safe preparation steps. The same fixture produces the same byte-for-byte report.

## 0:39–0:49 — Human boundary

Applying, publishing, sending, signing, spending, and submitting are default-deny. ActionQueue prepares evidence; a person remains accountable for consequential action.

## 0:49–0:55 — Verification

The repository includes an MIT license, architecture diagram, synthetic fixture, deterministic demo adapter, tests, and a one-command verifier.

## Reproduce

```bash
./verify.sh
PYTHONPATH=src .venv/bin/python -m actionqueue.cli fixtures/opportunities.json \
  --now 2026-08-26T00:00:00Z --output demo-output/report.md
```
