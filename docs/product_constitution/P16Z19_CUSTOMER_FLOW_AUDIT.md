# P16-Z19 Step 1 — Customer Flow Audit

**Date:** 2026-06-03  
**Sprint:** P16-Z19 Customer First Time-Saved Proof Sprint  
**Method:** Code trace + live API on `http://127.0.0.1:8001`  
**Constraint:** No new architecture — document what exists

---

## Validated path

```
CustomerEntryTab
  → triageMessage(text, persist_case=true, formal_submit?)
  → POST /api/inbox/triage
  → triage_conversation() / persist gate
  → save_case()  (when gates pass)
  → case_id
  → BrokerWorkbenchTab (GET /api/inbox/cases/{case_id})
  → appendFollowUpMessage(case_id, text)
  → POST /api/inbox/cases/{case_id}/append-message
  → same case_id
```

This path is **real, wired, and proven live** for Add-Car formal submit. Append continuity on the same `case_id` is proven (Z16/Z17 evidence + live run `case_3626b7457291`).

---

## Component map

| Layer | Location | Role |
|-------|----------|------|
| Customer UI | `ui/src/features/intake/components/CustomerEntryTab.tsx` | Paste, multi-turn, formal submit, post-handoff append |
| My Requests | `ui/src/components/intake/UserCaseListProgressPanel.tsx` | List persisted cases by `client_id` |
| API client | `ui/src/api/inboxTriage.ts` | `triageMessage`, `appendFollowUpMessage`, session restore |
| Route | `services/fiqa_api/routes/inbox_triage.py` | Triage + persist gate |
| Case store | `services/fiqa_api/inbox_triage/case_store.py` | `save_case()`, `append_follow_up_message()` |
| Session store | `services/fiqa_api/inbox_triage/session_store.py` | Pre-submit continuity |
| Broker UI | `ui/src/features/intake/components/BrokerWorkbenchTab.tsx` | Queue, glance, thread, append |

---

## What already works

### 1. Customer intake (Add-Car — mature lane)

| Step | Status | Evidence |
|------|--------|----------|
| Paste one message | ✅ | `submitMessage()` → `triageMessage()` |
| AI extracts slots | ✅ | `collected_fields`, `still_needed_fields` on system turn |
| Multi-turn pre-submit | ✅ | `session_id` in localStorage + Postgres `intake_sessions` |
| Session restore on refresh | ✅ | `GET /api/inbox/session/{id}` → toast「已恢复未完成的报送」 |
| Formal submit → `case_id` | ✅ | Live: `case_3626b7457291` from single rich paste + confirm line |
| `case_messages[]` at persist | ✅ | 3 sequenced messages in live payload |
| `formal_submitted_at` immutable | ✅ | Set once at `save_case()` |
| Post-handoff append (same session) | ✅ | `handlePostHandoffAppendSameCase()` while `lastCaseId` in React state |
| Boundary block for new issue | ✅ | `append_blocked_new_issue` → customer told to start new case |

**Persist gate (Add-Car):**

```python
should_persist = formal_submit and (struct_ok or handoff_ready)
```

Live Add-Car with full VIN/year/zip/driver in one paste → `handoff_ready: true` → formal submit → `case_id` in ~7s API time.

### 2. Broker workbench

| Capability | Status | Evidence |
|------------|--------|----------|
| Queue lists new cases | ✅ | `GET /api/inbox/cases` |
| Open case by `case_id` | ✅ | Full payload with thread + fields |
| See collected / missing | ✅ | `OfficeWorkbenchOneGlanceSummary` via `buildOfficeWorkbenchGlance()` |
| See broker next step | ✅ | English actionable line on live case |
| See message thread | ✅ | Last 5 `case_messages` in 对话记录 |
| Append from broker side | ✅ | `BrokerWorkbenchTab` → `appendFollowUpMessage()` |
| Copy client reply draft | ✅ | Available on case payload |

### 3. Generic intake (partial)

| Scenario | Triage quality | Persists to office? |
|----------|----------------|---------------------|
| Claim | ✅ Good field extraction | ❌ `handoff_ready: false` — no `case_id` without broker action |
| Underwriting doc | ✅ Category + still_needed | ❌ Same |
| Remove vehicle | ⚠️ Summary OK, `collected_fields` empty | ❌ Same |
| Payment / lapse | ❌ Classified `unclear` | ❌ Same |

