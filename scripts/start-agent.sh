#!/usr/bin/env bash
# scripts/start-agent.sh — unified launcher (kill old, pin ports, start FE/BE)
set -euo pipefail

# -------- repo root detection (works from any cwd) --------
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
REPO_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# -------- Config (env can override) --------
BACKEND_PORT="${BACKEND_PORT:-8001}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
EXTRA_KILL_PORTS="${EXTRA_KILL_PORTS:-5176,8002}"   # legacy ports to clear
BACKEND_DIR="${BACKEND_DIR:-$REPO_ROOT/services/fiqa_api}"
FRONTEND_DIR="${FRONTEND_DIR:-$REPO_ROOT/code-lookup-frontend}"
API_LOG="${API_LOG:-/tmp/fiqa_api.log}"
UI_LOG="${UI_LOG:-/tmp/fiqa_ui.log}"
FORCE_KILL="${FORCE_KILL:-1}"                        # 1=auto-kill occupied ports

# FastAPI entrypoint (run from repo root, not from services/fiqa_api directory)
BACKEND_CMD="${BACKEND_CMD:-python -m uvicorn main:app --host 0.0.0.0 --port ${BACKEND_PORT} --reload}"

# pick node runner
if command -v pnpm >/dev/null 2>&1; then NODE_RUNNER="pnpm"
elif command -v yarn >/dev/null 2>&1; then NODE_RUNNER="yarn"
else NODE_RUNNER="npm"
fi

# -------- Helpers --------
need () { command -v "$1" >/dev/null 2>&1 || { echo "Missing dependency: $1"; exit 1; }; }
need lsof; need nc

kill_on_port () {
  local p="$1"
  if lsof -ti tcp:"$p" >/dev/null 2>&1; then
    if [[ "$FORCE_KILL" == "1" ]]; then
      echo "🔪 Killing process on port $p"
      lsof -ti tcp:"$p" | xargs kill -9 || true
      sleep 0.2
    else
      echo "❌ Port $p in use. Set FORCE_KILL=1 to auto-kill." && exit 1
    fi
  fi
}

kill_legacy_ports () {
  IFS=',' read -ra arr <<<"$EXTRA_KILL_PORTS"
  for pp in "${arr[@]}"; do [[ -n "$pp" ]] && kill_on_port "$pp"; done
}

cleanup_old_processes () {
  if [[ "$FORCE_KILL" == "1" ]]; then
    echo "🧹 Cleaning up old processes..."
    # Kill old start-agent.sh instances (except current one)
    pkill -9 -f "start-agent.sh" 2>/dev/null || true
    # Kill old uvicorn processes on our port
    pkill -9 -f "uvicorn.*${BACKEND_PORT}" 2>/dev/null || true
    # Kill old vite/node processes on our port  
    pkill -9 -f "vite.*${FRONTEND_PORT}" 2>/dev/null || true
    sleep 0.5
    echo "✅ Old processes cleaned up"
  fi
}

wait_for_port () {
  local p="$1" tries=60
  while ! nc -z localhost "$p" >/dev/null 2>&1; do
    ((tries--)) || { echo "⏱️ Timeout waiting for :$p"; exit 1; }
    sleep 0.5
  done
}

start_backend () {
  echo "🚀 Starting backend on :$BACKEND_PORT ..."
  kill_on_port "$BACKEND_PORT"; kill_legacy_ports
  pushd "$BACKEND_DIR" >/dev/null
  # shellcheck disable=SC2086
  python -m uvicorn main:app --host 0.0.0.0 --port "$BACKEND_PORT" --reload >"$API_LOG" 2>&1 &
  API_PID=$!
  popd >/dev/null
  wait_for_port "$BACKEND_PORT"
  echo "✅ Backend ready: http://localhost:$BACKEND_PORT  (pid $API_PID)"
}

start_frontend () {
  echo "🎨 Starting frontend on :$FRONTEND_PORT (API=http://localhost:$BACKEND_PORT) ..."
  kill_on_port "$FRONTEND_PORT"
  pushd "$FRONTEND_DIR" >/dev/null
  export VITE_API_BASE_URL="http://localhost:$BACKEND_PORT"
  $NODE_RUNNER run dev -- --port "$FRONTEND_PORT" >"$UI_LOG" 2>&1 &
  UI_PID=$!
  popd >/dev/null
  wait_for_port "$FRONTEND_PORT"
  echo "✅ Frontend ready: http://localhost:$FRONTEND_PORT  (pid $UI_PID)"
}

cleanup () {
  echo -e "\n🧹 Stopping services..."
  kill -9 ${API_PID:-} ${UI_PID:-} >/dev/null 2>&1 || true
}
trap cleanup INT TERM EXIT

# -------- Run --------
cleanup_old_processes
start_backend
start_frontend
echo "📝 Logs: $API_LOG  |  $UI_LOG"
echo "🎯 Open: http://localhost:$FRONTEND_PORT"
wait
