#!/bin/bash
# Environment Variable Sync Verification
# Ensures frontend and backend use the same API base URL

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 ENVIRONMENT SYNC VERIFICATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

EXIT_CODE=0

# Read from root .env
if [ ! -f ".env" ]; then
    echo "❌ Root .env file not found"
    exit 1
fi

APP_DEMO_URL=$(grep "^APP_DEMO_URL=" .env | cut -d= -f2 | tr -d '\r\n ')
VITE_API_BASE_ROOT=$(grep "^VITE_API_BASE=" .env | cut -d= -f2 | tr -d '\r\n ')

echo "📋 Root .env configuration:"
echo "   APP_DEMO_URL    = $APP_DEMO_URL"
echo "   VITE_API_BASE   = $VITE_API_BASE_ROOT"
echo ""

# Check if they match
if [ "$APP_DEMO_URL" != "$VITE_API_BASE_ROOT" ]; then
    echo "⚠️  WARNING: Root .env values don't match!"
    echo "   Expected: VITE_API_BASE=$APP_DEMO_URL"
    echo "   Got:      VITE_API_BASE=$VITE_API_BASE_ROOT"
    echo ""
fi

# Read from frontend .env (if exists)
if [ -f "frontend/.env" ]; then
    VITE_API_BASE_FRONTEND=$(grep "^VITE_API_BASE=" frontend/.env | cut -d= -f2 | tr -d '\r\n ')
    echo "📋 Frontend .env configuration:"
    echo "   VITE_API_BASE   = $VITE_API_BASE_FRONTEND"
    echo ""
    
    # Check if frontend matches backend
    if [ "$APP_DEMO_URL" != "$VITE_API_BASE_FRONTEND" ]; then
        echo "❌ MISMATCH: Frontend and backend API bases don't match"
        echo "   Backend (APP_DEMO_URL):     $APP_DEMO_URL"
        echo "   Frontend (VITE_API_BASE):   $VITE_API_BASE_FRONTEND"
        echo ""
        echo "Fix: Run ./start_dashboard.sh to sync, or manually update frontend/.env"
        EXIT_CODE=1
    else
        echo "✅ Frontend and backend API bases match!"
        echo ""
    fi
else
    echo "⚠️  Frontend .env not found (will be created on startup)"
    echo ""
fi

# Check for hardcoded ports
echo "🔍 Checking for hardcoded port references..."
HARDCODED=$(grep -rn "localhost:8765" \
    --exclude-dir=node_modules \
    --exclude-dir=__pycache__ \
    --exclude-dir=.git \
    --exclude-dir=qdrant_storage \
    --exclude="*.pyc" \
    --exclude="PORT_*" \
    --exclude="verify_*" \
    . 2>/dev/null | wc -l | tr -d ' ')

if [ "$HARDCODED" -gt "0" ]; then
    echo "❌ Found $HARDCODED hardcoded port 8765 references"
    EXIT_CODE=1
else
    echo "✅ No hardcoded port 8765 references found"
fi
echo ""

# Test actual connectivity
echo "🔌 Testing connectivity..."
if curl -s -f "$APP_DEMO_URL/ops/summary" > /dev/null 2>&1; then
    echo "✅ Backend responding at $APP_DEMO_URL"
else
    echo "⚠️  Backend not responding at $APP_DEMO_URL"
    echo "   (Start with: cd services/fiqa_api && PORT=8001 uvicorn app_v2:app --port 8001)"
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Env sync OK - All configurations match!"
    echo ""
    echo "Configuration:"
    echo "  • Backend API:  $APP_DEMO_URL"
    echo "  • Frontend API: $VITE_API_BASE_ROOT"
    echo "  • Status: ✅ Synced"
else
    echo "❌ Env sync FAILED - See errors above"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

exit $EXIT_CODE

