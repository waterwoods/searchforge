# Pre-Trial Review Report

**Sprint:** Pre-Trial Review Sprint  
**Created:** 2026-03-18  
**Scope:** SearchForge → Chen Kui Insurance Unified Entry

---

## 1. Sprint Theme

**What was reviewed:** Current system state, standard scenario package, realistic simulation results (guardrail), trial package, kickoff docs, client-aware wiring (handoff phrases, client identity persistence), and Scenario Logic Center.

**Why now:** The product has evolved through demo → sellable package → scenario hardening → Real Broker Trial Package → Scenario Logic Center. Trial docs and simulation pack exist. The next step is real broker usage. Before that, we need a structured review to decide what is strong enough for trial, what to watch, what to defer, and what exact flows to include in the first real broker trial.

---

## 2. Document Set Created

| Doc | Purpose |
|-----|---------|
| `01_PRE_TRIAL_REVIEW_BLUEPRINT.md` | Why pre-trial review; what sprint does/does not do |
| `02_TRIAL_SCOPE_REVIEW_SPEC.md` | Included/excluded surfaces and scenarios |
| `03_SCENARIO_READINESS_REVIEW_SPEC.md` | Per-scenario assessment dimensions; guardrail evidence |
| `04_FIX_NOW_FIX_NEXT_DEFER_REVIEW_SPEC.md` | Practical fix queue with rationale |
| `05_EXECUTION_OUTLINE.md` | Workstreams; loop plan |
| `06_ACCEPTANCE_TRIAL_REVIEW_CRITERIA.md` | Pass criteria for pre-trial review and trial readiness |
| `07_FOUNDER_REVIEW_NOTES.md` | Before-trial; during first 3–5 conversations; post-trial |

---

## 3. Current Trial Readiness

### Strongest Areas

| Area | Evidence |
|------|----------|
| **Core 5 scenarios** | Add-car, missing doc, cancellation risk, premium review, claim — all strong in scenario_logic_center; guardrail 64/64 rule-based, 41/41 multi-turn, 27/27 SIM |
| **Client-aware wiring** | Handoff phrases by client; client identity persistence (append uses case.client_id); A/B variation PASS |
| **Scenario Logic Center** | Single place to see 14 scenarios, maturity, broker_next_step, config layer |
| **Trial package** | Clear 5 core + 2 extended; SIM1–SIM5 order; value validation questions |
| **Founder demo queue** | 13 cases; cancellation opens first; Load founder demo queue works |

### Medium-Risk Areas

| Area | Risk | Mitigation |
|------|------|------------|
| **Billing clarification** | fix_next; must NOT route to payment_lapse | Watch during trial; exclude from first 3 flows |
| **Remove vehicle** | Medium maturity; fewer sims | Include only if broker asks |
| **Correction / already_sent visibility** | Broker may not see when customer said "already sent" | Watch during first 3–5 conversations |
| **Talk to Agent** | Last-mile risk: routes wrong → trust-breaking | Test "联系人工" explicitly; part of flow but watch |

### Weakest Areas

| Area | State | Action |
|------|-------|--------|
| **Bundling** | Weak; defer | Exclude from first trial |
| **Unclear fallback** | Weak; generic broker_next_step | Acceptable; broker clarifies |
| **Append API test** | 1 fail when server not on 8001 | Verify route deployed; not scenario logic |
| **Handoff thresholds** | In triage.py; not config | Defer; extract if client variation needs it |

---

## 4. Scenario-by-Scenario Judgment

### Strong Enough for Trial

| Scenario | SIM | Why |
|----------|-----|-----|
| **Cancellation risk / Payment failed** | SIM1 | Urgency; same-day action; broker_next_step clear; guardrail PASS |
| **Missing document / Already sent** | SIM2 | Structured follow-up; verify receipt; R2 "都发过了怎么还要" PASS |
| **Add-car quote** | SIM3, SIM15 | Multi-turn; Collected chips; handoff at turn 3; SIM15 strongest multi-turn proof |
| **Premium review** | SIM6 | Retention follow-up; policy/bill mentioned |
| **Claim intake** | SIM5 | First-response; accident + hit-and-run; collected/still-needed |
| **Talk to Agent** | R3b | Client config; immediate handoff; watch during trial |

### Usable with Caution

| Scenario | Why caution |
|----------|-------------|
| **Remove vehicle** | Medium maturity; fewer sims; include if broker asks |
| **Billing clarification** | fix_next; route vs payment_lapse; exclude from first 3 flows |
| **English notice confusion** | Medium; R4, R19, F3, ER4 pass; lower frequency |

### Weak / Defer from First Trial

| Scenario | Why defer |
|----------|-----------|
| **Bundling** | Weak; low priority; defer |
| **Unclear** | Fallback; acceptable for edge cases |

---

## 5. Fix-Now / Fix-Next / Defer

### Fix-Now (Trial-Breaking)

| # | Item | Why |
|---|------|-----|
| — | *(None identified)* | Guardrail PASS; no known trial-blockers |

**Note:** If append API fails in production, verify route deployed. Not scenario logic.

### Fix-Next (Important, Not Blocking)

| # | Item | Why |
|---|------|-----|
| 1 | **Billing clarification** | fix_next in scenario_logic_center; must NOT route to payment_lapse |
| 2 | **Correction / already_sent visibility** | Last-mile risk; broker may not see when customer said "already sent" |
| 3 | **Handoff thresholds to config** | Hardcoded in triage.py; extract if client variation needs it |

### Defer

