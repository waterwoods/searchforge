#!/usr/bin/env bash
set -euo pipefail

CONTAINER=$(docker compose ps -q rag-api)
RUNS_DIR="/app/.runs"

echo "=== 验证 metrics.json ==="
BAD=0
for f in $(docker exec "$CONTAINER" bash -lc "find $RUNS_DIR -maxdepth 2 -name metrics.json 2>/dev/null"); do
  # Extract file content
  CONTENT=$(docker exec "$CONTAINER" bash -lc "cat $f" | python3 -m json.tool 2>/dev/null)
  
  SOURCE=$(echo "$CONTENT" | python3 -c "import sys,json; print(json.load(sys.stdin)['source'])" 2>/dev/null || echo "unknown")
  RECALL=$(echo "$CONTENT" | python3 -c "import sys,json; print(json.load(sys.stdin)['metrics']['recall_at_10'])" 2>/dev/null || echo "0")
  P95=$(echo "$CONTENT" | python3 -c "import sys,json; print(json.load(sys.stdin)['metrics']['p95_ms'])" 2>/dev/null || echo "0")
  
  echo "[GUARD] $f | source=$SOURCE | recall@10=$RECALL | p95_ms=$P95"
  
  if python3 -c "import sys; r=float('$RECALL'); p=float('$P95'); sys.exit(0 if r>0 and p>0 else 1)" 2>/dev/null; then
    echo "  ✅ OK"
  else
    echo "  ❌ FAIL: recall@10=$RECALL or p95_ms=$P95 is not > 0"
    BAD=1
  fi
  
  # Check source is "runner"
  if [ "$SOURCE" != "runner" ]; then
    echo "  ❌ FAIL: source is '$SOURCE', expected 'runner'"
    BAD=1
  fi
done

if [ $BAD -eq 0 ]; then
  echo "[GUARD] ✅ All metrics valid"
else
  echo "[GUARD] ❌ Some metrics invalid"
  exit 1
fi

echo ""
echo "=== 生成 winners.json ==="
docker exec "$CONTAINER" bash -lc "cd /app && python3 -c \"
import json, sys
from pathlib import Path

runs_dir = Path('$RUNS_DIR')
all_items = []

for job_dir in runs_dir.iterdir():
    if not job_dir.is_dir():
        continue
    metrics_file = job_dir / 'metrics.json'
    if not metrics_file.exists():
        continue
    
    with open(metrics_file) as f:
        metrics = json.load(f)
    
    if 'metrics' in metrics:
        metrics_data = metrics.get('metrics', {})
        config = metrics.get('config', {})
        source = metrics.get('source', 'unknown')
        
        if metrics_data.get('recall_at_10', 0) > 0 and metrics_data.get('p95_ms', 0) > 0:
            all_items.append({
                'job_id': job_dir.name,
                'top_k': config.get('top_k'),
                'fast_mode': config.get('fast_mode', False),
                'dataset_name': config.get('dataset'),
                'qrels_name': config.get('qrels'),
                'recall_at_10': metrics_data.get('recall_at_10', 0.0),
                'p95_ms': metrics_data.get('p95_ms', 0.0),
                'qps': metrics_data.get('qps', 0.0),
                'source': source,
                'status': 'SUCCEEDED'
            })

# Find winners
if all_items:
    best_quality = max(all_items, key=lambda x: x.get('recall_at_10', 0))
    latency_candidates = [x for x in all_items if x.get('p95_ms', 1e9) > 0]
    best_latency = min(latency_candidates, key=lambda x: x.get('p95_ms', 1e9)) if latency_candidates else best_quality
    balanced = max(all_items, key=lambda x: (x.get('recall_at_10', 0)) - 0.0005 * (x.get('p95_ms', 0)))
    
    winners = {
        'winners': {
            'quality': best_quality,
            'latency': best_latency,
            'balanced': balanced
        },
        'all': all_items
    }
else:
    winners = {
        'winners': {'quality': {}, 'latency': {}, 'balanced': {}},
        'all': []
    }

# Write winners.json
Path('/app/reports').mkdir(parents=True, exist_ok=True)
with open('/app/reports/winners.json', 'w') as f:
    json.dump(winners, f, indent=2, ensure_ascii=False)

print(f'✅ Winners written to /app/reports/winners.json')
print(f'Found {len(all_items)} jobs with valid metrics')
if winners['winners']['quality']:
    q = winners['winners']['quality']
    print(f'Best Quality: {q[\"job_id\"]} - Recall@10={q.get(\"recall_at_10\", 0):.4f}, P95={q.get(\"p95_ms\", 0):.1f}ms')
if winners['winners']['latency']:
    l = winners['winners']['latency']
    print(f'Best Latency: {l[\"job_id\"]} - Recall@10={l.get(\"recall_at_10\", 0):.4f}, P95={l.get(\"p95_ms\", 0):.1f}ms')
if winners['winners']['balanced']:
    b = winners['winners']['balanced']
    print(f'Best Balanced: {b[\"job_id\"]} - Recall@10={b.get(\"recall_at_10\", 0):.4f}, P95={b.get(\"p95_ms\", 0):.1f}ms')
\""

echo ""
echo "=== 最终汇总 ==="
docker exec "$CONTAINER" bash -lc "cat /app/reports/winners.json" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('1. Source验证: 所有 metrics.json 的 source 必须是 \"runner\"')
all_source_runner = all(item.get('source') == 'runner' for item in d.get('all', []))
print(f'   {'✅ 通过' if all_source_runner else '❌ 失败'}')

print('2. 非零指标验证: recall_at_10 与 p95_ms 必须 > 0')
all_nonzero = all(item.get('recall_at_10', 0) > 0 and item.get('p95_ms', 0) > 0 for item in d.get('all', []))
print(f'   {'✅ 通过' if all_nonzero else '❌ 失败'}')

print('3. Winners 报告:')
winners = d.get('winners', {})
if winners.get('quality'):
    q = winners['quality']
    print(f'   Quality: {q[\"job_id\"]} - Recall@10={q.get(\"recall_at_10\", 0):.4f}, P95={q.get(\"p95_ms\", 0):.1f}ms')
if winners.get('latency'):
    l = winners['latency']
    print(f'   Latency: {l[\"job_id\"]} - Recall@10={l.get(\"recall_at_10\", 0):.4f}, P95={l.get(\"p95_ms\", 0):.1f}ms')
if winners.get('balanced'):
    b = winners['balanced']
    print(f'   Balanced: {b[\"job_id\"]} - Recall@10={b.get(\"recall_at_10\", 0):.4f}, P95={b.get(\"p95_ms\", 0):.1f}ms')
"

