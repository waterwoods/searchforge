#!/usr/bin/env bash
# Operator wrapper — forwards to scripts/restore_8001_readiness.sh
# See: scripts/README_OPERATOR.md
exec bash "$(dirname "$0")/../restore_8001_readiness.sh" "$@"
