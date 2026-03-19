# Simulation Assistant Deep Trial Scenarios Sprint Report

**Sprint:** Chen Kui Insurance Unified Entry — Simulation Assistant Deep Trial Scenarios
**Date:** 2026-03-12

---

## 1. Top scenario selection

**Chosen top 5 trial scenarios (in order):**

| # | ID | Scenario | Turns | Why |
|---|-----|----------|-------|-----|
| 1 | SIM1 | Cancellation risk | 3 | Urgency, same-day action; most obvious "must act" value |
| 2 | SIM2 | Missing document | 3 | Operational, "client says already sent" — real office pain |
| 3 | SIM3 | Add-car quote (Chinese) | 3 | Revenue, multi-turn; handoff at turn 3; Collected chips |
| 4 | SIM6 | Premium review | 3 | Retention, repetitive office work |
| 5 | SIM5 | Claim intake | 3 | First-response guidance; accident + hit-and-run |

**Strongest multi-turn proof:** SIM15 Add-car 3-turn — proves turn-to-turn context preservation; handoff at turn 3.

---

## 2. Depth audit

| Scenario | Before | After | Handoff timing |
|----------|--------|-------|----------------|
| SIM1 Cancellation risk | 2 turns | 3 turns | Backend hands off at turn 2; turn 3 shows clarification value |
| SIM2 Missing document | 2 turns | 3 turns | Backend hands off at turn 2; turn 3 asks what to send |
| SIM3 Add-car quote | 2 turns | 3 turns | **Handoff at turn 3** — true 3-turn proof |
| SIM5 Claim intake | 2 turns | 3 turns | Backend hands off at turn 2; turn 3 asks what matters most |
| SIM6 Premium review | 2 turns | 3 turns | Backend hands off at turn 2; turn 3 asks if removing vehicle helps |
| SIM15 Add-car 3-turn | 3 turns | 3 turns | **Handoff at turn 3** — strongest multi-turn proof |

**Finding:** SIM3 and SIM15 are the only scenarios where the backend hands off at turn 3. The others hand off at turn 2 but now have 3 turns in the replay — each turn adds visible value (clarification, next-step ask).

---

## 3. Scenario deepening changes

| Scenario | New turn structure |
|----------|---------------------|
| **SIM1** | T1: vague notice question → T2: sent screenshot → T3: clarifies payment confusion + asks what matters most |
| **SIM2** | T1: need dec+garaging, client said sent → T2: dec resent, garaging missing → T3: asks what garaging proof means + what to send |
| **SIM3** | T1: vague quote ask → T2: year → T3: zip+delivery + asks if enough |
| **SIM5** | T1: accident → T2: hit-and-run, no photos → T3: asks what matters most |
| **SIM6** | T1: premium too high → T2: sent bill → T3: asks if removing vehicle helps + what office reviews first |

---

## 4. Replay/value clarity improvements

- **Section label:** "Recommended trial (Chen Kui)" → "Recommended trial (3–4 turn)"
- **Multi-turn section:** "Multi-turn depth (3+ turns)" → "Strongest multi-turn proof"
- **Trial tip:** "Top 5 are 3-turn deep. Run Cancellation risk → Missing document → Add-car quote first. SIM15 = strongest multi-turn proof."
- **Scenario notes:** Each top scenario now includes "Proves:" and turn-level value (e.g. "Turn 3 clarifies payment confusion")
- **Eval notes:** When 3+ turns and Normal, eval shows "Shows N-turn conversation value"

---

## 5. Trial results

| Check | Result |
|-------|--------|
| `run_simulation_assistant_scenarios.py` | 15/15 PASS |
| `guardrail_inbox_triage.sh` | PASS |
| `run_inbox_triage_scenarios.py` | 49/49 passed |
| `run_multi_turn_simulations.py` | 38/38 strong |
| `unified_intake_smoke_check.sh` | PASS |
| `npm run build` | PASS |

---

## 6. Final top-trial order

**Best 3-scenario order:** SIM1 → SIM2 → SIM3

1. Cancellation risk
2. Missing document
3. Add-car quote (Chinese)

