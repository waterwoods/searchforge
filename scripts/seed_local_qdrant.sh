#!/bin/bash
# Seed auto_insurance_demo_core into LOCAL Qdrant (no Cloud secrets needed)
# =========================================================================
# Use when Qdrant Cloud is unavailable (404/paused) and you want live demo.
# Requires: docker compose up -d qdrant, discovery passing.json, sentence-transformers
#
# Usage: bash scripts/seed_local_qdrant.sh
#
# After: USE_LOCAL_QDRANT=1 bash scripts/run_demo_local.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
RUNS_DIR="$REPO_DIR/results/auto_insurance_discovery/runs"
PASSING_PARENT="$REPO_DIR/results/auto_insurance_discovery/passing.json"
URL_LIST="/tmp/demo_urls_local.txt"
COLLECTION="auto_insurance_demo_core"
LIMIT=30
MAX_RUNTIME=20

cd "$REPO_DIR"

# Force local Qdrant (no Cloud) - overrides .env.cloudrun
export USE_LOCAL_QDRANT=1
unset QDRANT_URL
unset QDRANT_API_KEY
export QDRANT_HOST="${QDRANT_HOST:-localhost}"
export QDRANT_PORT="${QDRANT_PORT:-6333}"

echo "=========================================="
echo "Seed Local Qdrant (auto_insurance_demo_core)"
echo "=========================================="
echo "  Qdrant: $QDRANT_HOST:$QDRANT_PORT (local)"
echo ""

# 0. Ensure Qdrant is running
echo "[0] Checking local Qdrant..."
if ! curl -sf --max-time 3 "http://$QDRANT_HOST:$QDRANT_PORT/collections" > /dev/null 2>&1; then
  echo "  FAIL: Qdrant not reachable at $QDRANT_HOST:$QDRANT_PORT"
  echo ""
  echo "  Start it: docker compose up -d qdrant"
  echo "  Then re-run this script."
  exit 1
fi
echo "  OK: Qdrant running"
echo ""

# 1. Build URL list from passing.json
echo "[1] Building URL list..."
SELECTED_RUN=""
if [ -d "$RUNS_DIR" ]; then
  SELECTED_RUN=$(ls -1d "$RUNS_DIR"/[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]_* 2>/dev/null | sort -r | head -1)
fi

if [ -n "$SELECTED_RUN" ] && [ -f "$SELECTED_RUN/passing.json" ]; then
  echo "  Using run: $SELECTED_RUN"
  python3 -c "
import json
from pathlib import Path
data = json.loads(Path('$SELECTED_RUN/passing.json').read_text())
urls = [x['url'] for x in sorted(data, key=lambda z: z.get('score',0), reverse=True)[:$LIMIT] if 'url' in x]
Path('$URL_LIST').write_text('\n'.join(urls), encoding='utf-8')
print(f'  Extracted {len(urls)} URLs')
"
elif [ -f "$PASSING_PARENT" ]; then
  echo "  Using parent passing.json"
  python3 -c "
import json
from pathlib import Path
data = json.loads(Path('$PASSING_PARENT').read_text())
urls = [x['url'] for x in sorted(data, key=lambda z: z.get('score',0), reverse=True)[:$LIMIT] if 'url' in x]
Path('$URL_LIST').write_text('\n'.join(urls), encoding='utf-8')
print(f'  Extracted {len(urls)} URLs')
"
else
  echo "  ERROR: No passing.json found."
  echo "  Expected: $PASSING_PARENT or $RUNS_DIR/*/passing.json"
  echo ""
  echo "  Run discovery first: bash scripts/discover_auto_insurance_sources.py (or similar)"
  exit 1
fi

URL_COUNT=$(wc -l < "$URL_LIST" 2>/dev/null || echo 0)
if [ "$URL_COUNT" -lt 5 ]; then
  echo "  ERROR: Too few URLs ($URL_COUNT). Need at least 5."
  exit 1
fi
echo ""

# 2. Run ingest (build_demo_core_collection uses QDRANT_HOST/PORT when QDRANT_URL unset)
echo "[2] Ingesting to local Qdrant (collection=$COLLECTION, limit=$LIMIT)..."
INGEST_TIMESTAMP=$(date +%Y-%m-%d_%H%M%S)
REPORT_DIR="$REPO_DIR/results/opencrawl_demo_ingest/local_$INGEST_TIMESTAMP"
mkdir -p "$REPORT_DIR"

python3 scripts/build_demo_core_collection.py \
  --url-list "$URL_LIST" \
  --collection "$COLLECTION" \
  --limit "$LIMIT" \
  --max-runtime-minutes "$MAX_RUNTIME" \
  --report-dir "$REPORT_DIR" \
  --recreate \
  || { echo "Ingest failed"; exit 1; }
echo ""

# 3. Quick smoke
echo "[3] Smoke test..."
python3 -c "
import os
import sys
sys.path.insert(0, '$REPO_DIR')
from qdrant_client import QdrantClient
client = QdrantClient(host='$QDRANT_HOST', port=$QDRANT_PORT)
info = client.get_collection('$COLLECTION')
print(f'  Collection points: {info.points_count}')
" 2>/dev/null || echo "  Smoke skipped"
echo ""

echo "=========================================="
echo "Local Qdrant seeded"
echo "=========================================="
echo "  Collection: $COLLECTION"
echo "  Report: $REPORT_DIR/INGEST_REPORT.md"
echo ""
echo "  Next: USE_LOCAL_QDRANT=1 bash scripts/run_demo_local.sh"
echo ""
