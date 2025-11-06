#!/usr/bin/env bash
# Create a clean Git repository snapshot and switch server to it
# Usage: NEW_REPO_URL=<url> bash tools/cleanup/create_clean_repo.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

# Configuration
CLEAN_REPO_DIR="../searchforge-clean"
REMOTE="andy-wsl"
RDIR="~/searchforge"

# Check for required environment variable
if [ -z "${NEW_REPO_URL:-}" ]; then
    echo "❌ Error: NEW_REPO_URL environment variable is required"
    echo ""
    echo "Usage:"
    echo "  NEW_REPO_URL=https://github.com/user/repo.git bash tools/cleanup/create_clean_repo.sh"
    echo ""
    exit 1
fi

echo "=========================================="
echo "  Create Clean Repository Snapshot"
echo "=========================================="
echo ""
echo "Source: ${REPO_ROOT}"
echo "Target: ${CLEAN_REPO_DIR}"
echo "New Remote: ${NEW_REPO_URL}"
echo ""

# Step 1: Create clean snapshot
echo "📦 Step 1: Creating clean snapshot..."
echo ""

# Remove old clean directory if exists
if [ -d "${CLEAN_REPO_DIR}" ]; then
    echo "  ⚠️  Removing existing clean directory..."
    rm -rf "${CLEAN_REPO_DIR}"
fi

# Create clean directory
mkdir -p "${CLEAN_REPO_DIR}"

# Rsync with exclusions
echo "  📋 Syncing files (excluding heavy/regen assets)..."
rsync -av \
    --exclude='.git' \
    --exclude='.venv' \
    --exclude='venv' \
    --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='*.pyo' \
    --exclude='.pytest_cache' \
    --exclude='artifacts' \
    --exclude='mlruns' \
    --exclude='qdrant_storage' \
    --exclude='*.rdb' \
    --exclude='*.snapshot' \
    --exclude='dist' \
    --exclude='.vite' \
    --exclude='dump.rdb' \
    --exclude='archive' \
    --exclude='.DS_Store' \
    --exclude='*.log' \
    --exclude='.idea' \
    --exclude='.vscode' \
    "${REPO_ROOT}/" "${CLEAN_REPO_DIR}/" || {
    echo "  ❌ Rsync failed"
    exit 1
}

echo "  ✅ Clean snapshot created"
echo ""

# Ensure .gitignore and .dockerignore are present and correct
echo "  📝 Ensuring .gitignore and .dockerignore are correct..."

cd "${CLEAN_REPO_DIR}"

# Update .gitignore if needed
if ! grep -q "^node_modules/" .gitignore 2>/dev/null; then
    echo "" >> .gitignore
    echo "# Clean repo exclusions" >> .gitignore
    echo "node_modules/" >> .gitignore
    echo ".venv/" >> .gitignore
    echo "venv/" >> .gitignore
    echo "__pycache__/" >> .gitignore
    echo "*.pyc" >> .gitignore
    echo ".pytest_cache/" >> .gitignore
    echo "artifacts/" >> .gitignore
    echo "mlruns/" >> .gitignore
    echo "qdrant_storage/" >> .gitignore
    echo "*.rdb" >> .gitignore
    echo "*.snapshot" >> .gitignore
    echo "dist/" >> .gitignore
    echo ".vite/" >> .gitignore
fi

# Update .dockerignore if needed
if ! grep -q "^node_modules" .dockerignore 2>/dev/null; then
    echo "" >> .dockerignore
    echo "# Clean repo exclusions" >> .dockerignore
    echo "node_modules/" >> .dockerignore
    echo ".venv/" >> .dockerignore
    echo "venv/" >> .dockerignore
    echo "__pycache__/" >> .dockerignore
    echo "artifacts/" >> .dockerignore
    echo "mlruns/" >> .dockerignore
    echo "qdrant_storage/" >> .dockerignore
    echo "*.rdb" >> .dockerignore
    echo "*.snapshot" >> .dockerignore
fi

echo "  ✅ Git ignore files updated"
echo ""

# Step 2: Initialize and push
echo "📤 Step 2: Initializing Git repository and pushing..."
echo ""

# Initialize Git
git init
git add -A
git commit -m "init: clean snapshot from SearchForge"

# Rename branch to main
git branch -M main

# Add remote
git remote add origin "${NEW_REPO_URL}"

# Push
echo "  📤 Pushing to ${NEW_REPO_URL}..."
git push -u origin main

echo "  ✅ Repository pushed"
echo ""

# Step 3: Server switch
echo "🖥️  Step 3: Switching server to new remote..."
echo ""

# Check if server has existing repo
echo "  🔍 Checking server state..."
if ssh "${REMOTE}" "cd ${RDIR} && if [ -d .git ]; then echo 'exists'; else echo 'none'; fi" 2>/dev/null | grep -q "exists"; then
    echo "  📝 Updating existing repository..."
    ssh "${REMOTE}" "cd ${RDIR} && \
        git remote set-url origin ${NEW_REPO_URL} && \
        git fetch origin && \
        git reset --hard origin/main"
else
    echo "  📥 Cloning new repository..."
    ssh "${REMOTE}" "rm -rf ${RDIR} && git clone ${NEW_REPO_URL} ${RDIR}"
fi

echo "  ✅ Server switched"
echo ""

# Build on server
echo "🔨 Step 4: Building on server..."
echo ""

ssh "${REMOTE}" "cd ${RDIR} && \
    docker compose build rag-api && \
    docker compose up -d rag-api"

echo "  ✅ Build completed"
echo ""

# Wait for service to be ready
echo "⏳ Waiting for service to be ready..."
sleep 10

# Step 5: Health check
echo "🏥 Step 5: Health check..."
echo ""

HEALTH_CHECK=$(curl -fsS http://${REMOTE}:8000/health 2>/dev/null || echo "FAILED")

if [ "${HEALTH_CHECK}" != "FAILED" ]; then
    echo "  ✅ Health check passed: ${HEALTH_CHECK}"
else
    echo "  ❌ Health check failed"
    echo "     Service may still be starting. Please check manually."
fi

echo ""

# Final summary
echo "=========================================="
echo "  Summary"
echo "=========================================="
echo ""

CLEAN_SIZE=$(du -sh "${CLEAN_REPO_DIR}" 2>/dev/null | awk '{print $1}')
CLEAN_COMMIT=$(cd "${CLEAN_REPO_DIR}" && git rev-parse --short HEAD 2>/dev/null || echo "N/A")

echo "✅ Clean repository created:"
echo "   Location: ${CLEAN_REPO_DIR}"
echo "   Size: ${CLEAN_SIZE}"
echo "   Commit: ${CLEAN_COMMIT}"
echo ""
echo "✅ Server switched to new remote"
echo "   Remote: ${NEW_REPO_URL}"
echo "   Health: ${HEALTH_CHECK}"
echo ""
echo "📋 Old repository remains intact at: ${REPO_ROOT}"
echo ""
echo "🔄 To rollback server:"
echo "   ssh ${REMOTE} 'cd ${RDIR} && git remote set-url origin <OLD_REPO_URL> && git fetch && git reset --hard origin/<old-branch> && docker compose up -d'"
echo ""


