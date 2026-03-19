# Final Pilot Confidence Sprint Report

**Sprint:** Final Pilot Confidence Sprint  
**Date:** 2026-03-13  
**Scope:** SearchForge → Chen Kui Insurance Unified Entry

---

## 1. Initial audit

### Strongest parts

- **Multi-turn trial flows:** All 5 top scenarios (SIM1–SIM6, SIM5) pass; SIM3 and SIM15 hand off at turn 3; SIM2 garaging clarification fixed in prior sprint.
- **Simulation Assistant:** 15/15 scenarios PASS; clear grouping (Recommended trial, Strongest multi-turn proof, Edge cases); evaluation tags; Run/Next turn/Reset.
- **State/field logic:** 7/7 audit cases pass; follow_up_type, collection_stage, collected_fields, still_needed_fields, human_confirmation all wired.
- **Structured outputs:** collected_fields, still_needed_fields, broker_next_step, case focus, human_confirmation visible in Workbench UI.
- **Release discipline:** Release checklist, deployment playbook, gotchas doc; clear pre/deploy/post steps.
- **Validation stack:** guardrail_inbox_triage.sh, run_inbox_triage_scenarios.py (49/49), run_simulation_assistant_scenarios.py (15/15), audit_state_field_accuracy.py (7/7).

### Weakest parts

- **Simulation Assistant replay:** Replay showed only text; trust signals (Collected, Still needed, Human confirmation) were not visible per turn — trial users could not see what the AI extracted during the demo.
- **LC-AC3 friction:** One guardrail case (add-car correction "我刚才说错了，是我老婆开那辆") hands off at turn 2 vs expected 3; marked Acceptable, not Weak.
- **Manual verification:** Post-deploy still requires browser check; no automated UI test for Simulation Assistant.

### Biggest confidence gaps

1. **Trust-signal visibility in Simulation Assistant** — Chen Kui running SIM3/SIM15 would not see Collected/Still needed chips in the replay; only the main case card shows them after handoff.
2. **Release checklist** — No explicit Simulation Assistant verification step when frontend changes affect it.

---

## 2. Chosen fix set

| Fix | Why highest-value |
|-----|-------------------|
| **Simulation Assistant replay trust signals** | Makes trial demo convincing: Chen Kui sees Collected/Still needed/Human confirmation per system turn; aligns replay with Workbench case card. |
| **Release checklist Simulation Assistant hint** | Ensures post-deploy verification when UI changes affect trial surface. |
| **CHEN_KUI_TRIAL_PACK usability note** | Documents that replay now shows trust signals; keeps trial pack accurate. |

---

## 3. Implementation changes made

| File | Change |
|------|--------|
| `ui/src/components/simulation/SimulationAssistant.tsx` | Added `humanizeStructuredField()`; replay system turns now show `Ready for handoff`, `Collected: …`, `Still needed: …`, `Human confirmation recommended` when `triageResult` present. |
| `docs/runbooks/RELEASE_CHECKLIST.md` | Added Post-Deploy item: "Simulation Assistant: run SIM3 or SIM15; verify replay shows Collected/Still needed when present". |
| `docs/CHEN_KUI_TRIAL_PACK.md` | Updated Simulation Assistant row: "replay shows Collected/Still needed/Human confirmation per turn". |

---

## 4. Before vs after

| Area | Before | After |
|------|--------|-------|
| **Simulation Assistant replay** | Text only | Text + trust-signal tags (Collected, Still needed, Human confirmation, Ready for handoff) per system turn |
| **Release checklist** | No Simulation Assistant check | Explicit SIM3/SIM15 replay verification when UI changed |
| **Trial pack doc** | "evaluation tags" | "evaluation tags; replay shows Collected/Still needed/Human confirmation per turn" |

**Still remains weak:** LC-AC3 correction scenario (acceptable friction); no automated UI test for Simulation Assistant; manual browser verification required for every deploy.

---

## 5. Validation summary

| Check | Result |
|-------|--------|
| `bash scripts/guardrail_inbox_triage.sh` | PASS |
| `PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py` | 49/49 passed |
| `PYTHONPATH=. python3 scripts/run_simulation_assistant_scenarios.py` | 15/15 Normal |
| `PYTHONPATH=. python3 scripts/audit_state_field_accuracy.py` | 7/7 passed |
| `cd ui && npm run build` | ✓ built in ~20s |

