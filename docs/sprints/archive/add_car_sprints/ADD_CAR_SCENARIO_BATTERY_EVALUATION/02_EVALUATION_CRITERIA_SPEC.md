# Evaluation Criteria Spec

For **each scenario**, reviewers answer:

1. **Playbook** — Did the system stay on the **Add-Car / quote intake** path (`customer_question` with add-car behavior), or drift to unrelated categories?
2. **Intent** — Did it reflect what the customer actually wanted (quote new car, correction, materials sent, side question)?
3. **Next asks** — Were the **missing fields** sensible (ZIP, delivery/pickup, driver, vehicle detail)—not redundant with what was already in the thread?
4. **Customer reply** — Was the draft **natural** for WeChat (not echoing the whole customer message, not generic “内容不完整” when the ask is simple)?
5. **Broker side** — Did `broker_next_step` / structured fields support **office action** (concrete vehicle, verify materials, confirm driver)?
6. **Broker confidence** — Would a broker feel **reassured** or **nervous** showing this to a peer?
7. **Broker-review gate** — **Acceptable for broker review** vs not (binary judgment for demo).

## Classification labels

| Label | Meaning |
|-------|---------|
| **Strong** | Correct playbook, sensible slot logic, natural draft, broker step actionable; no material embarrassment risk. |
| **Acceptable** | Mostly correct; small friction (wording echo, redundant clause, minor structured-field noise) that a broker can forgive in MVP. |
| **Weak** | Wrong next ask, stuck loop, redundant or confusing client draft, or structured output inconsistent with conversation—**should fix before scaling demos**. |
| **Trust-breaking** | Wrong category, false “already sent,” generic failure on easy questions, or handoff that **misstates** the case—**high embarrassment risk** in front of a broker. |

## Rule-path vs LLM

This battery’s **frozen results** use **rule-based triage** (`LLM_GENERATION_ENABLED=false`). If you evaluate with LLM on, add a separate results file and note the path in the report header.
