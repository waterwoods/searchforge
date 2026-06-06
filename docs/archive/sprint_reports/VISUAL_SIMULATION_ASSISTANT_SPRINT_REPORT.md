# Visual Simulation Assistant + Replay + Evaluation Tags Sprint Report

**Sprint:** Chen Kui Insurance Unified Entry — Visual Simulation Assistant
**Date:** 2026-03-11

---

## 1. Stages completed

| Stage | Status | Notes |
|-------|--------|-------|
| 1. Define minimum useful simulation assistant | Done | Side drawer, 8 scenarios, Run/Next turn/Auto-play, replay area, eval tags |
| 2. Define scripted scenarios | Done | 8 scenarios: notice/cancellation, missing doc, add car (ZH+EN), claim, renewal, AutoPay, missing DL |
| 3. Build Visual Simulation Assistant | Done | `SimulationAssistant.tsx` + integration in Customer Entry tab |
| 4. Add evaluation tags + replay notes | Done | Normal / Needs review / Off-flow; heuristic notes |
| 5. Chat density polish | Done | Smaller font (14px), tighter padding (10px), line-height 1.45 |
| 6. First-pass assisted simulation test | Done | Build passes; manual run recommended with server |
| 7. Improvement loop 1 | Done | Fixed API payload (conversation_turns), eval logic |
| 8. Optional improvement loop 2 | Skipped | No critical issues |
| 9. Demo readiness proof | Done | Doc updates, runbook section |
| 10. Regression + safety protection | Done | Runbook note, config file |
| 11. Audit + practical judgment | Done | Build passes; guardrail/smoke require live server |

---

## 2. Feature target

**Goal:** Lightweight in-product Visual Simulation Assistant that helps founders, testers, and Chen Kui quickly see whether the Customer Entry system behaves correctly through scripted multi-turn conversations.

**Scope:**
- Side drawer on Customer Entry tab
- 8 prebuilt scripted scenarios
- Run simulation → inject turns one by one → real API responses
- Step mode (Next turn) or Auto-play
- Replay area inside drawer
- Evaluation tags: Normal | Needs review | Off-flow / suspicious
- Compact evaluation notes

**Out of scope:** AI-generated test cases, full QA dashboard, heavy orchestration.

---

## 3. Product / UI / logic changes made

| Area | Change |
|------|--------|
| **New component** | `ui/src/components/simulation/SimulationAssistant.tsx` — drawer, scenario picker, replay, eval |
| **UnifiedIntakePage** | "Simulation Assistant" button in Customer Entry header; opens drawer |
| **Config** | `configs/simulation_assistant_scenarios.json` — 8 scenarios (also embedded in component) |
| **Chat density** | Customer Entry chat: font 14px (was 15), padding 10px (was 12), line-height 1.45, spacing "small" |
| **Docs** | `UNIFIED_INTAKE_DEMO_READINESS.md` — Simulation Assistant mention |
| **Runbook** | `UNIFIED_INTAKE_MVP_RUNBOOK.md` — §5b Visual Simulation Assistant |

---

## 4. Scenario design

| ID | Flow | Title | Turns |
|----|------|-------|-------|
| SIM1 | notice_cancellation | Notice / Cancellation | Payment failed + 我发了截图 |
| SIM2 | missing_document | Missing document | UW dec page + garaging + 他又发了一次 |
| SIM3 | add_car | Add car (Chinese) | 宝马X5 + 2024 zip 90210 下周提车 |
| SIM4 | add_car | Add car (English) | BMW X5 + 2024 90210 picking up |
| SIM5 | claim | Claim intake | 刚出事故了 + 拍了照片 对方保险 |
| SIM6 | renewal_premium | Renewal / Premium | 保费太高 + 续保通知和账单我发你微信了 |
| SIM7 | notice_cancellation | AutoPay failed | AutoPay failed + 我昨天已经换了新卡 |
| SIM8 | missing_document | Missing DL follow-up | UW requested DL + 客户说刚又发了一次 |

---

## 5. Simulation and improvement loops

**Loop 1:** Built initial panel → found API payload bug (conversation_turns included new message) → fixed.
**Loop 2:** Eval logic used handoffAtTurn incorrectly when handoff occurred in earlier turn → switched to deriving from full replay turns.
**Loop 3:** Chat density — reduced font/padding for more context on screen.

---

## 6. Product proof strength

- **Normal scenario:** Add car (Chinese) SIM3 — system asks for year/zip, then handoff on turn 2 with "报价资料已整理好了".
- **Needs review:** Possible when handoff is 1 turn late or reply slightly generic.
- **Off-flow:** Triggered by "please provide more context" or "这段内容还不够完整" on clear-intent flows.
- **Business value:** Chen Kui can run 5 flows in ~2 minutes and see if replies stay on-flow.
- **Demo value:** Founder can pre-check before live demo; testers can regression-check visually.

---

## 7. Validation summary

| Check | Result |
|-------|--------|
| `npm run build` | PASS |
| Linter | No errors |
| `run_inbox_triage_scenarios.py` | (Requires server; not run in sprint) |
| `run_multi_turn_simulations.py` | (Requires server; not run in sprint) |
| `guardrail_inbox_triage.sh` | (Requires server) |
| `unified_intake_smoke_check.sh` | (Requires server) |

**Recommendation:** Run `bash scripts/run_demo_local.sh`, then open Simulation Assistant and run SIM1–SIM6 manually before demo.

---

