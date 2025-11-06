#!/usr/bin/env bash

set -euo pipefail

export MAIN_PORT="${MAIN_PORT:-8011}"
export WORKERS="${WORKERS:-1}"
export QUERY_TIMEOUT_S="${QUERY_TIMEOUT_S:-15}"

# 强制单进程，避免 JobManager 在多 worker 下的跨进程状态不一致
if [ "${WORKERS}" -ne 1 ]; then
  echo "[raglab] Forcing WORKERS=1 to avoid cross-process queue/state issues."
  WORKERS=1
fi

PIDFILE="/tmp/fiqa_api.pid"
LOGFILE="/tmp/fiqa_api.log"
PORT="$MAIN_PORT"

stop_old() {
  # 1) by pidfile
  if [[ -f "$PIDFILE" ]] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    kill -TERM "$(cat "$PIDFILE")" 2>/dev/null || true
    for i in {1..20}; do kill -0 "$(cat "$PIDFILE")" 2>/dev/null || break; sleep 0.5; done
    kill -KILL "$(cat "$PIDFILE")" 2>/dev/null || true
    rm -f "$PIDFILE"
  fi
  # 2) by port
  PIDS="$(lsof -t -i :"$PORT" -sTCP:LISTEN || true)"
  [[ -n "$PIDS" ]] && kill -TERM $PIDS 2>/dev/null || true
  for i in {1..10}; do [[ -z "$(lsof -t -i :"$PORT" -sTCP:LISTEN || true)" ]] && break; sleep 0.5; done
  PIDS="$(lsof -t -i :"$PORT" -sTCP:LISTEN || true)"
  [[ -n "$PIDS" ]] && kill -KILL $PIDS 2>/dev/null || true
  # 3) by cmdline
  pkill -TERM -f "uvicorn .*services\.fiqa_api\.app_main:app" 2>/dev/null || true
}

start_new() {
  echo "→ Starting backend on ${PORT} with ${WORKERS} workers"
  echo "  logs: ${LOGFILE}"
  nohup python -m uvicorn services.fiqa_api.app_main:app \
    --host 0.0.0.0 --port "$PORT" --workers "$WORKERS" \
    >"$LOGFILE" 2>&1 &
  echo $! > "$PIDFILE"
  echo "⏳ Waiting for health..."
  # 尝试 40 次，每次 0.5s，connect-timeout 0.5s，总体 ~20s
  for i in {1..40}; do
    if curl -s --connect-timeout 0.5 --max-time 1.5 "http://localhost:${PORT}/api/health/qdrant" | jq -e '.http_ok and .grpc_ok' >/dev/null 2>&1; then
      echo "✅ Healthy on attempt $i"
      return 0
    fi
    sleep 0.5
  done
  echo "❌ Health check failed (see $LOGFILE)"; exit 1
}

case "${1:-restart}" in
  stop)    stop_old ;;
  start)   stop_old; start_new ;;
  restart) stop_old; start_new ;;
  *) echo "Usage: $0 {start|stop|restart}"; exit 2 ;;
esac
