> **HISTORICAL / ARCHIVE — P9 Broker Surface Collapse (2026-05-30)**
> **Read instead:** [`docs/BROKER_ONE_PAGER.md`](../../../BROKER_ONE_PAGER.md), [`docs/BROKER_DEMO_FLOW.md`](../../../BROKER_DEMO_FLOW.md), [`docs/BROKER_TRIAL_PLAYBOOK.md`](../../../BROKER_TRIAL_PLAYBOOK.md)

# Broker Handoff Clarity Guide

**Purpose:** Define what a "clean enough broker handoff" should look like so the UI and logic can align to a practical target.

**Scope:** Unified Intake / Customer Entry / Broker Workbench mainline.

---

## 0. Unified Broker Workflow Language (Cross-Flow)

**Goal:** Same mental model across all 4 structured flows (Add Car, Renewal, Claim, Missing Document).

| Order | Section | What broker sees | Why |
|-------|---------|------------------|-----|
| 1 | **Case focus** | Add car quote · Premium review · Claim intake · Missing document | Triage at a glance |
| 2 | **Your next move** | One operational sentence: what the office should do next | Action clarity |
| 3 | **Collected** | Green chips: what the customer already provided | Avoid re-asking |
| 4 | **Still needed** | Orange chips: what broker should ask or verify next | Next ask clarity |
| 5 | **Full conversation** | Raw [客户] / [系统] text | Verification, context |

**Per-flow case focus:**

| Flow | Case focus label | What "Your next move" helps |
|------|------------------|----------------------------|
| Add car / new quote | Add car quote | Confirm missing driver/ZIP/VIN if needed, then quote or add same day |
| Renewal / premium | Premium review | Review renewal notice, confirm remove-vehicle or coverage-adjust intent |
| Claim intake | Claim intake | Guide client to collect evidence and start claim reporting |
| Missing document | Missing document | Verify whether customer-resubmitted items were received; request any still-missing |

**What stays in free-text summary:** Intent hint, message count, latest snippet, corrections. Structured chips take priority when present.

---

## 0a. Queue Triage at a Glance (Broker Case List)

**Goal:** Broker should decide which case to open first without opening every card.

**At minimum the queue should communicate:**

| Signal | What broker infers | Where it appears |
|--------|--------------------|------------------|
| **Urgency / priority** | Same-day vs routine | Urgency badge; "Action now" / "Due today" / "Your move" |
| **Case focus** | Add car, renewal, claim, missing doc, payment risk | Case focus label |
| **Readiness to act** | Ready for quote vs still needs key info | "Ready to act" vs "Needs more info" |
| **Follow-up state** | Broker's move vs waiting on client | "Your move" / "Waiting on client" |
| **Customer says already sent** | Missing-doc verification case | "Customer says sent" badge |
| **Work now vs parked** | Action section vs tracking section | Work now / Waiting or parked grouping |

**List-level useful snippets (compact):**

| Flow | Queue preview example |
|------|------------------------|
| Add car | "Collected: Year, Model, ZIP · Missing: Driver" |
| Renewal | "Premium concern · Missing renewal notice" |
| Claim | "Accident reported · Missing photos / other driver info" |
| Missing document | "Customer says dec page sent · Verify receipt" |
| Payment / cancellation | "Same-day action · Confirm balance due" |

**Triage tiers (lightweight):** urgent → active → waiting → parked. Not a full project manager; optimize for quick office triage.

---

## 0b. Lightweight Ticket / Follow-up Model (Daily-Use Continuity)

**Purpose:** Support day-to-day broker follow-up without building a heavy CRM.

| Concept | What it means | Where it appears |
|---------|---------------|------------------|
| **Status** | new, reviewing, waiting_client, done | Case card, queue |
| **Due-state** | Overdue, Due today, Due tomorrow, No due date | Case card, queue tags |
| **Last meaningful update** | Most recent of (broker note, activity) by timestamp; includes "Customer follow-up added" after append | Case card "Where this case stands", queue "Last update" |
| **Reopen context** | "Resume here" — waiting on + next contact + latest note | Case card when reopening saved case |
| **Waiting on** | none, client, broker, carrier, underwriting | Case card, queue |
| **Next step** | broker_next_step from triage | Case card "Your next move" |

**Reopen continuity:** When reopening a saved case, broker sees "Resume here" with follow-up summary and latest note so they can pick up where they left off.

**Paste new customer follow-up:** When the customer sends a new message, broker can paste it into the opened case and click "Update with new customer message." The system re-triages in context, updates source_text, broker_next_step, collected/still_needed, and last meaningful update. No inbox sync; broker pastes manually.

**What remains manual:** Inbox sync, email/WeChat integration. Broker pastes the new message; system updates the case.

**Daily-use polish (Broker Daily-Use Workflow Sprint):** After append, broker sees: (1) "Just updated with customer follow-up" badge in case card; (2) queue "Last update: Customer follow-up added: …" so what changed is visible without opening; (3) "Updated" tag on queue card for appended cases. Queue and case card both show the most recent of note vs activity by timestamp.

---

## 1. What the Broker Should See First

| Priority | Content | Why |
|----------|--------|-----|
| **1** | **Case focus** — What this case is mainly about (add car, premium review, missing doc, payment risk, etc.) | Broker can triage at a glance without reading raw text |
| **2** | **Your next move** — One operational sentence: check/confirm/resend/quote/remove | Broker knows exactly what to do |
| **3** | **Collected** (when applicable) — What the customer already provided | Broker avoids re-asking; can proceed faster |
| **4** | **Urgency** — Same-day vs routine | Broker prioritizes correctly |

