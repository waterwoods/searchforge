# Case Value Metrics — QA Report (Stage 2 instrumentation)

**Date:** 2026-08-03  
**Branch:** `stage2/real-usage-timing-instrumentation`  
**QA revision:** `fiqa-api-qa-00052-xvb` (instrumentation + export-safe `X-Case-Activity-Record: 0`)  
**Production / waterwoods:** untouched  
**QA scale:** minScale=0 / maxScale=2  

Semantics SSOT: `docs/metrics/CASE_VALUE_METRICS_SEMANTICS.md`

---

## Cases examined

| Case | Role | Source |
|------|------|--------|
| `case_4e5adf36c637` | Stage 1 Request More → supplement → office accept | Cloud QA + `docs/evidence/qa-fast-lane/20260803T190949Z-final-phone/` |
| `case_09ad6254614a` | Stage 2 known-customer policy confirm (phone) | Cloud QA + Stage 2 evidence pack |
| Request More loop | Same as Stage 1 case above | `broker_request_more_created` → `supplement_submitted` |

Export artifacts (local): `artifacts/case_value_metrics/stage2_timing_qa.{json,csv,summary.json}`

---

## Measured values (business facts — trustworthy)

### `case_4e5adf36c637` (Stage 1 / Request More)

| Metric | Value | Notes |
|--------|-------|-------|
| `formal_submitted_at` | `2026-08-03T18:34:50Z` | Equals `created_at` (pre-submit dwell not separately recorded) |
| `first_request_more_at` | `2026-08-03T18:41:08Z` | |
| `request_more_loops` | `1` | |
| `supplement_submitted_at` | `2026-08-03T19:09:03Z` | |
| `request_more_to_supplement_sec` | `1675` (~28 min) | QA phone session timing |
| `broker_supplement_reviewed_at` | `2026-08-03T19:10:05Z` | |
| `supplement_to_broker_review_sec` | `62` | |
| `office_materials_accepted_at` | `2026-08-03T19:10:06Z` | |
| Legacy `time_to_office_accept_sec` | `2116` | From `created_at`, not first_action |

### `case_09ad6254614a` (Stage 2 confirm)

| Metric | Value | Notes |
|--------|-------|-------|
| `policy_context_confirmed_at` | `2026-08-03T22:07:44Z` | Business confirm event present |
| `formal_submitted_at` | blank | Case still in collecting / not formally submitted |
| Request More / supplement / office | blank | Out of Stage 2 confirm scope |

---

## Missing values (expected for pre-instrumentation cases)

| Metric | `case_4e5adf…` | `case_09ad…` | Why |
|--------|----------------|--------------|-----|
| `customer_intake_opened_at` | missing | missing | Observational stamp did not exist during phone QA |
| `customer_first_action_at` | missing | missing | Same — no backfill from Timeline |
| `intake_open_to_submit_sec` | blank | blank | Depends on open stamp |
| `first_action_to_submit_sec` | blank | blank | Depends on first_action stamp |
| `first_action_to_office_accept_sec` | blank | blank | Depends on first_action stamp |

These require **new** customer sessions after instrumentation is live.

---

## QA / artificial timings (do not treat as pilot truth)

| Observation | Interpretation |
|-------------|----------------|
| `broker_first_opened_at` ≈ `2026-08-03T23:28:29Z` on both cases | Stamped by the **first post-deploy metrics export GET** before `X-Case-Activity-Record: 0` was added. **Not** the original Founder phone broker open. |
| `submit_to_broker_first_open_sec` = `17619` on Stage 1 case | Arithmetic from formal submit → that artificial stamp (~4.9 h). **Not** broker latency. |
| All cases tagged `qa_or_artificial_timing` | Test/demo/harness traffic |
| `time_to_formal_submit_sec` = `0` | Formal equals create on Stage 1 path |

Exporter now sends `X-Case-Activity-Record: 0` so subsequent exports do not invent new first-open stamps. Existing polluted first-open rows remain first-wins (immutable).

---

## Summary mode (n=2)

```
case_count: 2
statistically_meaningful: false
request_more_to_supplement_sec median: 1675 (n=1)
supplement_to_broker_review_sec median: 62 (n=1)
customer_intake_opened_at missing_rate: 1.0
customer_first_action_at missing_rate: 1.0
```

**Do not claim statistical significance.** Sample is Founder QA only.

---

## Metrics that require real pilot traffic

- `customer_intake_opened_at` / `customer_first_action_at` distributions
- `intake_open_to_submit_sec` / `first_action_to_submit_sec` (with honest “not active work” labeling)
- True `broker_first_opened_at` during normal Workbench use (not export GETs)
- `submit_to_broker_first_open_sec` as broker responsiveness
- `first_action_to_office_accept_sec` end-to-end
- AI accept/edit/reject rates — still **unsupported** (no events)

---

## Gates run

| Gate | Result |
|------|--------|
| Focused activity + exporter tests | PASS |
| Policy confirm / Request More / office accept tests | PASS |
| Frontend broker-open contract test | PASS |
| `miniapp` `npm run build:gate` | PASS |
| `bash scripts/run_deployment_qa_gate.sh` | READY FOR FOUNDER QA (`fiqa-api-qa-00052-xvb`) |
| Physical phone retest | Not required (no client-only uncertainty exposed) |
