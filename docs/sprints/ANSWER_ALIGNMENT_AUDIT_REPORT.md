# Answer Alignment Audit + Optimization Direction Report

**Sprint:** Answer Alignment Audit + Optimization Direction  
**Created:** 2026-03-15  
**Scope:** Chen Kui Insurance Unified Entry

---

## 1. Sprint Theme

- **What was audited:** Why responses sometimes do not directly answer the user’s real question (答非所问).
- **Why now:** Founder concern: “The answer is not good enough. It does not really answer the question being asked.” Trial success depends on the system feeling helpful, not bureaucratic.

---

## 2. Control Docs Created

| Doc | Path |
|-----|------|
| Sprint Blueprint | `docs/sprints/ANSWER_ALIGNMENT_AUDIT_SPRINT_BLUEPRINT.md` |
| Execution Outline | `docs/sprints/ANSWER_ALIGNMENT_AUDIT_EXECUTION_OUTLINE.md` |
| Evaluation / SLA Criteria | `docs/sprints/ANSWER_ALIGNMENT_EVALUATION_CRITERIA.md` |

---

## 3. Baseline Answer-Alignment Audit

### Strongest Examples (answered well)

| User asked | System answered | Alignment |
|------------|-----------------|-----------|
| 这个英文 notice 说 payment failed，我现在怎么办？ | 这看起来是付款出了问题。现在最关键的是把最新通知或付款截图发我... | answered_well |
| 宝马x5，多少钱？ | 好的，宝马x5。先把年份和地址邮编发我，我就能帮你算报价。 | answered_well |
| 刚撞了，对方跑了，我现在先干嘛？ | 刚出事故一定很着急，先别慌。对方跑了的话，最关键的是车牌号、现场照片和事故经过。先把这些发我... | answered_well |
| 我上周已经发过了，怎么还在追材料？ | 现在文件里还缺资料。请把资料再发我一次；如果你之前已经发过，也跟我说一声，我这边帮你核对。 | answered_well |
| payment failed 怎么办，另外 dec page 我上周发过了 | 这看起来是付款出了问题...；如果材料说发过了，我这边也帮你核对。 | answered_well |
| garaging proof 是什么意思？要发什么？ | garaging proof（车辆停放地址证明）是证明车平时停哪里的材料。把完整通知发我... | answered_well |

### Weakest Examples (mostly missed)

| User asked | System answered | Alignment |
|------------|-----------------|-----------|
| 这些够了吗？ (standalone) | 这段内容还不够完整。把完整通知或前后内容再发我一下... | mostly_missed |
| 我其实已经付了 (standalone) | 这段内容还不够完整... | mostly_missed |
| 其实已经付了...那我现在最要紧做什么？ (SIM1 T3) | ~~好的，明白了。办公室会尽快处理~~ → **FIXED** | was mostly_missed |

### Common Misalignment Pattern

1. **Context-free follow-ups:** “这些够了吗” and “我其实已经付了” as **standalone** messages get `unclear` because they lack conversation context. In multi-turn context they work (SIM3 T3, SIM9 T2).
2. **Correction + embedded question:** When the user corrects (“其实已经付了”) AND asks a question (“最要紧做什么”) in the same message, the system used `other_corrected` and replied with “好的，明白了” — **without answering the question**. The follow_up_type prioritizes correction over urgency_question, so the “answer first” logic never ran.

---

## 4. Root-Cause Diagnosis

### Primary Root Cause

**Reply strategy: correction overrides embedded question.**

When a message contains both correction markers (“其实已经”) and urgency/next-step markers (“最要紧做什么”), `_derive_follow_up_type` returns `correction` first. The reply then uses `other_corrected` (“好的，明白了。办公室会尽快处理”) and never answers the embedded question.

### Secondary Root Cause

**Standalone context-free messages:** “这些够了吗” and “我其实已经付了” are inherently ambiguous without prior turns. The system correctly returns `unclear` for single-turn `triage_message`. This is expected; the real flow uses `triage_conversation` with context.

### What Is NOT the Main Cause

| Suspect | Verdict |
|---------|---------|
| Intent classification | Generally correct; payment, add-car, claim, missing-doc all classify well. |
| Routing (fast vs LLM) | Not the main issue; both paths use the same reply strategy. |
| Reply templates | First-turn templates are strong; the gap is in multi-turn follow-up handling. |
| Model quality | Rule-based path is used; no model involved in the failure cases. |
| Over-handoff | Handoff timing is appropriate; the issue is *what* we say at handoff. |

---

## 5. Iteration Loop 1

### What Was Inspected

- 53 inbox triage scenarios (all passed)
- 38 multi-turn simulations (all passed)
- 27 Simulation Assistant scenarios (all passed)
- Targeted examples: payment failed 怎么办, 宝马x5多少钱, 刚撞了, 我上周发过了, mixed asks, garaging proof 是什么意思, 这些够了吗, 我其实已经付了
- SIM1 Turn 3, SIM2 Turn 3, SIM3 Turn 3

### Patterns Found

- Most direct-answer cases pass.
- Two failure modes: (1) standalone context-free follow-ups → unclear; (2) correction + embedded question → generic handoff without answering.

### What Looked Most Wrong

SIM1 Turn 3: user asked “那我现在最要紧做什么？” and got “好的，明白了。办公室会尽快处理” — no direct answer.

