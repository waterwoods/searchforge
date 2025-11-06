#!/bin/bash
# 1分钟快速自检：TPS + Redis + 时间轴对齐
# Quick self-check: TPS validation with Redis backend

set -euo pipefail

BASE_URL="${1:-http://localhost:8080}"
CONCURRENCY="${CONCURRENCY:-16}"  # 可设 CONCURRENCY=32 提高

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $*"; }
ok() { echo -e "${GREEN}✅${NC} $*"; }
fail() { echo -e "${RED}❌${NC} $*"; exit 1; }
warn() { echo -e "${YELLOW}⚠️${NC}  $*"; }

echo "========================================="
echo "快速自检 (1分钟)"
echo "========================================="
echo ""

# ===== 1. 健康检查 =====
log "Step 1/5: 检查服务健康..."
health=$(curl -sf "${BASE_URL}/admin/health" 2>&1) || fail "服务未响应 ${BASE_URL}"

status=$(echo "$health" | jq -r '.status' 2>/dev/null || echo "unknown")
backend=$(echo "$health" | jq -r '.core_metrics_backend' 2>/dev/null || echo "unknown")

if [ "$status" != "ok" ]; then
    fail "服务状态异常: $status"
fi

ok "服务健康: status=$status"

# ===== 2. Redis 后端检查 =====
log "Step 2/5: 检查 Redis 后端..."
if [ "$backend" = "redis" ]; then
    redis_connected=$(echo "$health" | jq -r '.redis_connected' 2>/dev/null || echo "false")
    if [ "$redis_connected" = "true" ]; then
        ok "Redis 后端: core_metrics_backend=redis ✓ (已连接)"
    else
        warn "Redis 后端配置但未连接，将回退到内存模式"
    fi
elif [ "$backend" = "memory" ]; then
    warn "当前使用内存后端 (memory)，如需 Redis 请设置 CORE_METRICS_BACKEND=redis 并重启"
else
    warn "后端状态未知: $backend"
fi

# ===== 3. 启动 AutoTraffic (关闭分流、开并发) =====
log "Step 3/5: 启动 AutoTraffic (cases=live, shadow=0, concurrency=${CONCURRENCY})..."

start_resp=$(curl -sf -X POST \
    "${BASE_URL}/auto/start?qps=12&duration=60&cycle=65&cases=live&concurrency=${CONCURRENCY}&total_cycles=1" \
    2>&1) || fail "启动 AutoTraffic 失败"

ok "AutoTraffic 已启动 (并发=${CONCURRENCY}, 纯 live 模式)"

# ===== 4. 快速 TPS 采样 (30s) =====
log "Step 4/5: 快速 TPS 采样 (等待 30s)..."

for i in {1..6}; do
    sleep 5
    status=$(curl -sf "${BASE_URL}/auto/status" 2>&1) || continue
    
    tps=$(echo "$status" | grep -o '"effective_tps_60s":[^,}]*' | sed 's/.*://' || echo "0")
    running=$(echo "$status" | grep -o '"running":[^,}]*' | sed 's/.*://' || echo "false")
    in_flight=$(echo "$status" | grep -o '"in_flight":[^,}]*' | sed 's/.*://' || echo "0")
    
    echo "  [${i}×5s] tps=${tps} running=${running} in_flight=${in_flight}"
done

# 获取最终 TPS
runtime=$(curl -sf "${BASE_URL}/admin/runtime" 2>&1) || fail "无法获取 /admin/runtime"
final_tps=$(echo "$runtime" | grep -o '"tps_60s":[^,}]*' | sed 's/.*://' || echo "0")
duty=$(echo "$runtime" | grep -o '"duty":[^,}]*' | sed 's/.*://' || echo "0")
workers=$(echo "$runtime" | grep -o '"workers":[^,}]*' | sed 's/.*://' || echo "1")

echo ""
echo "-----------------------------------------"
echo "TPS 采样结果:"
echo "  Workers: ${workers}"
echo "  Concurrency: ${CONCURRENCY}"
echo "  Duty: ${duty}"
echo "  TPS (60s): ${final_tps}"
echo "-----------------------------------------"

# 检查 TPS 阈值
threshold=10.0
if awk "BEGIN {exit !($final_tps >= $threshold)}"; then
    ok "TPS 达标: ${final_tps} ≥ ${threshold}"
else
    warn "TPS 未达标: ${final_tps} < ${threshold}"
    echo "  建议: CONCURRENCY=32 $0 或 WORKERS=4 ./start_server.sh"
fi

# ===== 5. 时间轴对齐检查 (快速版) =====
log "Step 5/5: 检查时间轴对齐 (series60s)..."

series=$(curl -sf "${BASE_URL}/metrics/series60s" 2>&1) || {
    warn "无法获取 /metrics/series60s (可能需要更多数据)"
    echo ""
    echo "========================================="
    echo "自检完成 (部分)"
    echo "========================================="
    exit 0
}

# 简化检查：只看 p95 是否有数据且不全为 null
p95_data=$(echo "$series" | grep -o '"p95":\[[^]]*\]' || echo '"p95":[]')
p95_count=$(echo "$p95_data" | grep -o '\[' | wc -l | tr -d ' ')

if [ "$p95_count" -gt 0 ]; then
    # 检查是否全为 null
    non_null=$(echo "$p95_data" | grep -o '[0-9]\+\.[0-9]\+' | wc -l | tr -d ' ')
    
    if [ "$non_null" -gt 5 ]; then
        ok "时间轴对齐: series60s 有 ${non_null} 个非空数据点 ✓"
    else
        warn "时间轴数据稀疏: 仅 ${non_null} 个非空点 (需要更多采样)"
    fi
else
    warn "时间轴数据不足 (需要更多时间积累)"
fi

echo ""
echo "========================================="
echo "✅ 自检完成"
echo "========================================="
echo ""
echo "关键指标:"
echo "  • Redis 后端: ${backend}"
echo "  • TPS (60s): ${final_tps}"
echo "  • Concurrency: ${CONCURRENCY}"
echo "  • Cases: live (无分流)"
echo "  • 时间轴: $([ "$non_null" -gt 5 ] && echo "✓ 正常" || echo "⚠ 采样中")"
echo ""

# 完整验证提示
echo "如需完整验证 (60s):"
echo "  ./scripts/soak_tps.sh          # 完整 TPS 测试"
echo "  ./scripts/test_series60s_alignment.sh  # 完整时间轴验证"
echo ""

