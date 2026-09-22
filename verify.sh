#!/usr/bin/env bash
set -euo pipefail
trap 'status=$?; echo "VERIFY FAILED line ${LINENO}: ${BASH_COMMAND}" >&2; exit $status' ERR
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"
export PYTHONPATH="$ROOT_DIR/src"
PY="${PYTHON:-$ROOT_DIR/.venv/bin/python}"

"$PY" -m pytest -q

node --test tests/frontend/*.test.mjs
node --check site/app.js
node --check site/data.js
node --check site/visuals.js

VERIFY_DIR="$(mktemp -d)"
trap 'rm -rf "$VERIFY_DIR"' EXIT
"$PY" -m morphosis.export_demo --output "$VERIFY_DIR/generated" --architecture-svg "$VERIFY_DIR/architecture.svg" >/dev/null
diff -qr site/generated "$VERIFY_DIR/generated" >/dev/null
cmp -s architecture.svg "$VERIFY_DIR/architecture.svg"

rm -rf demo-output
mkdir -p demo-output

"$PY" -m actionqueue.cli fixtures/opportunities.json --now 2026-08-26T00:00:00Z --output demo-output/report.md >/dev/null
test -s demo-output/report.md
grep -q "HUMAN APPROVAL REQUIRED" demo-output/report.md

"$PY" -m morphosis.cli --contract fixtures/morphosis_contract.json --candidates fixtures/morphosis_candidates.json > demo-output/morphosis.txt
grep -q "Morphosis verdict: REJECT" demo-output/morphosis.txt
grep -q "Morphosis verdict: PROMOTE" demo-output/morphosis.txt

"$PY" -m morphosis.cli --future-model fixtures/future_model_x.json > demo-output/future-model.txt
grep -q "Future model lane: UNKNOWN_BOOTSTRAP" demo-output/future-model.txt
grep -q "Novel capability: future.semantic_patch.v1" demo-output/future-model.txt
grep -q "Observed status: SUPPORTED" demo-output/future-model.txt
grep -q "Adaptation: ADAPTED" demo-output/future-model.txt
grep -q "Adaptation proof: OBSERVED" demo-output/future-model.txt
grep -q "Runtime gate: AUTO_APPLY" demo-output/future-model.txt
grep -q "Source gate: HUMAN_APPROVAL_REQUIRED" demo-output/future-model.txt

echo "PASS: Python + frontend + deterministic projections/SVG + real Strands loops + Evolving Morphosis gates + current-model qualification + future capability/adaptation verification"
