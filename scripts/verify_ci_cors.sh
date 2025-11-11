#!/usr/bin/env bash
set -euo pipefail

DEV_PORT=${DEV_PORT:-18080}
PROD_PORT=${PROD_PORT:-18081}

wait_ready() {
  local port="$1"
  for i in {1..60}; do
    if curl -sf "http://127.0.0.1:${port}/health/ready" >/dev/null; then
      return 0
    fi
    sleep 1
  done
  echo "Service on port ${port} did not become ready" >&2
  return 1
}

# 开发模式：允许任意 Origin（*）
make stop-api || true
HOST=127.0.0.1 PORT=${DEV_PORT} make dev-api-bg
wait_ready "${DEV_PORT}"
curl -si -H "Origin: http://evil.com" http://127.0.0.1:${DEV_PORT}/health/live | grep -i "access-control-allow-origin: \*" >/dev/null
echo "[DEV] CORS * OK"

# 生产模式：白名单
make stop-api || true
ALLOW_ALL_CORS=0 CORS_ORIGINS=http://localhost:5173 HOST=127.0.0.1 PORT=${PROD_PORT} make dev-api-bg
wait_ready "${PROD_PORT}"
curl -si -H "Origin: http://localhost:5173" http://127.0.0.1:${PROD_PORT}/health/live | grep -i "access-control-allow-origin: http://localhost:5173" >/dev/null
if curl -si -H "Origin: http://evil.com" http://127.0.0.1:${PROD_PORT}/health/live | grep -iq "access-control-allow-origin:"; then
  echo "[PROD] Unexpected header for disallowed origin" >&2
  exit 1
fi
echo "[PROD] CORS whitelist OK"

make stop-api || true

echo "ALL GOOD"
