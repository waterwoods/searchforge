#!/usr/bin/env bash
# Operator wrapper — forwards to scripts/deploy_paid_pilot.sh
# See: scripts/README_OPERATOR.md
exec bash "$(dirname "$0")/../deploy_paid_pilot.sh" "$@"
