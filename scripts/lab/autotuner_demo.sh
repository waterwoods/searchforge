#!/usr/bin/env bash
echo "LAB ONLY — not part of Unified Intake paid pilot path" >&2
echo "  Product validate: bash scripts/guardrail_inbox_triage.sh" >&2
echo "  Index: scripts/LAB_SCRIPT_INDEX.md" >&2
exec python3 "$(dirname "$0")/../autotuner_demo.py" "$@"
