# Mixed-Intent + Secondary Case Strategy Report

**Sprint:** Mixed-Intent + Secondary Case Strategy Sprint  
**Created:** 2026-03-19  
**Scope:** SearchForge → Chen Kui Insurance Unified Entry

---

## 1. Sprint Theme

- **What was chosen:** Design and implement the first practical strategy for handling mixed-intent customer conversations — topic switching, side questions, multi-goal messages — without turning one case into a mess.
- **Why now:** Product is strong in scenario package, trial pack, scenario logic center. Real-world customers often mix goals ("顺便问一下", "另外", "对了"). If not handled, case summaries become messy, broker follow-up gets harder, trial confidence drops.

---

## 2. Document Set Created

| Doc | Purpose |
|-----|---------|
| `01_MIXED_INTENT_STRATEGY_BLUEPRINT.md` | Why mixed-intent; what we strengthen; what we defer |
| `02_PRIMARY_VS_SECONDARY_INTENT_SPEC.md` | Primary vs secondary; same-goal vs different-goal |
| `03_CASE_SPLIT_SECONDARY_ISSUE_DECISION_SPEC.md` | When to keep; when to mark; when to split |
| `04_BROKER_HANDOFF_CLARITY_SPEC.md` | How mixed-intent appears in broker view |
| `05_EXECUTION_OUTLINE.md` | Workstreams; loop plan |
| `06_ACCEPTANCE_MIXED_INTENT_CRITERIA.md` | Pass criteria |
| `07_FOUNDER_INSPECTION_NOTES.md` | What founder should inspect; test cases |
| `00_BASELINE_AUDIT.md` | Current gaps; case pollution risk; broker confusion risk |
| `INDEX.md` | Doc index |

---

## 3. Baseline Audit

| Area | Finding |
|------|---------|
| **Biggest mixed-intent weakness** | Secondary intent was invisible to broker; no structured "Also asked" |
| **Biggest case-pollution risk** | Low (we pick one category); risk was broker missing second topic |
| **Biggest broker-confusion risk** | Broker reads case, acts on primary, misses that customer also asked about X |
| **Already acceptable** | Mixed→LLM routing; claim+payment; payment+doc; premium+doc; add-car+garaging; correction hint |

---

## 4. 10–20 Point Breakdown

1. **Same-goal correction** — 不是 payment，是续保 → keep in current case; context_hint "Customer corrected/clarified"
2. **Same-goal clarification** — declaration page 发你了，garaging 是什么意思 → keep; answer in draft
3. **True secondary issue** — 加车 + 顺便保费看一下 → mark "Also asked: premium review"
4. **True main-topic switch** — V1: mark only; broker decides split
5. **Side-question markers** — 顺便, 另外, 对了, 还有一个问题, and also, by the way
6. **Keep-current-case rules** — Same-goal correction/clarification; secondary is quick answer; uncertain
7. **Split-case rules** — V1: no auto-split; recommend in broker note when justified
8. **Secondary-issue rules** — Add "Also asked: X" to summary when 2+ flow markers
9. **Broker summary expectations** — Primary intent first; "Also asked" when mixed
10. **Next-step expectations** — One main action; secondary visible in summary
11. **Workbench visibility** — secondary_issue_note as blue Tag when present
12. **Deferred** — Auto-split; full concurrent graphs; solve all ambiguity
13. **Reduces broker confusion** — Broker sees "Also asked" explicitly
14. **Improves trial realism** — Handles real mixed messages (payment+doc, add-car+garaging)
15. **Tests/simulations** — run_complex_adversarial_simulation.py mixed_intent; guardrail_inbox_triage
16. **Most risky gap (fixed)** — Secondary invisible → now in summary + Tag
17. **V1 handles** — Detect 2+ flows; pick primary; add "Also asked"; persist secondary_issue_note
18. **V2 can wait** — Auto-split; multi-threaded engine; full secondary draft coverage

---

## 5. Iteration Loop 1

**What was added/clarified:** Full doc set; `_detect_secondary_intent_hint()`; secondary in `_build_conversation_summary`; `secondary_issue_note` in triage result and case_store.

**Why it matters:** Broker can now see when customer asked two things. Case summary includes "Also asked: X".

**What became easier:** Reasoning about mixed-intent; broker handoff clarity; founder can explain strategy.

**What did not improve:** Single-turn triage_message path (simulation) doesn't get summary — uses triage_conversation for paste flow, so handoff path is covered.

**Whether loop 1 was worth it:** Yes. Foundation for broker visibility.

---

## 6. Iteration Loop 2

**What was fixed:** Secondary detection with primary-from-category fallback; `secondary_issue_note` in case_store (save + append); UI Tag for secondary.

**Why these fixes:** Broker needs to see secondary in workbench; append flow must preserve it.

**What improved vs loop 1:** End-to-end: triage → case → UI. Blue Tag makes secondary obvious.

**What still remained weak:** broker_next_step does not append "If customer also asked about X" — deferred to keep main action clear.

**Whether loop 2 was worth it:** Yes. Broker sees secondary in UI.

---

## 7. Iteration Loop 3

