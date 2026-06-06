> **HISTORICAL / ARCHIVE — P9 Broker Surface Collapse (2026-05-30)**
> **Read instead:** [`docs/TRIAL_ONE_PATH.md`](../../../TRIAL_ONE_PATH.md), [`docs/BROKER_TRIAL_PLAYBOOK.md`](../../../BROKER_TRIAL_PLAYBOOK.md)

# Trial Observation-to-Iteration Spec

**Sprint:** Trial Execution Readiness + Last-Mile Hardening  
**Created:** 2026-03-18  
**Purpose:** Define what observations should be captured, how to categorize them, how to decide fix now / next / defer, how to map real trial feedback back to scenario or backbone work.

---

## 1. What Observations Should Be Captured

| Type | Example | When |
|------|---------|------|
| **Scenario friction** | "Add-car asked for zip again after I gave it" | During trial |
| **Handoff confusion** | "Next move was too vague" | During trial |
| **Trust moment** | "Broker didn't trust Collected chips" | During or after |
| **UI friction** | "Couldn't find Resume here" | During trial |
| **Performance** | "Turn 1 was slow" | During trial |
| **Value validation** | "Which scenario felt most useful?" | Post-trial |

**Daily log format:** `[Date] [Scenario ID or case type] [Friction/observation]: [one line]`

---

## 2. How to Categorize Observations

| Category | Definition | Example |
|----------|-------------|---------|
| **Trust-breaking** | Would cause broker to stop using | Wrong next move; auto-send confusion |
| **High friction** | Slows broker significantly | Draft needs full rewrite; Collected wrong |
| **Medium friction** | Noticeable but workable | Turn 1 slow; Resume here hard to find |
| **Low friction** | Minor polish | Wording tweak; badge placement |
| **Positive signal** | What worked well | "Collected chips saved time" |

---

## 3. Fix Now / Next / Defer

| Decision | When | Example |
|----------|------|---------|
| **Fix now** | Blocks trial or breaks trust | Talk to Agent routes wrong; next move always generic |
| **Fix next** | High value, can ship in 1–2 sprints | Correction badge not visible; observation log missing fields |
| **Defer** | Lower priority; document for later | Inbox sync; OCR; carrier API |

**Rule:** If it would make a broker say "I can't use this" → fix now. If it would make them say "this could be better" → fix next. If it's a feature request → defer.

---

## 4. Map Feedback to Scenario or Backbone Work

| Observation | Likely fix location |
|-------------|---------------------|
| "Add-car asked for zip again" | `_add_car_enough_for_handoff`; `collected_fields` extraction |
| "Next move too vague" | `_build_broker_next_step`; reply template |
| "Collected wrong" | Triage extraction; human_confirmation_required |
| "Talk to Agent awkward" | `talk_to_agent` intent; handoff phrasing |
| "Resume here unclear" | UI: reopen context; `waiting_on` display |
| "Turn 1 slow" | Speed routing; cold start |
| "Observation log missing X" | `TRIAL_OBSERVATION_LOG_TEMPLATE.md`; friction classification |

---

## 5. Friction Classification Table (Template)

| # | Date | Scenario | Observation | Category | Fix decision | Map to |
|---|------|----------|-------------|----------|--------------|--------|
| 1 | | | | Trust / High / Medium / Low | Fix now / Next / Defer | scenario or component |
| 2 | | | | | | |

**Map to:** e.g. add_car, triage.py, broker_next_step, UI case card, talk_to_agent

---

## 6. Post-Trial: Turn Observations into Next Sprint

1. **Collect** — All daily log entries + 5 value validation answers
2. **Classify** — Trust-breaking / High / Medium / Low
3. **Decide** — Fix now / Next / Defer for each
4. **Map** — Each "fix now" and "fix next" → scenario ID or backbone component
5. **Prioritize** — Fix now first; then highest-value fix next
6. **Document** — Add to next sprint backlog with clear acceptance

**Storage:** Save filled logs to `results/trial_logs/{broker}_{date}.md` for traceability.

---

*End of Trial Observation-to-Iteration Spec*
