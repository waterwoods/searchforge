#!/usr/bin/env bash
set -euo pipefail

# Resolve directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="${SCRIPT_DIR}/.pids"

BACKEND_PID_FILE="${PID_DIR}/backend.pid"
FRONTEND_PID_FILE="${PID_DIR}/frontend.pid"

stop_by_pid_file() {
    local name="$1"
    local file="$2"

    if [[ -f "${file}" ]]; then
        local pid
        pid=$(cat "${file}" || true)
        if [[ -n "${pid}" ]]; then
            if kill -0 "${pid}" >/dev/null 2>&1; then
                kill "${pid}" || true
                echo "⏹️ ${name} service with PID: ${pid} stopped."
            else
                echo "ℹ️ ${name} service PID ${pid} not running."
            fi
        else
            echo "⚠️ ${name} PID file exists but is empty: ${file}"
        fi
        rm -f "${file}"
    else
        echo "ℹ️ No PID file found for ${name}: ${file}"
    fi
}

stop_by_pid_file "Backend"  "${BACKEND_PID_FILE}"
stop_by_pid_file "Frontend" "${FRONTEND_PID_FILE}"

echo "Cleanup complete."


