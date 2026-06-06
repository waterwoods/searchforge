# Realistic Conversation Simulation + Fix-Now Report

**Sprint:** Realistic Conversation Simulation + Fix-Now Sprint  
**Scope:** SearchForge → Chen Kui Insurance Unified Entry  
**Date:** 2026-03-18

---

## 1. Sprint Theme

- **What was chosen:** Stress-test the product with 20 realistic customer conversations (shorthand, emotional, correction-heavy, Talk to Agent, mixed intent) before real broker trial.
- **Why now:** Product has stronger UI, backbone, scenario package. Founder needs reality check: will it hold up under messy, varied, real-world conversations?

---

## 2. Document Set Created

| Doc | Path |
|-----|------|
| Simulation Sprint Blueprint | `docs/sprints/REALISTIC_CONVERSATION_SIMULATION_SPRINT/01_SIMULATION_SPRINT_BLUEPRINT.md` |
| Realistic Conversation Pack Spec | `02_REALISTIC_CONVERSATION_PACK_SPEC.md` |
| Evaluation Criteria Spec | `03_EVALUATION_CRITERIA_SPEC.md` |
| Fix-Now Queue Spec | `04_FIX_NOW_QUEUE_SPEC.md` |
| Execution Outline | `05_EXECUTION_OUTLINE.md` |
| Acceptance / Simulation Criteria | `06_ACCEPTANCE_SIMULATION_CRITERIA.md` |
| Founder Inspection Notes | `07_FOUNDER_INSPECTION_NOTES.md` |

---

## 3. Baseline Audit

### Current Strengths

- **64/64** inbox triage scenarios pass
- **41/41** multi-turn simulations strong
- **27/27** adversarial real-user strong
- **23/23** complex adversarial (mixed-intent + long-context) strong
- Add-car, premium review, claim, payment, missing doc, Talk to Agent (联系人工) all well-covered
- Handoff timing, correction handling, already-sent context preserved in most flows

### Biggest Simulation Risk (Before Sprint)

- Ultra-short Talk to Agent ("找陈奎") not in markers → unclear
- Emotional cancellation ("急死了 保单要停了") with policy_stop but no notice/question → unclear

### Biggest Likely Trust-Breaking Moment

- Customer says "找陈奎" and gets generic "这段内容还不够完整" → feels broken
- Customer says "急死了 保单要停了" and gets unclear → same-day action missed

### Biggest Likely Broker Rework Source

- Misclassified cancellation risk → broker doesn't prioritize same-day

---

## 4. 10–20 Point Breakdown

| # | Point |
|---|-------|
| 1 | **20 scenarios** in realistic pack (15 single-turn, 5 multi-turn) |
| 2 | **Top flows:** add-car, material/already-sent, payment, renewal, remove-car, claim, Talk to Agent, mixed-intent |
| 3 | **Shorthand/vague:** x5 多少钱, 加车 90210 下周拿, 续保太贵 有办法吗 |
| 4 | **Correction-heavy:** 不是这个 2024 Model Y, 又发了一次 微信 |
| 5 | **Already-sent/paid:** 我付了呀, 都发过了怎么还要, dec page 上周就发了 |
| 6 | **Mixed-intent:** 加车顺便notice什么意思 |
| 7 | **Talk to Agent mid-flow:** 算了 联系人工吧 |
| 8 | **Emotional:** 急死了 保单要停了 |
| 9 | **Good behavior:** Intent-specific reply, no generic fallback, correct urgency |
| 10 | **Bad behavior:** "这段内容还不够完整", wrong category, wrong urgency |
| 11 | **Fix-now:** Direct broker/customer impact, trust loss, same-day missed |
| 12 | **Fix-next:** Friction with workaround |
| 13 | **Defer:** Rare edge, broad refactor |
| 14 | **Small fixes allowed:** Marker addition, single rule addition |
| 15 | **Out of scope:** Broad platform, new features |
| 16 | **Results:** Pass/weak per scenario, failure list for fix-now |
| 17 | **Trial:** Stronger confidence, clearer fix-now queue |
| 18 | **Next sprint:** Fix-next items, secondary intent in mixed-intent |

---

## 5. Iteration Loop 1

**What was tested:** 20 realistic conversations (15 single-turn, 5 multi-turn) covering shorthand, emotional, Talk to Agent, correction, already-sent, mixed-intent.

