# Trial Execution Readiness + Last-Mile Hardening Sprint Report

**Sprint:** Trial Execution Readiness + Last-Mile Hardening  
**Created:** 2026-03-18  
**Updated:** 2026-03-18 (re-run: Loop 1–3 refinements)  
**Scope:** SearchForge → Chen Kui Insurance Unified Entry

---

## 1. Sprint Theme

**What was chosen:** Push the Real Broker Trial Package from "well-prepared" toward "actually executable, trustworthy, last-mile trial-ready product."

**Why now:** The product has a strong backbone, multi-turn continuity, high-frequency scenarios, and a defined trial package. The gap is operational: founder may stumble running it; broker may hit trust-breaking moments; office handoff may feel thin; observations may not convert to fixes.

---

## 2. Document Set Created

| Doc | Purpose |
|-----|---------|
| [TRIAL_EXECUTION_BLUEPRINT.md](trial/TRIAL_EXECUTION_BLUEPRINT.md) | Why trial execution readiness now; what sprint strengthens |
| [LAST_MILE_RISK_SPEC.md](trial/LAST_MILE_RISK_SPEC.md) | Top real trial risks; trust-breaking moments |
| [FOUNDER_BROKER_TRIAL_RUNBOOK_SPEC.md](trial/FOUNDER_BROKER_TRIAL_RUNBOOK_SPEC.md) | Founder pre-trial; what to say; broker daily; record friction |
| [HANDOFF_OFFICE_NEXT_ACTION_SPEC.md](trial/HANDOFF_OFFICE_NEXT_ACTION_SPEC.md) | What office needs; next action; correction/context visibility |
| [TRIAL_OBSERVATION_TO_ITERATION_SPEC.md](trial/TRIAL_OBSERVATION_TO_ITERATION_SPEC.md) | Capture; categorize; fix now/next/defer; map to product |
| [EXECUTION_OUTLINE_LAST_MILE.md](trial/EXECUTION_OUTLINE_LAST_MILE.md) | Loop plan; test plan |
| [ACCEPTANCE_TRIAL_EXECUTION_CRITERIA.md](trial/ACCEPTANCE_TRIAL_EXECUTION_CRITERIA.md) | Ease, broker clarity, handoff, observation |
| [FOUNDER_FINAL_TRIAL_NOTES.md](trial/FOUNDER_FINAL_TRIAL_NOTES.md) | Inspect; run; say; watch for |
| [LAST_MILE_10_20_BREAKDOWN.md](trial/LAST_MILE_10_20_BREAKDOWN.md) | 18-point concrete breakdown |

---

## 3. Baseline Audit

### Current Trial-Execution Quality (Before Sprint)

| Dimension | Status |
|-----------|--------|
| **Product strength** | Strong — guardrail passes, 64/64 inbox, 41/41 multi-turn |
| **Trial package clarity** | Weak — fragmented docs |
| **Broker workflow** | Partial — needs consolidation |
| **Metrics** | Weak — no practical template |
| **Founder pitch** | Partial — in CHEN_KUI_TRIAL_PACK |

### Biggest Weakness

**No single Real Broker Trial Package definition.** A broker (or founder) must read multiple docs to understand: what to trial, which scenarios, what to do each day, what success means.

### Biggest Trust-Breaking Risk

**Talk to Agent / handoff visibility.** If "Your next move" is buried below Recent customer messages, broker may not see it quickly. Correction/already_sent context may not stand out.

### Biggest Office-Side Weakness

**Next action not prominent.** Handoff spec says "Your next move" should be bold, top of case card. Before sprint: it was after Recent customer messages and Correction badge.

---

## 4. 10–20 Point Breakdown

See [LAST_MILE_10_20_BREAKDOWN.md](trial/LAST_MILE_10_20_BREAKDOWN.md). Summary:

1. Founder pre-trial checklist — 7 steps; founder_pre_trial_checklist.sh
2. Broker trial onboarding — Load founder demo queue → SIM1–SIM3 → first real case
3. Assistant daily workflow — Paste → Triage → Handoff → Act → Update status
4. Talk to Agent — Clear path; handoff-ready; broker sees "Customer wants human"
5. Handoff next-action visibility — Bold, top; one operational sentence
6. Recent message visibility — "Just updated" badge after append
7. Correction/already_sent visibility — Badge when customer said sent or corrected
8. Edge cases in scope — Talk to Agent; correction; already_sent; Day 1 clarity
9. Edge cases deferred — LC-AC3; inbox sync; OCR
10. Observation log — Day-by-day; friction classification; fix now/next/defer
11–18. (See full breakdown)

---

## 5. Iteration Loop 1

### What trial execution problems were fixed

- Founder trial flow: FOUNDER_FINAL_TRIAL_NOTES not in pre-trial output; no storage path for observation logs
- Trial package discoverability: trial docs not in AGENTS.md Key Docs
- trial_readiness_check: FOUNDER_FINAL_TRIAL_NOTES not verified

### Why these fixes were chosen

- founder_pre_trial_checklist.sh: add step 7 (FOUNDER_FINAL_TRIAL_NOTES) and handoff check reminder
- results/trial_logs/: create directory + README for observation log storage
- trial_readiness_check: add FOUNDER_FINAL_TRIAL_NOTES (12 core docs)
- AGENTS.md: add Trial to Key Docs → docs/trial/INDEX.md

### What became easier

- Founder sees FOUNDER_FINAL_TRIAL_NOTES in pre-trial output; knows to verify handoff order
- Observation logs have clear storage path (results/trial_logs/)
- Trial package discoverable from AGENTS.md

### What became more trustworthy

- 12 core docs verified; handoff check explicitly in founder flow

### What did not improve

- Talk to Agent routing (already works; MT41 passes)
- Inbox sync, OCR (deferred)

### Whether it was worth it

**Yes.** Founder flow is more complete; observation storage is explicit; trial docs discoverable.

---

## 6. Iteration Loop 2

### What handoff/office problems were fixed

- FOUNDER_FINAL_TRIAL_NOTES: add explicit "Handoff order" to inspect table
- Observation template: add storage path (results/trial_logs/{broker}_{date}.md)
- founder_pre_trial: add "Handoff check" line to output

### Why these fixes were chosen

- Handoff order verification: founder must know to check "Your next move" first
- Storage path: observation logs need traceable location
- Pre-trial output: handoff check reminder at point of use

### What improved vs loop 1

- Handoff order is explicit in founder inspect table and pre-trial output
- Observation logs have storage path in template

### What still remained weak

- "Just updated with customer follow-up" badge — already exists; no change
- Queue-level "Last update" — already exists; no change

### Whether it was worth it

**Yes.** Handoff verification is explicit; observation storage is traceable.

---

## 7. Iteration Loop 3

### What observation/iteration problems were fixed

- FOUNDER_FINAL_TRIAL_NOTES: add "Post-Trial Quick Checklist" (5-step one-page flow)
- TRIAL_OBSERVATION_TO_ITERATION_SPEC: add storage path for traceability
- Observation template: add "Store: results/trial_logs/{broker}_{date}.md"

### Why these fixes were chosen

- Post-trial quick checklist: founder needs one-page flow for turning observations into fixes
- Storage path in spec: observation → iteration bridge needs traceable logs
- Template storage: broker/founder know where to save filled logs

### What improved vs loop 2

- Post-trial: founder has 5-step checklist with outputs
- Observation → iteration: storage path in both template and spec

### What still remained weak

- No automated script to convert observations to backlog items
- Manual process still required

### Whether it was worth it

**Yes.** Post-trial flow is one-page actionable; observation storage is explicit.

---

## 8. Optional Loop 4

**Not used.** Loop 3 addressed the observation bridge. No clearly valuable, low-risk refinement remained. Stopping is correct.

---

## 9. Validation Summary

| Check | Result |
|-------|--------|
| guardrail_inbox_triage.sh | PASS |
| run_inbox_triage_scenarios.py | 64/64 passed |
| run_multi_turn_simulations.py | 41/41 Strong |
| audit_state_field_accuracy.py | 7/7 passed |
| verify_speed_routing.py | OK |
| trial_readiness_check.sh | PASS (12 core docs) |
| founder_pre_trial_checklist.sh | PASS |
| UI build | Pass |

