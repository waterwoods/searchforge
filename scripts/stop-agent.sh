#!/usr/bin/env bash
# scripts/stop-agent.sh — stop all services (backend + frontend)
set -euo pipefail

# -------- repo root detection (works from any cwd) --------
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
REPO_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# -------- Config (env can override) --------
BACKEND_PORT="${BACKEND_PORT:-8001}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
EXTRA_KILL_PORTS="${EXTRA_KILL_PORTS:-5176,8002}"   # legacy ports to clear
FORCE_KILL="${FORCE_KILL:-1}"                        # 1=auto-kill occupied ports

# -------- Helpers --------
need () { command -v "$1" >/dev/null 2>&1 || { echo "Missing dependency: $1"; exit 1; }; }
need lsof

kill_on_port () {
  local p="$1"
  if lsof -ti tcp:"$p" >/dev/null 2>&1; then
    echo "🔪 Killing process on port $p"
    lsof -ti tcp:"$p" | xargs kill -9 || true
    sleep 0.2
  else
    echo "✅ Port $p is already free"
  fi
}

kill_legacy_ports () {
  IFS=',' read -ra arr <<<"$EXTRA_KILL_PORTS"
  for pp in "${arr[@]}"; do [[ -n "$pp" ]] && kill_on_port "$pp"; done
}

# -------- Main --------
echo "🛑 Stopping all services..."

# Kill backend
echo "🔪 Stopping backend on port $BACKEND_PORT..."
kill_on_port "$BACKEND_PORT"

# Kill frontend  
echo "🔪 Stopping frontend on port $FRONTEND_PORT..."
kill_on_port "$FRONTEND_PORT"

# Kill legacy ports
echo "🔪 Cleaning up legacy ports..."
kill_legacy_ports

echo "✅ All services stopped!"
echo "📝 Logs are still available at: /tmp/fiqa_api.log and /tmp/fiqa_ui.log"
