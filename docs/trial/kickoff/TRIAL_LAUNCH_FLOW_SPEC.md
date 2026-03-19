# Trial Launch Flow Spec

**Sprint:** Broker Trial Kickoff Readiness Sprint  
**Created:** 2026-03-18  
**Purpose:** Define the exact founder launch flow, broker day-1 flow, workbench review flow, and what should happen before, during, and after trial kickoff.

---

## 1. Founder Launch Flow (Before First Broker Meeting)

| Step | Action | Pass when |
|------|--------|-----------|
| 1 | Run `bash scripts/trial_launch_check.sh` | PASS |
| 2 | Run `bash scripts/run_demo_local.sh` | Backend 8001 + UI 5173 up |
| 3 | Open http://localhost:5173/workbench/unified-intake | Page loads |
| 4 | Click **Load founder demo queue** | 13 cases; cancellation opens first |
| 5 | Run SIM1, SIM2, SIM3 in Simulation Assistant | All pass |
| 6 | Copy `docs/trial/TRIAL_OBSERVATION_LOG_TEMPLATE.md` for broker | Ready to share |
| 7 | Bring `docs/trial/BROKER_TRIAL_ONE_PAGER.md` | Printed or on device |
| 8 | Read `docs/trial/FOUNDER_LAUNCH_NOTES.md` | Know what to say, inspect, watch for |

**Single command:** `bash scripts/trial_launch_check.sh` — runs readiness + prints checklist.

---

## 2. Broker Day-1 Flow

| Step | Action |
|------|--------|
| 1 | Open /workbench/unified-intake |
| 2 | Click **Load founder demo queue** — loads 13 demo cases |
| 3 | Open **Simulation Assistant** — run SIM1, SIM2, SIM3 |
| 4 | Paste one real customer message (or click "Need an example?") |
| 5 | Review Case focus, Your next move, Collected, Still needed |
| 6 | Edit draft reply; copy to client; update status |
| 7 | Record friction in observation log: `[Date] [Scenario] Friction: [one line]` |

**Source:** `docs/trial/BROKER_TRIAL_ONE_PAGER.md`

---

## 3. Workbench Review Flow (During Trial)

| Check | Where | What to verify |
|-------|-------|----------------|
| Case focus | Case card top | Add car quote · Premium review · etc. |
| Your next move | Case card, bold | One operational sentence |
| Collected / Still needed | Chips | Green/orange |
| Human confirmation | Badge | Gold when AI collected from conversation |
| Resume here | Reopen case | waiting_on + latest note |
| Correction / already_sent | Badge | Visible when applicable |

**Script:** `bash scripts/unified_intake_smoke_check.sh` — step 23: "Your next move" appears before Recent customer messages.

---

## 4. Before Trial Kickoff

- `trial_launch_check.sh` PASS
- Founder has run through checklist once
- Broker has BROKER_TRIAL_ONE_PAGER
- Observation log template ready
- Fix-now queue template ready (`docs/trial/FIX_NOW_QUEUE_TEMPLATE.md`)

---

## 5. During Trial Kickoff (First 5–10 Minutes)

1. Say opening (30 sec) — see FOUNDER_LAUNCH_NOTES
2. Load founder demo queue
3. Show cancellation risk case (opens first)
4. Reopen missing document from Recent cases
5. Reopen add-car quote or premium review
6. Show Simulation Assistant: SIM1 → SIM2 → SIM3
7. Give broker Day 1 checklist (BROKER_TRIAL_ONE_PAGER)
8. Share observation log template

---

## 6. After First 3–5 Real Conversations

| Collect | Format |
|---------|--------|
| Friction | `[Date] [Scenario] Friction: [one line]` |
| What worked | Brief note |
| Broker confusion | What confused, what they expected |
| Value signal | "Which scenario felt most useful?" |

**Store:** Add to observation log; post-trial fill Friction Classification table.

---

*End of Trial Launch Flow Spec*
