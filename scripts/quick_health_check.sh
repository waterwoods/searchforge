#!/usr/bin/env bash
# Quick Combined Health Check — Unified Intake guardrails + shortened ASGI chaos smoke
# ==================================================================================
# Intended for fast feedback before merges; full rigor stays in scripts/run_full_regression.py
#
# NOTE: scripts/guardrail_inbox_triage.sh can exceed 2 minutes on a cold tree; chaos --smoke
# is capped to ~8 sessions. Target wall time is typical developer hardware / warm interpreters.
#
# Usage: bash scripts/quick_health_check.sh
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_DIR"

echo "[quick_health] unified intake guardrail (full bash script)"
bash scripts/guardrail_inbox_triage.sh

echo "[quick_health] ASGI chaos (smoke, perf metrics)"
export PYTHONPATH="$REPO_DIR"
export TRIAGE_RETURN_PERF_METRICS=1
python3 scripts/llm_chaos_live_triage_check.py --asgi --smoke

echo "[quick_health] PASS"
