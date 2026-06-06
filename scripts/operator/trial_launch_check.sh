#!/usr/bin/env bash
# Operator wrapper — forwards to scripts/trial_launch_check.sh
# See: scripts/README_OPERATOR.md
exec bash "$(dirname "$0")/../trial_launch_check.sh" "$@"
