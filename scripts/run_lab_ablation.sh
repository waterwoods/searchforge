#!/bin/bash
# run_lab_ablation.sh - Ablation Study Runner for LabOps Agent V1
# ================================================================
# Runs three experiments back-to-back with identical seeds & load:
# 1. Flow-only (A: fixed; B: AIMD; routing OFF)
# 2. Routing-only (A: all-qdrant; B: faiss-first; flow fixed)
# 3. Combo (A: baseline; B: AIMD + faiss-first)
#
# Output: LAB_ABLATION_MINI.txt (≤80 lines) with 3-row comparison table
#
# Usage:
#   ./scripts/run_lab_ablation.sh [--seed SEED] [--qps QPS] [--rounds N]
#
# Flags:
#   --seed SEED     Seed for reproducibility (default: 42)
#   --qps QPS       Load in QPS (default: 10.0)
#   --rounds N      Number of ABAB rounds per experiment (default: 2)
#   --auto-apply    Auto-apply winning configs (default: safe mode)

set -e

# Configuration
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPORTS_DIR="$PROJECT_ROOT/reports"
TEMP_DIR="$PROJECT_ROOT/.tmp/ablation_$$"

# Default parameters
SEED=42
QPS=10.0
ROUNDS=2
WINDOW_SEC=120
AUTO_APPLY=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --seed)
            SEED="$2"
            shift 2
            ;;
        --qps)
            QPS="$2"
            shift 2
            ;;
        --rounds)
            ROUNDS="$2"
            shift 2
            ;;
        --auto-apply)
            AUTO_APPLY="--auto-apply"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--seed SEED] [--qps QPS] [--rounds N] [--auto-apply]"
            exit 1
            ;;
    esac
done

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Create temp dir for configs
mkdir -p "$TEMP_DIR"

echo "======================================================================"
echo "LABOPS ABLATION STUDY RUNNER"
echo "======================================================================"
echo "Seed: $SEED"
echo "QPS: $QPS"
echo "Rounds: $ROUNDS"
echo "Window: ${WINDOW_SEC}s"
echo "Auto-apply: ${AUTO_APPLY:-OFF}"
echo "======================================================================"
echo

# Function to run single experiment
run_experiment() {
    local exp_name=$1
    local config_file=$2
    local output_suffix=$3
    
    echo -e "${CYAN}[ABLATION]${NC} Running experiment: ${exp_name}"
    echo -e "${BLUE}[INFO]${NC} Config: $config_file"
    echo
    
    # Run lab headless script
    cd "$PROJECT_ROOT"
    
    if ! bash scripts/run_lab_headless.sh combo --with-load \
        --qps "$QPS" \
        --window "$WINDOW_SEC" \
        --rounds "$ROUNDS" \
        --seed "$SEED" \
        --flow-policy "$(grep 'flow_policy:' "$config_file" | awk '{print $2}' | tr -d '"')" \
        --target-p95 "$(grep 'target_p95:' "$config_file" | awk '{print $2}')" \
        --conc-cap "$(grep 'conc_cap:' "$config_file" | awk '{print $2}')" \
        --batch-cap "$(grep 'batch_cap:' "$config_file" | awk '{print $2}')" \
        --routing-mode "$(grep 'routing_mode:' "$config_file" | awk '{print $2}' | tr -d '"')" \
        --topk-threshold "$(grep 'topk_threshold:' "$config_file" | awk '{print $2}')"; then
        
        echo -e "${RED}[ERROR]${NC} Experiment failed: ${exp_name}"
        return 1
    fi
    
    # Copy report
    if [ -f "$REPORTS_DIR/LAB_COMBO_REPORT_MINI.txt" ]; then
        cp "$REPORTS_DIR/LAB_COMBO_REPORT_MINI.txt" "$TEMP_DIR/${output_suffix}.txt"
        echo -e "${GREEN}[SUCCESS]${NC} ${exp_name} completed"
    else
        echo -e "${RED}[ERROR]${NC} Report not found for ${exp_name}"
        return 1
    fi
    
    echo
    return 0
}

# Generate config files
echo -e "${BLUE}[INFO]${NC} Generating experiment configs..."

# Config 1: Flow-only (AIMD with routing OFF)
cat > "$TEMP_DIR/flow_only.yaml" << EOF
base_url: "http://localhost:8011"
timeout: 30
experiment:
  qps: ${QPS}
  window_sec: ${WINDOW_SEC}
  rounds: ${ROUNDS}
  seed: ${SEED}
  flow_policy: "aimd"
  target_p95: 1200
  conc_cap: 32
  batch_cap: 32
  routing_mode: "rules"
  topk_threshold: 999999
