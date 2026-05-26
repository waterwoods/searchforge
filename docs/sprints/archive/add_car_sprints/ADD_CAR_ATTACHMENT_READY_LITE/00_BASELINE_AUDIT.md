# Baseline Audit — Add-Car Attachment-Ready Lite

**Sprint:** Add-Car Attachment-Ready Lite  
**Purpose:** Honest audit of add-car flow from attachment/document realism perspective.

---

## 1. What Already Feels Structured and Real

| Area | Status | Notes |
|------|--------|-------|
| Quote-ready visibility | **Strong** | quote_ready / almost_ready / need_more in triage, case, workbench |
| Collected vs still-needed | **Strong** | year, make_model, zip, delivery_date, primary_driver, vin |
| Broker handoff | **Strong** | broker_next_step, client_prep, client_reply_draft |
| Customer identity | **Strong** | customer_name, customer_phone from triage extraction |
| Case persistence | **Strong** | case_store, append_follow_up_message, case_messages |

---

## 2. What Still Feels Document-Light or Fake

| Area | Status | Notes |
|------|--------|-------|
| Supporting materials | **Weak** | No upload; no registration, VIN photo, dec page |
| Material visibility | **Weak** | Broker cannot see if documents were received |
| Real office intake feel | **Weak** | Chat-only; real intake expects documents |
| Still-needed material cues | **Weak** | No "registration/dec page optional" |

---

## 3. Classification

| Category | Items |
|----------|-------|
| **Strong** | Quote-ready, collected/still-needed, broker handoff, identity, case persistence |
| **Acceptable** | Category display, urgency, follow-up tracking |
| **Weak** | Attachment intake, material visibility, still-needed material cues |
| **High-value to improve now** | Attachment intake, material visibility |

---

## 4. Biggest Current Weaknesses

| Weakness | Impact |
|----------|--------|
| **Biggest document-light/fake-feeling** | No way to upload or show supporting materials; add-car feels chat-only |
| **Biggest broker material-visibility gap** | Broker cannot tell if registration/VIN/dec page was received |
| **Biggest customer-trust gap** | Customer may have sent materials via WeChat/email; system has no record |

---

## 5. Current Assets to Reuse

- case_store: add case_attachments list; add_attachment_to_case
- Triage: quote_ready_status, collected_fields, still_needed_fields (unchanged)
- UI: Case detail layout, quote-ready badge, collected/still-needed tags
- API: /api/inbox/cases/{id} pattern for append, notes, follow-up

---

## 6. 10–20 Point Breakdown

1. **Why add-car still feels document-light today** — No upload; no registration/VIN/dec page support
2. **Which attachments matter most** — Registration, VIN photo, dec page, screenshot
3. **Which attachments are optional** — All; none mandatory
4. **Why uploads should not be mandatory** — Trial-friendly; chat-only must work
5. **How uploads should appear in UI** — Upload area in Customer Entry; optional
6. **How uploads should appear in workbench** — Badge on card; list in case detail
7. **How quote-ready interacts with attachments** — Separate signal; attachment does not change quote-ready
8. **When "attachment received" should show** — When case_attachments length > 0
9. **What broker should see** — Count, filename, type, "Materials received" vs "optional"
10. **What still-needed should show** — "Registration/dec page optional" when no attachment
11. **What most reduces broker rework** — Visible attachment list; no re-asking
12. **What most improves customer trust** — "Materials received" confirmation
13. **What most improves realism** — Add-car accepts documents like real office
14. **What should remain deferred** — OCR, extraction, mandatory upload
15. **Why OCR should stay out of V1** — Risky; not reliable; scope creep
16. **What V2 can add later** — OCR, auto-fill, document classification
17. **What simulations are needed** — Add-car + attachment scenarios
18. **What founder should manually test** — Upload flow, workbench display, 4–6 cases
