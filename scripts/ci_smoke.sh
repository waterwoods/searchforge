#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Repo-root imports (`services.*`) require PYTHONPATH — matches AGENTS.md / trial scripts.
export PYTHONPATH="${PWD}${PYTHONPATH:+:$PYTHONPATH}"
python3 scripts/import_smoke_check.py
bash scripts/guardrail_inbox_triage.sh
