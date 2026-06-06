# Scenario Handling Matrix Spec

**Sprint:** Top Scenarios Hardening Master Sprint

---

## Add-Car Quote

| Field | Value |
|-------|-------|
| Business goal | Collect vehicle + zip + delivery for quote |
| Common phrasings | 加车, 新车, 报价, 多少钱, add car, quote for, how much |
| User intent | New vehicle quote request |
| Next-best-question | year → model → zip → delivery (1–2 per turn) |
| Collected / still_needed | year, model, zip, delivery, driver |
| Route | FAST (rule-based) |
| Handoff | (year+model or VIN) + zip; delivery nice-to-have |
| Summary | "Add car quote. Collected: year, model, zip. Still needed: delivery." |
| Guardrails | Do NOT generic fallback for 新车保险多少; ask year/model |

## Payment Issue / Cancellation Risk

| Field | Value |
|-------|-------|
| Business goal | Urgent same-day action; verify payment/notice |
| Common phrasings | payment failed, 付款, 停保, 保单要停, overdue |
| User intent | Payment problem or cancellation risk |
| Next-best-question | Notice, screenshot, "I paid" |
| Route | FAST |
| Handoff | Notice or screenshot or "I sent it" |
| Guardrails | **Premium + "我发你账单了" must NOT route here** — check premium_review first |

## Missing Document / Already Sent

| Field | Value |
|-------|-------|
| Business goal | Identify item, verify receipt, resend if needed |
| Common phrasings | dec page, garaging proof, 驾照, 发过了, already sent |
| User intent | Document chase; client says sent |
| Next-best-question | Which item; confirm resend |
| Route | FAST |
| Handoff | Item + sent status clear |
| Guardrails | Reassure-first when "发过了" |

## Remove Vehicle / Policy Change

| Field | Value |
|-------|-------|
| Business goal | Remove sold vehicle from policy |
| Common phrasings | 拿掉, 卖车, 删车, remove car, sold |
| User intent | Vehicle removal |
| Next-best-question | Vehicle, sale date, transfer status |
| Route | FAST |
| Handoff | Vehicle + sale date or transfer |
| Guardrails | No vehicle context in T1 → ask for vehicle; still customer_question |

## Premium Too High / Renewal

| Field | Value |
|-------|-------|
| Business goal | Review options; lower premium |
| Common phrasings | 保费太高, 怎么降, 续保涨, premium too high |
| User intent | Premium review |
| Next-best-question | Policy, bill, renewal notice |
| Route | FAST |
| Handoff | Policy or bill mentioned |
| Guardrails | **"我发你账单了" = bill sent for review, NOT payment failure** |

## Add Driver (NEW)

| Field | Value |
|-------|-------|
| Business goal | Add driver to policy (teen, spouse) |
| Common phrasings | 加个司机, 加人开车, 我儿子刚拿驾照, add driver |
| User intent | Add driver request |
| Next-best-question | Which vehicle, driver details, license |
| Route | FAST (after markers added) |
| Handoff | 2 turns |
| Guardrails | Do NOT unclear; route to customer_question with add-driver reply |

## Bundling / Discount (NEW)

| Field | Value |
|-------|-------|
| Business goal | Cross-sell; home+auto discount |
| Common phrasings | bundling, 一起买能打折, home insurance 打折 |
| User intent | Bundling/discount inquiry |
| Next-best-question | Current policies, what they have |
| Route | FAST (after markers added) |
| Handoff | 2 turns |
| Guardrails | Route to customer_question / premium_review style |

---

*See: 04_CONVERSATION_STRATEGY_SPEC.md*