**What stayed strong:** 18/20 — add-car shorthand, payment clarification, missing doc, claim, premium review, remove-car, billing clarification, document confusion, Talk to Agent (联系人工), last notice, multi-turn flows.

**What failed or felt weak:** 2/20
- **RC-S5 "找陈奎"** — category unclear, draft generic
- **RC-S6 "急死了 保单要停了"** — category unclear, urgency medium (expected critical)

**What did not improve:** N/A (first loop)

**Whether it was worth it:** Yes. Exposed 2 high-value gaps before trial.

---

## 6. Iteration Loop 2

**Root-cause patterns:**
1. **Marker coverage too narrow:** "找陈奎" not in talk_to_agent markers
2. **Classification rule gap:** policy_stop alone (no notice, no question) fell through to unclear

**Fix-now:** RC-S5, RC-S6 (both addressed in Loop 3)

**Fix-next:** Secondary intent in mixed-intent (RC-S7 "加车顺便notice什么意思" — draft asks add-car only, not notice); acceptable for now.

**Deferred:** Broad LLM fallback, multi-intent splitting.

**Whether it was worth it:** Yes. Clear root causes, actionable fix-now.

---

## 7. Iteration Loop 3

**Small fixes applied:**
1. **"找陈奎"** — Added to `configs/industries/insurance/markers.json` talk_to_agent and triage fallback
2. **policy_stop alone** — Added rule in `triage.py`: when `has_policy_stop_marker` (and not already handled by policy_stop+notice+question) → `cancellation_warning`, `critical`

**Why chosen:** Direct evidence from RC-S5, RC-S6; small, low-risk, high-value.

**What improved:** 20/20 realistic pack strong; RC-S5, RC-S6 now pass.

**What still weak:** RC-S7 mixed-intent — draft addresses add-car only, not notice. Fix-next.

**Whether it was worth it:** Yes. Removed 2 embarrassing failures.

---

## 8. Optional Loop 4

**Used:** No. No clearly valuable, low-risk refinement remained. RC-S7 secondary intent is fix-next, not fix-now.

---

## 9. Validation Summary

| Check | Result |
|-------|--------|
| run_inbox_triage_scenarios.py | 64/64 passed |
| run_multi_turn_simulations.py | 41/41 strong |
| run_adversarial_simulation.py | 27/27 strong |
| run_complex_adversarial_simulation.py | 23/23 strong |
| run_realistic_conversation_pack.py | 20/20 strong |
| guardrail_inbox_triage.sh | PASS |

**Limitations:** Realistic pack is rule-based only (LLM_GENERATION_ENABLED=0). API test skipped (no server on 8001).

---

## 10. Deployment / Release Judgment

- **Backend changed:** Yes (triage.py, markers.json)
- **Backend redeploy needed:** Yes (Cloud Run)
- **Frontend changed:** No
- **Frontend redeploy needed:** No
- **Founder can inspect:** Yes — run `PYTHONPATH=. python3 scripts/run_realistic_conversation_pack.py`

---

## 11. Founder Showcase

### RC-S5 "找陈奎" (Fixed)

| Item | Content |
|------|---------|
| **Scenario** | Customer says "找陈奎" (find Chen Kui) — ultra-short Talk to Agent |
| **What happened** | Before: unclear, generic "这段内容还不够完整". After: customer_requested_human, "好的，已帮您转给陈奎办公室" |
| **Why it matters** | Real customers type this; misclassification feels broken |
| **Broker impact** | Before: broker never gets case. After: handoff correct |
| **Priority** | Fix-now (done) |

### RC-S6 "急死了 保单要停了" (Fixed)

| Item | Content |
|------|---------|
| **Scenario** | Customer says "急死了 保单要停了" (so anxious, policy going to cancel) |
| **What happened** | Before: unclear, medium. After: cancellation_warning, critical |
| **Why it matters** | Same-day action required; wrong urgency = missed deadline |
| **Broker impact** | Before: case buried. After: surfaced as critical |
| **Priority** | Fix-now (done) |

### RC-S7 "加车顺便notice什么意思" (Fix-Next)

| Item | Content |
|------|---------|
| **Scenario** | Mixed intent: add-car + notice confusion |
| **What happened** | Draft asks for add-car only; notice question not addressed |
| **Why it matters** | Customer asked 2 things; only 1 answered |
| **Broker impact** | Broker may need to ask about notice separately |
| **Priority** | Fix-next |

