# P16-Z17 Phase 2 — Return Later Test

**Date:** 2026-06-03  
**Sprint:** P16-Z17 Customer Case Builder Reality Sprint  
**Scenario:** Day 1 — "I bought a Tesla." → leave → refresh / close / reopen  
**Server:** `http://127.0.0.1:8001` (live)

---

## Test matrix

| Phase | Leave mechanism | Can customer find same case? | Evidence |
|-------|-----------------|------------------------------|----------|
| **Pre-submit** (no `case_id`) | Refresh browser | ✅ Same conversation | Session restore |
| **Pre-submit** | Close + reopen (same browser) | ✅ If localStorage intact | `unified_intake_session_id` |
| **Post-submit** (has `case_id`) | Refresh Customer Entry | ⚠️ Case exists, UI empty | `lastCaseId` lost |
| **Post-submit** | My Requests tab | ✅ Case listed | `GET /api/inbox/cases` |
| **Post-submit** | Customer Entry resume hint | ❌ Hidden for `submitted` lifecycle | Code filter |
| **Post-submit** | My Requests → 去客户报送继续 | ⚠️ Switches tab only | No `case_id` passed |

---

## Day 1 — Start case (pre-submit)

**Customer message:** "I bought a Tesla."

| Record | Value |
|--------|-------|
| **session_id** | `d241e5c4-5cf2-4faf-b81d-7cb80801cf7c` |
| **case_id** | `null` |
| **collected_fields** | `['make_model', 'insurance_status_new_customer']` |
| **still_needed_fields** | `['year', 'make_model', 'vin', 'zip', 'delivery_date', 'primary_driver']` |
| **case_messages** | None (pre-submit) |
| **case_activity** | None (pre-submit) |

Customer leaves with `localStorage.unified_intake_session_id` set.

---

## Simulate refresh (pre-submit)

**API:** `GET /api/inbox/session/d241e5c4-5cf2-4faf-b81d-7cb80801cf7c`

| Check | Result |
|-------|--------|
| HTTP status | 200 |
| Turns restored | 2 (customer + system) |
| workflow_state.collected_fields | `['make_model', 'insurance_status_new_customer']` |

**UI path:** `CustomerEntryTab` mount effect → `getSessionId()` → `getInProgressSession(sid)` → `setTurns(restored)` + toast「已恢复未完成的报送」.

**Verdict:** ✅ **Pre-submit return later works** on same browser when Postgres session store is configured (live server returned 200).

---

## Simulate close browser + reopen (pre-submit)

Mechanism: `localStorage` key `unified_intake_session_id` survives browser close on same origin/profile.

**Verdict:** ✅ Same as refresh — **if** localStorage persists and session row exists on server.

**Fails when:** Incognito end, cleared site data, different device, or no DB session backend.

---

## Sprint expectation: "Create case" on Day 1 with Tesla only

**Live test:** Formal submit after partial info (no VIN):

| Field | Value |
|-------|-------|
| **case_id** | `null` |
| **Blocked reason** | `struct_ok` requires VIN; `handoff_ready` false without `quote_ready` |

**Reality:** Day 1 "I bought a Tesla" alone does **not** create a persisted case. It creates an **in-progress session**. This matches product policy — Add-Car office records require structural completeness or explicit handoff confirmation.

---

## Post-submit leave (after formal submit)

Live case: `case_98f4ac099d15` created at `2026-06-03T08:58:13Z`.

| Asset after leave | State |
|-------------------|-------|
| `localStorage` session | Cleared by UI (`clearSessionId()` on case return) |
| React `lastCaseId` | Lost on refresh |
| Case store | ✅ Case survives |
| `GET /api/inbox/cases` | ✅ Case findable (`case_findable_via_GET_cases: true`) |

### Can customer find the same case after refresh?

| Surface | Answer |
|---------|--------|
| **My Requests** (`UserCaseListProgressPanel`) | ✅ Yes — lists case with collected/missing fields, timestamps |
| **Customer Entry empty state** | ❌ No auto-resume for `submitted` lifecycle |
| **Customer Entry resume hint** | Only shows cases where `resolveCaseLifecycle(c) !== 'submitted'` — post-handoff cases excluded |

```typescript
// CustomerEntryTab.tsx ~224-226
const ongoing = visible.filter(
    (c) => triageResultLooksLikeAddCar(c) && resolveCaseLifecycle(c) !== 'submitted',
);
```

Submitted cases (`formal_submitted_at` set) → lifecycle `submitted` → **no empty-state resume button**.

### My Requests → continue

```typescript
// UserCaseListProgressPanel.tsx ~326-329
<Button onClick={onContinueInCustomerPortal}>去客户报送继续</Button>
// UnifiedIntakePage: only setActiveTab('customer') — does NOT pass case_id
```

**Verdict:** ⚠️ Customer can **see** the case in My Requests but cannot **continue append** in Customer Entry after refresh without re-wiring.

---

## Answer

| Question | Answer |
|----------|--------|
| Can customer return to pre-submit work? | **Yes** — session restore proven |
| Can customer return to post-submit case? | **Partially** — case visible in My Requests; Customer Entry does not rehydrate |
| Does "I bought a Tesla" alone create `case_id`? | **No** — session only until formal submit gates pass |

---

## Phase 2 score implication

**Return Later: 58/100** — Strong pre-submit; post-submit UX gap is the main blocker for "never start over."
