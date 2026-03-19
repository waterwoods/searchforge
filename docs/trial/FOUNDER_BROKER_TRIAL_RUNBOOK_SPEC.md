# Founder / Broker Trial Runbook Spec

**Sprint:** Trial Execution Readiness + Last-Mile Hardening  
**Created:** 2026-03-18  
**Purpose:** Define what founder does before trial, what founder says in setup/demo, what broker does daily, what to check in workbench, how to record friction.

---

## 1. Founder: Before Trial

### Pre-trial checklist (run in order)

**One command:** `bash scripts/founder_pre_trial_checklist.sh` — runs trial readiness + prints steps.

| Step | Action | Pass when |
|------|--------|-----------|
| 1 | `bash scripts/trial_readiness_check.sh` (or founder_pre_trial_checklist.sh) | PASS |
| 2 | `bash scripts/run_demo_local.sh` | Backend 8001 + UI 5173 up |
| 3 | Open http://localhost:5173/workbench/unified-intake | Page loads |
| 4 | Click **Load founder demo queue** | 13 cases load; cancellation opens first |
| 5 | Run SIM1, SIM2, SIM3 in Simulation Assistant | All pass |
| 6 | Copy `docs/trial/TRIAL_OBSERVATION_LOG_TEMPLATE.md` for broker | Ready to share |
| 7 | Read `docs/trial/BROKER_TRIAL_WORKFLOW_SPEC.md` | Know Day 1 flow |

### What to bring to first meeting

- URL (local or production)
- Broker Trial One-Pager (`docs/trial/BROKER_TRIAL_ONE_PAGER.md`)
- Observation log template (or link)

---

## 2. Founder: First Setup / Demo (What to Say)

### Opening (30 seconds)

**Chinese:**
> "这是一个加州汽车保险经纪助手。客户发来messy消息——微信、截图、通知——系统会整理成一个结构化case：有 urgency、下一步动作、收集了什么、还缺什么、草稿回复。你确认后再发，**不自动发送**。经纪保持控制。"

**English:**
> "This turns messy customer messages into structured cases: urgency, next move, what's collected, what's still needed, draft reply. You review and send. No auto-send."

### Demo path (2–3 minutes)

1. **Load founder demo queue** — "13个预设case，取消风险第一个"
2. **Cancellation risk** — Point to: Case focus, Your next move, Same-day action, Broker action required
3. **Reopen missing document** — Point to: waiting on, next contact, note
4. **Add-car quote** — Point to: Collected chips (year, model, zip)
5. **Simulation Assistant** — "SIM1 → SIM2 → SIM3，三个核心场景"

### What NOT to say

- "It is connected to email or WeChat"
- "It reads image uploads"
- "It automatically sends replies"
- "It manages full CRM"

---

## 3. Broker: Daily During Trial

| Step | Action |
|------|--------|
| 1 | Open `/workbench/unified-intake` |
| 2 | Paste customer message from WeChat/email into Customer Entry |
| 3 | Start case — system triages; may ask 1–2 follow-up questions |
| 4 | Continue multi-turn until handoff (or paste follow-up if customer replied elsewhere) |
| 5 | Review case card: Case focus, Your next move, Collected, Still needed |
| 6 | Edit draft if needed; copy to client; send via WeChat/email |
| 7 | Update status (Reviewing, Waiting Client, etc.); save follow-up target if waiting |
| 8 | Reopen from Recent cases when customer replies |

---

## 4. Assistant: What to Check in Workbench

| Item | What to check |
|------|---------------|
| **Queue triage** | Work now vs Waiting or parked |
| **Ready to act** | Has enough info to proceed |
| **Needs more info** | Should ask customer something |
| **Verify receipt** | Customer said sent; broker should confirm |
| **Follow-up memory** | waiting_on, next_contact_by, broker note |
| **Resume here** | When reopening: waiting on + latest note |
| **Human confirmation** | Gold badge when AI collected from conversation — broker should verify |

---

## 5. How to Record Friction Quickly

| When | Record |
|------|--------|
| **During trial** | In observation log: Date, scenario, what happened, one-line friction |
| **Post-trial** | 5 value validation questions; Summary: most used scenario, biggest friction |
| **For founder** | Use `docs/trial/TRIAL_OBSERVATION_TO_ITERATION_SPEC.md` — fix now / next / defer |

**Quick format:** `[Date] [Scenario] Friction: [one line]`

---

## 6. Day 1 Broker Checklist (First 15 Minutes)

- [ ] Open `/workbench/unified-intake`
- [ ] Click **Load founder demo queue**
- [ ] Review cancellation risk case
- [ ] Open Simulation Assistant
- [ ] Run SIM1 (Cancellation risk) — 3 turns
- [ ] Run SIM2 (Missing document) — 3 turns
- [ ] Run SIM3 (Add-car quote) — 3 turns
- [ ] Paste one real customer message (or "Need an example?")
- [ ] Start case → complete multi-turn if asked
- [ ] Verify: Case focus, Your next move, Collected, Still needed
- [ ] Edit draft; Copy client draft; Update status
- [ ] Reopen a case from Recent cases; verify Resume here

---

*End of Founder / Broker Trial Runbook Spec*
