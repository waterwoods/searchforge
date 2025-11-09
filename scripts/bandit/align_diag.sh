#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

latest_file() {
  local pattern="$1"
  python3 - <<'PY' "${pattern}"
import glob
import os
import sys

pattern = sys.argv[1]
matches = glob.glob(pattern)
if not matches:
    sys.exit(1)
latest = max(matches, key=os.path.getmtime)
print(os.path.abspath(latest))
PY
}

source .env.bandit 2>/dev/null || true

export BASE="${BASE:-http://localhost:8000}"
export REPORTS_DIR="reports"
export RUNS_DIR="${RUNS_DIR:-.runs}"
export ALIGN_SEED="${ALIGN_SEED:-20251107}"
export ALIGN_TAG="${ALIGN_TAG:-ALIGN_DIAG}"

mkdir -p "${REPORTS_DIR}" "${RUNS_DIR}"

echo "[STEP0] BASE=${BASE}  SEED=${ALIGN_SEED}  TAG=${ALIGN_TAG}"

echo "[STEP1] Warmup"
bash scripts/warmup.sh

echo "[STEP2] Reset bandit window (reset-window=0) and capture pre-align summary"
python3 scripts/bandit/state_migrate.py --reset-window 0 --apply
python3 scripts/bandit/summarize.py --print-json > "${REPORTS_DIR}/BANDIT_SUMMARY_PRE_ALIGN.json"

declare -a C1_ROUTER_REPORTS=()
declare -a C4_ROUTER_REPORTS=()

echo "[STEP3] Diagnostic pass (concurrency=1)"
export SAMPLE=200 CONCURRENCY=1 WARM_CACHE=100
python3 scripts/bandit/run_ab.py --tag "${ALIGN_TAG}-C1"
AB_C1_CSV="$(latest_file "${REPORTS_DIR}/AB_ALIGN_*_${ALIGN_TAG}-C1.csv")"

for arm in fast_v1 balanced_v1 quality_v1; do
  echo "[STEP3][ROUTER] arm=${arm}"
  EPS=0 \
  BATCH="${SAMPLE}" \
  ROUNDS=1 \
  MIN_PER_ARM=1 \
  CONCURRENCY="${CONCURRENCY}" \
  WARM_CACHE="${WARM_CACHE}" \
  SEED="${ALIGN_SEED}" \
  python3 scripts/bandit/epsilon_router.py --force-arm "${arm}" --report-prefix "ALIGN_C1_"
  ROUTER_SRC="$(latest_file "${REPORTS_DIR}/ALIGN_C1_*.md")"
  ROUTER_TS="${ROUTER_SRC##*ALIGN_C1_}"
  ROUTER_TS="${ROUTER_TS%.md}"
  ROUTER_DEST="${REPORTS_DIR}/BANDIT_ROUNDS_ALIGN_${arm}_C1_${ROUTER_TS}.md"
  cp "${ROUTER_SRC}" "${ROUTER_DEST}"
  C1_ROUTER_REPORTS+=("${ROUTER_DEST}")
done

echo "[STEP3] Alignment audit (p95±5%, recall±0.01)"
C1_STATUS=0
set +e
python3 scripts/bandit/align_check.py \
  --ab "${AB_C1_CSV}" \
  --router "${C1_ROUTER_REPORTS[@]}" \
  --tol-p95 0.05 --tol-recall 0.01 \
  --output-prefix ALIGN_AND_FREEZE_C1 \
  --sample "${SAMPLE}" \
  --seed "${ALIGN_SEED}" \
  --concurrency "${CONCURRENCY}" \
  --warm-cache "${WARM_CACHE}"
C1_STATUS=$?
set -e
if [[ "${C1_STATUS}" -ne 0 ]]; then
  echo "[WARN] C1 alignment exited with status ${C1_STATUS}"
fi
if ALIGN_C1_REPORT="$(latest_file "${REPORTS_DIR}/ALIGN_AND_FREEZE_C1_*.md")"; then
  :
else
  ALIGN_C1_REPORT=""
fi

