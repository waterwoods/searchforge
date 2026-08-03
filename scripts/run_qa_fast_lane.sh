#!/usr/bin/env bash
# QA Fast Lane V1 — one command for automated smoke + evidence (Cloud QA only).
#
# Usage:
#   bash scripts/run_qa_fast_lane.sh
#   bash scripts/run_qa_fast_lane.sh --no-wait
#   bash scripts/run_qa_fast_lane.sh --frontend-origin https://ui-….vercel.app
#   QA_FAST_LANE_SESSION_ID=wx_… bash scripts/run_qa_fast_lane.sh
#
# Never targets Production. Never retargets waterwoods.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

export PYTHONPATH="${PYTHONPATH:-}:."
exec python3 scripts/qa_fast_lane.py "$@"
