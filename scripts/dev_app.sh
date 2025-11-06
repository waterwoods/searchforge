#!/usr/bin/env bash

# ============================================================
# dev_app.sh - Unified Development Environment Startup Script
# ============================================================
# Starts: Redis + Qdrant + app_main(8011) + frontend(3000)
# Health checks all services and generates a summary report
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPORT_FILE="$PROJECT_ROOT/reports/dev_start_mini.txt"
LOG_DIR="$PROJECT_ROOT/logs"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Ensure directories exist
mkdir -p "$LOG_DIR"
mkdir -p "$(dirname "$REPORT_FILE")"

echo "=================================================="
echo "  SearchForge Dev Environment Startup"
echo "=================================================="
echo ""

# ============================================================
# 1. Start Infrastructure (Redis + Qdrant)
# ============================================================
echo -e "${BLUE}[1/4] Starting Infrastructure (Redis + Qdrant)...${NC}"
cd "$PROJECT_ROOT"

# Check if services are already running
REDIS_RUNNING=$(docker-compose ps redis 2>/dev/null | grep -c "Up" || echo "0")
QDRANT_RUNNING=$(docker-compose ps qdrant 2>/dev/null | grep -c "Up" || echo "0")

if [[ "$REDIS_RUNNING" == "0" ]] || [[ "$QDRANT_RUNNING" == "0" ]]; then
    docker-compose up -d redis qdrant
    echo "  Waiting for services to initialize..."
    sleep 3
else
    echo "  Redis and Qdrant already running"
fi

# Verify infrastructure
REDIS_STATUS="❌ FAIL"
QDRANT_STATUS="❌ FAIL"

if docker-compose ps redis 2>/dev/null | grep -q "Up"; then
    if timeout 2 bash -c "echo PING | nc -w 1 localhost 6379 | grep -q PONG" 2>/dev/null; then
        REDIS_STATUS="✅ PASS"
        echo -e "  ${GREEN}✓${NC} Redis: OK"
    else
        echo -e "  ${RED}✗${NC} Redis: UP but not responding"
    fi
else
    echo -e "  ${RED}✗${NC} Redis: Not running"
fi

if docker-compose ps qdrant 2>/dev/null | grep -q "Up"; then
    if timeout 2 curl -sf http://localhost:6333/healthz >/dev/null 2>&1; then
        QDRANT_STATUS="✅ PASS"
        echo -e "  ${GREEN}✓${NC} Qdrant: OK"
    else
        echo -e "  ${RED}✗${NC} Qdrant: UP but not responding"
    fi
else
    echo -e "  ${RED}✗${NC} Qdrant: Not running"
fi

echo ""

# ============================================================
# 2. Start Backend (app_main on port 8011)
# ============================================================
echo -e "${BLUE}[2/4] Starting Backend (app_main)...${NC}"

# Kill any existing app_main process
pkill -f "python.*app_main.py" 2>/dev/null || true
sleep 1

# Start backend
cd "$PROJECT_ROOT/services/fiqa_api"
nohup python app_main.py > "$LOG_DIR/app_main.log" 2>&1 &
BACKEND_PID=$!

echo "  Backend started (PID: $BACKEND_PID)"
echo "  Log: $LOG_DIR/app_main.log"
echo "  Waiting for backend to be ready..."
sleep 3

# Check backend health
BACKEND_STATUS="❌ FAIL"
BACKEND_VERIFY_OK="false"
PROXY_TO_V2="unknown"
REDIS_BACKEND_OK="false"
QDRANT_BACKEND_OK="false"

