#!/bin/bash
# compare_window60s_vs_dashboard.sh - 对比 /metrics/window60s vs /dashboard.json
# 验证内存聚合与 CSV 聚合的口径一致性（允许 ±10% 误差）

set -e

API_URL="http://localhost:8080"
TOLERANCE=0.10  # ±10%

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "========================================"
echo "  Window60s vs Dashboard Comparison"
echo "========================================"
echo ""

# 获取 /metrics/window60s
echo "[1/3] Fetching /metrics/window60s..."
WINDOW_RESP=$(curl -s "$API_URL/metrics/window60s")
WINDOW_OK=$(echo "$WINDOW_RESP" | jq -r '.ok // false')

if [ "$WINDOW_OK" != "true" ]; then
    echo -e "${RED}SKIP${NC}: window60s not available"
    echo "Response: $WINDOW_RESP"
    exit 1
fi

WINDOW_SAMPLES=$(echo "$WINDOW_RESP" | jq -r '.samples // 0')
WINDOW_P95=$(echo "$WINDOW_RESP" | jq -r '.p95_ms // null')
WINDOW_TPS=$(echo "$WINDOW_RESP" | jq -r '.tps // 0')
WINDOW_RECALL=$(echo "$WINDOW_RESP" | jq -r '.recall_at_10 // null')

echo "  samples: $WINDOW_SAMPLES"
echo "  p95_ms: $WINDOW_P95"
echo "  tps: $WINDOW_TPS"
echo "  recall_at_10: $WINDOW_RECALL"
echo ""

# 获取 /dashboard.json
echo "[2/3] Fetching /dashboard.json..."
DASH_RESP=$(curl -s "$API_URL/dashboard.json")

# 提取 dashboard 的窗口配置
DASH_WINDOW=$(echo "$DASH_RESP" | jq -r '.meta.window_sec // null')

# 检查窗口口径是否一致
if [ "$DASH_WINDOW" != "60" ] && [ "$DASH_WINDOW" != "null" ]; then
    echo -e "${YELLOW}  WARNING: Dashboard window_sec=$DASH_WINDOW (expected 60)${NC}"
    echo -e "${YELLOW}  口径不同，对比结果可能不准确${NC}"
    echo ""
fi

# 提取 dashboard 的实际 P95（current_p95 或 actual_p95）
DASH_P95=$(echo "$DASH_RESP" | jq -r '.sla.current_p95 // .sla.actual_p95 // null')
# 提取 TPS（kpi.tps 或 cards.tps）
DASH_TPS=$(echo "$DASH_RESP" | jq -r '.kpi.tps // .cards.tps // null')
# 提取 Recall（取最近的 recall_on 平均值，若无则标记 NA）
DASH_RECALL_ON=$(echo "$DASH_RESP" | jq -r '.series.recall_on[-5:] | if length > 0 then (map(.[1]) | add / length) else null end')

echo "  meta.window_sec: ${DASH_WINDOW:-'(not set)'}"
echo "  sla.current_p95: $DASH_P95"
echo "  kpi.tps: $DASH_TPS"
echo "  recall_on (avg last 5): $DASH_RECALL_ON"
echo ""

# 对比函数
compare_metric() {
    local name=$1
    local val1=$2
    local val2=$3
    
    if [ "$val1" = "null" ] || [ "$val2" = "null" ]; then
        echo -e "${BLUE}  $name: NA (one or both values null)${NC}"
        return 2  # NA
    fi
    
    # 检查除数是否为 0
    local is_zero=$(echo "$val2 == 0" | bc -l)
    if [ "$is_zero" -eq 1 ]; then
        echo -e "${BLUE}  $name: NA (dashboard value is 0)${NC}"
        return 2  # NA
    fi
    
    # 计算差异百分比
    local diff=$(echo "scale=4; ($val1 - $val2) / $val2" | bc -l)
    local abs_diff=$(echo "$diff" | tr -d '-')
    local pct=$(echo "scale=1; $diff * 100" | bc -l)
    
    # 判断是否在容差内
    local in_range=$(echo "$abs_diff <= $TOLERANCE" | bc -l)
    
    if [ "$in_range" -eq 1 ]; then
        echo -e "${GREEN}  $name: PASS${NC} (window=$val1, dash=$val2, diff=${pct}%)"
        return 0  # PASS
    else
        echo -e "${YELLOW}  $name: WARN${NC} (window=$val1, dash=$val2, diff=${pct}%)"
        return 1  # WARN/FAIL
    fi
}

# 执行对比
echo "[3/3] Comparing metrics (tolerance: ±10%)..."
echo ""

PASS_COUNT=0
WARN_COUNT=0
NA_COUNT=0

# P95 对比
if compare_metric "P95" "$WINDOW_P95" "$DASH_P95"; then
    ((PASS_COUNT++))
else
    case $? in
        1) ((WARN_COUNT++)) ;;
        2) ((NA_COUNT++)) ;;
    esac
fi

# TPS 对比
if compare_metric "TPS" "$WINDOW_TPS" "$DASH_TPS"; then
    ((PASS_COUNT++))
else
    case $? in
        1) ((WARN_COUNT++)) ;;
        2) ((NA_COUNT++)) ;;
    esac
fi

# Recall 对比
if compare_metric "Recall@10" "$WINDOW_RECALL" "$DASH_RECALL_ON"; then
    ((PASS_COUNT++))
else
    case $? in
        1) ((WARN_COUNT++)) ;;
        2) ((NA_COUNT++)) ;;
    esac
fi

echo ""
echo "========================================"

# 判断结论
TOTAL_VALID=$((PASS_COUNT + WARN_COUNT))

# 检查窗口口径一致性
if [ "$DASH_WINDOW" = "60" ]; then
    echo -e "${GREEN}  ✓ Window alignment: dashboard window_sec=60s${NC}"
elif [ "$DASH_WINDOW" = "null" ] || [ -z "$DASH_WINDOW" ]; then
    echo -e "${YELLOW}  ⚠ Window not set in dashboard (assuming 60s)${NC}"
else
    echo -e "${RED}  ✗ Window mismatch: dashboard=$DASH_WINDOW, expected=60${NC}"
    echo -e "${YELLOW}  口径不同，对比结果可能不准确${NC}"
fi
echo ""

if [ "$WINDOW_SAMPLES" -lt 50 ]; then
    echo -e "${YELLOW}  NOTICE: Low samples ($WINDOW_SAMPLES < 50)${NC}"
    echo "  More samples needed for reliable comparison"
    echo ""
fi

if [ "$WARN_COUNT" -eq 0 ]; then
    echo -e "  ${GREEN}✓ COMPARISON PASSED${NC}"
    echo "  All metrics within ±10% tolerance"
    echo "  (PASS: $PASS_COUNT, NA: $NA_COUNT)"
    echo "========================================"
    exit 0
elif [ "$PASS_COUNT" -ge 2 ] && [ "$TOTAL_VALID" -ge 2 ]; then
    echo -e "  ${YELLOW}⚠ COMPARISON WARN${NC}"
    echo "  Some metrics outside tolerance"
    echo "  (PASS: $PASS_COUNT, WARN: $WARN_COUNT, NA: $NA_COUNT)"
    echo "========================================"
    exit 1
else
    echo -e "  ${RED}✗ COMPARISON FAILED${NC}"
    echo "  Metrics differ significantly"
    echo "  (PASS: $PASS_COUNT, WARN: $WARN_COUNT, NA: $NA_COUNT)"
    echo "========================================"
    exit 1
fi