**What final hardening was done:** Added MI-AC5 scenario (顺便问一下 + garaging + add-car); all 14 mixed-intent scenarios pass; UI build verified.

**Why:** Side-question marker coverage; simulation proof.

**What improved vs loop 2:** 14/14 mixed-intent strong; new scenario validates 顺便问一下.

**What still remained weak:** broker_next_step append for secondary deferred; some edge cases (e.g. 3+ intents) pick first secondary only.

**Whether loop 3 was worth it:** Yes. Simulation proof; founder can demo.

---

## 8. Validation Summary

| Check | Result |
|-------|--------|
| `bash scripts/guardrail_inbox_triage.sh` | PASS |
| `run_complex_adversarial_simulation.py --pack mixed_intent` | 14/14 Strong |
| `cd ui && npm run build` | PASS |
| Manual: triage_conversation("我想加一辆车，然后这个 garaging proof 又是什么？", []) | summary has "Also asked: garaging/dec page meaning"; secondary_issue_note set |

**Limitations:** Single-turn triage_message (used by sim) does not build conversation_summary; sim checks category and draft. Handoff flow uses triage_conversation, which has full summary + secondary.

---

## 9. Deployment / Release Judgment

| Component | Changed | Redeploy needed |
|-----------|---------|------------------|
| Backend | triage.py, case_store.py | Yes, if backend redeployed |
| Frontend | UnifiedIntakePage.tsx, inboxTriage.ts | Yes, if frontend redeployed |
| Config | mixed_intent_scenarios.json (MI-AC5 added) | No |
| Docs | docs/sprints/MIXED_INTENT_SECONDARY_CASE_SPRINT/* | No |

**Founder can inspect now:** Yes — paste mixed-intent message in Unified Intake; see "Also asked" in summary and blue Tag.

---

## 10. Final Judgment

- **Biggest gain:** Broker visibility for mixed-intent — "Also asked: X" in summary and as Tag; secondary_issue_note persisted; 14/14 mixed-intent sim pass.
- **Biggest remaining weakness:** broker_next_step does not explicitly append secondary action; 3+ intents pick first secondary only.
- **Whether this meaningfully improves realistic conversation handling:** Yes. Broker can now see and act on secondary topics. Same-goal corrections stay in case. No case pollution.
- **Best next step:** Founder tests with real mixed messages; consider broker_next_step append for secondary in future sprint if brokers request it.

---

## 11. 中文宏观总结

**为什么现在做 mixed-intent：** 产品已有场景包、trial pack、scenario logic center，但客户常混多个目标（顺便问一下、另外、对了）。不处理则 case 摘要乱、broker 跟进难、trial 信心降。

**这轮主要做了什么：** 文档先行（Blueprint、Primary/Secondary Spec、Case Split、Broker Handoff、Acceptance、Founder Notes）；实现 `_detect_secondary_intent_hint`；conversation_summary 增加 "Also asked: X"；secondary_issue_note 持久化；UI 蓝色 Tag 展示；14 个 mixed-intent 场景全过。

**最大提升是什么：** Broker 可见 secondary — 摘要和 Tag 明确显示「客户还问了 X」；一 case 一主目标；same-goal 修正留在当前 case。

**还差什么：** broker_next_step 未追加 secondary 动作；3+ 意图只取第一个 secondary；自动拆 case 未做。

**下一步最该做什么：** 创始人用真实 mixed 消息测试；若 broker 需要，再考虑 broker_next_step 追加 secondary。

---

## 12. COPY/PASTE FOUNDER BLOCK

```
Mixed-Intent + Secondary Case Strategy Sprint — Founder Summary

Biggest improvement: Broker can now see when customer asked two things. 
conversation_summary includes "Also asked: X"; secondary_issue_note as blue Tag in workbench.
14/14 mixed-intent simulations pass (add-car+garaging, payment+doc, claim+notice, etc.).

Biggest remaining weakness: broker_next_step does not append "If customer also asked about X"; 
3+ intents pick first secondary only.

Redeploy needed: Backend (triage, case_store) and frontend (UnifiedIntakePage) if deploying.

What Andy should test next: Paste "我想加一辆车，然后这个 garaging proof 又是什么？" or 
"payment failed 怎么办，另外 dec page 我上周发过了" in Unified Intake; confirm blue Tag 
"Also asked: garaging/dec page meaning" or "Also asked: missing document" appears.
```

---

## 13. REQUIRED SHORT OVERVIEW

### 为什么做这件事
客户常混多个目标（顺便、另外、对了），不处理则 case 乱、broker 跟进难。需要第一版实用的 mixed-intent 策略。

### 主要用了什么方法/技术
文档先行；`_detect_secondary_intent_hint` 检测 2+ flow markers；conversation_summary 追加 "Also asked: X"；secondary_issue_note 持久化；UI Tag 展示；14 场景仿真验证。

### 这轮最大的提升
Broker 可见 secondary — 摘要和 Tag 明确显示客户还问了什么；一 case 一主目标；14/14 mixed-intent 过。

### 现在还差什么
broker_next_step 未追加 secondary；3+ 意图只取第一个；自动拆 case 未做。

---

*End of Mixed-Intent + Secondary Case Strategy Sprint Report*
