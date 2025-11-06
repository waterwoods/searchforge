#!/usr/bin/env bash
# Apply cleanup: move candidates to archive/
# Usage: bash tools/cleanup/apply.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

OUTPUT_DIR="${REPO_ROOT}/artifacts/cleanup"
CANDIDATES_FILE="${OUTPUT_DIR}/candidates.txt"
ARCHIVE_DIR="${REPO_ROOT}/archive"

# Check if candidates file exists
if [ ! -f "${CANDIDATES_FILE}" ]; then
    echo "❌ Error: candidates file not found: ${CANDIDATES_FILE}"
    echo "   Run 'make cleanup-audit' first"
    exit 1
fi

# Check if candidates file is empty
if [ ! -s "${CANDIDATES_FILE}" ]; then
    echo "✅ No candidates to archive"
    exit 0
fi

echo "=========================================="
echo "  Repository Cleanup Apply"
echo "=========================================="
echo ""

# Print before size
BEFORE_SIZE=$(du -sh . | awk '{print $1}')
echo "📊 Repository size (before): ${BEFORE_SIZE}"
echo ""

# Create archive directory
mkdir -p "${ARCHIVE_DIR}"

# Ensure archive/ is in .gitignore
if ! grep -q "^archive/\*\*$" .gitignore 2>/dev/null; then
    echo "📝 Adding archive/** to .gitignore..."
    echo "" >> .gitignore
    echo "archive/**" >> .gitignore
fi

# Process candidates
MOVED_COUNT=0
SKIPPED_COUNT=0
ERROR_COUNT=0

while IFS= read -r candidate; do
    # Skip empty lines
    [ -z "${candidate}" ] && continue
    
    # Skip if file doesn't exist
    if [ ! -e "${candidate}" ]; then
        echo "  ⚠️  Skipping (not found): ${candidate}"
        ((SKIPPED_COUNT++)) || true
        continue
    fi
    
    # Skip whitelist items (safety check)
    if echo "${candidate}" | grep -qE '^(services|ui|core|configs)/' || \
       echo "${candidate}" | grep -qE '^docker-compose.*\.yml$' || \
       echo "${candidate}" | grep -qE '^Makefile$' || \
       echo "${candidate}" | grep -qE '^tools/switch/' || \
       echo "${candidate}" | grep -qE '^migration_.*\.sh$' || \
       echo "${candidate}" | grep -qE '^README\.md$'; then
        echo "  ⚠️  Skipping (whitelist): ${candidate}"
        ((SKIPPED_COUNT++)) || true
        continue
    fi
    
    # Calculate archive path (preserve directory structure)
    ARCHIVE_PATH="${ARCHIVE_DIR}/${candidate}"
    ARCHIVE_PARENT=$(dirname "${ARCHIVE_PATH}")
    mkdir -p "${ARCHIVE_PARENT}"
    
    # Use git mv to move (reversible)
    if git mv "${candidate}" "${ARCHIVE_PATH}" 2>/dev/null; then
        echo "  ✅ Moved: ${candidate}"
        ((MOVED_COUNT++)) || true
    else
        echo "  ❌ Error moving: ${candidate}"
        ((ERROR_COUNT++)) || true
    fi
done < "${CANDIDATES_FILE}"

echo ""
echo "📊 Summary:"
echo "  Moved:    ${MOVED_COUNT} files"
echo "  Skipped:  ${SKIPPED_COUNT} files"
echo "  Errors:  ${ERROR_COUNT} files"
echo ""

# Print after size
AFTER_SIZE=$(du -sh . | awk '{print $1}')
echo "📊 Repository size (after): ${AFTER_SIZE}"
echo ""

if [ "${MOVED_COUNT}" -gt 0 ]; then
    echo "💾 Committing changes..."
    git add .gitignore "${ARCHIVE_DIR}" 2>/dev/null || true
    git commit -m "chore: archive unused scripts/tests/docs" || true
    echo ""
    echo "✅ Cleanup applied successfully!"
    echo ""
    echo "To restore: make cleanup-restore"
else
    echo "ℹ️  No files were moved"
fi
echo ""


