#!/usr/bin/env bash
# Restore archived files back to original locations
# Usage: bash tools/cleanup/restore.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

ARCHIVE_DIR="${REPO_ROOT}/archive"

echo "=========================================="
echo "  Repository Cleanup Restore"
echo "=========================================="
echo ""

# Check if archive directory exists
if [ ! -d "${ARCHIVE_DIR}" ]; then
    echo "❌ Error: archive directory not found: ${ARCHIVE_DIR}"
    echo "   Nothing to restore"
    exit 1
fi

# Find all files in archive
RESTORED_COUNT=0
SKIPPED_COUNT=0
ERROR_COUNT=0

echo "🔍 Finding files in archive..."
echo ""

# Process all files in archive
find "${ARCHIVE_DIR}" -type f | while read -r archived_file; do
    # Calculate original path (remove archive/ prefix)
    original_path="${archived_file#${ARCHIVE_DIR}/}"
    
    # Skip if original path already exists
    if [ -e "${original_path}" ]; then
        echo "  ⚠️  Skipping (exists): ${original_path}"
        ((SKIPPED_COUNT++)) || true
        continue
    fi
    
    # Create parent directory if needed
    original_parent=$(dirname "${original_path}")
    if [ "${original_parent}" != "." ]; then
        mkdir -p "${original_parent}"
    fi
    
    # Use git mv to restore (reversible)
    if git mv "${archived_file}" "${original_path}" 2>/dev/null; then
        echo "  ✅ Restored: ${original_path}"
        ((RESTORED_COUNT++)) || true
    else
        echo "  ❌ Error restoring: ${original_path}"
        ((ERROR_COUNT++)) || true
    fi
done

# Count files (need to recalculate after loop)
RESTORED_COUNT=$(find "${ARCHIVE_DIR}" -type f 2>/dev/null | wc -l | tr -d ' ' || echo "0")

if [ "${RESTORED_COUNT}" -eq 0 ]; then
    echo "  ℹ️  No files found in archive"
else
    echo ""
    echo "📊 Processing files..."
    find "${ARCHIVE_DIR}" -type f | while read -r archived_file; do
        original_path="${archived_file#${ARCHIVE_DIR}/}"
        
        if [ -e "${original_path}" ]; then
            continue
        fi
        
        original_parent=$(dirname "${original_path}")
        if [ "${original_parent}" != "." ]; then
            mkdir -p "${original_parent}"
        fi
        
        if git mv "${archived_file}" "${original_path}" 2>/dev/null; then
            echo "  ✅ Restored: ${original_path}"
        else
            echo "  ❌ Error: ${original_path}"
        fi
    done
fi

echo ""
echo "📊 Summary:"
ARCHIVE_FILE_COUNT=$(find "${ARCHIVE_DIR}" -type f 2>/dev/null | wc -l | tr -d ' ' || echo "0")
echo "  Files in archive: ${ARCHIVE_FILE_COUNT}"
echo ""

if [ "${ARCHIVE_FILE_COUNT}" -gt 0 ]; then
    echo "💾 Committing restore..."
    git add . 2>/dev/null || true
    git commit -m "chore: restore archived files" || true
    echo ""
    echo "✅ Restore complete!"
    echo ""
    echo "Note: Empty archive directory will remain but is ignored by git"
else
    echo "ℹ️  Archive is empty, nothing to restore"
fi
echo ""


