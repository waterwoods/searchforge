#!/usr/bin/env bash
set -euo pipefail

# Sync experiments directory to remote server
# This ensures the container has access to experiment scripts via bind mount

REMOTE=andy-wsl

echo "🔄 Syncing experiments directory to ${REMOTE}:\${HOME}/searchforge/experiments/"

# Ensure remote experiments directory exists with correct permissions
ssh "${REMOTE}" "mkdir -p \${HOME}/searchforge/experiments && sudo chown -R \$(whoami):\$(whoami) \${HOME}/searchforge/experiments 2>/dev/null || true"

# Ensure local experiments directory exists
mkdir -p experiments

# Sync experiments directory (excluding cache and system files)
rsync -avz --delete \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude '.DS_Store' \
  --exclude '*.swp' \
  --exclude '.git' \
  experiments/ "${REMOTE}:\${HOME}/searchforge/experiments/"

# Verify sync by listing remote directory
echo ""
echo "✅ Sync complete. Remote directory contents:"
ssh "${REMOTE}" "ls -lh \${HOME}/searchforge/experiments/ | head -20"

# Check for required file
if ssh "${REMOTE}" "test -f \${HOME}/searchforge/experiments/fiqa_suite_runner.py"; then
  echo ""
  echo "✅ Required file fiqa_suite_runner.py found on remote"
else
  echo ""
  echo "⚠️  WARNING: fiqa_suite_runner.py not found on remote"
  exit 1
fi

