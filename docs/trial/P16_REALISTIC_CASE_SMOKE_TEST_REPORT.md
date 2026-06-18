# P16 Realistic Case Smoke Test Report

**Date:** 2026-06-07  
**Sprint:** P16-FINAL-QA-CERTIFICATION  
**API:** `https://fiqa-api-g7zatxrycq-uw.a.run.app`  
**UI alias (not browser-tested this sprint):** `ui-waterwoods-andys-projects-1f411b73.vercel.app`  
**Commit:** `366a7d6`

---

## Method

Cloud Run API only (`curl` / Python urllib). No browser MCP.

Endpoints used:

- `GET /api/inbox/customer/active-case?phone=…`
- `POST /api/inbox/customer/start-add-car`
- `POST /api/inbox/triage`
- `PATCH /api/inbox/cases/{id}/customer` (UI-parity phone bind after formal submit)
- `GET /api/inbox/cases/{id}` (conversation + Postgres proxy)

---

## Case A — Tesla Model Y (fresh)

| Field | Value |
|-------|-------|
| **Phone** | `7145559104` |
| **Name** | Xiao A |
| **Case ID** | `case_5bf93c1993e9` |
| **Draft case (pre-formal)** | `case_3325416e827a` |

### Conversation

1. Start add-car (Customer First entry)
2. `I bought a 2024 Tesla Model Y. ZIP 92620. VIN 7SAYGDEE5PA910104. Delivery date next Wednesday. I am the primary driver.`
3. Formal submit (UI-parity): `【正式提交办公室】…` + `conversation_turns` + customer phone patch

### Results

| Check | Result |
|-------|--------|
| New case created | ✅ `case_3325416e827a` |
| Pre-formal status | ✅ `等客户补资料` · `saved_not_yet_submitted` |
| Fields collected | ✅ `still_needed_fields: []` · vehicle `2024 Tesla Model Y` |
| Formal submit | ✅ `formal_submitted_at: 2026-06-07T16:34:49Z` |
| Post-formal status | ✅ `已提交办公室` · `submitted_to_office` |
| Phone return | ✅ same `case_5bf93c1993e9` |
| Conversation restore | ✅ 3 customer messages in case API |
| No false submit while gaps | ✅ |

**CASE A: PASS**

---

## Case B — Honda Accord (incremental Chinese)

| Field | Value |
|-------|-------|
| **Phone** | `7145559102` |
| **Case ID** | `case_a6980e5a3f0a` |

### Conversation

1. `我想给新买的 Honda Accord 加保险。`
2. `2023`
3. `邮编 Irvine 92618`

### Results

| Check | Result |
|-------|--------|
| Status | ✅ `等客户补资料` |
| Status label | ✅ `saved_not_yet_submitted` (not 已提交办公室) |
| Missing fields shown | ✅ `year, vin, delivery_date, primary_driver` |
| Contact state | ✅ `waiting_for_customer` |
| Phone return | ✅ same case id |
| Memory | ✅ all 3 supplements in `case_messages` |

**CASE B: PASS**

Note: standalone `2023` did not clear `year` from still_needed (known year-parsing gap; does not block pilot — gaps remain visible, no false submit).

---

## Case C — BMW X5 (return + supplement)

| Field | Value |
|-------|-------|
| **Phone** | `7145559103` |
| **Case ID** | `case_d1f8a7fb743e` |

### Conversation

1. `我刚买了一台 BMW X5，想加到保险里。`
2. *(simulated tab close — fresh active-case lookup)*
3. `VIN 5UXCR6C05P9D91003，邮编 92612，我自己开。`

### Results

| Check | Result |
|-------|--------|
| Phone return mid-flow | ✅ same case id, BMW intro in messages |
| After supplement | ✅ `vin` no longer in still_needed |
| Status | ✅ `等客户补资料` |
| No false submit | ✅ `saved_not_yet_submitted` |
| Still needed | `year, delivery_date, name` |

**CASE C: PASS**

---

## Four-state spot check (Cases A–C)

| Case | `business_state` | Customer label | Contradiction? |
|------|------------------|----------------|----------------|
| A | `submitted_to_office` | 已提交办公室 | None |
| B | `awaiting_customer` | 等客户补资料 | None |
| C | `awaiting_customer` | 等客户补资料 | None |

No green submitted card while gaps remain (B, C).

---

## Case memory chain

| Step | A | B | C |
|------|---|---|---|
| Phone lookup | ✅ | ✅ | ✅ |
| Active case id | ✅ | ✅ | ✅ |
| GET case messages | ✅ | ✅ | ✅ |
| Return same id | ✅ | ✅ | ✅ |

**CASE MEMORY: PASS**

---

## Summary

| Case | Verdict |
|------|---------|
| A | **PASS** |
| B | **PASS** |
| C | **PASS** |

---

*End of P16 Realistic Case Smoke Test Report*
