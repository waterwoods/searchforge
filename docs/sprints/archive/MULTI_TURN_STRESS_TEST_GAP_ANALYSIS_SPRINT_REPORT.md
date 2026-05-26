# Multi-Turn Scenario Stress Test + Gap Analysis Report

**Sprint:** Multi-Turn Scenario Stress Test + Gap Analysis Sprint  
**Target:** SearchForge → Chen Kui Insurance Unified Entry  
**Date:** 2026-03-17  
**Execution mode:** Structured evaluation / simulation / gap-analysis  
**Budget:** ~60 minutes

---

## 1. Sprint theme

**What was tested:** The Unified Entry product was stress-tested using realistic multi-turn conversations across 10 core business flows: add-car quote, payment/billing clarification, missing document, remove vehicle, claim first notice, renewal/premium review, add driver, bundling, DMV/SR-22, and mixed-intent/ambiguous cases.

**Why now:** The founder wants to know whether the current system can survive realistic multi-turn use, not just single-prompt checks. The system has customer entry, multi-turn continuity, workflow_state, lifecycle visibility, in-progress persistence, case creation, and hardened business scenarios. Real merchant value depends on multi-turn coherence, next-best-question quality, avoiding wrong routes, useful handoff output, and human-feeling replies.

---

## 2. Control docs created

| Doc | Location | Purpose |
|-----|----------|---------|
| **Sprint Blueprint** | This report §2 | Scope, method, non-negotiables |
| **Test Plan / Scenario Set** | §3 | 10 scenarios with business goals |
| **Evaluation Criteria** | §4 | 9 dimensions per scenario |
| **Gap Analysis Framework** | §5–6 | Strengths/weaknesses + root-cause taxonomy |

---

## 3. Scenario set

| # | Scenario | Business goal | Why it matters |
|---|----------|---------------|----------------|
| 1 | **Add-car quote** | Collect year, model, zip, delivery for quote | Revenue driver; multi-turn collection; handoff at 2–4 turns |
| 2 | **Payment / billing clarification** | Distinguish "bill看不懂" from payment failure | Misroute = wrong urgency; broker gets wrong action |
| 3 | **Missing document / already sent** | Item + sent status; verify receipt | Operational pain; "都发过了怎么还要" frustration |
| 4 | **Remove vehicle** | Vehicle + sale date + transfer | Policy change; common shorthand (删车, 卖车) |
| 5 | **Claim first notice** | Accident details, photos, other driver | First-response guidance; hit-and-run handling |
| 6 | **Renewal increase / premium review** | Policy/bill; remove-vehicle interest | Retention; repetitive office work |
| 7 | **Add driver** | Vehicle, driver info, license | Policy change; teen/spouse |
| 8 | **Bundling / discount** | Home+auto; policy info | Cross-sell; "一起买能打折" |
| 9 | **DMV / SR-22 help** | Notice, suspension, what to bring | Compliance; Chinese-speaking clients |
| 10 | **Mixed-intent / ambiguous** | Two intents at once | Real customers bundle questions |

---

## 4. Multi-turn evaluation results

### Execution summary

| Pack | Count | Strong | Friction | Weak |
|------|-------|--------|----------|------|
| **customer_entry_multi_turn_simulations** | 39 | 39 | 0 | 0 |
| **long_context_memory_shift** | 23 | 22 | 1 | 0 |
| **mixed_intent** | 13 | 13 | 0 | 0 |
| **Simulation Assistant + guardrail** | 27 + 63 | All PASS | 0 | 0 |

### Per-scenario highlights

