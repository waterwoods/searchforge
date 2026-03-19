#!/bin/bash
# One-Click Demo Ingest for ChenKui
# =================================
# 1. Use --run-dir or auto-pick latest discovery run
# 2. Build URL list from RUN_REVIEW.md (Top 20 table) or passing.json (top-N by score)
# 3. Fetch, extract, embed, upsert to auto_insurance_demo_core
# 4. Run smoke test
#
# Usage: bash scripts/run_demo_ingest_oneclick.sh [--run-dir <path>]
#   --run-dir: specific run folder (e.g. results/auto_insurance_discovery/runs/2026-02-21_105716)
#   If omitted: auto-picks latest run under results/auto_insurance_discovery/runs/

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
RUNS_DIR="$REPO_DIR/results/auto_insurance_discovery/runs"
URL_LIST="/tmp/demo_urls.txt"
COLLECTION="auto_insurance_demo_core"
LIMIT=30
MAX_RUNTIME=20

# Parse --run-dir
RUN_DIR=""
while [[ $# -gt 0 ]]; do
  case $1 in
    --run-dir)
      RUN_DIR="$2"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

cd "$REPO_DIR"

# Load env
if [ -f ".env" ]; then
  set -a
  source .env
  set +a
fi
if [ -f ".env.cloudrun" ]; then
  set -a
  source .env.cloudrun
  set +a
fi

echo "=========================================="
echo "One-Click Demo Ingest"
echo "=========================================="
echo ""

# STEP 0: Resolve run dir + build URL list
echo "[STEP 0] Resolving run dir and building URL list..."
if [ -n "$RUN_DIR" ]; then
  if [[ "$RUN_DIR" != /* ]]; then
    RUN_DIR="$REPO_DIR/$RUN_DIR"
  fi
  SELECTED_RUN="$RUN_DIR"
  echo "  Using --run-dir: $SELECTED_RUN"
else
  SELECTED_RUN=""
  if [ -d "$RUNS_DIR" ]; then
    SELECTED_RUN=$(ls -1d "$RUNS_DIR"/[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]_* 2>/dev/null | sort -r | head -1)
  fi
  echo "  Auto-picked latest run: ${SELECTED_RUN:-N/A}"
fi

if [ -z "$SELECTED_RUN" ] || [ ! -d "$SELECTED_RUN" ]; then
  echo "ERROR: No run directory found. Use --run-dir <path> or ensure runs exist under $RUNS_DIR"
  exit 1
fi

# Build URL list: RUN_REVIEW.md Top 20 table if present and sufficient; else passing.json (top-N by score)
# Use passing.json for top 30 to ensure insurer-domain mix (RUN_REVIEW Top 20 is often gov-heavy)
if [ -f "$SELECTED_RUN/passing.json" ]; then
  echo "  Using passing.json (top $LIMIT by score) for insurer+gov mix..."
  python3 -c "
import json
from pathlib import Path
data = json.loads(Path('$SELECTED_RUN/passing.json').read_text())
urls = [x['url'] for x in sorted(data, key=lambda z: z.get('score',0), reverse=True)[:$LIMIT] if 'url' in x]
Path('$URL_LIST').write_text('\n'.join(urls), encoding='utf-8')
print(f'  Extracted {len(urls)} URLs from passing.json')
"
elif [ -f "$SELECTED_RUN/RUN_REVIEW.md" ]; then
  echo "  Extracting from RUN_REVIEW.md Top 20 table..."
  python3 -c "
import re
from pathlib import Path
p = Path('$SELECTED_RUN/RUN_REVIEW.md')
content = p.read_text(encoding='utf-8')
pattern = r'\|[^|]+\|[^|]+\|\s*(https?://[^\s\|]+)'
urls = []
for m in re.finditer(pattern, content):
    u = m.group(1).rstrip('|').strip()
    if u and u not in urls:
        urls.append(u)
if len(urls) < 5:
    for m in re.finditer(r'https?://[^\s\|\)]+', content):
        u = m.group(0).rstrip('|)').strip()
        if u and u not in urls:
            urls.append(u)
urls = urls[:$LIMIT]
Path('$URL_LIST').write_text('\n'.join(urls), encoding='utf-8')
print(f'  Extracted {len(urls)} URLs from RUN_REVIEW.md')
" 2>/dev/null || true
fi

if [ ! -s "$URL_LIST" ] && [ -f "$REPO_DIR/results/auto_insurance_discovery/passing.json" ]; then
  echo "  Fallback: using parent passing.json"
  python3 -c "
import json
from pathlib import Path
data = json.loads(Path('$REPO_DIR/results/auto_insurance_discovery/passing.json').read_text())
urls = [x['url'] for x in sorted(data, key=lambda z: z.get('score',0), reverse=True)[:$LIMIT] if 'url' in x]
Path('$URL_LIST').write_text('\n'.join(urls), encoding='utf-8')
print(f'  Extracted {len(urls)} URLs')
"
fi

URL_COUNT=$(wc -l < "$URL_LIST" 2>/dev/null || echo 0)
if [ "$URL_COUNT" -lt 1 ]; then
  echo "ERROR: No URLs in $URL_LIST. Ensure discovery has run and RUN_REVIEW.md or passing.json exists."
  exit 1
fi
echo "  URL list: $URL_LIST ($URL_COUNT URLs)"
echo ""

# STEP 1: Check Qdrant env
echo "[STEP 1] Checking Qdrant config..."
python3 scripts/check_qdrant_env.py || {
  echo ""
  echo "To fix: export QDRANT_URL and QDRANT_API_KEY (see .env.example)"
  exit 1
}
echo ""

# Timestamped report dir
INGEST_TIMESTAMP=$(date +%Y-%m-%d_%H%M%S)
REPORT_DIR="$REPO_DIR/results/opencrawl_demo_ingest/$INGEST_TIMESTAMP"
RUN_ID=$(basename "$SELECTED_RUN")

# STEP 2: Run ingest
echo "[STEP 2] Running ingest (collection=$COLLECTION, limit=$LIMIT, max-runtime=${MAX_RUNTIME}min)..."
python3 scripts/build_demo_core_collection.py \
  --url-list "$URL_LIST" \
  --collection "$COLLECTION" \
  --limit "$LIMIT" \
  --max-runtime-minutes "$MAX_RUNTIME" \
  --report-dir "$REPORT_DIR" \
  --report-run-dir "$RUN_ID" \
  --recreate \
  || { echo "Ingest failed"; exit 1; }
echo ""

# STEP 3: Smoke test (query Qdrant directly, top 5 for insurer citation check)
echo "[STEP 3] Smoke test..."
python3 -c "
import os
import sys
sys.path.insert(0, '$REPO_DIR')
from qdrant_client import QdrantClient
url = os.getenv('QDRANT_URL')
key = os.getenv('QDRANT_API_KEY')
if not url:
    print('  QDRANT_URL not set, skip smoke test')
    sys.exit(0)
try:
    from fastembed import TextEmbedding
    model = TextEmbedding(model_name='BAAI/bge-small-en-v1.5')
    emb = list(model.embed(['California auto insurance requirements']))[0]
except Exception:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    emb = model.encode(['California auto insurance requirements'])[0].tolist()
client = QdrantClient(url=url, api_key=key or None)
results = client.search('$COLLECTION', emb, limit=5, with_payload=True)
print('  Top 5 matches:')
insurer_domains = ['geico.com', 'progressive.com', 'nationwide.com', 'travelers.com', 'libertymutual.com', 'usaa.com']
insurer_count = 0
for i, r in enumerate(results, 1):
    payload = r.payload or {}
    u = payload.get('url', payload.get('source_url', 'N/A'))
    domain = payload.get('domain', '')
    snippet = (payload.get('text', '') or '')[:120].replace(chr(10), ' ')
    is_insurer = any(d in domain for d in insurer_domains)
    if is_insurer:
        insurer_count += 1
    print(f'    {i}. {str(u)[:75]}')
    print(f'       domain={domain} {\"(insurer)\" if is_insurer else \"\"}')
    print(f'       snippet: {snippet}...')
print(f'  Insurer-domain citations in top 5: {insurer_count}')
" 2>/dev/null || echo "  Smoke test skipped (ensure .env.cloudrun is sourced)"
echo ""

# Summary
echo "=========================================="
echo "One-Click Ingest Complete"
echo "=========================================="
echo "  Run folder: $SELECTED_RUN"
echo "  Run ID: $RUN_ID"
echo "  URL list: $URL_LIST"
echo "  Collection: $COLLECTION"
echo "  Report: $REPORT_DIR/INGEST_REPORT.md"
echo ""
echo "If it fails, check:"
echo "  1. QDRANT_URL and QDRANT_API_KEY are set (source .env.cloudrun)"
echo "  2. Latest run has RUN_REVIEW.md or passing.json"
echo "  3. Network allows outbound HTTPS to target URLs"
echo "  4. sentence-transformers, qdrant-client, requests, beautifulsoup4 installed"
echo ""
