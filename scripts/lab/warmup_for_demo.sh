#!/usr/bin/env bash
echo "LAB ONLY — not part of Unified Intake paid pilot path" >&2
echo "  Vectors optional for intake triage — see OPERATOR_IGNORE_LIST.md" >&2
echo "  Index: scripts/LAB_SCRIPT_INDEX.md" >&2
exec bash "$(dirname "$0")/../warmup_for_demo.sh" "$@"
