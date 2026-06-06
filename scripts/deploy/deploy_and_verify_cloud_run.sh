#!/usr/bin/env bash
echo "DEPLOY: deploy_and_verify_cloud_run.sh is legacy." >&2
echo "  Paid pilot:  bash scripts/deploy_paid_pilot.sh" >&2
echo "  See: docs/runbooks/DEPLOY_TRUTH_MAP.md" >&2
exec bash "$(dirname "$0")/../deploy_and_verify_cloud_run.sh" "$@"