| # | Item | Why |
|---|------|-----|
| 1 | Inbox sync, email/WeChat | Out of scope |
| 2 | OCR upload | Out of scope |
| 3 | Carrier API | Out of scope |
| 4 | Bundling scenario | Weak; low priority |
| 5 | Simulation coverage counts in UI | Nice-to-have |
| 6 | add-car-rules client-aware | Legacy; fallback works |

---

## 6. Recommended First Trial Scope

### Exact Scenarios to Include

| Order | Scenario | SIM | Why |
|-------|----------|-----|-----|
| 1 | **Cancellation risk** | SIM1 | Urgency; same-day; opens founder demo queue first |
| 2 | **Missing document** | SIM2 | Operational; "already sent" pain; verify receipt |
| 3 | **Add-car quote** | SIM3 | Revenue; multi-turn; Collected chips |
| 4 | **Premium review** | SIM6 | Retention; optional if time |
| 5 | **Claim intake** | SIM5 | First-response; optional if time |

**Best 3-scenario order (short trial):** SIM1 → SIM2 → SIM3

**Best 5-scenario order (full trial):** SIM1 → SIM2 → SIM3 → SIM6 → SIM5

### Exact Scenarios to Exclude from First Trial

| Scenario | Why exclude |
|----------|-------------|
| Billing clarification | fix_next; route risk |
| Remove vehicle | Medium; include only if broker asks |
| Bundling | Weak; defer |
| DMV/SR-22 | Unless broker asks |
| Talk to Agent | Available in flow; watch but don't lead with it |

### Why This Scope

- **3 flows minimum:** Cancellation, missing doc, add-car — prove urgency, operational follow-up, and multi-turn revenue.
- **5 flows if time:** Add premium review and claim — prove retention and first-response.
- **Exclude billing:** Known fix_next; avoid trust-breaking route confusion.
- **Exclude bundling:** Weak; not worth trial time.

---

## 7. Founder Guidance

### What Andy Should Do Before Trial

| Step | Action |
|------|--------|
| 1 | Run `bash scripts/trial_launch_check.sh` — must PASS |
| 2 | Run `bash scripts/run_demo_local.sh` |
| 3 | Open http://localhost:5173/workbench/unified-intake |
| 4 | Load founder demo queue — verify 13 cases; cancellation opens first |
| 5 | Run SIM1, SIM2, SIM3 in Simulation Assistant |
| 6 | Read `docs/trial/FOUNDER_LAUNCH_NOTES.md` |
| 7 | Bring `docs/trial/BROKER_TRIAL_ONE_PAGER.md` |
| 8 | Copy `docs/trial/TRIAL_OBSERVATION_LOG_TEMPLATE.md` for broker |

### What Andy Should Inspect During First 3–5 Real Conversations

| Watch for | Why |
|-----------|-----|
| **Talk to Agent flow** | If customer says "联系人工" — does it route correctly? Handoff immediate? |
| **Correction / already_sent** | Does broker see when customer said "already sent"? |
| Broker hesitates at paste | May not know what to paste; give example |
| Broker ignores Collected chips | May not trust; point out Human confirmation |
| Broker rewrites draft completely | Draft quality; note for iteration |
| Broker can't find next move | Visibility; may need UI tweak |
| Broker confused on reopen | Resume here; waiting_on clarity |

### Post-Trial

1. Copy observation log to `results/trial_logs/{broker}_{date}.md`
2. Fill Friction Classification table
3. Use `docs/trial/FIX_NOW_QUEUE_SPEC.md`
4. Copy `docs/trial/FIX_NOW_QUEUE_TEMPLATE.md`; fill and save
5. Add fix-now items to next sprint backlog

---

## 8. 中文宏观总结

### 为什么现在做 Pre-Trial Review

产品已完成 demo → 可售包 → 场景硬化 → 真实经纪 Trial 包 → Scenario Logic Center。Trial 文档、模拟包、client-aware 布线都已就绪。下一步是真实经纪使用。在此之前，需要结构化审核，决定：哪些足够强可以 trial、哪些需谨慎、哪些弱需暂缓、fix-now/fix-next/defer 如何划分、第一轮真实 trial 应包含哪些具体流程。

### 最强的是哪些

- **核心 5 场景：** 加车报价、缺材料、取消风险、续保审核、事故报备 — 全部 strong；guardrail 64/64、41/41、27/27 通过
- **Client-aware 布线：** handoff 按 client 变化；append 用 case.client_id；A/B 测试通过
- **Scenario Logic Center：** 单一入口看 14 场景、强弱、broker 下一步、config 层
- **Trial 包：** 5 核心 + 2 扩展；SIM1–SIM5 顺序清晰；价值验证问题已定义

### 最弱的是哪些

- **Billing clarification：** fix_next；路由可能混淆 payment_lapse；第一轮 trial 排除
- **Bundling：** weak；defer
- **Correction / already_sent 可见性：** 经纪可能看不到客户说「已发」；需观察
- **Talk to Agent：** 路由错误会破坏信任；需在 trial 中重点观察

### 第一轮真实 Trial 应该怎么收口

**必须包含 3 流程：** SIM1（取消风险）→ SIM2（缺材料）→ SIM3（加车报价）。证明：紧急、运营跟进、多轮收入。

**若时间允许加 2 流程：** SIM6（续保审核）、SIM5（事故报备）。

**排除：** Billing clarification（fix_next）、Bundling（weak）、DMV/SR-22（除非经纪要求）。

**创始人观察重点：** Talk to Agent 是否路由正确；Correction / already_sent 经纪是否可见；经纪能否找到 next move；草稿是否可用。

**Trial 后：** 填 observation log → Friction Classification → Fix-Now Queue → 下一 sprint backlog。

---

*End of Pre-Trial Review Report*
