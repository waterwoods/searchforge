> **HISTORICAL / ARCHIVE — P9 Broker Surface Collapse (2026-05-30)**
> **Read instead:** [`docs/TRIAL_ONE_PATH.md`](../../../TRIAL_ONE_PATH.md), [`docs/BROKER_TRIAL_PLAYBOOK.md`](../../../BROKER_TRIAL_PLAYBOOK.md)

# Broker Trial Workflow Spec

**Sprint:** Real Broker Trial Package Sprint  
**Created:** 2026-03-18

---

## 1. How the Broker Uses the System During Trial

### Daily workflow

1. **Open** `/workbench/unified-intake` (or production URL)
2. **Paste** customer message from WeChat/email into Customer Entry
3. **Start case** — system triages, may ask 1–2 follow-up questions
4. **Continue** multi-turn until handoff (or paste follow-up if customer replied elsewhere)
5. **Review** case card: Case focus, Your next move, Collected, Still needed
6. **Edit** draft if needed; copy to client; send via WeChat/email
7. **Update** status (Reviewing, Waiting Client, etc.); save follow-up target if waiting
8. **Reopen** from Recent cases when customer replies

---

## 2. How to Review Handoff Cases

| Step | Action |
|------|--------|
| 1 | Read **Case focus** — what type of case |
| 2 | Read **Your next move** — one operational sentence |
| 3 | Check **Collected** — what customer already provided (do not re-ask) |
| 4 | Check **Still needed** — what to ask or verify next |
| 5 | Check **Human confirmation recommended** — when AI collected from conversation, broker should verify |
| 6 | Edit **Client reply draft** — confirm tone and content |
| 7 | Copy to client — send via WeChat/email |

---

## 3. What to Inspect in Workbench

| Item | What to check |
|------|---------------|
| **Queue triage** | Work now vs Waiting or parked |
| **Ready to act** | Has enough info to proceed |
| **Needs more info** | Should ask customer something |
| **Verify receipt** | Customer said sent; broker should confirm |
| **Follow-up memory** | waiting_on, next_contact_by, broker note |
| **Resume here** | When reopening: waiting on + latest note |

---

## 4. What to Do After Customer Handoff

1. **Act** on the next move (call carrier, verify receipt, send quote, etc.)
2. **Update status** when done or waiting
3. **Save follow-up** if waiting on customer/carrier
4. **Add broker note** for context when reopening
5. **Paste new message** when customer replies — click "Update with new customer message"

---

## 5. Feedback to Record During Trial

- Which scenarios felt most useful
- Which parts felt risky or confusing
- Whether draft was editable vs needed full rewrite
- Whether Collected/Still needed reduced re-asking
- Any bugs or unexpected behavior

---

## 6. Trial Day 1 Checklist (Broker)

**Before starting:**
- [ ] Open `/workbench/unified-intake` (local: http://localhost:5173/workbench/unified-intake)
- [ ] Click **Load founder demo queue** — seeds 13 demo cases; cancellation risk opens first

**First 15 minutes:**
- [ ] Review cancellation risk case — see urgency, Same-day action, Broker action required
- [ ] Open **Simulation Assistant** (sidebar)
- [ ] Run SIM1 (Cancellation risk) — 3 turns; watch handoff at turn 2
- [ ] Run SIM2 (Missing document) — 3 turns; see dec page sent, garaging clarification
- [ ] Run SIM3 (Add-car quote) — 3 turns; see Collected chips at handoff

**First real case:**
- [ ] Click "Need an example?" or paste a real customer message
- [ ] Click **Start case** — complete multi-turn if system asks
- [ ] Verify: Case focus, Your next move, Collected, Still needed
- [ ] Edit draft if needed; click **Copy client draft** — paste into WeChat/email
- [ ] Update status (Reviewing / Waiting Client)
- [ ] Save follow-up target if waiting on customer
- [ ] Add one broker note

**Reopen flow:**
- [ ] Click a case in Recent cases — verify saved state loads
- [ ] Check "Resume here" shows waiting on + latest note
- [ ] Paste new customer message in "Paste new customer follow-up" — click Update

---

## 7. Observation Log

Use [TRIAL_OBSERVATION_LOG_TEMPLATE.md](TRIAL_OBSERVATION_LOG_TEMPLATE.md) to record daily conversations, handoffs, scenario mix, and post-trial feedback.

---

*End of Broker Trial Workflow Spec*
