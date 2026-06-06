# P16-Z18 Customer-First Architecture

**Date:** 2026-06-03  
**Sprint:** P16-Z18 Product Constitution Refresh  
**Scope:** **Current architecture only** — no future fantasy  
**Method:** Code trace + P16-Z16/Z17 live proof

---

## Canonical flow

```
Customer
    ↓
Customer Entry          (CustomerEntryTab.tsx — 客户报送)
    ↓
Draft Case              (POST /api/inbox/triage → triage.py)
    ↓
Case ID                 (formal_submit → save_case() → case_store.py)
    ↓
My Requests             (MyRequestsTab → UserCaseListProgressPanel)
    ↓
Append                  (POST .../cases/{id}/append-message → triage_for_append)
    ↓
Broker Workbench        (BrokerWorkbenchTab.tsx — same case_id)
    ↓
Timeline                (case_messages[] + case_activity[])
    ↓
Close                   (observation log + broker SOP — no closure UI yet)
```

---

## Layer diagram (as deployed in repo)

```
┌─────────────────────────────────────────────────────────────┐
│  UI — UnifiedIntakePage (tabs)                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ CustomerEntry│  │ MyRequests   │  │ BrokerWorkbench  │  │
│  │ Tab          │  │ Tab          │  │ Tab              │  │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘  │
└─────────┼─────────────────┼───────────────────┼────────────┘
          │                 │                   │
          ▼                 ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│  API — routes/inbox_triage.py                               │
│  POST /triage · GET /session/{id} · GET /cases · append     │
└─────────────────────────────┬───────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ triage.py       │ │ case_store.py   │ │ session_store.py│
│ case_draft_eng  │ │ SavedCase JSON  │ │ intake_sessions │
│ triage_for_append│ │ + PG mirror    │ │ (pre-submit)    │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

---

## Step-by-step (current behavior)

### 1. Customer → Customer Entry

| | |
|---|---|
| **Component** | `ui/src/features/intake/components/CustomerEntryTab.tsx` |
| **Identity** | `getOrCreateSessionId()` → `localStorage.unified_intake_session_id` |
| **Action** | Customer types message → Send |
| **API** | `POST /api/inbox/triage` via `triageMessage()` in `inboxTriage.ts` |

Pre-submit: multi-turn in React state + session store.  
Post-submit: post-handoff closure card + append panel (**in-memory `lastCaseId` only**).

---

### 2. Customer Entry → Draft Case

| | |
|---|---|
| **Engine** | `services/fiqa_api/inbox_triage/triage.py` |
| **Draft output** | category, `collected_fields`, `still_needed_fields`, `broker_next_step`, reply draft |
| **Persist gate** | `formal_submit: true` + structural truth OR `handoff_ready` |
| **Not yet persisted** | `persist_case: false` / pre-submit turns → session only |

Customer sees draft bubbles and gap list. Broker sees same shape if pasting in workbench.

---

### 3. Draft Case → Case ID

| | |
|---|---|
| **Trigger** | Customer clicks 正式提交办公室 (`formalSubmit=true`) |
| **Function** | `save_case()` in `case_store.py` |
| **Output** | `case_{hash}` e.g. `case_98f4ac099d15` |
| **Side effects** | `formal_submitted_at` set · `case_messages` seeded · `case_activity: case_created` · **`clearSessionId()`** |

Live proof: P16-Z17 case created 2026-06-03 on port 8001.

---

### 4. Case ID → My Requests

| | |
|---|---|
| **Component** | `MyRequestsTab` → `UserCaseListProgressPanel.tsx` |
| **API** | `listRecentCasesPage()` / `GET /api/inbox/cases` |
| **Shows** | case reference, lifecycle, collected gaps, updated_at |
| **Gap today** | 去客户报送继续 switches tab **without** `case_id` prop |

Customer can **discover** case after refresh. Cannot **resume** conversation in Customer Entry without wiring.

---

### 5. My Requests → Append

| | |
|---|---|
| **In-session path** | Customer Entry `handlePostHandoffAppendSameCase` → `appendFollowUpMessage()` |
| **API** | `POST /api/inbox/cases/{case_id}/append-message` |
| **Engine** | `triage_for_append()` → merge fields → `append_follow_up_message()` |
| **Broker path** | BrokerWorkbench append box (when `case_id` set) |

Same `case_id`, new `case_messages` sequences, `formal_submitted_at` unchanged. Proven 3-day Tesla simulation (P16-Z16).

---

### 6. Append → Broker Workbench

| | |
|---|---|
| **Component** | `BrokerWorkbenchTab.tsx` |
| **API** | `GET /api/inbox/cases/{id}` |
| **Reads** | Same `SavedCase` — summary, fields, thread (Z6), office value surface (Z11) |
| **Broker acts** | Copy draft · append · PATCH `waiting_on` |

Broker does not need customer chat open. P16-Z17: 11 messages visible after Day 3 append.

---

### 7. Broker Workbench → Timeline

| | |
|---|---|
| **Message thread** | `case_messages[]` — `{role, text, sequence, created_at}` |
| **Audit trail** | `case_activity[]` — `case_created`, `follow_up_added`, etc. |
| **Immutability** | `formal_submitted_at` never changes on append |
| **Broker UI** | 对话记录 (last 5 bubbles) after Z6 |
| **Customer UI** | Chat pre-handoff only; post-return thread **not wired** |

---

### 8. Timeline → Close

| | |
|---|---|
| **Product UI** | **None** — no closure button or outcome field |
| **Process** | Founder observation log · broker marks done in SOP |
| **Commercial** | Manual invoice · testimonial |

Close is **human + log**, not automated in MVP.

---

## Parallel broker entry (still exists, subordinate)

```
Broker → Broker Workbench → Paste → Draft Case → same case_store
```

Used for Chen Kui Day 0 wedge (cancel, payment paste). **Same engine, same case store** — not a separate architecture.

---

## Storage truth

| Store | Purpose | Required for MVP |
|-------|---------|------------------|
| `case_store.py` (JSON) | Case records, messages, activity | ✅ Always |
| Postgres service record | Production mirror | ⚠️ Recommended |
| `session_store.py` | Pre-submit multi-turn | ⚠️ Needs DB for prod restart survival |
| `localStorage` | session_id, (future) active_case_id | ✅ Same-browser |

---

## Known wiring gaps (architecture unchanged)

| Gap | Location | Fix type |
|-----|----------|----------|
| Post-submit Customer Entry empty | `CustomerEntryTab` mount | Wire hydrate `case_id` |
| My Requests handoff | `UnifiedIntakePage` callback | Pass `case_id` prop |
| Resume hint excludes submitted | `caseLifecycleDisplay.ts` | Policy fix |
| Preview ≠ local backend | Cloud Run deploy | Ops — not redesign |

**Do not add new layers.** Fix callbacks and storage keys.

---

## Anti-patterns (never in this diagram)

- Customer Builder microservice  
- Timeline service  
- Memory service  
- GraphRAG layer  
- CRM sync layer  
- Stripe billing layer  

All case truth lives in **`case_store.py` + `triage.py`** today.

---

*End of P16-Z18 Phase 6 — Customer-First Architecture*
