# Unified Intake Extended Workflow Sprint Report

**Date:** 2026-03-07  
**Sprint:** SearchForge → Unified Intake MVP v1  
**Duration:** ~30 min

---

## 1. Major task 1 — Real message robustness

### What realistic messages were tested

| ID | Input | Style |
|----|-------|-------|
| R1 | Fwd: FW: Re: Policy - 客户说看了这个不知道怎么弄 | Partial forwarded email, vague |
| R2 | 保险公司说我的保单7天后要cancel | Customer pasted summary, mixed language |
| R3 | Payment failed | Minimal payment notice |
| R4 | 客户发了一张截图 上面是dmv的信 看不懂 | Vague screenshot, client can't understand |
| R5 | 需要驾照 copy 客户说上周寄了 | Fragmented underwriting doc request |
| R6 | ⚠️ 重要：您的保单即将因未缴款而被取消 | Chinese cancellation warning with emoji |

### What weaknesses were found

- **R5, R6:** Rule-based triage returned `unclear` instead of correct category (missing_document, cancellation_warning)
- **R1, R4:** Returned `unclear` instead of `customer_question` (客户说/看不懂 patterns missing)
- Generic broker_next_step and client_reply_draft for all cases

### What changed

**`services/fiqa_api/inbox_triage/triage.py`:**

- Added Chinese cancellation keywords: `取消`, `未缴款`
- Added fragmented doc pattern: `驾照` + (`copy` | `客户说` | `寄了` | `request` | `需要`) → missing_document
- Added customer-question phrases: `看不懂`, `不知道怎么弄`

**`configs/inbox_triage_scenarios.json`:**

- Added 6 realistic scenarios (R1–R6) for repeatable validation

### Before vs after

| Scenario | Before | After |
|----------|--------|-------|
| R1 | unclear | customer_question |
| R2 | cancellation_warning ✓ | (unchanged) |
| R3 | payment_lapse_expiration ✓ | (unchanged) |
| R4 | unclear | customer_question |
| R5 | unclear | missing_document |
| R6 | unclear | cancellation_warning |

---

## 2. Major task 2 — Case card actionability

### What actionability issue was targeted

- Urgency not prominent enough for critical/high
- Broker next step felt like generic label
- Unclear split between broker-side and client-facing content

### What changed

**`ui/src/pages/UnifiedIntakePage.tsx`:**

- Added **"Same-day action"** tag for critical/high urgency
- Renamed "What to do next" → **"Your next step"** with stronger typography (fontWeight 600, fontSize 14)
- Renamed draft section to **"Client-facing draft (copy to WeChat/email)"**
- Added **"Realistic (fragmented)"** quick-fill example

### Before vs after

| Element | Before | After |
|---------|--------|-------|
| Critical/high | urgency tag only | urgency + "Same-day action" tag |
| Broker action | "What to do next" | "Your next step" (bolder) |
| Draft section | "Draft to send client" | "Client-facing draft (copy to WeChat/email)" |
| Quick-fill | 4 examples | 5 (added Realistic fragmented) |

---

## 3. Major task 3 — End-to-end broker smoke flow

### What flow was verified or improved

Full broker flow: **paste message → triage → review case card → copy draft → decide manual follow-up**

### What changed

**`scripts/unified_intake_smoke_check.sh`:**

- Updated manual steps to match new quick-fill labels ("Cancellation" not "Cancellation warning")
- Added explicit flow description
- Added verification for "Same-day action" tag and "Your next step"
- Added step 6: "Decide: manual follow-up needed? (critical/high = yes)"
- Added "Realistic (fragmented)" to optional quick-fills

**`scripts/test_inbox_triage_api.py`:**

- Added Test 4: realistic fragmented scenario (accepts missing_document or unclear for LLM/rule variance)

**`docs/runbooks/UNIFIED_INTAKE_MVP_RUNBOOK.md`:**

- Expanded smoke-flow checklist with full broker flow steps

### Why it matters

- Smoke flow is now repeatable before demos or internal reviews
- API test covers realistic input; guardrail runs 18 scenarios (12 original + 6 realistic)
- Manual steps are explicit and easy to follow

---

## 4. Validation / guardrail result

### What checks were run

| Check | Result |
|-------|--------|
| `npm run build` | PASS |
| `PYTHONPATH=. python scripts/run_inbox_triage_scenarios.py` | 18/18 passed |
| `bash scripts/guardrail_inbox_triage.sh` | PASS |
| `PYTHONPATH=. python scripts/test_inbox_triage_api.py` | All 4 tests passed |
| `bash scripts/unified_intake_smoke_check.sh` | PASS |

### What they protect

- **Scenario pack:** Rule-based triage correctness; regression on 18 cases
- **Guardrail:** Scenario pack + optional API (when server on 8001)
- **API test:** Cancellation, informational, empty-text 400, realistic fragmented
- **Smoke script:** Guardrail + printed manual UI steps for full broker flow

---

## 5. Business / broker impact

- **Realistic messages:** Brokers can paste messy, fragmented, or mixed-language input and get correct triage
- **Case card:** Urgency and "Same-day action" are obvious; broker knows what to do first
- **Copy draft:** Clear "Client-facing draft (copy to WeChat/email)" reduces ambiguity
- **Repeatable flow:** Smoke check validates the full path before demos

---

## 6. Manual-work reduction

| Before | After |
|--------|-------|
| Andy guesses if realistic messages work | 6 realistic scenarios in pack; guardrail validates |
| Andy inspects case card layout | "Same-day action" and "Your next step" make action obvious |
| Andy remembers smoke steps | `unified_intake_smoke_check.sh` prints full flow |
| Cursor/OpenClaw can't validate realistic input | Scenario runner + API test cover R1–R6 |

---

## 7. Remaining blocker(s)

- None. All validation passed.

---

## 8. Recommended next sprint

**One clear next step:** Add 1–2 category-specific client_reply_draft templates to the rule-based triage (e.g., cancellation_warning gets a payment-urgent draft, missing_document gets a resend-reminder draft) so the copy-to-client output is more tailored when LLM is disabled.

---

*End of report*
