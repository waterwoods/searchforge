# Broker Trial Handoff Simulation Spec

**Sprint:** Broker Trial Simulation + Handoff Timing Audit  
**Purpose:** Define realistic simulation pack focused on handoff timing.

---

## Simulation Pack: Handoff Timing Focus

| ID | Category | Name | Business Goal | Why Timing Matters | Likely Failure Mode | Good Timing |
|----|----------|------|---------------|-------------------|---------------------|-------------|
| HT1 | add_car | Add-car + one more detail after handoff point | Collect vehicle + zip + delivery + driver | User may add "对了 是我老婆开" in T3 | Hand off T2, miss driver | Ask driver at T2; hand off T3 |
| HT2 | missing_document | Missing doc + another question in T3 | Dec page sent; garaging question | User asks "garaging proof 是什么意思" in T3 | Hand off T2, never answer T3 | Hand off T2 with answer, or defer to T3 |
| HT3 | premium_review | Premium + remove-vehicle idea after summary | Bill sent; remove-vehicle interest | User adds "其中一辆去掉会便宜吗" in T3 | Hand off T2, miss remove intent | Hand off T3 with both |
| HT4 | talk_to_agent | Talk to agent — handoff should stay fast | Customer wants human | Must hand off immediately | Slow handoff | Hand off T1 |
| HT5 | add_car | Correction after likely handoff point | Wrong vehicle corrected | "不是这个车 是另一辆 2024 Tesla" | Hand off with wrong vehicle | Use correction; hand off with correct |
| HT6 | mixed_intent | Mixed intent before handoff | Add-car + document confusion | Two intents in one message | Premature closure on one | Surface both; hand off when both addressed |
| HT7 | vague | Vague user — should NOT hand off early | "帮我" / "在吗" | Hand off T1 with nothing | No handoff T1; ask clarifying |
| HT8 | add_car | Add-car: user adds detail in same turn as "还有一个问题" | Vehicle + side question | "2024 X5 90210 下周提车 对了 garaging proof是什么" | Ignore side question | Answer question; hand off with both |
| HT9 | payment_failed | Payment + correction in T3 | Paid + sent screenshot | T2: "我付了" T3: "截图发你微信了" | Hand off T2 without screenshot | Hand off T3 with screenshot |
| HT10 | premium_review | Premium: bill sent T2, remove-vehicle T3 | Renewal + remove interest | T2: "账单发你了" T3: "2021 Accord 想拿掉" | Hand off T2, miss which vehicle | Hand off T3 with vehicle |

---

## Per-Simulation Definition

### HT1 — Add-car + one more detail after handoff point
- **Turns:** T1: "加车 2024 Tesla Model Y" T2: "90210 下周提车" T3: "对了 是我老婆开"
- **Expected:** Hand off at T3 (ask driver at T2)
- **Failure:** Hand off at T2, broker misses driver

### HT2 — Missing doc + another question in T3
- **Turns:** T1: "要dec page和garaging proof" T2: "dec page发你了" T3: "garaging proof 是什么意思"
- **Expected:** Either hand off T2 with answer in draft, or defer to T3. Broker must see garaging question.
- **Failure:** Hand off T2, T3 never processed; customer never gets answer

### HT3 — Premium + remove-vehicle after summary
- **Turns:** T1: "续保涨了好多" T2: "账单发你了" T3: "其中一辆去掉会便宜吗"
- **Expected:** Hand off at T3 with remove_vehicle_interest
- **Failure:** Hand off T2, miss remove intent

### HT4 — Talk to agent (fast handoff)
- **Turns:** T1: "联系人工"
- **Expected:** Hand off T1
- **Failure:** Ask clarifying question

### HT5 — Correction after likely handoff point
- **Turns:** T1: "加车 2021 Honda" T2: "不是这个 是另一辆 2024 Tesla Model Y" T3: "90210 下周提车"
- **Expected:** Hand off T3 with 2024 Tesla
- **Failure:** Hand off with 2021 Honda

### HT6 — Mixed intent before handoff
- **Turns:** T1: "想加车 顺便 garaging proof 是什么"
- **Expected:** Answer garaging; collect add-car; hand off when both addressed
- **Failure:** Close on one intent only

### HT7 — Vague user
- **Turns:** T1: "帮我"
- **Expected:** No handoff T1
- **Failure:** Hand off T1

### HT8 — Add-car + side question in same turn
- **Turns:** T1: "加车 2024 X5" T2: "90210 下周提车 对了 garaging proof 是什么"
- **Expected:** Answer garaging; hand off with vehicle info
- **Failure:** Ignore side question; generic handoff

### HT9 — Payment + screenshot in T3
- **Turns:** T1: "payment failed 怎么办" T2: "我昨天付了" T3: "截图发你微信了"
- **Expected:** Hand off T3 with screenshot
- **Failure:** Hand off T2 without screenshot

### HT10 — Premium + which vehicle in T3
- **Turns:** T1: "续保涨了好多" T2: "账单发你了" T3: "2021 Accord 想拿掉"
- **Expected:** Hand off T3 with which_vehicle_to_remove
- **Failure:** Hand off T2, miss vehicle

---

*End of Spec*
