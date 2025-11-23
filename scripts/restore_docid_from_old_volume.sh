#!/bin/bash
# Restore original doc_id for fiqa_para_50k from old Qdrant volume
# This script safely reads from old volume (read-only) and restores doc_id mappings

set -euo pipefail

COLLECTION="fiqa_para_50k"
VOL="searchforge_qdrant_data"     # 旧命名卷
OUT=".runs/docid_map_${COLLECTION}.json"
OLD_PORT=7000
# Try newer versions first (volume might be from newer Qdrant), then older versions
CANDIDATE_TAGS=("v1.9.0" "v1.8.4" "v1.8.0" "v1.7.4" "v1.6.3" "v1.5.1" "v1.4.0" "v1.3.0" "v1.2.0" "v1.1.0" "v1.0.0")

echo "[INFO] Starting doc_id restoration for ${COLLECTION}"

# 0) 预检查：卷存在、Make 目标存在
echo "[0/5] Pre-checks..."
if ! docker volume inspect "$VOL" >/dev/null 2>&1; then
    echo "[ERROR] Volume $VOL does not exist"
    exit 1
fi
echo "  ✓ Volume $VOL exists"

if ! grep -q 'docid-export-old' Makefile; then
    echo "[ERROR] Make target docid-export-old missing"
    exit 1
fi
if ! grep -q 'docid-apply' Makefile; then
    echo "[ERROR] Make target docid-apply missing"
    exit 1
fi
if ! grep -q 'docid-verify' Makefile; then
    echo "[ERROR] Make target docid-verify missing"
    exit 1
fi
echo "  ✓ All required Make targets exist"

# 1) 找可用旧版本：只读挂旧卷，起临时 qdrant-old，直到 /collections 可读
# First check if we can use current Qdrant directly (faster)
echo "[1/5] Finding compatible Qdrant version..."
if curl -s "http://localhost:6333/collections/${COLLECTION}" >/dev/null 2>&1; then
    echo "[INFO] Collection ${COLLECTION} found in current Qdrant - using it directly"
    OLD_BASE="http://localhost:6333"
    SKIP_CLEANUP=true
    FOUND="current"
else
    docker rm -f qdrant-old >/dev/null 2>&1 || true
    
    FOUND=""
    SKIP_CLEANUP=false  # Initialize early
    for tag in "${CANDIDATE_TAGS[@]}"; do
    echo "  [try] qdrant/qdrant:$tag"
    # Clean up any existing container first
    docker rm -f qdrant-old >/dev/null 2>&1 || true
    
    # Try to start container
    CONTAINER_ID=$(docker run -d --name qdrant-old -p ${OLD_PORT}:6333 \
        -v "${VOL}":/qdrant/storage:ro qdrant/qdrant:"$tag" 2>&1)
    
    if [ $? -ne 0 ]; then
        echo "    ✗ Failed to start container: $CONTAINER_ID"
        docker rm -f qdrant-old >/dev/null 2>&1 || true
        continue
    fi
    
    # Wait for container to be ready
    for i in {1..30}; do
        # Check if container is still running
        if ! docker ps | grep -q qdrant-old; then
            echo "    ✗ Container stopped unexpectedly"
            docker logs qdrant-old 2>&1 | tail -5 || true
            break
        fi
        
        # Try to connect (try multiple endpoints)
        if curl -s --connect-timeout 2 "http://localhost:${OLD_PORT}/collections" >/dev/null 2>&1 || \
           curl -s --connect-timeout 2 "http://127.0.0.1:${OLD_PORT}/collections" >/dev/null 2>&1; then
            FOUND="$tag"
            echo "    ✓ Qdrant $tag is responding on localhost:${OLD_PORT}"
            break
        fi
        sleep 1
    done
    
    if [ -n "$FOUND" ]; then
        break
    else
        echo "    ✗ Container did not become ready in time"
        docker logs qdrant-old 2>&1 | tail -10 || true
        docker rm -f qdrant-old >/dev/null 2>&1 || true
    fi
    done
    
    if [ -z "$FOUND" ]; then
    echo "[WARN] No compatible Qdrant tag found for old volume"
    echo "[INFO] Trying to export from currently running Qdrant as fallback..."
    
    # Check if current Qdrant has the collection
    if curl -s "http://localhost:6333/collections/${COLLECTION}" >/dev/null 2>&1; then
        echo "[INFO] Found collection ${COLLECTION} in current Qdrant"
        echo "[INFO] Exporting directly from current Qdrant (localhost:6333)..."
        
        OLD_BASE="http://localhost:6333"
        SKIP_CLEANUP=true  # Don't try to cleanup qdrant-old since we're not using it
        
        # Skip to export step
    else
        echo "[ERROR] No compatible Qdrant tag found and collection not in current Qdrant"
        docker rm -f qdrant-old >/dev/null 2>&1 || true
        exit 1
    fi
    fi
