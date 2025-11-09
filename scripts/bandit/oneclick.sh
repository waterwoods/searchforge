#!/usr/bin/env bash
set -euo pipefail

abort() {
  echo "[ONECLICK_ABORT] $1" >&2
  exit 1
}

if [ -f .env.bandit ]; then
  # shellcheck disable=SC1091
  source .env.bandit
fi

BASE=${BASE:-http://localhost:8000}
BANDIT_STATE=${BANDIT_STATE:-$HOME/data/searchforge/bandit/bandit_state.json}
EPS=${EPS:-0.50}
BATCH=${BATCH:-240}
ROUNDS=${ROUNDS:-3}
MIN_PER_ARM=${MIN_PER_ARM:-15}
PROMOTE_P95=${PROMOTE_P95:-0.15}
PROMOTE_STREAK=${PROMOTE_STREAK:-2}
TARGET_P95=${TARGET_P95:-1000}
SLA_P95=${SLA_P95:-1500}
SLA_ERR=${SLA_ERR:-0.01}
REWARD_WEIGHTS=${REWARD_WEIGHTS:-recall=1,latency=3,err=1,cost=0}
ALPHA=${ALPHA:-0.30}
SEED=${SEED:-$(date +%s)}

export BASE BANDIT_STATE EPS BATCH ROUNDS MIN_PER_ARM PROMOTE_P95 PROMOTE_STREAK TARGET_P95 SLA_P95 SLA_ERR REWARD_WEIGHTS ALPHA SEED

echo "[ONECLICK] Step1 migrate dryrun"
python3 scripts/bandit/state_migrate.py --print-diff --dryrun || abort "state_migrate dryrun failed"

echo "[ONECLICK] Step1 migrate apply"
python3 scripts/bandit/state_migrate.py --print-diff --apply || abort "state_migrate apply failed"

echo "[ONECLICK] Step3 epsilon router"
EPS=0.50 \
BATCH=240 \
ROUNDS=3 \
MIN_PER_ARM=15 \
PROMOTE_P95=${PROMOTE_P95} \
PROMOTE_STREAK=${PROMOTE_STREAK} \
TARGET_P95=${TARGET_P95} \
SLA_P95=${SLA_P95} \
SLA_ERR=${SLA_ERR} \
WEIGHTS="${REWARD_WEIGHTS}" \
ALPHA=${ALPHA} \
BASE=${BASE} \
BANDIT_STATE=${BANDIT_STATE} \
python3 scripts/bandit/epsilon_router.py || abort "epsilon_router failed"

ROUTER_MD=$(ls -1t reports/BANDIT_ROUNDS_*.md | head -1)

echo "[ONECLICK] Step3 summarize (pre-AB)"
python3 scripts/bandit/summarize.py --print-json > reports/BANDIT_SUMMARY_LATEST.json || abort "summarize pre-AB failed"

echo "[ONECLICK] Step4 AB fixed sample"
AB_SAMPLE=200 AB_SEED=20251107 python3 scripts/bandit/run_ab.py || abort "run_ab failed"

echo "[ONECLICK] Step4 summarize (post-AB)"
python3 scripts/bandit/summarize.py --print-json > reports/BANDIT_SUMMARY_LATEST.json || abort "summarize post-AB failed"

echo "[ONECLICK] Step5 final summary"
python3 scripts/bandit/oneclick_summary.py || abort "oneclick summary failed"

MIGRATE_MD=$(ls -1t reports/BANDIT_MIGRATE_*.md | head -1)
AB_CSV=$(ls -1t reports/AB_*.csv | head -1)
AB_MD=$(ls -1t reports/AB_*.md | head -1)
FINAL_MD=$(ls -1t reports/BANDIT_ONECLICK_SUMMARY_*.md | head -1)

echo "[ONECLICK] migrate_report=${MIGRATE_MD}"
echo "[ONECLICK] router_report=${ROUTER_MD}"
echo "[ONECLICK] ab_csv=${AB_CSV}"
echo "[ONECLICK] ab_md=${AB_MD}"
echo "[ONECLICK] final_summary=${FINAL_MD}"

python3 - <<'PY'
import json
import os
from pathlib import Path

state_path = Path(os.environ.get("BANDIT_STATE"))
data = json.loads(state_path.read_text())
print("arm\tn\tavg_reward\tlast_p95\tlast_recall")
for arm in ["fast_v1", "balanced_v1", "quality_v1"]:
    entry = data.get(arm, {})
    last = entry.get("last_metrics") or {}
    print(
        f"{arm}\t{entry.get('counts')}\t{entry.get('avg_reward')}\t"
        f"{last.get('p95_ms')}\t{last.get('recall_at_10')}"
    )
PY