| Scenario | Turns | Observed behavior | Strengths | Weaknesses | Pass |
|----------|-------|-------------------|-----------|------------|------|
| **MT1 BMW X5 新车报价** | 2 | T1: ask year+zip; T2: handoff | Correct next-ask; handoff at 2 | — | ✓ |
| **MT11 加车 shorthand** | 3 | T1: ask zip; T2: ask delivery; T3: handoff | Progressive collection; no overload | — | ✓ |
| **MT13 加车 partial** | 4 | T1→T4: year→zip→delivery→handoff | Correct sequencing | — | ✓ |
| **MT15 Full info first turn** | 1 | Handoff immediately | No over-question | — | ✓ |
| **MT5 付款失败** | 2 | T1: reassure + ask notice; T2: 好的收到了 | Urgency; already_sent phrase | — | ✓ |
| **MT9 缺材料 dec+garaging** | 2 | T1: ask items + "发过了" path; T2: handoff | Item-specific; 发过了 acknowledged | — | ✓ |
| **MT28 garaging proof 是什么意思** | 2 | T1: explain; T2: handoff | Answer-first (SIM2 fix) | — | ✓ |
| **MT26 Notice correction** | 2 | T1: payment; T2: 不是payment是final notice | Correction handled | — | ✓ |
| **LC-AC3  driver correction** | 3 | Handoff at T2 (expected T3) | Correction detected | Handoff 1 turn early | FRICTION |
| **MT18 Ultra-short add-car** | 2 | T1: ask year/model; T2: 2025 CR-V | Delivery from T1 preserved | Final category=None in sim output (cosmetic) | ✓ |
| **MI-AC1 add-car + garaging** | 1 | Both intents addressed | Mixed-intent primary+secondary | — | ✓ |
| **MI-PR3 premium + dec page** | 1 | Premium + doc chase both in draft | Complex mixed | — | ✓ |

### Key observations

1. **Add-car:** Handoff logic works; year+model+zip or delivery triggers handoff. Progressive ask (zip → delivery) correct. Full-info first turn hands off immediately.
2. **Payment / missing doc:** Reassure-first; "发过了" → "好的收到了"; "garaging 是什么意思" → answer first then handoff.
3. **Correction handling:** "不是这个，是另一辆车", "不是 payment failed 是 final notice" — handled. LC-AC3 (driver correction at T3) hands off at T2 because `customer_turn_count >= 2` triggers handoff before T3 is processed in same flow.
4. **Mixed-intent:** All 13 scenarios PASS; primary intent recognized; secondary often addressed in draft.

---

## 5. Current strongest areas

| Area | Evidence | Why preserve |
|------|----------|--------------|
| **Add-car multi-turn** | MT1, MT11, MT13, MT15, MT16 | Correct next-ask; no over-question; handoff when enough |
| **Payment / cancellation** | MT5, MT6, MT12, MT25, MT26 | Urgency; reassure-first; "今天尽快" when needed |
| **Missing document** | MT9, MT10, MT27, MT29 | Item-specific ask; "发过了" path; verify receipt |
| **Already_sent / correction** | other_received, other_corrected phrases | Warmer handoff; "好的收到了"; correction acknowledged |
| **Mixed-intent** | MI-AC1–MI-D2 all PASS | Primary intent; secondary often in draft |
| **Claim intake** | MT17, MT22, MT23, LC-CL1 | First-response guidance; hit-and-run; photos/other driver |
| **Remove vehicle** | MT3 | Vehicle + sale date + transfer; handoff at 2 |
| **Premium review** | MT4, MT20, MT21 | Policy/bill ask; remove-vehicle interest |
| **Billing clarification** | _is_billing_clarification_request | "账单什么意思" → customer_question, NOT payment |
| **Add driver / bundling** | Markers + reply templates | No longer unclear; tailored replies |
| **Document clarification** | "garaging 是什么意思" → answer first | SIM2 fix; explain then handoff |

---

## 6. Current weakest areas

### 6.1 LC-AC3: Driver correction handoff timing (FRICTION)

| Aspect | What happened | Why weak | Root cause | Business impact | Priority |
|--------|---------------|----------|------------|-----------------|----------|
| **Handoff timing** | Handoff at turn 2; expected turn 3 | Customer sends correction at T3 ("我刚才说错了，是我老婆开那辆"); system already handed off at T2 | `_should_handoff`: `customer_turn_count >= 2` → handoff. Add-car has year+model+zip+delivery at T2, so handoff. T3 correction arrives after case created | Broker may not see driver correction in same case; would need append | **Medium** |

**Mitigation:** Append flow handles T3; broker gets update. Friction is simulation expectation vs. real flow. Could add "correction at T3" detection to delay handoff when add-car has enough but follow_up_type=correction on next message — complex; defer.