for i in {1..10}; do
    if timeout 2 curl -sf http://localhost:8011/healthz >/dev/null 2>&1; then
        BACKEND_STATUS="✅ PASS"
        echo -e "  ${GREEN}✓${NC} Backend: Responding on http://localhost:8011"
        
        # Get detailed verify info
        VERIFY_JSON=$(curl -s http://localhost:8011/ops/verify 2>/dev/null || echo "{}")
        BACKEND_VERIFY_OK=$(echo "$VERIFY_JSON" | jq -r '.ok // false' 2>/dev/null || echo "false")
        PROXY_TO_V2=$(echo "$VERIFY_JSON" | jq -r '.proxy_to_v2 // "unknown"' 2>/dev/null || echo "unknown")
        REDIS_BACKEND_OK=$(echo "$VERIFY_JSON" | jq -r '.data_sources.redis.connected // .data_sources.redis.ok // false' 2>/dev/null || echo "false")
        QDRANT_BACKEND_OK=$(echo "$VERIFY_JSON" | jq -r '.data_sources.qdrant.available // false' 2>/dev/null || echo "false")
        
        break
    fi
    sleep 1
done

if [[ "$BACKEND_STATUS" == "❌ FAIL" ]]; then
    echo -e "  ${RED}✗${NC} Backend: Failed to start (check logs/app_main.log)"
fi

echo ""

# ============================================================
# 3. Start Frontend (npm run dev on port 3000)
# ============================================================
echo -e "${BLUE}[3/4] Starting Frontend...${NC}"

# Kill any existing frontend process
pkill -f "vite.*3000" 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
sleep 1

# Start frontend
cd "$PROJECT_ROOT/frontend"
nohup npm run dev > "$LOG_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!

echo "  Frontend started (PID: $FRONTEND_PID)"
echo "  Log: $LOG_DIR/frontend.log"
echo "  Waiting for frontend to be ready..."
sleep 3

# Check frontend health
FRONTEND_STATUS="❌ FAIL"
for i in {1..10}; do
    if timeout 2 curl -sf http://localhost:3000 >/dev/null 2>&1; then
        FRONTEND_STATUS="✅ PASS"
        echo -e "  ${GREEN}✓${NC} Frontend: Responding on http://localhost:3000"
        break
    fi
    sleep 1
done

if [[ "$FRONTEND_STATUS" == "❌ FAIL" ]]; then
    echo -e "  ${YELLOW}⚠${NC} Frontend: May still be starting (check logs/frontend.log)"
fi

echo ""

# ============================================================
# 4. Health Verification Summary
# ============================================================
echo -e "${BLUE}[4/4] Health Verification...${NC}"

# Determine overall status
OVERALL_STATUS="✅ SUCCESS"
if [[ "$REDIS_STATUS" == *"FAIL"* ]] || [[ "$QDRANT_STATUS" == *"FAIL"* ]] || \
   [[ "$BACKEND_STATUS" == *"FAIL"* ]] || [[ "$BACKEND_VERIFY_OK" != "true" ]]; then
    OVERALL_STATUS="❌ PARTIAL"
fi

# Display summary
echo ""
echo "=================================================="
echo "  Dev Environment Status"
echo "=================================================="
echo -e "Redis:          $REDIS_STATUS"
echo -e "Qdrant:         $QDRANT_STATUS"
echo -e "Backend:        $BACKEND_STATUS"
echo -e "  - Verify OK:  $([ "$BACKEND_VERIFY_OK" = "true" ] && echo "✅" || echo "❌") ($BACKEND_VERIFY_OK)"
echo -e "  - Proxy V2:   $PROXY_TO_V2"
echo -e "  - Redis Data: $([ "$REDIS_BACKEND_OK" = "true" ] && echo "✅" || echo "❌") ($REDIS_BACKEND_OK)"
echo -e "  - Qdrant:     $([ "$QDRANT_BACKEND_OK" = "true" ] && echo "✅" || echo "❌") ($QDRANT_BACKEND_OK)"
echo -e "Frontend:       $FRONTEND_STATUS"
echo ""
echo -e "Overall:        $OVERALL_STATUS"
echo "=================================================="
echo ""

# ============================================================
# 5. Generate Report
# ============================================================
cat > "$REPORT_FILE" << EOF
== Dev Startup Summary ==
Generated: $(date '+%Y-%m-%d %H:%M:%S')

Infrastructure Status:
---------------------
Redis:          $REDIS_STATUS
Qdrant:         $QDRANT_STATUS

Backend Status (app_main):
-------------------------
Service:        $BACKEND_STATUS
Verify OK:      $BACKEND_VERIFY_OK
Proxy to V2:    $PROXY_TO_V2
Redis Backend:  $REDIS_BACKEND_OK
Qdrant Backend: $QDRANT_BACKEND_OK

Frontend Status:
---------------
Service:        $FRONTEND_STATUS

Overall Result:
--------------
Total:          $OVERALL_STATUS

Next Steps:
----------
1. Visit frontend:  http://localhost:3000
2. Check backend:   http://localhost:8011/healthz
3. Full verify:     http://localhost:8011/ops/verify

Logs:
----
Backend:  $LOG_DIR/app_main.log
Frontend: $LOG_DIR/frontend.log

Process IDs:
-----------
Backend:  $BACKEND_PID
Frontend: $FRONTEND_PID

Troubleshooting:
---------------
EOF

# Add troubleshooting tips for failed components
if [[ "$REDIS_STATUS" == *"FAIL"* ]]; then
    echo "❌ Redis failed (check: docker-compose logs redis)" >> "$REPORT_FILE"
fi

if [[ "$QDRANT_STATUS" == *"FAIL"* ]]; then
    echo "❌ Qdrant failed (check: docker-compose logs qdrant)" >> "$REPORT_FILE"
fi

if [[ "$BACKEND_STATUS" == *"FAIL"* ]]; then
    echo "❌ Backend failed (check: $LOG_DIR/app_main.log)" >> "$REPORT_FILE"
fi

if [[ "$FRONTEND_STATUS" == *"FAIL"* ]]; then
    echo "❌ Frontend failed (check: $LOG_DIR/frontend.log)" >> "$REPORT_FILE"
fi

if [[ "$OVERALL_STATUS" == "✅ SUCCESS" ]]; then
    echo "✅ All services started successfully!" >> "$REPORT_FILE"
fi

echo "" >> "$REPORT_FILE"
echo "Report saved to: $REPORT_FILE"

# Display final message
echo ""
if [[ "$OVERALL_STATUS" == "✅ SUCCESS" ]]; then
    echo -e "${GREEN}🎉 All services started successfully!${NC}"
    echo ""
    echo "Next: visit http://localhost:3000"
else
    echo -e "${YELLOW}⚠️  Some services may have issues${NC}"
    echo ""
    echo "Check the logs and report for details:"
    echo "  Report: $REPORT_FILE"
    echo "  Backend Log: $LOG_DIR/app_main.log"
    echo "  Frontend Log: $LOG_DIR/frontend.log"
fi

echo ""
echo "=================================================="

exit 0

