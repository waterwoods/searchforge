# Three Critical Entry Scenarios — Execution Outline

---

## Variants to Test

### Scenario 1 — Payment problem
- "付款有问题"
- "payment failed，现在怎么办？"
- "他说 payment failed，现在怎么办" (R20)
- Empty input (edge case)

### Scenario 2 — Quote problem
- "我才买了一个2026年的丰田花冠，大约半年的保费是多少？"
- "宝马x5，多少钱"
- "刚提一台X5，报价能看下吗" (ER1)
- "新车保险多少" (AC-ULTRA-2)
- Empty input (edge case)

### Scenario 3 — Missing-doc / already-sent
- "我上周已经发过了，怎么还在追材料？"
- "UW要dec page，我发过了"
- "发你了"
- "declaration page 我上周就发了，怎么还在追？" (MT29 T1)
- "客户说dec page发过了，carrier还说要" (F4)

---

## Surfaces Checked

- `triage_message()` — single-turn rule-based (LLM_GENERATION_ENABLED=0)
- `triage_conversation()` — multi-turn
- Scenario pack: inbox_triage_scenarios.json (R3, R9, R11, R20, R18, ER1, AC-ULTRA-2, F4, FAQ-AS1, MT29, D3, R7)

---

## Likely Loop Count

- Loop 1: Baseline + qualitative evaluation
- Loop 2: Small fixes if 1–2 high-ROI issues
- Loop 3: Optional, only if clearly valuable
