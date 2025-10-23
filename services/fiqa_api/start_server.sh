#!/bin/bash
# SearchForge API Server Startup Script

# Load environment variables from .env file
if [ -f "../../.env" ]; then
    echo "📄 Loading environment variables from .env file..."
    export $(grep -v '^#' ../../.env | xargs)
fi

# Fix OpenMP conflicts
export KMP_DUPLICATE_LIB_OK=TRUE

# Optional: Set LLM model and timeout (with defaults)
export CODE_LOOKUP_LLM_MODEL="${CODE_LOOKUP_LLM_MODEL:-gpt-4o-mini}"
export CODE_LOOKUP_LLM_TIMEOUT_MS="${CODE_LOOKUP_LLM_TIMEOUT_MS:-8000}"

echo "🚀 Starting SearchForge API Server..."
echo "📊 OpenMP conflicts: Fixed"
echo "🤖 LLM features: $(if [ -n "$OPENAI_API_KEY" ]; then echo "Enabled ✅"; else echo "Disabled ⚠️ (set OPENAI_API_KEY to enable)"; fi)"
echo "🌐 Server: http://localhost:8011"
echo "📋 Health: http://localhost:8011/healthz"
echo "🔍 Ready: http://localhost:8011/readyz"
echo "📝 LLM Model: $CODE_LOOKUP_LLM_MODEL"
echo "⏱️ LLM Timeout: ${CODE_LOOKUP_LLM_TIMEOUT_MS}ms"
echo ""

# Start the server
uvicorn app_main:app --host 0.0.0.0 --port 8011 --reload
