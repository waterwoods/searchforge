# Real Usage Timing V1 — Closeout

**Status:** `REAL USAGE TIMING V1 CLOSED`  
**Date:** 2026-08-03  
**Branch:** `stage2/real-usage-timing-instrumentation`  
**QA revision at close:** `fiqa-api-qa-00053-hkx`  
**Production / waterwoods:** untouched  
**QA scale:** minScale=0 / maxScale=2  

---

## Event contract

Store: `case_activity_events` (not customer Timeline)

| Event | Actor | How stamped |
|-------|-------|-------------|
| `customer_intake_opened` | customer | Customer context / intake / start-claim success |
| `customer_first_action` | customer | First durable meaningful customer mutation |
| `broker_first_opened` | broker | **Only** `POST /api/inbox/cases/{id}/activity/broker-first-opened` after Workbench detail render |

Properties: `case_id`, `event_type`, `actor_role`, server `created_at`, `source_surface`, `schema_version=1`, idempotency key, optional `session_id_hash`. No accident text / tokens / PII.

Semantics: `docs/metrics/CASE_VALUE_METRICS_SEMANTICS.md`

---

## Verified read-only behavior

Integrity evidence: `docs/evidence/real-usage-timing-v1/20260803T234426Z-integrity/`  
Case: `case_064c13b33017`

Proved:

1. Before Workbench activity POST → `broker_first_opened_at` blank; exporter blank  
2. Metrics export GET, support manifest, repeated API case GETs → **do not** create `broker_first_opened`  
3. Those reads do not invent `customer_intake_opened` / `customer_first_action` beyond customer-path stamps  
4. Dedicated activity POST → exactly one first-wins event (`actor_role=broker`, `source_surface=broker_workbench`, server `…Z` timestamp)  
5. Re-POST / reopen → same timestamp (`duplicate`)  
6. Exporter returns the same timestamp  
7. Activity response has no PII fields  
8. Exporter remains read-only (`X-Case-Activity-Record: 0` defense-in-depth; GET never stamps)

**Fix shipped in closeout:** removed generic GET stamp; Workbench UI calls dedicated POST after successful detail render.

---

## Supported metrics

Business facts: formal submit, policy confirm, Request More loops, supplement turnaround, broker supplement review, office accept  

Observational (first-wins): intake opened, first action, broker first opened + derived deltas when both ends exist  

Exporter: CSV/JSON + summary (median/p75/p90, missing rates, `statistically_meaningful=false` for small n)

---

## Unsupported claims

- Customer/broker time saved or revenue impact  
- Production usage statistics  
- Page-open = active work  
- AI accept/edit/reject rates  
- Historical backfill of open/first-action for pre-instrumentation phone cases  
- Artificial post-deploy GET stamps from early revision (documented; superseded by dedicated POST)

---

## Exact commits

| Commit | Summary |
|--------|---------|
| `a7f7bf7` | Durable case activity timing instrumentation |
| `46e50b7` | Exporter + QA report + portfolio evidence |
| *(closeout)* | Dedicated broker-open activity POST; GET never stamps; integrity evidence |

---

## Verdict

**REAL USAGE TIMING V1 CLOSED**
