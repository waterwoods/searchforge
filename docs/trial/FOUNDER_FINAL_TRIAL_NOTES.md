# Founder Final Trial Notes

**Sprint:** Trial Execution Readiness + Last-Mile Hardening  
**Created:** 2026-03-18  
**Purpose:** What founder should inspect after this sprint, how to run the trial, what to say, what to watch for during the first few real conversations.

---

## 1. What to Inspect After This Sprint

| Item | Where | What to verify |
|------|-------|----------------|
| Trial package docs | `docs/trial/` | All 8 control docs exist |
| Pre-trial checklist | `FOUNDER_BROKER_TRIAL_RUNBOOK_SPEC.md` §1 | Run all 7 steps; trial_readiness_check PASS |
| Last-mile risks | `LAST_MILE_RISK_SPEC.md` | Know top 5 risks |
| Observation template | `TRIAL_OBSERVATION_LOG_TEMPLATE.md` | Ready to share with broker |
| Fix prioritization | `TRIAL_OBSERVATION_TO_ITERATION_SPEC.md` | Know fix now / next / defer |
| **Handoff order** | Smoke step 23 | "Your next move" appears first (before Recent customer messages) |

---

## 2. How to Run the Trial

### Before first broker meeting

1. Run `bash scripts/trial_readiness_check.sh` — must PASS
2. Run `bash scripts/run_demo_local.sh` — backend + frontend up
3. Open http://localhost:5173/workbench/unified-intake
4. Load founder demo queue — verify 13 cases
5. Run SIM1, SIM2, SIM3 — verify pass
6. Copy observation log template for broker
7. Read `BROKER_TRIAL_WORKFLOW_SPEC.md`

### During first meeting (setup + demo)

1. Say opening (30 sec) — see §3
2. Load founder demo queue
3. Show cancellation risk → missing doc → add-car
4. Show Simulation Assistant: SIM1 → SIM2 → SIM3
5. Give broker Day 1 checklist
6. Share observation log template

### During trial week

- Broker uses daily; founder checks in as needed
- Broker logs friction in observation template
- Post-trial: 5 value validation questions

---

## 3. What to Say

### Opening (Chinese)

> "这是一个加州汽车保险经纪助手。客户发来messy消息——微信、截图、通知——系统会整理成一个结构化case：有 urgency、下一步动作、收集了什么、还缺什么、草稿回复。你确认后再发，**不自动发送**。经纪保持控制。"

### Opening (English)

> "This turns messy customer messages into structured cases: urgency, next move, what's collected, what's still needed, draft reply. You review and send. No auto-send."

### One-sentence pilot offer

> 试用一个月：帮你把客户发来的messy消息整理成结构化case，有下一步动作、收集了什么、还缺什么、草稿回复。你确认后再发，不自动发送。

---

## 4. What to Watch For During First Few Real Conversations

| Watch for | Why |
|-----------|-----|
| **Broker hesitates at paste** | May not know what to paste; give example |
| **Broker ignores Collected chips** | May not trust; point out Human confirmation |
| **Broker rewrites draft completely** | Draft quality; note for iteration |
| **Broker can't find next move** | Visibility; may need UI tweak |
| **Broker confused on reopen** | Resume here; waiting_on clarity |
| **Talk to Agent flow** | If customer says "联系人工" — does it work? |
| **Correction / already_sent** | Does broker see when customer said "already sent"? |

---

## 5. If Something Goes Wrong

| Issue | Action |
|-------|--------|
| 503 / embedding_warming | `bash scripts/restore_8001_readiness.sh` |
| Guardrail fails | Fix per script output; see `docs/ANDY_IF_SOMETHING_GOES_WRONG.md` |
| Offline mode | Use Simulation Assistant; demo works with preset scenarios |
| Broker stuck | Switch to founder demo queue; show SIM1–SIM3 |

---

## 6. Post-Trial: Turn Observations into Next Work

1. Collect all daily log entries + 5 value validation answers
2. Fill **Friction Classification** table in `TRIAL_OBSERVATION_LOG_TEMPLATE.md`
3. Use `TRIAL_OBSERVATION_TO_ITERATION_SPEC.md` — classify, decide fix now/next/defer
4. Map each fix to scenario or backbone component (see spec §4)
5. Prioritize fix now first
6. Add to next sprint backlog with clear acceptance

**Quick reference:** Trust-breaking → fix now. High friction → fix next. Low → defer.

### Post-Trial Quick Checklist (One Page)

| Step | Action | Output |
|------|--------|--------|
| 1 | Copy observation log to `results/trial_logs/{broker}_{date}.md` | Stored log |
| 2 | Fill Friction Classification table (Date, Scenario, Observation, Category, Fix decision, Map to) | Classified list |
| 3 | For each Trust-breaking: map to component (triage, broker_next_step, UI) | Fix-now backlog |
| 4 | For each High: decide fix next or defer | Fix-next list |
| 5 | Add fix-now items to next sprint with acceptance criteria | Sprint ready |

---

*End of Founder Final Trial Notes*
