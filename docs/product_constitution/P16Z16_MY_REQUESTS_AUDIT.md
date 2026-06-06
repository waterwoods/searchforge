# P16-Z16 Phase 2 — My Requests Audit

**Date:** 2026-06-03  
**Sprint:** P16-Z16 Customer Builder Reality Validation  
**Sources:** `MyRequestsTab.tsx`, `UserCaseListProgressPanel.tsx`, `listRecentCasesPage`, `filterUserVisibleCases`, `GET /api/inbox/cases`

---

## Executive answer

**My Requests is a read-only progress dashboard for persisted cases.** It lets a customer find and inspect previous submissions on the same browser/office pack, but it does **not** resume the conversation thread or wire the selected case back into Customer Entry. Production-ready as a **status panel**; not production-ready as a **resume builder**.

---

## 1. Can customer return later?

| Mechanism | Works? | Scope |
|-----------|--------|-------|
| Pre-submit session restore (Customer Entry mount) | ✅ Same browser + DB session | In-progress only |
| My Requests list | ✅ After formal submit | Persisted cases only |
| Cross-device / new browser | ❌ | No customer auth |
| My Requests → continue | ⚠️ Partial | Switches tab only |

**Pre-submit cases never appear in My Requests.** Empty-state copy confirms: *「请先在客户报送完成办理并正式提交办公室」*.

---

## 2. Can customer find previous case?

**Yes**, when:

1. Case was formally submitted (exists in case store).
2. Case passes `filterUserVisibleCases`.
3. Customer opens **我的办理** tab (hidden when `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1`).

### `filterUserVisibleCases` logic

```typescript
// UserCaseListProgressPanel.tsx
cases.filter((c) => {
    if (c.workbench_test) return false;
    if (c.workbench_archived) return false;
    const cid = (c.client_id || '').trim();
    if (cid && clientId && cid !== clientId) return false;
    return true;
});
```

**Filters out:** test cases, archived cases, wrong broker client pack.  
**Does NOT filter by:** customer identity, phone, WeChat, session, or device.

**Data source:** `GET /api/inbox/cases?limit=30&offset=0` → `listRecentCasesPage()` → backend `list_recent_cases_for_read()` (JSON and/or Postgres).

List refreshes on mount and on `window.focus`.

---

## 3. Can customer resume previous case?

**No — not as a conversation builder.**

What exists today:

| Action | Behavior |
|--------|----------|
| Select case in list | Shows detail panel: lifecycle tag, `updated_at`, collected/missing fields, next-step hint |
| **「去客户报送继续」** | `onContinueInCustomerPortal()` → `setActiveTab('customer')` — **no `case_id` passed** |
| Customer Entry empty hint | Sets `lastCaseId` for single ongoing case — rarely fires for Add-Car (see Phase 1) |
| Post-handoff append | Requires `lastCaseId` in Customer Entry React state — lost on refresh |

**Gap:** `UnifiedIntakePage` has `brokerInitialCaseId` for broker tab but **no `customerInitialCaseId`** equivalent.

Customer can read progress in My Requests and manually go to Customer Entry, but must re-identify the case (or start fresh). Append path requires remembering/reference-copying `case_id` or still having post-submit UI in memory.

---

## 4. Is this production-ready?

| Dimension | Rating | Notes |
|-----------|--------|-------|
| **List + detail UI** | ✅ Demo-ready | Clean cards, lifecycle labels, field chips |
| **Data freshness** | ✅ | Refetch on focus |
| **Customer-scoped list** | ❌ | Shows all office cases for client pack |
| **Resume into builder** | ❌ | Tab switch only |
| **Pre-submit visibility** | ❌ | By design — session path separate |
| **Trial deploy visibility** | ❌ | Tab hidden in `productOnlyUi` mode |

**Verdict:** Production-ready as **office-shared case browser** for pilot demos with one customer at a time. **Not** production-ready as self-service "my cases" for real multi-customer traffic.

---

## 5. What data source powers it?

```
UserCaseListProgressPanel
  → listRecentCasesPage({ limit: 30, offset: 0 })
    → GET /api/inbox/cases
      → list_recent_cases_for_read() / list_cases_for_office_enforcement_read()
        → case_store JSON and/or Postgres service_record_repository
          → enrich_cases_for_workbench() (optional metadata)
```

### Fields displayed

- `userFacingCaseTitle()` — from `primary_vehicle_summary` or service lane
- `resolveCaseLifecycle()` — collecting / almost_ready / ready_for_handoff / submitted
- `updated_at`, `collected_fields`, `still_needed_fields`
- `nextStepHint()` — derived from `next_best_question` or still-needed fields

### Fields NOT displayed

- `case_messages[]` thread
- `case_activity[]` timeline
- `case_id` (not copyable in this panel)
- Append UI

---

## Architecture note

`MyRequestsTab` is intentionally thin — a wrapper delegating to `UserCaseListProgressPanel`. All logic lives in one component (~340 lines). No shared state with `CustomerEntryTab`.

---

## Verdict

My Requests proves **persistence and progress readback exist**. It does **not** complete the Customer Builder loop for return-and-continue. The missing wire is a single prop: pass selected `case_id` into Customer Entry and hydrate thread from `GET /api/inbox/cases/{id}` or enable append mode — **that wiring does not exist today** (validation finding only; out of sprint scope to build).
