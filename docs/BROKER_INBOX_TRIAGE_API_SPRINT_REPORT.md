# Broker Inbox Triage API Sprint Report

**Date:** 2026-03-07  
**Sprint:** Add minimal API route for Broker Inbox Triage Assistant

---

## 1. Primary Objective

**What was built:** A minimal `POST /api/inbox/triage` route that accepts `{"text": "..."}` and returns the structured triage output from the existing engine.

**Why it mattered most:** The triage engine was previously only callable via CLI or scenario runner. The API turns it into a callable product capability that a demo UI, test page, or future unified intake can consume without Andy manually running CLI tools.

---

## 2. Primary Changes Made

| File | Change |
|------|--------|
| `services/fiqa_api/routes/inbox_triage.py` | **New.** Router with `POST /api/inbox/triage`, Pydantic request model, calls `triage_message()`. |
| `services/fiqa_api/app_main.py` | Import and mount `inbox_triage_router`. |
| `scripts/test_inbox_triage_api.py` | **New.** HTTP-based API test script (cancellation, empty text 400, informational). |
| `scripts/guardrail_inbox_triage.sh` | Add optional step [3]: run API test when server on 8001. |
| `docs/runbooks/BROKER_INBOX_TRIAGE_RUNBOOK.md` | Add Section 4: API endpoint, curl example, test script. Renumber sections. |
| `AGENTS.md` | Add inbox triage API test to execution path table. |

---

## 3. API Verification Result

**Endpoint:** `POST /api/inbox/triage`

**Example input:**
```json
{"text": "Notice: Policy will be cancelled in 7 days due to non-payment. Last notice."}
```

**Example output shape:**
```json
{
  "issue_category": "cancellation_warning",
  "urgency": "critical",
  "broker_next_step": "Review and act on cancellation warning.",
  "client_prep": "Please have any relevant documents or information ready.",
  "client_reply_draft": "Thank you for reaching out. We are reviewing your message and will follow up shortly. If you have any documents to share, please send them at your earliest convenience.",
  "manual_followup_needed": true
}
```

**Field mapping (engine vs sprint spec):**
- `issue_category` = category
- `urgency` = urgency
- `manual_followup_needed` = manual_followup_required
- `broker_next_step` = broker_next_step
- `client_prep` = client_should_prepare
- `client_reply_draft` = client_reply_draft

**Scenarios tested:** S3 (cancellation), S10 (informational), empty text (400). All pass.

**Before vs after:** Before: CLI and scenario runner only. After: API route callable by any HTTP client. **Better.**

---

## 4. Secondary Objective

**What was selected:** Input text normalization (strip, collapse whitespace).

**Why:** Pasted OCR or email text often has extra spaces/newlines. Normalization improves robustness without changing triage logic.

**What changed:** Added `_normalize_input()` in `inbox_triage.py`: strip, collapse `\s+` to single space before calling `triage_message()`.

**Result:** Scenarios still pass; API correctly triages input with extra whitespace.

---

## 5. Guardrail / Regression Result

| Check | Result |
|-------|--------|
| Scenario runner | PASS (12/12) |
| Guardrail script | PASS |
| API test script | PASS (when server on 8001) |
| Output shape | All 6 fields present, correct types |

**What they protect:** Scenario pack regression, output shape stability, API route correctness.

---

## 6. Business / Broker Impact

- **Closer to real broker use:** Triage is now callable via HTTP; a demo UI or simple test page can POST message text and get structured output.
- **Reduces manual work:** Andy no longer needs to run CLI for each message; Cursor/OpenClaw can validate via API.
- **Prepares for unified intake:** Single entry point for future Gmail/CRM integration.

---

## 7. Manual-Work Reduction

| Before | After |
|--------|-------|
| Andy runs `inbox_triage_cli.py "message"` for each test | Curl or API test script; UI can call API |
| Andy mentally maps engine output to product behavior | API returns stable JSON; documented in runbook |
| Cursor/OpenClaw cannot validate API | `test_inbox_triage_api.py` + guardrail step [3] |

---

## 8. Remaining Blocker(s)

None. API is usable for internal review.

---

## 9. Recommended Next Sprint

**One clear next step:** Add a minimal demo UI page or test harness that calls `POST /api/inbox/triage`, displays the result, and allows pasting message text. Keeps scope narrow; no Gmail/CRM integration yet.

---

*End of report*
