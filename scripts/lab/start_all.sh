#!/usr/bin/env bash
echo "LAB ONLY — not part of Unified Intake paid pilot path" >&2
echo "  Product path: bash scripts/run_demo_local.sh (port 8001)" >&2
echo "  Index: scripts/LAB_SCRIPT_INDEX.md" >&2
exec bash "$(dirname "$0")/../start_all.sh" "$@"
