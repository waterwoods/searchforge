#!/bin/bash
# monitor_combo.sh - 监控正在运行的 Combo 测试
# 用法: ./scripts/monitor_combo.sh

clear
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  20 分钟 Combo 测试 - 实时监控"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# 检查进程
echo "📍 进程状态:"
if ps aux | grep -E "run_combo_20min|run_lab_headless" | grep -v grep | head -2; then
    echo "✓ 测试正在运行"
else
    echo "✗ 未检测到运行中的测试"
fi

echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 实验状态 (API):"
echo

# 查询 API 状态
STATUS=$(curl -s http://localhost:8011/ops/lab/status 2>/dev/null)

if echo "$STATUS" | jq -e '.ok' >/dev/null 2>&1; then
    RUNNING=$(echo "$STATUS" | jq -r '.running')
    PHASE=$(echo "$STATUS" | jq -r '.phase')
    ROUND=$(echo "$STATUS" | jq -r '.current_round // 0')
    TOTAL=$(echo "$STATUS" | jq -r '.total_rounds // 0')
    PROGRESS=$(echo "$STATUS" | jq -r '.current_window_progress // 0')
    
    echo "  Running: $RUNNING"
    echo "  Phase: $PHASE"
    echo "  Round: $ROUND / $TOTAL"
    echo "  Progress: $PROGRESS%"
else
    echo "  ⚠ API 未返回状态（可能正在启动或已完成）"
fi

echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 最新日志 (最后 20 行):"
echo

if [ -f /tmp/combo_20min_run.log ]; then
    tail -20 /tmp/combo_20min_run.log
else
    echo "  ⚠ 日志文件未找到"
fi

echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo
echo "💡 提示:"
echo "  • 查看完整日志: tail -f /tmp/combo_20min_run.log"
echo "  • 查看 API 状态: curl http://localhost:8011/ops/lab/status | jq"
echo "  • 重新运行监控: watch -n 10 ./scripts/monitor_combo.sh"
echo

