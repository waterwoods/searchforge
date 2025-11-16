# Go Proxy On/Off Concurrency & QPS

Client → rag-api vs client → Go retrieval proxy, budget_ms = 70, concurrency = 1/4/8/16/32, no autotuner.

## Aggregated metrics

| mode | concurrency | p95_ms | qps | error_rate | timeout_rate |
|------|-------------|--------|-----|------------|--------------|
| baseline | 1 | 35.136 | 35.434 | 0.00000 | 0.00000 |
| baseline | 4 | 153.206 | 29.949 | 0.00000 | 0.00000 |
| baseline | 8 | 315.244 | 30.507 | 0.00000 | 0.00000 |
| baseline | 16 | 641.623 | 32.568 | 0.00000 | 0.00000 |
| baseline | 32 | 1133.687 | 32.658 | 0.00000 | 0.00000 |
| proxy | 1 | 1.366 | 822.465 | 0.00000 | 0.00000 |
| proxy | 4 | 7.364 | 1039.639 | 0.00000 | 0.00000 |
| proxy | 8 | 16.828 | 1036.998 | 0.00000 | 0.00000 |
| proxy | 16 | 33.852 | 982.672 | 0.00000 | 0.00000 |
| proxy | 32 | 54.377 | 967.520 | 0.00000 | 0.00000 |

> Under 70 ms budget, the rag-api baseline saturates around ~30 QPS with p95 up to ~1.1 s,
> while the Go proxy path sustains ~800–1000 QPS with p95 staying below ~60 ms at concurrency 32.
