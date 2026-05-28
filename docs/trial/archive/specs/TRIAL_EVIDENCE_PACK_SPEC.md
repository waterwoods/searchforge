# Trial Evidence Pack Spec

**Sprint:** Trial Launch + Fix-Now Queue Sprint  
**Created:** 2026-03-18  
**Purpose:** Define what evidence/logs should be captured during trial, what metrics matter most, what screenshots or notes should be saved, how to avoid noisy/unusable feedback, and what a useful evidence packet looks like after 1 week.

---

## 1. Evidence Types to Capture

| Type | When | Format | Storage |
|------|------|--------|---------|
| **Daily log** | Each trial day | Date, conversations, handoffs, scenario mix, notes | `results/trial_logs/{broker}_{date}.md` |
| **Friction entry** | When broker hits friction | `[Date] [Scenario] Friction: [one line]` | Same file |
| **Value validation** | Post-trial | 5 questions answered | Same file |
| **Friction classification** | Post-trial | #, Date, Scenario, Observation, Category, Fix decision | Same file |
| **Screenshots** | Optional, high-value moments | Case card, Collected chips, Human confirmation | `results/trial_logs/{broker}_{date}_screenshots/` |

---

## 2. Metrics to Track

| Metric | Definition | Why |
|--------|-------------|-----|
| Total conversations | Number of cases started | Volume |
| Total handoffs | Cases that reached enough_for_handoff | Value delivered |
| Scenario mix | Count per scenario (add-car, cancellation, etc.) | Which scenarios used |
| Most used scenario | Highest count | What broker values |
| Biggest friction | Single most impactful friction | Fix-now priority |
| Would use again | Y/N | Trial success signal |

---

## 3. What Screenshots or Notes to Save (Optional)

| Moment | What to capture | Why |
|--------|-----------------|-----|
| First handoff | Case card with Your next move, Collected, Still needed | Baseline quality |
| Human confirmation | Gold badge visible | Trust boundary |
| Correction / already_sent | Badge visible | Context visibility |
| Resume here | Reopen context | Follow-up continuity |
| Broker confusion | Note: what confused | Fix-now input |

**Avoid:** Screenshots of every case; noisy/unstructured notes.

---

## 4. How to Avoid Noisy/Unusable Feedback

| Anti-pattern | Better approach |
|--------------|-----------------|
| Vague "didn't work" | One-line: "Add-car asked for zip again after I gave it" |
| Feature requests during trial | Capture; classify as Defer |
| Emotional only | Add: what happened, what broker expected |
| No scenario ID | Include: SIM1, add-car, cancellation, etc. |

**Rule:** Each friction entry should be actionable: scenario + what happened + one line.

---

## 5. What a Useful Evidence Packet Looks Like After 1 Week

| Section | Content |
|---------|---------|
| **Summary** | Total conversations, handoffs, most used scenario, biggest friction, would use again |
| **Daily log** | 5 rows: Date, conversations, handoffs, scenario mix, notes |
| **Value validation** | 5 answers |
| **Friction classification** | Table: #, Date, Scenario, Observation, Category, Fix decision, Map to |
| **Fix-now queue** | Filled from Friction Classification (Trust-breaking, High → fix now/next) |

**Output:** `results/trial_logs/{broker}_{trial_end_date}_evidence_pack.md` — single file for post-trial sprint planning.

---

*End of Trial Evidence Pack Spec*
