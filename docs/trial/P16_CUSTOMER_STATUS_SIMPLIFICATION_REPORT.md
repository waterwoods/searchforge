# P16 Customer Status Simplification — Report

**Sprint:** P16-P2-CUSTOMER-STATUS-SIMPLIFICATION-SPRINT  
**Date:** 2026-06-07

---

## 1. Root cause review

Prior customer surfaces exposed **two independent dimensions** (`status_label` + `contact_state`) plus lifecycle chip copy (`补充资料中`, `已送达办公室`, etc.). Customers had to interpret implementation vocabulary.

The Status Truth sprint fixed false **Submitted To Office** and green closure cards when `still_needed_fields` was non-empty. This sprint **collapses** customer-visible truth into **four business states** while keeping internal fields for broker/office tooling.

| Internal signal | Customer business state |
|-----------------|-------------------------|
| `collecting`, `handoff_pending`, gaps, no formal submit | **等客户补资料** (`awaiting_customer`) |
| Formal submit complete, `handed_off`, not actively processing | **已提交办公室** (`submitted_to_office`) |
| `office_followup`, `waiting_on` broker/carrier/underwriting | **办公室处理中** (`office_processing`) |
| `case_status: closed` | **已关闭** (`closed`) |

---

## 2. State mapping matrix

| Runtime source | Customer-visible text (zh) |
|----------------|------------------------------|
| `business_state: awaiting_customer` | 等客户补资料 |
| `business_state: submitted_to_office` | 已提交办公室 |
| `business_state: office_processing` | 办公室处理中 |
| `business_state: closed` | 已关闭 |

**Surfaces updated**

| Surface | Before | After |
|---------|--------|-------|
| `CustomerFirstEntryScreen` Active card | Status + Contact State (6+ labels) | Single **Status / 状态** row |
| `AddCarCaseStatusStrip` (customer portal) | Lifecycle chips | Single business-state chip |
| Chat system-turn tag | `补充资料中` / `已送达办公室` | Business-state zh label |
| Phone lookup API | `status_label`, `contact_state` only | Adds `business_state` (legacy fields retained) |

---

## 3. BMW X5 test results (6265558001)

| Step | Expected | Result |
|------|----------|--------|
| 宝马X5 | 等客户补资料, no green closure | **PASS** |
| 2027 | Still 等客户补资料 | **PASS** |
| All required fields + formal submit | 已提交办公室 | **PASS** |
| Office pickup (`office_followup`) | 办公室处理中 | **PASS** |
| Broker close | 已关闭 | **PASS** |

No false green closure card during collecting turns (verified via `isFormalSubmissionToOfficeComplete` gate + business state).

---

## 4. Phone return results (6265558002)

| Check | Result |
|-------|--------|
| Same `case_id` on return | **PASS** |
| `business_state` restored | **PASS** |
| `still_needed_fields` restored | **PASS** |
| Vehicle hint (宝马/X5) | **PASS** |

---

## 5. Simulation battery (A–F)

Script: `scripts/run_p16_customer_status_simplification_simulations.py`

| Scenario | Result |
|----------|--------|
| A — New customer | PASS |
| B — Return customer | PASS |
| C — Wrong phone digit | PASS |
| D — BMW X5 full lifecycle | PASS |
| E — Case close | PASS |
| F — Re-open validation | PASS |
| Phone return — 6265558002 | PASS |

**Pass rate:** 7/7 (100%) on local API `:8001`

Artifact: `docs/trial/.p16_customer_status_simulation.json`

---

## 6. Files changed

| File | Change |
|------|--------|
| `services/fiqa_api/inbox_triage/active_case_lookup.py` | `resolve_customer_business_state`, `business_state` on summary |
| `ui/src/features/intake/utils/customerFirstEntry.ts` | Business state resolver + display |
| `ui/src/features/intake/components/CustomerFirstEntryScreen.tsx` | Single status section |
| `ui/src/features/intake/utils/intakePure.ts` | Status strip uses business state |
| `ui/src/features/intake/components/CustomerEntryTab.tsx` | Chat tag uses business state |
| `ui/src/api/inboxTriage.ts` | Type for `business_state` |
| `tests/test_active_case_by_phone.py` | Business state regressions |
| `scripts/run_p16_customer_status_simplification_simulations.py` | Sprint simulation battery |

---

## 7. Remaining risks

| Risk | Mitigation |
|------|------------|
| Legacy UI paths still read `status_label` / `contact_state` | Internal only; customer surfaces migrated |
| Formal submit via API without `case_id` binds orphan case | UI always sends `case_id`; simulation patches phone on BMW case |
| Closed case + same phone allows new draft | By design (Rule 7 applies to **open** cases only) |