echo "[STEP4] Production pass (concurrency=4)"
export SAMPLE=200 CONCURRENCY=4 WARM_CACHE=100
python3 scripts/bandit/run_ab.py --tag "${ALIGN_TAG}-C4"
AB_C4_CSV="$(latest_file "${REPORTS_DIR}/AB_ALIGN_*_${ALIGN_TAG}-C4.csv")"

for arm in fast_v1 balanced_v1 quality_v1; do
  echo "[STEP4][ROUTER] arm=${arm}"
  EPS=0 \
  BATCH="${SAMPLE}" \
  ROUNDS=1 \
  MIN_PER_ARM=1 \
  CONCURRENCY="${CONCURRENCY}" \
  WARM_CACHE="${WARM_CACHE}" \
  SEED="${ALIGN_SEED}" \
  python3 scripts/bandit/epsilon_router.py --force-arm "${arm}" --report-prefix "ALIGN_C4_"
  ROUTER_SRC="$(latest_file "${REPORTS_DIR}/ALIGN_C4_*.md")"
  ROUTER_TS="${ROUTER_SRC##*ALIGN_C4_}"
  ROUTER_TS="${ROUTER_TS%.md}"
  ROUTER_DEST="${REPORTS_DIR}/BANDIT_ROUNDS_ALIGN_${arm}_C4_${ROUTER_TS}.md"
  cp "${ROUTER_SRC}" "${ROUTER_DEST}"
  C4_ROUTER_REPORTS+=("${ROUTER_DEST}")
done

echo "[STEP4] Alignment audit (p95±10%, recall±0.02)"
C4_STATUS=0
set +e
python3 scripts/bandit/align_check.py \
  --ab "${AB_C4_CSV}" \
  --router "${C4_ROUTER_REPORTS[@]}" \
  --tol-p95 0.10 --tol-recall 0.02 \
  --output-prefix ALIGN_AND_FREEZE_C4 \
  --freeze-if-aligned \
  --sample "${SAMPLE}" \
  --seed "${ALIGN_SEED}" \
  --concurrency "${CONCURRENCY}" \
  --warm-cache "${WARM_CACHE}"
C4_STATUS=$?
set -e
if [[ "${C4_STATUS}" -ne 0 ]]; then
  echo "[WARN] C4 alignment exited with status ${C4_STATUS}"
fi
if ALIGN_C4_REPORT="$(latest_file "${REPORTS_DIR}/ALIGN_AND_FREEZE_C4_*.md")"; then
  :
else
  ALIGN_C4_REPORT=""
fi

echo "[STEP5] Refresh summary"
python3 scripts/bandit/summarize.py --print-json > "${REPORTS_DIR}/BANDIT_SUMMARY_LATEST.json"

echo "[DONE] 关键产物："
ls -1 "${REPORTS_DIR}"/ALIGN_AND_FREEZE_C1*.md 2>/dev/null | head -n1 || true
ls -1 "${REPORTS_DIR}"/ALIGN_AND_FREEZE_C4*.md 2>/dev/null | head -n1 || true
ls -1 "${REPORTS_DIR}/BANDIT_SUMMARY_LATEST.json" 2>/dev/null | head -n1 || true

echo "[CHECK] 当前策略："
curl -fsS "${BASE}/api/admin/policy/current" | python3 -m json.tool
echo "[CHECK] 响应头："
curl -s -D /tmp/hdr.txt -H 'content-type: application/json' \
  -X POST "${BASE}/api/query" \
  -d '{"question":"ping","top_k":10,"mmr":true,"mmr_lambda":0.3,"collection":"fiqa_para_50k"}' >/dev/null
grep -Ei 'x-mmr|x-mmr-lambda|x-collection' /tmp/hdr.txt || true

EXIT_CODE="${C4_STATUS}"
if [[ "${EXIT_CODE}" -eq 0 ]]; then
  echo "[RESULT] Alignment (C4) succeeded."
else
  echo "[RESULT] Alignment (C4) drift detected (exit=${EXIT_CODE})."
fi
exit "${EXIT_CODE}"

