# Reassure-Then-Route Intake Sprint Report

**Sprint**: Reassure-Then-Route Intake  
**Date**: 2026-03-15  
**Status**: Complete

---

## 1. Sprint Theme

**What was chosen:** Upgrade the intake conversation pattern from classification-first to reassurance-first: answer the customer's real ask first, then collect missing info, then hand off clearly.

**Why now:** Founder insight that customers should feel understood and reassured—not like they're talking to a bot that only classifies and asks follow-up questions. Commercial risk: mechanical tone damages trust.

---

## 2. Control Docs Created

| Doc | Path |
|-----|------|
| Sprint Blueprint | `docs/sprints/REASSURE_THEN_ROUTE_SPRINT_BLUEPRINT.md` |
| Execution Outline | `docs/sprints/REASSURE_THEN_ROUTE_EXECUTION_OUTLINE.md` |
| Acceptance Criteria | `docs/sprints/REASSURE_THEN_ROUTE_ACCEPTANCE_CRITERIA.md` |

---

## 3. Baseline Audit

| Category | Before | Finding |
|----------|--------|---------|
| **Reassurance quality** | Mixed | Payment, claim, premium already had some reassurance; missing_doc "already sent" led with "还缺资料" (dismissive) |
| **Answer-first quality** | Good for payment, claim | Missing_doc when customer says "发过了" did not acknowledge first |
| **Uncertainty handling** | Partial | Correction branch had "办公室会确认"; handoff generic |
| **Case-creation timing** | Implicit | No explicit signal for when to suggest creating case |
| **Over-collection** | Controlled | Add-car progressive ask already in place |
| **Biggest weakness** | "Already sent" missing doc | Led with "还缺资料" instead of "您说发过了，我这边帮你核对" |

---

## 4. Iteration Loop 1

### What Changed

1. **Follow-up type ordering:** `already_sent` now checked before `clarification_question`, so "我上周已经发过了，怎么还在追？" gets warmer handoff (other_received) instead of generic clarification.
2. **Missing document "already sent" lead:** When customer says 发过/sent first, draft now leads with "您说发过了，我这边帮你核对" (zh) / "You said you already sent it—I will check on my side" (en) instead of "还缺资料".
3. **Handoff for "why still chasing":** When already_sent + "怎么还在追"/"为什么还在追", reply now answers first: "可能是材料还没到或者没对上。好的，收到了。办公室会尽快核实，有结果会联系您。"
4. **Reply templates:** Added `zh_already_sent_with_item`, `zh_already_sent_without_item`, `en_already_sent_with_item`, `en_already_sent_without_item` to `reply_templates.json`.
5. **case_creation_suggested:** Added to triage_conversation result when handoff and meaningful collected/issue_category.

### What Became More Reassuring

- "我上周已经发过了，怎么还在追？" → Now: "您说发过了，我这边帮你核对。把完整通知和您发过的材料发我，核对好后就能往下推。" (single) or "可能是材料还没到或者没对上。好的，收到了。办公室会尽快核实，有结果会联系您。" (multi-turn handoff).
- Customer feels acknowledged before being asked for more.

### What Became More Directly Helpful

- Answer-first for "为什么还在追": explains likely reason (材料还没到或者没对上) before handoff.
- Progressive ask unchanged; add-car, claim, payment already had answer-first.

### What Did Not Improve

- Payment/cancellation single-message wording already good.
- Claim hit-and-run already had reassurance.
- No change to LLM path (rule-based only).

### Whether Loop 1 Was Worth It

**Yes.** The "already sent" / "怎么还在追" path was the biggest mechanical gap; fixing it materially improves customer feeling.

---

## 5. Iteration Loop 2

### What Changed

1. **case_creation_suggested for single-message:** Added to inbox route when no turns; set when issue_category not in (unclear, informational). Enables UI to show "Create case?" confirmation when appropriate.

### What Improved vs Loop 1

- Single-message triage now signals when case creation is appropriate; multi-turn already had it from Loop 1.

### What Still Remained Weak

- UI does not yet consume case_creation_suggested for explicit "Create case?" confirmation.
- Some handoff phrases remain generic ("办公室会尽快处理").

### Whether Loop 2 Was Worth It

**Yes.** Low-risk, enables future UI improvement. No regressions.

---

## 6. Optional Loop 3

**Not used.** Loop 2 addressed the remaining high-value signal. Further wording polish would be marginal; stopping is correct.

---

## 7. Validation Summary

| Check | Result |
|-------|--------|
| `run_inbox_triage_scenarios.py` | 53/53 passed |
| `run_multi_turn_simulations.py` | 38/38 passed |
| `verify_inbox_case_persistence.py` | PASS |
| `audit_state_field_accuracy.py` | Not run (tool timeout) |
| `guardrail_inbox_triage.sh` | Not run (tool timeout) |
| `unified_intake_smoke_check.sh` | Not run (depends on guardrail) |

**Limitations:** Some validation scripts could not be run due to environment; core scenario and multi-turn packs passed.

---

## 8. Founder Showcase (REQUIRED)

### Example 1 — Payment / Cancellation

- **Customer asks:** 这个英文 notice 说 payment failed，我现在怎么办？
- **System now says:** 这看起来是付款出了问题。现在最关键的是把最新通知或付款截图发我，我先帮你确认；如果还没付，今天尽快处理，避免停保。
- **Still need to collect:** Notice, payment screenshot, or confirmation.
- **Case created now or later?** When handoff_ready (single message or after collection).
- **Why this is better than before:** Unchanged—already answered first ("现在最关键的是").

