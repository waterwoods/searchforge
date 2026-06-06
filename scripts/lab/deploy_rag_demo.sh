#!/usr/bin/env bash
echo "LAB ONLY — not part of Unified Intake paid pilot path" >&2
echo "  Paid pilot: bash scripts/deploy_paid_pilot.sh" >&2
echo "  Index: scripts/LAB_SCRIPT_INDEX.md" >&2
exec bash "$(dirname "$0")/../deploy_rag_demo.sh" "$@"
