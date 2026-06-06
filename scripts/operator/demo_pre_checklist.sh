#!/usr/bin/env bash
# Operator wrapper — forwards to scripts/demo_pre_checklist.sh
# See: scripts/README_OPERATOR.md
exec bash "$(dirname "$0")/../demo_pre_checklist.sh" "$@"
