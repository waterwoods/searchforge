#!/bin/bash
# Pre-demo warmup — avoid cold start before broker demo
# =====================================================
# Call 2–3 min before demo to warm Cloud Run / local backend.
# Reduces Turn 1 latency when first request hits a cold instance.
#
# Usage: bash scripts/warmup_for_demo.sh [--port PORT] [--url URL]
#   --port: local port (default 8001)
#   --url:  full base URL (overrides port; use for Cloud Run)
#
# Example (local):  bash scripts/warmup_for_demo.sh
# Example (Cloud):  bash scripts/warmup_for_demo.sh --url https://fiqa-api-xxx.run.app

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${PORT:-8001}"
BASE_URL=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --port) PORT="$2"; shift 2 ;;
    --url)  BASE_URL="$2"; shift 2 ;;
    *) shift ;;
  esac
done

if [ -z "$BASE_URL" ]; then
  BASE_URL="http://127.0.0.1:$PORT"
fi

echo "Warming backend at $BASE_URL..."
echo ""

# 1. Health / readiness (healthz for local; readyz/health fallback for Cloud Run)
echo "[1] Health check..."
if curl -sf --max-time 15 "$BASE_URL/healthz" > /dev/null 2>&1; then
  echo "  OK (/healthz)"
elif curl -sf --max-time 15 "$BASE_URL/readyz" > /dev/null 2>&1; then
  echo "  OK (/readyz — Cloud Run)"
elif curl -sf --max-time 15 "$BASE_URL/health" > /dev/null 2>&1; then
  echo "  OK (/health — fallback)"
else
  echo "  SKIP (backend not running)"
  exit 0
fi

echo "[2] /readyz..."
if curl -sf --max-time 15 "$BASE_URL/readyz" > /dev/null 2>&1; then
  echo "  OK"
else
  echo "  SKIP or not ready (Qdrant/embedder may still warm)"
fi

# 3. Triage ping — realistic Turn 1 payload (warms triage + embedder if retrieval enabled)
echo "[3] /api/inbox/triage (Turn 1 payload)..."
# Use a short high-frequency opener so lightweight path warms; LLM path also warms if enabled
BODY='{"text":"Payment failed. Client says they already paid. What should I do?","persist_case":false}'
if RESP=$(curl -sf --max-time 30 -X POST "$BASE_URL/api/inbox/triage" \
  -H "Content-Type: application/json" \
  -d "$BODY" 2>/dev/null); then
  if echo "$RESP" | grep -q '"issue_category"'; then
    echo "  OK (triage warm)"
  else
    echo "  OK (response received)"
  fi
else
  echo "  SKIP (triage failed or timeout)"
fi

echo ""
echo "Warmup complete. Backend should be warm for Turn 1."
echo "Open demo URL and run first scenario within 2–3 min."
echo ""
echo "Tip: For Cloud Run, use: bash scripts/warmup_for_demo.sh --url https://YOUR-CLOUD-RUN-URL"
