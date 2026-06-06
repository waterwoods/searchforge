# P16-Z17 Phase 6 — Customer Builder Scorecard

**Date:** 2026-06-03  
**Sprint:** P16-Z17 Customer Case Builder Reality Sprint  
**Method:** Live API + code trace + UI audit (guilty until proven innocent)

Scoring: 0 = missing, 100 = production-ready for supervised broker pilot.

---

## Scores

| # | Capability | Score | Evidence |
|---|------------|-------|----------|
| **A** | Create Case | **82** | `save_case()` on formal submit proven (`case_98f4ac099d15`). Partial Tesla-only submit correctly blocked (VIN gate). UI + API wired. |
| **B** | Return Later | **58** | Pre-submit session restore ✅ (`GET /session`, 2 turns). Post-submit: My Requests ✅, Customer Entry empty ❌. |
| **C** | Continue Same Case | **62** | In-session append ✅ (`handlePostHandoffAppendSameCase`). After refresh: no `case_id` hydrate ❌. My Requests CTA switches tab only. |
| **D** | Timeline | **78** | `case_messages` seq 1–11 + `case_activity` × 3 proven. Broker ✅. Customer thread UI lost on refresh. |
| **E** | Broker Review | **88** | Same case_id, summary, fields, thread, next step — broker understands without reopening chat. |
| **F** | Persistence | **91** | JSON + Postgres paths; session + case stores; `formal_submitted_at` immutable; append merges fields. |
| **G** | Multi-Day Continuity | **74** | Data layer: 3-day story ✅. Customer UX: must rediscover case manually; append panel not restored. |

---

## Weighted overall

| Formula | Value |
|---------|-------|
| Simple average (A–G) | **76 / 100** |
| Pilot-critical path (A + B + C + E + G) | **73 / 100** |

---

## Interpretation

| Score band | Meaning |
|------------|---------|
| 0–40 | Not built |
| 41–60 | Exists but broken for real users |
| 61–75 | **Current state — usable with wiring** |
| 76–90 | Pilot-ready single-customer |
| 91–100 | Self-serve multi-customer SaaS |

---

## What works without new architecture

- CustomerEntryTab multi-turn triage
- Session restore pre-submit
- Formal submit → real case_id
- Append → same case, merged fields, timeline
- Broker workbench reads full record

---

## What drags scores down

1. Post-submit refresh loses Customer Entry context (`lastCaseId`, append panel, thread)
2. My Requests → Customer Entry does not pass `case_id`
3. Resume hint excludes `submitted` lifecycle cases
4. No customer-visible message timeline after return

---

## One-line scorecard verdict

> **Customer Builder averages ~76/100 — real at the data and broker layers, incomplete at post-submit customer return.**
