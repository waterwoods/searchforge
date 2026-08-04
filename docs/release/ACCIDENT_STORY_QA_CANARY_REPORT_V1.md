# Accident Story — QA Canary Report V1

**Generated:** 2026-08-04T19:52:16Z  
**Branch:** `stage2/restricted-pilot-canary-release`  
**Commits:** `7fcc72d` (metrics/canary harness) + follow-on LLM wiring commit  
**QA revision:** `fiqa-api-qa-00062-zhk`  
**Production:** `fiqa-api-00233-scz` (untouched)  
**waterwoods:** untouched / not present  

## Classification

**QA CANARY PASS — PILOT READY WITH RESTRICTIONS**

Not Production Ready. Not a claim of real-broker accuracy beyond synthetic allowlisted QA.

---

## 1. Deterministic golden suite

| Check | Result |
|-------|--------|
| `accident_story_v1` offline golden | **20/20** |
| Local deterministic canary (20 cases) | **20/20**, p95 15ms |
| Cloud QA deterministic canary | **20/20**, p95 227ms |

Evidence: `docs/evidence/langsmith-pr-b/latest-eval-report.md`,  
`docs/evidence/pilot-canary-pr-d/canary-deterministic-local/`,  
`docs/evidence/pilot-canary-pr-d/canary-deterministic-qa/`

---

## 2. Injected-failure suite

| Injection | Result |
|-----------|--------|
| Timeout | Fallback deterministic; story preserved; lifecycle untouched |
| Malformed JSON | Fallback deterministic |
| Feature disabled / office not allowlisted | Manual intake; `failure_category=disabled` |
| Missing credentials | Fail closed to deterministic |
| Tracing failure | Intake continues |
| Duplicate command | Idempotent replay |

Evidence: `tests/test_accident_story_pilot_safety.py` + canary `timeout_sim` / `malformed_sim`

---

## 3. Live-model synthetic canary

Allowlisted office only: `qa_canary_synth`. LLM enabled only after deterministic QA PASS.

| Metric | Local live | Cloud QA live |
|--------|------------|---------------|
| Pass | 20/20 | 20/20 |
| OpenAI-backed proposes | 18/20 | 18/20 |
| Injury accuracy | 100% | 100% |
| unknown→no violations | 0 | 0 |
| >3 questions | 0 | 0 |
| p95 latency | 2626ms | 2356ms |

Inject cases remain deterministic by design.  
Evidence: `docs/evidence/pilot-canary-pr-d/canary-live-local/`, `canary-live-qa/`

---

## 4. Cloud QA runtime behavior

| Item | Value |
|------|-------|
| Revision | `fiqa-api-qa-00062-zhk` |
| Scale | minScale=0 / maxScale=2 |
| Assistant | enabled |
| LLM | enabled (allowlisted office only) |
| Office allowlist | `qa_canary_synth` (count=1) |
| LangSmith on QA | off (no key configured on service) |
| Deterministic fallback | always on |
| Non-allowlisted office | disabled → manual intake |

Support diagnostics expose flag posture without secrets.

---

## 5. Trace / redaction verification

| Item | Status |
|------|--------|
| Current `accident_story.*` runs | Redacted I/O; marker leak check **PASS** |
| LangGraph auto-trace | Suppressed via `tracing_context(enabled=False)` |
| Pre-fix unsafe runs | **PARTIAL**: `delete_run` unsupported; `update_run` redacted 8/54; remainder needs LangSmith UI manual delete/quarantine |
| Evidence | `docs/evidence/pilot-canary-pr-d/langsmith-cleanup/` |

Manual cleanup: in LangSmith project (name not printed), filter bare node names (`normalize_story`, `LangGraph`, …) from before commit `2ef3065` and delete or move to a quarantine project.

---

## 6. Durable metrics verification

| Item | Status |
|------|--------|
| Table | `accident_story_pilot_events` (Postgres) |
| Idempotency | `(event_type, idempotency_key)` |
| Cloud QA source after canary | `postgres` |
| Event count (window) | 96 |
| Proposals created | 56 |
| PII policy | no raw stories / phones / OpenIDs / tokens / photos / names |
| Exporter | `scripts/export_accident_story_pilot_metrics.py --since/--until` |
| Evidence | `docs/evidence/pilot-canary-pr-d/durable-metrics/QA_WINDOW_SUMMARY.json` |

In-memory counters are convenience only.

---

## Restricted-pilot thresholds (stated)

| Threshold | Required | Observed (QA live) |
|-----------|----------|--------------------|
| unknown-injury → no | 0 | 0 |
| raw PII in new traces | 0 | 0 (post-fix) |
| LangGraph lifecycle mutations | 0 | 0 |
| Usable fallback completion | 100% | 100% (inject + disabled paths) |
| Max questions | ≤3 | ≤3 |
| Extracted injury accuracy | ≥80% live | 100% |
| p95 latency | ≤15000ms live | 2356ms |

---

## Failures found and fixed during canary

1. **English / mixed clock times** extracted as bare `Yesterday`/`昨天` → unnecessary time question — fixed extractor preference for clock-bearing phrases.  
2. **Hedged injury** (“好像有人受伤也可能没有”) coerced to `yes` — fixed hedge → `unknown` + conflict.  
3. **Live LLM stub** raised synthetic timeout — wired bounded OpenAI JSON extract; stripped `_provider`/`_model` before schema validate.  
4. **LangSmith pre-fix raw-state runs** — cannot fully auto-delete; documented manual quarantine; new runs proven safe.

---

## Honest limits

- Synthetic QA identities/cases only  
- LLM restricted to `qa_canary_synth`  
- Pre-fix LangSmith project still has residual unsafe historical runs pending UI cleanup  
- Not validated with real office customers or Founder phone QA in this PR
