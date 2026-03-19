# Lightweight State Machine + Field Progress + Multi-Turn Strategy Blueprint

**Purpose:** Define a lightweight conversation-state framework for the 5 core business flows. Not a heavy workflow engine—a thin layer that helps the system know where it is, what's collected, what's missing, and how to reply.

**Scope:** Chen Kui Insurance Unified Entry — Customer Entry, Broker Workbench, 5 core flows.

**Created:** 2026-03-12 — Lightweight State Machine Sprint

---

## 1. What This Is (and Is NOT)

| Is | Is NOT |
|----|--------|
| A lightweight state-based layer | A full enterprise workflow engine |
| Helps decide: collect vs explain vs hand off | Orchestrates external systems |
| Per-flow field progress + follow-up type | Multi-tenant CRM or case routing |
| Explicit trust boundaries | Automated binding decisions |
| Improves multi-turn reply quality | A giant refactor of the whole app |

---

## 2. Global Conversation State Concept

The system derives a **conversation state** from:

| Dimension | Meaning | Example |
|----------|---------|---------|
| **issue_category / flow** | Which of the 5 flows we're in | add_car, missing_document, cancellation_warning, claim_intake, renewal_premium |
| **collection_stage** | Where we are in the detect→ask→enough?→handoff cycle | collecting, enough_for_handoff, handed_off |
| **collected_fields** | What we've extracted from the conversation | year, model, zip, customer_says_sent_dec_page |
| **still_needed_fields** | What would materially improve the case | primary_driver, delivery_date |
| **follow_up_type** | What kind of later-turn message the user sent | new_info, correction, already_sent, clarification_question, urgency_question, next_step_question |
| **ready_for_handoff** | Whether handoff threshold is met | true / false |
| **human_confirmation_required** | Whether broker must verify before acting | true for VIN, payment status, customer_says_sent |

**What state helps decide:**
- Should we ask one more thing or hand off?
- Should we explain (clarification) or collect (new info)?
- Should we use warmer handoff phrasing (already_sent) or generic?
- Which reply template fits this follow-up type?

---

## 3. Per-Flow State Examples

### 3.1 Cancellation / Notice / Payment Risk

| State | collection_stage | collected | still_needed | follow_up_type | Reply action |
|-------|------------------|-----------|--------------|---------------|--------------|
| Turn 1 vague | collecting | — | notice, payment_proof | — | Ask for notice/screenshot |
| Turn 2 sent | enough_for_handoff | notice_sent, screenshot | verify_receipt | already_sent | Hand off with "好的，收到了" |
| Turn 3 correction | enough_for_handoff | paid_claimed | verify_receipt | correction | Hand off with "好的，明白了" |
| Turn 3 clarification | enough_for_handoff | — | — | clarification_question | Answer "最要紧做什么" then hand off |

### 3.2 Missing Document / Underwriting Follow-up

| State | collection_stage | collected | still_needed | follow_up_type | Reply action |
|-------|------------------|-----------|--------------|---------------|--------------|
| Turn 1 need dec+garaging | collecting | requested_items | item_status | — | Ask for items, mention "发过了" path |
| Turn 2 dec resent | enough_for_handoff | dec_sent, garaging_missing | garaging_proof | new_info | Hand off with "好的，收到了" |
| Turn 3 "garaging 是什么意思" | enough_for_handoff | — | — | clarification_question | **Explain first** then hand off (SIM2 fix) |

### 3.3 Add-Car / Quote

| State | collection_stage | collected | still_needed | follow_up_type | Reply action |
|-------|------------------|-----------|--------------|---------------|--------------|
| Turn 1 model only | collecting | model | year, zip, delivery, driver | — | Ask year + zip |
| Turn 2 year | collecting | year, model | zip | new_info | Ask zip |
| Turn 3 zip+delivery | enough_for_handoff | year, model, zip, delivery | driver (optional) | new_info | Hand off |

### 3.4 Claim Intake

