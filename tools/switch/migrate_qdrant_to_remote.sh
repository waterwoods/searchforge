#!/usr/bin/env bash
# Migrate Qdrant collections from local to remote

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$WORKSPACE_ROOT"

REMOTE=${REMOTE:-andy-wsl}
COMPOSE_DIR=${COMPOSE_DIR:-~/searchforge}
PROJECT=${PROJECT:-searchforge}
LOCAL_VOLUME=${LOCAL_VOLUME:-searchforge_qdrant_data}
REMOTE_VOLUME=${REMOTE_VOLUME:-searchforge_qdrant_data}

echo "=================================================="
echo "🔄 Migrating Qdrant Collections to Remote"
echo "=================================================="
echo ""

# Step 1: Verify local volume has collections
echo "[1/6] Checking local Qdrant volume..."
LOCAL_COLLECTIONS=$(docker run --rm -v "${LOCAL_VOLUME}:/data" alpine ls -1 /data/collections 2>/dev/null | grep -v "^$" | wc -l | tr -d ' ')

if [ "$LOCAL_COLLECTIONS" -eq 0 ]; then
    echo "❌ Error: No collections found in local volume '${LOCAL_VOLUME}'"
    exit 1
fi

echo "✅ Found $LOCAL_COLLECTIONS collections in local volume"
docker run --rm -v "${LOCAL_VOLUME}:/data" alpine ls -1 /data/collections 2>/dev/null | sed 's/^/   - /'
echo ""

# Step 2: Check remote Qdrant status
echo "[2/6] Checking remote Qdrant status..."
REMOTE_CONTAINER="searchforge-qdrant-1"
if ssh "$REMOTE" "docker ps --format '{{.Names}}' | grep -q '^${REMOTE_CONTAINER}$'" 2>/dev/null; then
    echo "⚠️  Remote Qdrant is running. It needs to be stopped for data migration."
    echo "   Stopping remote Qdrant container..."
    ssh "$REMOTE" "cd $COMPOSE_DIR && docker compose -p $PROJECT stop qdrant" || {
        ssh "$REMOTE" "docker stop $REMOTE_CONTAINER" || true
    }
    sleep 2
    echo "✅ Remote Qdrant stopped"
else
    echo "✅ Remote Qdrant is not running"
fi
echo ""

# Step 3: Create backup of remote volume (if it has data)
echo "[3/6] Creating backup of remote volume (if needed)..."
REMOTE_HAS_DATA=$(ssh "$REMOTE" "docker run --rm -v ${REMOTE_VOLUME}:/data alpine ls -1 /data/collections 2>/dev/null | wc -l | tr -d ' '" || echo "0")

if [ "$REMOTE_HAS_DATA" -gt "0" ]; then
    BACKUP_NAME="qdrant_backup_$(date +%Y%m%d_%H%M%S)"
    echo "⚠️  Remote volume has data. Creating backup: $BACKUP_NAME"
    ssh "$REMOTE" "docker run --rm -v ${REMOTE_VOLUME}:/data -v /tmp:/backup alpine tar czf /backup/${BACKUP_NAME}.tar.gz -C /data ." || {
        echo "⚠️  Warning: Failed to create backup (continuing anyway)"
    }
    echo "✅ Backup created (if successful, located at /tmp/${BACKUP_NAME}.tar.gz on remote)"
else
    echo "✅ Remote volume is empty, no backup needed"
fi
echo ""

# Step 4: Export local volume data
echo "[4/6] Exporting local Qdrant data..."
TEMP_TAR_NAME="qdrant_migrate_$(date +%s).tar.gz"
TEMP_TAR="/tmp/${TEMP_TAR_NAME}"
docker run --rm -v "${LOCAL_VOLUME}:/data" -v "/tmp:/backup" alpine tar czf "/backup/${TEMP_TAR_NAME}" -C /data . || {
    echo "❌ Error: Failed to export local volume data"
    exit 1
}
LOCAL_TAR="$TEMP_TAR"
echo "✅ Local data exported to: $TEMP_TAR"
echo ""

# Step 5: Copy data to remote and import
echo "[5/6] Copying data to remote and importing..."
echo "   This may take a while depending on data size..."
rsync -avzP "$LOCAL_TAR" "${REMOTE}:${TEMP_TAR}" || {
    echo "❌ Error: Failed to copy data to remote"
    rm -f "$LOCAL_TAR"
    exit 1
}
echo "   Data copied to remote"

# Import into remote volume
ssh "$REMOTE" "docker run --rm -v ${REMOTE_VOLUME}:/data -v /tmp:/backup alpine sh -c 'cd /data && rm -rf * && tar xzf /backup/${TEMP_TAR_NAME} && rm /backup/${TEMP_TAR_NAME}'" || {
    echo "❌ Error: Failed to import data into remote volume"
    rm -f "$LOCAL_TAR"
    exit 1
}
echo "   Data imported into remote volume"

# Cleanup local temp file
rm -f "$LOCAL_TAR"
echo "✅ Data migration completed"
echo ""

# Step 6: Restart remote Qdrant
echo "[6/6] Restarting remote Qdrant..."
ssh "$REMOTE" "cd $COMPOSE_DIR && docker compose -p $PROJECT up -d qdrant" || {
    ssh "$REMOTE" "docker start $REMOTE_CONTAINER" || {
        echo "❌ Error: Failed to restart remote Qdrant"
        echo "   Please manually restart: ssh $REMOTE 'cd $COMPOSE_DIR && docker compose -p $PROJECT up -d qdrant'"
        exit 1
    }
}

echo "   Waiting for Qdrant to be ready..."
sleep 5

# Verify collections
MAX_WAIT=30
WAIT_COUNT=0
while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    if curl -fsS "http://${REMOTE}:6333/collections" >/dev/null 2>&1; then
        REMOTE_COLLECTIONS=$(curl -fsS "http://${REMOTE}:6333/collections" 2>/dev/null | python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data.get('result', {}).get('collections', [])))" 2>/dev/null || echo "0")
        if [ "$REMOTE_COLLECTIONS" -gt "0" ]; then
            echo "✅ Remote Qdrant is ready with $REMOTE_COLLECTIONS collections"
            curl -fsS "http://${REMOTE}:6333/collections" 2>/dev/null | python3 -c "import sys, json; data = json.load(sys.stdin); cols = data.get('result', {}).get('collections', []); [print(f'   - {c[\"name\"]}') for c in cols]" 2>/dev/null
            break
        fi
    fi
    sleep 1
    WAIT_COUNT=$((WAIT_COUNT + 1))
done

if [ $WAIT_COUNT -eq $MAX_WAIT ]; then
    echo "⚠️  Warning: Remote Qdrant may not be fully ready yet"
    echo "   Please check manually: curl http://${REMOTE}:6333/collections"
fi

echo ""
echo "=================================================="
echo "✅ Migration Complete!"
echo "=================================================="
echo ""
echo "Summary:"
echo "  - Migrated $LOCAL_COLLECTIONS collections from local to remote"
echo "  - Remote Qdrant is running at http://${REMOTE}:6333"
echo ""
echo "Next steps:"
echo "  1. Verify collections: curl http://${REMOTE}:6333/collections"
echo "  2. Test a collection: curl http://${REMOTE}:6333/collections/<collection_name>"