---

## 6. Release / redeploy readiness

| Component | Redeploy needed? | What to check online |
|-----------|------------------|----------------------|
| **Backend** | No | — |
| **Frontend** | **Yes** (Simulation Assistant UI change) | Open Simulation Assistant → run SIM3 or SIM15 → verify replay shows Collected/Still needed tags on system turns |

---

## 7. Final pilot confidence judgment

**Verdict: Ready for pilot confidence use**

- Top trial pack (SIM1→SIM2→SIM3→SIM6→SIM5) is strong; SIM15 proves multi-turn value.
- Multi-turn trust is high: turn 2/3 differentiation, garaging clarification, add-car progressive collection all work.
- Structured outputs are useful: Collected/Still needed, broker_next_step, case focus, human confirmation visible in Workbench and now in Simulation Assistant replay.
- Trust boundaries are visible: Human confirmation badge, Ready for handoff, per-turn trust signals in replay.
- Simulation Assistant is convincing: clear scenario order, evaluation tags, replay now shows what AI extracted.
- Release process is reliable: checklist, playbook, gotchas; Simulation Assistant verification step added.

**Remaining weakness:** One acceptable friction case (LC-AC3); manual browser verification required; no automated UI test for Simulation Assistant.

---

## 8. 中文宏观总结

**今天最后这轮最重要修了什么：**  
Simulation Assistant 的 Replay 现在会在每个系统回复下面显示 Collected、Still needed、Human confirmation 等 trust 标签，试用时能直接看到 AI 每轮提取了什么。

**哪几条 trial 主线现在最强：**  
1. 取消风险 (SIM1)  
2. 缺材料 (SIM2)  
3. 加车报价 (SIM3)  
4. 保费审核 (SIM6)  
5. 理赔 (SIM5)  
SIM15 是最强 multi-turn 证明。

**哪些 trust/state 信息现在最有用了：**  
Collected / Still needed 芯片、broker_next_step、case focus、Human confirmation recommended；Simulation Assistant replay 现在也显示这些。

**现在拿去试点是不是更放心了：**  
是。试用时 Chen Kui 能在 Simulation Assistant 里看到每轮 AI 提取了什么，和 Workbench case card 一致；release checklist 加了 Simulation Assistant 验证步骤。

**还剩下最大的短板：**  
LC-AC3 一个 acceptable 摩擦；每次 deploy 仍需人工浏览器验证；没有 Simulation Assistant 的自动化 UI 测试。

---

## 9. COPY/PASTE PILOT CONFIDENCE BLOCK

```
=== PILOT CONFIDENCE BLOCK ===

Strongest 3 trial flows
1. Cancellation risk (SIM1) — urgency, same-day action, turn 3 clarifies payment confusion
2. Missing document (SIM2) — operational follow-up, garaging clarification, verify receipt
3. Add-car quote (Chinese) (SIM3) — 3-turn progressive collection, handoff at turn 3, Collected chips

Strongest multi-turn proof
SIM15 Add-car 3-turn — model → year → zip+delivery; handoff at turn 3; proves turn-to-turn context preservation

Most useful trust signals
• Collected / Still needed chips (add-car, renewal, claim, missing-doc)
• broker_next_step (one operational sentence)
• Case focus (Add car quote, Premium review, etc.)
• Human confirmation recommended (when AI collected from conversation)
• Simulation Assistant replay now shows these per system turn

What is now safer/more trustworthy
• Simulation Assistant replay displays Collected, Still needed, Human confirmation, Ready for handoff per turn
• Release checklist includes Simulation Assistant verification when UI changes
• All 15 Simulation Assistant scenarios pass; 49 inbox triage scenarios pass; 7 state audit cases pass

What still needs manual human attention
• Browser verification after every frontend deploy
• LC-AC3 add-car correction scenario (acceptable friction)
• No automated UI test for Simulation Assistant

Ready for pilot feedback?
Yes. Top trial pack is strong; multi-turn quality is high; structured outputs and trust signals are visible; Simulation Assistant is convincing for demo and QA.
```

---

*End of report*
