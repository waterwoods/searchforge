# AutoTuner vs Heavy Baseline under Tight SLA

150 FIQA queries, budgets = 50/60/70 ms, baseline (TopK=40, rerank=on) vs Autotuner (TopK=10, rerank=off, Balanced).

## Aggregated metrics

| mode | budget_ms | p95_ms | timeout_rate | avg_items |
|------|-----------|--------|--------------|-----------|
| autotuner | 50 | 36.301 | 0.00000 | 10.000 |
| autotuner | 60 | 36.105 | 0.00222 | 10.000 |
| autotuner | 70 | 36.484 | 0.00000 | 10.000 |
| baseline | 50 | 139.739 | 0.24889 | 16.000 |
| baseline | 60 | 136.738 | 0.25111 | 16.000 |
| baseline | 70 | 141.951 | 0.25111 | 16.000 |

> Under 50–70 ms SLA, the heavy baseline has ~140 ms p95 and ~25% timeouts,
> while the Balanced Autotuner keeps p95 ≈ 35–40 ms with ~0% timeouts and fewer items per query.
