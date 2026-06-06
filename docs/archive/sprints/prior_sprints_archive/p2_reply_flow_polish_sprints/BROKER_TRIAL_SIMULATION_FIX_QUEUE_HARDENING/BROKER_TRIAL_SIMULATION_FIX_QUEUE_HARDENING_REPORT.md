# Broker Trial Simulation + Fix Queue Hardening Report

**Sprint:** Broker Trial Simulation + Fix Queue Hardening Sprint  
**Created:** 2026-03-19  
**Scope:** SearchForge → Chen Kui Insurance Unified Entry

---

## 1. Sprint Theme

- **What was chosen:** Run a stronger broker-style simulation round, identify remaining practical weaknesses, classify them into fix-now / fix-next / defer, and apply only 1–2 small high-value fixes justified by evidence.
- **Why now:** Product is near-trial-ready. Before real broker trial, the team needed one more cycle of simulate → observe → classify → harden. Founder away 1–2 hours; use time for maximum practical value.

---

## 2. Document Set Created

| Doc | Purpose |
|-----|---------|
| 01_BROKER_TRIAL_SIMULATION_BLUEPRINT.md | Why this sprint; what we strengthen; what we defer |
| 02_SIMULATION_PACK_SPEC.md | Realistic flow coverage; broker/customer behavior |
| 03_EVALUATION_CRITERIA_SPEC.md | Per-simulation judgment; classification |
| 04_FIX_QUEUE_HARDENING_SPEC.md | Fix now/next/defer; root-cause classes |
| 05_EXECUTION_OUTLINE.md | Workstreams; loop plan; validation |
| 06_ACCEPTANCE_TRIAL_HARDENING_CRITERIA.md | Pass criteria |
| 07_FOUNDER_INSPECTION_NOTES.md | What founder should inspect when back |

---

## 3. Baseline Audit

### Current Strongest Areas

| Area | Evidence |
|------|----------|
| Inbox triage | 64/64 scenarios pass |
| Multi-turn | 41/41 strong |
| Adversarial | 27/27 strong |
| Complex adversarial | 23/23 strong |
| Simulation Assistant | 27/27 pass |
| Follow-up append | 5/5 pass |
| Client-aware handoff | PASS |
| Client identity persistence | PASS |
| State/workflow backbone | PASS |

### Biggest Trial-Risk (Pre-Sprint)

From LAST_MILE_RISK_SPEC: **Talk to Agent awkward** — if "联系人工" routes wrong, trust-breaking. Mitigation: clear path; handoff-ready immediately.

### Biggest Broker Rework Source

**Correction/already_sent visibility** — broker may not see when customer said "already sent" or corrected. Mitigation: badge/chip; broker_next_step verify receipt.

### Biggest Trust-Breaking Product Moment

**Wrong next move** — broker_next_step vague ("Review and follow up") instead of operational. Mitigation: operational one-liner; concrete action verbs.

---

## 4. 10–20 Point Breakdown

1. **Flows in scope** — Cancellation, missing doc, add-car, premium, talk-to-agent, mixed-intent, correction, vague, already-sent, append
2. **Why those flows** — Highest commercial value; real office pain; trial pack top 5
3. **Short/vague coverage** — BS1 "帮我", BS2 "在吗" — both pass (no handoff turn 1)
4. **Correction-heavy** — BS8 "不是这个车"; LC-AC1, LC-N1, FA5 — all pass
5. **Already-sent / already-paid** — BS6, BS7, SIM9, SIM10, FA4 — all pass
6. **Mixed-intent** — Complex adversarial MI-* — all pass
7. **Talk-to-agent** — BS3, BS4, BS5, MT41 — all pass
8. **Broker append/reopen** — FA1–FA5; client identity persistence — pass
9. **Strong behavior** — Correct route; handoff when enough; broker_next_step concrete
10. **Weak behavior** — Generic first reply; wrong route; handoff turn 1 for vague
11. **Fix-now criteria** — Blocks trial or breaks trust
12. **Fix-next criteria** — High value; 1–2 sprints
13. **Defer criteria** — Lower priority; document for later
14. **Small fixes allowed** — Marker additions; single broker_next_step; one UI tweak
15. **Intentionally deferred** — Broad refactors; new scenario systems; inbox sync; OCR
16. **Founder test first** — Load founder demo queue; SIM1–SIM3; paste "联系人工"; append flow
17. **Trial trust impact** — Talk-to-agent; correction visibility; broker_next_step
18. **Next sprint feed** — Fix-next queue; observation log from real trial

