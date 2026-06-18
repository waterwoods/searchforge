# P16 Customer Rehydration — Controlled Reproduction

**Sprint:** P16-CUSTOMER-FIRST-CASE-REHYDRATION-ROOT-CAUSE-SPRINT  
**Date:** 2026-06-07  
**Environment:** Cloud Run QA API (`https://fiqa-api-g7zatxrycq-uw.a.run.app`) + local Python triage harness  
**UI reference:** `https://ui-waterwoods-andys-projects-1f411b73.vercel.app/workbench/unified-intake?tab=customer`

---

## Test setup

| Item | Value |
|------|-------|
| Fresh phone | `6265550888` |
| Customer name | `P16测试` |
| Flow | Customer First → start add-car draft → two triage turns → phone lookup → full case GET |
| API auth | `X-Unified-Intake-Api-Key` (from `.env.cloudrun`, not printed) |

---

## Scenario steps and observations

### Step 1 — Enter phone / start add-car

**API:** `POST /api/inbox/customer/start-add-car`

```json
{ "phone": "6265550888", "customer_name": "P16测试" }
```

**Response (200):**

- `case_id`: `case_9a86a610fb66`
- Draft `still_needed_fields`: `["year","make_model","zip","delivery_date","primary_driver","vin"]`
- Draft `collected_fields`: `[]`

**UI state (expected):** Customer First gate passes; add-car starter message sent; `lastCaseId` bound.

---

### Step 2 — Customer message (turn 1)

**Customer says:**

> 我刚刚买了一台二零二五年的宝马X5，提车日是七月一号二零二六年。

**API:** `POST /api/inbox/triage`

```json
{
  "text": "我刚刚买了一台二零二五年的宝马X5，提车日是七月一号二零二六年。",
  "persist_case": true,
  "case_id": "case_9a86a610fb66",
  "conversation_turns": [
    { "role": "customer", "text": "我想加一台车，开始报价资料。" },
    { "role": "system", "text": "好的，请告诉我车辆信息。" }
  ]
}
```

**Response (200) — triage result:**

| Field | Value |
|-------|-------|
| `collected_fields` | `["make_model", "insurance_status_add_to_existing"]` |
| `still_needed_fields` | `["year", "make_model", "vin", "zip", "delivery_date", "primary_driver"]` |
| `case_id` | `case_9a86a610fb66` (echoed from existing draft) |

**UI state:** System reply asks for missing slots; status surface would show **年份** (year) still needed because `year ∉ collected_fields`.

**Note:** Chinese numerals `二零二五年` / `二零二六年` are **not** matched by ASCII `20[12][0-9]` year regex — turn 1 never collects year.

---

### Step 3 — Customer supplement (turn 2)

**Customer says:**

> 2027

**API:** `POST /api/inbox/triage` (same `case_id`, prior turns in `conversation_turns`)

**Response (200):**

| Field | Value |
|-------|-------|
| `collected_fields` | `["make_model", "insurance_status_add_to_existing"]` — **year still absent** |
| `still_needed_fields` | `["year", "make_model", "vin", "zip", "delivery_date", "primary_driver"]` |

**UI state:** **Issue 1 reproduced** — 年份 remains in Still Needed / missing-field surface after customer supplied `2027`.

---

### Step 4 — Active-case lookup (phone return, new tab equivalent)

**API:** `GET /api/inbox/customer/active-case?phone=6265550888`

**Response (200):**

```json
{
  "has_active_case": true,
  "phone_normalized": "6265550888",
  "active_case": {
    "case_id": "case_9a86a610fb66",
    "vehicle_display": "加车申请（车辆信息待补充）",
    "missing_fields": ["year", "make_model", "zip", "delivery_date", "primary_driver", "vin"],
    "still_needed_fields": ["year", "make_model", "zip", "delivery_date", "primary_driver", "vin"],
    "contact_state": "waiting_for_customer",
    "status_label": "saved_not_yet_submitted",
    "lifecycle_status": "collecting"
  }
}
```

**Payload gaps (by design today):** No `source_text`, `case_messages`, conversation turns, timeline, or `client_reply_draft`.

---

### Step 5 — Full case GET (hydration path after “Continue Request”)

**API:** `GET /api/inbox/cases/case_9a86a610fb66`

**Response (200) — persisted record:**

| Field | Value |
|-------|-------|
| `collected_fields` | `[]` (never updated by triage) |
| `still_needed_fields` | `["year", "make_model", "zip", "delivery_date", "primary_driver", "vin"]` (draft defaults) |
| `case_messages` | **1 message only** |
| `source_text` | `[客户] 开始加车申请（Customer First 入口）` |

**Only persisted message:**

```
[customer] 开始加车申请（Customer First 入口）
```

BMW message and `2027` reply are **not** in `case_messages` or `source_text`.

**UI hydration (`customerEntryTurnsFromSavedCase`):** Would restore **one** customer line (draft starter) — not the full BMW + 2027 conversation.

**Issue 2 reproduced:** Phone lookup finds active case; conversation history is not rehydrated.

---

## API call summary

| # | Method | Endpoint | Purpose | Issue |
|---|--------|----------|---------|-------|
| 1 | POST | `/api/inbox/customer/start-add-car` | Claim phone, create collecting draft | — |
| 2 | POST | `/api/inbox/triage` | Turn 1 — BMW Chinese message | Issue 1 seed (year not extracted) |
| 3 | POST | `/api/inbox/triage` | Turn 2 — `2027` supplement | Issue 1 (year still in still_needed) |
| 4 | GET | `/api/inbox/customer/active-case?phone=` | Phone return key | Issue 2 surface (summary only) |
| 5 | GET | `/api/inbox/cases/{case_id}` | Continue / hydrate path | Issue 2 (1 message, no chat) |

---

## Local harness confirmation (no server)

```bash
PYTHONPATH=. python3 -c "
from services.fiqa_api.inbox_triage.truth_field_guardrails import should_accept_field
print(should_accept_field('year', '2027', True, customer_bubbles=['2027']))
# (False, 'no_explicit_vehicle_identity', 'no_explicit_vehicle_identity')
"
```

Evidence artifact: `/tmp/p16_repro_evidence.json` (from live run).

---

## Reproduction verdict

| Issue | Reproduced | Layer |
|-------|:----------:|-------|
| **1 — Year not cleared after `2027`** | ✅ Live + local | Backend extraction + truth guardrails |
| **2 — Phone return loses conversation** | ✅ Live | Backend persistence gap + frontend hydration depends on empty `case_messages` |

Both defects are **deterministic** on QA backend with a fresh phone number.