| State | collection_stage | collected | still_needed | follow_up_type | Reply action |
|-------|------------------|-----------|--------------|---------------|--------------|
| Turn 1 accident | collecting | accident_reported | photos, other_driver | — | First-step guidance |
| Turn 2 hit-and-run | enough_for_handoff | hit_and_run, plate | photos | new_info | Hand off |
| Turn 3 "最要紧做什么" | enough_for_handoff | — | — | next_step_question | Answer then hand off |

### 3.5 Renewal / Premium Review

| State | collection_stage | collected | still_needed | follow_up_type | Reply action |
|-------|------------------|-----------|--------------|---------------|--------------|
| Turn 1 premium high | collecting | premium_concern | policy_bill | — | Ask for policy/bill |
| Turn 2 sent bill | enough_for_handoff | policy_bill_sent | — | already_sent | Hand off |
| Turn 3 "去掉会便宜吗" | enough_for_handoff | remove_interest | which_vehicle | next_step_question | Answer + hand off |

---

## 4. Field Progress Model (Per Flow)

### 4.1 Add-Car

| Field | Critical? | Optional? | High-risk? | Human-confirm? | Enough for handoff? |
|-------|------------|------------|------------|----------------|---------------------|
| year | ✓ | | | | ✓ (with model) |
| make_model | ✓ | | | | ✓ (with year) |
| VIN | | ✓ | | ✓ | ✓ (replaces year+model) |
| zip | ✓ | | | | ✓ |
| delivery_date | | ✓ | | | ✓ (or zip or driver) |
| primary_driver | | ✓ | | ✓ | ✓ (or zip or delivery) |

**Enough when:** (year+model OR VIN) + (zip OR delivery OR driver)

### 4.2 Missing Document

| Field | Critical? | Optional? | High-risk? | Human-confirm? | Enough for handoff? |
|-------|------------|------------|------------|----------------|---------------------|
| requested_item | ✓ | | | | ✓ |
| customer_says_sent | ✓ | | | ✓ | ✓ |
| still_missing_item | ✓ | | | | ✓ |

**Enough when:** Item identified + sent status clear (sent, not sent, or "will send")

### 4.3 Cancellation / Payment Risk

| Field | Critical? | Optional? | High-risk? | Human-confirm? | Enough for handoff? |
|-------|------------|------------|------------|----------------|---------------------|
| notice | ✓ | | | | ✓ |
| payment_screenshot | ✓ | | | ✓ | ✓ |
| already_paid_claimed | ✓ | | | ✓ | ✓ |
| due_date_urgency | | ✓ | | | |

**Enough when:** Notice or screenshot or "I sent it" / "I paid" mentioned

### 4.4 Claim Intake

| Field | Critical? | Optional? | High-risk? | Human-confirm? | Enough for handoff? |
|-------|------------|------------|------------|----------------|---------------------|
| accident_reported | ✓ | | | | ✓ |
| hit_and_run | | ✓ | | | |
| photos | ✓ | | | ✓ | ✓ |
| other_driver_info | ✓ | | | ✓ | ✓ |
| police_report | | ✓ | | | |
| injuries | | ✓ | | | |

**Enough when:** 1–2 turns with accident details; photos and other-driver info mentioned or "will send"

### 4.5 Renewal / Premium Review

| Field | Critical? | Optional? | High-risk? | Human-confirm? | Enough for handoff? |
|-------|------------|------------|------------|----------------|---------------------|
| renewal_context | ✓ | | | | ✓ |
| premium_concern | ✓ | | | | ✓ |
| policy_bill_sent | ✓ | | | ✓ | ✓ |
| remove_vehicle_interest | | ✓ | | | |
| which_vehicle_to_remove | | ✓ | | ✓ | |

**Enough when:** Policy or bill mentioned

---

## 5. Follow-Up Type Strategy

### 5.1 Categories

