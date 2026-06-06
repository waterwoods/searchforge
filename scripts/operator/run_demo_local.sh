#!/usr/bin/env bash
# Operator wrapper — forwards to scripts/run_demo_local.sh
# See: scripts/README_OPERATOR.md
exec bash "$(dirname "$0")/../run_demo_local.sh" "$@"
