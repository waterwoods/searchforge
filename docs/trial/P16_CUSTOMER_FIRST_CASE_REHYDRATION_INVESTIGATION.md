# P16 Customer First Case Rehydration — Investigation Report

**Sprint:** P16-CUSTOMER-FIRST-CASE-REHYDRATION-ROOT-CAUSE-SPRINT  
**Date:** 2026-06-07  
**Status:** Root causes confirmed (live QA API + code audit)  
**Artifacts:**  
- `P16_CUSTOMER_REHYDRATION_REPRODUCTION.md`  
- `P16_APPEND_YEAR_FIELD_ROOT_CAUSE.md`  
- `P16_PHONE_RETURN_REHYDRATION_ROOT_CAUSE.md`

---

## Executive summary

Two Customer First defects on QA Preview share a persistence/extraction theme but have **distinct root causes**:

| Issue | Root cause (one line) | Layer |
|-------|----------------------|-------|
| **1 — Year not cleared after `2027`** | Strict truth guardrails reject standalone year tokens (`no_explicit_vehicle_identity`); Chinese `二零二五年` invisible to year regex | **Backend** |
| **2 — Phone return loses conversation** | `/api/inbox/triage` with bound `case_id` never calls `append_follow_up_message`; in-progress session save skipped when `case_id` present | **Backend** (+ API shape) |

Frontend faithfully renders API truth. Database contains draft-only messages after multi-turn intake.

---

## 1. Root cause — Issue 1 (year field)

### Mechanism

1. **Turn 1:** `二零二五年` not matched by `text_has_vehicle_year_signal` (ASCII-only). `make_model` collected; `year` → `still_needed`.
2. **Turn 2:** `2027` detected by rule layer, then **rejected** by `should_accept_field("year", …)` because `utterance_has_explicit_vehicle_identity("2027")` is false (year alone, no make/model in same bubble).
3. `_add_car_structured_fields` leaves `year` in `still_needed_fields`.
4. Triage response shows 年份; **persisted case never updated** (`collected_fields: []` on GET).

### Not the cause

- Year range validation (2027 is valid).
- Append field merge dropping year (year never enters `new_collected`).
- Frontend stale cache.
- Overwrite of 2025 with 2027 (2025 never extracted).

**Detail:** `P16_APPEND_YEAR_FIELD_ROOT_CAUSE.md`

---

## 2. Root cause — Issue 2 (phone return / rehydration)

### Mechanism

1. Customer First `start-add-car` persists a **one-message draft**.
2. Each collecting turn uses `/api/inbox/triage` with `case_id` → response includes `case_id` → **blocks** in-progress session save (`not result.get("case_id")`).
3. **`append_follow_up_message` not invoked** from triage route (only from `/cases/{id}/append-message`, used post-handoff in UI).
4. New tab: `active-case` finds case (summary only — no chat by contract).
5. Continue → `getSavedCase` → `case_messages` length **1** → hydration cannot rebuild BMW / 2027 thread.

### Not the cause

- Phone lookup failure (works).
- Postgres unavailable (case row exists).
- Frontend ignoring returned messages (none returned).
- active-case endpoint regression (summary-only is intentional; gap is **empty** full case).

**Detail:** `P16_PHONE_RETURN_REHYDRATION_ROOT_CAUSE.md`

---

## 3. Backend vs frontend classification

| Concern | Owner |
|---------|-------|
| Year extraction / guardrails | **Backend** (`truth_field_guardrails.py`, `add_car_vehicle_signals.py`) |
| Chinese year numerals | **Backend** |
| Collecting-turn message persistence | **Backend** (`routes/inbox_triage.py`) |
| active-case summary shape | **Backend API design** (not a bug; incomplete for memory story) |
| Chat bubble rendering | Frontend (correct) |
| Phone entry / Continue wiring | Frontend (correct) |
| Hydration from `case_messages` | Frontend (correct — data absent) |

---

## 4. Database evidence

**Live case:** `case_9a86a610fb66` · phone `6265550888` · Cloud Run QA · 2026-06-07

| Field | Value after 2 triage turns |
|-------|----------------------------|
| `customer_phone` | `6265550888` |
| `lifecycle_status` | `collecting` |
| `case_messages` | 1 × `[customer] 开始加车申请（Customer First 入口）` |
| `source_text` | `[客户] 开始加车申请（Customer First 入口）` |
| `collected_fields` | `[]` |
| `still_needed_fields` | `["year","make_model","zip","delivery_date","primary_driver","vin"]` |

