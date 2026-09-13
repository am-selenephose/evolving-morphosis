#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"
export PYTHONPATH="$ROOT_DIR/src"
.venv/bin/python -m unittest discover -s tests -v
rm -rf demo-output
.venv/bin/python -m actionqueue.cli fixtures/opportunities.json --now 2026-08-26T00:00:00Z --output demo-output/report.md >/dev/null
test -s demo-output/report.md
grep -q "HUMAN APPROVAL REQUIRED" demo-output/report.md
echo "PASS: tests, Strands tool loop, deterministic report, and approval gates"
