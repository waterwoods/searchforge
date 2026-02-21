#!/bin/bash
# One-Click Demo Ingest for ChenKui
# =================================
# 1. Auto-pick latest discovery run
# 2. Build URL list from RUN_REVIEW.md (Top 20) or passing.json
# 3. Fetch, extract, embed, upsert to auto_insurance_demo_core
# 4. Run smoke test
#
# Usage: bash scripts/run_demo_ingest_oneclick.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
RUNS_DIR="$REPO_DIR/results/auto_insurance_discovery/runs"
URL_LIST="/tmp/demo_urls.txt"
COLLECTION="auto_insurance_demo_core"
LIMIT=20
MAX_RUNTIME=20

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

# STEP 0: Find latest run + build URL list
echo "[STEP 0] Finding latest run and building URL list..."
LATEST_RUN=""
if [ -d "$RUNS_DIR" ]; then
  LATEST_RUN=$(ls -1d "$RUNS_DIR"/[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]_* 2>/dev/null | sort -r | head -1)
fi

if [ -n "$LATEST_RUN" ] && [ -f "$LATEST_RUN/RUN_REVIEW.md" ]; then
  echo "  Using RUN_REVIEW.md from: $LATEST_RUN"
  python3 -c "
import re
from pathlib import Path
p = Path('$LATEST_RUN/RUN_REVIEW.md')
content = p.read_text(encoding='utf-8')
# Match table rows: | # | Title | URL | ... (same as build_demo_core_collection)
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
print(f'  Extracted {len(urls)} URLs')
" 2>/dev/null || {
    echo "  Fallback: using passing.json"
    python3 -c "
import json
from pathlib import Path
pf = Path('$LATEST_RUN/passing.json') if Path('$LATEST_RUN').exists() else Path('$REPO_DIR/results/auto_insurance_discovery/passing.json')
if pf.exists():
    data = json.loads(pf.read_text())
    urls = [x['url'] for x in sorted(data, key=lambda z: z.get('score',0), reverse=True)[:$LIMIT] if 'url' in x]
else:
    urls = []
Path('$URL_LIST').write_text('\n'.join(urls), encoding='utf-8')
print(f'  Extracted {len(urls)} URLs from passing.json')
" 2>/dev/null
}
elif [ -n "$LATEST_RUN" ] && [ -f "$LATEST_RUN/passing.json" ]; then
  echo "  Using passing.json from: $LATEST_RUN"
  python3 -c "
import json
from pathlib import Path
data = json.loads(Path('$LATEST_RUN/passing.json').read_text())
urls = [x['url'] for x in sorted(data, key=lambda z: z.get('score',0), reverse=True)[:$LIMIT] if 'url' in x]
Path('$URL_LIST').write_text('\n'.join(urls), encoding='utf-8')
print(f'  Extracted {len(urls)} URLs')
"
else
  echo "  No run folder with RUN_REVIEW.md or passing.json, trying parent passing.json..."
  python3 -c "
import json
from pathlib import Path
pf = Path('$REPO_DIR/results/auto_insurance_discovery/passing.json')
if pf.exists():
    data = json.loads(pf.read_text())
    urls = [x['url'] for x in sorted(data, key=lambda z: z.get('score',0), reverse=True)[:$LIMIT] if 'url' in x]
else:
    urls = []
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

# STEP 2: Run ingest
echo "[STEP 2] Running ingest (collection=$COLLECTION, limit=$LIMIT, max-runtime=${MAX_RUNTIME}min)..."
python3 scripts/build_demo_core_collection.py \
  --url-list "$URL_LIST" \
  --collection "$COLLECTION" \
  --limit "$LIMIT" \
  --max-runtime-minutes "$MAX_RUNTIME" \
  --report-dir "$REPO_DIR/results/opencrawl_demo_ingest" \
  || { echo "Ingest failed"; exit 1; }
echo ""

# STEP 3: Smoke test (query Qdrant directly)
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
results = client.search('$COLLECTION', emb, limit=3, with_payload=True)
print('  Top 3 matches:')
for i, r in enumerate(results, 1):
    u = (r.payload or {}).get('url', (r.payload or {}).get('source_url', 'N/A'))
    print(f'    {i}. {str(u)[:70]}...')
" 2>/dev/null || echo "  Smoke test skipped (ensure .env.cloudrun is sourced)"
echo ""

# Summary
echo "=========================================="
echo "One-Click Ingest Complete"
echo "=========================================="
echo "  Run folder: ${LATEST_RUN:-N/A}"
echo "  URL list: $URL_LIST"
echo "  Collection: $COLLECTION"
echo "  Report: $REPO_DIR/results/opencrawl_demo_ingest/INGEST_REPORT.md"
echo ""
echo "If it fails, check:"
echo "  1. QDRANT_URL and QDRANT_API_KEY are set (source .env.cloudrun)"
echo "  2. Latest run has RUN_REVIEW.md or passing.json"
echo "  3. Network allows outbound HTTPS to target URLs"
echo "  4. sentence-transformers, qdrant-client, requests, beautifulsoup4 installed"
echo ""
