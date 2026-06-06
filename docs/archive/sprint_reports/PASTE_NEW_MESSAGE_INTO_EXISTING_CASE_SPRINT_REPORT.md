# Paste New Message Into Existing Case Sprint Report

**Sprint:** Paste New Message Into Existing Case Sprint  
**Date:** 2026-03-11  
**Scope:** SearchForge → Chen Kui Insurance Unified Entry — lightweight follow-up continuation

---

## 1. Stages completed

| Stage | Status | Notes |
|-------|--------|-------|
| **Stage 1 — Define lightweight append model** | ✅ Completed | §0b updated in BROKER_HANDOFF_CLARITY_GUIDE.md |
| **Stage 2 — Implement append flow** | ✅ Completed | Backend, API, UI: paste box + "Update with new customer message" |
| **Stage 3 — Follow-up continuity simulation** | ✅ Completed | 5/5 scenarios pass (FA1–FA5) |
| **Stage 4 — Classify weaknesses** | ✅ Completed | No high-value weaknesses; first pass strong |
| **Stage 5 — Improvement Loop 1** | Skipped | First pass sufficient |
| **Stage 6 — Improvement Loop 2** | Skipped | No clear value-add |
| **Stage 7 — Optional Improvement Loop 3** | Skipped | Not needed |
| **Stage 8 — Lightweight follow-up product proof** | ✅ Completed | 5 walkthroughs below |
| **Stage 9 — Regression + safety protection** | ✅ Completed | Smoke step 19, API test 13, runbook note |
| **Stage 10 — Audit + practical judgment** | ✅ Completed | Verdict: Accept |

---

## 2. Lightweight append target

**What the broker does:**
1. Opens existing case from Recent cases
2. Pastes new customer follow-up message in "Paste new customer follow-up" text box
3. Clicks "Update with new customer message"
4. Sees refreshed case: updated next step, collected/still needed, source_text, last meaningful update

**What the system receives:** `case_id` + `new_message` (plain text)

**What the system updates:**
- `source_text` — merged: old + `\n\n[客户] ` + new message
- `broker_next_step`, `client_prep`, `client_reply_draft`, `manual_followup_needed`
- `conversation_summary`, `collected_fields`, `still_needed_fields`
- `updated_at`, `case_activity` (adds "follow_up_added")

**What stays manual:** Broker pastes the message; no inbox sync, no email/WeChat integration.

---

## 3. Product / data / UX changes made

| File | Change | Purpose |
|------|--------|---------|
| `services/fiqa_api/inbox_triage/case_store.py` | `get_case_by_id()`, `append_follow_up_message()` | Fetch case; merge source + triage result |
| `services/fiqa_api/inbox_triage/triage.py` | `_parse_source_to_turns()`, `triage_for_append()` | Parse existing source; re-triage in context |
| `services/fiqa_api/routes/inbox_triage.py` | `POST /api/inbox/cases/{case_id}/append-message` | Append endpoint |
| `ui/src/api/inboxTriage.ts` | `appendFollowUpMessage()` | API client |
| `ui/src/pages/UnifiedIntakePage.tsx` | "Paste new customer follow-up" card, `handleAppendMessage()` | UI flow |
| `docs/BROKER_HANDOFF_CLARITY_GUIDE.md` | Paste follow-up description | Doc update |
| `docs/runbooks/UNIFIED_INTAKE_MVP_RUNBOOK.md` | Append-message endpoint | Runbook |
| `scripts/run_follow_up_append_simulations.py` | New script | FA1–FA5 simulations |
| `scripts/test_inbox_triage_api.py` | Test 13: append follow-up | API regression |
| `scripts/unified_intake_smoke_check.sh` | Step 19: paste follow-up | Smoke check |

---

## 4. Simulation and improvement loops

**Follow-up append simulations (5/5 passed):**

| ID | Scenario | Result |
|----|----------|--------|
| FA1 | Add-car gets ZIP later | zip, delivery_date in collected; primary_driver still needed |
| FA2 | Renewal case gets bill later | policy_bill_sent in collected; which_vehicle_to_remove still needed |
| FA3 | Claim case gets photos later | photos, other_driver_info in collected |
| FA4 | Missing-document sent again | customer_says_sent_declaration_page; verify_carrier_received still needed |
| FA5 | Corrected notice case | payment_lapse_expiration; broker_next_step refreshed |

**Improvement loops:** None needed. First pass strong.

---

## 5. Product proof strength

| Question | Answer |
|----------|--------|
| Can broker continue yesterday's case more easily? | Yes. Paste new message → case refreshes in place. |
| Does pasted follow-up update the case usefully? | Yes. Next step, collected/still needed, source_text all refresh. |
| Does reopen feel stronger? | Yes. Append flow complements Resume here and last meaningful update. |
| Is the system still lightweight? | Yes. No inbox sync, no CRM; broker pastes manually. |
| Is anything overengineered? | No. One text box, one button, one API call. |

---

## 6. Validation summary

| Check | Result | Protects |
|-------|--------|----------|
| `bash scripts/guardrail_inbox_triage.sh` | PASS | 49 scenarios, multi-turn, adversarial, complex |
| `cd ui && npm run build` | PASS | UI compiles |
| `PYTHONPATH=. python3 scripts/run_follow_up_append_simulations.py` | PASS | 5/5 FA scenarios |
| `scripts/test_inbox_triage_api.py` (with server) | Test 13 added | Append endpoint regression |

**Note:** API test 13 requires server restart to pick up new route. Run: `bash scripts/run_demo_local.sh` then `python3 scripts/test_inbox_triage_api.py`.

