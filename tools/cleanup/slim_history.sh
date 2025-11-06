#!/usr/bin/env bash
# Slim Git history by removing heavy paths using git-filter-repo
# Usage: I_KNOW_WHAT_IM_DOING=1 bash tools/cleanup/slim_history.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

# Safety check: require explicit confirmation
if [ "${I_KNOW_WHAT_IM_DOING:-}" != "1" ]; then
    echo "❌ Error: This script modifies Git history and requires explicit confirmation."
    echo ""
    echo "⚠️  WARNING: This operation will:"
    echo "   - Rewrite Git history (cannot be undone easily)"
    echo "   - Require force-push to remote"
    echo "   - Affect all collaborators (they must re-clone)"
    echo ""
    echo "To proceed, set the environment variable:"
    echo "   I_KNOW_WHAT_IM_DOING=1 make cleanup-history"
    echo ""
    exit 1
fi

echo "=========================================="
echo "  Git History Slimming"
echo "=========================================="
echo ""
echo "⚠️  WARNING: This will rewrite Git history!"
echo "   - A backup tag will be created"
echo "   - You will need to force-push after this"
echo "   - All collaborators must re-clone"
echo ""

# Check if git-filter-repo is installed
echo "🔍 Checking for git-filter-repo..."
if ! command -v git-filter-repo &> /dev/null; then
    echo "  ❌ git-filter-repo not found"
    echo ""
    echo "  Installing git-filter-repo..."
    echo "  Tip: pip install git-filter-repo"
    echo ""
    
    # Try to install
    if command -v pip3 &> /dev/null; then
        echo "  Attempting to install via pip3..."
        pip3 install git-filter-repo || {
            echo "  ❌ Installation failed. Please install manually:"
            echo "     pip install git-filter-repo"
            exit 1
        }
    elif command -v pip &> /dev/null; then
        echo "  Attempting to install via pip..."
        pip install git-filter-repo || {
            echo "  ❌ Installation failed. Please install manually:"
            echo "     pip install git-filter-repo"
            exit 1
        }
    else
        echo "  ❌ pip not found. Please install git-filter-repo manually:"
        echo "     pip install git-filter-repo"
        exit 1
    fi
fi

if ! command -v git-filter-repo &> /dev/null; then
    echo "  ❌ git-filter-repo still not found after installation attempt"
    exit 1
fi

echo "  ✅ git-filter-repo found"
echo ""

# Create backup tag
BACKUP_TAG="pre-slim-$(date +%Y%m%d)"
echo "📦 Creating backup tag: ${BACKUP_TAG}"
if git tag "${BACKUP_TAG}" 2>/dev/null; then
    echo "  ✅ Tag created: ${BACKUP_TAG}"
else
    echo "  ⚠️  Tag may already exist, continuing..."
fi
echo ""

# Print before size
echo "📊 Git repository size (before):"
BEFORE_SIZE=$(git count-objects -vH)
echo "${BEFORE_SIZE}"
echo ""

# Create migration note
MIGRATION_NOTE=".git-slim-migration-$(date +%Y%m%d-%H%M%S).txt"
cat > "${MIGRATION_NOTE}" << EOF
Git History Slimming Migration Note
===================================

Date: $(date)
Backup Tag: ${BACKUP_TAG}

Removed paths from Git history:
  - artifacts/
  - mlruns/
  - qdrant_storage/
  - *.ipynb
  - *.rdb
  - *.snapshot

Before Size:
${BEFORE_SIZE}

To restore from backup:
  git tag -l "pre-slim-*"
  git checkout <backup-tag>

After force-push, collaborators must:
  1. Backup their work
  2. Delete local repository
  3. Re-clone from remote
EOF

echo "📝 Migration note created: ${MIGRATION_NOTE}"
echo ""

# Run git-filter-repo
echo "🔧 Running git-filter-repo..."
echo "   Removing: artifacts/, mlruns/, qdrant_storage/, *.ipynb, *.rdb, *.snapshot"
echo ""

git filter-repo \
    --path artifacts \
    --path mlruns \
    --path qdrant_storage \
    --path-glob '*.ipynb' \
    --path-glob '*.rdb' \
    --path-glob '*.snapshot' \
    --invert-paths \
    --force

echo ""
echo "✅ git-filter-repo completed"
echo ""

# Run git gc
echo "🧹 Running git garbage collection..."
git gc --aggressive --prune=now
echo "✅ Garbage collection completed"
echo ""

# Print after size
echo "📊 Git repository size (after):"
AFTER_SIZE=$(git count-objects -vH)
echo "${AFTER_SIZE}"
echo ""

# Extract size comparison
BEFORE_PACK=$(echo "${BEFORE_SIZE}" | grep "pack" | awk '{print $3}')
AFTER_PACK=$(echo "${AFTER_SIZE}" | grep "pack" | awk '{print $3}')

echo "=========================================="
echo "  Summary"
echo "=========================================="
echo ""
echo "✅ Backup tag created: ${BACKUP_TAG}"
echo "✅ History slimmed"
echo "✅ Migration note: ${MIGRATION_NOTE}"
echo ""
echo "📊 Size reduction:"
echo "   Before: ${BEFORE_PACK:-N/A}"
echo "   After:  ${AFTER_PACK:-N/A}"
echo ""

echo "⚠️  NEXT STEPS:"
echo ""
echo "1. Verify the changes:"
echo "   git log --all --oneline | head -10"
echo ""
echo "2. Test the build:"
echo "   docker compose build"
echo ""
echo "3. Force-push to remote (DESTRUCTIVE):"
echo "   git push origin --force --all"
echo "   git push origin --force --tags"
echo ""
echo "4. Inform all collaborators to re-clone"
echo ""
echo "⚠️  WARNING: Force-push will rewrite remote history!"
echo "   Make sure all collaborators are aware!"
echo ""


