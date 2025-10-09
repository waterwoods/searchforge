#!/bin/bash
# AutoTuner 一页报告生成器
# 从 ~/Downloads/autotuner_runs/ 收集数据并生成完整报告

set -e

cd "$(dirname "$0")/.."

echo "🚀 AutoTuner 一页报告生成器"
echo "================================"
echo ""

# 步骤1: 收集数据
echo "📊 [1/4] 收集实验数据..."
python3 scripts/collect_onepager_data.py

# 步骤2: 生成时序曲线
echo ""
echo "📈 [2/4] 生成时序曲线..."
python3 scripts/plot_timeseries.py

# 步骤3: 生成 Markdown 报告
echo ""
echo "📝 [3/4] 生成 Markdown 报告..."
python3 scripts/build_onepager.py

# 步骤4: 生成 PDF 报告
echo ""
echo "📄 [4/4] 生成 PDF 报告..."
python3 scripts/generate_pdf_report.py

echo ""
echo "================================"
echo "✅ 报告生成完成！"
echo ""
echo "输出文件："
echo "  📄 Markdown: docs/RESULTS_SUMMARY.md"
echo "  📄 PDF:      docs/one_pager_autotuner.pdf"
echo "  📊 曲线图:   docs/plots/scenario_{A,B,C}_{recall,p95}.png"
echo ""

