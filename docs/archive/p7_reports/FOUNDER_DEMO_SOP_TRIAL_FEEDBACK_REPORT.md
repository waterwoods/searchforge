# Founder Demo SOP + Real Trial Feedback Report

**Sprint:** Founder Demo SOP + Real Trial Feedback Sprint  
**Created:** 2026-03-14  
**Scope:** SearchForge → Chen Kui Insurance Unified Entry

---

## 1. Sprint Theme

**Theme:** Demo readiness + trial readiness + feedback collection readiness.

**Why now:** The product is technically ready enough. The gap is operational readiness: a clear, repeatable demo path and trial flow that Andy can run confidently and that a small-client prospect (e.g., 陈魁) can understand and trust.

---

## 2. Control Docs Created

| Doc | Path | Purpose |
|-----|------|---------|
| Sprint Blueprint | `docs/sprints/FOUNDER_DEMO_SOP_TRIAL_FEEDBACK_SPRINT_BLUEPRINT.md` | Why sprint matters, scope, in/out |
| Execution Outline | `docs/sprints/FOUNDER_DEMO_SOP_TRIAL_FEEDBACK_EXECUTION_OUTLINE.md` | Workstreams, roles, rehearsal sequence |
| Acceptance / SLA Criteria | `docs/sprints/FOUNDER_DEMO_SOP_TRIAL_FEEDBACK_ACCEPTANCE.md` | What must be clear to founder and prospect |

---

## 3. Demo SOP

**Primary doc:** `docs/FOUNDER_DEMO_SOP.md`

### Pre-demo steps

1. `bash scripts/demo_pre_checklist.sh`
2. `bash scripts/run_demo_local.sh` (if not running)
3. Optional: `bash scripts/warmup_for_demo.sh` 2–3 min before
4. `bash scripts/guardrail_inbox_triage.sh` → must PASS

### What to say first (30–60 sec)

> "这是一个加州汽车保险经纪助手。客户发来messy消息——微信、截图、通知——系统会整理成一个结构化case：有 urgency、下一步动作、收集了什么、还缺什么、草稿回复。你确认后再发，**不自动发送**。经纪保持控制。"

### What to show first

**Primary path:** Broker Workbench → Load founder demo queue → Cancellation risk opens first → Reopen Missing document, Add-car.

**Backup path:** Simulation Assistant → SIM1, SIM2, SIM3.

### What to avoid saying

- Connected to email/WeChat
- Reads image uploads
- Automatically sends replies
- Full CRM or carrier integration
- Perfect multilingual handling

### Fallback if demo goes slow

- Say: "有时第一轮会慢一点，我们继续看第二轮。"
- If API fails: switch to Simulation Assistant (no live API needed).

### "不自动发送" and human confirmation

Say explicitly: "系统会生成草稿回复，但**不自动发送**。你确认、修改后再发。当AI从对话里收集了敏感信息，会显示「Human confirmation recommended」，提醒你核对。"

---

## 4. Strongest Demo / Trial Path

### Primary path

**Broker Workbench → Load founder demo queue → Cancellation risk first**

1. Open http://localhost:5173/workbench/unified-intake
2. Switch to Broker Workbench tab
3. Click **Load founder demo queue** (seeds 13 demo-safe cases)
4. Cancellation-risk case auto-opens
5. Point to: Case focus, Your next move, Same-day action, Broker action required, Human confirmation
6. Reopen Missing document case → show waiting on, next contact
7. Reopen Add-car quote → show Collected / Still needed chips

### Backup path

**Simulation Assistant → SIM1, SIM2, SIM3**

1. Customer Entry tab → click **Simulation Assistant**
2. Run **SIM1 Cancellation risk** (3-turn)
3. Run **SIM2 Missing document** (3-turn)
4. Run **SIM3 Add-car quote (Chinese)** (3-turn)
5. Point to: Collected, Still needed, Human confirmation per turn

### Strongest scenarios

| # | Scenario | Why |
|---|----------|-----|
| 1 | Cancellation risk (SIM1) | Urgency, same-day action; most obvious "must act" value |
| 2 | Missing document (SIM2) | Operational follow-up; "client says already sent" — real office pain |
| 3 | Add-car quote (Chinese) (SIM3) | Revenue, multi-turn, Collected chips; handoff at turn 3 |

