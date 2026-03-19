# Office Workflow / Handoff Packaging Spec

**Purpose:** Define what office side gets from the package, what the broker sees when a case is handed off, what is already collected, what the broker can do next, and how the package reduces manual follow-up.

---

## 1. What Office Side Gets From the Package

| Item | Description |
|------|-------------|
| **Unified intake surface** | One paste for customer messages; no separate inbox per channel |
| **Structured case card** | Case focus, Your next move, Collected, Still needed, Full conversation |
| **Queue view** | Work now / Waiting or parked; urgency; readiness |
| **Lightweight status** | new, reviewing, waiting_client, done |
| **Follow-up memory** | waiting_on, next_contact_by, broker note |
| **Client reply draft** | Editable; broker confirms before sending |

---

## 2. What the Broker Sees When a Case Is Handed Off

| Section | Content |
|---------|---------|
| **Case focus** | Add car quote · Premium review · Claim intake · Missing document · Payment risk |
| **Your next move** | One operational sentence: what the office should do next |
| **Collected** | Green chips: what the customer already provided |
| **Still needed** | Orange chips: what broker should ask or verify |
| **Client reply draft** | Handoff message: "报价资料已收集..." or "办公室会尽快处理..." |
| **Full conversation** | Raw [客户] / [系统] text for verification |

---

## 3. What Is Already Collected

| Scenario | Collected fields |
|----------|------------------|
| Add-car | year, model, zip, delivery, driver (when provided) |
| Missing doc | item requested, sent status |
| Renewal | policy, bill, remove intent |
| Cancellation | notice, payment proof |
| Claim | accident details, photos, other driver info |

---

## 4. What the Broker Should Be Able to Do Next

| Action | Supported |
|--------|-----------|
| Update status | new → reviewing → waiting_client → done |
| Set waiting_on | client, broker, carrier, underwriting |
| Set next_contact_by | Date for follow-up |
| Add broker note | Short note; appears in activity |
| Paste new customer message | Append → re-triage → update case |
| Copy draft | Clipboard copy for WeChat/email |

---

## 5. How the Package Reduces Manual Follow-up

| Pain | Package reduces it by |
|------|------------------------|
| Manual triage | One paste → structured case |
| Repeated explanation | Draft reply; broker edits |
| Lost follow-up | waiting_on, next_contact_by, broker note |
| Scattered context | One case per message; full conversation |

---

*End of Office Workflow / Handoff Packaging Spec*