Generic lanes **produce useful triage output** but do **not** auto-create office records on one paste today unless `handoff_ready` becomes true (rare on first turn).

---

## What is broken

| # | Issue | Impact | Blocks customer completing case? |
|---|-------|--------|----------------------------------|
| 1 | **Post-submit refresh loses Customer Entry context** | `clearSessionId()` + `lastCaseId` only in React state | ⚠️ Partial — case exists in My Requests but Customer Entry empty |
| 2 | **My Requests → 继续 does not pass `case_id`** | Tab switch only; no rehydrate | ⚠️ Customer cannot append after refresh without re-finding case |
| 3 | **Resume hint hides `submitted` lifecycle cases** | Filter `resolveCaseLifecycle(c) !== 'submitted'` | ⚠️ Post-handoff return path weak |
| 4 | **Generic scenarios don't persist on first paste** | No `case_id` for remove/payment/claim/UW in live test | ✅ Blocks **office handoff** for non-Add-Car; customer can still paste and see draft |
| 5 | **Payment Chinese lapse misclassified** | `issue_category: unclear` on live paste | ⚠️ Broker gets generic next step — time saved reduced |
| 6 | **`office_case_title` null on live cases** | Headline falls back to inferred category | ❌ Does not block completion — broker can still work case |
| 7 | **`broker_next_step` in English on Chinese intake** | Chen Kui reads slower | ❌ Does not block — adds ~5–10s broker read time |

---

## What blocks a customer from completing a case

### Hard blockers (cannot reach office timeline)

| Blocker | Who hit | Workaround today |
|---------|---------|------------------|
| Add-Car without VIN/zip/driver | Customer on sparse Day-1 message | Keep chatting until `handoff_ready`, then formal submit |
| Generic lane never reaches `handoff_ready` | Remove, payment, claim, UW one-paste customers | **No customer self-serve path to `case_id`** — broker must triage manually or customer must use Add-Car lane |
| Append after refresh without `case_id` | Returning customer | Use My Requests to **view** only; append broken until UX re-wires |

### Soft blockers (case created but friction remains)

| Blocker | Effect |
|---------|--------|
| Name/phone still needed on Add-Car | Case persists with `still_needed_fields: [delivery_date, name, phone]` — office can follow up |
| No cross-device identity | Same browser only for session restore |
| WeChat binding stub | Optional; not required for pilot |

---

## End-to-end flow diagram

```
                    CUSTOMER                           OFFICE
                    ────────                           ──────

[Empty] ──paste──► [AI draft in thread]
                         │
              pre-submit │ session_id + turns
                         ▼
              [Refresh?] ──yes──► session restore ✅
                         │
              Add-Car ready │
                         ▼
              [Formal submit] ──save_case()──► case_id ──► Broker queue ✅
                         │                                    │
              clearSessionId()                                 │
                         │                                    ▼
              [Refresh?] ──► UI empty ⚠️              Open case ✅
                         │                                    │
              My Requests ──► see case ✅                 Thread + fields ✅
                         │                                    │
              Append ──► only if lastCaseId in memory ⚠️   Append ✅
```

---

## Live evidence (2026-06-03)

**Add vehicle (full paste):**

| Field | Value |
|-------|-------|
| `case_id` | `case_3626b7457291` |
| `formal_submitted_at` | `2026-06-03T09:56:12Z` |
| `collected_fields` | year, make_model, vin, zip, primary_driver, insurance_status_add_to_existing |
| `still_needed_fields` | delivery_date, name, phone |
| `case_messages` | 3 entries |
| API time (paste + formal) | 7.4s |

---

## Verdict

| Question | Answer |
|----------|--------|
| Does CustomerEntryTab → formal_submit → save_case → case_id work? | **Yes** for Add-Car |
| Does append preserve same case_id? | **Yes** at API layer |
| Can every customer scenario complete without broker? | **No** — only Add-Car reliably persists today |
| Biggest customer-completion gap? | Post-submit return + generic lane persist |

**Flow audit: PASS for Add-Car north star path. PARTIAL for full 5-scenario portfolio.**
