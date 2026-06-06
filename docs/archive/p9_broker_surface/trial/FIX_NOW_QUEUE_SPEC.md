> **HISTORICAL / ARCHIVE — P9 Broker Surface Collapse (2026-05-30)**
> **Read instead:** [`docs/TRIAL_ONE_PATH.md`](../../../TRIAL_ONE_PATH.md), [`docs/BROKER_TRIAL_PLAYBOOK.md`](../../../BROKER_TRIAL_PLAYBOOK.md)

# Fix-Now Queue Spec

**Sprint:** Trial Launch + Fix-Now Queue Sprint  
**Created:** 2026-03-18  
**Purpose:** Define how trial observations get turned into fix now / fix next / defer, how to group issues, and what should trigger immediate sprint planning after the trial.

---

## 1. Observation → Fix Decision

| Decision | When | Example |
|----------|------|---------|
| **Fix now** | Blocks trial or breaks trust | Talk to Agent routes wrong; next move always generic |
| **Fix next** | High value, can ship in 1–2 sprints | Correction badge not visible; observation log missing fields |
| **Defer** | Lower priority; document for later | Inbox sync; OCR; carrier API |

**Rule:** If broker would say "I can't use this" → fix now. If "this could be better" → fix next. If feature request → defer.

---

## 2. Group Issues By Layer

| Layer | Examples |
|-------|----------|
| **Scenario layer** | add_car_enough_for_handoff; collected_fields extraction; SIM1/SIM2/SIM3 |
| **Workbench / handoff** | broker_next_step; reply template; next move visibility |
| **Backbone / state** | triage extraction; human_confirmation_required; follow_up_type |
| **Trial workflow / docs** | Observation log; founder checklist; broker one-pager |

---

## 3. Fix-Now Queue Structure

| Column | Purpose |
|--------|---------|
| # | Row number |
| Date | When observed |
| Scenario | SIM1, add-car, cancellation, etc. |
| Observation | One-line description |
| Category | Trust-breaking / High / Medium / Low |
| Fix decision | Fix now / Fix next / Defer |
| Map to | Scenario ID or component (triage.py, broker_next_step, UI case card) |
| Notes | Optional |

**Template:** `docs/trial/FIX_NOW_QUEUE_TEMPLATE.md` — copy for each trial; fill post-trial.

---

## 4. What Triggers Immediate Sprint Planning

| Trigger | Action |
|---------|--------|
| Any Trust-breaking | Add to fix-now backlog; plan sprint within 1 week |
| 3+ High friction | Prioritize fix-next; plan sprint |
| Broker says "would not use again" | Root-cause; fix-now sprint |
| Value validation: "risky" answer | Map to component; fix next or fix now |

---

## 5. Post-Trial Quick Flow

1. **Collect** — All daily log entries + 5 value validation answers
2. **Classify** — Trust-breaking / High / Medium / Low
3. **Decide** — Fix now / Fix next / Defer for each
4. **Map** — Each fix now and fix next → scenario ID or backbone component
5. **Prioritize** — Fix now first; then highest-value fix next
6. **Document** — Add to next sprint backlog with clear acceptance

**Storage:** `results/trial_logs/{broker}_{date}_fix_now_queue.md` — or use FIX_NOW_QUEUE_TEMPLATE filled and saved.

---

*End of Fix-Now Queue Spec*
