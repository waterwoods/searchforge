# Simulation Assistant Scenario Expansion + Bug Harvest Sprint Report

**Sprint:** Chen Kui Insurance Unified Entry — Simulation Assistant Scenario Expansion + Bug Harvest
**Date:** 2026-03-12

---

## 1. Stages completed

| Stage | Status | Notes |
|-------|--------|-------|
| 1. Define highest-value new scenarios | Done | 7 new scenarios: notice correction, vague "already sent", add-car partial, claim hit-and-run, renewal indirect, notice minimal (tricky), add-car 3-turn |
| 2. Implement scenario expansion | Done | Added to `configs/simulation_assistant_scenarios.json` and `SimulationAssistant.tsx` |
| 3. First bug harvest pass | Done | Ran all 15 scenarios; 15/15 Normal (no bugs harvested) |
| 4. Prioritize fixes | Done | No product bugs found; improved eval visibility instead |
| 5. Improvement loop 1 | Done | Enhanced eval notes: "Issue likely at turn N", "Good next-step guidance" |
| 6. Optional improvement loop 2 | Done | Added 3-turn scenario (SIM15) to stress turn-3 behavior |
| 7. Improve issue visibility | Done | Eval notes now include turn-level hints for suspicious runs |
| 8. Demo + QA value proof | Done | 5 walkthroughs below |
| 9. Validation | Done | npm build, run_simulation_assistant_scenarios, guardrail pass |
| 10. Redeploy readiness | Done | Frontend-only change; stable for redeploy |
| 11. Audit + practical judgment | Done | Accept |

---

## 2. Feature target

**Goal:** Expand the Visual Simulation Assistant from 8 to 15 scenarios, add higher-value coverage (notice correction, vague "already sent", add-car partial, claim hit-and-run, renewal indirect, tricky minimal follow-up, 3-turn add-car), improve issue visibility in eval notes, and integrate into guardrail.

**Scope:**
- 7 new scripted scenarios (SIM9–SIM15)
- Enhanced eval notes: "Issue likely at turn N", "Good next-step guidance"
- CLI script `run_simulation_assistant_scenarios.py` for bug harvest
- Guardrail step 8: Simulation Assistant scenarios

**Out of scope:** AI-generated tests, heavy scoring engine, full QA platform.

---

## 3. Scenario expansion

| ID | Flow | Title | Turns | Purpose |
|----|------|-------|-------|---------|
| SIM9 | notice_cancellation | Notice correction (already paid) | Payment failed + 我其实已经付了 | Second-turn correction; verify-receipt handoff |
| SIM10 | missing_document | Vague "already sent" follow-up | UW dec page + 就是上次那个材料，我又发了 | Vague "上次那个材料"; preserve context |
| SIM11 | add_car | Add car partial (zip only) | 2024 BMW X5 + 90210 下周提车 | First turn has year+model; second adds zip+delivery |
| SIM12 | claim | Claim hit-and-run no photos | 刚出事故 + 对方跑了，没拍照片，记了车牌 | Hit-and-run, no photos; should still hand off |
| SIM13 | renewal_premium | Renewal indirect wording | 保费涨了好多 + 续保账单我微信发你了 | Informal "发你了" |
| SIM14 | notice_cancellation | Notice minimal follow-up (tricky) | Payment failed + 发你了 | Minimal follow-up; may expose wrong ask |
| SIM15 | add_car | Add car 3-turn (stress turn 3) | 宝马X5 → 2024年的 → 90210 下周提车 | 3-turn flow; hand off at turn 3 |

---

## 4. Bug harvest findings

**Result:** All 15 scenarios passed (Normal). No product bugs harvested.

**Observations:**
- Rule-based triage handles notice correction, vague "already sent", add-car partial, claim hit-and-run, renewal indirect, and minimal follow-up correctly
- 3-turn add-car flow works: turn 1 asks year+zip, turn 2 acknowledges year and asks zip, turn 3 hands off
- Handoff phrases ("好的，收到了", "报价资料已整理好了") appear correctly for all flows

