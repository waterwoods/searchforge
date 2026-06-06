# Real Customer Pack — Realism Blueprint

**Sprint:** Real Customer Pack Mainline  
**Date:** 2026-03-13  
**Purpose:** Make Simulation Assistant feel like real small-client customer traffic, not teaching scripts.

---

## A. Why the current Simulation Assistant feels too "demo-like"

| Issue | Example |
|-------|---------|
| **Broker-forwarded voice** | "客户问：...", "客户说...", "我发了截图在微信" — broker dictation, not raw customer |
| **Too clean / complete** | "我买了台宝马X5，想问下保费多少钱" — real users say "宝马x5，多少钱" or "我新车，下周拿，保险大概？" |
| **Over-orderly field reveal** | Turn 1 quote → Turn 2 year → Turn 3 zip — too neat; real customers mix or omit |
| **Not enough messiness** | 15 scenarios mostly orderly; adversarial pack (27 messy) not in Simulation Assistant |
| **Mixed intent missing** | Single-intent per scenario; real: "加车，顺便 garaging proof 是什么？" |
| **Few corrections / emotion** | Few "我其实已经付了" style corrections; no "都发过了怎么还要", "还不行吗" |

---

## B. What "real customer style" means for this product

- **Short fragments** — "宝马x5，多少钱", "发你了", "续保涨了好多 有办法吗"
- **Mixed Chinese/English** — "dec page 我上周就发了", "payment failed 怎么办"
- **Incomplete information** — no year, no zip, wrong order
- **Late corrections** — "不是 payment failed，是 final notice"
- **"Already sent" confusion** — "都发过了怎么还要", "上次那个材料我又发了"
- **Emotional or impatient** — "还不行吗", "怎么还在追"
- **Screenshot / notice references** — "通知我发你了", "账单发你微信了" without full context
- **Mixed intent in one message** — "加车，顺便 garaging proof 是什么"
- **Common shorthand** — "发你了", "弄好了发你", "发你微信了"

---

## C. What the first real-customer pack should contain

| Flow | Scenario type | Example |
|------|---------------|---------|
| **Cancellation/payment** | Notice + cancel confusion, correction | "这个英文 notice 是不是要停了 我没看懂" → "我其实已经付了" |
| **Missing document** | Frustrated "already sent", vague | "都发过了怎么还要 declaration page" → "就是上次那个材料，我又发了" |
| **Add-car** | Ultra-short, fragment | "宝马x5，多少钱" → "2024年的，90210，下周拿" |
| **Add-car + doc** | Mixed intent | "我想加一辆车，然后这个 garaging proof 又是什么？" |
| **Claim** | Panic, hit-and-run | "刚撞了，对方跑了，我现在先干嘛" → "拍了现场照，发你微信了" |
| **Renewal** | Short, no bill | "续保涨了好多 有办法吗" → "账单我发你" |
| **Payment + doc** | Mixed intent | "payment failed 怎么办，另外dec page我上周发过了" |
| **Document chase** | Vague prior convo | "上次说那个材料我又发了 还不行吗" |

---

## D. What should NOT be overdone yet

- **100+ scenarios** — keep pack compact (6–10)
- **Fully generative synthetic pipeline** — scripted is fine for pilot
- **Edge cases too exotic** — focus on Chen Kui / small-client daily traffic
- **Destroy clarity** — realism, not unreadable chaos

---

## E. Source assets to reuse

| Source | Use |
|--------|-----|
| `configs/adversarial_real_user_scenarios.json` | A1, D1, D2, C1, N1, R3 — single-turn; add follow-up turns |
| `configs/mixed_intent_scenarios.json` | MI-AC1, MI-N2 — convert to multi-turn |
| `configs/customer_entry_multi_turn_simulations.json` | MT22, MT29, MT33, MT34 — already multi-turn, messier wording |

---

*See also: `docs/SIMULATION_ASSISTANT_SPEED_REALISM_AUDIT_REPORT.md`, `docs/ADVERSARIAL_REAL_USER_SIMULATION_SPRINT_REPORT.md`*
