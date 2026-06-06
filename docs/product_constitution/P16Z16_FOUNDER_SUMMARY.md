# P16-Z16 Phase 8 — Founder Summary

**Date:** 2026-06-03  
**Sprint:** P16-Z16 Customer Builder Reality Validation  
**North star validated:** Customer First → Case Builder → Broker Review

---

## Answers (exact)

### 1. Do we already have a Customer Builder?

**Yes.**

It lives today as **「客户报送」** (`CustomerEntryTab`) inside Unified Intake. It creates real cases, collects structured Add-Car fields across turns, formal-submits to the office, and appends follow-ups to the same record. The broker workbench reads the same cases.

---

### 2. If yes, how complete is it?

**~70% complete (72/100).**

| Leg | Status |
|-----|--------|
| Customer → Case | ✅ Works (Add-Car flagship) |
| Case → Broker Review | ✅ Works |
| Customer → Return Later | ⚠️ Partial (pre-submit session only; post-submit breaks on refresh) |
| Customer → Append | ⚠️ Works in-session; not wired to My Requests |
| Cross-device | ❌ Not ready |

Not 50%. Not 90%. **Usable pilot.**

---

### 3. What should be renamed?

| Current | Proposed customer-facing |
|---------|-------------------------|
| 客户报送 (Customer Entry tab) | **Case Builder** / 办理申请 |
| 我的办理 (My Requests tab) | **My Cases** / 我的申请 |
| 服务记录编号 | **Your case reference** (keep copyable ID) |
| 正式提交办公室 | **Submit to office** (keep action semantics) |
| Unified Intake (internal) | **Customer First** (product positioning) |

Backend names (`save_case`, `CustomerEntryTab` file) can stay — rename is product/copy layer.

---

### 4. What should be reused?

**Reuse everything in the Reuse Map.** Priority order:

1. `CustomerEntryTab` + `triageMessage` — primary builder  
2. `save_case` / formal submit path — case creation  
3. `appendFollowUpMessage` + `triage_for_append` — continuity  
4. `UserCaseListProgressPanel` — progress (wire `case_id` back)  
5. `BrokerWorkbenchTab` — broker review (unchanged)  
6. Session store + `getInProgressSession` — pre-submit return  
7. `case_messages` / `case_activity` — timeline truth  

---

### 5. What should be archived?

| Archive / demote | Reason |
|------------------|--------|
| Docs proposing greenfield Customer Builder | Contradicted by this audit |
| Simulation-only customer paths as "the product" | Role C/D is test harness, not Customer First |
| Duplicate intake experiments in `docs/archive/sprints/` | Already superseded by current stack |
| Any roadmap item "build case persistence from scratch" | Exists in `case_store.py` |

**Do not archive:** `CustomerEntryTab`, `MyRequestsTab`, append APIs, session store, workbench.

---

### 6. How many engineer-days remain before Customer First MVP?

| Task | Days |
|------|------|
| Wire My Requests → Customer Entry (`case_id` hydrate + append mode) | 1–1.5 |
| Persist active `case_id` across refresh (sessionStorage) | 0.5 |
| Customer-facing rename / tab copy (Case Builder, My Cases) | 0.5 |
| Demo env: ensure Postgres for session restore | 0.5 (ops) |
| Pilot test: 3-day Tesla walkthrough in UI | 0.5 |

**Total: 3–4 engineer-days** for pilot-ready Customer First MVP (single-customer, same broker pack).

**Additional 5–8 days** if customer-scoped identity (Blocker 1) required before first paid customer — not required for supervised Chen Kui pilot.

---

### 7. Should we build a new Customer Builder?

## **A. Customer Builder already exists. Reuse and repackage.**

Do **not** build new. The repository contains a working Customer First → Case Builder → Broker Review loop at the data and broker layers. Remaining work is **wiring return-later UX** and **product naming** — not architecture.

---

## One-sentence verdict

> **The Customer Builder is real, ~70% complete, and living under 「客户报送」— reuse it, wire My Requests back into it, rename it for customers, and ship.**

---

## Supporting evidence

- Live 3-day simulation: case created, VIN appended, driver appended, timeline sequences 1–7, `formal_submitted_at` preserved  
- Phases 1–7: `docs/product_constitution/P16Z16_*.md`  
- Prior archaeology aligned: P16-Z4 continuity audit, P16-Z6 memory visibility