### Why this path is strongest

- Cancellation risk leads with urgency and same-day action.
- Missing document proves structured follow-up and verification clarity.
- Add-car proves multi-turn collection and Collected/Still needed chips.
- All three are 3-turn deep; guardrail passes 23/23 Simulation Assistant scenarios.

---

## 5. Feedback Capture Questions

Ask Chen Kui or a small-client prospect after the trial:

1. **Which scenario felt most useful to your office?** (Reveals what he values most.)
2. **Which part still feels risky or not trustworthy?** (Reveals trust concerns.)
3. **Would this save you or your assistant time?** (Reveals time-saving perception.)
4. **What would you want it to do next?** (Reveals next feature priority.)
5. **What would you be willing to try first in a pilot?** (Reveals what he would pay for.)

**Why they matter:** Commercially useful; inform pilot offer vs. gap fix.

---

## 6. Iteration Loop 1

### What was rehearsed

- Guardrail: PASS (49/49 inbox triage, 38/38 multi-turn, 27/27 adversarial, 23/23 Simulation Assistant)
- Unified intake smoke check: PASS (guardrail + daily-use simulation)
- UI build: PASS
- Browser rehearsal:
  - Navigated to http://localhost:5173/workbench/unified-intake
  - Switched to Broker Workbench
  - Clicked Load founder demo queue → 8 cases loaded
  - Opened first case (cancellation notice) → saw Copy client draft, status, follow-up, Save note
  - Switched to Customer Entry
  - Opened Simulation Assistant → saw SIM1, SIM2, SIM3, etc.

### What improved confidence

- Load founder demo queue works and populates cases.
- Case card shows: Case focus, Your next move, Human confirmation, Collected/Still needed, Copy client draft.
- Simulation Assistant clearly lists scenarios with good labels.
- Broker Workbench structure: Needs attention, Waiting on client, etc.
- Draft card already shows "不自动发送。"

### What reduced confidence

- Queue cards show "Reopen case" — case focus tags are present but snapshot did not emphasize order.
- Demo path was buried in secondary text; founder had to read to find it.
- No explicit "不自动发送" in the Founder demo snapshot area.

### Whether it was worth it

Yes. Rehearsal confirmed the flow works and identified where to improve founder guidance.

---

## 7. Iteration Loop 2

### What changed

1. **Founder demo snapshot card:** Added bold "Demo path: Load queue → Cancellation risk opens first → Reopen Missing document, then Add-car." Replaced long Chen Kui trial text with shorter line including "不自动发送 — broker confirms before sending."
2. **ANDY_2MIN_BEFORE_DEMO.md:** Added line for Unified Intake / Chen Kui trial: "Use docs/FOUNDER_DEMO_SOP.md — URL: http://localhost:5173/workbench/unified-intake"

### What improved vs loop 1

- Demo path is visible at a glance in the Founder demo snapshot.
- "不自动发送" is explicitly shown in the demo guidance.
- ANDY_2MIN now points to the correct SOP for Unified Intake trials.

### What still remained weak

- Queue cards show case focus tags but order depends on triage; founder may need to know "cancellation opens first" from the hint.
- Sider still shows "Experiment Lab" — could feel technical to a broker prospect (low priority).

### Whether the loop was worth it

Yes. Small, low-risk changes that improve founder clarity.

---

## 8. Optional Loop 3

**Whether used:** No.

**Reason:** No obvious additional fix. Queue cards already show case focus. Simulation Assistant order is clear. Further changes would risk scope creep. Stopping is correct.

---

## 9. Validation Summary

| Check | Result |
|-------|--------|
| `bash scripts/guardrail_inbox_triage.sh` | PASS |
| `bash scripts/unified_intake_smoke_check.sh` | PASS |
| `cd ui && npm run build` | PASS |
| Browser rehearsal (Broker Workbench + Simulation Assistant) | Flow works |

**Limitations:** API test skipped when server not on 8001; manual smoke steps require human verification.

---

## 10. Iteration Log (REQUIRED)

### Loop 1

