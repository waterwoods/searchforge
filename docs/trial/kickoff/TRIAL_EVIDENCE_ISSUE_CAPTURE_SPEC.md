# Trial Evidence / Issue Capture Spec

**Sprint:** Broker Trial Kickoff Readiness Sprint  
**Created:** 2026-03-18  
**Purpose:** Define what should be captured during trial, what counts as a useful issue, how to classify issues, and how to group them into fix-now / fix-next / defer.

---

## 1. What to Capture During Trial

| Type | When | Format | Storage |
|------|------|--------|---------|
| **Daily log** | Each trial day | Date, conversations, handoffs, scenario mix, notes | `results/trial_logs/{broker}_{date}.md` |
| **Friction entry** | When broker hits friction | `[Date] [Scenario] Friction: [one line]` | Same file |
| **Value validation** | Post-trial | 5 questions answered | Same file |
| **Friction classification** | Post-trial | #, Date, Scenario, Observation, Category, Fix decision, Map to | Same file |
| **Screenshots** | Optional | Case card, Collected chips, Human confirmation | `results/trial_logs/{broker}_{date}_screenshots/` |

---

## 2. What Counts as a Useful Issue

| Useful | Not useful |
|--------|------------|
| "Add-car asked for zip again after I gave it" | "Didn't work" |
| "SIM1: next move was generic, not cancellation-specific" | Vague complaint |
| "Broker couldn't find Resume here on reopen" | Feature request (defer) |
| Scenario + what happened + one line | Emotional only |

**Rule:** Each friction entry should be actionable: scenario + what happened + one line.

---

## 3. How to Classify Issues

| Category | When | Example |
|----------|------|---------|
| **Trust-breaking** | Broker would say "I can't use this" | Talk to Agent routes wrong; next move always generic |
| **High friction** | Significant pain, can fix in 1–2 sprints | Correction badge not visible |
| **Medium friction** | Noticeable but tolerable | Observation log missing fields |
| **Low friction** | Minor polish | UI tweak |

---

## 4. Fix-Now / Fix-Next / Defer Logic

| Decision | When | Example |
|----------|------|---------|
| **Fix now** | Blocks trial or breaks trust | Talk to Agent routes wrong |
| **Fix next** | High value, can ship in 1–2 sprints | Correction badge not visible |
| **Defer** | Lower priority; document for later | Inbox sync; OCR; carrier API |

**Rule:** If broker would say "I can't use this" → fix now. If "this could be better" → fix next. If feature request → defer.

---

## 5. Group Issues By Layer

| Layer | Examples |
|-------|----------|
| **Scenario layer** | add_car_enough_for_handoff; collected_fields extraction; SIM1/SIM2/SIM3 |
| **Workbench / handoff** | broker_next_step; reply template; next move visibility |
| **Backbone / state** | triage extraction; human_confirmation_required; follow_up_type |
| **Trial workflow / docs** | Observation log; founder checklist; broker one-pager |

---

## 6. Post-Trial Quick Flow

1. **Collect** — All daily log entries + 5 value validation answers
2. **Classify** — Trust-breaking / High / Medium / Low
3. **Decide** — Fix now / Fix next / Defer for each
4. **Map** — Each fix now and fix next → scenario ID or backbone component
5. **Prioritize** — Fix now first; then highest-value fix next
6. **Document** — Add to next sprint backlog with clear acceptance

**Storage:** `results/trial_logs/{broker}_{date}_fix_now_queue.md` — copy from `docs/trial/FIX_NOW_QUEUE_TEMPLATE.md`.

---

## 7. What Triggers Immediate Sprint Planning

| Trigger | Action |
|---------|--------|
| Any Trust-breaking | Add to fix-now backlog; plan sprint within 1 week |
| 3+ High friction | Prioritize fix-next; plan sprint |
| Broker says "would not use again" | Root-cause; fix-now sprint |
| Value validation: "risky" answer | Map to component; fix next or fix now |

---

*See also: `docs/trial/FIX_NOW_QUEUE_SPEC.md`, `docs/trial/FIX_NOW_QUEUE_TEMPLATE.md`, `docs/trial/TRIAL_OBSERVATION_LOG_TEMPLATE.md`*