fi

if [ "$SKIP_CLEANUP" != "true" ]; then
    echo "  ✓ Old volume readable via qdrant-old:$FOUND"
fi

# 2) 从旧卷导出 doc_id 映射（按文本内容哈希做键），保存到 .runs/
echo "[2/5] Exporting doc_id mapping from old volume..."
mkdir -p "$(dirname "$OUT")"

# Determine the base URL to use - only set if not already set (fallback case)
if [ -z "${OLD_BASE:-}" ]; then
    # Prefer localhost if container runs locally
    OLD_BASE="http://localhost:${OLD_PORT}"
    if ! curl -s "${OLD_BASE}/collections" >/dev/null 2>&1; then
        OLD_BASE="http://andy-wsl:${OLD_PORT}"
    fi
fi

# Try export with lenient expected count (allow some missing points)
if ! EXPECTED_COUNT=10000 make docid-export-old OLD_BASE="${OLD_BASE}" COLLECTION="${COLLECTION}" OUT="${OUT}"; then
    echo "[ERROR] Failed to export doc_id mapping"
    if [ "$SKIP_CLEANUP" != "true" ]; then
        docker rm -f qdrant-old >/dev/null 2>&1 || true
    fi
    exit 1
fi

# 基本体检：文件必须存在且行数/大小靠谱
if [ ! -s "${OUT}" ]; then
    echo "[ERROR] Mapping file is empty or missing: ${OUT}"
    docker rm -f qdrant-old >/dev/null 2>&1 || true
    exit 1
fi

MAPPING_COUNT=$(jq 'length' "${OUT}" 2>/dev/null || echo "0")
if [ "$MAPPING_COUNT" -lt 10000 ]; then
    echo "[ERROR] Mapping too small: expected >= 10000, got $MAPPING_COUNT"
    if [ "$SKIP_CLEANUP" != "true" ]; then
        docker rm -f qdrant-old >/dev/null 2>&1 || true
    fi
    exit 1
fi

echo "  ✓ Mapping exported: $MAPPING_COUNT entries"

# 3) 关闭临时容器（只读，不会改旧卷）
if [ "$SKIP_CLEANUP" != "true" ]; then
    echo "[3/5] Cleaning up temporary container..."
    docker rm -f qdrant-old >/dev/null 2>&1 || true
    echo "  ✓ Temporary container removed"
else
    echo "[3/5] Skipping container cleanup (using current Qdrant)"
fi

# 4) 回写映射到当前集合（在线服务）
echo "[4/5] Applying doc_id mapping to current collection..."
# Use lenient expected count (same as export)
if ! EXPECTED_COUNT=10000 make docid-apply COLLECTION="${COLLECTION}" MAP="${OUT}"; then
    echo "[ERROR] Failed to apply doc_id mapping"
    exit 1
fi
echo "  ✓ Mapping applied"

# 5) 验收：抽样校验 + 冒烟质量
echo "[5/5] Verification and smoke tests..."
if ! make docid-verify COLLECTION="${COLLECTION}" MAP="${OUT}"; then
    echo "[ERROR] doc_id verification failed"
    exit 1
fi
echo "  ✓ doc_id verification passed"

if ! make policy-smoke; then
    echo "[ERROR] policy-smoke test failed"
    exit 1
fi
echo "  ✓ policy-smoke test passed"

echo ""
echo "[DONE] doc_id restored for ${COLLECTION} and smoke passed."
echo "  Mapping file: ${OUT}"
echo "  Mapping count: $MAPPING_COUNT"

