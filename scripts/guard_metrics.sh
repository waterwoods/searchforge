#!/usr/bin/env bash
set -euo pipefail

RUNS_DIR="/app/.runs"
bad=0

for f in $(find "$RUNS_DIR" -maxdepth 2 -name metrics.json 2>/dev/null); do
  r=$(jq -r '.metrics.recall_at_10 // 0' "$f" 2>/dev/null || echo "0")
  p=$(jq -r '.metrics.p95_ms // 0' "$f" 2>/dev/null || echo "0")
  s=$(jq -r '.source // "unknown"' "$f" 2>/dev/null || echo "unknown")
  echo "[GUARD] $f | source=$s | recall@10=$r | p95_ms=$p"
  
  # Check if recall@10 > 0 AND p95_ms > 0
  if awk "BEGIN{exit !($r>0 && $p>0)}" 2>/dev/null; then
    :  # OK
  else
    echo "[GUARD] FAIL: recall@10=$r or p95_ms=$p is not > 0"
    bad=1
  fi
done

exit $bad

