#!/usr/bin/env bash
echo "DEPLOY: deploy_demo_cloud_smoke.sh — DEMO cloud smoke only (DEMO_MODE)." >&2
echo "  Paid pilot:  bash scripts/deploy_paid_pilot.sh" >&2
echo "  See: docs/CURRENT_PRODUCT_SHAPE.md § Demo vs paid pilot" >&2
exec bash "$(dirname "$0")/../deploy_demo_cloud_smoke.sh" "$@"
