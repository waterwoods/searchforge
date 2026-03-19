# Realistic Conversation Pack Spec

**Purpose:** Define the 10–30 realistic conversation set for stress-testing before broker trial.

---

## Coverage Requirements

| Area | Count | Examples |
|------|-------|----------|
| Quote / add-car | 3–4 | Shorthand, vague, mixed lang |
| Material collection / already sent | 3–4 | Frustrated, "又发了", "上周就发了" |
| Payment / billing clarification | 3–4 | Already paid, notice confusion |
| Renewal increase / premium review | 2–3 | Vague, shorthand |
| Remove vehicle / policy change | 2 | Shorthand, correction |
| Claim first notice | 2 | Panic, hit-and-run |
| Talk to Agent | 1–2 | Mid-flow, free-text |
| Mixed intent | 2–3 | Add-car + notice, premium + doc |
| Correction-heavy | 2–3 | "不是这个", "说错了" |
| Vague / shorthand | 2–3 | Ultra-short, no verb |

---

## Per-Conversation Definition

For each conversation:
- **Business goal:** What broker needs to achieve
- **Why it matters:** Commercial impact
- **Likely failure mode:** Where product might break
- **Good behavior:** What success looks like

---

## Realistic Variations (Non-Negotiable)

- Shorthand: "x5 多少钱", "加车 90210"
- Mixed Chinese/English: "payment failed 怎么办"
- Vague: "那个材料", "上次那个"
- Correction mid-flow: "不是 payment failed，是 final notice"
- Already-sent / already-paid: "我付了呀", "上周发过了"
- Emotional: "都发过了怎么还要"
- Partial info: "VIN 还没有"
- Late clarification: "是我老婆开那辆"
- Talk to Agent: "联系人工", "找陈奎"
- Mixed intent: "加车，顺便 notice 什么意思"

---

## Scenario IDs in Pack

See `configs/realistic_conversation_simulation_pack.json`.

---

*End of Pack Spec*