---

## 2. What Collected Info Should Be Visible

| Case type | Collected fields | Display format |
|-----------|------------------|----------------|
| **Add car / quote** | year, model, zip, delivery, driver | "Collected: year, model, zip, delivery" |
| **Remove car** | vehicle, sale date, transfer status | "Collected: vehicle, sale date, transfer" (when extractable) |
| **Premium review** | policy/bill mentioned | "Collected: policy/bill mentioned" |
| **Missing document** | item(s) identified, sent status | "Collected: dec page resent; garaging proof still needed" |
| **Payment risk** | notice/screenshot mentioned | "Collected: client says sent screenshot" |

**Rule:** Only show "Collected:" when we can safely derive it from the conversation. Do not guess.

---

## 3. What Still-Missing Info Should Be Visible

| Case type | Still needed (when safe to infer) | Display format |
|-----------|-----------------------------------|----------------|
| **Add car** | delivery, driver (when year+model+zip present but those missing) | "Still needed: delivery date, main driver" |
| **Missing document** | specific item not yet resent | "Still needed: garaging proof" |
| **Others** | Defer to broker inference from source_text | — |

**Rule:** Only add "Still needed:" when it is cheap and safe to derive. Prefer broker inference over wrong guesses.

---

## 4. What broker_next_step Should Say

| Style | Good | Bad |
|-------|------|-----|
| **Operational** | "Confirm whether the payment actually failed, check whether the carrier still shows the balance due, and help the client fix it today." | "Review and follow up." |
| **Concrete** | "Collect the new vehicle details, confirm the delivery date and primary driver, then quote or add it the same day if possible." | "Handle the customer request." |
| **Action verbs** | check, confirm, resend, quote, remove, tell client what to bring | review, investigate, look into |

---

## 5. What conversation_summary Should Contain

| Component | When | Example |
|-----------|------|---------|
| **Intent hint** | Always | "Add-car / new vehicle quote. " |
| **Collected** | When extractable | "Collected: year, model, zip. " |
| **Message count** | Multi-turn | "2 customer message(s). " |
| **Latest snippet** | Multi-turn | "Latest: 2024年的，zip 90210，下周提车..." |

**Format:** `{intent_hint}{collected}{msg_count} Latest: {snippet}...`

---

## 6. Visual Hierarchy (Broker Case Card)

| Section | Prominence | Content |
|---------|------------|---------|
| **Case focus / category** | Tag, top | Add car quote, Premium review, Payment risk, etc. |
| **Your next move** | Bold, large | One operational sentence |
| **Collected** | Secondary, below next move | "Collected: year, model, zip" |
| **Still needed** | Secondary, only when safe | "Still needed: garaging proof" |
| **Client prep** | Card, secondary | What client should prepare |
| **Draft to send** | Card, secondary | Editable client reply |
| **Full conversation** | Collapsible or below fold | Raw [客户] / [系统] turns |

**Principle:** Broker should understand the case and next step without scrolling. Raw conversation is for detail, not first scan.

---

## 7. How Much Raw Conversation Should Remain Visible

| Scenario | Visibility |
|----------|------------|
| **Single message** | Show as "Message that opened this case" |
| **Multi-turn** | Show full [客户] / [系统] conversation; label as "Full conversation" |
| **Placement** | Below the action-focused section; broker can expand or scroll when needed |

**Principle:** Raw text supports verification and context. It should not dominate the first view.

---

## 8. Implementation Notes

- **Backend:** `_build_conversation_summary()` in `services/fiqa_api/inbox_triage/triage.py` produces intent + Collected + msg count + snippet.
- **Collected:** Currently implemented for add-car only. Extend to remove-car, missing-document, premium-review when extraction is safe.
- **Still needed:** Optional; add only when cheap (e.g. add-car: missing delivery/driver when year+model+zip present).
- **Structured fields (Add Car / New Quote Gap-Closing Sprint):** `triage_conversation()` and `triage_message()` now return `collected_fields` and `still_needed_fields` for add-car cases. These are lists (e.g. `["year", "make_model", "zip", "delivery_date"]`, `["primary_driver"]`) that complement the free-text `conversation_summary`. API route `/api/inbox/triage` includes them when the message is add-car.
- **Structured fields (Structured Workbench Expansion Sprint):** Renewal / Premium Too High and Claim Intake / Accident First Response now also produce `collected_fields` and `still_needed_fields`. Renewal: premium_concern, renewal_context, remove_vehicle_interest, coverage_adjust_interest, policy_bill_sent; still_needed: renewal_notice_or_bill, current_premium_details, which_vehicle_to_remove (if remove interest), target_coverage_preference (if coverage interest). Claim: accident_reported, hit_and_run, photos, other_driver_info, police_report, injuries; still_needed: photos, other_driver_insurance_license, accident_time_location, police_report_if_applicable.
- **Structured fields (Missing Document Sprint):** Missing Document / Underwriting Follow-up now produces `collected_fields` and `still_needed_fields`. Collected: requested_*item* (declaration_page, garaging_proof, driver_license, questionnaire), customer_says_sent_*item*, already_sent_claimed, underwriting_followup. Still needed: *item* when not yet sent; verify_carrier_received when customer claims already sent.
- **UI:** `UnifiedIntakePage.tsx` surfaces `collected_fields` and `still_needed_fields` as labeled chips (Collected / Still needed) when present. Add-car, renewal, claim, and missing-document cases show structured intake at a glance; other flows fall back to conversation_summary text.

---

*End of guide*