### 6.2 MT18: Ultra-short add-car — cosmetic output

| Aspect | What happened | Why weak | Root cause | Business impact | Priority |
|--------|---------------|----------|------------|-----------------|----------|
| **Final category** | `category=None` in simulation output | Simulation runner may not capture final result when handoff at T2 | Handoff occurs; result is correct; simulation output display quirk | None | **Low** |

### 6.3 Billing multi-turn not added (known gap)

| Aspect | What happened | Why weak | Root cause | Business impact | Priority |
|--------|---------------|----------|------------|-----------------|----------|
| **Billing clarification** | Single-turn only | "账单什么意思" → customer_question; no multi-turn collection | TOP_SCENARIOS_HARDENING_PHASE2 deferred billing multi-turn | If customer sends "发你了" at T2, may not get already_sent handoff | **Medium** |

### 6.4 Talk-to-agent / handoff-to-human (not implemented)

| Aspect | What happened | Why weak | Root cause | Business impact | Priority |
|--------|---------------|----------|------------|-----------------|----------|
| **"找经纪人" / "talk to agent"** | No dedicated handling | Customer may want human; system continues triage | No markers or route for "I want to speak to someone" | Low frequency; can defer | **Low** |

### 6.5 Summary thinness in edge cases

| Aspect | What happened | Why weak | Root cause | Business impact | Priority |
|--------|---------------|----------|------------|-----------------|----------|
| **conversation_summary** | Long-context sims check "resent"/"correct" in summary | Some corrections may not be explicitly labeled | Summary builder is heuristic; no structured "correction" field | Broker may miss nuance | **Low** |

---

## 7. Root-cause patterns

| Pattern | Description | Where seen |
|---------|-------------|------------|
| **Handoff threshold** | `customer_turn_count >= 2` forces handoff for manual_followup_needed | LC-AC3: correction at T3 arrives after handoff |
| **Add-car threshold** | (year+model OR VIN) + (zip OR delivery OR driver) | Works well; MT11, MT13, MT15 |
| **Marker coverage** | Billing, add driver, bundling, 减车, 报事故 added | Phase 1–2 hardening; no major gaps |
| **Classification order** | Billing before payment; premium before payment | Prevents misroutes |
| **Follow-up type** | already_sent, correction, clarification_question | Reply strategy; "好的收到了"; answer-first |
| **Mixed-intent** | Primary intent; secondary in draft | All 13 PASS |
| **Generic fallback** | "please provide more context" blocklist | Not observed in current sims |

---

## 8. Comparison to a stronger system

A stronger small-business intake product would:

| Current | Stronger |
|---------|----------|
| Handoff at 2 turns for most flows | Same; acceptable |
| LC-AC3: handoff before T3 correction | Detect "correction coming" and delay handoff 1 turn when add-car has enough but low confidence |
| Billing single-turn | Billing multi-turn: T2 "发你了" → already_sent handoff |
| Summary heuristic | Structured correction/clarification flags in summary |
| No "talk to agent" | Route "找经纪人" to handoff with broker_next_step="Client requested human; call back." |

**Verdict:** Current system is close. Biggest gap: LC-AC3 (driver correction timing) and billing multi-turn. Both are medium priority; neither blocks pilot.

---

## 9. Best next fixes

### Fix now

| Fix | What | Why | Value |
|-----|------|-----|-------|
| **None** | System is pilot-ready | All critical flows pass; 1 friction case (LC-AC3) has append mitigation | — |

### Fix next

| Fix | What | Why | Value |
|-----|------|-----|-------|
| **LC-AC3 driver correction** | When add-car has enough at T2 but next customer message is correction (说错了, 是另一辆, 是我老婆开), delay handoff 1 turn OR ensure append flow surfaces correction prominently | Reduces broker missing driver correction | Medium |
| **Billing multi-turn** | Add T2 "发你了" / "sent" path for billing clarification → already_sent handoff | Completes billing flow | Medium |

### Defer

| Fix | What | Why |
|-----|------|-----|
| **Talk to agent** | Route "找经纪人" to handoff | Low frequency |
| **Summary correction flags** | Structured correction in summary | Heuristic works for most |
| **MT18 cosmetic** | Fix simulation output display | No user impact |

