#!/usr/bin/env bash
# Operator wrapper — forwards to scripts/summarize_support_posture.sh
# See: scripts/README_OPERATOR.md
exec bash "$(dirname "$0")/../summarize_support_posture.sh" "$@"
