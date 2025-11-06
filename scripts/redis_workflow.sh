#!/bin/bash
# redis_workflow.sh - Unified Redis workflow (≤120 LoC)
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load .env if available
if [ -f "$ROOT/.env" ]; then
    export $(grep -v '^#' "$ROOT/.env" | xargs)
fi

API="${FIQA_API_URL:-http://localhost:8080}"

check_api() { for i in {1..10}; do curl -s "$API/admin/health" &>/dev/null && return 0; sleep 1; done; return 1; }
parse() { R=$(curl -s "$API/admin/health"); BE=$(echo "$R"|grep -o '"core_metrics_backend":"[^"]*"'|cut -d'"' -f4); RC=$(echo "$R"|grep -o '"redis_connected":[^,}]*'|cut -d':' -f2|tr -d ' '); RO=$(echo "$R"|grep -o '"rows_60s":[0-9]*'|cut -d':' -f2); }

upd_env() {
    local m=$1 e="$ROOT/.env"
    grep -v "^CORE_METRICS_BACKEND=" "$e" 2>/dev/null|grep -v "^REDIS_" >"$e.tmp"||:
    if [ "$m" = "redis" ]; then
        cat >>"$e.tmp" <<E
CORE_METRICS_BACKEND=redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_METRICS_PREFIX=searchforge
REDIS_METRICS_TTL=120
E
    else echo "CORE_METRICS_BACKEND=memory" >>"$e.tmp"; fi
    mv "$e.tmp" "$e"
}

restart() {
    pkill -f "uvicorn services.fiqa_api"||:; sleep 1; cd "$ROOT/services/fiqa_api"
    [ "$1" = "redis" ]&&export CORE_METRICS_BACKEND=redis REDIS_HOST=localhost REDIS_PORT=6379||{ export CORE_METRICS_BACKEND=memory; unset REDIS_HOST REDIS_PORT REDIS_DB REDIS_METRICS_PREFIX REDIS_METRICS_TTL; }
    nohup uvicorn services.fiqa_api.app_main:app --host 0.0.0.0 --port 8080 >/dev/null 2>&1 &
    sleep 3
}

to_redis() {
    echo "=========================================="; echo "🔄 Switch to Redis"; echo "=========================================="
    command -v redis-server &>/dev/null||{ echo "❌ FAIL: Redis not found"; echo "💡 Fix: brew install redis"; return 1; }
    redis-cli ping &>/dev/null||{ redis-server --daemonize yes --port 6379 2>/dev/null||:; sleep 2; redis-cli ping &>/dev/null||{ echo "❌ FAIL: Cannot start Redis"; echo "💡 Fix: redis-server --daemonize yes"; return 1; }; }
    echo "✅ Redis OK"; upd_env redis; echo "✅ .env OK"; restart redis; echo "✅ API OK"
    check_api && parse && [ "$BE" = "redis" ] && [ "$RC" = "true" ] && { echo "✅ Backend: redis, Connected: true"; echo "=========================================="; echo "✅ PASS"; return 0; }
    echo "❌ FAIL: BE=$BE, RC=$RC"; return 1
}

to_mem() {
    echo "=========================================="; echo "🔄 Switch to Memory"; echo "=========================================="
    upd_env memory; echo "✅ .env OK"; restart memory; echo "✅ API OK"
    check_api && parse && [ "$BE" = "memory" ] && [ "$RC" = "false" ] && { echo "✅ Backend: memory"; echo "=========================================="; echo "✅ PASS"; return 0; }
    echo "❌ FAIL: BE=$BE, RC=$RC"; return 1
}

check() {
    echo "=========================================="; echo "📊 Status"; echo "=========================================="
    curl -s "$API/admin/health" &>/dev/null||{ echo "❌ FAIL: API down"; echo "💡 Fix: MAIN_PORT=8080 bash services/fiqa_api/start_server.sh"; return 1; }
    parse; echo "Backend: $BE"; echo "Redis: $RC"; echo "Rows: $RO"; echo "=========================================="; echo "✅ PASS"
}

verify() {
    echo "=========================================="; echo "🔍 Verify"; echo "=========================================="
    check_api||{ echo "❌ FAIL: API down"; return 1; }
    parse; echo "✅ [1/3] Health (BE=$BE, RC=$RC)"
    echo "[2/3] Load 30s..."
    LR=$(curl -s -X POST "$API/load/start?qps=12&duration=30&concurrency=16")
    echo "$LR"|grep -q '"ok":true'&&{ echo "✅ Load started"; sleep 32; }||echo "⚠️  Load skip"
    echo "[3/3] series60s..."
    SR=$(curl -s "$API/metrics/series60s")
    BK=$(echo "$SR"|grep -o '"buckets":[0-9]*'|cut -d':' -f2)
    ST=$(echo "$SR"|grep -o '"step_sec":[0-9]*'|cut -d':' -f2)
    SA=$(echo "$SR"|grep -o '"samples":[0-9]*'|cut -d':' -f2)
    F=0
    [ "$BK" -ge 12 ]&&echo "✅ Buckets: $BK"||{ echo "❌ Buckets: $BK"; F=1; }
    [ "$ST" = "5" ]&&echo "✅ Step: ${ST}s"||{ echo "❌ Step: $ST"; F=1; }
    [ "$SA" -ge 3 ]&&echo "✅ Samples: $SA"||{ echo "❌ Samples: $SA"; F=1; }
    echo "=========================================="
    [ $F -eq 0 ]&&{ echo "✅ PASS"; return 0; }||{ echo "❌ FAIL"; echo "💡 Fix: POST /search"; return 1; }
}

case "${1:-}" in
    --to-redis)  to_redis ;;
    --to-memory) to_mem ;;
    --check)     check ;;
    --verify)    verify ;;
    *)
        cat <<H
Usage: $0 [--to-redis|--to-memory|--check|--verify]

Commands:
  --to-redis    Switch to Redis backend
  --to-memory   Switch to Memory backend
  --check       Check current status
  --verify      Full validation (health+traffic+series60s)

Examples:
  $0 --to-redis   # Enable Redis
  $0 --verify     # Full check
  $0 --to-memory  # Rollback
H
        exit 1 ;;
esac
