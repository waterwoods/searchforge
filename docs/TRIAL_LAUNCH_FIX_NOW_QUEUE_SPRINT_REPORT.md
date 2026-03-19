# Trial Launch + Fix-Now Queue Sprint Report

**Sprint:** Trial Launch + Fix-Now Queue Sprint  
**Created:** 2026-03-18  
**Target:** 45–75 min; launch-ready state for real 1-week broker trial

---

## 1. Sprint Theme

- **What was chosen:** Push the trial package from "trial-ready in theory" to "launch-ready in practice" — single launch entry, evidence capture, fix-now queue, and one small product friction reduction.
- **Why now:** Trial package and execution docs exist; the remaining gap is founder confusion at launch and weak post-trial iteration path.

---

## 2. Document Set Created

| Doc | Purpose |
|-----|---------|
| [TRIAL_LAUNCH_BLUEPRINT.md](trial/TRIAL_LAUNCH_BLUEPRINT.md) | Why launch-readiness now; what this sprint strengthens |
| [TRIAL_LAUNCH_CHECKLIST_SPEC.md](trial/TRIAL_LAUNCH_CHECKLIST_SPEC.md) | Founder/broker checklist; ready to launch; blockers |
| [TRIAL_EVIDENCE_PACK_SPEC.md](trial/TRIAL_EVIDENCE_PACK_SPEC.md) | Evidence types; metrics; screenshots; useful packet |
| [FIX_NOW_QUEUE_SPEC.md](trial/FIX_NOW_QUEUE_SPEC.md) | Fix now/next/defer; group by layer; post-trial sprint |
| [FIX_NOW_QUEUE_TEMPLATE.md](trial/FIX_NOW_QUEUE_TEMPLATE.md) | Post-trial queue template — copy and fill |
| [SMALL_FRICTION_REDUCTION_SPEC.md](trial/SMALL_FRICTION_REDUCTION_SPEC.md) | 1–2 small product improvements |
| [TRIAL_LAUNCH_EXECUTION_OUTLINE.md](trial/TRIAL_LAUNCH_EXECUTION_OUTLINE.md) | Workstreams; loop plan |
| [ACCEPTANCE_LAUNCH_CRITERIA.md](trial/ACCEPTANCE_LAUNCH_CRITERIA.md) | Launch criteria; acceptable to defer |
| [FOUNDER_LAUNCH_NOTES.md](trial/FOUNDER_LAUNCH_NOTES.md) | Single entry: what to do, say, inspect, collect |
| [EVIDENCE_PACK_TEMPLATE.md](trial/EVIDENCE_PACK_TEMPLATE.md) | Post-trial evidence pack template |

---

## 3. Baseline Audit

| Dimension | Status |
|----------|--------|
| **Product strength** | Strong — guardrail passes, scenarios coherent |
| **Trial package clarity** | Weak — fragmented docs; no single entry |
| **Broker workflow** | Partial — BROKER_TRIAL_ONE_PAGER exists |
| **Metrics / evidence** | Weak — template exists but no fix-now queue structure |
| **Post-trial iteration** | Weak — spec exists but no ready-made queue template |

**Biggest blocker:** No single "launch trial now" entry point.  
**Biggest evidence weakness:** No structured fix-now queue for post-trial sprint planning.  
**Biggest iteration gap:** Observations don't map cleanly to fix now/next/defer with a fillable template.

---

## 4. 10–20 Point Breakdown

