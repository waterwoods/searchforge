# P16-Z17 Phase 8 — Founder Summary

**Date:** 2026-06-03  
**Sprint:** P16-Z17 Customer Case Builder Reality Sprint  
**North star tested:** Customer → Create Case → Leave → Return → Continue → Broker Review → Timeline

---

## Answers (exact)

### 1. Does Customer Builder already exist?

**Yes.**

It is **`CustomerEntryTab`** (客户报送) in Unified Intake. It runs multi-turn Add-Car triage, formal submit to office, and post-handoff append. Cases persist in `case_store.py`; brokers read the same records in `BrokerWorkbenchTab`.

Live proof: `case_98f4ac099d15` created via `POST /api/inbox/triage` with `formal_submit: true`.

---

### 2. Can customer return later?

**Partially.**

| When | Answer |
|------|--------|
| **Before formal submit** | **Yes** — `session_id` in localStorage + `GET /api/inbox/session/{id}` restores conversation (proven: 2 turns). |
| **After formal submit** | **Partial** — case survives in store and appears in **My Requests**; Customer Entry does not auto-restore on refresh. |

---

### 3. Can customer continue same case?

**Partially.**

| When | Answer |
|------|--------|
| **Same browser session (no refresh)** | **Yes** — append via `handlePostHandoffAppendSameCase` + `POST .../append-message`. |
| **After refresh / new visit** | **No** — `lastCaseId` lost; My Requests button switches tab without passing `case_id`. |

Persistence layer: **Yes** (same case_id, merged fields). Customer UX: **Not without wiring.**

---

### 4. Can broker see updates?

**Yes.**

Broker opens `case_98f4ac099d15` and sees updated `collected_fields`, `broker_next_step`, 11 `case_messages`, and activity entries after Day 2 and Day 3 appends — without reopening customer chat.

---

### 5. Can timeline survive 3 days?

**Yes (data layer).**

`case_messages` sequences 1–11 with distinct timestamps; `case_activity` records create + two append events. `formal_submitted_at` unchanged. Broker timeline is usable today.

Customer does not see full message timeline after return — wiring gap, not storage gap.

---

### 6. Is Customer Builder 70% / 80% / 90% / 95% complete?

## **~76% complete (between 70% and 80%).**

Scorecard average across seven capabilities: **76/100**. Strong on create, persist, broker review, append API. Weak on post-submit customer return.

Not 50%. Not 90%. **Supervised pilot viable after 3–4 wiring days.**

---

### 7. How many engineer-days remain?

**3.0–3.5 engineer-days** for MVP loop closure:

- Hydrate `case_id` into Customer Entry after return (1.0d)
- My Requests → pass case_id on continue (0.5d)
- Resume hint for submitted cases (0.5d)
- Session DB ops + browser walkthrough (1.0d)

---

### 8. What should be renamed?

| Current | Proposed (customer-facing) |
|---------|---------------------------|
| 客户报送 | **Case Builder** / 办理申请 |
| 我的办理 | **My Cases** / 我的申请 |
| 服务记录编号 | **Your case reference** |
| 正式提交办公室 | **Submit to office** |
| Unified Intake (internal) | **Customer First** (positioning) |

Backend names (`CustomerEntryTab`, `save_case`) can stay.

---

### 9. What should be archived?

| Archive / demote | Reason |
|------------------|--------|
| Docs proposing greenfield Customer Builder | Contradicted by P16-Z17 live proof |
| Roadmap items "build case persistence from scratch" | Exists in `case_store.py` |
| Simulation Role C/D as primary customer product story | Test harness, not Customer First |

**Do not archive:** `CustomerEntryTab`, `MyRequestsTab`, append APIs, session store, broker workbench.

---

### 10. Should we build anything new?

## **No. Finish wiring. Do not rebuild.**

---

## Founder decision (no ambiguity)

# Customer Builder already exists. Finish wiring. Do not rebuild.

The repository contains a working loop:

```
CustomerEntryTab → triage → formal_submit → save_case → case_id
                                              ↓
                                    append-message (same case)
                                              ↓
                                    BrokerWorkbenchTab (full visibility)
```

What remains is **customer return UX** — rehydrate `case_id` after refresh and connect My Requests to Customer Entry. That is 3–4 engineer-days, not a new product.

---

## Evidence index

| Phase | Document |
|-------|----------|
| 1 Journey trace | `P16Z17_CUSTOMER_JOURNEY.md` |
| 2 Return later | `P16Z17_RETURN_LATER.md` |
| 3 Append | `P16Z17_APPEND_TEST.md` |
| 4 Broker | `P16Z17_BROKER_VISIBILITY.md` |
| 5 Timeline | `P16Z17_TIMELINE_TEST.md` |
| 6 Scorecard | `P16Z17_SCORECARD.md` |
| 7 Gaps | `P16Z17_TRUE_MVP_GAPS.md` |

Live case: `case_98f4ac099d15` @ `2026-06-03T08:58:13Z` on port 8001.

Prior aligned sprint: P16-Z16 (`docs/product_constitution/P16Z16_*.md`).