**Potential future stress points (not observed):**
- Mixed-intent messages (e.g. 出事了要拍什么 + payment failed 什么意思) — covered by complex adversarial pack
- Turn-2 flow pollution — not observed in current scenarios

---

## 5. Improvements made

| Area | Change |
|------|--------|
| **Eval notes** | Added "Issue likely at turn N" when handoff wrong or no handoff; "Good next-step guidance" for Normal |
| **Scenarios** | 7 new (SIM9–SIM15); total 15 |
| **CLI script** | `scripts/run_simulation_assistant_scenarios.py` — runs all 15, reports Normal/Needs review/Off-flow |
| **Guardrail** | Step 8: Simulation Assistant scenarios (15 scripted) |
| **Runbook** | Updated §5b with 15 scenarios, CLI script, eval note hints |

---

## 6. Demo + QA proof

- **Normal:** SIM3 Add car (Chinese) — asks year+zip, handoff "报价资料已整理好了"
- **Normal:** SIM9 Notice correction — "我其实已经付了" → handoff "好的，收到了"
- **Needs review:** (None observed; eval would show "Issue likely at turn N" if present)
- **Off-flow:** (None observed; would show "First reply too generic" if generic fallback)
- **3-turn:** SIM15 — turn 1 model, turn 2 year, turn 3 zip+delivery → handoff at turn 3

---

## 7. Validation summary

| Check | Result |
|-------|--------|
| `npm run build` (ui/) | PASS |
| `run_simulation_assistant_scenarios.py` | 15/15 Normal |
| `guardrail_inbox_triage.sh` | PASS (including step 8) |
| `run_inbox_triage_scenarios.py` | 49/49 passed |
| `run_multi_turn_simulations.py` | 29 strong |
| `run_adversarial_simulation.py` | 27 strong |
| `run_complex_adversarial_simulation.py` | 22 strong, 1 acceptable |

---

## 8. Redeploy readiness

| Item | Status |
|------|--------|
| Change set stable | Yes |
| Frontend redeploy | Yes — SimulationAssistant.tsx, scenario list |
| Backend redeploy | No — no backend changes |
| Redeploy order | Frontend only (Vercel) |
| Post-redeploy smoke | Run SIM1, SIM3, SIM5, SIM15 in Simulation Assistant |

---

## 9. Recommended next step

1. Redeploy frontend to Vercel
2. Before Chen Kui demo: run SIM1 (cancellation), SIM3 (add car), SIM5 (claim), SIM15 (3-turn) as quick sanity check
3. If new flows emerge, add 1–2 scenarios to `simulation_assistant_scenarios.json`

---

## 10. 中文或中英混合宏观总结

**这次仿真助手加强了什么：**
- 从 8 个场景扩展到 15 个，覆盖 notice 纠正、模糊「又发了」、add-car 部分信息、claim 对方跑了、renewal 间接说法、最小 follow-up、3 轮 add-car
- 评估标签增加「Issue likely at turn N」和「Good next-step guidance」，方便看出问题出在第几轮
- 新增 CLI 脚本 `run_simulation_assistant_scenarios.py`，可批量跑 15 个场景做 bug harvest
- 纳入 guardrail 第 8 步，CI/回归可自动跑

**新增了哪些最值钱场景：**
- SIM9 通知纠正（已付了）— 第二句纠正，验证 receipt 类 handoff
- SIM10 模糊「上次那个材料」— 考验上下文保持
- SIM11 add-car 部分信息 — 第一句有 year+model，第二句补 zip
- SIM12 claim 对方跑了没照片 — 考验 hit-and-run 场景
- SIM15 3 轮 add-car — 考验第三轮不丢上下文

**抓出了哪些真实 bug：**
- 本次 15 个场景全部 Normal，未发现 product bug
- 说明 rule-based triage 对当前场景覆盖较好

