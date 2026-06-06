# Trial One Path — 7-Day Broker Trial

**Purpose:** ONE trial path for founders and brokers.  
**Founder setup:** [`FOUNDER_ONE_PATH.md`](./FOUNDER_ONE_PATH.md) § Trial  
**Broker playbook:** [`BROKER_TRIAL_PLAYBOOK.md`](./BROKER_TRIAL_PLAYBOOK.md)

> **Historical trial specs archived:** `docs/archive/p9_broker_surface/trial/`

---

## Before Day 0 — Founder checklist

```bash
bash scripts/trial_launch_check.sh    # must PASS
bash scripts/run_demo_local.sh        # or confirm production URL live
bash scripts/guardrail_inbox_triage.sh
```

**Prepare:**

- [ ] Copy [`trial/TRIAL_OBSERVATION_LOG_TEMPLATE.md`](./trial/TRIAL_OBSERVATION_LOG_TEMPLATE.md)
- [ ] Send broker [`BROKER_ONE_PAGER.md`](./BROKER_ONE_PAGER.md) + [`BROKER_TRIAL_PLAYBOOK.md`](./BROKER_TRIAL_PLAYBOOK.md)
- [ ] Confirm workbench URL (local or production)

**What to say (first 30 seconds):**

> 这是一个加州汽车保险经纪助手。客户发来 messy 消息，系统整理成结构化 case：urgency、下一步、收集了什么、还缺什么、草稿回复。你确认后再发，不自动发送。

---

## Day 0 — Kickoff

| Who | Action |
|-----|--------|
| **Founder** | Trial launch check PASS; send URL + one-pager + playbook |
| **Broker** | Open workbench; bookmark URL; read one-pager (5 min) |

**Founder inspects:**

- Load founder demo queue — 13 cases; cancellation first
- Run Simulation Assistant: Cancellation, Missing doc, Add-car (3 turns each)

---

## Day 1 — Learn + first real message

| Who | Action |
|-----|--------|
| **Broker** | Load demo queue; run 3 Simulation Assistant scenarios; paste 1 real message |
| **Founder** | Available for questions; no hovering |

**Broker watches for:** Case focus, Your next move, Collected, Still needed, Human confirmation

**Founder collects (if broker shares):**

- First impression (1 line)
- Any confusion (screenshot welcome)

---

## Day 3 — Real office use

| Who | Action |
|-----|--------|
| **Broker** | 2–3 real cases from the week; try reopen + paste follow-up |
| **Founder** | Check in (15 min call or async); review observation log |

**Collect per case:**

```
[Date] [Scenario] Friction: [one line]
[Date] [Scenario] Worked: [one line]
```

---

## Day 7 — Value validation + decision

| Who | Action |
|-----|--------|
| **Broker** | Answer 5 value questions (below) |
| **Founder** | Post-trial fix-now queue; pilot decision |

**5 value questions:**

1. Which scenario felt most useful to your office?
2. Which part still feels risky or not trustworthy?
3. Would this save you or your assistant time?
4. What would you want it to do next?
5. What would you be willing to try first in a pilot?

---

## Success criteria

| Signal | Evidence |
|--------|----------|
| **Understands product** | Can explain one-sentence value to colleague |
| **Sees office fit** | Names scenario they'd use Monday morning |
| **Trusts draft** | Would use draft as starting point (with edits) |
| **Time savings** | Says yes or "maybe" to Q3 with specific example |
| **Pilot interest** | Willing to try paid month or asks for pricing |

---

## Failure criteria

| Signal | Action |
|--------|--------|
| Can't explain what system does | Stop trial; fix messaging before retry |
| Output routinely wrong/unusable | Log cases → fix-now queue → engineering |
| Expected WeChat sync / auto-send | Reset expectations with one-pager; assess fit |
| Broker stops opening after Day 1 | Ask why; classify friction in observation log |

---

## Feedback collection

**During trial:** Broker adds notes to observation log (or WeChat voice/text to founder)

**Template fields:**

- Date, scenario, friction, what worked, broker confusion, value signal

**Store:** `results/trial_logs/{broker}_{date}.md`

**Post-trial:** Fill [`trial/FIX_NOW_QUEUE_TEMPLATE.md`](./trial/FIX_NOW_QUEUE_TEMPLATE.md) — fix now / next / defer

---

## Support escalation

| Level | Trigger | Response |
|-------|---------|----------|
| **L1** | Broker question on usage | Founder answers from BROKER_TRIAL_PLAYBOOK |
| **L2** | Case output wrong | Screenshot + case snapshot; founder logs for fix queue |
| **L3** | System down | `summarize_support_posture.sh`; broker uses Simulation Assistant |
| **L4** | Trust broken | Pause trial; fix before continuing |

---

## What to ignore

| Ignore | Why |
|--------|-----|
| 12 archived trial spec docs | TRIAL_ONE_PATH replaces them |
| Kickoff blueprint folder | Optional depth only |
| `/demo` RAG page | Not the trial product surface |
| SIM1–SIM15 IDs with broker | Use scenario names |
| Qdrant / vector status | Intake works without vectors |
| Demo queue count as analytics | Illustration only |

---

## Templates (keep using)

| Template | Path |
|----------|------|
| Observation log | [`trial/TRIAL_OBSERVATION_LOG_TEMPLATE.md`](./trial/TRIAL_OBSERVATION_LOG_TEMPLATE.md) |
| Fix-now queue | [`trial/FIX_NOW_QUEUE_TEMPLATE.md`](./trial/FIX_NOW_QUEUE_TEMPLATE.md) |

---

*End of trial one path*
