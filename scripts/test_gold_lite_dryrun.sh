#!/bin/bash
set -euo pipefail

# Dry-run test for gold_lite_eval_loop.sh
# 测试脚本逻辑，不实际执行 SSH 命令

export REMOTE=andy-wsl
export RBASE=~/searchforge
export DATASET=fiqa_50k_v1
export QRELS=fiqa_qrels_50k_v1
export QRELS_GOLD=fiqa_gold_50k_v1
export API_BASE=http://127.0.0.1:8000

echo "=========================================="
echo "  Gold-Lite Evaluation Loop - DRY RUN"
echo "=========================================="
echo "Testing script logic without SSH..."
echo ""

# Test 1: Check Python scripts syntax and imports
echo "Test 1: Checking Python scripts..."
for script in \
    tools/eval/qrels_doctor.py \
    tools/eval/embed_doctor.py \
    tools/eval/consistency_check.py \
    tools/eval/generate_gold_candidates.py \
    tools/eval/gold_finalize.py \
    tools/eval/update_presets_gold.py \
    scripts/collect_metrics.py; do
    if [ -f "$script" ]; then
        echo "  ✓ $script exists"
        python3 -m py_compile "$script" 2>&1 && echo "    ✓ Syntax OK" || echo "    ✗ Syntax error"
    else
        echo "  ✗ $script NOT FOUND"
    fi
done
echo ""

# Test 2: Check argument parsing
echo "Test 2: Testing argument parsing..."
echo "  Testing qrels_doctor.py --help"
python3 tools/eval/qrels_doctor.py --help 2>&1 | head -5 || echo "    ✗ Help failed"
echo ""

echo "  Testing embed_doctor.py --help"
python3 tools/eval/embed_doctor.py --help 2>&1 | head -5 || echo "    ✗ Help failed"
echo ""

# Test 3: Check path resolution logic
echo "Test 3: Testing path resolution..."
python3 <<'PY'
import sys
from pathlib import Path

# Test qrels path resolution
dataset = "fiqa_50k_v1"
dataset_short = dataset.replace("_v1", "").replace("fiqa_", "")
paths_to_try = [
    f"experiments/data/fiqa/fiqa_qrels_{dataset_short}_v1.tsv",
    f"experiments/data/fiqa/{dataset}_qrels.tsv",
    f"data/fiqa/fiqa_qrels_{dataset_short}_v1.tsv"
]

print(f"  Looking for qrels for dataset: {dataset}")
for path in paths_to_try:
    exists = Path(path).exists()
    print(f"    {path}: {'✓' if exists else '✗'}")
    if exists:
        print(f"      Found! Using: {path}")
        break
else:
    print(f"    ✗ No qrels file found in any expected location")
PY
echo ""

# Test 4: Check presets file
echo "Test 4: Checking presets file..."
if [ -f "configs/presets_v10.json" ]; then
    echo "  ✓ configs/presets_v10.json exists"
    python3 <<'PY'
import json
from pathlib import Path

presets_path = Path("configs/presets_v10.json")
with open(presets_path, 'r') as f:
    presets = json.load(f)
    
print(f"    Found {len(presets.get('presets', []))} presets")
for preset in presets.get("presets", [])[:3]:
    print(f"      - {preset.get('name', 'unknown')}: dataset={preset.get('dataset_name', 'N/A')}, collection={preset.get('collection', 'N/A')}")
PY
else
    echo "  ✗ configs/presets_v10.json NOT FOUND"
fi
echo ""

# Test 5: Check required tools
echo "Test 5: Checking required tools..."
for tool in python3 curl jq; do
    if command -v $tool >/dev/null 2>&1; then
        echo "  ✓ $tool available"
    else
        echo "  ✗ $tool NOT FOUND"
    fi
done
echo ""

# Test 6: Validate script structure
echo "Test 6: Validating script structure..."
if [ -f "scripts/gold_lite_eval_loop.sh" ]; then
    echo "  ✓ gold_lite_eval_loop.sh exists"
    
    # Check for required functions
    if grep -q "print_evidence" scripts/gold_lite_eval_loop.sh; then
        echo "    ✓ print_evidence function found"
    else
        echo "    ✗ print_evidence function NOT FOUND"
    fi
    
    # Check for all phases
    for phase in "Phase 0" "Phase 1" "Phase 2" "Phase 3" "Phase 4" "Phase 5"; do
        if grep -q "$phase" scripts/gold_lite_eval_loop.sh; then
            echo "    ✓ $phase found"
        else
            echo "    ✗ $phase NOT FOUND"
        fi
    done
else
    echo "  ✗ gold_lite_eval_loop.sh NOT FOUND"
fi
echo ""

# Test 7: Check for common issues
echo "Test 7: Checking for common issues..."
echo "  Checking for hardcoded paths..."
if grep -q "/app/" scripts/gold_lite_eval_loop.sh; then
    echo "    ⚠ Found hardcoded /app/ paths (may need adjustment)"
else
    echo "    ✓ No hardcoded /app/ paths found"
fi

echo "  Checking for missing error handling..."
if grep -q "set -euo pipefail" scripts/gold_lite_eval_loop.sh; then
    echo "    ✓ Error handling enabled (set -euo pipefail)"
else
    echo "    ✗ Error handling may be missing"
fi
echo ""

echo "=========================================="
echo "  Dry-run test complete"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Fix any errors found above"
echo "  2. Test with actual SSH connection (if available)"
echo "  3. Run full workflow: bash scripts/gold_lite_eval_loop.sh"
echo ""

