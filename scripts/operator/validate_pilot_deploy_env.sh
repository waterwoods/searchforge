#!/usr/bin/env bash
# Operator wrapper — forwards to scripts/validate_pilot_deploy_env.py
exec env PYTHONPATH=. python3 "$(dirname "$0")/../validate_pilot_deploy_env.py" "$@"
