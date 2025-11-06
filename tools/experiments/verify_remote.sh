#!/usr/bin/env bash
set -euo pipefail

# Verify that required experiment files exist on remote server

REMOTE=andy-wsl
RDIR=~/searchforge

REMOTE=andy-wsl

# Check for required file
if ssh "${REMOTE}" "test -f \${HOME}/searchforge/experiments/fiqa_suite_runner.py"; then
  echo "✅ fiqa_suite_runner.py exists"
  
  # Show file details
  ssh "${REMOTE}" "ls -lh \${HOME}/searchforge/experiments/fiqa_suite_runner.py"
  
  # Check if file is readable
  if ssh "${REMOTE}" "test -r \${HOME}/searchforge/experiments/fiqa_suite_runner.py"; then
    echo "✅ File is readable"
  else
    echo "❌ File exists but is not readable"
    exit 1
  fi
else
  echo "❌ MISSING: fiqa_suite_runner.py not found on remote"
  echo ""
  echo "Run 'make sync-experiments' to sync files"
  exit 1
fi

echo ""
echo "✅ Verification passed"

# Check matplotlib availability in container
echo ""
echo "🔍 Checking matplotlib availability in container..."
if ssh "${REMOTE}" 'cd ~/searchforge && docker compose exec -T rag-api python -c "import matplotlib,sys;print(matplotlib.__version__);sys.exit(0)"' 2>&1; then
  echo "✅ matplotlib is available"
else
  echo "❌ matplotlib import failed"
  echo "   Run 'make rebuild-api' to install dependencies"
  exit 1
fi