---

## 5. Iteration Loop 1

### What Was Tested

- Guardrail full run (11 steps + new 8b)
- Multi-turn: 41 simulations
- Adversarial: 27
- Complex adversarial: 23
- Simulation Assistant: 27
- Follow-up append: 5
- **New:** Broker trial stress: 8 (vague, talk-to-agent, already-sent, correction)

### What Stayed Strong

- All existing packs: 100% pass
- Vague "帮我", "在吗" — no handoff turn 1 ✓
- Talk-to-agent "联系人工", "找陈奎" — customer_requested_human ✓
- Add-car → "联系人工" mid-flow — handoff at turn 2 ✓
- Already paid/sent — handoff with verify receipt ✓
- Correction "不是这个车" — handoff at turn 3 with correct vehicle ✓

### What Failed or Felt Weak

- **None** in automated simulations
- API append test fails when server not on 8001 (needs case_id) — environmental, not product

### Whether Loop 1 Was Worth It

**Yes.** Confirmed all existing packs pass; added broker stress pack; no new failures discovered.

---

## 6. Iteration Loop 2

### Root-Cause Patterns Identified

- **No observed failures** — All simulations pass
- **Documented risks** (from LAST_MILE_RISK_SPEC, Scenario Logic Center) remain theoretical:
  - Talk-to-agent: **mitigated** — tests pass
  - Correction visibility: **acceptable** — triage uses correction; UI badge optional
  - broker_next_step: **acceptable** — category_templates provide operational phrases

### What Entered Fix-Now

- **Empty** — No evidence of trust-breaking or trial-blocking behavior in simulations.

### What Entered Fix-Next

| Item | Layer | Notes |
|------|-------|-------|
| Correction badge visibility | UI/UX | When customer said "already sent" or corrected — broker may want explicit chip |
| Handoff thresholds in code | Scenario | triage.py; consider config extraction if client variation needed |
| Observation log template | Trial docs | Day-by-day; map to fix queue |

### What Was Deferred

- Simulation coverage counts in UI
- Last-changed timestamps in Scenario Logic Center
- Inbox sync; OCR; carrier API
- Broad refactors

### Whether Loop 2 Was Worth It

**Yes.** Clear fix-now (empty) / fix-next / defer; disciplined classification.

---

## 7. Iteration Loop 3

### Small Fixes Applied

1. **Broker trial stress pack + guardrail step**
   - Created `configs/broker_trial_stress_simulations.json` (8 flows)
   - Created `scripts/run_broker_trial_stress_simulations.py`
   - Added guardrail step [8b] in `scripts/guardrail_inbox_triage.sh`

### Why These Fixes Were Chosen

- **Evidence-based:** No product failures; the fix hardens **regression coverage** — future changes must not break vague, talk-to-agent, already-sent, correction flows.
- **Small, low-risk:** Config + script + one guardrail step; no triage logic change.
- **High-value:** Expands test surface for trial-critical behaviors.

### What Improved

- Guardrail now includes broker-style stress flows
- Future regressions in vague/talk-to-agent/already-sent/correction will be caught

### What Still Remained Weak

- Correction badge visibility (fix-next)
- Handoff thresholds in code (fix-next)
- Observation log template (fix-next)

### Whether Loop 3 Was Worth It

**Yes.** One small, justified hardening fix; no overreach.

