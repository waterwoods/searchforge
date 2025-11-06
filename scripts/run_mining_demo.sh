#!/bin/bash
# Step 4: 一键生成与打开页面

set -e

echo "🚀 Step 4: 一键生成与打开 Judge 页面"
echo ""

# 1. Run ground truth check
echo "📊 Step 1: 真值检查..."
python3 scripts/check_ground_truth.py
echo ""

# 2. Run mining script
echo "🔍 Step 2: 批量采样并挖差异..."
python3 scripts/mine_diff_cases.py
echo ""

# 2.5. Create demo votes (optional)
echo "🎭 创建演示投票数据..."
python3 scripts/create_demo_votes.py
echo ""

# 3. Open judge page
echo "🌐 Step 4: 打开 Judge 页面..."
JUDGE_URL="http://localhost:8080/judge?batch=mined"
REPORT_URL="http://localhost:8080/judge/report?batch=mined"

# Check if server is running
if ! curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo "⚠️  警告: API服务未运行，请先启动："
    echo "   cd services/fiqa_api && python app.py"
    exit 1
fi

echo "   ✅ Judge UI: $JUDGE_URL"
echo "   ✅ Report: $REPORT_URL"
echo ""
echo "   📋 说明："
echo "     1. Judge UI - 用于人工标注对比案例"
echo "     2. Report - 显示标注结果统计（需要先完成标注）"

# Open Judge UI first (for annotation)
if [[ "$OSTYPE" == "darwin"* ]]; then
    open "$JUDGE_URL"
    echo "   🌐 已打开 Judge 标注页面"
    echo ""
    echo "   📝 标注说明："
    echo "     1. 在Judge页面中对比 ON vs OFF 结果"
    echo "     2. 选择更好的结果：ON/OFF/SAME"
    echo "     3. 完成几个案例标注后，再访问 Report 页面查看统计"
    echo ""
    echo "   🔗 手动访问 Report 页面：$REPORT_URL"
else
    echo "   请手动访问: $JUDGE_URL"
fi

echo ""
echo "✅ 完成！后续步骤："
echo "   1. 在浏览器中查看对比报告"
echo "   2. 截图保存到 docs/cases/ 目录"
echo "   3. 更新 docs/one_pager_fiqa.pdf 的对比案例区块"