### Optimization Direction

- **Primary:** When `follow_up_type == correction` but the message contains urgency/next-step question markers, answer the question first, then hand off.
- **Secondary:** Standalone “这些够了吗” / “我其实已经付了” are edge cases; triage_conversation handles them correctly when context exists.

### Whether It Was Worth It

Yes. The audit pinpointed the failure mode and a clear fix.

---

## 6. Iteration Loop 2

### Small Fix Applied

**Correction + embedded urgency question:** When handoff, `key == other_corrected`, and the last customer message contains urgency/next-step markers (“最要紧”, “先干嘛”, “办公室先看什么”, etc.) AND category is `payment_lapse_expiration` or `cancellation_warning`, the reply now answers the question first:

- **ZH:** “您这边最要紧的是等办公室确认付款是否到账；如果确认了您这边就不用再做什么。办公室会尽快处理，有结果会联系您。”
- **EN:** “The most important thing for you now is to wait for our office to confirm whether the payment was received; if confirmed, you don't need to do anything else. Our office will process this and follow up with you.”

### What Changed

- `services/fiqa_api/inbox_triage/triage.py`: Added block after document-clarification handling to detect correction + embedded question and build a tailored answer for payment/cancellation context.

### What Improved

- SIM1 Turn 3 now answers “最要紧做什么” directly.
- All 53 inbox triage, 38 multi-turn, and 27 Simulation Assistant scenarios still pass.

### What Still Remains Weak

- **Renewal/claim “办公室先看什么”:** Similar logic could be added for `customer_question` (renewal_premium, claim_intake) when the user asks “办公室先看什么” or “先干嘛” in a correction or handoff context. Lower priority.
- **Standalone “这些够了吗” / “我其实已经付了”:** These remain unclear when sent without context. Acceptable; they are not realistic first messages.

### Whether the Loop Was Worth It

Yes. One small, targeted fix improved a high-value trial scenario (SIM1) with no regressions.

---

## 7. Final Optimization Direction

### 1. Biggest Reason Answers Feel 答非所问

**Correction + embedded question:** When the user corrects and asks “最要紧做什么” or “先干嘛” in the same message, the system used a generic correction handoff and did not answer the question.

### 2. Main Layer Responsible

| Layer | Responsibility |
|-------|----------------|
| **Reply strategy** | Primary — follow_up_type prioritizes correction over urgency_question; reply logic did not handle combined case. |
| **Intent** | Minor — classification is correct. |
| **Routing** | Not the cause. |
| **Over-handoff** | Not the cause — handoff timing is fine; the issue is reply content. |
| **Lack of “answer first”** | Yes — the “answer first” rule existed for clarification_question and urgency_question, but correction short-circuited it. |

### 3. Single Highest-Value Optimization Direction

**Extend “answer first” to correction + embedded question.**

When a correction message also contains an explicit question (“最要紧做什么”, “办公室先看什么”), treat it as “answer first” and reply with a direct answer before the handoff suffix.

### 4. Best Small Next Step

- **Done:** Payment/cancellation correction + “最要紧做什么” — implemented.
- **Next:** Add similar handling for renewal_premium and claim_intake when the user asks “办公室先看什么” or “先干嘛” in a correction or handoff context. Low effort, extends the same pattern.

### 5. What to Postpone

- Broad “answer first” refactor across all categories.
- LLM-based reply generation for answer alignment.
- Handling standalone “这些够了吗” / “我其实已经付了” as first messages (edge case).
- Scenario pack expansion for “answer the ask” cases — current pack is sufficient for now.

---

## 8. 中文宏观总结

- **现在为什么会答非所问：** 当用户在同一句话里既纠正（“其实已经付了”）又提问（“最要紧做什么”）时，系统只按“纠正”处理，回复“好的，明白了”，没有回答“最要紧做什么”。
- **最大问题在：** 回复策略层（reply strategy），不是路由或意图分类。
- **最值得优化的方向：** 在“纠正 + 内嵌问题”的场景下，先回答问题再交接。
- **如果只改一件事：** 已改：付款/取消场景下，纠正 + “最要紧做什么” → 先回答再交接。
- **哪些问题先不要动：** 单独的“这些够了吗”“我其实已经付了”（无上下文）保持 unclear；大范围重构、LLM 生成回复暂不碰。

---

## 9. COPY/PASTE FOUNDER BLOCK

```
Answer Alignment Audit — Founder Summary

Biggest answer-quality problem:
  When the user corrects ("其实已经付了") AND asks a question ("最要紧做什么") in the same message,
  the system replied "好的，明白了。办公室会尽快处理" — without answering the question.

Biggest root cause:
  Reply strategy: correction overrides embedded question. The system treated it as pure correction
  and never ran the "answer first" logic for the urgency question.

Best optimization direction:
  Extend "answer first" to correction + embedded question. When the message contains both
  correction markers and urgency/next-step question markers, answer the question first, then hand off.

Best immediate next step:
  DONE: Payment/cancellation + "最要紧做什么" — now answers directly.
  NEXT: Add same pattern for renewal/claim "办公室先看什么" (low effort).

What to postpone:
  - Broad refactor of reply strategy
  - LLM-based answer generation
  - Standalone "这些够了吗" / "我其实已经付了" (edge case, low value)
```

---

*End of report*