| follow_up_type | Detection markers | Reply action | Collect? | Explain? | Hand off? |
|----------------|-------------------|--------------|----------|----------|----------|
| **new_info** | New field values (year, zip, dec page sent, photos) | Acknowledge + ask next OR hand off | ✓ | | ✓ when enough |
| **correction** | "不是", "不是这个", "说错了", "是另一辆" | Acknowledge correction + hand off | | | ✓ |
| **already_sent** | "发了", "发你", "发我", "sent", "截图", "screenshot" | Warmer handoff "好的，收到了" | | | ✓ |
| **clarification_question** | "什么意思", "要发什么", "what does", "garaging 是什么意思" | **Answer the question** + hand off | | ✓ | ✓ |
| **urgency_question** | "最要紧", "是不是今天", "一定要处理" | Answer urgency + hand off | | ✓ | ✓ |
| **next_step_question** | "先看什么", "办公室先看什么", "what matters most" | Answer next step + hand off | | ✓ | ✓ |
| **office_review_question** | "先看什么", "办公室会" | Same as next_step | | ✓ | ✓ |

### 5.2 Detection Logic (Lightweight)

- **already_sent:** `发`, `sent`, `截图`, `screenshot`, `发你`, `发我` (avoid bare `发` matching "要发什么")
- **correction:** `不是`, `不是这个`, `说错了`, `是另一辆`
- **clarification_question:** `什么意思`, `要发什么`, `what does`, `what is`, `garaging 是什么意思`, `declaration page 是什么`
- **urgency_question:** `最要紧`, `是不是今天`, `一定要处理`, `is this urgent`
- **next_step_question:** `先看什么`, `办公室先看什么`, `what matters most`, `what should I do`

### 5.3 Reply Strategy by Type

| Type | If handoff_ready | Reply |
|------|------------------|-------|
| new_info | Yes | Handoff phrase (add_car / other) |
| correction | Yes | other_corrected phrase |
| already_sent | Yes | other_received phrase ("好的，收到了") |
| clarification_question | Yes | **Answer question first** + handoff suffix |
| urgency_question | Yes | Answer urgency + handoff suffix |
| next_step_question | Yes | Answer next step + handoff suffix |

---

## 6. Human Confirmation Boundaries

### 6.1 Fields That Require Human Confirmation

| Field | Why |
|-------|-----|
| VIN | Wrong VIN → wrong quote; broker must verify |
| primary_driver | Affects premium; broker must confirm |
| policy_number | Binding identifier |
| due_date / payment_status | Business-critical; "customer says paid" ≠ verified |
| customer_says_sent_* | Broker must verify carrier actually received |
| quote implications | Never commit to a number without broker |
| business commitments | "我们会尽快" is OK; "保费一定降" is not |

### 6.2 When to Mark "Human Confirmation Recommended"

- `customer_says_sent_*` in collected_fields
- `vin` or `primary_driver` in collected_fields
- `payment_lapse_expiration` or `cancellation_warning` category
- Any "already paid" or "already sent" claim without carrier verification

### 6.3 When to Avoid Overcommitting

- Do not state a premium as final
- Do not promise "carrier has received" when customer said they sent
- Do not interpret ambiguous "last week" as a specific date

---

## 7. Implementation Notes

- **Triage module:** `services/fiqa_api/inbox_triage/triage.py`
- **Existing:** `_extract_add_car_fields`, `_extract_missing_doc_status`, `_add_car_enough_for_handoff`, handoff phrase keys (`other_received`, `other_corrected`, `other_clarification`)
- **To add:** `_derive_follow_up_type()`, `_derive_collection_stage()`, expose in triage result when useful
- **Config:** Handoff phrases in `configs/`; reply templates per category

---

*See also: `docs/MATURE_INTAKE_SKELETON.md`, `docs/TRUSTED_ASSISTANT_PLATFORM_BLUEPRINT.md`, `docs/CUSTOMER_ENTRY_REPLY_STRATEGY.md`*
