#!/bin/bash
# Quick smoke test - daily health check
# Generates .runs/smoke_status.json with test results

set -euo pipefail

cd "$(dirname "$0")/.."
SCRIPT_DIR="$(pwd)"
RUNS_DIR="${SCRIPT_DIR}/.runs"
STATUS_FILE="${RUNS_DIR}/smoke_status.json"
LOG_FILE="${RUNS_DIR}/smoke.log"

mkdir -p "${RUNS_DIR}"

# Get server commit
SERVER_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

# Start timing
START_TIME=$(date +%s.%N)

# Function to generate status JSON
gen_status() {
    local ok=$1
    local notes=$2
    local end_time=$(date +%s.%N)
    local latency_ms=$(python3 -c "print(int((${end_time} - ${START_TIME}) * 1000))" 2>/dev/null || echo "0")
    
    cat > "${STATUS_FILE}" <<EOF
{
  "ts": $(date +%s),
  "ok": ${ok},
  "server_commit": "${SERVER_COMMIT}",
  "latency_ms": ${latency_ms:-0},
  "notes": "${notes}"
}
EOF
}

# Capture output to log file, also show on stdout/stderr
exec 1> >(tee -a "${LOG_FILE}")
exec 2> >(tee -a "${LOG_FILE}" >&2)

# Trap to ensure status is written even on failure
trap 'gen_status false "Script interrupted"; exit 1' INT TERM
trap 'exit_code=$?; if [ $exit_code -ne 0 ]; then gen_status false "Exit code: $exit_code"; exit $exit_code; fi' EXIT

# Run diag-now
echo "[SMOKE] Running diag-now..."
if ! make diag-now; then
    gen_status false "diag-now failed"
    exit 1
fi

# Run policy-smoke
echo "[SMOKE] Running policy-smoke..."
if ! make policy-smoke; then
    gen_status false "policy-smoke failed"
    exit 1
fi

# Success
gen_status true "All checks passed"
trap - INT TERM EXIT

echo "[SMOKE] Status written to ${STATUS_FILE}"
