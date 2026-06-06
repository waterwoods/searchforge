> **HISTORICAL / ARCHIVE — P9 Broker Surface Collapse (2026-05-30)**
> **Read instead:** [`docs/TRIAL_ONE_PATH.md`](../../../TRIAL_ONE_PATH.md), [`docs/BROKER_TRIAL_PLAYBOOK.md`](../../../BROKER_TRIAL_PLAYBOOK.md)

# Founder Launch Notes

**Sprint:** Trial Launch + Fix-Now Queue Sprint  
**Created:** 2026-03-18  
**Purpose:** What founder should do immediately before the first broker trial, what to say, what to inspect on Day 1, and what to collect after the first 3–5 real conversations.

---

## 1. Immediately Before First Broker Trial

| Step | Action |
|------|--------|
| 1 | Run `bash scripts/trial_launch_check.sh` — must PASS |
| 2 | Run `bash scripts/run_demo_local.sh` — backend + frontend up |
| 3 | Open http://localhost:5173/workbench/unified-intake |
| 4 | Load founder demo queue — verify 13 cases; cancellation opens first |
| 5 | Run SIM1, SIM2, SIM3 in Simulation Assistant |
| 6 | Copy `docs/trial/TRIAL_OBSERVATION_LOG_TEMPLATE.md` for broker |
| 7 | Bring `docs/trial/BROKER_TRIAL_ONE_PAGER.md` (or print) |
| 8 | Read this file (FOUNDER_LAUNCH_NOTES) |

---

## 2. What to Say (First 30 Seconds)

**Chinese:**
> "这是一个加州汽车保险经纪助手。客户发来messy消息——微信、截图、通知——系统会整理成一个结构化case：有 urgency、下一步动作、收集了什么、还缺什么、草稿回复。你确认后再发，**不自动发送**。经纪保持控制。"

**English:**
> "This turns messy customer messages into structured cases: urgency, next move, what's collected, what's still needed, draft reply. You review and send. No auto-send."

**One-sentence pilot offer:**
> 试用一个月：帮你把客户发来的messy消息整理成结构化case，有下一步动作、收集了什么、还缺什么、草稿回复。你确认后再发，不自动发送。

---

## 3. What to Inspect on Day 1

| Item | Where | What to verify |
|------|-------|----------------|
| Case focus | Case card top | Add car quote · Premium review · etc. |
| Your next move | Case card, bold | One operational sentence |
| Collected / Still needed | Chips | Green/orange |
| Human confirmation | Badge | Gold when AI collected |
| Resume here | Reopen case | waiting_on + latest note |
| Load founder demo queue | Button | 13 cases; cancellation first |

---

## 4. What to Collect After First 3–5 Real Conversations

| Collect | Format |
|---------|--------|
| Friction | `[Date] [Scenario] Friction: [one line]` |
| What worked | Brief note |
| Broker confusion | What confused, what they expected |
| Value signal | "Which scenario felt most useful?" |

**Store:** Add to observation log; post-trial fill Friction Classification table.

---

## 5. If Something Goes Wrong

| Issue | Action |
|-------|--------|
| 503 / embedding_warming | `bash scripts/restore_8001_readiness.sh` |
| Guardrail fails | Fix per script output |
| Broker stuck | Switch to founder demo queue; show SIM1–SIM3 |
| Offline mode | Use Simulation Assistant |

---

## 6. Post-Trial: Fix-Now Queue

1. Copy observation log to `results/trial_logs/{broker}_{date}.md`
2. Fill Friction Classification table
3. Use `docs/trial/FIX_NOW_QUEUE_SPEC.md` — fix now / next / defer
4. Copy `docs/trial/FIX_NOW_QUEUE_TEMPLATE.md`; fill and save to results/trial_logs
5. Add fix-now items to next sprint backlog

---

*End of Founder Launch Notes*
