# Critical Multi-Turn Quality Polish Sprint Report

**Sprint:** Chen Kui Insurance Unified Entry — Critical Multi-Turn Quality Polish  
**Date:** 2026-03-12

---

## 1. Top scenario audit

| Scenario | Classification | Notes |
|----------|----------------|-------|
| **SIM1** Cancellation risk | Strong | Turn 2 handoff; turn 3 "已经付了" + "最要紧" → other_clarification distinct from turn 2 |
| **SIM2** Missing document | **Was weak → Fixed** | Turn 3 "garaging proof 是什么意思？要发什么？" now gets specific explanation instead of generic handoff |
| **SIM3** Add-car quote (Chinese) | Strong | 3-turn progressive ask; handoff at turn 3 |
| **SIM5** Claim intake | Strong | Turn 2 handoff; turn 3 "最要紧做什么" → other_clarification |
| **SIM6** Premium review | Strong | Turn 2 handoff; turn 3 "先看什么" → other_clarification |
| **SIM15** Add-car 3-turn | Strong | Strongest multi-turn proof; year → zip+delivery |

**Summary:** SIM2 was the only scenario with a clearly wrong/generic later-turn reply. SIM1, SIM5, SIM6 already had other_clarification differentiation from a prior sprint; SIM2’s document-clarification case was still generic.

---

## 2. Most important quality failures

| Issue | Where | Why it matters | Fix location |
|-------|-------|----------------|--------------|
| **Garaging proof / document clarification** | SIM2 Turn 3 | User asks "garaging proof 是什么意思？要发什么？" → system replied generic "办公室会优先核实" instead of explaining what it is and what to send. Directly hurts trust. | triage.py |
| Repeated reply even with clarification | SIM2 (before fix) | Turn 2 and Turn 3 replies were identical or nearly identical; user added meaningful clarification. | triage.py |
| "What does X mean / what should I send" not answered specifically | Missing document flow | other_clarification was generic; did not explain document terms. | triage.py |

**Other scenarios (SIM1, SIM5, SIM6):** "已经付了", "最要紧", "先看什么" already use other_clarification phrase; acceptable. "What matters most" and "what should office check first" remain generic; broker receives case and can clarify. Lower priority for this sprint.

---

## 3. Fixes made

| File | Change |
|------|--------|
| `services/fiqa_api/inbox_triage/triage.py` | When handoff=True and key=other_clarification, and last customer message is a **document clarification question** (what does garaging/declaration mean, what to send), use tailored explanation instead of generic handoff. Build reply via `_build_client_reply_draft(merged_text, "customer_question")` to get the document explanation, then append "。办公室会尽快处理，有结果会联系您。" |

**Why:** The base triage classifies merged text as missing_document when the full conversation has UW follow-up + dec page + garaging. So base_result["client_reply_draft"] was the "还缺 X，请再发我一次" template. For document clarification questions, we need the customer_question path, which produces the garaging proof definition. The fix explicitly builds the customer_question draft when we detect document confusion + handoff.

---

## 4. Before vs after

### SIM2 Missing document

| Turn | Before | After |
|------|--------|-------|
| 1 | 现在文件里还缺 declaration page 和 garaging proof。请再发我一次... | Same |
| 2 | 好的，收到了。办公室会尽快处理，有结果会联系您。 | Same |
| 3 | 您说的已收到，办公室会优先核实，有结果会联系您。 | **garaging proof（车辆停放地址证明）是证明车平时停哪里的材料。把完整通知发我，我先帮你确认缺哪一份、要补给谁。办公室会尽快处理，有结果会联系您。** |

### What got better

- SIM2 Turn 3 now answers the user’s question directly instead of a generic handoff.
- Garaging proof / declaration page clarification questions are handled with a specific explanation.

### What still remains weak

- "最要紧做什么" / "what matters most" / "先看什么" → still generic other_clarification; broker receives and clarifies.
- LC-AC3 (add-car correction) → handoff at turn 2, expected 3; pre-existing friction.

---

## 5. Validation summary

| Check | Result |
|-------|--------|
| `cd ui && npm run build` | ✓ Built successfully |
| `run_inbox_triage_scenarios.py` | 49/49 passed |
| `run_multi_turn_simulations.py` | 38/38 strong |
| `guardrail_inbox_triage.sh` | PASS |
| `unified_intake_smoke_check.sh` | PASS |
| Simulation Assistant scenarios | 15/15 Normal |

---

## 6. Redeploy readiness

| Component | Redeploy? | Notes |
|-----------|-----------|------|
| **Frontend** | No | No UI changes |
| **Backend** | Yes | `triage.py` — document clarification handoff logic |

---

## 7. 中文总结

- **哪几个多轮场景最有问题？** SIM2（缺材料）最明显：客户问「garaging proof 是什么意思？要发什么？」，系统回复太泛，没有具体说明。
- **这次修了什么？** 当客户在 handoff 后追问「garaging proof / declaration page 是什么意思、要发什么」时，系统现在会先给出解释（garaging proof = 车辆停放地址证明）和下一步指引，再附上「办公室会尽快处理」。
- **garaging proof 这种问题有没有修到位？** 有。SIM2 Turn 3 现在会回复：「garaging proof（车辆停放地址证明）是证明车平时停哪里的材料。把完整通知发我，我先帮你确认缺哪一份、要补给谁。办公室会尽快处理，有结果会联系您。」
- **现在最该再看哪几个场景？** SIM2（缺材料）— 确认 Turn 3 回复是否具体；SIM1、SIM5、SIM6 — 确认 Turn 3 与 Turn 2 有明显区分。
- **如果还不够好，下一轮最该补哪块？** ①「最要紧做什么」「办公室先看什么」这类追问可考虑更具体的回复；② 在「要发什么」时补充「通常是水电账单、租约或类似证明停放地址的文件」等具体示例。
