# Answer Alignment Audit — Execution Outline

**Sprint:** Answer Alignment Audit + Optimization Direction  
**Created:** 2026-03-15

---

## 1. Examples to Inspect

### A. Direct answer expected
- “这个英文 notice 说 payment failed，我现在怎么办？”
- “宝马x5，多少钱？”
- “刚撞了，对方跑了，我现在先干嘛？”
- “我上周已经发过了，怎么还在追材料？”

### B. Mixed ask
- “payment failed 怎么办，另外 dec page 我上周发过了”
- “我刚买了车，怎么保？大概要多少钱？”

### C. Clarification follow-up
- “这些够了吗？”
- “我其实已经付了”
- “garaging proof 是什么意思？”

### D. Simulation Assistant scenarios (SIM1–SIM15)
- SIM1: payment failed → 怎么办 → 发截图 → 其实付了，最要紧做什么
- SIM2: dec page + garaging → 发过了 → garaging 是什么意思
- SIM3: 宝马X5 保费 → 2024年 → 90210 下周提车，够了吗
- SIM5: 刚出事故 → 对方跑了 → 最要紧做什么
- SIM6: 保费太高 → 发你微信了 → 少一辆车便宜点？办公室先看什么？

---

## 2. Layers to Audit

| Layer | What to check |
|-------|---------------|
| **Intent** | Does classification match the real ask? |
| **Routing** | Fast path vs LLM — does either over-generalize or over-mechanize? |
| **Reply strategy** | Answer first vs collect first; handoff timing |
| **Reply wording** | Too office-like? Too generic? Missing direct answer? |
| **Follow-up type** | clarification_question, urgency_question → answer first? |
| **Scenario realism** | Do simulations expose “answer the ask” cases? |

---

## 3. Tests / Simulations to Run

| Script | Purpose |
|--------|---------|
| `run_inbox_triage_scenarios.py` | Single-turn classification + draft quality |
| `run_multi_turn_simulations.py` | Multi-turn handoff + reply quality |
| `run_simulation_assistant_scenarios.py` | SIM1–SIM15 + R1–R8 |
| `audit_state_field_accuracy.py` | Structured field extraction |
| `verify_speed_routing.py` | Fast vs LLM path behavior |
| `guardrail_inbox_triage.sh` | Full guardrail pass |

---

## 4. Likely Loop Count

- **Loop 1:** Baseline audit + diagnosis + direction.
- **Loop 2:** Small fixes only if clearly high-value, low-risk.

---

*End of execution outline*
