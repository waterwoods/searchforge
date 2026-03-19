# Small-Business Readiness Stress Test Report

**Sprint:** Small-Business Readiness Stress Test  
**Date:** 2026-03-14  
**Execution:** Multi-angle evaluation, no feature building

---

## 1. Sprint Theme

**What was evaluated:** Turn 1 responsiveness, language naturalness, Case Report accuracy, and overall small-business trust/sellability for the Chen Kui Insurance Unified Entry product.

**Why now:** Founder observes Turn 1 feels very slow (15–20+ seconds), language sometimes too system-like, and needs stronger confidence on speed, smoothness, case report accuracy, and sellability before pilot conversations.

---

## 2. Control Docs Created

| Doc | Path |
|-----|------|
| Sprint Blueprint | `docs/sprints/SMALL_BUSINESS_READINESS_STRESS_TEST_BLUEPRINT.md` |
| Execution Outline | `docs/sprints/SMALL_BUSINESS_READINESS_EXECUTION_OUTLINE.md` |
| Evaluation / SLA Criteria | `docs/sprints/SMALL_BUSINESS_READINESS_SLA_CRITERIA.md` |

---

## 3. Baseline Audit

### Speed

| Dimension | Classification | Evidence |
|-----------|----------------|----------|
| **Turn 1 latency (rule path)** | **Strong** | Rule-based triage: ~50–200 ms. No LLM, no embedding. |
| **Turn 1 latency (LLM path)** | **Risky** | When `LLM_GENERATION_ENABLED=1`: LLM call 1.5–5 s; cold start 5–15 s. **15–20 s plausible.** |
| **Turn 2+ simple (fast path)** | **Strong** | already_sent, clarification, add-car field → rules only; ~50–200 ms when LLM enabled. |
| **Cold start** | **Weak** | Cloud Run idle → 5–15 s first request. Embedding warmup adds risk. |

**Verdict:** Rule path (default local demo) is fast. LLM path (production with OpenAI) makes Turn 1 **risky** — 15–20 s is plausible and too slow for small-business trust.

---

### Language

| Dimension | Classification | Evidence |
|-----------|----------------|----------|
| **Rule-based drafts** | **Acceptable to Strong** | Sample outputs: "这看起来是付款出了问题。现在最关键的是把最新通知或付款截图发我..." — natural, actionable. |
| **Add-car acknowledgement** | **Strong** | "好的，宝马X5。先把年份和地址邮编发我..." — office-natural. |
| **Robotic markers** | **Blocked** | FORMAL_DRAFT_MARKERS, ROBOTIC_DRAFT_MARKERS filter "Thank you for reaching out", "feel free to ask", "尊敬的". |
| **Unclear fallback** | **Weak** | "这段内容还不够完整。把完整通知或前后内容再发我一下" — generic when context is short. |

**Verdict:** Core flows (cancellation, add-car, missing-doc, claim) produce natural, broker-ready drafts. Edge case: very short/vague first message gets generic reply. **Acceptable** for trial; not perfect.

---

### Case Report

| Dimension | Classification | Evidence |
|-----------|----------------|----------|
| **Collected / Still needed** | **Strong** | State field audit: 7/7 passed. Add-car, missing-doc, claim, renewal, cancellation all correct. |
| **Broker next step** | **Strong** | Actionable, category-specific. |
| **Handoff timing** | **Strong** | 38/38 multi-turn simulations strong; 23/23 Simulation Assistant scenarios pass. |
| **Human confirmation** | **Strong** | `human_confirmation_required`, `human_confirmation_fields` surfaced for payment/cancellation, customer_says_sent. |

**Verdict:** Case report accuracy is **strong**. Trust boundary (human confirmation) is visible.

---

### Trust

| Dimension | Classification | Evidence |
|-----------|----------------|----------|
| **Nothing auto-sends** | **Strong** | UI and docs state broker confirms before sending. |
| **Human confirmation badge** | **Strong** | Gold tag when AI collected data broker should verify. |
| **Trust boundary visibility** | **Acceptable** | Clear in trial pack; may need reinforcement in UI copy. |

**Verdict:** Trust boundary is **acceptable to strong**. Not invisible.

---

### Pilot / Demo Maturity

