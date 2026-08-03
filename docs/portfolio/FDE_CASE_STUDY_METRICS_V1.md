# FDE / Applied AI Case Study — Measurement Foundation (V1)

**Product:** California auto-insurance broker assistant (Unified Intake / Claim workbench)  
**Slice:** Stage 2 real-usage timing instrumentation  
**Evidence date:** 2026-08-03  
**Environment:** Cloud QA only (Production untouched)

This note is evidence-backed for interviews and portfolio review. It does **not** claim customer savings, revenue impact, or production usage.

---

## Customer problem

Brokers and founders need a trustworthy answer to: *how long does the claim journey take, where does it stall, and did the customer actually start working?*

Without durable first-event timestamps, demos can show a complete workflow while measurement still confuses:

- case `created_at` with formal submit,
- page opens with active work,
- broker queue glance with first meaningful broker open.

---

## Workflow already implemented (validated before this slice)

**Stage 1 (tag `stage1-founder-validated-demo-2026-08-03`):** customer intake → Request More → customer supplement → broker supplement review → office materials accept. Founder phone GO on `case_4e5adf36c637`.

**Stage 2 (closed, phone validated):** known-customer policy-context prefill + confirm without forcing insurance-card upload (`case_09ad6254614a`, commit `f1bb8e0`).

This metrics slice does **not** add a new customer feature. It instruments timing around the existing journey.

---

## Instrumentation architecture

```
Customer Mini Program / H5          Broker Workbench
        │                                    │
        ▼                                    ▼
  context / intake /               GET /api/inbox/cases/{id}
  start-claim / patch /            (first successful detail)
  confirm / request-item
        │                                    │
        └────────────┬───────────────────────┘
                     ▼
         case_activity_events (Postgres + memory)
         first-wins: open / first_action / broker_open
                     │
                     ▼
         tools/export_case_value_metrics.py
         CSV + JSON + summary (median/p75/p90)
```

- Dedicated `case_activity_events` store (not customer Timeline).
- Server timestamps only; hashed optional session id; no accident text / tokens / PII.
- Business stamps unchanged: `formal_submitted_at`, Request More, supplement, review, office accept, policy confirm.
- Metrics export sends `X-Case-Activity-Record: 0` so read-only export does not invent broker-open events.

Semantics: `docs/metrics/CASE_VALUE_METRICS_SEMANTICS.md`

---

## Reliability controls

| Control | Implementation |
|---------|----------------|
| Idempotency / first-wins | Unique `(case_id, event_type, idempotency_key)`; refresh does not reset |
| Actor separation | `customer` vs `broker` on event rows |
| No PII in telemetry meta | Allow-list: `command_type`, `surface_detail`, `outcome` |
| Fail-open | Telemetry never breaks business commands (`safe_record`) |
| Production safety | This PR deploys Cloud QA only; Production/waterwoods untouched |
| Honest missing data | Exporter leaves blanks; marks `unsupported:` / `missing:` / `qa_or_artificial_timing` |

---

## Metrics now measurable

**Business facts (already authoritative, now exported cleanly):**

- Formal submit, policy-context confirm, first Request More, request_more_loops
- Supplement submit + turnaround, broker supplement review latency
- Office materials accepted

**New observational stamps (live after instrumentation deploy):**

- `customer_intake_opened_at` — session open, **not** active work time
- `customer_first_action_at` — first durable meaningful customer mutation
- `broker_first_opened_at` — first successful case-detail/Brief GET

**Derived (when stamps exist):** intake_open→submit, first_action→submit, submit→broker_open, request_more→supplement, supplement→review, first_action→office_accept.

---

## Bugs / truths found through real phone QA (prior slices)

Recorded honestly from Stage 1 / Stage 2 phone evidence (not invented here):

- Formal submit often equals `created_at` on the demo start-claim path → pre-submit dwell was previously invisible.
- Broker first-open was **unsupported** in the V1 exporter (`unsupported:broker_first_open_not_recorded`).
- Stage 2 required invite isolation so phone QA did not resume the wrong Active Case.
- Export GETs can accidentally stamp observational “first open” if not gated — fixed with `X-Case-Activity-Record: 0`.

---

## What cannot yet be claimed

- Customer time saved, broker hours saved, or revenue impact
- Production usage or pilot-scale statistics (QA n≪30; `statistically_meaningful: false`)
- Page-open duration as active working time
- AI accept / edit / reject rates (no events yet)
- Historical backfill of open/first-action for Stage 1/2 phone cases

See `docs/metrics/CASE_VALUE_METRICS_QA_REPORT.md` for measured vs missing vs artificial.

---

## Concise interview talking points

1. **Shipped a measurement foundation before LangGraph/LangSmith** so AI work has ground truth, not demo vibes.
2. **Separated business facts from observational telemetry** and refused to put page-view noise on the customer Timeline.
3. **First-wins idempotency** so refresh/replay cannot rewrite funnel timestamps.
4. **Exporter with summary percentiles and explicit missing-data rates**, with a hard “not statistically meaningful” flag on small QA samples.
5. **Founder-validated Stage 1 + Stage 2 phone journeys** already prove the workflow; this slice proves we can measure the next one honestly.

---

## Exact next engineering PR (recommended)

**PR A:** Deterministic AI contract + bounded LangGraph accident-story assistant (no LangSmith yet).  
**PR B:** LangSmith tracing, golden evaluation dataset, evaluators, regression gate.

Keep them sequential so contract failures are not confused with tracing/eval failures.