---

## 8. Optional Loop 4

**Whether used:** No.

**Reason:** Loop 3 achieved the sprint goal. No clearly valuable, low-risk refinement remained. Stopping is correct.

---

## 9. Validation Summary

| Check | Result |
|-------|--------|
| `bash scripts/guardrail_inbox_triage.sh` | PASS |
| `run_multi_turn_simulations.py` | 41/41 strong |
| `run_simulation_assistant_scenarios.py` | 27/27 pass |
| `run_follow_up_append_simulations.py` | 5/5 pass |
| `run_broker_trial_stress_simulations.py` | 8/8 pass |
| `cd ui && npm run build` | Not run (frontend not touched) |

**Limitations:** API append test requires server on 8001 + case_id; skipped when server down.

---

## 10. Deployment / Release Judgment

| Component | Changed | Redeploy needed |
|-----------|---------|------------------|
| Backend | No | No |
| Frontend | No | No |
| Config | New broker_trial_stress_simulations.json | No (static) |
| Scripts | New run_broker_trial_stress_simulations.py; guardrail updated | No |

**Founder can inspect now:** Yes — run guardrail; run broker stress pack; Load founder demo queue on Vercel.

---

## 11. Founder Showcase

| Scenario | What happened | Why it matters | Broker impact | Priority |
|----------|---------------|----------------|---------------|----------|
| BS1 帮我 | No handoff turn 1; asks clarifying question | Vague messages common | Avoids premature handoff | Strong |
| BS3 联系人工 | customer_requested_human; handoff immediately | Trust-critical | Broker sees "Customer wants human" | Strong |
| BS5 Add-car → 联系人工 | Turn 2 escalates to talk_to_agent | Mid-flow switch | Handoff with context | Strong |
| BS7 都发过了怎么还要 | Handoff; verify receipt | Already-sent pain | broker_next_step: verify | Strong |
| BS8 不是这个车 | Correction used; handoff turn 3 | Correction common | Collected shows 2024 Tesla | Strong |

---

## 12. Final Judgment

- **Biggest gain:** Broker trial stress pack added to guardrail; 8 flows (vague, talk-to-agent, already-sent, correction) now regression-tested.
- **Biggest remaining weakness:** Correction badge visibility (fix-next); handoff thresholds in code (fix-next).
- **Whether product is safer for real broker trial:** Yes. Stronger simulation coverage; no new failures; disciplined fix queue.
- **Best next step:** Run real trial; use observation log; feed fix-next from real broker feedback.

---

## 13. Iteration Log

| Loop | What changed | Better vs prior | Did not improve | Worth it? | Next step |
|------|--------------|-----------------|-----------------|----------|-----------|
| 1 | Ran all simulations; added broker stress pack | 8 new flows tested | No failures to fix | Yes | Loop 2 |
| 2 | Root-cause; fix queue | fix-now/fix-next/defer clear | No product changes | Yes | Loop 3 |
| 3 | Broker stress + guardrail step | Regression coverage | Correction badge; thresholds | Yes | Stop |

---

## 14. 中文宏观总结

**为什么现在做这一轮：** 产品已近 trial-ready，但真实 broker trial 前需要一轮 simulate → observe → classify → harden，用创始人离开的 1–2 小时产出最大实用价值。

**主要用了什么方法/技术：** 文档先行（Blueprint、Simulation Pack、Evaluation、Fix Queue 等）；跑全量 guardrail + 新建 broker 压力包（8 条：模糊、联系人工、已发/已付、纠正）；根因分类 fix-now/fix-next/defer；小修复：broker 压力包加入 guardrail。

**这轮最大的发现：** 所有现有模拟包 + 新建 broker 压力包全部通过，无新失败。Talk-to-agent、vague、already-sent、correction 均表现良好。

**现在最该修什么：** fix-now 为空；fix-next：correction badge 可见性、handoff 阈值提取、observation log 模板。