No BMW text, no `2027`, no system replies stored.

---

## 5. API evidence

| Call | Key result |
|------|------------|
| `POST /api/inbox/triage` (BMW message) | `collected_fields` without `year` |
| `POST /api/inbox/triage` (`2027`) | `still_needed_fields` still contains `year` |
| `GET /api/inbox/customer/active-case?phone=6265550888` | `has_active_case: true`, `still_needed_fields` includes `year` |
| `GET /api/inbox/cases/case_9a86a610fb66` | `case_messages.length === 1` |

---

## 6. UI evidence

| Surface | Observed |
|---------|----------|
| QA Customer tab — Still Needed | 年份 remains after `2027` |
| QA — new tab phone entry | Active case card OK; no prior chat |
| QA — Continue Request | No full conversation restore |
| Code path | `CustomerFirstEntryScreen` → active-case summary; `hydrateFromSavedCase` → `customerEntryTurnsFromSavedCase` with empty thread |

Matches API payloads; no UI-only defect found.

---

## 7. Severity

| Issue | Severity | Rationale |
|-------|----------|-----------|
| **Issue 1 — Year append** | **P1** | Breaks Chinese + supplement intake; customer answered; blocks quote-ready path |
| **Issue 2 — Phone rehydration** | **P1** | Breaks P16 phone return key for **memory**; multi-tab / return-later story fails |

Neither is P0 (case exists, phone lookup works, no data loss for office if broker opens workbench with future fixes). Both are above P2 for paid pilot with Chinese customers.

---

## 8. Minimal fix options

### Issue 1

| Option | Effort | Risk |
|--------|--------|------|
| **A. Accept standalone `20xx` year when thread has make/model** (`truth_field_guardrails`) | ~0.5 d | Low |
| **B. Chinese year numeral normalization** (`add_car_vehicle_signals`) | ~0.5 d | Low |
| **C. Persist slot lists on bound-case triage** (shared with Issue 2) | ~1 d | Low–med |

**Recommended:** A + B (+ C for active-case accuracy).

### Issue 2

| Option | Effort | Risk |
|--------|--------|------|
| **D. Call `append_follow_up_message` from triage when `case_id` bound** | ~1 d | Low (existing primitive) |
| **E. Optional: last N messages on active-case** | ~0.5 d | Low after D |
| **F. Session fallback without clearing `session_id`** | ~0.25 d | Partial (same-device only) |

**Recommended:** D (required); E optional; F not sufficient alone.

---

## 9. Recommendation

1. **Implement D first** — restores conversation + enables hydration + unblocks office-visible thread.
2. **Implement A + B** — fixes year supplement and Chinese year on turn 1.
3. **Ensure C** — field lists written on append so `active-case` Still Needed matches chat.
4. **Re-run** `P16_CUSTOMER_REHYDRATION_REPRODUCTION.md` scenario as acceptance gate.
5. **Do not** ship CRM, new chat stack, or constitution changes.

Estimated total: **2–3 engineer-days**, all within Customer First Constitution.

---

## 10. Demo verdict — Chen Kui / Wu Xiaojie

### **CONDITIONAL GO**

| Criterion | Status |
|-----------|--------|
| Phone lookup finds active case | ✅ GO |
| Status surface (Still Needed, contact state) | ✅ GO (shows draft truth — may be wrong until fixes) |
| Chinese vehicle message → structured year | ❌ NO-GO |
| Supplement year clears 年份 | ❌ NO-GO |
| Return on new tab with conversation memory | ❌ NO-GO |
| Office-visible thread for broker | ❌ NO-GO until append wired |

### Safe demo script (today)

- Phone entry → active case detection → status labels.
- **Avoid:** Chinese year-only supplement loop; new-tab “continue where I left off” chat story.
- **Broker path:** Use workbench on same session without refresh, or disclose that return-later chat is not yet wired.

### Upgrade to GO after

- [ ] Reproduction scenario passes on QA Preview (year collected; `case_messages` ≥ 4 after 2 turns).
- [ ] `GET active-case` Still Needed matches last triage turn.
- [ ] New tab Continue restores BMW + 2027 + system replies.

---

## Sign-off

| Role | Verdict |
|------|---------|
| Engineering | Root cause closed — backend extraction + persistence |
| Product / Pilot | CONDITIONAL GO — status surface demo OK; memory + year loop blocked |

**No further investigation required** for these two defects; proceed to minimal fix implementation when approved.
