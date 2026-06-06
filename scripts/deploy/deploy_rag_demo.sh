#!/usr/bin/env bash
echo "DEPLOY: deploy_rag_demo.sh is DEPRECATED." >&2
echo "  Paid pilot:  bash scripts/deploy_paid_pilot.sh" >&2
echo "  Demo smoke:  bash scripts/deploy_demo_cloud_smoke.sh" >&2
echo "  See: docs/runbooks/DEPLOY_TRUTH_MAP.md" >&2
exec bash "$(dirname "$0")/../deploy_rag_demo.sh" "$@"
