#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

LOG_PREFIX="[NIGHTLY_ALIGN]"
REPORTS_DIR="${REPO_ROOT}/reports"

log() {
  echo "${LOG_PREFIX} $*"
}

latest_file() {
  local pattern="$1"
  python3 - <<'PY' "$pattern"
import glob
import os
import sys

pattern = sys.argv[1]
matches = glob.glob(pattern)
if not matches:
    sys.exit(1)
latest = max(matches, key=os.path.getmtime)
print(latest)
PY
}

if [ -f "${REPO_ROOT}/.env.bandit" ]; then
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/.env.bandit"
fi

mkdir -p "${REPORTS_DIR}"

ALIGN_SAMPLE="${AB_SAMPLE:-${SAMPLE:-200}}"
ALIGN_SEED="${AB_SEED:-${SEED:-20251107}}"
ALIGN_CONCURRENCY="${CONCURRENCY:-4}"
ALIGN_WARM_CACHE="${WARM_CACHE:-100}"
ALIGN_TAG="${ALIGN_TAG:-NIGHTLY}"
DRYRUN_FLAG="${DRYRUN:-0}"

log "Warm cache bootstrap"
bash scripts/warmup.sh

log "Resetting bandit state window (reset-window=300 apply)"
python3 scripts/bandit/state_migrate.py --reset-window 300 --apply

log "Running fixed-sample AB (sample=${ALIGN_SAMPLE} seed=${ALIGN_SEED})"
SAMPLE="${ALIGN_SAMPLE}" \
AB_SAMPLE="${ALIGN_SAMPLE}" \
SEED="${ALIGN_SEED}" \
AB_SEED="${ALIGN_SEED}" \
CONCURRENCY="${ALIGN_CONCURRENCY}" \
AB_CONCURRENCY="${ALIGN_CONCURRENCY}" \
WARM_CACHE="${ALIGN_WARM_CACHE}" \
RUN_TAG="${ALIGN_TAG}" \
python3 scripts/bandit/run_ab.py --tag "${ALIGN_TAG}"

AB_CSV="$(latest_file "${REPORTS_DIR}/AB_ALIGN_*_${ALIGN_TAG}.csv")"
AB_MD="$(latest_file "${REPORTS_DIR}/AB_ALIGN_*_${ALIGN_TAG}.md")"

log "Router single-arm alignment runs"
declare -a ROUTER_REPORTS=()
for arm in fast_v1 balanced_v1 quality_v1; do
  log "Router alignment for ${arm}"
  EPS=0 \
  BATCH="${ALIGN_SAMPLE}" \
  ROUNDS=1 \
  MIN_PER_ARM=1 \
  CONCURRENCY="${ALIGN_CONCURRENCY}" \
  WARM_CACHE="${ALIGN_WARM_CACHE}" \
  SEED="${ALIGN_SEED}" \
  python3 scripts/bandit/epsilon_router.py --force-arm "${arm}" --report-prefix NIGHTLY_ALIGN_

  ROUTER_SRC="$(latest_file "${REPORTS_DIR}/NIGHTLY_ALIGN_*.md")"
  ROUTER_BASENAME="$(basename "${ROUTER_SRC}")"
  ROUTER_STAMP="${ROUTER_BASENAME#NIGHTLY_ALIGN_}"
  ROUTER_STEM="${ROUTER_STAMP%.md}"
  ROUTER_DEST="${REPORTS_DIR}/BANDIT_ROUNDS_ALIGN_${arm}_${ROUTER_STEM}_NIGHTLY.md"
  cp "${ROUTER_SRC}" "${ROUTER_DEST}"
  ROUTER_REPORTS+=("${ROUTER_DEST}")
done

log "Alignment check & conditional freeze"
ALIGN_STATUS=0
ALIGN_CMD=(
  python3 scripts/bandit/align_check.py
  --ab "${AB_CSV}"
  --router "${ROUTER_REPORTS[@]}"
  --tol-p95 0.10
  --tol-recall 0.02
  --freeze-if-aligned
  --output-prefix ALIGN_AND_FREEZE_NIGHTLY
  --sample "${ALIGN_SAMPLE}"
  --seed "${ALIGN_SEED}"
  --concurrency "${ALIGN_CONCURRENCY}"
  --warm-cache "${ALIGN_WARM_CACHE}"
)
if [ "${DRYRUN_FLAG}" != "0" ]; then
  ALIGN_CMD+=(--dryrun-freeze)
fi
set +e
"${ALIGN_CMD[@]}"
ALIGN_STATUS=$?
set -e
if [ "${ALIGN_STATUS}" -ne 0 ]; then
  log "Alignment check exited with status ${ALIGN_STATUS}"
fi

ALIGN_REPORT="$(latest_file "${REPORTS_DIR}/ALIGN_AND_FREEZE_NIGHTLY_*.md")"

log "Refreshing summary JSON"
python3 scripts/bandit/summarize.py --print-json > "${REPORTS_DIR}/BANDIT_SUMMARY_LATEST.json"
SUMMARY_JSON="${REPORTS_DIR}/BANDIT_SUMMARY_LATEST.json"

log "Artifacts ready"
echo "${LOG_PREFIX} AB_CSV=${AB_CSV}"
echo "${LOG_PREFIX} AB_MD=${AB_MD}"
for router_path in "${ROUTER_REPORTS[@]}"; do
  echo "${LOG_PREFIX} ROUTER_MD=${router_path}"
done
echo "${LOG_PREFIX} ALIGN_MD=${ALIGN_REPORT}"
echo "${LOG_PREFIX} SUMMARY_JSON=${SUMMARY_JSON}"

if [ "${ALIGN_STATUS}" -ne 0 ]; then
  log "Nightly alignment completed with DRIFT"
fi
exit "${ALIGN_STATUS}"