1. **Founder launch checklist** — 7 steps; `trial_launch_check.sh` prints it
2. **Broker onboarding steps** — BROKER_TRIAL_ONE_PAGER; Day 1: Load founder demo queue → SIM1–SIM3 → paste real message
3. **Assistant/workbench day-1 checks** — Case focus, Your next move, Collected/Still needed, Human confirmation, Resume here
4. **Evidence types to capture** — Daily log, friction entry, value validation, friction classification
5. **Metrics to track** — Total conversations, handoffs, scenario mix, most used, biggest friction, would use again
6. **Observation categories** — Trust-breaking / High / Medium / Low
7. **Fix-now / next / defer mapping** — FIX_NOW_QUEUE_SPEC + FIX_NOW_QUEUE_TEMPLATE
8. **How to store trial logs** — `results/trial_logs/{broker}_{date}.md`
9. **How to store screenshots or notes** — Optional: `results/trial_logs/{broker}_{date}_screenshots/`
10. **Product friction in scope** — Copy case snapshot (implemented)
11. **Product friction deferred** — Full trial summary export, paste hint enhancement
12. **Workbench clarity** — Your next move already prominent; Copy case snapshot added
13. **Founder post–first few cases** — Collect friction, what worked, broker confusion
14. **Launch blocker** — trial_launch_check FAIL; 503; missing docs
15. **Acceptable trial friction** — Manual evidence pack; no inbox sync
16. **Launch package coherence** — Single command + FOUNDER_LAUNCH_NOTES + BROKER_TRIAL_ONE_PAGER
17. **First post-trial sprint** — Fill FIX_NOW_QUEUE_TEMPLATE; map to components; prioritize fix now
18. **Later production hardening** — Inbox sync, OCR, carrier API, multi-tenant

---

## 5. Iteration Loop 1 — Strengthen Trial Launch Path

**What launch problems were fixed:**
- No single entry point → `trial_launch_check.sh` created
- Fragmented launch docs → TRIAL_LAUNCH_CHECKLIST_SPEC, FOUNDER_LAUNCH_NOTES consolidated
- No clear "ready to launch" definition → Checklist spec defines it

**Why these fixes were chosen:** Founder needs one command and one place to read before first broker trial.

**What became easier:** Founder runs `bash scripts/trial_launch_check.sh` → gets PASS + printed checklist; no need to hunt across docs.

**What did not improve:** Backend/frontend still need manual start; API test still skipped when server not on 8001.

**Worth it:** Yes — single entry reduces confusion significantly.

---

## 6. Iteration Loop 2 — Evidence Capture + Fix-Now Queue

**What evidence/queue problems were fixed:**
- No fix-now queue template → FIX_NOW_QUEUE_TEMPLATE.md created
- No evidence pack template → EVIDENCE_PACK_TEMPLATE.md created
- trial_logs README thin → Updated with fix-now queue and evidence pack instructions

**Why these fixes were chosen:** Post-trial observations need a ready-made structure to become actionable sprint backlog.

**What improved vs loop 1:** Founder (or broker) can copy FIX_NOW_QUEUE_TEMPLATE, fill from friction classification, save to results/trial_logs — immediate input for next sprint.

**What still remained weak:** Evidence pack is still manual; no automated export.

**Worth it:** Yes — fix-now queue is now actionable.

---

## 7. Iteration Loop 3 — Small Product Friction Reduction

**What product friction problems were fixed:**
- No quick way to copy case summary for trial log or handoff sharing → "Copy case snapshot" button added

**Why this fix was chosen:** During trial, founder/broker may want to paste a case into observation log or share for feedback; manual copy of multiple sections is friction.

**What improved vs loop 2:** One click copies case focus, next move, collected, still needed, draft preview — compact text for evidence capture.

**What still remained weak:** No "Copy trial summary" for full evidence pack; paste hint not enhanced.

**Worth it:** Yes — low risk, high value for trial evidence capture.

---

## 8. Optional Loop 4

**Used:** No.  
**Reason:** Copy case snapshot was the primary friction reduction; paste hint is already adequate. Stopping is correct — no clearly valuable, low-risk refinement remaining.

---

## 9. Validation Summary

| Check | Result |
|-------|--------|
| trial_launch_check.sh | PASS |
| guardrail_inbox_triage.sh | PASS (64/64, 41/41, 27/27, 23/23, 27/27) |
| run_multi_turn_simulations.py | 41/41 Strong |
| audit_state_field_accuracy.py | 7/7 passed |
| verify_speed_routing.py | OK |
| UI build | OK |

