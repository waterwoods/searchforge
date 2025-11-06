#!/bin/bash

###############################################################################
# Auto-RCA Kit Validation Script
# 
# This script validates that the Auto-RCA Kit is properly installed and
# configured without actually running the tests.
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Auto-RCA Kit - Installation Validation                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

PASS=0
FAIL=0

check_file() {
    local file=$1
    local description=$2
    
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅${NC} $description"
        ((PASS++))
        return 0
    else
        echo -e "${RED}❌${NC} $description - File not found: $file"
        ((FAIL++))
        return 1
    fi
}

check_dir() {
    local dir=$1
    local description=$2
    
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✅${NC} $description"
        ((PASS++))
        return 0
    else
        echo -e "${RED}❌${NC} $description - Directory not found: $dir"
        ((FAIL++))
        return 1
    fi
}

echo -e "${YELLOW}📋 Checking core files...${NC}"
check_file "package.json" "package.json exists"
check_file "playwright.config.ts" "Playwright config exists"
check_file "tests/e2e/black_swan.e2e.spec.ts" "Black Swan E2E test exists"
check_file "scripts/auto_rca.sh" "Auto-RCA runner script exists"
check_file "tests/e2e/README.md" "E2E documentation exists"
check_file "AUTO_RCA_KIT_QUICKSTART.md" "Quick start guide exists"
echo ""

echo -e "${YELLOW}📁 Checking directories...${NC}"
check_dir "tests/e2e" "E2E test directory exists"
check_dir "artifacts" "Artifacts directory exists"
check_dir "scripts" "Scripts directory exists"
echo ""

echo -e "${YELLOW}📦 Checking npm dependencies...${NC}"
if [ -d "node_modules" ]; then
    echo -e "${GREEN}✅${NC} node_modules directory exists"
    ((PASS++))
    
    if [ -d "node_modules/@playwright/test" ]; then
        echo -e "${GREEN}✅${NC} @playwright/test installed"
        ((PASS++))
    else
        echo -e "${RED}❌${NC} @playwright/test not installed"
        ((FAIL++))
    fi
    
    if [ -d "node_modules/adm-zip" ]; then
        echo -e "${GREEN}✅${NC} adm-zip installed"
        ((PASS++))
    else
        echo -e "${RED}❌${NC} adm-zip not installed"
        ((FAIL++))
    fi
else
    echo -e "${RED}❌${NC} node_modules not found - run 'npm install'"
    ((FAIL+=3))
fi
echo ""

echo -e "${YELLOW}🌐 Checking Playwright browsers...${NC}"
if [ -d "$HOME/Library/Caches/ms-playwright" ] || [ -d "$HOME/.cache/ms-playwright" ]; then
    echo -e "${GREEN}✅${NC} Playwright browsers cache exists"
    ((PASS++))
else
    echo -e "${YELLOW}⚠️${NC}  Playwright browsers not found - run 'npx playwright install chromium'"
    ((FAIL++))
fi
echo ""

echo -e "${YELLOW}🔧 Checking script permissions...${NC}"
if [ -x "scripts/auto_rca.sh" ]; then
    echo -e "${GREEN}✅${NC} auto_rca.sh is executable"
    ((PASS++))
else
    echo -e "${YELLOW}⚠️${NC}  auto_rca.sh is not executable - run 'chmod +x scripts/auto_rca.sh'"
    ((FAIL++))
fi
echo ""

echo -e "${YELLOW}📝 Checking .gitignore rules...${NC}"
if grep -q "artifacts/" .gitignore 2>/dev/null; then
    echo -e "${GREEN}✅${NC} artifacts/ in .gitignore"
    ((PASS++))
else
    echo -e "${YELLOW}⚠️${NC}  artifacts/ not in .gitignore"
    ((FAIL++))
fi

if grep -q "node_modules/" .gitignore 2>/dev/null; then
    echo -e "${GREEN}✅${NC} node_modules/ in .gitignore"
    ((PASS++))
else
    echo -e "${YELLOW}⚠️${NC}  node_modules/ not in .gitignore"
    ((FAIL++))
fi

if grep -q "playwright-report/" .gitignore 2>/dev/null; then
    echo -e "${GREEN}✅${NC} playwright-report/ in .gitignore"
    ((PASS++))
else
    echo -e "${YELLOW}⚠️${NC}  playwright-report/ not in .gitignore"
    ((FAIL++))
fi
echo ""

echo -e "${YELLOW}🧪 Checking package.json scripts...${NC}"
if grep -q '"test": "playwright test"' package.json; then
    echo -e "${GREEN}✅${NC} npm test script configured"
    ((PASS++))
else
    echo -e "${RED}❌${NC} npm test script not configured"
    ((FAIL++))
fi

if grep -q '"test:black-swan"' package.json; then
    echo -e "${GREEN}✅${NC} npm run test:black-swan script configured"
    ((PASS++))
else
    echo -e "${RED}❌${NC} npm run test:black-swan script not configured"
    ((FAIL++))
fi
echo ""

# Summary
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}📊 Validation Summary${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Passed: $PASS${NC}"
if [ $FAIL -gt 0 ]; then
    echo -e "${RED}Failed: $FAIL${NC}"
else
    echo -e "${GREEN}Failed: $FAIL${NC}"
fi
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! Auto-RCA Kit is ready to use.${NC}"
    echo ""
    echo -e "${YELLOW}📚 Next steps:${NC}"
    echo -e "   1. Start the Demo server (port 8001): ${GREEN}bash scripts/start_demo_app.sh${NC}"
    echo -e "   2. Run the Auto-RCA Kit: ${GREEN}bash scripts/auto_rca.sh${NC}"
    echo -e "   3. View the results: ${GREEN}unzip -l artifacts/auto_rca_*.zip${NC}"
    echo ""
    echo -e "${YELLOW}💡 Tip:${NC} See ${GREEN}AUTO_RCA_PORT_GUIDE.md${NC} for port configuration options"
    echo ""
    exit 0
else
    echo -e "${RED}❌ Some checks failed. Please fix the issues above.${NC}"
    echo ""
    echo -e "${YELLOW}💡 Quick fixes:${NC}"
    if [ ! -d "node_modules" ]; then
        echo -e "   ${GREEN}npm install${NC}"
    fi
    if [ ! -d "$HOME/Library/Caches/ms-playwright" ] && [ ! -d "$HOME/.cache/ms-playwright" ]; then
        echo -e "   ${GREEN}npx playwright install chromium${NC}"
    fi
    if [ ! -x "scripts/auto_rca.sh" ]; then
        echo -e "   ${GREEN}chmod +x scripts/auto_rca.sh${NC}"
    fi
    echo ""
    exit 1
fi

