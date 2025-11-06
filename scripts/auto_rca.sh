#!/bin/bash

###############################################################################
# Auto-RCA Kit Runner for SearchForge
# 
# This script runs the automated Black Swan E2E test and captures:
# - HAR (HTTP Archive) files for network traffic
# - Video recordings of the test execution
# - Screenshots at key steps
# - Trace files for detailed debugging
# - JSON report with test results
# 
# All artifacts are bundled into a timestamped ZIP file in the artifacts/ directory.
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Auto-RCA Kit - SearchForge Black Swan Test            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Get the project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# Load environment variables from .env file
if [ -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${BLUE}📝 Loading configuration from .env${NC}"
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
fi

echo -e "${YELLOW}📍 Project root: ${PROJECT_ROOT}${NC}"
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠️  node_modules not found. Running npm install...${NC}"
    npm install
    echo ""
fi

# Check if Playwright browsers are installed
if [ ! -d "$HOME/Library/Caches/ms-playwright/chromium-"* ] && \
   [ ! -d "$HOME/.cache/ms-playwright/chromium-"* ]; then
    echo -e "${YELLOW}⚠️  Playwright browsers not found. Installing...${NC}"
    npx playwright install chromium
    echo ""
fi

# Check if the server is running (use APP_DEMO_URL from .env, fallback to BASE_URL or default)
BASE_URL="${BASE_URL:-${APP_DEMO_URL:-http://localhost:8001}}"
PORT=$(echo "$BASE_URL" | sed -n 's/.*:\([0-9]*\).*/\1/p')
PORT=${PORT:-8001}

echo -e "${BLUE}🔍 Checking if SearchForge server is running on port $PORT...${NC}"
# Try multiple endpoints to check server status
if curl -s "${BASE_URL}/docs" > /dev/null 2>&1 || \
   curl -s "${BASE_URL}/ops/black_swan/status" > /dev/null 2>&1 || \
   curl -s "${BASE_URL}/health" > /dev/null 2>&1; then
    : # Server is running
else
    echo -e "${RED}❌ Server is not running on port $PORT${NC}"
    echo -e "${YELLOW}Please start the SearchForge server first:${NC}"
    echo -e "   ${GREEN}# Option 1: Start on port 8001 (for Black Swan Demo)${NC}"
    echo -e "   ${GREEN}bash scripts/start_demo_app.sh${NC}"
    echo -e ""
    echo -e "   ${GREEN}# Option 2: Use existing server on port 8080${NC}"
    echo -e "   ${GREEN}BASE_URL=http://localhost:8080 bash scripts/auto_rca.sh${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Server is running${NC}"
echo ""

# Clean up old test results
echo -e "${BLUE}🧹 Cleaning up old test results...${NC}"
rm -rf test-results/
rm -rf playwright-report/
echo ""

# Run the E2E test
echo -e "${BLUE}🚀 Starting Black Swan E2E test...${NC}"
echo -e "${YELLOW}This will take up to 3 minutes...${NC}"
echo ""

START_TIME=$(date +%s)

# Run the test (don't exit on failure, we want to show the report)
set +e
npx playwright test tests/e2e/black_swan.e2e.spec.ts
TEST_EXIT_CODE=$?
set -e

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ Test PASSED${NC}"
else
    echo -e "${RED}❌ Test FAILED (exit code: $TEST_EXIT_CODE)${NC}"
fi

echo -e "${BLUE}⏱️  Duration: ${DURATION}s${NC}"
echo ""

# Find the latest artifact ZIP
LATEST_ZIP=$(find artifacts -name "auto_rca_*.zip" -type f -print0 | xargs -0 ls -t | head -n 1)

if [ -n "$LATEST_ZIP" ]; then
    echo -e "${GREEN}📦 Evidence bundle created:${NC}"
    echo -e "   ${LATEST_ZIP}"
    echo ""
    
    # Show ZIP contents
    echo -e "${BLUE}📋 Bundle contents:${NC}"
    unzip -l "$LATEST_ZIP" | tail -n +4 | head -n -2
    echo ""
    
    echo -e "${YELLOW}💡 To extract the bundle:${NC}"
    echo -e "   ${GREEN}unzip $LATEST_ZIP -d artifacts/extracted/${NC}"
else
    echo -e "${YELLOW}⚠️  No artifact bundle found${NC}"
fi

echo ""
echo -e "${BLUE}📊 Additional reports:${NC}"
if [ -d "playwright-report" ]; then
    echo -e "   HTML Report: ${GREEN}playwright-report/index.html${NC}"
    echo -e "   View with: ${GREEN}npm run report${NC}"
fi

if [ -d "test-results" ]; then
    echo -e "   Test Results: ${GREEN}test-results/${NC}"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

exit $TEST_EXIT_CODE