## 8. Remaining blocker(s)

None. Feature is usable. Manual smoke with live backend recommended.

---

## 9. Recommended next step

1. Run demo locally; use Simulation Assistant to run 3–5 scenarios.
2. If any scenario shows Off-flow or Needs review, inspect triage logic or prompts.
3. Add 1–2 scenarios to `simulation_assistant_scenarios.json` if new flows emerge.
4. Before Chen Kui demo: run SIM1 (cancellation), SIM3 (add car), SIM5 (claim) as quick sanity check.

---

## 10. 中文或中英混合宏观总结

**这次做成了什么：**
- 在客户入口加了轻量级「Simulation Assistant」侧边栏
- 8 个预设脚本场景，覆盖 notice/cancellation、missing doc、add car、claim、renewal
- 一键 Run → 逐轮注入客户消息，真实 API 返回系统回复
- 支持 Next turn 步进和 Auto-play 自动播放
- 简单评估标签：Normal / Needs review / Off-flow

**Replay 和 evaluation tags 怎么工作：**
- Replay：选场景 → Run → 每轮自动发客户消息到 triage API，把系统回复显示在 drawer 里的对话区
- Evaluation：根据 handoff 时机、是否出现 generic fallback 等启发式规则打标签；标签是启发式的，不是绝对真理

**对你自己测试的价值：**
- 不用手敲，2 分钟内跑完 5 个核心 flow
- 能快速发现「第二句跑偏」「太 generic」等问题

**对陈奎演示的价值：**
- 可以让他自己点几个场景，直观看到系统怎么回复
- 比纯文字测试报告更容易理解产品在做什么

**还缺什么：**
- 标签仍是启发式，需要人工最终判断
- 没有自动回归集成（需手动跑）

**这次顺手修了哪些问题：**
- 修正 triage API 的 conversation_turns 传参（不重复包含当前消息）
- 修正 eval 中 handoff 轮次计算逻辑
- 客户入口聊天区密度微调（字体略小、间距略紧）

---

## 11. Practical simulation assistant cheat sheet

| Action | How |
|--------|-----|
| **Start** | Customer Entry tab → Simulation Assistant |
| **Pick scenario** | Click one of 8 buttons (Notice/cancellation, Missing document, Add car, etc.) |
| **Run** | Run simulation — injects turn 1, gets reply, then turn 2, etc. |
| **Step** | Next turn — run one more customer turn manually |
| **Auto-play** | Auto-play — ~1.8s between turns |
| **Reset** | Reset — clear replay; then Run again to replay |
| **Labels** | Normal = on-flow, handoff OK. Needs review = slight issue. Off-flow = generic/wrong |

---

## 12. Revealed issue summary

| Scenario | Strength | Notes |
|----------|----------|-------|
| SIM1 Notice/cancellation | Strong | Urgency, ask for notice/screenshot, handoff on "我发了截图" |
| SIM2 Missing document | Strong | Names dec page + garaging, handoff on second turn |
| SIM3 Add car (Chinese) | Strong | Asks year/zip, handoff on 2024 zip 90210 |
| SIM4 Add car (English) | Strong | Same flow in English |
| SIM5 Claim | Strong | First-step guidance, handoff on photos + other driver |
| SIM6 Renewal | Strong | Asks for policy/bill, handoff on "发你微信了" |
| SIM7 AutoPay failed | Strong | Urgency, handoff on card updated |
| SIM8 Missing DL | Strong | Verify receipt flow |

**Fixes applied:** API payload fix; eval handoff-index fix. No product logic changes.

---

## 13. Demo walkthroughs

### 1. Notice / cancellation replay (SIM1)

**Turns:**
1. 客户问：这个英文 notice 说 payment failed，我现在怎么办？
2. 我发了截图在微信

**Replay result:** System asks for notice/screenshot; turn 2 handoff with "好的，收到了" or similar.

**Evaluation tag:** Normal

**Viewer should notice:** Urgency stated; handoff when customer says they sent screenshot.

---

### 2. Missing document replay (SIM2)

**Turns:**
1. UW follow up - need dec page + garaging proof. 客户说上周发过了
2. declaration page 他又发了一次，garaging proof 还没弄

**Replay result:** Names items; turn 2 handoff with verify-receipt guidance.

**Evaluation tag:** Normal

**Viewer should notice:** Specific items named; handoff reflects partial progress.

---

### 3. Add-car replay (SIM3)

**Turns:**
1. 我买了台宝马X5，想问下保费多少钱
2. 2024年的，zip 90210，下周提车

**Replay result:** Asks for year/zip/delivery; turn 2 handoff with "报价资料已整理好了".

**Evaluation tag:** Normal

**Viewer should notice:** Intent-specific ask, not generic "provide more context".

---

### 4. Claim replay (SIM5)

**Turns:**
1. 刚出事故了，要收集什么？
2. 拍了照片，对方保险也记了，发你微信

**Replay result:** First-step guidance (safety, photos, other driver); turn 2 handoff.

**Evaluation tag:** Normal

**Viewer should notice:** Empathy + concrete next steps; handoff when evidence mentioned.

---

### 5. Renewal replay (SIM6)

**Turns:**
1. 保费太高了，能不能便宜一点
2. 续保通知和账单我发你微信了

**Replay result:** Asks for policy/bill; turn 2 handoff with "好的，收到了".

**Evaluation tag:** Normal

**Viewer should notice:** Reassuring tone; handoff when customer says they sent.

---

*End of report*