| Dimension | Classification | Evidence |
|-----------|----------------|----------|
| **Guardrail** | **Strong** | All 8 steps pass: inbox triage, multi-turn, adversarial, complex adversarial, simulation assistant, case persistence. |
| **UI build** | **Strong** | `npm run build` succeeds. |
| **Scenario coverage** | **Strong** | 49 inbox scenarios, 38 multi-turn, 27 adversarial, 23 complex, 23 Simulation Assistant. |

**Verdict:** Pilot/demo maturity is **strong**. Scripts and coverage are production-grade.

---

## 4. Multi-Angle Test / Simulation Pass

### Tests Run

| Test | Result |
|------|--------|
| `run_inbox_triage_scenarios.py` (LLM=0) | 49/49 passed |
| `run_multi_turn_simulations.py` (LLM=0) | 38 strong, 0 weak |
| `audit_state_field_accuracy.py` (LLM=0) | 7/7 passed |
| `verify_speed_routing.py` (LLM=0) | 6/6 OK |
| `guardrail_inbox_triage.sh` | PASS |
| `run_simulation_assistant_scenarios.py` | 23/23 pass |
| `run_adversarial_simulation.py` | 27 strong |
| `run_complex_adversarial_simulation.py` | 22 strong, 1 friction (LC-AC3) |
| `cd ui && npm run build` | Success |

### What Passed

- All scenario packs pass.
- State field accuracy (collected, still_needed, follow_up_type) correct.
- Speed routing logic verified (Turn 1 → rule/LLM; Turn 2+ simple → fast when LLM on).
- One friction: LC-AC3 ("我刚才说错了，是我老婆开那辆") — handoff at turn 2, expected 3. Minor.

### What Looked Concerning

- **Turn 1 latency with LLM:** Not directly measured in this run (LLM=0 for guardrail). Architecture review confirms: Turn 1 always uses LLM when enabled; 15–20 s plausible with cold start + LLM.
- **R2 isolated:** "都发过了怎么还要" alone → unclear → generic draft. In full R2 scenario (with "declaration page") → missing_document → correct. Context matters.

### Directly Observed vs Inferred

| Item | Observed | Inferred |
|------|----------|----------|
| Rule path speed | Yes (~200 ms) | — |
| LLM path Turn 1 speed | No | From architecture: 2–6 s + cold start |
| Language quality | Yes (sample outputs) | — |
| Case report accuracy | Yes (audits) | — |
| Small-business perception | No | From criteria + founder concerns |

---

## 5. Targeted Scenario Evaluation

### Real Customer Style (R1, R2, R3)

| Scenario | Speed feel | Language realism | Case report | Trust | Business usefulness |
|----------|------------|------------------|-------------|-------|---------------------|
| **R1** Notice + cancel | Fast (rule) | Strong: "这看起来是付款出了问题..." | Strong | Strong | High |
| **R2** Doc frustrated | Fast (rule) | Strong in context | Strong | Strong | High |
| **R3** Add-car ultra-short | Fast (rule) | Strong: "好的，2024年的。先把地址邮编发我..." | Strong | Strong | High |

### Recommended Demo Path (SIM1, SIM2, SIM3)

| Scenario | Speed feel | Language realism | Case report | Trust | Business usefulness |
|----------|------------|------------------|-------------|-------|---------------------|
| **SIM1** Cancellation | Fast (rule) | Strong | Strong | Strong | High |
| **SIM2** Missing document | Fast (rule) | Strong | Strong | Strong | High |
| **SIM3** Add-car | Fast (rule) | Strong | Strong | Strong | High |

### Strongest Multi-Turn Proof (SIM15)

| Scenario | Speed feel | Language realism | Case report | Trust | Business usefulness |
|----------|------------|------------------|-------------|-------|---------------------|
| **SIM15** Add-car 3-turn | Fast (rule) | Strong | Strong | Strong | High |

### Mixed-Intent (R4, R7)

| Scenario | Speed feel | Language realism | Case report | Trust | Business usefulness |
|----------|------------|------------------|-------------|-------|---------------------|
| **R4** Add-car + garaging | Fast (rule) | Strong | Strong | Strong | High |
| **R7** Payment + dec page | Fast (rule) | Strong | Strong | Strong | High |

**Note:** All evaluations above assume rule path (LLM=0). With LLM=1, Turn 1 would add 2–6 s; cold start adds 5–15 s.

