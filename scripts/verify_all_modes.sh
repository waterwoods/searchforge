#!/bin/bash
# Verify Black Swan Mode A/B/C configuration from .env

set -e

cd "$(dirname "$0")/.."

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║         Black Swan Mode A/B/C Configuration Verification                    ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo

# Check if settings module loads correctly
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. Settings Module Verification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path('services/fiqa_api')))
import settings

print('✅ Settings module loaded successfully')
print()
print('📊 Mode A Configuration (High QPS Burst):')
print(f'   PLAY_A_DURATION_SEC  = {settings.PLAY_A_DURATION_SEC}s  (burst phase)')
print(f'   PLAY_A_RECOVERY_SEC  = {settings.PLAY_A_RECOVERY_SEC}s  (recovery phase)')
print(f'   Total runtime        = {settings.PLAY_A_DURATION_SEC + settings.PLAY_A_RECOVERY_SEC}s')
print()
print('📊 Mode B Configuration (Heavy Request):')
print(f'   PLAY_B_DURATION_SEC  = {settings.PLAY_B_DURATION_SEC}s')
print(f'   HEAVY_NUM_CANDIDATES = {settings.HEAVY_NUM_CANDIDATES}')
print(f'   HEAVY_RERANK_TOPK    = {settings.HEAVY_RERANK_TOPK}')
print(f'   RERANK_MODEL         = {settings.RERANK_MODEL}')
print(f'   RERANK_DELAY_MS      = {settings.RERANK_DELAY_MS}ms')
print(f'   HEAVY_QUERY_BANK     = {settings.HEAVY_QUERY_BANK}')
print()
print('📊 Mode C Configuration (Network Delay):')
print(f'   PLAY_C_DURATION_SEC  = {settings.PLAY_C_DURATION_SEC}s')
print(f'   MODE_C_DELAY_MS      = {settings.MODE_C_DELAY_MS}ms')
"

echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. Environment Variables Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo
echo "Mode A variables:"
if grep -q "PLAY_A_DURATION_SEC" .env 2>/dev/null; then
    echo "  ✓ $(grep PLAY_A_DURATION_SEC .env)"
else
    echo "  ℹ PLAY_A_DURATION_SEC not set in .env (using default: 15)"
fi

if grep -q "PLAY_A_RECOVERY_SEC" .env 2>/dev/null; then
    echo "  ✓ $(grep PLAY_A_RECOVERY_SEC .env)"
else
    echo "  ℹ PLAY_A_RECOVERY_SEC not set in .env (using default: 45)"
fi

echo
echo "Mode B variables:"
if grep -q "PLAY_B_DURATION_SEC" .env 2>/dev/null; then
    echo "  ✓ $(grep PLAY_B_DURATION_SEC .env)"
else
    echo "  ℹ PLAY_B_DURATION_SEC not set in .env (using default: 180)"
fi

if grep -q "HEAVY_NUM_CANDIDATES" .env 2>/dev/null; then
    echo "  ✓ $(grep HEAVY_NUM_CANDIDATES .env)"
else
    echo "  ℹ HEAVY_NUM_CANDIDATES not set in .env (using default: 1500)"
fi

if grep -q "HEAVY_RERANK_TOPK" .env 2>/dev/null; then
    echo "  ✓ $(grep HEAVY_RERANK_TOPK .env)"
else
    echo "  ℹ HEAVY_RERANK_TOPK not set in .env (using default: 300)"
fi

echo
echo "Mode C variables:"
if grep -q "PLAY_C_DURATION_SEC" .env 2>/dev/null; then
    echo "  ✓ $(grep PLAY_C_DURATION_SEC .env)"
else
    echo "  ℹ PLAY_C_DURATION_SEC not set in .env (using default: 60)"
fi

if grep -q "MODE_C_DELAY_MS" .env 2>/dev/null; then
    echo "  ✓ $(grep MODE_C_DELAY_MS .env)"
else
    echo "  ℹ MODE_C_DELAY_MS not set in .env (using default: 250)"
fi

echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. Code Integration Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# Check Mode A references
MODE_A_REFS=$(grep -c "settings.PLAY_A_DURATION_SEC\|settings.PLAY_A_RECOVERY_SEC" services/fiqa_api/app_v2.py || true)
echo "Mode A settings references: $MODE_A_REFS"
if [ "$MODE_A_REFS" -ge 3 ]; then
    echo "  ✓ Mode A correctly using settings module"
else
    echo "  ⚠ Mode A may not be fully integrated"
fi

# Check Mode B references
MODE_B_REFS=$(grep -c "settings.PLAY_B_DURATION_SEC\|settings.HEAVY_NUM_CANDIDATES\|settings.HEAVY_RERANK_TOPK" services/fiqa_api/app_v2.py || true)
echo "Mode B settings references: $MODE_B_REFS"
if [ "$MODE_B_REFS" -ge 6 ]; then
    echo "  ✓ Mode B correctly using settings module"
else
    echo "  ⚠ Mode B may not be fully integrated"
fi

# Check Mode C references
MODE_C_REFS=$(grep -c "settings.PLAY_C_DURATION_SEC\|settings.MODE_C_DELAY_MS" services/fiqa_api/app_v2.py || true)
echo "Mode C settings references: $MODE_C_REFS"
if [ "$MODE_C_REFS" -ge 3 ]; then
    echo "  ✓ Mode C correctly using settings module"
else
    echo "  ⚠ Mode C may not be fully integrated"
fi

# Check for hardcoded durations
echo
HARDCODED=$(grep -E '"[0-9]+".*# (15s|45s|60s|180s)' services/fiqa_api/app_v2.py | grep -c "BLACK_SWAN_LOAD_DURATION\|BLACK_SWAN_RECOVERY_DURATION" || true)
if [ "$HARDCODED" -eq 0 ]; then
    echo "  ✓ No hardcoded durations found (all using settings)"
else
    echo "  ⚠ Found $HARDCODED hardcoded duration(s)"
fi

echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. Summary Table"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo
printf "| %-8s | %-20s | %-12s | %-40s |\n" "Mode" "Parameter" "Default" "Description"
echo "|----------|----------------------|--------------|------------------------------------------|"
printf "| %-8s | %-20s | %-12s | %-40s |\n" "A" "PLAY_A_DURATION_SEC" "15s" "Burst duration (600 QPS)"
printf "| %-8s | %-20s | %-12s | %-40s |\n" "A" "PLAY_A_RECOVERY_SEC" "45s" "Hold duration (300 QPS)"
printf "| %-8s | %-20s | %-12s | %-40s |\n" "B" "PLAY_B_DURATION_SEC" "180s" "Heavy load duration"
printf "| %-8s | %-20s | %-12s | %-40s |\n" "B" "HEAVY_NUM_CANDIDATES" "1500" "Candidate set size"
printf "| %-8s | %-20s | %-12s | %-40s |\n" "B" "HEAVY_RERANK_TOPK" "300" "Rerank size"
printf "| %-8s | %-20s | %-12s | %-40s |\n" "C" "PLAY_C_DURATION_SEC" "60s" "Delay test duration"
printf "| %-8s | %-20s | %-12s | %-40s |\n" "C" "MODE_C_DELAY_MS" "250ms" "Artificial latency"

echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Verification Complete"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo
echo "💡 To customize configuration:"
echo "   1. Copy .env.black_swan.example to .env"
echo "   2. Edit duration values as needed"
echo "   3. Restart backend"
echo