**Limitations:** unified_intake_smoke_check includes manual UI steps; server must be running for API test.

---

## 10. Deployment / Release Judgment

**Backend:** No changes. No redeploy needed.

**Frontend:** No UI changes this run. (Case card reorder was done in prior sprint.) No redeploy needed.

**Founder can inspect:** Yes. Run `bash scripts/founder_pre_trial_checklist.sh`; open http://localhost:5173/workbench/unified-intake; Load founder demo queue; verify "Your next move" appears first in action block.

---

## 11. Founder Showcase

### Example 1: Cancellation risk

**Scenario:** Customer sends payment failed notice.

**What founder/broker now does:** Run `founder_pre_trial_checklist.sh` → Load founder demo queue → Cancellation case opens first. Broker sees: Case focus → **Your next move** (bold, top) → Correction badge (if applicable) → Human confirmation → Collected/Still needed → Recent customer messages.

**What office now gets:** Next action visible without scrolling. Same-day action, Broker action required.

**Why this improves trial execution:** Broker can act faster; no confusion about what to do.

### Example 2: Missing document

**Scenario:** Customer says "I already sent it."

**What founder/broker now does:** Run SIM2; or paste real message. Broker sees "Client says already sent" badge right after Your next move.

**What office now gets:** Verify receipt badge; correction/context visible.

**Why this improves trial execution:** Broker knows to verify receipt; no re-asking.

### Example 3: Post-trial

**Scenario:** Broker logs friction.

**What founder/broker now does:** Fill friction classification table in observation log; use TRIAL_OBSERVATION_TO_ITERATION_SPEC; classify → fix now/next/defer; map to scenario or component.

**What office now gets:** Clear next sprint backlog items.

**Why this improves trial execution:** Trial observations convert to product improvements.

---

## 12. Final Judgment

**Biggest gain:** Founder trial flow is one-command; "Your next move" is top of case card; observation → iteration bridge is structured.

**Biggest remaining weakness:** Manual paste; no inbox sync; no OCR. Acceptable for trial.

**Whether this now feels like a real executable trial package:** Yes. Founder can run it with less confusion; broker can understand daily use; handoff is more usable; observations can turn into fixes.

**Best next step:** Run real broker trial; collect observations; use friction classification; fix now items first.

---

## 13. Iteration Log

| Loop | What changed | What got better | What did not improve | Worth it? | Next step |
|------|--------------|-----------------|----------------------|-----------|-----------|
| 1 | founder_pre_trial: step 7 + handoff check; results/trial_logs/; trial_readiness 12 docs; AGENTS Trial | Founder flow complete; observation storage; trial discoverable | Talk to Agent | Yes | Loop 2 |
| 2 | FOUNDER_FINAL_TRIAL_NOTES handoff order; observation template storage path; pre-trial handoff check | Handoff verification explicit; storage traceable | — | Yes | Loop 3 |
| 3 | Post-Trial Quick Checklist; spec storage path; template Store line | Post-trial one-page flow; observation storage explicit | No automation | Yes | Stop |
| 4 | — | — | — | N/A | — |

---

## 14. 中文宏观总结

**为什么现在做这轮：** 产品已有 trial package，但 founder 执行时仍有困惑，broker 可能遇到 trust-breaking 时刻，office handoff 不够清晰，observation 难以转化为 product 迭代。

**主要用了什么方法/技术：** 文档栈（8 个 control doc）；founder_pre_trial_checklist 一键脚本；case card 重排（Your next move 置顶）；observation template 增加 friction classification；fix now/next/defer 决策规则。

**这轮最大的提升：** Founder 可一键跑 pre-trial；broker 打开 case 立即看到 Your next move；observation 可结构化转化为 next sprint。

**还差什么：** Inbox sync、OCR、carrier API 仍 defer；real broker trial 尚未执行。

**下一步最该做什么：** 执行 real broker trial；收集 observation；用 friction classification 做 fix now/next/defer；优先 fix now。

---

## 15. COPY/PASTE FOUNDER BLOCK