---

## 6. Small-Business Readiness Judgment

### What a Small Business Would Likely Like

- **Structured output:** Clear next step, collected/still needed chips, draft reply.
- **No auto-send:** Broker stays in control.
- **Bilingual:** Chinese + English support.
- **Coverage:** Cancellation, add-car, missing-doc, claim, renewal — all handled.

### What They Would Likely Worry About

- **Turn 1 speed:** 15–20 s is too slow. "Is it broken?" risk.
- **Edge cases:** Very short/vague first message → generic reply.
- **Trust:** "Human confirmation recommended" — good, but some may not fully understand.

### Would They Try It?

- **Rule path (local demo):** Yes. Fast, responsive, natural.
- **LLM path (production):** Maybe. Turn 1 slowness could cause abandonment.

### Would They Pay for a Pilot?

- **With Turn 1 fix:** More likely. Value is clear.
- **Without fix:** Hesitant. Speed is a blocker.

---

## 7. Optional Re-Check Loop

**Used:** Yes.

**What was rechecked:** Turn 1 latency assumptions.

**What changed in confidence:** Confirmed from architecture. Turn 1 always uses LLM when `LLM_GENERATION_ENABLED=1`. No rule-based path for Turn 1. Cold start + LLM = 7–21 s. **15–20 s is plausible and too slow.**

---

## 8. Final Product Decision

### Current Maturity Level

| Level | Verdict |
|-------|---------|
| Internal demo only | ✅ Ready |
| Founder demo | ✅ Ready |
| Early pilot conversation | ✅ Ready (with caveat: use rule path or fix Turn 1) |
| Small paid trial | ⚠️ Ready with caveat: Turn 1 speed is a blocker |

### Top 5 Strengths

1. **Case report accuracy** — Collected, still needed, broker next step, human confirmation all correct.
2. **Scenario coverage** — 49+38+27+23 scenarios pass; strong multi-turn, adversarial, mixed-intent.
3. **Language naturalness** — Core flows produce office-natural drafts; robotic markers blocked.
4. **Trust boundary** — Human confirmation visible; nothing auto-sends.
5. **Guardrail maturity** — Scripts, guardrails, persistence all production-grade.

### Top 5 Weaknesses / Risks

1. **Turn 1 latency (LLM path)** — 15–20 s plausible; too slow for small-business trust.
2. **Cold start** — 5–15 s extra on first request; Cloud Run idle.
3. **Unclear fallback** — Very short/vague first message → generic "这段内容还不够完整".
4. **LC-AC3 friction** — Minor handoff timing; "我刚才说错了" edge case.
5. **Default config** — Local demo uses rule path (fast); production may use LLM (slow) without clear operator guidance.

### Strongest Sellable Value

**"试用一个月：帮你把客户发来的messy消息整理成结构化case，有下一步动作、收集了什么、还缺什么、草稿回复。你确认后再发，不自动发送。"**

### Single Biggest Blocker to Small-Business Conversion

**Turn 1 speed.** 15–20 seconds feels broken. Brokers will abandon before seeing value.

### What the Founder Should Do Next

| When | Action |
|------|--------|
| **Immediately** | For pilot demo: use rule path (LLM_GENERATION_ENABLED=0) or ensure warm backend. Document Turn 1 latency caveat. |
| **This week** | Add Turn 1 latency mitigation: streaming/typing indicator, or pre-warm backend before demo. Consider rule-based Turn 1 for high-frequency intents (add-car, payment, missing-doc) when LLM disabled. |
| **Later** | Explore LLM caching, smaller model for Turn 1, or hybrid rule+LLM for Turn 1 intent. |

---

## 9. Iteration Log

### Loop 1: Baseline + Script Pass

| Item | What was evaluated | What increased confidence | What reduced confidence | What still needs checking |
|------|-------------------|---------------------------|-------------------------|---------------------------|
| Inbox triage | 49 scenarios | All pass | — | — |
| Multi-turn | 38 simulations | All strong | — | — |
| State audit | 7 cases | 7/7 passed | — | — |
| Speed routing | 6 cases | Logic correct | — | LLM=1 live test |
| Guardrail | 8 steps | All pass | — | — |
| **Worth it?** | Yes | Scenario coverage, case accuracy | — | Turn 1 live latency |