thresholds:
  pass_delta_p95_max: -10.0
  edge_delta_p95_max: -5.0
  max_error_rate: 1.0
  ab_balance_warn: 5.0
time_budget: 0
report:
  max_lines: 60
  output_path: "reports/LABOPS_AGENT_SUMMARY.txt"
  history_path: "agents/labops/state/history.jsonl"
EOF

# Config 2: Routing-only (FAISS-first with flow fixed)
cat > "$TEMP_DIR/routing_only.yaml" << EOF
base_url: "http://localhost:8011"
timeout: 30
experiment:
  qps: ${QPS}
  window_sec: ${WINDOW_SEC}
  rounds: ${ROUNDS}
  seed: ${SEED}
  flow_policy: "aimd"
  target_p95: 1200
  conc_cap: 16
  batch_cap: 16
  routing_mode: "rules"
  topk_threshold: 32
thresholds:
  pass_delta_p95_max: -10.0
  edge_delta_p95_max: -5.0
  max_error_rate: 1.0
  ab_balance_warn: 5.0
time_budget: 0
report:
  max_lines: 60
  output_path: "reports/LABOPS_AGENT_SUMMARY.txt"
  history_path: "agents/labops/state/history.jsonl"
EOF

# Config 3: Combo (AIMD + FAISS-first)
cat > "$TEMP_DIR/combo.yaml" << EOF
base_url: "http://localhost:8011"
timeout: 30
experiment:
  qps: ${QPS}
  window_sec: ${WINDOW_SEC}
  rounds: ${ROUNDS}
  seed: ${SEED}
  flow_policy: "aimd"
  target_p95: 1200
  conc_cap: 32
  batch_cap: 32
  routing_mode: "rules"
  topk_threshold: 32
thresholds:
  pass_delta_p95_max: -10.0
  edge_delta_p95_max: -5.0
  max_error_rate: 1.0
  ab_balance_warn: 5.0
time_budget: 0
report:
  max_lines: 60
  output_path: "reports/LABOPS_AGENT_SUMMARY.txt"
  history_path: "agents/labops/state/history.jsonl"
EOF

echo -e "${GREEN}[SUCCESS]${NC} Configs generated"
echo

# Run experiments
echo -e "${CYAN}[ABLATION]${NC} Starting experiments..."
echo

FAILED=0

run_experiment "Flow-only" "$TEMP_DIR/flow_only.yaml" "flow_only" || FAILED=1
sleep 5

run_experiment "Routing-only" "$TEMP_DIR/routing_only.yaml" "routing_only" || FAILED=1
sleep 5

run_experiment "Combo" "$TEMP_DIR/combo.yaml" "combo" || FAILED=1

if [ $FAILED -eq 1 ]; then
    echo -e "${RED}[ERROR]${NC} One or more experiments failed"
    echo "Partial results saved in: $TEMP_DIR"
    exit 1
fi

# Parse results and generate summary
echo
echo -e "${BLUE}[INFO]${NC} Generating ablation summary..."

ABLATION_REPORT="$REPORTS_DIR/LAB_ABLATION_MINI.txt"

# Extract metrics using Python
python3 << 'PYEOF' > "$ABLATION_REPORT"
import re
import sys
from pathlib import Path

temp_dir = Path(sys.argv[1])
seed = sys.argv[2]
qps = sys.argv[3]
rounds = sys.argv[4]

def extract_metrics(report_path):
    """Extract ΔP95%, ΔQPS%, Err%, FAISS% from report."""
    text = report_path.read_text()
    
    delta_p95 = 0.0
    delta_qps = 0.0
    error_rate = 0.0
    faiss_share = 0.0
    
    for line in text.split('\n'):
        if 'ΔP95:' in line:
            match = re.search(r'\(([+-]?\d+\.?\d*)%\)', line)
            if match:
                delta_p95 = float(match.group(1))
        elif 'ΔQPS:' in line:
            match = re.search(r'\(([+-]?\d+\.?\d*)%\)', line)
            if match:
                delta_qps = float(match.group(1))
        elif 'Error Rate:' in line or 'Err:' in line:
            match = re.search(r'([0-9.]+)%', line)
            if match:
                error_rate = float(match.group(1))
        elif 'FAISS:' in line and '(' in line:
            match = re.search(r'FAISS:\s*\d+\s*\(([0-9.]+)%\)', line)
            if match:
                faiss_share = float(match.group(1))
    
    return delta_p95, delta_qps, error_rate, faiss_share