**Best 5-scenario order:** SIM1 → SIM2 → SIM3 → SIM6 → SIM5

1. Cancellation risk
2. Missing document
3. Add-car quote (Chinese)
4. Premium review
5. Claim intake

**Strongest multi-turn proof:** SIM15 Add-car 3-turn

---

## 7. Validation summary

All validation commands pass. Product remains stable.

---

## 8. Redeploy readiness

| Item | Status |
|------|--------|
| Change set stable | Yes |
| Frontend redeploy | Yes — SimulationAssistant.tsx, config |
| Backend redeploy | No — config only |
| Redeploy order | Frontend only (Vercel) |
| Post-redeploy smoke | Open Simulation Assistant; verify "Recommended trial (3–4 turn)" section; run SIM1, SIM3, SIM15 |

---

## 9. Recommended next step

1. Redeploy frontend to Vercel
2. Before Chen Kui trial: run SIM1, SIM2, SIM3, SIM15 as quick sanity check
3. Founder should open Simulation Assistant first; run top 3 scenarios in order

---

## 10. 中文或中英混合宏观总结

**现在最强的 3–5 个 trial 场景是不是已经放到顶部？** 是。Recommended trial (3–4 turn) 在最上面，5 个场景按 trial_order 排列。

**它们现在有没有真正做到 3–4 轮？** 是。5 个场景都是 3-turn；SIM3 和 SIM15 的 handoff 在 turn 3，其他在 turn 2 但 replay 显示 3 轮对话。

**哪个场景是最强的 multi-turn proof？** SIM15 Add-car 3-turn。model → year → zip+delivery，handoff 在 turn 3，证明 turn-to-turn context preservation。

**这次修了什么？** 把 top 5 从 2-turn 加深到 3-turn；section 改名 "Recommended trial (3–4 turn)"；SIM15 单独成组 "Strongest multi-turn proof"；每个 scenario 的 notes 加了 "Proves:" 和 turn 级价值说明。

**为什么这一步最值钱？** Chen Kui 试用时能立刻看到多轮对话价值；replay 显示 3 轮，每轮都有意义；SIM3/SIM15 证明系统能在 turn 3 才 handoff，不是一上来就 generic fallback。

---

## 11. Practical top-trial checklist

| Action | How |
|--------|-----|
| **Top scenarios** | Recommended trial (3–4 turn): SIM1, SIM2, SIM3, SIM6, SIM5 |
| **Best 3-scenario order** | SIM1 → SIM2 → SIM3 |
| **Best 5-scenario order** | SIM1 → SIM2 → SIM3 → SIM6 → SIM5 |
| **Strongest multi-turn proof** | SIM15 Add-car 3-turn |
| **Watch for** | Case focus, Your next move, Collected/Still needed, handoff at expected turn, "Shows 3-turn conversation value" in eval |

---

## 12. Depth-gap summary

| Category | Before | After |
|----------|--------|-------|
| **Top 5 depth** | All 2-turn | All 3-turn |
| **Handoff at turn 3** | Only SIM15 | SIM3 + SIM15 |
| **Replay value** | Generic notes | "Proves:" + turn-level value |
| **Section label** | "Recommended trial (Chen Kui)" | "Recommended trial (3–4 turn)" |
| **Remains weak** | — | Backend hands off at turn 2 for SIM1/SIM2/SIM5/SIM6; turn 3 still visible in replay |

---

## 13. COPY/PASTE TOP-TRIAL BLOCK

```
=== Simulation Assistant — Recommended Trial (3–4 turn) ===

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

Strongest multi-turn proof
• Add-car 3-turn (SIM15) — proves turn-to-turn context preservation; handoff at turn 3

What each top scenario proves
• Cancellation risk: urgency + clarification; turn 3 clarifies payment confusion
• Missing document: structured follow-up; turn 3 asks what to send
• Add-car quote: collects year/model/zip across 3 turns; handoff at turn 3
• Premium review: retention-style; turn 3 asks if removing vehicle helps
• Claim intake: first-response guidance; turn 3 asks what matters most
• Add-car 3-turn (SIM15): strongest proof of multi-turn value
```

---

*End of report*
