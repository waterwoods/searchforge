#!/usr/bin/env bash
# Deploy tier wrapper — forwards to scripts/deploy_paid_pilot.sh
# See: scripts/deploy/README.md, docs/runbooks/DEPLOY_TRUTH_MAP.md
exec bash "$(dirname "$0")/../deploy_paid_pilot.sh" "$@"
