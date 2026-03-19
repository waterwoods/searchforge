# Trial Kickoff Demo / Checklist Spec

**Sprint:** Broker Trial Kickoff Readiness Sprint  
**Created:** 2026-03-18  
**Purpose:** Define what founder should show in the first 5–10 minutes, what minimal case flows should be tested, and what should be confirmed before real broker usage begins.

---

## 1. Founder: First 5–10 Minutes Demo

| Step | Action | What to say |
|------|--------|-------------|
| 1 | Open /workbench/unified-intake | — |
| 2 | Click **Load founder demo queue** | "13个示例case，取消风险排第一" |
| 3 | Cancellation risk case opens first | "紧急，当天处理；Same-day action" |
| 4 | Reopen **missing document** from Recent cases | "缺材料，客户说发过了；核实收到" |
| 5 | Reopen **add-car quote** or **premium review** | "Collected chips 绿色，Still needed 橙色" |
| 6 | Optional: Simulation Assistant → SIM1 → SIM2 → SIM3 | "多轮对话，3个核心场景" |

**One-sentence:** "One paste → structured case. One next move. One draft to edit. No auto-send."

---

## 2. Minimal Case Flows to Test Before Kickoff

| Flow | How to test | Pass when |
|------|-------------|-----------|
| Load founder demo queue | Click button | 13 cases; cancellation opens first |
| SIM1 Cancellation risk | Simulation Assistant → Run SIM1 | 3-turn; urgency; Same-day action |
| SIM2 Missing document | Simulation Assistant → Run SIM2 | 3-turn; reopen from Recent; waiting_on |
| SIM3 Add-car quote | Simulation Assistant → Run SIM3 | 3-turn; Collected chips; handoff at turn 3 |
| Case focus visible | Open any case | Add car quote · Premium review · etc. |
| Your next move visible | Case card | One operational sentence, bold |
| Collected / Still needed | Chips | Green/orange |
| Copy case snapshot | Click button on case | Copies focus, next move, collected, still needed, draft |

---

## 3. What Must Be Confirmed Before Kickoff

| Check | How |
|-------|-----|
| trial_launch_check.sh PASS | Run script |
| Backend + UI up | run_demo_local.sh |
| Founder demo queue loads | Click button; verify 13 cases |
| SIM1, SIM2, SIM3 pass | Simulation Assistant |
| Observation log template ready | Copy from docs/trial/ |
| BROKER_TRIAL_ONE_PAGER ready | Print or on device |

---

## 4. What Can Remain Rough During First Trial

| Item | Why |
|------|-----|
| Evidence pack manual | No automated export for v1 |
| Full trial summary export | Defer |
| Inbox sync, OCR | Out of scope |
| Multi-tenant, auth | Out of scope |

---

## 5. What Would Block Kickoff

| Blocker | Action |
|---------|--------|
| trial_launch_check.sh FAIL | Fix guardrail, UI build, or missing docs |
| Backend 503 / embedding_warming | `bash scripts/restore_8001_readiness.sh` |
| Guardrail fails | Fix per script output |
| Missing observation log template | Copy from `docs/trial/TRIAL_OBSERVATION_LOG_TEMPLATE.md` |
| Missing fix-now queue | Copy from `docs/trial/FIX_NOW_QUEUE_TEMPLATE.md` |

---

*End of Trial Kickoff Demo / Checklist Spec*
