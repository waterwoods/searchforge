#!/bin/bash

###############################################################################
# Start SearchForge Demo App on Port 8001
# 
# This script starts the app_v2.py server specifically for:
# - Black Swan Demo
# - Auto-RCA Kit testing
# - Live Tap Mode
# 
# Default port: 8001 (as required by Black Swan Demo)
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Get the project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# Load environment variables from .env file
if [ -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${BLUE}📝 Loading configuration from .env${NC}"
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
    echo ""
fi

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     SearchForge Demo App - Starting on Port 8001              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Configuration (from .env or defaults)
PORT="${PORT:-8001}"
QDRANT_PORT=$(echo "${QDRANT_URL:-http://localhost:6333}" | sed -n 's/.*:\([0-9]*\).*/\1/p')
QDRANT_PORT="${QDRANT_PORT:-6333}"
WORKERS="${WORKERS:-1}"

echo -e "${YELLOW}📍 Project root: ${PROJECT_ROOT}${NC}"
echo -e "${YELLOW}🌐 Port: ${PORT}${NC}"
echo ""

# Check if port is already in use
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Port $PORT is already in use${NC}"
    echo -e "${YELLOW}Attempting to kill existing process...${NC}"
    lsof -tiTCP:$PORT -sTCP:LISTEN | xargs -I{} kill -9 {} 2>/dev/null || true
    sleep 2
fi

# Check if Qdrant is running
echo -e "${BLUE}🔍 Checking Qdrant status...${NC}"
if curl -s http://localhost:$QDRANT_PORT/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Qdrant is running on port $QDRANT_PORT${NC}"
else
    echo -e "${YELLOW}⚠️  Qdrant not detected on port $QDRANT_PORT${NC}"
    
    # Try to start Qdrant with docker-compose
    if command -v docker-compose >/dev/null 2>&1 || command -v docker >/dev/null 2>&1; then
        echo -e "${BLUE}🐳 Starting Qdrant with docker-compose...${NC}"
        docker-compose up -d qdrant 2>/dev/null || docker compose up -d qdrant 2>/dev/null || true
        
        # Wait for Qdrant to be ready
        echo -e "${YELLOW}⏳ Waiting for Qdrant to be ready...${NC}"
        for i in {1..30}; do
            if curl -s http://localhost:$QDRANT_PORT/health > /dev/null 2>&1; then
                echo -e "${GREEN}✅ Qdrant is ready!${NC}"
                break
            fi
            echo -n "."
            sleep 1
        done
        echo ""
    else
        echo -e "${YELLOW}⚠️  Docker not found. Will use in-memory backend.${NC}"
        export USE_QDRANT=0
    fi
fi
echo ""

# Set environment variables
export QDRANT_URL="${QDRANT_URL:-http://localhost:${QDRANT_PORT}}"
export USE_QDRANT="${USE_QDRANT:-1}"
export COLLECTION_NAME="${COLLECTION_NAME:-beir_fiqa_full_ta}"
export AUTO_TRAFFIC="${AUTO_TRAFFIC:-1}"
export TOKENIZERS_PARALLELISM="${TOKENIZERS_PARALLELISM:-false}"

# Display configuration
echo -e "${BLUE}⚙️  Configuration:${NC}"
echo -e "   Port: ${GREEN}${PORT}${NC}"
echo -e "   Qdrant URL: ${GREEN}${QDRANT_URL}${NC}"
echo -e "   Collection: ${GREEN}${COLLECTION_NAME}${NC}"
echo -e "   Auto Traffic: ${GREEN}${AUTO_TRAFFIC}${NC}"
echo -e "   Workers: ${GREEN}${WORKERS}${NC}"
echo ""

# Check if app_v2.py exists
if [ ! -f "services/fiqa_api/app_v2.py" ]; then
    echo -e "${RED}❌ Error: services/fiqa_api/app_v2.py not found${NC}"
    exit 1
fi

# Start the server
echo -e "${GREEN}🚀 Starting app_v2 server...${NC}"
echo -e "${YELLOW}   Server will be available at: http://localhost:${PORT}${NC}"
echo -e "${YELLOW}   Health check: http://localhost:${PORT}/health${NC}"
echo -e "${YELLOW}   Black Swan: http://localhost:${PORT}/ops/black_swan${NC}"
echo -e "${YELLOW}   Demo UI: http://localhost:${PORT}/demo${NC}"
echo ""
echo -e "${BLUE}Press Ctrl+C to stop the server${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Start uvicorn
cd "$PROJECT_ROOT"
uvicorn services.fiqa_api.app_main:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --workers "$WORKERS" \
    --reload \
    --reload-dir services/fiqa_api \
    --reload-dir core