---

## 12. Final Judgment

- **Biggest gain:** 2 high-value fixes applied; realistic pack 20/20; product safer for trial
- **Biggest remaining weakness:** Mixed-intent secondary intent not fully addressed (fix-next)
- **Safer for real trial:** Yes
- **Best next step:** Redeploy backend; run realistic pack in pre-trial checklist

---

## 13. Iteration Log

| Loop | What changed | Better vs prior | Not improved | Worth it? | Next step |
|------|--------------|-----------------|--------------|-----------|-----------|
| 1 | Built + ran realistic pack | Identified 2 failures | RC-S5, RC-S6 | Yes | Root-cause |
| 2 | Root-cause, fix-now queue | Clear priorities | — | Yes | Apply fixes |
| 3 | 2 small fixes | 20/20 strong | RC-S7 secondary | Yes | Stop |
| 4 | — | — | — | N/A | Not used |

---

## 14. 中文宏观总结

- **为什么现在做这个仿真压测：** 产品已有较强UI和场景包，但缺少对真实、杂乱、口语化对话的压测；创始人需要在真实经纪人试用前做一次现实检验。
- **主要方法/技术：** 新建20条真实对话包（简写、情绪、已发/已付、纠正、联系人工、混合意图），用 `run_realistic_conversation_pack.py` 跑规则引擎，发现2处失败，根因分析后做2个小修复。
- **这轮最大的发现：** "找陈奎" 未被识别为联系人工；"急死了 保单要停了" 未被识别为取消风险。两处均为标记/规则覆盖不足。
- **现在最该修什么：** 已修。混合意图的次要意图（如加车+notice）为 fix-next。
- **下一步最该做什么：** 后端重新部署；将 realistic pack 加入 trial 前检查脚本。

---

## 15. COPY/PASTE FOUNDER BLOCK

**Biggest simulation finding:** 2 failures — "找陈奎" (Talk to Agent) and "急死了 保单要停了" (cancellation risk) both got unclear. Root cause: marker/rule gaps.

**Biggest remaining weakness:** Mixed-intent secondary intent (e.g. add-car + notice) — draft addresses primary only. Fix-next.

**Safer for real trial:** Yes. 2 fixes applied; 20/20 realistic pack pass.

**Redeploy needed:** Backend yes (triage + markers). Frontend no.

**Andy should inspect:** Run `PYTHONPATH=. python3 scripts/run_realistic_conversation_pack.py`; verify RC-S5, RC-S6 pass; redeploy backend.

---

## 16. REQUIRED CROSS-WINDOW BLOCK

**Trial-safety maturity:** Improved. Realistic pack 20/20; 2 fix-now items resolved.

**Strengths:** Add-car, payment, missing doc, claim, premium, Talk to Agent (联系人工, 找陈奎), cancellation (policy_stop alone), multi-turn, correction, already-sent.

**Weaknesses:** Mixed-intent secondary intent not fully addressed (fix-next).

**Fix-now queue:** Empty (all addressed). Fix-next: secondary intent in mixed-intent.

**Direction correct:** Yes.

**Best recommendation:** Redeploy backend; add `run_realistic_conversation_pack.py` to trial_readiness_check or founder_pre_trial_checklist.

**Technical backbone:** Python triage (services/fiqa_api/inbox_triage/triage.py), configs/industries/insurance/markers.json, configs/inbox_triage_scenarios.json, configs/realistic_conversation_simulation_pack.json. Rule-based + optional LLM.

---

## 17. REQUIRED SHORT OVERVIEW

### 为什么做这件事

产品已有较强基础，但缺少对真实、杂乱、口语化对话的压测。在真实经纪人试用前，需要做一次现实检验，找出并修复最明显的弱项。

### 主要用了什么方法/技术

新建20条真实对话包（简写、情绪、已发/已付、纠正、联系人工、混合意图），用新脚本 `run_realistic_conversation_pack.py` 跑规则引擎，发现2处失败，根因分析后做2个小修复（标记+规则）。

### 这轮最大的发现

"找陈奎" 和 "急死了 保单要停了" 未被正确分类，根因是标记/规则覆盖不足。修复后20/20通过。

### 现在最该修什么

已修。混合意图的次要意图为 fix-next，可后续迭代。

---

*End of Report*
