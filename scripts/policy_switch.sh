#!/usr/bin/env bash
# policy_switch.sh - Switch current policy
# Usage: bash scripts/policy_switch.sh <policy_name>
#   policy_name: baseline | latency_v1

set -euo pipefail

POLICY_NAME=${1:-}

if [ -z "$POLICY_NAME" ]; then
    echo "Usage: bash scripts/policy_switch.sh <policy_name>"
    echo ""
    echo "Available policies:"
    echo "  baseline     - policy_baseline.json (ef=96, conc=12)"
    echo "  latency_v1   - policy_latency_v1.json (ef=32, conc=4, warm=100)"
    echo ""
    exit 1
fi

POLICY_FILE="configs/policies/policy_${POLICY_NAME}.json"

if [ ! -f "$POLICY_FILE" ]; then
    echo "❌ Error: Policy file not found: $POLICY_FILE"
    exit 1
fi

echo "🔄 Switching policy..."
echo ""
echo "Before:"
cat configs/policies/current_policy.json | python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"  Name: {d['name']}\"); print(f\"  efSearch: {d['ef_search']}\"); print(f\"  Concurrency: {d['concurrency']}\")"

echo ""

cp "$POLICY_FILE" configs/policies/current_policy.json

echo "After:"
cat configs/policies/current_policy.json | python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"  Name: {d['name']}\"); print(f\"  efSearch: {d['ef_search']}\"); print(f\"  Concurrency: {d['concurrency']}\")"

echo ""
echo "✅ Switched to: $POLICY_NAME"
echo ""
echo "Diff:"
diff -u <(cat "$POLICY_FILE" | head -8) <(cat configs/policies/current_policy.json | head -8) || echo "  (identical)"

