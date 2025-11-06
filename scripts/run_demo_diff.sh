#!/bin/bash
# run_demo_diff.sh - 一键运行对比演示

set -e

echo "🚀 对比演示启动..."
echo "=========================================="

# 1. 确保 API 服务运行
if ! curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo "⚠️  API服务未运行，请先启动: bash launch.sh"
    exit 1
fi

echo "✓ API服务正常"

# 2. 运行差异挖掘
echo ""
echo "🔍 开始挖掘差异案例..."
python3 scripts/mine_diff_cases.py

# 3. 统计结果
COMPARE_FILE="reports/compare_batch_latest.json"
if [ -f "$COMPARE_FILE" ]; then
    # 提取统计数据
    TOTAL=$(jq -r '.total' "$COMPARE_FILE")
    IMPROVED=$(jq -r '.improved_count' "$COMPARE_FILE")
    MEDIAN_DELTA=$(jq -r '.median_rank_delta' "$COMPARE_FILE")
    
    # 计算触发原因分布
    KW_COUNT=$(jq -r '[.items[] | select(.trigger_reason | contains("kw"))] | length' "$COMPARE_FILE")
    LEN_COUNT=$(jq -r '[.items[] | select(.trigger_reason | contains("len"))] | length' "$COMPARE_FILE")
    DISP_COUNT=$(jq -r '[.items[] | select(.trigger_reason | contains("dispersion"))] | length' "$COMPARE_FILE")
    
    echo ""
    echo "=========================================="
    echo "📊 对比结果摘要"
    echo "=========================================="
    echo "[COMPARE] kept=${IMPROVED}/${TOTAL} | improved=${IMPROVED} | median_rank_delta=+${MEDIAN_DELTA}"
    echo "[REASONS] kw:${KW_COUNT}, disp:${DISP_COUNT}, len:${LEN_COUNT}"
    echo ""
    echo "[HINT] DEMO_FORCE_DIFF=true (可关闭: services/fiqa_api/settings.py)"
    echo ""
    echo "✓ 访问标注页面: http://localhost:8080/judge?batch=latest"
    echo "=========================================="
else
    echo "⚠️  未找到对比结果文件"
    exit 1
fi

# 4. 自动打开浏览器（可选）
if command -v open &> /dev/null; then
    echo ""
    echo "🌐 自动打开浏览器..."
    open "http://localhost:8080/judge?batch=latest"
elif command -v xdg-open &> /dev/null; then
    xdg-open "http://localhost:8080/judge?batch=latest"
fi

echo ""
echo "✓ 完成！"

