# P16 Case Memory Persistence — Certification

**Sprint:** P16-P2-CASE-MEMORY-PERSISTENCE-SPRINT  
**Date:** 2026-06-07  
**Certifier:** Cursor agent (automated + browser)

---

## 1. Root cause

Collecting-phase `/api/inbox/triage` with bound `case_id` never called `append_follow_up_message`. Conversation lived in React state; Postgres retained only the Customer First draft starter.

See: [`P16_CASE_MEMORY_ROOT_CAUSE.md`](./P16_CASE_MEMORY_ROOT_CAUSE.md)

---

## 2. Exact files changed

| File | Change |
|------|--------|
| `services/fiqa_api/routes/inbox_triage.py` | Wire `append_follow_up_message` on bound-case triage when append allowed |
| `tests/test_collecting_case_memory_persistence.py` | Regression tests |
| `scripts/run_p16_case_memory_simulation.py` | E2E simulation battery |

---

## 3. DB tables used

- **`service_records`** — case row (Postgres primary)
- **`case_messages`** (JSONB) — customer/system turns with sequence
- **`source_text`**, **`collected_fields`**, **`still_needed_fields`** — updated via existing append merge

No new tables.

---

## 4. Before behavior

| Step | Result |
|------|--------|
| Phone lookup | Active case found ✅ |
| Continue | Empty chat (draft starter only) ❌ |
| Still Needed / Status | Partially from summary card; thread missing ❌ |
| Storage | React state only during session |

---

## 5. After behavior

| Step | Result |
|------|--------|
| Each collecting triage turn | `append_follow_up_message` → Postgres |
| Phone return → Continue | Full timeline from `case_messages` ✅ |
| Still Needed / Status | From persisted case record ✅ |
| Browser refresh / new tab | No dependency on localStorage thread ✅ |

---

## 6. Simulation results

| Sim | Phone | Scenario | Local (8001) | Cloud Run QA |
|-----|-------|----------|--------------|--------------|
| A | 6265553001 | Multi-turn + phone return | PASS | PASS |
| B | 6265553002 | Page refresh | PASS | PASS |
| C | 6265553003 | New tab / active-case | PASS | PASS |
| D | 6265553004 | Timeline order (4 supplements) | PASS | PASS |

**Unit tests:** `tests/test_collecting_case_memory_persistence.py` — 2/2 PASS

**Backend deploy:** `bash scripts/deploy_paid_pilot.sh` → `fiqa-api-g7zatxrycq-uw.a.run.app`

---

## 7. Preview URL tested

**URL:** https://ui-waterwoods-andys-projects-1f411b73.vercel.app/workbench/unified-intake?tab=customer

**Test phone:** 6265553001 (seeded via API with `client_id=chen_kui`)

| Check | Result |
|-------|--------|
| 1. Customer enters phone | ✅ |
| 2. Active case found | ✅ "Active Add-Car Request" card |
| 3. Continue | ✅ Hydration spinner → intake UI |
| 4. Previous conversation visible | ✅ BMW X5, 2027, ZIP 92620 in thread |
| 5. Missing fields visible | ✅ Year, VIN, Effective Date, Driver License on card |
| 6. Status visible | ✅ "本加车报价请求已提交办公室处理" / progress strip |
| 7. No browser-memory dependency | ✅ Data from `GET /cases/{id}` after cold entry |

---

## 8. Remaining risks

| Risk | Severity | Notes |
|------|----------|-------|
| Append blocked on vehicle-scope conflict | Low | By design — no silent mutation |
| `client_id` mismatch hides active case | Low | Preview uses `chen_kui`; test data must match |
| Formal-submit `save_case` path unchanged | Low | Separate from collecting append |
| Idempotent retry of same turn | Low | Out of scope |

---

## 9. GO / CONDITIONAL GO / NO GO

## **GO**

Case Memory persistence is repaired. Customer can start intake, add information, close browser, return via phone, see previous conversation, and continue from the same point — verified on live Cloud Run API and Preview UI.

**Constitution rules:** Unchanged — no new rules, no login, no multi-case picker.

**Related docs:**

- [`P16_CASE_MEMORY_ROOT_CAUSE.md`](./P16_CASE_MEMORY_ROOT_CAUSE.md)
- [`P16_CASE_MEMORY_FIX_REPORT.md`](./P16_CASE_MEMORY_FIX_REPORT.md)
- [`P16_CASE_MEMORY_SIMULATION_REPORT.md`](./P16_CASE_MEMORY_SIMULATION_REPORT.md)
