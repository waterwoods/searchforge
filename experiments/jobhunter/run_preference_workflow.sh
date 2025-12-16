#!/bin/bash
# JobHunter Preference Workflow Script
# This script guides you through the RLHF-style preference rating workflow

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "=========================================="
echo "JobHunter Preference Workflow"
echo "=========================================="
echo ""

# Step 1: Check if initial report exists
REPORT_FILE="reports/jobhunter/job_shortlist_data_ml_platform_latest.md"
if [ ! -f "$REPORT_FILE" ]; then
    echo "⚠️  初始报告不存在，正在生成..."
    python3 -m experiments.jobhunter.job_hunter_report \
        --input-file data/jobhunter/scored/jobs_scored_data_ml_platform_latest.json \
        --min-match-score 8 \
        --output-file "$REPORT_FILE"
    echo "✅ 报告已生成: $REPORT_FILE"
else
    echo "✅ 初始报告已存在: $REPORT_FILE"
fi
echo ""

# Step 2: Interactive rating
echo "=========================================="
echo "Step 2: 交互式偏好打分"
echo "=========================================="
echo ""
echo "评分标准："
echo "  5 分：非常想要 / dream job"
echo "  4 分：很想要，合适"
echo "  3 分：一般，没感觉"
echo "  2 分：基本不想要"
echo "  1 分：完全不想要"
echo ""
echo "标签建议：remote, onsite_ok, dream, backup, safer_offer, hard_interview"
echo ""
read -p "按 Enter 开始交互式打分，或输入 'skip' 跳过（如果已完成打分）: " response

if [ "$response" != "skip" ]; then
    python3 -m experiments.jobhunter.job_preferences_cli \
        --scored-file data/jobhunter/scored/jobs_scored_data_ml_platform_latest.json \
        --min-match-score 8 \
        --max-jobs 20
    echo ""
    echo "✅ 偏好打分完成"
else
    echo "⏭️  跳过打分步骤"
fi
echo ""

# Step 3: Generate preference-based report
echo "=========================================="
echo "Step 3: 生成偏好重排报告"
echo "=========================================="
echo ""

PREF_REPORT="reports/jobhunter/job_shortlist_data_ml_platform_with_prefs_latest.md"

python3 -m experiments.jobhunter.job_hunter_report \
    --input-file data/jobhunter/scored/jobs_scored_data_ml_platform_latest.json \
    --min-match-score 8 \
    --use-preferences \
    --output-file "$PREF_REPORT"

echo ""
echo "✅ 偏好重排报告已生成: $PREF_REPORT"
echo ""

# Step 4: Show summary
echo "=========================================="
echo "Step 4: 工作流完成总结"
echo "=========================================="
echo ""

SCORED_FILE="data/jobhunter/scored/jobs_scored_data_ml_platform_latest.json"
PREF_FILE="data/jobhunter/preferences/preferences.json"

echo "📊 数据文件路径："
echo "  - Scored 文件: $SCORED_FILE"
echo "  - 偏好文件: $PREF_FILE"
echo "  - 初始报告: $REPORT_FILE"
echo "  - 偏好重排报告: $PREF_REPORT"
echo ""

if [ -f "$PREF_FILE" ]; then
    PREF_COUNT=$(python3 -c "import json; data=json.load(open('$PREF_FILE')); print(len(data))" 2>/dev/null || echo "0")
    echo "✅ 偏好记录数: $PREF_COUNT"
else
    echo "⚠️  偏好文件不存在"
fi

echo ""
echo "=========================================="
echo "✅ 工作流完成！"
echo "=========================================="
echo ""
echo "已完成：基于 JobHunter 的偏好打分 + 重排序闭环"
echo "（模型基础分 + 用户 1-5 星评分 + 重排报告）"
echo ""
echo "可在面试中作为 'mini-RLHF on job search' 案例讲解。"
echo ""
