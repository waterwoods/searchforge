#!/usr/bin/env bash
# verify_agent_v3.sh - Agent V3 健康检查（10行汇总）
set -euo pipefail

API=${API:-http://127.0.0.1:8011}

# 1) 健康检查
curl -fsS "$API/readyz" >/dev/null || { echo "❌ Backend not ready"; exit 1; }

# 2) V3 Summary（必须含 ok, bullets, explainer_mode）
curl -fsS "$API/api/agent/summary?v=3" | jq -e '.ok!=null and .bullets!=null and .explainer_mode!=null' >/dev/null || { echo "❌ V3 summary invalid"; exit 1; }

# 3) V3 Run dry（必须含 verdict, mode="dry"）
curl -fsS -X POST "$API/api/agent/run?v=3&dry=true" | jq -e '.verdict!=null and .mode=="dry"' >/dev/null || { echo "❌ V3 run invalid"; exit 1; }

echo "✅ Agent V3 OK"
