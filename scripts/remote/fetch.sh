#!/bin/bash
# =============================================================================
# Remote Fetch Script - Pull Results from Remote to Local
# =============================================================================
set -euo pipefail

REMOTE_USER_HOST=${REMOTE_USER_HOST:-"andy@100.67.88.114"}
REMOTE_BASE=${REMOTE_BASE:-"~/searchforge"}
LOCAL_DST=${LOCAL_DST:-"$HOME/Downloads/autotuner_runs"}
PACK_ROOT=${PACK_ROOT:-""}

echo "==============================================="
echo "📥 Fetching AutoTuner Results"
echo "==============================================="

# Create local destination
mkdir -p "${LOCAL_DST}"
echo "✓ Local destination: ${LOCAL_DST}"

# If PACK_ROOT not specified, find the latest
if [ -z "${PACK_ROOT}" ]; then
    echo "Finding latest run on remote..."
    PACK_ROOT=$(ssh "${REMOTE_USER_HOST}" "ls -td ~/runs/* 2>/dev/null | head -n 1" || echo "")
    
    if [ -z "${PACK_ROOT}" ]; then
        echo "❌ No run directories found on remote"
        exit 1
    fi
    echo "✓ Latest run: ${PACK_ROOT}"
fi

# Check if package exists
PACK_FILE="${PACK_ROOT}.tgz"
echo ""
echo "Checking for package: ${PACK_FILE}"
if ssh "${REMOTE_USER_HOST}" "[ -f ${PACK_FILE} ]" 2>/dev/null; then
    echo "✓ Package found, downloading..."
    scp "${REMOTE_USER_HOST}:${PACK_FILE}" "${LOCAL_DST}/"
    
    # Extract
    BASENAME=$(basename "${PACK_ROOT}")
    cd "${LOCAL_DST}"
    tar -xzf "${BASENAME}.tgz"
    echo "✓ Extracted to: ${LOCAL_DST}/${BASENAME}"
    
    # Try to open index.html
    INDEX_FILE="${LOCAL_DST}/${BASENAME}/index.html"
    if [ -f "${INDEX_FILE}" ]; then
        echo ""
        echo "🌐 Opening report in browser..."
        open "${INDEX_FILE}"
    else
        echo "ℹ️  No index.html found"
        echo "Available files:"
        ls -lh "${LOCAL_DST}/${BASENAME}/" | head -n 20
    fi
else
    echo "⚠️  Package not found, syncing directory directly..."
    rsync -avz --progress \
        "${REMOTE_USER_HOST}:${PACK_ROOT}/" \
        "${LOCAL_DST}/$(basename ${PACK_ROOT})/"
    
    echo "✓ Synced to: ${LOCAL_DST}/$(basename ${PACK_ROOT})"
    
    # Try to open index.html
    INDEX_FILE="${LOCAL_DST}/$(basename ${PACK_ROOT})/index.html"
    if [ -f "${INDEX_FILE}" ]; then
        echo ""
        echo "🌐 Opening report in browser..."
        open "${INDEX_FILE}"
    fi
fi

echo ""
echo "==============================================="
echo "✅ Fetch completed"
echo "Local path: ${LOCAL_DST}/$(basename ${PACK_ROOT})"
echo "==============================================="
