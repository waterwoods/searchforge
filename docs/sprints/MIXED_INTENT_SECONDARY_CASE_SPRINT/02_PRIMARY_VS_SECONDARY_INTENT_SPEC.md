# Primary vs Secondary Intent Spec

**Sprint:** Mixed-Intent + Secondary Case Strategy  
**Purpose:** Define what counts as primary vs secondary intent, same-goal vs different-goal.

---

## 1. Primary Intent

**Definition:** The main business goal the customer is trying to accomplish in this conversation turn.

| Type | Examples |
|------|----------|
| Add-car / quote | 加车, 新车报价, add car, new vehicle |
| Remove vehicle | 删车, 卖车, remove car |
| Premium review | 保费太高, 续保涨, premium too high |
| Payment / cancellation risk | payment failed, 停保, 付款失败 |
| Missing document | 缺材料, dec page 发过了, garaging proof |
| Claim intake | 出事故, 撞车, accident, claim |
| Notice confusion | 英文 notice 看不懂, what does this mean |
| Talk to agent | 联系办公室, 找人工 |

**Detection:** Uses existing markers in `configs/industries/insurance/markers.json` and `_classify_with_guardrails()` in triage.py.

---

## 2. Secondary Intent

**Definition:** A second, distinct business goal present in the same message or conversation.

| Type | Examples |
|------|----------|
| Document confusion | garaging proof 是什么, dec page 什么意思 |
| Premium review (as side) | 顺便保费能不能看一下 |
| Add-car (as side) | 另外我想加一台车 |
| Notice confusion (as side) | 这个 notice 什么意思 |
| Renewal (as side) | 保单是不是也快到期了 |
| Missing document (as side) | dec page 发过了还说要 |

---

## 3. Same-Goal Clarification / Correction

**Definition:** Customer is refining or correcting information about the SAME business goal.

| Type | Examples |
|------|----------|
| Correction | 不是 payment，是续保；说错了，是另一辆 |
| Clarification | declaration page 发你了，garaging 是什么意思 |
| Already sent | 材料发过了，上周发的 |
| Field addition | (add-car) 2024 Tesla Model Y，邮编 94102 |

**Rule:** Keep in current case. Do NOT split.

---

## 4. True Separate Business Goal

**Definition:** Customer introduces a different business outcome that would require different broker actions.

| Primary | Secondary (separate goal) |
|---------|---------------------------|
| Add-car | Premium review |
| Claim intake | Renewal question |
| Payment risk | Missing document (already sent) |
| Premium review | Remove vehicle + notice confusion |
| Notice confusion | Add-car |

**Rule:** Mark as secondary issue or suggest second case. Do NOT merge into one confusing case.

---

## 5. Side-Question Markers (Chinese + English)

| Marker | Meaning |
|--------|---------|
| 顺便问一下 | By the way / side question |
| 顺便 | By the way |
| 对了 | Oh, also |
| 另外 | Additionally |
| 还有一个问题 | One more question |
| 还有 | And also |
| and also | English equivalent |
| by the way | English equivalent |
| one more thing | English equivalent |

**Use:** When detected, treat following clause as candidate secondary intent.

---

## 6. Primary Selection Rules (When Multiple Intents Present)

| Situation | Primary | Rationale |
|-----------|---------|-----------|
| Claim + payment | Claim | Accident first response (existing rule) |
| Add-car + document confusion | Add-car | Main action; confusion is clarification |
| Payment + document already sent | Payment | Urgency; document is "also" |
| Premium + remove-car + notice | Premium | Most actionable first |
| Notice + add-car | Notice or add-car | Depends on urgency; notice often urgent |

---

*End of Spec*