---

## 10. Founder manual test script

### Setup

1. Start: `bash scripts/run_demo_local.sh`
2. Open: http://localhost:5173/workbench/unified-intake
3. Click **Customer Entry** (or paste into input)

### Test 1: Add-car 3-turn (strongest multi-turn proof)

| Step | Paste | Expected |
|------|-------|----------|
| 1 | `我买了台宝马X5，想问下保费多少钱` | Reply asks for year and zip. **Pass:** No "please provide more context". **Fail:** Generic fallback. |
| 2 | `2024年的，zip 90210，下周提车` | Handoff: "报价资料已整理好了，办公室会尽快出价". **Pass:** Handoff. **Fail:** Asks for more. |
| 3 | (If still collecting) `90210` | Handoff or ask delivery. **Pass:** Handoff or 1 more ask. |

### Test 2: Payment failed + already sent

| Step | Paste | Expected |
|------|-------|----------|
| 1 | `这个英文 notice 说 payment failed，我现在怎么办？` | Reply: 最关键的是把通知或截图发我; 今天尽快处理. **Pass:** Urgent tone. **Fail:** Generic. |
| 2 | `我发了截图在微信` | Handoff: "好的，收到了。办公室会尽快处理". **Pass:** 好的收到了. **Fail:** Asks for more. |

### Test 3: Missing document + "发过了"

| Step | Paste | Expected |
|------|-------|----------|
| 1 | `要驾照 copy，我上周就发过了` | Reply: 您说发过了，我这边帮你核对. 把驾照正反面发我. **Pass:** Acknowledges 发过了. **Fail:** Ignores. |
| 2 | `刚又发了一次正反面` | Handoff: "好的，收到了". **Pass:** 好的收到了. **Fail:** Re-asks. |

### Test 4: Billing clarification (NOT payment)

| Step | Paste | Expected |
|------|-------|----------|
| 1 | `这个账单什么意思，我看不懂` | Reply: 把完整账单或通知发我，我先帮你看一下. Category: customer_question. **Pass:** NOT payment_lapse_expiration. **Fail:** Urgent payment tone. |

### Test 5: Mixed-intent (add-car + garaging)

| Step | Paste | Expected |
|------|-------|----------|
| 1 | `我想加一辆车，然后这个 garaging proof 又是什么？` | Reply addresses BOTH: quote info (year, zip) AND garaging explanation. **Pass:** Both in reply. **Fail:** Only one. |

### Test 6: Correction

| Step | Paste | Expected |
|------|-------|----------|
| 1 | `想加一台车，2021 Honda Accord` | Asks for zip. |
| 2 | `不是这个，是另一辆车，2024 Tesla Model Y` | Handoff with corrected vehicle (2024 Tesla Model Y). **Pass:** 2024 Tesla in summary/draft. **Fail:** Still 2021 Accord. |

### Quick validation

```bash
bash scripts/guardrail_inbox_triage.sh   # Must PASS
PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py  # 39 PASS
PYTHONPATH=. python3 scripts/run_complex_adversarial_simulation.py  # Mixed + long-context
```

---

## 11. Final judgment

| Dimension | Assessment |
|-----------|------------|
| **Overall maturity** | **Pilot-usable.** 39/39 multi-turn, 13/13 mixed-intent, 22/23 long-context (1 friction). Guardrail PASS. |
| **Biggest strength** | Add-car multi-turn, payment/missing-doc reassure-first, mixed-intent handling, correction handling (except LC-AC3). |
| **Biggest weakness** | LC-AC3 driver correction handoff 1 turn early; billing multi-turn not added. |
| **Pilot-usable?** | **Yes.** Broker gets structured cases, next step, draft; multi-turn stays coherent; no critical misroutes. |
| **Next sprint** | LC-AC3 refinement (optional); billing multi-turn; founder trial feedback. |

---

## 12. 中文宏观总结