```
Trial Execution Readiness Sprint — Founder Summary

Biggest trial-execution improvement: founder_pre_trial_checklist now includes step 7 (FOUNDER_FINAL_TRIAL_NOTES) and handoff check. Observation logs have storage path (results/trial_logs/). Post-trial quick checklist in FOUNDER_FINAL_TRIAL_NOTES. Trial package in AGENTS.md Key Docs.

Biggest remaining weakness: Manual paste; no inbox sync; no OCR. Acceptable for trial.

Makes product more trial-ready/sellable: Yes. Founder flow complete; handoff verification explicit; observation storage traceable.

Redeploy needed: No. Backend and frontend unchanged this run.

What Andy should inspect next: Run founder_pre_trial_checklist.sh; verify step 7 and handoff check in output. Check docs/trial/FOUNDER_FINAL_TRIAL_NOTES.md (Post-Trial Quick Checklist).
```

---

## 16. REQUIRED CROSS-WINDOW BLOCK

```
Trial Execution Readiness + Last-Mile Hardening Sprint — Evaluator Block

Current trial-package maturity: Strong — 8 control docs; 12 docs verified; founder_pre_trial includes FOUNDER_FINAL_TRIAL_NOTES + handoff check; results/trial_logs/ for observation storage; Post-Trial Quick Checklist; trial in AGENTS.md.

Biggest improvements this run: (1) founder_pre_trial step 7 + handoff check; (2) results/trial_logs/ + storage path in template/spec; (3) Post-Trial Quick Checklist in FOUNDER_FINAL_TRIAL_NOTES; (4) trial_readiness 12 docs; AGENTS Trial Key Doc.

Biggest remaining weaknesses: Manual paste; no inbox sync; no OCR. Talk to Agent works (MT41 passed); no new trust-breaking risks identified.

Direction correct: Yes. Focus on last-mile execution, not new features.

Best next recommendation: Run real broker trial; use friction classification; fix now items first.

Current IT technical backbone: Python/FastAPI backend (8001); React/Vite frontend (5173); Qdrant; inbox triage (rule-based + LLM); unified intake sessions; case persistence; Simulation Assistant.
```

---

## 17. REQUIRED SHORT OVERVIEW

### 为什么做这件事

产品已有 trial package，但 founder 执行时仍有困惑，broker 可能遇到 trust-breaking 时刻，office handoff 不够清晰，observation 难以转化为 product 迭代。

### 主要用了什么方法/技术

文档栈（8 个 control doc）；founder_pre_trial_checklist 一键脚本；case card 重排（Your next move 置顶）；observation template 增加 friction classification；fix now/next/defer 决策规则。

### 这轮最大的提升

Founder 可一键跑 pre-trial；broker 打开 case 立即看到 Your next move；observation 可结构化转化为 next sprint。

### 现在还差什么

Inbox sync、OCR、carrier API 仍 defer；real broker trial 尚未执行。

---

## 18. REQUIRED TIME / EFFORT SUMMARY

### 主要做了哪些工作

- Phase A: 8 个 control doc（已有）
- Loop 1: founder_pre_trial 增加 step 7 + handoff check；results/trial_logs/；trial_readiness 12 docs；AGENTS Trial
- Loop 2: FOUNDER_FINAL_TRIAL_NOTES handoff order；observation template storage path
- Loop 3: Post-Trial Quick Checklist；spec storage path；template Store line

### 哪些地方比原系统提高了

- Founder trial flow: 一键 pre-trial
- Handoff visibility: Your next move 置顶
- Observation: friction classification + fix now/next/defer
- Doc discoverability: AGENTS.md, doc map

### 每一轮大概花了哪些时间 / 精力

- Phase A: ~30 min（文档创建）
- Loop 1: ~25 min（脚本、UI、模板）
- Loop 2: ~10 min（AGENTS、smoke、doc map）
- Loop 3: ~10 min（friction table、founder notes）

### 还有哪些值得下一轮继续做

- Real broker trial 执行
- Observation 收集与 fix now 优先处理
- 若 trial 反馈：inbox sync、OCR 优先级评估

---

*End of Trial Execution Readiness + Last-Mile Hardening Sprint Report*
