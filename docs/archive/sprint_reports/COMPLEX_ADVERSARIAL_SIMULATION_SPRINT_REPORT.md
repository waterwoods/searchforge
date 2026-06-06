# Complex Adversarial Simulation Sprint Report

**Sprint:** Complex Adversarial Simulation  
**Date:** 2026-03-09  
**Status:** Complete

## 1. Stages completed

- Stage 1: Built mixed-intent pack (13 scenarios) and long-context pack (10 simulations)
- Stage 2: First-pass 13 strong, 6 acceptable, 4 weak
- Stage 3: Classified failures: mixed-intent prioritization, lost secondary intent, weak summary
- Stage 4: Prioritized fixes: claim+payment rule, mixed-intent replies, summary hints
- Stage 5: Implemented 5 fixes in triage.py
- Stage 6-7: Skipped
- Stage 8: 21 strong, 2 acceptable, 0 weak after fixes
- Stage 9: Complex pack in guardrail
- Stage 10: Accept

## 2. Complex scenario coverage

Mixed-Intent: add-car+garaging, premium+notice, claim+payment, payment+document, document+add-car. Long-Context: corrections (不是这个), vague follow-ups (就是上次那个材料我又发了), already-sent.

## 3. Failure classification

Mixed-intent prioritization (MI-CL2), lost secondary intent (MI-AC1, MI-PR3, MI-N2), weak summary (LC-AC1, LC-N1, LC-N2).

## 4. Fixes

1. Claim+payment both present → prefer claim
2. Add-car+garaging confusion → add garaging explanation
3. Premium/payment+document 发过 → add 如果材料说发过了我帮你核对
4. Summary: Customer corrected/clarified, Client says already sent

## 5. Validation

Inbox 44/44, Adversarial 27/27, Multi-turn 17/17, Complex 21+2 acceptable, Guardrail PASS.

## 6. 中文总结

混合意图和长期上下文测出加车+garaging、事故+付款、材料发过、客户纠正等问题。修好：claim+payment优先、garaging解释、材料核对、summary纠正/已发提示。五条主线更稳。

## 7. Cheat sheet

Add car: 加车+garaging → Fixed. Claim: 出事了+payment → Fixed. Premium/Payment+document: Fixed. Document+already sent: Fixed.

## 8. Live proof walkthroughs

1. **Add car + garaging:** 我想加一辆车，然后这个 garaging proof 又是什么？ → Before: add-car only. After: garaging explanation + add-car ask. Strong.
2. **Claim + payment:** 出事了要拍什么，还有payment failed什么意思 → Before: payment. After: claim first-step. Strong.
3. **Notice + correction:** 不是 payment failed，是 final notice，我发你截图 → After: Summary has Customer corrected + Client says already sent. Strong.
4. **Document + already sent:** 就是上次那个材料，我又发了 → After: Summary has Client says already sent. Strong.
5. **Premium + document:** 续保涨了好多，顺便dec page发过了还说要 → After: premium ask + 如果材料说发过了我帮你核对. Strong.

## 9. Remaining blockers

1. LC-AC3: Handoff at turn 2 when driver correction in turn 3
2. Three+ intents in one message not handled

## 10. Recommended next step

Add 2–3 complex examples to founder demo queue.
