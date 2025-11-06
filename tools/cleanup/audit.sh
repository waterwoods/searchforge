#!/usr/bin/env bash
# Audit script to identify cleanup candidates
# Usage: bash tools/cleanup/audit.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

OUTPUT_DIR="${REPO_ROOT}/artifacts/cleanup"
mkdir -p "${OUTPUT_DIR}"

CANDIDATES_FILE="${OUTPUT_DIR}/candidates.txt"

echo "=========================================="
echo "  Repository Cleanup Audit (Dry-Run)"
echo "=========================================="
echo ""

# Print current disk usage
echo "📊 Current repository size:"
du -sh . | awk '{print "  " $0}'
echo ""

# Find unused .sh scripts (not referenced in Makefile, tools/**/*.sh, docker-compose*.yml)
echo "🔍 Finding unused .sh scripts..."
UNUSED_SH="${OUTPUT_DIR}/unused_sh.txt"
{
    # Get all tracked .sh files
    git ls-files '*.sh' | sort > "${OUTPUT_DIR}/all_sh.txt" || true
    
    # Get referenced .sh files
    {
        grep -hroE '[^ ]+\.sh' Makefile tools/**/*.sh docker-compose*.yml 2>/dev/null || true
    } | sort -u > "${OUTPUT_DIR}/referenced_sh.txt" || true
    
    # Find unused ones, excluding whitelist
    comm -23 "${OUTPUT_DIR}/all_sh.txt" "${OUTPUT_DIR}/referenced_sh.txt" 2>/dev/null | \
        grep -vE 'tools/switch/|migration_.*\.sh' > "${UNUSED_SH}" || true
} 

if [ -s "${UNUSED_SH}" ]; then
    echo "  Found $(wc -l < "${UNUSED_SH}" | tr -d ' ') unused .sh scripts:"
    head -20 "${UNUSED_SH}" | sed 's/^/    /'
    if [ "$(wc -l < "${UNUSED_SH}" | tr -d ' ')" -gt 20 ]; then
        echo "    ... and $(($(wc -l < "${UNUSED_SH}" | tr -d ' ') - 20)) more"
    fi
else
    echo "  ✅ No unused .sh scripts found"
fi
echo ""

# Find heavy tests/docs
echo "🔍 Finding large test/doc files..."
HEAVY_FILES="${OUTPUT_DIR}/heavy_files.txt"
{
    git ls-files | grep -E '(^tests?/|\.md$)' | \
        while read -r file; do
            if [ -f "${file}" ]; then
                du -h "${file}" 2>/dev/null || true
            fi
        done | sort -h | tail -n 100 > "${HEAVY_FILES}" || true
}

if [ -s "${HEAVY_FILES}" ]; then
    TOTAL_SIZE=$(awk '{sum+=$1} END {print sum}' "${HEAVY_FILES}" 2>/dev/null || echo "0")
    echo "  Found large test/doc files (top 100):"
    head -20 "${HEAVY_FILES}" | sed 's/^/    /'
    if [ "$(wc -l < "${HEAVY_FILES}" | tr -d ' ')" -gt 20 ]; then
        echo "    ... and $(($(wc -l < "${HEAVY_FILES}" | tr -d ' ') - 20)) more"
    fi
else
    echo "  ✅ No large test/doc files found"
fi
echo ""

# Show untracked ignored files (info only, won't touch)
echo "📋 Untracked ignored files (will NOT be touched):"
UNTRACKED_COUNT=$(git clean -Xfdn 2>&1 | wc -l | tr -d ' ')
echo "  Found ${UNTRACKED_COUNT} untracked ignored files"
echo "  (Run 'git clean -Xfdn' to see details)"
echo ""

# Combine candidates (excluding whitelist)
echo "📝 Generating candidate list..."
{
    # Unused scripts
    if [ -s "${UNUSED_SH}" ]; then
        cat "${UNUSED_SH}"
    fi
    
    # Large test/doc files (excluding README.md)
    if [ -s "${HEAVY_FILES}" ]; then
        awk '{print $2}' "${HEAVY_FILES}" | grep -v '^README\.md$' | grep -vE '^(services|ui|core|configs)/' || true
    fi
} | sort -u | grep -vE '^(services|ui|core|configs)/' | grep -vE '^docker-compose.*\.yml$' | grep -vE '^Makefile$' | grep -vE '^tools/switch/' | grep -vE '^migration_.*\.sh$' > "${CANDIDATES_FILE}" || true

CANDIDATE_COUNT=$(wc -l < "${CANDIDATES_FILE}" | tr -d ' ' || echo "0")

if [ "${CANDIDATE_COUNT}" -gt 0 ]; then
    echo "  ✅ Generated ${CANDIDATE_COUNT} candidates"
    echo "  📄 Saved to: ${CANDIDATES_FILE}"
    echo ""
    echo "  Preview (first 20):"
    head -20 "${CANDIDATES_FILE}" | sed 's/^/    /'
    if [ "${CANDIDATE_COUNT}" -gt 20 ]; then
        echo "    ... and $((${CANDIDATE_COUNT} - 20)) more"
    fi
else
    echo "  ✅ No candidates found"
    touch "${CANDIDATES_FILE}"
fi
echo ""

echo "=========================================="
echo "  Audit Complete"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Review: ${CANDIDATES_FILE}"
echo "  2. Apply:  make cleanup-apply"
echo "  3. Restore: make cleanup-restore (if needed)"
echo ""


