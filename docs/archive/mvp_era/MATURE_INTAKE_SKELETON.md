# Mature Intake Skeleton — Design

**Purpose:** Define the shared intake flow that all high-value Chen Kui insurance scenarios follow. One reusable skeleton, not custom one-off flows.

**Scope:** Unified Intake / Customer Entry / Broker Workbench mainline only.

---

## 1. Shared Stages

Every customer scenario follows the same four-stage shape:

| Stage | Name | What happens |
|-------|------|---------------|
| **1** | **Detect likely intent** | Classify the inbound message (add-car, remove-car, premium review, payment risk, notice confusion, missing doc, DMV/SR-22, claim intake, unclear). |
| **2** | **Ask the next most useful thing** | Reply with 1–2 focused questions. Do not overload. Do not use generic "please provide more context" when intent is obvious. |
| **3** | **Decide if enough info is collected** | Apply per-category handoff thresholds. Either ask one more thing or hand off. |
| **4** | **Hand off with summary/context** | Persist case to broker workbench with `conversation_summary`, `broker_next_step`, `client_reply_draft`, and full `source_text`. |

**Flow shape:** `detect → ask → enough? → hand off`

---

## 2. Shared Design Rules

| Rule | Meaning |
|------|---------|
| **Ask only 1–2 next things** | Per turn, ask for the next most useful field(s). Do not list 6 items at once. |
| **Do not over-question** | Once enough info is collected, hand off. Do not become a long-form chatbot. |
| **Do not stop too early** | If one critical field would materially improve the case, ask for it before handoff. (Add-car: ask for zip when only year given.) |
| **Do not keep chatting once clean enough** | Hand off when thresholds are met. Max 2–3 customer turns before handoff for most categories. |
| **Keep tone calm and office-natural** | Chen Kui proxy style: conclusion first, next step second. No formal letter tone, no generic AI empathy. |
| **Keep broker handoff cleaner than raw message** | `conversation_summary` and `broker_next_step` must be more actionable than the raw customer text. |

---

## 3. Shared Handoff Threshold Logic

### 3.1 When is a case "clean enough"?

| Category | Enough when |
|----------|-------------|
| **新车 / 加车报价** | (year + model or VIN) + (zip OR delivery OR driver). |
| **删车 / 保单变更** | Vehicle identified + (sale date OR transfer status). |
| **保费太高 / renewal** | Policy or bill mentioned. |
| **付款失败 / cancellation risk** | Notice, screenshot, or "I sent it" / "I paid" mentioned. |
| **英文 notice confusion** | Full notice or clear summary provided. |
| **缺材料 / dec page / DL / garaging** | Item identified + sent status clear. |
| **DMV / SR-22 help** | DMV notice or enough context to advise. |
| **事故 / Claim intake** | Accident details, photos, other driver info mentioned. |

### 3.2 When to ask one more thing

- **Add-car:** When year+model present but zip, delivery, and driver all missing → ask for zip (or delivery/driver).
- **Other categories:** After 2 turns, hand off. Do not repeat the same ask.

### 3.3 When to allow a third turn

- **Add-car only:** When turn 2 gives only partial info (e.g. year only), ask for zip; turn 3 zip → hand off.
- **All others:** Hand off after 2 customer turns.

### 3.4 When to stop and hand off

- Threshold met (see 3.1).
- OR customer turn count ≥ 2 (for non–add-car).
- OR customer says "先这样", "你先看", or similar.
- OR `manual_followup_needed` is false (informational, renewal reminder, etc.).

---

## 4. Scenario-to-Skeleton Mapping

| Scenario | Detect | Ask | Enough? | Hand off |
|----------|--------|-----|---------|----------|
| **新车 / 加车报价** | add-car + vehicle context | year, model, VIN, zip, delivery, driver | year+model + zip/delivery/driver | "报价资料已收集，办公室会尽快出价" |
| **删车 / 保单变更** | remove-car + vehicle | sale date, vehicle details, transfer | vehicle + sale date/transfer | "办公室会尽快处理" |
| **保费太高 / renewal** | premium review markers | policy, renewal notice, bill | policy or bill mentioned | "办公室会尽快处理" |
| **付款失败 / cancellation risk** | payment/cancel markers | notice, payment screenshot | notice or proof mentioned | "办公室会尽快处理" (urgent) |
| **英文 notice confusion** | notice + confusion markers | full notice or clearer photo | full notice or summary | "办公室会尽快处理" |
| **缺材料 / dec page / DL / garaging** | missing doc markers | exact item, whether sent | item + sent status | "办公室会尽快处理" |
| **DMV / SR-22 help** | DMV/SR-22 + help markers | DMV notice, suspension letter | notice or enough to advise | "办公室会尽快处理" |
| **事故 / Claim intake** | claim_intake markers | accident details, photos, other driver info | 1–2 turns | "办公室会尽快处理" |

---

## 5. Broker Handoff Consistency

When handoff occurs, the broker case receives:

| Field | Content |
|-------|---------|
| `source_text` | Full `[客户]` / `[系统]` conversation |
| `conversation_summary` | Intent hint + "Collected:" (when add-car) + message count + latest snippet |
| `broker_next_step` | One operational sentence: check/confirm/resend/quote/remove/tell client what to bring |
| `client_reply_draft` | Handoff message: "报价资料已收集..." (add-car) or "办公室会尽快处理..." (others) |
| `what_still_needed` | (Deferred) Broker infers from `source_text` and `conversation_summary` |

**broker_next_step style:** Read like a real office work instruction. Mention concrete document, deadline, payment, or vehicle when known.

---

## 6. Implementation Notes

- **Triage module:** `services/fiqa_api/inbox_triage/triage.py`
- **Intent detection:** `_is_add_vehicle_request`, `_is_remove_vehicle_request`, `_is_premium_review_request`, `_is_sr22_help_request`, etc.
- **Handoff logic:** `_should_handoff()`, `_get_next_ask_draft()`, `_add_car_enough_for_handoff()`
- **Summary builder:** `_build_conversation_summary()`
- **Strategy doc:** `docs/CUSTOMER_ENTRY_REPLY_STRATEGY.md` §4

---

---

## 7. Sprint Report Reference

Sprint report: `docs/MATURE_INTAKE_SKELETON_ALIGNMENT_SPRINT_REPORT.md` (created by Mature Intake Skeleton Alignment Sprint).

*End of skeleton design*
