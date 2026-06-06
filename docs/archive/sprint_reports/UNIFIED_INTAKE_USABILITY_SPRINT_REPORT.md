# Unified Intake MVP v1 – Usability Sprint Report

**Date:** 2026-03-07  
**Sprint focus:** Copy draft action + adjacent usability

---

## 1. Primary objective

**What was built:** A usable **Copy draft** button for `client_reply_draft` on the Unified Intake result card.

**Why it mattered most:** The broker (e.g., 陈奎) can now paste a message → review triage → click one button → copy the client-ready reply to clipboard. No manual select-and-copy. One fewer step in the workflow.

---

## 2. Primary changes made

| File | Change |
|------|--------|
| `ui/src/pages/UnifiedIntakePage.tsx` | Added Copy draft button next to "Client reply draft" label; imports `copyToClipboard` from `demoCopy.ts` and `CopyOutlined` from antd; uses `message.success` / `message.error` for feedback |

**What changed:**
- Button labeled "Copy draft" with copy icon, placed next to "Client reply draft"
- On click: copies `client_reply_draft` to clipboard via `navigator.clipboard.writeText`
- Feedback: "Copied" on success, "Copy failed" on error, "No draft to copy" when empty
- Button disabled when `client_reply_draft` is empty or missing

**Why it helps:** Broker can immediately paste the draft into WeChat/email without selecting text.

---

## 3. Primary verification result

**How the copy action works:**
1. Broker pastes message → clicks Triage → sees result card
2. If `client_reply_draft` has content, "Copy draft" button is enabled
3. Click → draft copied to clipboard → "Copied" toast
4. If draft is empty, button is disabled; programmatic click would show "No draft to copy"

**What was tested:**
- UI build: PASS
- Scenario runner: 12/12 passed
- Guardrail: PASS
- API test: PASS (cancellation_warning, empty text 400, informational)

**Before vs after:**
- **Before:** Broker had to manually select the draft text and copy (Ctrl+C / Cmd+C)
- **After:** One click copies the draft; clear success/failure feedback

**Result:** Better.

---

## 4. Secondary objective (done)

**What was selected:** Make `manual_followup_needed` more visually obvious + rename "Broker next step" to "Broker action".

**Why chosen:** Manual follow-up is a critical signal; brokers must not miss it. The tag alone was easy to overlook.

**What changed:**
- When `manual_followup_needed` is true: added an Alert at the top of the result card with message "Manual follow-up needed" and description "This case requires broker action before sending to client."
- Renamed "Broker next step" to "Broker action" for easier scanning

**Result:** Result card feels more like a case card; broker sees action-required cases immediately.

---

## 5. Validation / guardrail result

| Check | Result | What it protects |
|-------|--------|------------------|
| `npm run build` (ui) | PASS | No compile/type errors |
| `run_inbox_triage_scenarios.py` | 12/12 passed | Triage logic and output shape |
| `guardrail_inbox_triage.sh` | PASS | Scenario pack, runner, API route |
| `test_inbox_triage_api.py` | PASS | POST /api/inbox/triage returns correct shape |

---

## 6. Business / broker impact

- **Reduces broker effort:** One click instead of select-and-copy
- **More likely to be used repeatedly:** Lower friction → higher adoption
- **Closer to paid value:** Broker can paste → triage → copy → send in seconds

---

## 7. Manual-work reduction

- **Andy no longer needs to:** Manually imagine "how would a broker copy the draft" — the flow is explicit
- **Cursor can now handle:** Copy action implementation and feedback
- **OpenClaw can validate:** Guardrail and scenario runner confirm backend shape; UI build confirms frontend compiles

---

## 8. Remaining blocker(s)

None. All checks pass.

---

## 9. Recommended next sprint

**One clear next step:** Add a quick manual smoke test to the demo checklist: "Open /workbench/unified-intake, paste a quick-fill example, triage, click Copy draft, verify clipboard contains the draft." This gives Andy a repeatable verification path without adding automated UI tests.

---

*End of report*
