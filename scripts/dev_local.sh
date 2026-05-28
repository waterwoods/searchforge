#!/usr/bin/env bash
# scripts/dev_local.sh - Start backend and frontend for local development
# =============================================================================
# LAB ONLY — SearchForge local dev (default port 8000)
# Product path: bash scripts/run_demo_local.sh → 8001 (Unified Intake workbench)
# See: scripts/README_OPERATOR.md, docs/archive/platform/README_LAB_INFRA.md
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Configuration (8000 = general dev; broker demo = run_demo_local.sh on 8001)
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
BACKEND_HOST="${BACKEND_HOST:-0.0.0.0}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting SearchForge Local Development${NC}"
echo ""

# Check dependencies
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Error: python3 not found${NC}"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ Error: npm not found${NC}"
    exit 1
fi

# Check if ports are available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo -e "${YELLOW}⚠️  Port $port is already in use${NC}"
        return 1
    fi
    return 0
}

# Start backend
start_backend() {
    echo -e "${GREEN}📦 Starting backend on port $BACKEND_PORT...${NC}"
    
    cd "$REPO_ROOT"
    
    # Check if virtual environment exists
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
    
    # Start uvicorn
    python3 -m uvicorn services.fiqa_api.app_main:app \
        --host "$BACKEND_HOST" \
        --port "$BACKEND_PORT" \
        --reload \
        > /tmp/searchforge_backend.log 2>&1 &
    
    BACKEND_PID=$!
    echo $BACKEND_PID > /tmp/searchforge_backend.pid
    
    # Wait for backend to be ready
    echo -e "${YELLOW}⏳ Waiting for backend to be ready...${NC}"
    for i in {1..30}; do
        if curl -sS "http://localhost:$BACKEND_PORT/healthz" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Backend ready at http://localhost:$BACKEND_PORT${NC}"
            return 0
        fi
        sleep 1
    done
    
    echo -e "${RED}❌ Backend failed to start (check /tmp/searchforge_backend.log)${NC}"
    return 1
}

# Start frontend
start_frontend() {
    echo -e "${GREEN}🎨 Starting frontend on port $FRONTEND_PORT...${NC}"
    
    cd "$REPO_ROOT/ui"
    
    # Ensure .env.local exists
    if [ ! -f ".env.local" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env.local
            # Update with local backend URL
            sed -i.bak "s|VITE_API_BASE_URL=.*|VITE_API_BASE_URL=http://localhost:$BACKEND_PORT|" .env.local
            rm -f .env.local.bak
            echo -e "${YELLOW}📝 Created .env.local from .env.example${NC}"
        else
            echo "VITE_API_BASE_URL=http://localhost:$BACKEND_PORT" > .env.local
            echo -e "${YELLOW}📝 Created .env.local${NC}"
        fi
    fi
    
    # Start vite dev server
    npm run dev -- --host 0.0.0.0 --port "$FRONTEND_PORT" > /tmp/searchforge_frontend.log 2>&1 &
    
    FRONTEND_PID=$!
    echo $FRONTEND_PID > /tmp/searchforge_frontend.pid
    
    # Wait for frontend to be ready
    echo -e "${YELLOW}⏳ Waiting for frontend to be ready...${NC}"
    for i in {1..30}; do
        if curl -sS "http://localhost:$FRONTEND_PORT" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Frontend ready at http://localhost:$FRONTEND_PORT${NC}"
            return 0
        fi
        sleep 1
    done
    
    echo -e "${RED}❌ Frontend failed to start (check /tmp/searchforge_frontend.log)${NC}"
    return 1
}

# Cleanup function
cleanup() {
    echo ""
    echo -e "${YELLOW}🧹 Cleaning up...${NC}"
    
    if [ -f /tmp/searchforge_backend.pid ]; then
        BACKEND_PID=$(cat /tmp/searchforge_backend.pid)
        kill $BACKEND_PID 2>/dev/null || true
        rm -f /tmp/searchforge_backend.pid
    fi
    
    if [ -f /tmp/searchforge_frontend.pid ]; then
        FRONTEND_PID=$(cat /tmp/searchforge_frontend.pid)
        kill $FRONTEND_PID 2>/dev/null || true
        rm -f /tmp/searchforge_frontend.pid
    fi
    
    echo -e "${GREEN}✅ Cleanup complete${NC}"
}

# Trap signals
trap cleanup INT TERM EXIT

# Main execution
cd "$REPO_ROOT"

# Check ports
if ! check_port $BACKEND_PORT; then
    echo -e "${RED}❌ Backend port $BACKEND_PORT is in use. Please stop the process or use a different port.${NC}"
    exit 1
fi

if ! check_port $FRONTEND_PORT; then
    echo -e "${RED}❌ Frontend port $FRONTEND_PORT is in use. Please stop the process or use a different port.${NC}"
    exit 1
fi

# Start services
if start_backend && start_frontend; then
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✅ SearchForge is running!${NC}"
    echo ""
    echo -e "   Backend:  ${GREEN}http://localhost:$BACKEND_PORT${NC}"
    echo -e "   Frontend: ${GREEN}http://localhost:$FRONTEND_PORT${NC}"
    echo -e "   Demo:     ${GREEN}http://localhost:$FRONTEND_PORT/demo${NC}"
    echo ""
    echo -e "   Health:   ${GREEN}http://localhost:$BACKEND_PORT/healthz${NC}"
    echo -e "   Ready:    ${GREEN}http://localhost:$BACKEND_PORT/readyz${NC}"
    echo ""
    echo -e "${YELLOW}📝 Logs:${NC}"
    echo -e "   Backend:  /tmp/searchforge_backend.log"
    echo -e "   Frontend: /tmp/searchforge_frontend.log"
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    
    # Wait for user interrupt
    wait
else
    echo -e "${RED}❌ Failed to start services${NC}"
    cleanup
    exit 1
fi
