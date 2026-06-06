#!/usr/bin/env bash
echo "LAB ONLY — not part of Unified Intake paid pilot path" >&2
echo "  Product validate: bash scripts/guardrail_inbox_triage.sh" >&2
echo "  Index: scripts/LAB_SCRIPT_INDEX.md" >&2
exec bash "$(dirname "$0")/../stop_all.sh" "$@"