**Limitations:** unified_intake_smoke_check manual steps not run (requires live UI); API test skipped when server not on 8001.

---

## 10. Deployment / Release Judgment

| Component | Changed | Redeploy needed |
|-----------|---------|-----------------|
| Backend | No | No |
| Frontend | Yes (Copy case snapshot) | Yes — Vercel |

**Backend live:** No change.  
**Frontend live:** Redeploy recommended to expose Copy case snapshot in production.

---

## 11. Founder Showcase

| Example | What founder/broker now does | What became easier | Evidence better captured |
|---------|------------------------------|--------------------|--------------------------|
| **Before first trial** | Run `bash scripts/trial_launch_check.sh` | Single command; printed checklist | — |
| **During trial** | Click "Copy case snapshot" on any case | One-click copy for log or sharing | Case focus, next move, collected, still needed, draft |
| **Post-trial** | Copy FIX_NOW_QUEUE_TEMPLATE → fill → save to results/trial_logs | Ready-made structure | Fix now/next/defer with map-to |

**Why this helps next sprint:** Observations convert directly into prioritized backlog with component mapping.

---

## 12. Final Judgment

- **Biggest gain:** Single launch entry (`trial_launch_check.sh`) + fix-now queue template + Copy case snapshot.
- **Biggest remaining weakness:** Evidence pack is manual; no automated trial summary export.
- **Meaningfully improves trial launchability and learning quality:** Yes.
- **Best next step:** Run real 1-week trial; fill fix-now queue; plan next sprint from observations.

---

## 13. Iteration Log

| Loop | What changed | Better vs prior | Not improved | Worth it | Next after loop |
|------|--------------|-----------------|--------------|----------|-----------------|
| 1 | trial_launch_check.sh, launch docs, FOUNDER_LAUNCH_NOTES | Single entry; clear checklist | API test still skipped | Yes | Loop 2 |
| 2 | FIX_NOW_QUEUE_TEMPLATE, EVIDENCE_PACK_TEMPLATE, trial_logs README | Post-trial queue actionable | Evidence pack manual | Yes | Loop 3 |
| 3 | Copy case snapshot button | Trial evidence capture easier | No full trial summary | Yes | Stop |
| 4 | — | — | — | — | Not used |

---

## 14. 中文宏观总结

**为什么现在做这轮：** 试用包已有文档和场景，但缺少“一键启动”和“试后迭代”的清晰路径。创始人启动试用时容易困惑，试后反馈难以转化为可执行的修复队列。

**主要用了什么方法/技术：** 控制文档栈（Blueprint、Checklist、Evidence Pack、Fix-Now Queue、Friction Reduction）、单入口脚本（trial_launch_check.sh）、可填充模板（FIX_NOW_QUEUE_TEMPLATE、EVIDENCE_PACK_TEMPLATE）、小产品改进（Copy case snapshot）。

**这轮最大的提升：** 创始人可通过一条命令启动试用，试后可用现成模板将观察转化为 fix now / fix next / defer 队列；工作台新增“Copy case snapshot”便于证据采集和分享。

**还差什么：** 证据包仍为手动；无自动化试用总结导出；需真实试用验证。

**下一步最该做什么：** 执行真实 1 周经纪人试用，填写 fix-now 队列，根据观察规划下一轮迭代。

---

## 15. COPY/PASTE FOUNDER BLOCK

```
Trial Launch + Fix-Now Queue Sprint — Founder Summary

Biggest launch/evidence improvement:
- Single entry: bash scripts/trial_launch_check.sh — prints checklist
- Fix-now queue template: docs/trial/FIX_NOW_QUEUE_TEMPLATE.md — copy, fill, save to results/trial_logs
- Copy case snapshot: New button in workbench — one-click copy of case focus, next move, collected, still needed, draft

Biggest remaining weakness:
- Evidence pack is manual; no automated trial summary export

Makes product more trial-ready/reusable: Yes

Redeploy needed: Frontend (Vercel) — Copy case snapshot is new

What Andy should inspect next:
1. Run bash scripts/trial_launch_check.sh — verify PASS
2. Open workbench → open any case → click "Copy case snapshot" → paste somewhere to verify
3. Copy docs/trial/FIX_NOW_QUEUE_TEMPLATE.md → results/trial_logs/test_fix_now.md — verify structure
```

