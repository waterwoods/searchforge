# Unified Intake Workflow Maturity Sprint Report

**Date:** 2026-03-07  
**Sprint focus:** Case card presentation + smoke-flow helper + future-compatibility

---

## 1. Primary objective

**What was improved:** The Unified Intake result presentation was refined so it behaves like a usable **case card** instead of a raw triage output.

**Why it mattered most:** A broker can now scan the result quickly and understand: (1) what the issue is, (2) how urgent it is, (3) whether broker/manual action is required, (4) what action to take, (5) what to tell the client. The result feels like a work item, not a JSON dump.

---

## 2. Primary changes made

| File | Change |
|------|--------|
| `ui/src/pages/UnifiedIntakePage.tsx` | Case card redesign: title "Case card" with urgency + category + "Broker action required" tag in header; reordered sections with clearer labels; dividers between sections; orange left border when manual follow-up needed; humanized category labels; "What to do next" / "What client should prepare" / "Draft to send client" section labels; Copy draft button promoted to primary style |

**What changed:**
- **Header:** Case card title now shows urgency tag, humanized category (e.g. "Cancellation Warning"), and "Broker action required" tag when `manual_followup_needed` is true
- **Visual hierarchy:** Urgency and action-required status are visible at a glance in the card header
- **Section labels:** "What to do next" (broker_next_step), "What client should prepare" (client_prep), "Draft to send client" (client_reply_draft)
- **Dividers:** Clear separation between sections for scan-ability
- **Action emphasis:** Orange left border on the card when manual follow-up is needed
- **Humanized category:** `cancellation_warning` → "Cancellation Warning"

**Why it helps:** Broker can scan the case card in seconds; urgency and action-required status are impossible to miss; sections follow the logical workflow (do next → client prep → draft to send).

---

## 3. Primary verification result

**Scenarios checked:**
- Cancellation warning (critical, manual follow-up)
- Missing document (medium, manual follow-up)
- Payment failed (high, manual follow-up)
- Customer question (medium, manual follow-up)
- Informational (low, no manual follow-up)

**Before vs after:**
- **Before:** Flat "Triage result" card; category/urgency in a single row; sections labeled "Broker action", "Client prep", "Client reply draft"; no visual emphasis for action-required cases
- **After:** "Case card" with urgency + category + action tag in header; clear section hierarchy; "What to do next" / "What client should prepare" / "Draft to send client"; orange border and Alert for action-required cases

**Result:** Better. More work-item feel, less raw API result feel.

---

## 4. Secondary objective (done)

**What was selected:** Add a small smoke-flow helper/checklist for Unified Intake.

**Why chosen:** The previous sprint recommended "Add a quick manual smoke test to the demo checklist." A dedicated script gives Andy a repeatable verification path without adding automated UI tests.

**What changed:**
- Created `scripts/unified_intake_smoke_check.sh`: runs guardrail first, then prints manual UI verification steps (open page, quick-fill, triage, copy draft)
- Updated `docs/runbooks/UNIFIED_INTAKE_MVP_RUNBOOK.md`: added section 10 (Future-Compatibility Placeholders) and section 11 (Smoke-Flow Checklist)

**Result:** Andy can run `bash scripts/unified_intake_smoke_check.sh` before demos to verify guardrail + get manual checklist.

---

## 5. Guardrail / validation result

| Check | Result | What it protects |
|-------|--------|------------------|
| `npm run build` | PASS | No compile/type errors |
| `run_inbox_triage_scenarios.py` | 12/12 passed | Triage logic and output shape |
| `guardrail_inbox_triage.sh` | PASS | Scenario pack, runner, API route |
| `test_inbox_triage_api.py` | PASS | POST /api/inbox/triage returns correct shape |
| `unified_intake_smoke_check.sh` | PASS | Guardrail + manual checklist printed |

---

## 6. Business / broker impact

- **More usable:** Broker can scan the case card in seconds; urgency and action-required status are prominent
- **Reduces broker effort:** Clear "What to do next" and "Draft to send client" reduce cognitive load
- **Closer to paid value:** Feels like a broker work surface, not a raw API result viewer
- **Repeatable verification:** Smoke-flow script gives Andy a quick pre-demo check

---

## 7. Manual-work reduction

- **Andy no longer needs to:** Manually imagine "is this product-like enough" — the case card structure makes it obvious
- **Cursor can now handle:** Case card layout, section hierarchy, labels, visual emphasis
- **OpenClaw can validate:** Guardrail and scenario runner confirm backend; smoke script prints manual steps

---

## 8. Future-compatibility note

**Identified for later (without implementing now):**

| Future field | Purpose | Where to add |
|--------------|---------|--------------|
| `case_id` | Link triage to a case record | API response; Case card header |
| `customer_id` | Link to customer/contact | API response; Case card header |
| `case_status` | open / in_progress / resolved | API response |
| `assigned_owner` | Broker or team member | API response |
| `timeline` / `history` | Past actions, notes | Separate section below case card |

**Documentation:** Added to `docs/runbooks/UNIFIED_INTAKE_MVP_RUNBOOK.md` section 10. When case management is built, extend the triage response and Case card UI in a backward-compatible way (new optional fields).

---

## 9. Remaining blocker(s)

None. All checks pass.

---

## 10. Recommended next sprint

**One clear next step:** Run a live broker walkthrough (陈奎 or proxy): paste 3–5 real messages, verify case card readability and Copy draft usability. Capture feedback on section order, labels, or missing signals.

---

*End of report*
