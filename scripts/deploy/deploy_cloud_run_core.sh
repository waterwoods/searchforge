#!/usr/bin/env bash
echo "DEPLOY: deploy_cloud_run_core.sh is IMPLEMENTATION ONLY — not an operator entry." >&2
echo "  Paid pilot:  bash scripts/deploy_paid_pilot.sh" >&2
echo "  See: docs/runbooks/DEPLOY_TRUTH_MAP.md" >&2
exec bash "$(dirname "$0")/../deploy_cloud_run_core.sh" "$@"
