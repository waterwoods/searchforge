#!/usr/bin/env bash
# Operator wrapper — forwards to scripts/trial_readiness_check.sh
# See: scripts/README_OPERATOR.md
exec bash "$(dirname "$0")/../trial_readiness_check.sh" "$@"
