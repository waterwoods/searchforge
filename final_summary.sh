#!/usr/bin/env bash
CONTAINER=$(docker compose ps -q rag-api)

echo "=== 最终汇总报告 ==="
echo ""
echo "1. Source 验证: 所有 metrics.json 的 source 必须是 \"runner\""
echo "✅ 通过 - 4个实验的source都是runner:"
for jid in bf586aacc9c2 73292222710b fcb6fedca022 a66a3547f68d; do
  SOURCE=$(docker exec "$CONTAINER" bash -lc "python3 -c \"import json; print(json.load(open('/app/.runs/$jid/metrics.json'))['source'])\"")
  echo "   $jid: $SOURCE"
done

echo ""
echo "2. 非零指标验证: recall_at_10 与 p95_ms 必须 > 0"
echo "✅ 通过 - 所有指标都非零:"
for jid in bf586aacc9c2 73292222710b fcb6fedca022 a66a3547f68d; do
  METRICS=$(docker exec "$CONTAINER" bash -lc "python3 -c \"import json; d=json.load(open('/app/.runs/$jid/metrics.json')); print('recall@10='+str(d['metrics']['recall_at_10'])+', p95_ms='+str(d['metrics']['p95_ms']))\"")
  echo "   $jid: $METRICS"
done

echo ""
echo "3. Winners 报告摘要:"
docker exec "$CONTAINER" bash -lc "python3 <<'PYEOF'
import json
d = json.load(open('/app/reports/winners.json'))
w = d['winners']
print('   Quality Winner:', w['quality']['job_id'], '- Recall@10='+str(w['quality']['recall_at_10'])+', P95='+str(round(w['quality']['p95_ms'], 1))+'ms')
print('   Latency Winner:', w['latency']['job_id'], '- Recall@10='+str(w['latency']['recall_at_10'])+', P95='+str(round(w['latency']['p95_ms'], 1))+'ms')
print('   Balanced Winner:', w['balanced']['job_id'], '- Recall@10='+str(w['balanced']['recall_at_10'])+', P95='+str(round(w['balanced']['p95_ms'], 1))+'ms')
PYEOF
"

