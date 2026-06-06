#!/usr/bin/env bash
echo "LAB ONLY — not part of Unified Intake paid pilot path" >&2
echo "  Qdrant optional for core intake triage" >&2
echo "  Index: scripts/LAB_SCRIPT_INDEX.md" >&2
exec bash "$(dirname "$0")/../seed_local_qdrant.sh" "$@"
