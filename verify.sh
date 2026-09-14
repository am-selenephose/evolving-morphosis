#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"
export PYTHONPATH="$ROOT_DIR/src"
PY="${PYTHON:-$ROOT_DIR/.venv/bin/python}"
"$PY" -m pytest -q
rm -rf demo-output
"$PY" -m actionqueue.cli fixtures/opportunities.json --now 2026-08-26T00:00:00Z --output demo-output/report.md >/dev/null
test -s demo-output/report.md
grep -q "HUMAN APPROVAL REQUIRED" demo-output/report.md
"$PY" -m morphosis.cli --contract fixtures/morphosis_contract.json --candidates fixtures/morphosis_candidates.json > demo-output/morphosis.txt
grep -q "Morphosis verdict: REJECT" demo-output/morphosis.txt
grep -q "Morphosis verdict: PROMOTE" demo-output/morphosis.txt
echo "PASS: 11 tests, real Strands loops, ActionQueue approval gates, and Morphosis promotion control"
