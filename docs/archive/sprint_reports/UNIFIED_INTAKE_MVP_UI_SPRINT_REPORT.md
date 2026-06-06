# Unified Intake MVP v1 – UI & Validation Sprint Report

**Date:** 2026-03-07  
**Sprint:** UI flow + validation

---

## 1. Primary objective

**What was built:** A minimal broker-facing UI flow for Unified Intake MVP v1.

**Why it mattered most:** The triage engine and API existed, but brokers had no product-facing way to use them. Andy had to imagine the flow or run CLI/curl. The new UI makes the product visible, testable, and reviewable.

---

## 2. Primary changes made

| File | Change |
|------|--------|
| `ui/src/api/inboxTriage.ts` | **New.** API client for `POST /api/inbox/triage` with `TriageResult` type. |
| `ui/src/pages/UnifiedIntakePage.tsx` | **New.** Page with textarea, submit, result card (all 6 fields), error handling, empty-input validation. |
| `ui/src/App.tsx` | Added route `/workbench/unified-intake` and import for `UnifiedIntakePage`. |
| `ui/src/components/layout/AppSider.tsx` | Added "Unified Intake" under AI Workbench with `InboxOutlined` icon. |
| `ui/src/components/layout/AppLayout.tsx` | Hide right panel for `/workbench/unified-intake` (full-width content). |
| `docs/runbooks/UNIFIED_INTAKE_MVP_RUNBOOK.md` | Added section 5: UI entry point (route, nav, flow, quick-fill). Renumbered sections 6–9. |

**Why it helps:** Brokers can paste message → submit → review structured result without leaving the app. Integration is minimal: one new route, one sider entry, no new nav branch.

---

## 3. UI verification result

| Item | Value |
|------|-------|
| **Page/route** | `/workbench/unified-intake` |
| **Nav** | AI Workbench → Unified Intake |
| **Flow** | Paste message → Triage → See result card |

**Result card surfaces:**
- issue_category (tag)
- urgency (color-coded tag: critical=red, high=orange, medium=gold, low=green)
- manual_followup_needed (volcano tag when true)
- broker_next_step
- client_prep
- client_reply_draft (in styled block)

**Scenarios tested via API (UI build verified):**
- S3: cancellation_warning, critical, manual_followup=true ✓
- S2: missing_document ✓
- S7: customer_question ✓
- S9: payment_lapse_expiration ✓
- S10: informational ✓

**Before vs after:**
- **Before:** Triage only via CLI (`inbox_triage_cli.py`) or curl; no product-facing flow.
- **After:** Broker can use UI at `/workbench/unified-intake`; paste → triage → review. **Better.**

---

## 4. Secondary objective (done)

| Task | Choice | Change | Result |
|------|--------|--------|--------|
| Quick-fill examples | 4 examples | Added "Quick-fill examples" card with buttons: Cancellation warning, Missing document, Customer question, Payment failed. | One-click load of representative scenarios. |
| Doc update | Runbook | Added section 5 (UI entry point) to `UNIFIED_INTAKE_MVP_RUNBOOK.md`. | Runbook now documents how to run and test the UI. |

---

## 5. Validation / guardrail result

| Check | Result | Protects |
|-------|--------|----------|
| `PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py` | **PASS** (12/12) | Scenario pack regression |
| `bash scripts/guardrail_inbox_triage.sh` | **PASS** | Scenario pack, output shape, API route |
| `python3 scripts/test_inbox_triage_api.py` | **PASS** (cancellation, empty text 400, informational) | API contract |
| `npm run build` (ui) | **PASS** | UI compiles |
| Manual API curl | **PASS** | End-to-end triage response shape |

---

## 6. Business / broker impact

- **More reviewable:** Andy can open the UI and see the full flow instead of imagining it.
- **More useful:** Brokers get a single entry point: paste → triage → review → decide.
- **Closer to real use:** Flow matches the master goal: paste message → structured triage → broker reviews and acts.

---

## 7. Manual-work reduction

| Before | After |
|--------|-------|
| Andy imagines how the product will work | Andy opens `/workbench/unified-intake` and sees it |
| Manual curl/CLI to test triage | UI + quick-fill for fast testing |
| No visible broker flow | Visible paste → triage → result flow |
| Cursor/OpenClaw could not validate UI | Cursor can validate via build + API; OpenClaw can run scenario pack |

---

## 8. Remaining blocker(s)

None. UI flow is working; scenarios and guardrail pass.

---

## 9. Recommended next sprint

**One clear next step:** Add a small "Copy draft" button next to `client_reply_draft` so brokers can copy the draft to clipboard before pasting into WeChat/email. Low effort, high practical value.

---

*End of report*
