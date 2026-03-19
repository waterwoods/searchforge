# Handoff / Office Next Action Spec

**Sprint:** Trial Execution Readiness + Last-Mile Hardening  
**Created:** 2026-03-18  
**Purpose:** Define what the office most needs to see after handoff, what next action should be visible, what correction/context should stand out, what makes handoff truly usable in a live trial.

---

## 1. What the Office Most Needs to See After Handoff

| Priority | Content | Why |
|----------|---------|-----|
| **1** | **Case focus** | Add car quote · Premium review · Missing document · Payment/cancellation risk · Claim intake | Triage at a glance |
| **2** | **Your next move** | One operational sentence: what the office should do next | Action clarity |
| **3** | **Collected** | Green chips: what the customer already provided | Avoid re-asking |
| **4** | **Still needed** | Orange chips: what to ask or verify next | Next ask clarity |
| **5** | **Urgency** | Same-day vs routine | Prioritize correctly |
| **6** | **Human confirmation** | When AI collected from conversation — broker should verify | Trust boundary |

---

## 2. What Next Action Should Be Visible

| Requirement | Definition |
|-------------|------------|
| **Prominence** | Bold, top of case card; broker should not scroll to find it |
| **Style** | Operational: check, confirm, resend, quote, remove, tell client what to bring |
| **Concrete** | Mention document, deadline, payment, or vehicle when known |
| **One sentence** | Not a paragraph; one dominant next move |

**Good:** "Confirm whether the payment actually failed, check whether the carrier still shows the balance due, and help the client fix it today."

**Bad:** "Review and follow up."

---

## 3. What Correction / Context Should Stand Out

| Context type | What broker needs to see | Where |
|--------------|--------------------------|-------|
| **Correction** | Customer corrected earlier info (e.g. "actually paid") | Badge or chip on case card |
| **Already sent** | Customer says "I already sent it" | Badge: "Customer says sent" or "Verify receipt" |
| **Verify receipt** | Underwriting requested X; customer claims sent | "Verify receipt" badge; Still needed: verify_carrier_received |
| **Recent follow-up** | Customer just sent new message | "Just updated with customer follow-up" badge |
| **Human confirmation** | AI extracted sensitive data (payment, VIN, DL) | Gold "Human confirmation recommended" badge |

---

## 4. What Makes Handoff Truly Usable in a Live Trial

| Criterion | Definition |
|-----------|-------------|
| **Broker can act without reconstructing** | Next move + Collected + Still needed enough to proceed |
| **No manual case assembly** | System did the triage; broker reviews and acts |
| **Correction/context visible** | Broker sees "already sent" or "correction" without reading full conversation |
| **Draft editable** | Broker can tweak tone/content; copy to client; no auto-send |
| **Reopen context** | "Resume here" with waiting_on + latest note when reopening |

---

## 5. Queue-Level Visibility (Broker Case List)

| Signal | What broker infers |
|--------|--------------------|
| **Urgency** | Same-day vs routine |
| **Case focus** | Add car, renewal, claim, missing doc, payment risk |
| **Readiness** | Ready to act vs Needs more info |
| **Follow-up state** | Your move vs Waiting on client |
| **Customer says sent** | Verify receipt badge |
| **Work now vs parked** | Action section vs tracking section |

---

## 6. Implementation Notes

- **Backend:** `broker_next_step` from triage; `collected_fields`, `still_needed_fields`; `handoff_context` (correction, already_sent)
- **UI:** Case card: Case focus (top) → Your next move (bold) → Collected/Still needed chips → Human confirmation badge → Draft
- **Queue:** Urgency badge; case focus; "Verify receipt" when applicable

---

*End of Handoff / Office Next Action Spec*
