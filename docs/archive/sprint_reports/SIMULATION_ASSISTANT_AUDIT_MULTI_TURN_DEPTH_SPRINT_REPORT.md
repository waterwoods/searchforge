# Simulation Assistant Audit + Multi-Turn Depth Gap Sprint Report

**Sprint:** Chen Kui Insurance Unified Entry — Simulation Assistant Audit + Multi-Turn Depth Gap
**Date:** 2026-03-12

---

## 1. Current audit

**Verdict:** Good but partial — usable but uneven for trial clarity.

| Area | Status | Notes |
|------|--------|-------|
| Scenario names | **Partial** | "Notice / Cancellation" did not match trial "Cancellation risk"; "Renewal / Premium" vs "Premium review"; "Add car" vs "Add-car quote" |
| Trial language alignment | **Gap** | Founder expects "Cancellation risk" — not visible in scenario list |
| Scenario ordering | **Flat** | 15 scenarios in one list; no recommended section; strongest buried |
| Multi-turn visibility | **Gap** | Only SIM15 is 3-turn; buried at bottom; no explicit "multi-turn depth" section |
| Replay/result clarity | **Good** | Eval tags (Normal/Needs review/Off-flow) and notes work |
| Business value in eval | **Partial** | Notes say "Good next-step guidance" but don't tie to business value explicitly |

**Classification:** Confusing in important ways — naming mismatch and flat list hurt demo/trial usefulness.

---

## 2. Biggest gaps

| Gap | Current problem | Where | Why it hurts | Worth fixing |
|-----|-----------------|-------|---------------|--------------|
| **Naming mismatch** | "Notice / Cancellation" vs "Cancellation risk" | SIM1 title | Founder expects "Cancellation risk"; trial pack uses it consistently | Yes |
| **Trial language** | "Renewal / Premium" vs "Premium review"; "Add car" vs "Add-car quote" | SIM3, SIM6 | Chen Kui trial pack uses different terms | Yes |
| **Flat list** | 15 scenarios in one long list | Scenario card | Hard to find right scenario quickly | Yes |
| **Strongest not surfaced** | Recommended trial order buried in small tip text | Trial tip | Founder/Chen Kui can't quickly see "run these 5 first" | Yes |
| **3–4 turn not obvious** | SIM15 at bottom; no section label | Scenario list | Multi-turn value not visible enough | Yes |
| **Replay value note** | Eval notes don't say "Proves: urgency" etc. | Evaluation card | Business value not explicit | Deferred (low risk) |

---

## 3. Best packaging approach

**Chosen:**

1. **Recommended trial (Chen Kui)** — SIM1, SIM2, SIM3, SIM5, SIM6 in trial order (1–5)
2. **Multi-turn depth (3+ turns)** — SIM15 Add-car 3-turn
3. **Edge cases / QA** — SIM4, SIM7, SIM8, SIM9, SIM10, SIM11, SIM12, SIM13, SIM14

**Renames:**
- SIM1: "Notice / Cancellation" → **Cancellation risk**
- SIM3: "Add car (Chinese)" → **Add-car quote (Chinese)**
- SIM6: "Renewal / Premium" → **Premium review**
- SIM15: "Add car 3-turn (stress turn 3)" → **Add-car 3-turn (multi-turn depth)**

---

## 4. Multi-turn depth review

| Scenario | Turns | Visible depth | Later-turn value |
|----------|-------|---------------|------------------|
| SIM1–SIM14 | 2 | 2-turn only | Turn 2 adds info; handoff at turn 2 |
| SIM15 | 3 | 3-turn | Turn 1 model → Turn 2 year → Turn 3 zip+delivery; handoff at turn 3 |

**Finding:** Only SIM15 demonstrates 3-turn depth. Backend has more 3-turn variants (MT13, MT19) but they are not in the Simulation Assistant. SIM15 is sufficient for trial proof of multi-turn value. Moving it to a dedicated "Multi-turn depth" section makes it visible.

**Gap addressed:** SIM15 now in its own section with explicit "multi-turn depth" label.

---

## 5. Improvements made

| Area | Change |
|------|--------|
| **Config** | Added `section`, `trial_order`, `recommended_trial_order`; renamed SIM1, SIM3, SIM6, SIM15 |
| **Component** | Load from config; group scenarios into Recommended / Multi-turn / Edge cases |
| **Trial tip** | "Run Cancellation risk → Missing document → Add-car quote first. SIM15 shows 3-turn depth." |
| **Docs** | CHEN_KUI_TRIAL_PACK, UNIFIED_INTAKE_MVP_RUNBOOK updated with new names and grouping |

---

## 6. Online trial view recommendation

**Best 3 scenarios to show first:** SIM1 → SIM2 → SIM3
1. Cancellation risk
2. Missing document
3. Add-car quote (Chinese)

**Best 5 scenarios if time allows:** SIM1 → SIM2 → SIM3 → SIM6 → SIM5
1. Cancellation risk
2. Missing document
3. Add-car quote (Chinese)
4. Premium review
5. Claim intake

