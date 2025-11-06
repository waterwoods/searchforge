#!/bin/bash
# 检查30分钟长测的进度

echo "🧭 30分钟长测进度监控"
echo "========================================================================"

# 检查进程是否在运行
if ps aux | grep -v grep | grep "run_canary_30min.py" > /dev/null; then
    echo "✅ 测试正在运行中..."
    
    # 显示进程信息
    ps aux | grep -v grep | grep "run_canary_30min.py" | awk '{print "   PID: " $2 "  CPU: " $3 "%  内存: " $4 "%"}'
    
    # 统计已收集的数据点
    if [ -f "services/fiqa_api/logs/api_metrics.csv" ]; then
        total_lines=$(wc -l < services/fiqa_api/logs/api_metrics.csv)
        on_count=$(grep -c ",on," services/fiqa_api/logs/api_metrics.csv 2>/dev/null || echo 0)
        off_count=$(grep -c ",off," services/fiqa_api/logs/api_metrics.csv 2>/dev/null || echo 0)
        
        echo ""
        echo "📊 数据收集进度:"
        echo "   总请求数: $total_lines"
        echo "   mode=on:  $on_count 个样本"
        echo "   mode=off: $off_count 个样本"
        
        # 估算进度（30分钟 = 1800秒，每10秒采样2次 = 360个样本）
        total_samples=$((on_count + off_count))
        expected_samples=360
        if [ $total_samples -gt 0 ]; then
            progress=$((total_samples * 100 / expected_samples))
            remaining=$((expected_samples - total_samples))
            remaining_minutes=$((remaining / 12))  # 12个样本/分钟
            
            echo "   进度: ${progress}% (预计剩余 ${remaining_minutes} 分钟)"
        fi
    fi
    
    # 显示最近的样本
    echo ""
    echo "📝 最近5个样本:"
    tail -5 services/fiqa_api/logs/api_metrics.csv 2>/dev/null | \
        awk -F',' '{printf "   [%s] mode=%s latency=%.1fms recall=%.3f\n", substr($1,12,8), $8, $2, $3}'
    
    echo ""
    echo "💡 提示:"
    echo "   - 再次运行此脚本查看进度: bash scripts/check_canary_progress.sh"
    echo "   - 测试完成后运行: python scripts/build_dashboard.py"
    echo "   - 查看结果: open http://localhost:8080/demo"
    
else
    echo "❌ 测试未运行"
    echo ""
    echo "启动测试:"
    echo "   python scripts/run_canary_30min.py --sources fiqa,news,forum"
    
    # 检查是否已有完成的报告
    if [ -f "reports/autotuner_canary.json" ]; then
        echo ""
        echo "✅ 发现已完成的报告:"
        cat reports/autotuner_canary.json | python -m json.tool 2>/dev/null | head -20
    fi
fi

echo "========================================================================"




