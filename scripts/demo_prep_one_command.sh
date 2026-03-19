#!/bin/bash
# One-command demo prep for broker demo
# ======================================
# Checks backend, runs validation, prints next steps.
# Use before a broker demo to confirm state.
#
# Usage: bash scripts/demo_prep_one_command.sh
#   USE_LOCAL_QDRANT=1  - expect local Qdrant (skip Cloud); suggest seed if needed

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
HEALTH_URL="http://127.0.0.1:8001/healthz"
DEMO_URL="http://localhost:5173/demo"
QDRANT_HOST="${QDRANT_HOST:-localhost}"
QDRANT_PORT="${QDRANT_PORT:-6333}"

cd "$REPO_DIR"

echo "=========================================="
echo "Broker Demo Prep"
echo "=========================================="
echo ""

# 1. Check backend
echo "[1] Backend health..."
if curl -sf --max-time 5 "$HEALTH_URL" > /dev/null 2>&1; then
  echo "  OK: Backend at 8001"
else
  echo "  FAIL: Backend not running. Start with: bash scripts/run_demo_local.sh"
  echo ""
  echo "  Fallback: Open $DEMO_URL, click the 5 recommended questions for offline demo."
  exit 1
fi

# 2. Run quick validate
echo ""
echo "[2] Validating 5 demo questions..."
if bash "$SCRIPT_DIR/demo_quick_validate.sh" 2>/dev/null; then
  echo "  OK: Live retrieval working"
  echo ""
  echo "=========================================="
  echo "Ready for Live Demo"
  echo "=========================================="
  echo "  Demo URL: $DEMO_URL"
  echo "  Mode: Live (real-time retrieval)"
  echo ""
  echo "  Quick ref: docs/ANDY_2MIN_BEFORE_DEMO.md"
  echo ""
else
  echo "  NOTE: Live retrieval failed."
  echo ""
  if [ "${USE_LOCAL_QDRANT:-0}" = "1" ]; then
    echo "=========================================="
    echo "Local Qdrant Path"
    echo "=========================================="
    echo "  1. Start Qdrant: docker compose up -d qdrant"
    echo "  2. Seed collection: bash scripts/seed_local_qdrant.sh"
    echo "  3. Run demo: USE_LOCAL_QDRANT=1 bash scripts/run_demo_local.sh"
    echo ""
    echo "  Or use Offline: Open $DEMO_URL, click the 5 recommended questions."
    exit 0
  fi
  echo "=========================================="
  echo "Use Offline Demo"
  echo "=========================================="
  echo "  1. Open: $DEMO_URL"
  echo "  2. Click the 5 recommended questions (in order)"
  echo "  3. Demo works with preset answers"
  echo ""
  echo "  To fix live:"
  echo "    - Wake Qdrant Cloud at cloud.qdrant.io, then restart backend"
  echo "    - Or use local Qdrant: bash scripts/seed_local_qdrant.sh, then USE_LOCAL_QDRANT=1 bash scripts/run_demo_local.sh"
  exit 0
fi