**下一步最该做什么：** 跑真实 broker trial；用 observation log 收集反馈；将真实反馈纳入 fix-next。

---

## 15. COPY/PASTE FOUNDER BLOCK

```
Broker Trial Simulation + Fix Queue Hardening Sprint — Founder Summary

Biggest simulation finding: All packs pass (64 inbox + 41 multi-turn + 27 adversarial + 23 complex + 27 sim assistant + 5 append + 8 new broker stress). No failures. Talk-to-agent, vague, already-sent, correction all strong.

Biggest remaining weakness: Correction badge visibility (fix-next); handoff thresholds in code (fix-next).

Makes product safer for real trial: Yes. Broker stress pack (8 flows) added to guardrail; regression coverage expanded.

Redeploy needed: No. Backend/frontend unchanged.

What Andy should inspect/test first when back: (1) bash scripts/guardrail_inbox_triage.sh — should PASS. (2) Load founder demo queue on Vercel; run SIM1–SIM3. (3) Paste "联系人工" — verify routes to talk_to_agent. (4) Append flow — add message to existing case.
```

---

## 16. REQUIRED SHORT OVERVIEW

### 为什么做这件事
产品已近 trial-ready，真实 broker trial 前需要一轮 simulate → classify → harden，产出最大实用价值。

### 主要用了什么方法/技术
文档先行；全量 guardrail + 新建 broker 压力包（8 条）；根因分类；broker 压力包加入 guardrail。

### 这轮最大的发现
所有模拟包通过，无新失败。Talk-to-agent、vague、already-sent、correction 均强。

### 现在最该修什么
fix-now 为空；fix-next：correction badge、handoff 阈值、observation log。

---

## 17. REQUIRED MACRO PRINT BLOCK

```
MACRO PROJECT SUMMARY — SearchForge Chen Kui Insurance Unified Entry

1. Current product readiness
   Trial-ready. Guardrail PASS. 64 inbox + 41 multi-turn + 27 adversarial + 23 complex + 27 sim assistant + 5 append + 8 broker stress — all pass.

2. Strongest modules
   Inbox triage; multi-turn; adversarial; talk-to-agent; vague handling; already-sent; correction; append; client-aware handoff; Scenario Logic Center.

3. Weakest modules
   Correction badge visibility (UI); handoff thresholds in code; observation log template.

4. Current fix-now / fix-next / defer snapshot
   Fix-now: empty (no observed failures)
   Fix-next: correction badge; handoff thresholds to config; observation log
   Defer: simulation counts in UI; inbox sync; OCR; carrier API

5. Next best step
   Run real broker trial; use observation log; feed fix-next from real broker feedback.
```

---

## 18. REQUIRED CROSS-WINDOW SUMMARY

```
Broker Trial Simulation + Fix Queue Hardening Sprint — Cross-Window Evaluator Block

What was simulated: Full guardrail (64 inbox, 41 multi-turn, 27 adversarial, 23 complex, 27 sim assistant, 5 append) + new broker stress pack (8 flows: vague 帮我/在吗, talk-to-agent 联系人工/找陈奎, add-car→联系人工 mid-flow, already paid/sent, correction 不是这个车).

What stayed strong: All packs pass. Talk-to-agent, vague, already-sent, correction, append all behave correctly.

What remained weak: No simulation failures. Documented fix-next: correction badge visibility, handoff thresholds in code, observation log template.

Hardened fix queue: Fix-now empty. Fix-next: correction badge, handoff thresholds, observation log. Defer: simulation counts, inbox sync, OCR.

Direction correct: Yes. Disciplined; no overreach; one small hardening fix (broker stress + guardrail).

Current IT technical backbone: FastAPI backend (8001); React + Ant Design frontend; Vite; configs (common, industries/insurance, clients/chen_kui); triage.py; case_store; Qdrant for RAG. Guardrail includes new step [8b] broker trial stress.
```

---

*End of Report*