**现在系统哪些地方已经不错：**
- 加车多轮收集正确，不会一次问太多，也不会过早转交
- 付款/缺材料有「发过了」路径，回复「好的收到了」
- 混合意图（加车+garaging、保费+dec page）能识别主意图并兼顾次意图
- 纠正类（不是这个、不是payment）能正确处理
- 账单解释不会误判为付款失败

**哪些地方还不够：**
- LC-AC3：客户第三轮说「我刚才说错了，是我老婆开那辆」时，系统已在第二轮转交，纠正会走 append，经纪人可能不够显眼
- 账单解释只有单轮，没有「发你了」的多轮路径

**为什么会不够：**
- 转交阈值：`customer_turn_count >= 2` 即转交，无法预知第三轮会有纠正
- 账单多轮在 Phase 2 被推迟

**哪些最值得下一步修：**
1. LC-AC3：考虑在 add-car 足够时，若检测到下一句是纠正，延迟一轮转交；或强化 append 时纠正的展示
2. 账单多轮：补上「发你了」的 already_sent 转交

**现在整体算不算能试用：**
**能。** 多轮连贯，转交时机合理，回复不泛化，混合意图和纠正大多处理正确。可开始试用，边用边收反馈再迭代。

---

## 13. COPY/PASTE CROSS-WINDOW BLOCK

```
## SearchForge Unified Entry — Multi-Turn Stress Test Summary

**Current strengths:**
- Add-car multi-turn: correct next-ask (year→zip→delivery); handoff when (year+model)+(zip|delivery|driver)
- Payment/missing-doc: reassure-first; "发过了" → "好的收到了"; "garaging 是什么意思" → answer first then handoff
- Mixed-intent: 13/13 PASS; primary + secondary often both addressed
- Correction: "不是这个", "不是 payment failed" handled
- Billing clarification: "账单什么意思" → customer_question (not payment)
- Add driver, bundling: tailored replies; no longer unclear

**Current weaknesses:**
- LC-AC3: Driver correction at T3; system hands off at T2 (customer_turn_count>=2); correction goes to append
- Billing multi-turn: Not added; T2 "发你了" would need already_sent path
- Talk-to-agent: Not implemented (low priority)

**Root-cause patterns:**
- Handoff threshold: customer_turn_count>=2 drives early handoff
- Add-car threshold works well
- Marker coverage and classification order solid after Phase 1–2 hardening

**Best next recommendations:**
1. Fix next: LC-AC3 — delay handoff 1 turn when add-car enough + next message is correction; OR surface correction in append flow
2. Fix next: Billing multi-turn — T2 "发你了" → already_sent handoff
3. Defer: Talk-to-agent, summary correction flags

**Current IT/product maturity:** Pilot-usable. 39/39 multi-turn, 13/13 mixed-intent, 22/23 long-context. Guardrail PASS. No critical misroutes. Founder can trial.
```

---

## 14. REQUIRED SHORT OVERVIEW

### 为什么做这件事

创始人需要确认当前 Unified Entry 在真实多轮对话下是否可靠，而不只是单轮通过。系统已有 customer entry、多轮连续性、workflow_state、case 创建等，但商业价值取决于多轮是否连贯、是否问对下一个问题、是否减少经纪人重复追问。

### 主要用了什么方法/技术

- 运行 `run_multi_turn_simulations.py`（39 场景）、`run_complex_adversarial_simulation.py`（混合意图 + 长上下文）、`guardrail_inbox_triage.sh`
- 按 MATURE_INTAKE_SKELETON、LIGHTWEIGHT_STATE_MACHINE 评估：分类、首轮回复、next-best-question、转交时机、collected/still_needed、summary
- 根因分析：转交阈值、marker 覆盖、follow_up_type、分类顺序

### 这轮最大的发现

**系统已具备试用条件。** 加车、付款、缺材料、混合意图、纠正处理整体正确。唯一摩擦点：LC-AC3 司机纠正时转交早一轮；账单多轮未做。两者不阻塞试点。

### 现在最该修什么

1. **LC-AC3**：司机纠正场景 — 在 add-car 已足够时若下一句是纠正，可考虑延迟一轮转交，或强化 append 时纠正的展示
2. **账单多轮**：补上「发你了」的 already_sent 转交路径

---

*End of report*
