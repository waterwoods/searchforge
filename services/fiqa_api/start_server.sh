#!/usr/bin/env bash
set -euo pipefail

# Navigate to project root
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" || { echo "❌ 错误: 无法切换到项目根目录"; exit 1; }

# Load environment variables from .env file
if [ -f ".env" ]; then
    echo "📄 Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
fi

# Fix OpenMP conflicts
export KMP_DUPLICATE_LIB_OK=TRUE

# Workers configuration (default: 2)
export WORKERS="${WORKERS:-2}"

# Query timeout configuration (default: 20 seconds)
export QUERY_TIMEOUT_S="${QUERY_TIMEOUT_S:-20}"

# Uvicorn workers (default: 4 for multi-process)
export UVICORN_WORKERS="${UVICORN_WORKERS:-4}"

# Optional: Set LLM model and timeout (with defaults)
export CODE_LOOKUP_LLM_MODEL="${CODE_LOOKUP_LLM_MODEL:-gpt-4o-mini}"
export CODE_LOOKUP_LLM_TIMEOUT_MS="${CODE_LOOKUP_LLM_TIMEOUT_MS:-8000}"

# MAIN_PORT configuration (default: 8011)
MAIN_PORT="${MAIN_PORT:-8011}"

echo "[boot] MAIN_PORT=${MAIN_PORT}"

# Kill any existing uvicorn processes for this service (optional cleanup)
pkill -f "uvicorn services.fiqa_api" >/dev/null 2>&1 || true

echo "🚀 Starting SearchForge API Server..."
echo "📁 工作目录: $(pwd)"
echo "📊 OpenMP conflicts: Fixed"
echo "🤖 LLM features: $(if [ -n "$OPENAI_API_KEY" ]; then echo "Enabled ✅"; else echo "Disabled ⚠️ (set OPENAI_API_KEY to enable)"; fi)"
echo "🌐 Server: http://localhost:${MAIN_PORT}"
echo "📋 Health: http://localhost:${MAIN_PORT}/healthz"
echo "🔍 Ready: http://localhost:${MAIN_PORT}/readyz"
echo "📝 LLM Model: $CODE_LOOKUP_LLM_MODEL"
echo "⏱️ LLM Timeout: ${CODE_LOOKUP_LLM_TIMEOUT_MS}ms"
echo "🔧 Workers: ${WORKERS}"
echo "⏱️ Query Timeout: ${QUERY_TIMEOUT_S}s"
echo ""

# Start the server with multiple workers
exec python -m uvicorn services.fiqa_api.app_main:app \
  --host 0.0.0.0 --port "${MAIN_PORT}" --workers "${WORKERS}"
