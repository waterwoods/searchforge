#!/usr/bin/env bash
# start_app_main.sh - Quick start script for app_main
# =====================================================

set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Starting app_main (Clean Entry Point)${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if port 8011 is already in use
if lsof -Pi :8011 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}⚠️  Port 8011 is already in use${NC}"
    echo ""
    echo "To kill the process:"
    echo "  lsof -ti:8011 | xargs kill -9"
    echo ""
    exit 1
fi

# Change to fiqa_api directory
cd "$(dirname "$0")/../services/fiqa_api" || exit 1

echo -e "${GREEN}✓${NC} Changed to services/fiqa_api"
echo ""

# Check if .env exists
if [ ! -f "../../.env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found${NC}"
    echo ""
    echo "Creating .env from .env.main.example..."
    cp ../../.env.main.example ../../.env
    echo -e "${GREEN}✓${NC} Created .env"
    echo ""
fi

# Start app_main
echo -e "${BLUE}Starting app_main on port 8011...${NC}"
echo ""

python app_main.py &
APP_MAIN_PID=$!

# Wait for startup
echo "Waiting for app_main to start..."
sleep 3

# Check if process is running
if ps -p $APP_MAIN_PID > /dev/null 2>&1; then
    echo ""
    echo -e "${GREEN}✓ app_main started successfully!${NC}"
    echo ""
    echo "Process ID: $APP_MAIN_PID"
    echo "Port: 8011"
    echo "Health check: http://localhost:8011/healthz"
    echo ""
    echo "To stop:"
    echo "  kill $APP_MAIN_PID"
    echo "  # or"
    echo "  lsof -ti:8011 | xargs kill -9"
    echo ""
    echo -e "${BLUE}Verification:${NC}"
    echo "  Run: ./scripts/verify_app_main.sh"
    echo ""
else
    echo ""
    echo -e "${YELLOW}⚠️  app_main failed to start${NC}"
    echo ""
    echo "Check logs for errors"
    exit 1
fi