- **What changed:** Rehearsed demo path; ran guardrail, smoke check, build.
- **What got better:** Confirmed flow works; identified friction (demo path visibility, 不自动发送).
- **What did not improve:** Demo path was still buried; no explicit 不自动发送 in demo area.
- **Worth it?** Yes.
- **Recommended next step:** Fix demo path visibility and 不自动发送 in Founder demo snapshot.

### Loop 2

- **What changed:** Added bold demo path line; added 不自动发送 to Founder demo snapshot; linked ANDY_2MIN to FOUNDER_DEMO_SOP.
- **What got better:** Demo path visible at a glance; 不自动发送 explicit; correct SOP for Unified Intake.
- **What did not improve:** Queue card order still implicit; sider label unchanged.
- **Worth it?** Yes.
- **Recommended next step:** Stop; no obvious Loop 3 gain.

### Loop 3

- **Whether used:** No.
- **Reason:** No obvious gain; stopping is correct.

---

## 11. Final Judgment

| Question | Answer |
|----------|--------|
| **Is the demo SOP ready to use tomorrow?** | Yes. `docs/FOUNDER_DEMO_SOP.md` is complete and actionable. |
| **Best primary path** | Broker Workbench → Load founder demo queue → Cancellation risk first → Reopen Missing doc, Add-car |
| **Best backup path** | Simulation Assistant → SIM1, SIM2, SIM3 |
| **Top 3 scenarios** | SIM1 Cancellation risk, SIM2 Missing document, SIM3 Add-car quote (Chinese) |
| **Top 3 hesitation points** | (1) "Is it really reliable?" — show Human confirmation badge; (2) "Does it auto-send?" — say 不自动发送 explicitly; (3) "Will it work with my real messages?" — show Simulation Assistant real-customer pack |
| **What Andy should do before/during/after** | Before: Run demo_pre_checklist, guardrail; open FOUNDER_DEMO_SOP. During: Say 30-sec intro; show primary path; emphasize 不自动发送. After: Ask 5 feedback questions. |
| **Single best next move** | Run one real trial with Chen Kui using this SOP; capture feedback; iterate on gaps. |

---

## 12. 中文宏观总结

**明天 demo 该怎么演：**  
打开 http://localhost:5173/workbench/unified-intake → Broker Workbench → Load founder demo queue → Cancellation risk 自动打开 → 依次 Reopen Missing document、Add-car。备选：Simulation Assistant → SIM1、SIM2、SIM3。

**最强的 3 个场景：**  
1. Cancellation risk（紧急、当天要处理）  
2. Missing document（缺材料、客户说发过了）  
3. Add-car quote（加车报价、多轮收集、Collected chips）

**最该强调的卖点：**  
messy 消息 → 结构化 case → 下一步动作、草稿回复。**不自动发送**，经纪确认后再发。

**最该避免说什么：**  
已接邮箱/微信、自动发回复、读图片、完整 CRM。

**最容易让对方犹豫的 3 个点：**  
(1) 可靠吗？→ 指出 Human confirmation recommended；(2) 会不会自动发？→ 明确说 不自动发送；(3) 真实消息能处理吗？→ 用 Simulation Assistant 的 real-customer 场景演示。

**这轮值不值得：**  
值得。SOP 清晰、路径明确、反馈问题就绪，可支撑真实 trial。

---

## 13. COPY/PASTE DEMO BLOCK

```
Pre-demo:
  bash scripts/demo_pre_checklist.sh
  bash scripts/guardrail_inbox_triage.sh  # must PASS
  bash scripts/run_demo_local.sh

URL: http://localhost:5173/workbench/unified-intake

Best demo path:
  1. Broker Workbench tab
  2. Load founder demo queue
  3. Cancellation risk opens first
  4. Reopen Missing document, then Add-car

Top scenarios: SIM1 → SIM2 → SIM3 (Simulation Assistant backup)

Strongest value: messy message → structured case → next move + draft. 不自动发送.

Biggest hesitation: "Does it auto-send?" — Say 不自动发送 explicitly.

What Andy should do next: Run one real trial with Chen Kui; capture feedback; iterate.
```

---

*See: `docs/FOUNDER_DEMO_SOP.md`, `docs/CHEN_KUI_TRIAL_PACK.md`, `docs/UNIFIED_INTAKE_DEMO_READINESS.md`*
