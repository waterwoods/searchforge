# P16-Z16 Phase 7 — True Gaps

**Date:** 2026-06-03  
**Sprint:** P16-Z16 Customer Builder Reality Validation  
**Scope:** Genuine blockers only — not nice-to-haves, not platform dreams

**Blocker definition:** Prevents Customer → Case → Return Later → Broker Review without new architecture.

---

## Blocker 1 — No customer-scoped case list

**Symptom:** `GET /api/inbox/cases` returns all cases for the office/client pack. `filterUserVisibleCases` filters test/archive/client pack only — not customer identity.

**Blocks:** Real multi-customer production where each person sees only their cases.

**Not blocked:** Single-customer pilot, demo, broker-supervised flow.

**Fix class:** Identity binding (WeChat/phone stub exists) + filter — not new architecture.

---

## Blocker 2 — Post-submit return does not rehydrate Customer Entry

**Symptom:**

- `clearSessionId()` on case creation
- `lastCaseId` lives in React state only
- My Requests `onContinueInCustomerPortal()` switches tab without passing `case_id`
- No `GET /api/inbox/cases/{id}` hydrate on Customer Entry mount

**Blocks:** Customer returns Day 2, refreshes browser, and continues same case in builder UI.

**Fix class:** Wire existing APIs — pass `case_id`, load case, enable append panel. ~1–2 engineer-days.

---

## Blocker 3 — Pre-submit session restore requires Postgres

**Symptom:** `session_repository` returns `None` without `DATABASE_URL` / `SERVICE_RECORD_DATABASE_URL` (unless test in-memory flag).

**Blocks:** Pre-formal-submit refresh recovery in default JSON-only local demo.

**Fix class:** Ensure demo env has DB URL (already documented in runbooks) — config, not architecture.

---

## Blocker 4 — Customer tabs hidden in product-only trial mode

**Symptom:** `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1` hides Customer Entry and My Requests tabs (`UnifiedIntakePage.tsx`).

**Blocks:** Customer First demo on default broker trial deploy surface.

**Fix class:** Env flag / tab policy — not new product.

---

## Blocker 5 — Pre-submit cases invisible in My Requests

**Symptom:** Cases persist only on formal submit (Add-Car) or `handoff_ready` (generic). My Requests reads case store only.

**Blocks:** Customer who left mid-intake (pre-submit) from finding in-progress work via My Requests — must rely on session restore (Blocker 3).

**Fix class:** Either promote partial cases to store (policy change) or ensure session path is reliable — product decision, not greenfield.

---

## NOT blockers (explicitly excluded)

| Item | Why not a blocker |
|------|-------------------|
| Better UI polish | Nice-to-have |
| Auth / multi-tenant | Platform — out of MVP scope per AGENTS.md |
| Stripe billing | Out of scope |
| New timeline architecture | `case_messages` + `case_activity` exist |
| Rebuild Customer Builder | Would discard 72% complete system |
| Broker activity hero placement | Broker path works |
| Cross-device sync | Depends on Blocker 1; defer until identity |
| LLM quota / fallback quality | Operational, not structural |
| `conversation_summary` merge gaps | Broker-facing; append still works |

---

## Blocker count summary

| # | Blocker | Severity for Customer First MVP |
|---|---------|--------------------------------|
| 1 | No customer-scoped list | High for production; Low for pilot |
| 2 | No post-submit rehydrate | **Critical for return-later story** |
| 3 | Session requires Postgres | Medium for local demo |
| 4 | productOnlyUi hides tabs | Medium for trial positioning |
| 5 | Pre-submit not in My Requests | Medium — session path alternative |

**Minimum to ship Customer First pilot:** Resolve **Blocker 2** + **Blocker 4**. Blockers 1 and 5 can wait for real multi-customer traffic.

---

## Verdict

There are **5 genuine gaps**, of which **1 is critical** (post-submit customer rehydrate). None require new architecture — all are wiring, config, or identity scope on existing assets.