### Loop 2: Targeted Scenario Evaluation

| Item | What was evaluated | What increased confidence | What reduced confidence | What still needs checking |
|------|-------------------|---------------------------|-------------------------|---------------------------|
| R1, R2, R3 | Real customer style | Language natural, case correct | — | — |
| SIM1–3 | Demo path | All strong | — | — |
| SIM15 | Multi-turn proof | Context preserved | — | — |
| R4, R7 | Mixed intent | Handled | — | — |
| **Worth it?** | Yes | Business usefulness clear | — | — |

### Loop 3: Re-Check (Turn 1 Latency)

| Item | What was evaluated | What increased confidence | What reduced confidence | What still needs checking |
|------|-------------------|---------------------------|-------------------------|---------------------------|
| Architecture | triage.py, SPEED_ROUTING | Turn 1 always LLM | — | — |
| Cold start | ready.py, clients.py | 5–15 s documented | — | — |
| **Worth it?** | Yes | 15–20 s plausible; confirmed blocker | — | — |

### Loop 4: Final Judgment

| Item | What was evaluated | What increased confidence | What reduced confidence | What still needs checking |
|------|-------------------|---------------------------|-------------------------|---------------------------|
| Maturity | All dimensions | Ready for founder demo | Turn 1 speed | — |
| **Worth it?** | Yes | Clear verdict, actionable next step | — | — |

---

## 10. 中文宏观总结

**现在这个产品能不能卖给小企业试一试？**  
能。但有一个前提：**第一轮速度不能太慢**。如果用规则路径（LLM_GENERATION_ENABLED=0），本地 demo 很快，可以卖。如果用 LLM 路径且冷启动，15–20 秒会让小企业觉得「坏了」，不敢试。

**最大的优点是什么？**  
Case report 准确、结构清晰、语言自然、信任边界明显。多轮对话、混合意图、对抗场景都覆盖得好。

**最大的问题是什么？**  
**第一轮速度**。LLM 路径下 Turn 1 必走 LLM，冷启动 + LLM 约 7–21 秒，15–20 秒是常见情况，太慢。

**第一轮速度到底是不是太慢？**  
是。在 LLM 启用、且后端冷启动时，15–20 秒是合理的。规则路径下是 50–200 毫秒，不慢。

**语言和 case report 够不够自然、够不够准？**  
够。核心流程（取消、加车、缺材料、理赔、续保）语言自然，case report 准确，Collected/Still needed 正确。

**现在最该先修什么？**  
**第一轮速度**。要么 demo 用规则路径，要么加预热/流式反馈，要么探索 Turn 1 规则+LLM 混合。

---

## 11. COPY/PASTE FOUNDER BLOCK

```
============================================
SMALL-BUSINESS READINESS — FOUNDER SUMMARY
============================================

Current level: Ready for founder demo / early pilot conversation.  
Small paid trial: Ready with caveat — Turn 1 speed is a blocker.

STRONGEST VALUE
试用一个月：帮你把客户发来的messy消息整理成结构化case，有下一步动作、收集了什么、还缺什么、草稿回复。你确认后再发，不自动发送。

BIGGEST BLOCKER
Turn 1 speed. 15–20 seconds (LLM path + cold start) feels broken. Brokers will abandon.

TOP STRENGTHS
1. Case report accuracy: Collected, still needed, broker next step, human confirmation all correct.
2. Scenario coverage: 49+38+27+23 scenarios pass.
3. Language naturalness: Core flows produce office-natural drafts.
4. Trust boundary: Human confirmation visible; nothing auto-sends.
5. Guardrail maturity: Scripts, persistence, production-grade.

TOP RISKS
1. Turn 1 latency (LLM path): 15–20 s plausible.
2. Cold start: 5–15 s extra.
3. Unclear fallback: Very short first message → generic reply.
4. LC-AC3 friction: Minor handoff edge case.
5. Default config: Local fast; production may be slow.

BEST IMMEDIATE NEXT STEP
For pilot demo: use rule path (LLM_GENERATION_ENABLED=0) or ensure warm backend.  
This week: Add Turn 1 latency mitigation (streaming indicator, pre-warm, or rule-based Turn 1 for high-frequency intents).
```

---

*End of report*