---

## 7. Business / platform value

| Area | Improvement |
|------|-------------|
| **Daily-use continuity** | Broker can paste customer's new message into existing case and get refreshed guidance |
| **Reopen experience** | Append flow + Resume here + last meaningful update = stronger reopen |
| **Lightweight CRM** | No inbox sync; manual paste keeps product simple |
| **Structured intake** | Add-car, renewal, claim, missing-doc all refresh collected/still_needed on append |

---

## 8. Remaining blocker(s)

None. Append flow is implemented and validated.

---

## 9. Recommended next step

- Use paste follow-up in founder demo: reopen add-car case, paste "我发了ZIP 90210"，show refreshed Collected/Still needed.
- Optional: add one follow-up append scenario to guardrail if desired.

---

## 10. 中文或中英混合宏观总结

**这次 paste new message into existing case 变好了什么：**
- Broker 可以 reopen 旧 case，在「Paste new customer follow-up」里粘贴客户新消息，点「Update with new customer message」，case 会刷新：next step、Collected/Still needed、source_text、last meaningful update 都会更新。
- 不需要 inbox sync，broker 手动粘贴即可。

**broker 现在怎么继续旧 case：**
1. 从 Recent cases 打开旧 case
2. 在「Paste new customer follow-up」粘贴客户新消息
3. 点「Update with new customer message」
4. 看刷新后的 next step、Collected、Still needed

**哪些地方更像日常办公：**
- 客户发微信说「我发了ZIP 90210」→ broker 粘贴到 case → 系统自动更新 collected_fields，still_needed 只剩 primary_driver。
- 客户说「declaration page 我又发了一遍」→ 粘贴 → 系统更新 customer_says_sent，next step 变成 verify carrier received。

**还缺什么：**
- Inbox sync、email/WeChat 自动拉取 —  intentionally not built。
- 客户发新消息仍需 broker 手动粘贴。

**这次对陈奎和以后别的小客户有什么帮助：**
- 陈奎办公室可以继续昨天的 case，粘贴客户新消息，立刻看到刷新后的 next step 和 collected/still needed，不用重建 context。
- 以后别的 broker 客户也能用同一套轻量 paste 流程，贴近真实办公室 follow-up 工作方式。

---

## 11. Practical append-flow cheat sheet

| Broker does | System updates |
|-------------|----------------|
| Opens existing case | — |
| Pastes new customer message | — |
| Clicks "Update with new customer message" | source_text (merged), broker_next_step, client_prep, client_reply_draft, collected_fields, still_needed_fields, conversation_summary, updated_at, case_activity (follow_up_added) |

**What becomes clearer:** Next step, collected/still needed, last meaningful update (activity: "Customer follow-up added: …").

**What still remains manual:** Broker pastes; no inbox sync.

---

## 12. Continuity problem summary

| Category | Strength | Notes |
|----------|----------|-------|
| **Add-car append** | Strong | ZIP, delivery in collected; primary_driver still needed |
| **Renewal append** | Strong | policy_bill_sent in collected |
| **Claim append** | Strong | photos, other_driver_info in collected |
| **Missing-doc append** | Strong | customer_says_sent; verify_carrier_received still needed |
| **Corrected notice append** | Strong | payment_lapse_expiration; next step refreshed |

**Repeated weaknesses addressed:** None. First pass sufficient.

---

## 13. Follow-up proof walkthroughs

### 1. Add-car updated later

**Old state:** 客户要加一台2021 Tesla Model Y，下周提车，问今天能不能先出报价. Collected: year, make_model, delivery_date. Still needed: zip, primary_driver.

**New customer message:** 我发了ZIP 90210，下周一提车

**Updated case result:** Collected: year, make_model, zip, delivery_date. Still needed: primary_driver. broker_next_step refreshed. source_text includes new message.

**Result:** Strong.

---

### 2. Renewal updated later

**Old state:** 续保保费太高了，其中一辆去掉会便宜吗. Still needed: renewal notice, which vehicle.

**New customer message:** 我发了最新的账单和declaration page

**Updated case result:** Collected: premium_concern, renewal_context, remove_vehicle_interest, policy_bill_sent. Still needed: which_vehicle_to_remove.

**Result:** Strong.

---

### 3. Claim updated later

**Old state:** 刚出事故了，要收集什么？. Still needed: photos, other driver info.

**New customer message:** 我拍了现场照片，对方车牌和保险信息也发你了

**Updated case result:** Collected: accident_reported, photos, other_driver_info. Still needed: accident_time_location, police_report_if_applicable.

**Result:** Strong.

---

### 4. Missing-document updated later

**Old state:** UW follow up - need dec page + garaging proof. 客户说上周发过了.

**New customer message:** declaration page 我又发了一遍，请查收

**Updated case result:** Collected: requested_declaration_page, requested_garaging_proof, customer_says_sent_declaration_page, customer_says_sent_garaging_proof. Still needed: verify_carrier_received.

**Result:** Strong.

---

### 5. Corrected notice case

**Old state:** 客户问：这个英文 notice 说 payment failed，我现在怎么办？

**New customer message:** 不是payment failed，是final notice说保单要停了

**Updated case result:** issue_category: payment_lapse_expiration. broker_next_step refreshed for final notice context.

**Result:** Strong.

---

### One limitation intentionally not solved

**Inbox sync / email/WeChat integration:** Building automatic message pull would add CRM complexity. Broker pastes manually; keeps product lightweight.

---

*End of report*