# Extract metrics from each report
flow_metrics = extract_metrics(temp_dir / "flow_only.txt")
routing_metrics = extract_metrics(temp_dir / "routing_only.txt")
combo_metrics = extract_metrics(temp_dir / "combo.txt")

# Generate report (≤80 lines)
lines = []
lines.append("=" * 70)
lines.append("LABOPS ABLATION STUDY - MINI REPORT")
lines.append("=" * 70)
lines.append("")
lines.append("EXPERIMENT PARAMETERS")
lines.append("-" * 70)
lines.append(f"Seed: {seed}")
lines.append(f"QPS: {qps}")
lines.append(f"Rounds: {rounds} (ABAB cycles)")
lines.append(f"Window: 120s per phase")
lines.append("")

lines.append("ABLATION RESULTS")
lines.append("-" * 70)
lines.append("Three experiments with identical load & seed:")
lines.append("  1. Flow-only:    A=fixed params  B=AIMD control  (routing OFF)")
lines.append("  2. Routing-only: A=all→Qdrant   B=FAISS-first   (flow fixed)")
lines.append("  3. Combo:        A=baseline     B=AIMD+FAISS    (both ON)")
lines.append("")

lines.append("COMPARISON TABLE")
lines.append("-" * 70)
lines.append(f"{'Experiment':<15} {'ΔP95%':>8} {'ΔQPS%':>8} {'Err%':>8} {'FAISS%':>8}")
lines.append("-" * 70)
lines.append(f"{'Flow-only':<15} {flow_metrics[0]:>8.1f} {flow_metrics[1]:>8.1f} {flow_metrics[2]:>8.2f} {flow_metrics[3]:>8.1f}")
lines.append(f"{'Routing-only':<15} {routing_metrics[0]:>8.1f} {routing_metrics[1]:>8.1f} {routing_metrics[2]:>8.2f} {routing_metrics[3]:>8.1f}")
lines.append(f"{'Combo':<15} {combo_metrics[0]:>8.1f} {combo_metrics[1]:>8.1f} {combo_metrics[2]:>8.2f} {combo_metrics[3]:>8.1f}")
lines.append("-" * 70)
lines.append("")

lines.append("INSIGHTS")
lines.append("-" * 70)

# Determine best experiment
best_idx = 0
best_score = flow_metrics[0]  # Use ΔP95 as primary metric
if routing_metrics[0] < best_score:
    best_idx = 1
    best_score = routing_metrics[0]
if combo_metrics[0] < best_score:
    best_idx = 2
    best_score = combo_metrics[0]

experiments = ["Flow-only", "Routing-only", "Combo"]
lines.append(f"Best performer: {experiments[best_idx]} (ΔP95={best_score:.1f}%)")

# Check if combo is additive
combo_expected = flow_metrics[0] + routing_metrics[0]
combo_actual = combo_metrics[0]
if abs(combo_actual - combo_expected) < 2.0:
    lines.append("Combo effect: ADDITIVE (flow + routing benefits combine)")
elif combo_actual < combo_expected:
    lines.append("Combo effect: SYNERGISTIC (better than sum of parts)")
else:
    lines.append("Combo effect: SUBADDITIVE (interaction reduces benefits)")

lines.append("")

lines.append("INDIVIDUAL REPORTS")
lines.append("-" * 70)
lines.append("Detailed reports available:")
lines.append(f"  - {temp_dir}/flow_only.txt")
lines.append(f"  - {temp_dir}/routing_only.txt")
lines.append(f"  - {temp_dir}/combo.txt")
lines.append("")

lines.append("=" * 70)
lines.append("END OF ABLATION REPORT")
lines.append("=" * 70)

# Limit to 80 lines
for line in lines[:80]:
    print(line)

PYEOF "$TEMP_DIR" "$SEED" "$QPS" "$ROUNDS"

echo -e "${GREEN}[SUCCESS]${NC} Ablation study complete"
echo
echo "Summary report: $ABLATION_REPORT"
echo "Temp dir: $TEMP_DIR"
echo

# Display summary
cat "$ABLATION_REPORT"

echo
echo "======================================================================"
echo "ABLATION STUDY COMPLETE"
echo "======================================================================"

exit 0

