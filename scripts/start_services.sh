#!/usr/bin/env bash
set -euo pipefail

# Resolve directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="${SCRIPT_DIR}/.."
PID_DIR="${SCRIPT_DIR}/.pids"

mkdir -p "${PID_DIR}"

# Cleanup any previously running services to ensure idempotent startup
echo "--- Running cleanup of old services first..."
"${SCRIPT_DIR}/stop_services.sh"

# Start backend
cd "${ROOT_DIR}"
uvicorn services.fiqa_api.app_main:app --reload --port 8001 &
BACKEND_PID=$!
echo "${BACKEND_PID}" > "${PID_DIR}/backend.pid"
echo "✅ Backend service started with PID: ${BACKEND_PID}"

# Start frontend
cd "${ROOT_DIR}/frontend"
# Prefer dev script since package.json defines it
npm run dev &
FRONTEND_PID=$!
echo "${FRONTEND_PID}" > "${PID_DIR}/frontend.pid"
echo "✅ Frontend service started with PID: ${FRONTEND_PID}"

# Return to project root for consistency
cd "${ROOT_DIR}"

echo "\nServices started. PIDs stored under ${PID_DIR}."


