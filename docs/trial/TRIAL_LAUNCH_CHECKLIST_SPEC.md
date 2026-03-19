# Trial Launch Checklist Spec

**Sprint:** Trial Launch + Fix-Now Queue Sprint  
**Created:** 2026-03-18  
**Purpose:** Define what founder must do before launch, what broker must understand before Day 1, what assistant/workbench check should happen, what "ready to launch" means, and what would block launch.

---

## 1. Founder: Before Launch (Must Complete)

| # | Action | Pass when |
|---|--------|-----------|
| 1 | Run `bash scripts/trial_launch_check.sh` | PASS |
| 2 | Run `bash scripts/run_demo_local.sh` | Backend 8001 + UI 5173 up |
| 3 | Open http://localhost:5173/workbench/unified-intake | Page loads |
| 4 | Click **Load founder demo queue** | 13 cases load; cancellation opens first |
| 5 | Run SIM1, SIM2, SIM3 in Simulation Assistant | All pass |
| 6 | Copy `docs/trial/TRIAL_OBSERVATION_LOG_TEMPLATE.md` for broker | Ready to share |
| 7 | Read `docs/trial/BROKER_TRIAL_ONE_PAGER.md` | Know Day 1 flow |
| 8 | Read `docs/trial/FOUNDER_LAUNCH_NOTES.md` | Know what to say, inspect, watch for |

**One command:** `bash scripts/trial_launch_check.sh` — runs readiness + prints checklist.

---

## 2. Broker: Before Day 1 (Must Understand)

| # | Item | Source |
|---|------|--------|
| 1 | What the product does | One-sentence: 试用一个月：帮你把messy消息整理成结构化case，有下一步动作、收集了什么、还缺什么、草稿回复。你确认后再发，不自动发送。 |
| 2 | 5 core scenarios | Cancellation risk, Missing doc, Add-car, Premium review, Claim intake |
| 3 | Day 1 flow | Open /workbench/unified-intake → Load founder demo queue → SIM1–SIM3 → paste real message |
| 4 | What to record | Observation log: Date, scenario, friction (one line) |
| 5 | Post-trial questions | 5 value validation questions |

**Deliverable:** `docs/trial/BROKER_TRIAL_ONE_PAGER.md` — broker-facing 一页说明.

---

## 3. Assistant / Workbench: Day-1 Checks

| Check | Where | Pass when |
|-------|-------|-----------|
| Case focus visible | Case card top | Add car quote · Premium review · etc. |
| Your next move visible | Case card, bold | One operational sentence |
| Collected / Still needed | Chips | Green/orange chips |
| Human confirmation | Badge | Gold when AI collected from conversation |
| Resume here | Reopen case | waiting_on + latest note |
| Correction / already_sent | Badge | Visible when applicable |

**Script:** `bash scripts/unified_intake_smoke_check.sh` — step 23: "Your next move" appears before Recent customer messages.

---

## 4. What "Ready to Launch" Means

- `trial_launch_check.sh` PASS
- Founder has run through checklist once
- Broker has BROKER_TRIAL_ONE_PAGER
- Observation log template ready
- Fix-now queue template ready (`docs/trial/FIX_NOW_QUEUE_TEMPLATE.md`)

---

## 5. What Would Block Launch

| Blocker | Action |
|---------|--------|
| trial_launch_check.sh FAIL | Fix guardrail, UI build, or missing docs |
| Backend 503 / embedding_warming | `bash scripts/restore_8001_readiness.sh` |
| Guardrail fails | Fix per script output |
| Missing observation log template | Copy from `docs/trial/TRIAL_OBSERVATION_LOG_TEMPLATE.md` |
| Missing fix-now queue | Create from `docs/trial/FIX_NOW_QUEUE_TEMPLATE.md` |

---

*End of Trial Launch Checklist Spec*
