#!/usr/bin/env bash
# setup_soak_env.sh - Setup and verify environment for 60-minute soak test
# Sets required environment variables and validates service state

set -euo pipefail

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 Setting Up Soak Test Environment"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. Set Environment Variables
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "1️⃣  Setting environment variables..."

export DISABLE_FAISS=true
export PREWARM_FAISS=false
export VECTOR_BACKEND=milvus
export LAB_REDIS_TTL=86400
export KMP_DUPLICATE_LIB_OK=TRUE

echo "  ✓ DISABLE_FAISS=$DISABLE_FAISS"
echo "  ✓ PREWARM_FAISS=$PREWARM_FAISS"
echo "  ✓ VECTOR_BACKEND=$VECTOR_BACKEND"
echo "  ✓ LAB_REDIS_TTL=$LAB_REDIS_TTL (24h)"
echo "  ✓ KMP_DUPLICATE_LIB_OK=$KMP_DUPLICATE_LIB_OK"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. Check if Service is Running
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo ""
echo "2️⃣  Checking service on port 8011..."

if lsof -ti:8011 >/dev/null 2>&1; then
  echo "  ✓ Service already running on port 8011"
  PID=$(lsof -ti:8011)
  echo "  PID: $PID"
else
  echo "  ⚠️  No service on port 8011"
  echo "  Starting service..."
  
  cd "$(dirname "$0")/../services/fiqa_api" || exit 1
  
  # Start in background with nohup
  nohup uvicorn app_main:app --port 8011 --reload > /tmp/fiqa_api_8011.log 2>&1 &
  PID=$!
  
  echo "  Started with PID: $PID"
  echo "  Waiting 5s for startup..."
  sleep 5
  
  # Verify it started
  if lsof -ti:8011 >/dev/null 2>&1; then
    echo "  ✓ Service started successfully"
  else
    echo "  ❌ Failed to start service"
    echo "  Check logs: /tmp/fiqa_api_8011.log"
    exit 1
  fi
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. Display Current Configuration
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Environment Setup Complete"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Key Settings:"
echo "  • Vector Backend: $VECTOR_BACKEND (FAISS disabled)"
echo "  • Redis TTL: 24 hours (auto-refresh on writes)"
echo "  • Service: http://localhost:8011"
echo ""
echo "Next Steps:"
echo "  1. Run preflight checks: ./scripts/verify_preflight.sh"
echo "  2. Run mini A/B test: ./scripts/run_mini_ab.sh --qps 6 --window 90"
echo "  3. Run 60-min soak: ./scripts/run_soak_60m.sh --qps 6 --window 1800"
echo ""

