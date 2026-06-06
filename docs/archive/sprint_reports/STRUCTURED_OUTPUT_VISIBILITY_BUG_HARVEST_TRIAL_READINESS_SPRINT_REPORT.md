# Structured Output Visibility + Bug Harvest + Trial Readiness Sprint Report

**Date:** 2026-03-12  
**Sprint:** Chen Kui Insurance Unified Entry  
**Budget:** 30–45 minutes focused work

---

## 1. Stages completed

| Stage | Status | Notes |
|-------|--------|-------|
| 1. Review structured output visibility | Done | Classified as good but partial |
| 2. Define best structured output surface | Done | Target layout aligned with BROKER_HANDOFF_CLARITY_GUIDE |
| 3. Bug harvest with Simulation Assistant | Done | 15/15 Normal; no off-flow bugs |
| 4. Prioritize fixes | Done | Visibility improvements chosen; no flow bugs to fix |
| 5. Improvement loop 1 | Done | Case focus + queue card visibility |
| 6. Optional improvement loop 2 | Skipped | No high-value bugs; visibility pass sufficient |
| 7. Chen Kui trial prep | Done | 5 walkthroughs prepared |
| 8. Validation | Done | npm build, guardrail PASS |
| 9. Redeploy readiness | Done | Frontend-only redeploy |
| 10. Audit | Done | Accept |

---

## 2. Visibility review

**Classification:** Good but partial → improved to **strong**.

**Before:**
- Case focus: Present as tag; sometimes generic "Client request"
- Your next move: Prominent ✓
- Collected / Still needed: Chips present for 4 flows ✓
- Last update: Present in "Where this case stands" ✓
- Queue cards: Compact preview; category tag

**Gaps identified:**
1. Case focus not always surfaced from structured data (relied on text regex)
2. Queue cards did not lead with case focus when inferable
3. No dedicated "Case focus:" label at top of action card

**After improvements:**
1. **Case focus** — Dedicated line at top of action card: "Case focus: Add car quote" (or Premium review, Claim intake, Missing document, Payment / cancellation risk)
2. **Structured-field inference** — New `inferCaseFocusFromStructuredFields()` uses `collected_fields` / `still_needed_fields` / `issue_category` for reliable focus when backend provides structured data
3. **Queue cards** — Case focus tag shown first when inferable; category tag only when focus unknown

---

## 3. Bug harvest findings

**Simulation Assistant (15 scenarios):** All PASS. No off-flow, no generic fallback.

| Scenario | Flow | Result |
|----------|------|--------|
| SIM1–SIM15 | notice_cancellation, missing_document, add_car, claim, renewal_premium | Normal |

**Notable behaviors:**
- SIM14 (Notice minimal "发你了") — Handoff at turn 2 ✓
- SIM12 (Claim hit-and-run no photos) — Handoff with "您说的情况已整理好了" ✓
- SIM15 (Add car 3-turn) — Handoff at turn 3 ✓

**Other packs:**
- Inbox triage: 49/49 passed
- Multi-turn: 29/29 strong
- Adversarial: 27/27 strong
- Complex adversarial: 22 strong, 1 acceptable (LC-AC3 handoff 1 turn early)

**Conclusion:** No high-value flow bugs to fix this sprint. System is stable.

---

## 4. Improvements made

| Change | File | Purpose |
|--------|------|---------|
| Case focus line at top of action card | UnifiedIntakePage.tsx | Broker sees focus before next move |
| `inferCaseFocusFromStructuredFields()` | UnifiedIntakePage.tsx | Reliable focus from structured data |
| Queue card case focus tag first | UnifiedIntakePage.tsx | Triage at a glance without opening |

---

## 5. Trial scenario preparation

See §12 Chen Kui trial walkthroughs below.

---

## 6. Validation summary

| Check | Result |
|-------|--------|
| `npm run build` | ✓ |
| `run_inbox_triage_scenarios.py` | 49/49 passed |
| `run_simulation_assistant_scenarios.py` | 15/15 Normal |
| `guardrail_inbox_triage.sh` | PASS |
| `run_multi_turn_simulations.py` | 29/29 strong |

---

## 7. Redeploy readiness

- **Frontend-only redeploy needed:** Yes
- **Backend changes:** None
- **Deploy order:** Frontend (Vercel) only
- **Post-deploy smoke:** Open `/workbench/unified-intake`, Load founder demo queue, reopen cancellation risk, verify Case focus line and queue card case focus tags

---

## 8. Recommended next step

1. Redeploy frontend to Vercel
2. Chen Kui runs 3–5 trial walkthroughs (§12)
3. Collect feedback on Case focus visibility and queue triage
4. Optional: Add 1–2 Simulation Assistant scenarios for edge cases if new bugs surface

---

## 9. 中文或中英混合宏观总结