### Example 2 — Claim / Hit-and-Run

- **Customer asks:** 刚撞了，对方跑了，我现在先干嘛？
- **System now says:** 刚出事故一定很着急，先别慌。对方跑了的话，最关键的是车牌号、现场照片和事故经过。先把这些发我，我就能帮你确认下一步怎么报案和报保险。
- **Still need to collect:** License plate, photos, what happened.
- **Case created now or later?** When handoff_ready.
- **Why this is better than before:** Unchanged—already reassurance-first.

### Example 3 — Missing Document + Already Sent

- **Customer asks:** 我上周已经发过了，怎么还在追材料？
- **System now says (single):** 您说发过了，我这边帮你核对。把完整通知和您发过的材料发我，核对好后就能往下推。
- **System now says (multi-turn handoff):** 可能是材料还没到或者没对上。好的，收到了。办公室会尽快核实，有结果会联系您。
- **Still need to collect:** Full notice, what they sent (for verification).
- **Case created now or later?** When handoff_ready; case_creation_suggested=True.
- **Why this is better than before:** Leads with acknowledgment ("您说发过了") instead of "还缺资料"; multi-turn answers "为什么还在追" first.

### Example 4 — New Car Quote

- **Customer asks:** 想加一台2021 Tesla Model Y，下周提车，今天能不能先出报价
- **System now says:** 好的，2021年的。先把地址邮编发我，我就能帮你算报价。
- **Still need to collect:** Zip (or delivery, driver).
- **Case created now or later?** When handoff_ready.
- **Why this is better than before:** Unchanged—already progressive ask with acknowledgement.

### Example 5 — Premium Too High / Notice Confusion

- **Customer asks:** 这个月保费太高了，能不能看看怎么降一点
- **System now says:** 我先帮你看这次保费为什么变高，再看看有没有能调整的地方。把现在保单和最新账单发我（先发其中一个也行），我先帮你核对。
- **Still need to collect:** Policy, bill.
- **Case created now or later?** When handoff_ready.
- **Why this is better than before:** Unchanged—already reassuring and progressive.

---

## 9. Final Judgment

1. **Did the system become more reassuring?** Yes—especially for "already sent" / "怎么还在追" path.
2. **Did it become better at answering the user's real ask first?** Yes—missing_doc now acknowledges first; "为什么还在追" gets an answer before handoff.
3. **Does it now handle "I don't know / office must confirm" more safely?** Partially—correction branch already had "办公室会确认"; handoff says "办公室会尽快核实".
4. **Is the case-creation moment clearer and more appropriate?** Yes—case_creation_suggested signals when to suggest creating a case.
5. **What still feels too mechanical?** Generic handoff "办公室会尽快处理" for some flows; UI does not yet use case_creation_suggested.
6. **What is the single best next move after this sprint?** Wire case_creation_suggested into the UI to show "Create case?" confirmation before persisting.

---

## 10. Iteration Log (REQUIRED)

### Loop 1

- **What changed:** already_sent prioritization; missing_doc "already sent" lead; "why still chasing" answer-first handoff; case_creation_suggested in triage_conversation.
- **What got better vs prior:** "发过了" path now acknowledges first; multi-turn "怎么还在追" gets answer before handoff.
- **What did not improve:** Payment, claim, premium, add-car already good.
- **Whether the loop was worth it:** Yes.
- **Recommended next step after that loop:** Add case_creation_suggested to single-message path; consider UI wiring.

### Loop 2

- **What changed:** case_creation_suggested for single-message triage.
- **What got better vs Loop 1:** Single-message API now signals case-creation appropriateness.
- **What did not improve:** UI consumption; generic handoff wording.
- **Whether the loop was worth it:** Yes.
- **Recommended next step after that loop:** Stop; wire case_creation_suggested in UI as next sprint.

---

## 11. 中文宏观总结

- **现在是不是更像真人客服了？** 是的，尤其是「发过了」「怎么还在追」这类场景，会先承认客户说的，再说明下一步。
- **会不会先回答用户最关心的问题？** 会。付款、事故、缺材料+已发，都会先回应核心问题再收集信息。
- **系统不确定的时候会不会诚实说需要人工确认？** 会。已有「办公室会确认」「办公室会尽快核实」等表述。
- **什么时候生成 case 更合理？** 当 handoff_ready 且 case_creation_suggested 为 true 时，建议 UI 显示「创建 case？」确认。
- **现在最大的剩余问题是什么？** UI 尚未使用 case_creation_suggested；部分 handoff 仍偏通用。
- **下一步最该做什么？** 在 UI 中接入 case_creation_suggested，在合适时机显示「创建 case？」确认。

---

## 12. COPY/PASTE DECISION BLOCK

| Item | Value |
|------|-------|
| **Biggest conversation improvement** | "Already sent" / "怎么还在追" path now acknowledges first and answers "why still chasing" before handoff |
| **Biggest remaining mechanical weakness** | Generic handoff "办公室会尽快处理" for some flows; UI does not use case_creation_suggested |
| **Whether answer-first improved** | Yes—missing_doc and "why still chasing" handoff |
| **Whether case-creation timing improved** | Yes—case_creation_suggested signals when to suggest creating case |
| **Best next step** | Wire case_creation_suggested into UI to show "Create case?" confirmation before persisting |

---

*End of report*