---

## 16. REQUIRED CROSS-WINDOW BLOCK

```
Trial Launch + Fix-Now Queue Sprint — Evaluator Block

Current launch/trial maturity:
- Product: Strong (guardrails pass, 7 scenarios, workbench coherent)
- Launch path: Now has single entry (trial_launch_check.sh) and consolidated founder notes
- Evidence capture: Template + fix-now queue structure ready
- Post-trial iteration: FIX_NOW_QUEUE_TEMPLATE + spec; observations map to fix now/next/defer

Biggest improvements:
1. Single launch entry (trial_launch_check.sh)
2. Fix-now queue template for post-trial sprint planning
3. Copy case snapshot button for evidence capture

Biggest remaining weaknesses:
- Evidence pack manual; no automated export
- Real broker trial not yet run — validation pending

Direction correct: Yes — focused on launch readiness and learning quality, not broad features

Best next recommendation: Run real 1-week broker trial; fill fix-now queue; plan next sprint from observations

Current IT technical backbone/stack:
- Backend: Python/FastAPI on Cloud Run (port 8001 local)
- Frontend: React/Vite on Vercel (port 5173 local)
- RAG: Qdrant; config-driven triage; rule + LLM hybrid
- No Stripe, auth, multi-tenant
```

---

## 17. REQUIRED SHORT OVERVIEW

### 为什么做这件事

试用包已有文档和场景，但缺少“一键启动”和“试后迭代”的清晰路径。创始人启动试用时容易困惑，试后反馈难以转化为可执行的修复队列。

### 主要用了什么方法/技术

控制文档栈（Blueprint、Checklist、Evidence Pack、Fix-Now Queue、Friction Reduction）、单入口脚本（trial_launch_check.sh）、可填充模板（FIX_NOW_QUEUE_TEMPLATE、EVIDENCE_PACK_TEMPLATE）、小产品改进（Copy case snapshot）。

### 这轮最大的提升

创始人可通过一条命令启动试用，试后可用现成模板将观察转化为 fix now / fix next / defer 队列；工作台新增“Copy case snapshot”便于证据采集和分享。

### 现在还差什么

证据包仍为手动；无自动化试用总结导出；需真实试用验证。

---

## 18. REQUIRED TIME / EFFORT SUMMARY

### 主要做了哪些工作

1. 创建 9 个控制文档（Blueprint、Checklist、Evidence Pack、Fix-Now Queue Spec/Template、Friction Reduction、Execution Outline、Acceptance Criteria、Founder Launch Notes、Evidence Pack Template）
2. 实现 trial_launch_check.sh 单入口脚本
3. 更新 results/trial_logs README 和 docs/trial INDEX
4. 实现 Copy case snapshot 按钮

### 哪些地方比原系统提高了

- 单入口启动：trial_launch_check.sh 替代分散的多个脚本和文档
- 试后迭代：FIX_NOW_QUEUE_TEMPLATE 可直接填充并映射到组件
- 证据采集：Copy case snapshot 一键复制 case 摘要

### 每一轮大概花了哪些时间 / 精力

- Loop 1（Launch path）：~15 min — 文档 + 脚本
- Loop 2（Evidence + queue）：~10 min — 模板 + README
- Loop 3（Friction reduction）：~10 min — Copy case snapshot 实现

### 还有哪些值得下一轮继续做

- 真实 1 周经纪人试用执行
- 根据试用反馈填充 fix-now 队列并规划下一轮迭代
- 可选：自动化证据包导出；paste hint 增强

---

*End of Trial Launch + Fix-Now Queue Sprint Report*
