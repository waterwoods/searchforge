#!/bin/bash
set -euo pipefail

# Gold Standard Workflow Script
# 薄金标工作流 - 完整执行脚本

export LOCAL=/Users/nanxinli/Documents/dev/searchforge
export REMOTE=andy-wsl
export RBASE=~/searchforge

# 数据集与金标命名
export DATASET=fiqa_50k_v1
export QRELS_GOLD=fiqa_gold_50k_v1

echo "=========================================="
echo "  Gold Standard Workflow"
echo "=========================================="
echo "LOCAL: $LOCAL"
echo "REMOTE: $REMOTE:$RBASE"
echo "DATASET: $DATASET"
echo "QRELS_GOLD: $QRELS_GOLD"
echo "=========================================="
echo ""

# 0) 同步必要脚本/配置
echo "Step 0: Syncing scripts and configs..."
rsync -avz \
  $LOCAL/tools/guards/check_no_cuda.py \
  $LOCAL/tools/guards/check_no_cuda_local.py \
  $LOCAL/tools/eval/*.py \
  $LOCAL/scripts/collect_metrics.py \
  $LOCAL/configs/presets_v10.json \
  $LOCAL/Makefile \
  $REMOTE:$RBASE/ || {
    echo "❌ Failed to sync files"
    echo "Evidence: rsync error"
    exit 1
}

echo "✅ Files synced"
echo ""

# 1) 体检（无 CUDA / 嵌入模型一致 / qrels 覆盖率 / 一致性）
echo "Step 1: Running health checks..."

echo "1.1) Checking for CUDA packages..."
ssh $REMOTE "cd $RBASE && make guard-no-cuda" || {
    echo "❌ CUDA check failed"
    echo "Evidence:"
    ssh $REMOTE "cd $RBASE && docker compose exec -T rag-api pip freeze | grep -iE '(nvidia|cuda|torch.*cuda)' || echo 'No CUDA packages in pip freeze'"
    exit 2
}
echo "✅ No CUDA packages found"
echo ""

echo "1.2) Checking embedding model configuration..."
ssh $REMOTE "cd $RBASE && make embed-doctor" || {
    echo "❌ Embedding model check failed"
    echo "Evidence:"
    ssh $REMOTE "cd $RBASE && curl -fsS http://127.0.0.1:8000/api/health/embeddings 2>&1 || curl -fsS http://localhost:8000/api/health/embeddings 2>&1"
    exit 3
}
echo "✅ Embedding model check passed"
echo ""

echo "1.3) Checking qrels coverage..."
ssh $REMOTE "cd $RBASE && make eval-qrels" || {
    echo "❌ Qrels coverage check failed"
    echo "Evidence:"
    ssh $REMOTE "cd $RBASE && cat reports/qrels_coverage_50k.json 2>&1 || echo 'Coverage report not found'"
    exit 4
}
echo "✅ Qrels coverage check passed"
echo ""

echo "1.4) Checking consistency..."
ssh $REMOTE "cd $RBASE && make eval-consistency" || {
    echo "❌ Consistency check failed"
    echo "Evidence:"
    ssh $REMOTE "cd $RBASE && cat reports/consistency.json 2>&1 || echo 'Consistency report not found'"
    exit 5
}
echo "✅ Consistency check passed"
echo ""

# 2) 生成薄金标候选
echo "Step 2: Generating gold standard candidates..."
ssh $REMOTE "cd $RBASE && python3 tools/eval/generate_gold_candidates.py \
  --dataset-name $DATASET \
  --limit 1200 \
  --out reports/gold_candidates.csv" || {
    echo "❌ Candidate generation failed"
    echo "Evidence: Check logs above"
    exit 6
}
echo "✅ Candidates generated"
echo ""

# 3) 人工标注提示
echo "=========================================="
echo "⚠️  MANUAL STEP: Label candidates"
echo "=========================================="
echo "Please label candidates in:"
echo "  $REMOTE:$RBASE/reports/gold_candidates.csv"
echo ""
echo "Set label=1 for relevant, leave empty for irrelevant"
echo ""
read -p "Press Enter after labeling is complete..."
echo ""

# 4) 产出金标
echo "Step 4: Generating gold qrels..."
ssh $REMOTE "cd $RBASE && LABELS_FILE=reports/gold_candidates.csv make gold-finalize" || {
    echo "❌ Gold qrels generation failed"
    echo "Evidence:"
    ssh $REMOTE "cd $RBASE && head -n 5 reports/gold_candidates.csv 2>&1 || echo 'CSV file not found'"
    exit 7
}
echo "✅ Gold qrels generated"
ssh $REMOTE "cd $RBASE && ls -lh reports/qrels_gold.tsv && head -n 3 reports/qrels_gold.tsv"
echo ""

# 5) 更新 presets
echo "Step 5: Updating presets with gold qrels..."
ssh $REMOTE "cd $RBASE && DATASET_NAME=$DATASET QRELS_NAME=$QRELS_GOLD make gold-update-presets" || {
    echo "❌ Preset update failed"
    echo "Evidence:"
    ssh $REMOTE "cd $RBASE && cat configs/presets_v10.json | python3 -m json.tool | head -n 60 2>&1"
    exit 8
}
echo "✅ Presets updated"
ssh $REMOTE "cd $RBASE && jq . configs/presets_v10.json | sed -n '1,60p'"
echo ""

# 6) 回归 + 汇总 + 质量门
echo "Step 6: Running baseline experiment and collecting metrics..."

echo "6.1) Submitting baseline experiment..."
ssh $REMOTE "cd $RBASE && make baseline-run" || {
    echo "❌ Baseline submission failed"
    echo "Evidence: Check API logs"
    exit 9
}
echo "✅ Baseline submitted"
echo ""

echo "6.2) Polling baseline completion..."
ssh $REMOTE "cd $RBASE && make baseline-poll" || {
    echo "❌ Baseline polling failed"
    echo "Evidence: Check job status"
    exit 10
}
echo "✅ Baseline completed"
echo ""

echo "6.3) Collecting metrics and generating winners.json..."
ssh $REMOTE "cd $RBASE && python3 scripts/collect_metrics.py && jq . reports/winners.json" || {
    echo "❌ Metrics collection failed"
    echo "Evidence:"
    ssh $REMOTE "cd $RBASE && ls -la reports/winners.json 2>&1 || echo 'winners.json not found'"
    exit 10
}
echo "✅ Metrics collected"
echo ""

echo "6.4) Running quality gate..."
ssh $REMOTE "cd $RBASE && make gold-gate || true"
echo "✅ Quality gate completed (non-blocking)"
echo ""

echo "=========================================="
echo "✅ Gold Standard Workflow Complete!"
echo "=========================================="
echo ""
echo "Output files:"
echo "  - reports/qrels_gold.tsv"
echo "  - reports/winners.json"
echo "  - configs/presets_v10.json (updated with gold presets)"
echo ""