**结构化输出这次看得更清楚了没有？**  
是的。工作台现在在 case card 顶部有明确的 "Case focus: Add car quote" 等标签，queue 卡片也会优先显示 case focus，broker 不用再猜这是什么类型的 case。

**抓出了哪些 bug？**  
Simulation Assistant 15 个场景全部通过，没有 off-flow 或 generic fallback。其他 pack（inbox triage、multi-turn、adversarial）也都通过。这次没有发现需要修复的 bug。

**修了哪些最重要的问题？**  
主要是 visibility：  
1）Case focus 从 structured fields 推断，更可靠；  
2）Case card 顶部增加 "Case focus:" 行；  
3）Queue 卡片优先显示 case focus tag。

**陈奎现在试用时最该看什么？**  
1）Load founder demo queue 后，看 queue 卡片上的 case focus（Add car quote、Premium review 等）；  
2）打开一个 case，看顶部的 "Case focus:" 和 "Your next move"；  
3）看 Collected / Still needed 的绿色/橙色 chips；  
4）用 Simulation Assistant 跑几个场景，确认 handoff 正常。

**为什么这一步很重要？**  
数据库存了 case，工作台要能清楚展示 case。Broker 不应该再去翻原始聊天或数据库才能干活。这次把 structured output 的可见性提高，broker 能更快 triage、更少 reread。

---

## 10. Practical broker visibility checklist

| Broker 现在能看到 | 不用再去看数据库的地方 | 还得依赖原始聊天的地方 |
|-------------------|------------------------|------------------------|
| Case focus | ✓ 从 structured fields 或 source 推断 | 仅当无法推断时 |
| Your next move | ✓ 直接显示 | — |
| Collected | ✓ 绿色 chips | — |
| Still needed | ✓ 橙色 chips | — |
| Status / due-state | ✓ Tag + Where this case stands | — |
| Last meaningful update | ✓ 在 case card 和 queue | — |
| What changed after append | ✓ "Just updated with customer follow-up" | — |
| Full conversation | ✓ 在 case card 下方 | 需要验证细节时 |

---

## 11. Bug + visibility summary

| Area | Status |
|------|--------|
| Strongest scenarios | SIM1–15, MT1–29, adversarial 27, complex 22 |
| Suspicious scenarios | None this sprint |
| Visible structured-output improvements | Case focus line, queue case focus tag, structured-field inference |
| Remaining issues | API test 2 failures when server stale (persist, append); not blocking |

---

## 12. Chen Kui trial walkthroughs

### Walkthrough 1: Cancellation risk (urgency)

**What to run:** Load founder demo queue (or paste cancellation message)  
**What to say/click:** Click "Load founder demo queue" → cancellation risk case opens first  
**What to watch for:** Case focus "Payment / cancellation risk", "Same-day action", "Your next move" 明确  
**What this proves:** 紧急 case 能一眼看出，broker 知道今天要处理

---

### Walkthrough 2: Missing document (operational)

**What to run:** Reopen "Missing document follow-up" from Recent cases  
**What to say/click:** 点击 Reopen case  
**What to watch for:** "Resume here" 显示 waiting on client + next contact；Collected/Still needed chips（如 declaration page, garaging proof）  
**What this proves:** 跟进 continuity，broker 不用重读聊天

---

### Walkthrough 3: Add car quote (revenue)

**What to run:** Customer Entry 或 Broker Workbench，paste: "我买了台宝马X5，想问下保费多少钱" → 第二句 "2024年的，zip 90210，下周提车"  
**What to say/click:** 客户入口输入第一句 → 发送 → 输入第二句 → 发送 → 查看工作台  
**What to watch for:** Case focus "Add car quote"；Collected: Year, Make/Model, ZIP, Delivery；handoff "报价资料已整理好了"  
**What this proves:** 多轮 intake 能收集关键字段，broker 看到 structured output

---

### Walkthrough 4: Claim intake (first response)

**What to run:** Paste "刚出事故了，要收集什么？" → 第二句 "拍了照片，对方保险也记了，发你微信"  
**What to say/click:** 客户入口或工作台，两轮对话  
**What to watch for:** Case focus "Claim intake"；Collected: Accident reported, Photos, Other driver info；handoff "好的，收到了"  
**What this proves:** 事故 first response 流程正常，broker 知道已收集什么

---

### Walkthrough 5: Simulation Assistant (QA)

**What to run:** 客户入口 → Simulation Assistant → 选 "Notice / Cancellation" 或 "Add car (Chinese)"  
**What to say/click:** Run simulation → 看 Evaluation: Normal  
**What to watch for:** 两轮后 handoff；无 generic "please provide more context"  
**What this proves:** 系统对 scripted 场景稳定，可用于内部 QA

---

*End of report*
