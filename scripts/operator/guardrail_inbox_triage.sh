#!/usr/bin/env bash
# Operator wrapper — forwards to scripts/guardrail_inbox_triage.sh
# See: scripts/README_OPERATOR.md
exec bash "$(dirname "$0")/../guardrail_inbox_triage.sh" "$@"
