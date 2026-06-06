# Ops RAG Evaluation Report
**Generated:** 2025-11-30 19:25:07
**Test Cases:** 16
**Top-k:** 5

---
## Overall Statistics
- Total cases: 16
- Hit@k rate: 93.8% (15/16)
- Top1 hit rate: 62.5% (10/16)
- Average results per query: 5.0
- Average score: 0.4458

## By Source Type

| Source Type | Cases | Hit@k | Hit@k Rate | Top1 Hit | Top1 Rate |
|-------------|-------|-------|------------|----------|-----------|
| configs | 2 | 2 | 100.0% | 1 | 50.0% |
| incidents | 2 | 2 | 100.0% | 1 | 50.0% |
| lessons_learned | 2 | 1 | 50.0% | 0 | 0.0% |
| runbooks | 10 | 10 | 100.0% | 8 | 80.0% |

## Test Cases

| Case ID | Service | Symptom | Expected | Hit@k | Top1 | Avg Score |
|---------|---------|---------|----------|-------|------|-----------|
| case_001 | payment-service | high_error_rate | runbooks, runbooks.md | ✓ | ✓ | 0.555 |
| case_002 | api-gateway | high_error_rate | runbooks, runbooks.md | ✓ | ✓ | 0.530 |
| case_003 | search-api | high_error_rate | runbooks, runbooks.md | ✓ | ✓ | 0.508 |
| case_004 | payment-service | high_latency | runbooks, runbooks.md | ✓ | ✓ | 0.535 |
| case_005 | auth-service | high_latency | runbooks, runbooks.md | ✓ | ✓ | 0.396 |
| case_006 | api-gateway | high_cpu | runbooks, runbooks.md | ✓ | ✓ | 0.438 |
| case_007 | metrics-collector | high_cpu | runbooks, runbooks.md | ✓ | ✗ | 0.328 |
| case_008 | search-api | disk_near_full | runbooks, runbooks.md | ✓ | ✓ | 0.307 |
| case_009 | payment-service | retry_timeout | configs, configs.md | ✓ | ✓ | 0.575 |
| case_010 | api-gateway | timeout_config | configs, configs.md | ✓ | ✗ | 0.477 |
| case_011 | payment-service | severe_outage | incidents, incidents.md | ✓ | ✗ | 0.552 |
| case_012 | api-gateway | production_incident | incidents, incidents.md | ✓ | ✓ | 0.417 |
| case_013 | search-api | lessons_learned | lessons, lessons_learned | ✗ | ✗ | 0.298 |
| case_014 | payment-service | post_mortem | lessons, lessons_learned | ✓ | ✗ | 0.368 |
| case_015 | search-api | slow_queries | runbooks, runbooks.md | ✓ | ✓ | 0.473 |
| case_016 | auth-service | high_memory | runbooks, runbooks.md | ✓ | ✗ | 0.375 |

## Interpretation
<!-- TODO: Add interpretation notes here -->
