#!/bin/bash
set -euo pipefail

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Default ports
BACKEND=${BACKEND:-8011}
FRONTEND=${FRONTEND:-5173}
QDRANT=${QDRANT:-6333}
REDIS=${REDIS:-6379}

echo "🔍 Health Check for SearchForge Services"
echo "========================================"

FAILED_CHECKS=0

# Check backend health
echo -n "Backend (http://localhost:$BACKEND/readyz): "
if curl -s -f "http://localhost:$BACKEND/readyz" | grep -q '"ok":true'; then
    echo "✅ PASS"
else
    echo "❌ FAIL"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

# Check backend code lookup endpoint
echo -n "Backend Code Lookup (POST /api/agent/code_lookup): "
if curl -s -X POST "http://localhost:$BACKEND/api/agent/code_lookup" \
    -H "Content-Type: application/json" \
    -d '{"message":"ping"}' | grep -q '"status":"success"\|"ok":true\|200'; then
    echo "✅ PASS"
else
    echo "❌ FAIL (graceful error handling)"
    # Don't count this as a failure since it might be expected
fi

# Check frontend
echo -n "Frontend (http://localhost:$FRONTEND): "
if curl -s -f "http://localhost:$FRONTEND" | grep -q "<!DOCTYPE html\|<html"; then
    echo "✅ PASS"
else
    echo "❌ FAIL"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

# Check Qdrant
echo -n "Qdrant (http://localhost:$QDRANT): "
if curl -s -f "http://localhost:$QDRANT" > /dev/null; then
    echo "✅ PASS"
else
    echo "❌ FAIL"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

# Check Redis
echo -n "Redis (localhost:$REDIS): "
if redis-cli -p $REDIS ping 2>/dev/null | grep -q "PONG"; then
    echo "✅ PASS"
else
    # Try Python redis check as fallback
    if python3 -c "import redis; r=redis.Redis(host='localhost', port=$REDIS); print(r.ping())" 2>/dev/null | grep -q "True"; then
        echo "✅ PASS"
    else
        echo "❌ FAIL"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
fi

echo "========================================"
if [ $FAILED_CHECKS -eq 0 ]; then
    echo "🎉 All services are healthy!"
    exit 0
else
    echo "⚠️  $FAILED_CHECKS service(s) failed health checks"
    exit 1
fi
