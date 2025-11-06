#!/usr/bin/env bash
# Switch to remote SearchForge target

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$WORKSPACE_ROOT"

REMOTE=${REMOTE:-andy-wsl}
COMPOSE_DIR=${COMPOSE_DIR:-~/searchforge}
PROJECT=${PROJECT:-searchforge}

echo "=================================================="
echo "🔄 Switching to Remote Target"
echo "=================================================="
echo ""

# Step 0: Update /etc/hosts for hostname resolution
echo "[0/6] Updating /etc/hosts for hostname resolution..."
if bash tools/switch/update_hosts.sh; then
    echo "✅ Hostname resolution configured"
else
    echo "⚠️  Warning: Failed to update /etc/hosts (continuing anyway)"
    echo "   You may need to manually add: $(ssh -G "$REMOTE" 2>/dev/null | awk '/^hostname /{print $2}') $REMOTE"
fi
echo ""

# Step 1: Freeze writers (idempotent)
echo "[1/5] Freezing local writers..."
if [ -f "./migration_freeze_writers.sh" ]; then
    bash ./migration_freeze_writers.sh || {
        echo "⚠️  Warning: writer freeze script encountered issues (continuing anyway)"
    }
else
    echo "⚠️  Warning: migration_freeze_writers.sh not found (skipping freeze step)"
fi
echo ""

# Step 2: Verify remote compose is running
echo "[2/6] Verifying remote compose services..."
REMOTE_COMPOSE="cd $COMPOSE_DIR && docker compose -p $PROJECT ps"
if ssh "$REMOTE" "$REMOTE_COMPOSE" >/dev/null 2>&1; then
    echo "✅ Remote compose services verified"
    ssh "$REMOTE" "$REMOTE_COMPOSE"
elif ssh "$REMOTE" "cd $COMPOSE_DIR && docker compose ps" >/dev/null 2>&1; then
    echo "✅ Remote compose services verified (without project name)"
    ssh "$REMOTE" "cd $COMPOSE_DIR && docker compose ps"
else
    echo "⚠️  Warning: Cannot verify remote compose services (continuing anyway)"
    echo "   Make sure remote services are running manually"
fi
echo ""

# Step 3: Copy .env.remote.template -> .env.current
echo "[3/6] Setting up .env.current from remote template..."
if [ ! -f ".env.remote.template" ]; then
    echo "❌ Error: .env.remote.template not found"
    exit 1
fi
cp .env.remote.template .env.current
echo "✅ .env.current created from .env.remote.template"
echo ""

# Step 4: Stop local containers (preserve volumes)
echo "[4/6] Stopping local containers (preserving volumes)..."
docker compose --env-file .env.current -p "$PROJECT" down
echo "✅ Local containers stopped"
echo ""

# Step 5: Print target and verify config
echo "[5/6] Verifying configuration..."
echo ""
echo "Current target:"
bash tools/switch/print_target.sh
echo ""
echo "Service endpoints from .env.current:"
docker compose --env-file .env.current -p "$PROJECT" config 2>/dev/null | grep -E 'RAG_API_BASE|QDRANT_URL' || echo "⚠️  Note: RAG_API_BASE/QDRANT_URL may be set via environment variables"
echo ""

# Step 6: Remote health checks
echo "[6/6] Performing remote health checks..."
if curl -fsS --max-time 5 "http://${REMOTE}:8000/health" >/dev/null 2>&1; then
    echo "✅ Remote rag-api /health check passed"
else
    echo "⚠️  Warning: Remote rag-api /health check failed"
    echo "   This may be normal if services are still starting up"
fi

if curl -fsS --max-time 5 "http://${REMOTE}:6333/collections" >/dev/null 2>&1; then
    echo "✅ Remote qdrant /collections check passed"
else
    echo "⚠️  Warning: Remote qdrant /collections check failed"
    echo "   This may be normal if services are still starting up"
fi
echo ""

echo "=================================================="
echo "✅ Switch to remote complete!"
echo "=================================================="
