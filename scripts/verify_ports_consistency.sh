#!/bin/bash
# Port Consistency Verification Script
# Ensures all services use the correct ports from .env

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 PORT CONSISTENCY VERIFICATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

EXIT_CODE=0

# Check 1: .env file exists and has APP_DEMO_URL
echo "✓ Check 1: .env configuration"
if [ ! -f ".env" ]; then
    echo "  ❌ FAIL: .env file not found"
    EXIT_CODE=1
else
    APP_DEMO_URL=$(grep "^APP_DEMO_URL=" .env | cut -d= -f2)
    if [ "$APP_DEMO_URL" != "http://localhost:8001" ]; then
        echo "  ❌ FAIL: APP_DEMO_URL should be http://localhost:8001, got: $APP_DEMO_URL"
        EXIT_CODE=1
    else
        echo "  ✅ PASS: APP_DEMO_URL=http://localhost:8001"
    fi
fi
echo ""

# Check 2: Backend health check
echo "✓ Check 2: Backend on port 8001"
if curl -s -f http://localhost:8001/ops/summary > /dev/null 2>&1; then
    echo "  ✅ PASS: Backend responding on port 8001"
else
    echo "  ❌ FAIL: Backend not responding on http://localhost:8001/ops/summary"
    echo "     → Start with: cd services/fiqa_api && PORT=8001 uvicorn app_v2:app --host 0.0.0.0 --port 8001"
    EXIT_CODE=1
fi
echo ""

# Check 3: No :8765 references in codebase
echo "✓ Check 3: No port 8765 drift in codebase"
FOUND_8765=$(grep -r ":8765" \
    --exclude-dir=node_modules \
    --exclude-dir=__pycache__ \
    --exclude-dir=.git \
    --exclude-dir=qdrant_storage \
    --exclude="*.pyc" \
    --exclude="PORT_DRIFT_REPORT.md" \
    --exclude="PORT_CONSOLIDATION_NOTE.md" \
    --exclude="verify_ports_consistency.sh" \
    . 2>/dev/null | wc -l | tr -d ' ')

if [ "$FOUND_8765" -gt "0" ]; then
    echo "  ❌ FAIL: Found $FOUND_8765 references to :8765 in codebase"
    echo "     → Run: grep -rn ':8765' --exclude-dir=node_modules ."
    EXIT_CODE=1
else
    echo "  ✅ PASS: No :8765 references found"
fi
echo ""

# Check 4: Frontend .env
echo "✓ Check 4: Frontend VITE_API_BASE configuration"
if [ -f "frontend/.env" ]; then
    VITE_API_BASE=$(grep "^VITE_API_BASE=" frontend/.env | cut -d= -f2)
    if [ "$VITE_API_BASE" != "http://localhost:8001" ]; then
        echo "  ❌ FAIL: VITE_API_BASE should be http://localhost:8001, got: $VITE_API_BASE"
        EXIT_CODE=1
    else
        echo "  ✅ PASS: VITE_API_BASE=http://localhost:8001"
    fi
else
    echo "  ⚠️  WARNING: frontend/.env not found (will use fallback)"
fi
echo ""

# Check 5: Dashboard endpoints
echo "✓ Check 5: Dashboard API endpoints"
ENDPOINTS=("ops/summary" "tuner/enabled" "ops/black_swan/status")
ALL_OK=true

for endpoint in "${ENDPOINTS[@]}"; do
    if curl -s -f "http://localhost:8001/$endpoint" > /dev/null 2>&1; then
        echo "  ✅ GET /$endpoint"
    else
        echo "  ❌ GET /$endpoint - not responding"
        ALL_OK=false
        EXIT_CODE=1
    fi
done
echo ""

# Check 6: CORS configuration
echo "✓ Check 6: CORS allows frontend origin"
if grep -q "allow_origins=\[\"http://localhost:3000\"" services/fiqa_api/app_v2.py; then
    echo "  ✅ PASS: CORS configured for http://localhost:3000"
else
    echo "  ⚠️  WARNING: CORS may not be properly configured"
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ ALL CHECKS PASSED - Port configuration is consistent!"
    echo ""
    echo "Port Map:"
    echo "  • Frontend:      http://localhost:3000"
    echo "  • Ops/Metrics:   http://localhost:8001 (app_v2.py)"
    echo "  • FIQA API:      http://localhost:8080 (app.py)"
    echo "  • Qdrant:        http://localhost:6333"
else
    echo "❌ SOME CHECKS FAILED - See errors above"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

exit $EXIT_CODE

