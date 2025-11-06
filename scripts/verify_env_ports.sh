#!/bin/bash
###############################################################################
# verify_env_ports.sh - Verify .env port configuration
# 
# This script:
# 1. Checks if .env file exists
# 2. Loads and displays all port configurations
# 3. Tests connectivity to each service
# 4. Reports overall health status
###############################################################################

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         SearchForge Port Configuration Verification           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if .env exists
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${RED}❌ .env file not found at: $PROJECT_ROOT/.env${NC}"
    echo -e "${YELLOW}Creating .env from .env.example...${NC}"
    
    if [ -f "$PROJECT_ROOT/.env.example" ]; then
        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
        echo -e "${GREEN}✅ Created .env from template${NC}"
    else
        echo -e "${RED}❌ .env.example not found. Cannot create .env${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ .env file found${NC}"
echo ""

# Load environment variables
export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)

# Display configuration
echo -e "${BLUE}📝 Port Configuration:${NC}"
echo -e "   ${YELLOW}APP_DEMO_URL:${NC}    ${APP_DEMO_URL:-NOT SET}"
echo -e "   ${YELLOW}FIQA_API_URL:${NC}    ${FIQA_API_URL:-NOT SET}"
echo -e "   ${YELLOW}QDRANT_URL:${NC}      ${QDRANT_URL:-NOT SET}"
echo -e "   ${YELLOW}BASE_URL:${NC}        ${BASE_URL:-NOT SET}"
echo -e "   ${YELLOW}API_BASE:${NC}        ${API_BASE:-NOT SET}"
echo -e "   ${YELLOW}PORT:${NC}            ${PORT:-NOT SET}"
echo ""

# Health check function
check_health() {
    local name=$1
    local url=$2
    local endpoint=${3:-"/health"}
    
    echo -ne "${BLUE}🔍 Checking ${name}...${NC} "
    
    if [ -z "$url" ]; then
        echo -e "${YELLOW}SKIP (URL not set)${NC}"
        return 2
    fi
    
    # Extract port from URL
    local port=$(echo "$url" | sed -n 's/.*:\([0-9]*\).*/\1/p')
    
    # Check if port is in use
    if ! lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${RED}DOWN (port $port not listening)${NC}"
        return 1
    fi
    
    # Try to connect
    if curl -sf "${url}${endpoint}" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ HEALTHY (port $port)${NC}"
        return 0
    elif curl -sf "${url}/" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ RESPONDING (port $port)${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  LISTENING but no HTTP response (port $port)${NC}"
        return 1
    fi
}

# Run health checks
echo -e "${BLUE}🏥 Health Checks:${NC}"
echo ""

PASS=0
FAIL=0
SKIP=0

# Check APP_DEMO_URL (port 8001)
if check_health "Demo App (8001)" "$APP_DEMO_URL" "/health"; then
    ((PASS++))
elif [ $? -eq 2 ]; then
    ((SKIP++))
else
    ((FAIL++))
fi

# Check FIQA_API_URL (port 8080)
if check_health "FIQA API (8080)" "$FIQA_API_URL" "/health"; then
    ((PASS++))
elif [ $? -eq 2 ]; then
    ((SKIP++))
else
    ((FAIL++))
fi

# Check QDRANT_URL (port 6333)
if check_health "Qdrant (6333)" "$QDRANT_URL" "/"; then
    ((PASS++))
elif [ $? -eq 2 ]; then
    ((SKIP++))
else
    ((FAIL++))
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}📊 Summary:${NC}"
echo -e "   ${GREEN}✅ Healthy:${NC}  $PASS"
echo -e "   ${RED}❌ Down:${NC}     $FAIL"
echo -e "   ${YELLOW}⚠️  Skipped:${NC} $SKIP"
echo ""

# Final verdict
if [ $FAIL -eq 0 ] && [ $PASS -gt 0 ]; then
    echo -e "${GREEN}✅ All configured ports are healthy!${NC}"
    echo ""
    echo -e "${BLUE}💡 All environment references resolved${NC}"
    exit 0
elif [ $PASS -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Some services are down${NC}"
    echo ""
    echo -e "${BLUE}💡 Tip: Start missing services:${NC}"
    echo -e "   ${YELLOW}Demo App:${NC}  bash scripts/start_demo_app.sh"
    echo -e "   ${YELLOW}FIQA API:${NC}  MAIN_PORT=8080 bash services/fiqa_api/start_server.sh"
    echo -e "   ${YELLOW}Qdrant:${NC}    docker-compose up -d qdrant"
    exit 1
else
    echo -e "${RED}❌ No services are running${NC}"
    echo ""
    echo -e "${BLUE}💡 Start services first:${NC}"
    echo -e "   ${YELLOW}bash scripts/start_demo_app.sh${NC}"
    exit 1
fi