**Multi-turn proof:** SIM15 Add-car 3-turn (multi-turn depth)

**What founder should notice:**
- Recommended trial section at top
- Scenario names match trial pack
- SIM15 in "Multi-turn depth" section — run it to prove 3-turn value

---

## 7. Validation summary

| Check | Result |
|-------|--------|
| `npm run build` (ui/) | PASS |
| `run_simulation_assistant_scenarios.py` | 15/15 Normal |
| `guardrail_inbox_triage.sh` | PASS |
| `run_inbox_triage_scenarios.py` | Pass |
| `run_multi_turn_simulations.py` | Pass |
| `unified_intake_smoke_check.sh` | PASS |

---

## 8. Redeploy readiness

| Item | Status |
|------|--------|
| Change set stable | Yes |
| Frontend redeploy | Yes — SimulationAssistant.tsx, config import |
| Backend redeploy | No — config only; Python script reads same config |
| Redeploy order | Frontend only (Vercel) |
| Post-redeploy smoke | Open Simulation Assistant; verify Recommended trial section; run SIM1, SIM3, SIM15 |

---

## 9. Recommended next step

1. Redeploy frontend to Vercel
2. Before Chen Kui trial: run SIM1, SIM2, SIM3, SIM15 as quick sanity check
3. If new flows emerge, add 1–2 scenarios to config; keep section/trial_order in sync

---

## 10. 中文或中英混合宏观总结

**Simulation Assistant 最大的不足：**
- 命名和 trial pack 不一致（Notice/Cancellation vs Cancellation risk）
- 15 个场景平铺，没有「推荐试用」分组
- 3 轮 add-car 场景 (SIM15) 埋在最后，多轮价值不明显

**这次修了什么：**
- 改名：SIM1 → Cancellation risk，SIM3 → Add-car quote (Chinese)，SIM6 → Premium review
- 分组：Recommended trial (Chen Kui) / Multi-turn depth / Edge cases
- SIM15 单独成组，标题改为 Add-car 3-turn (multi-turn depth)

**修完以后最强的 3–5 个场景：**
1. Cancellation risk — 紧急、当天行动
2. Missing document — 缺材料跟进
3. Add-car quote (Chinese) — 加车报价、Collected chips
4. Premium review — 续保/保费
5. Claim intake — 事故 intake
+ SIM15 Add-car 3-turn — 证明多轮对话价值

**为什么这一步重要：**
- Chen Kui 试用时能快速找到对的场景
- 命名和业务语言一致，founder 更容易信任
- 3 轮场景单独展示，多轮价值更明显

---

## 11. Practical Simulation Assistant checklist

| Action | How |
|--------|-----|
| **Top scenarios** | Recommended trial (Chen Kui): SIM1, SIM2, SIM3, SIM5, SIM6 |
| **Names to use** | Cancellation risk, Missing document, Add-car quote (Chinese), Premium review, Claim intake |
| **Best 3-scenario order** | SIM1 → SIM2 → SIM3 |
| **Best 5-scenario order** | SIM1 → SIM2 → SIM3 → SIM6 → SIM5 |
| **Multi-turn proof** | SIM15 Add-car 3-turn |
| **Watch for** | Case focus, Your next move, Collected/Still needed, handoff at expected turn |

---

## 12. Gap summary

| Category | Before | After |
|----------|--------|-------|
| **Naming** | Notice/Cancellation, Renewal/Premium, Add car | Cancellation risk, Premium review, Add-car quote |
| **Depth** | SIM15 buried; no section | Multi-turn depth section; SIM15 prominent |
| **Replay/value** | Eval notes generic | Same (deferred explicit "Proves:" notes) |
| **Fixed** | Renames, grouping, trial order, trial tip | Done |
| **Remains** | Eval could add "Proves: urgency" style notes | Low priority |

---

## 13. COPY/PASTE TRIAL-LABEL BLOCK

```
=== Simulation Assistant — Recommended Trial ===

Best 3-scenario order
1. Cancellation risk (SIM1)
2. Missing document (SIM2)
3. Add-car quote (Chinese) (SIM3)

Best 5-scenario order
1. Cancellation risk (SIM1)
2. Missing document (SIM2)
3. Add-car quote (Chinese) (SIM3)
4. Premium review (SIM6)
5. Claim intake (SIM5)

Multi-turn depth
• Add-car 3-turn (multi-turn depth) (SIM15) — proves 3-turn conversation value

What each scenario proves
• Cancellation risk: prioritizes urgent follow-up; same-day action
• Missing document: structured follow-up; verify receipt
• Add-car quote: collects year/model/zip; broker sees Collected chips
• Premium review: retention-style; repetitive office work
• Claim intake: first-response guidance; accident + hit-and-run
• Add-car 3-turn: multi-turn intake; handoff at turn 3
```

---

*End of report*