**修了哪些最重要的问题：**
- 无 product bug 需修
- 改进了 eval 可见性：问题出现时能标出「Issue likely at turn N」

**这次做完以后为什么值得重新部署到线上：**
- 仿真助手从 8 场景增至 15，覆盖更全
- 评估更清晰，方便 founder、Chen Kui、内部测试快速发现 flow 问题
- 对 demo 和 QA 都更有用

---

## 11. Practical simulation assistant checklist

| Action | How |
|--------|-----|
| **Start** | Customer Entry tab → Simulation Assistant |
| **Pick scenario** | Click one of 15 buttons |
| **Run** | Run simulation — injects turn 1, gets reply, then turn 2, etc. |
| **Step** | Next turn — run one more customer turn manually |
| **Auto-play** | Auto-play — ~1.8s between turns |
| **Reset** | Reset — clear replay; then Run again |
| **Labels** | Normal = on-flow, handoff OK. Needs review = slight issue. Off-flow = generic/wrong |
| **CLI** | `PYTHONPATH=. python3 scripts/run_simulation_assistant_scenarios.py` |
| **Suspicious** | Watch for: "Issue likely at turn N", "No handoff after expected turns", "First reply too generic" |
| **Demo vs QA** | Demo: run 3–5 core flows (SIM1, SIM3, SIM5, SIM15). QA: run all 15 before release |

---

## 12. Bug harvest summary

| Category | Count |
|----------|-------|
| Strongest new scenarios | SIM9 (notice correction), SIM10 (vague "already sent"), SIM15 (3-turn) |
| Most revealing scenarios | SIM14 (tricky minimal), SIM12 (hit-and-run no photos) |
| Bugs found | 0 |
| Bugs fixed | 0 (improved eval visibility instead) |
| What remains | Monitor for turn-2 flow pollution, mixed-intent edge cases |

---

## 13. Demo/QA walkthroughs

### 1. Normal — Add car (Chinese) SIM3

**Turns:**
1. 我买了台宝马X5，想问下保费多少钱
2. 2024年的，zip 90210，下周提车

**Result:** System asks year+zip; turn 2 handoff "报价资料已整理好了". Tag: Normal. Notes: Good next-step guidance, Handoff at expected turn.

**Viewer should notice:** Intent-specific ask, not generic; handoff when year+zip+delivery provided.

---

### 2. Normal — Notice correction SIM9

**Turns:**
1. 客户问：这个英文 notice 说 payment failed，我现在怎么办？
2. 我其实已经付了，需要发什么给你吗

**Result:** Turn 1 asks for notice/screenshot; turn 2 handoff "好的，收到了". Tag: Normal.

**Viewer should notice:** Second turn corrects (already paid); system hands off with verify-receipt, does not re-ask for payment.

---

### 3. Normal — Vague "already sent" SIM10

**Turns:**
1. UW follow up - need dec page. 客户说上周发过了
2. 就是上次那个材料，我又发了

**Result:** Turn 1 names dec page; turn 2 handoff "好的，收到了". Tag: Normal.

**Viewer should notice:** Vague "上次那个材料" preserved in context; handoff reflects verify-receipt.

---

### 4. Normal — 3-turn add-car SIM15

**Turns:**
1. 想加一台车，宝马X5
2. 2024年的
3. 90210，下周提车

**Result:** Turn 1 asks year+zip; turn 2 acknowledges "2024年的", asks zip; turn 3 handoff "报价资料已整理好了". Tag: Normal.

**Viewer should notice:** Turn 3 does not lose context; handoff at expected turn 3.

---

### 5. Off-flow (hypothetical) — would show

If first reply were "please provide more context" or "这段内容还不够完整" on a clear-intent flow, tag would be Off-flow / suspicious with notes: "Issue likely at turn 1", "First reply too generic for clear intent".

---

*End of report*
