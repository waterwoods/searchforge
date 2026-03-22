# Founder Inspection Notes — 30-Minute Read Path

**Use this** to understand Unified Intake **without** reading all of `triage.py`.

---

## 1. Start here (mental model)

1. **Customer** types in the Unified Intake UI (or API).
2. **Engine** (`triage.py`) decides: category, urgency, what the **broker** should do, what the **customer** should prepare, and a **draft reply**.
3. **Config** tunes **words** and **markers**; **code** tunes **when** things happen and **what** gets extracted.
4. **Case store** saves the thread so the demo feels like a **workbench**.

---

## 2. Files to open in order

| Order | Path | What to notice |
|-------|------|----------------|
| 1 | `configs/clients/chen_kui/ui_copy.json` | Everything the **customer** sees in the chrome (titles, buttons, handoff closure). |
| 2 | `configs/clients/chen_kui/handoff_phrases.json` | What the **assistant** says when handing off by flow type. |
| 3 | `configs/industries/insurance/markers.json` | How we **spot** intents (keywords). |
| 4 | `configs/industries/insurance/add_car_rules.json` | Next-question **prompts** for add-car collection. |
| 5 | `config_loader.py` | **Load order**: common → industry → client; see `get_ui_copy`, `get_handoff_phrases`, `get_reply_templates`. |
| 6 | `triage.py` (search only) | `triage_conversation`, `WORKFLOW_STATE_KEYS`, `_classify_append_case_boundary` — **policy**, not prose. |
| 7 | `case_store.py` (skim top) | What a “case” contains and validation limits. |
| 8 | `scripts/guardrail_inbox_triage.sh` | What **must stay green** before you promise behavior. |

---

## 3. Five questions founders ask

| Question | Where is the truth? |
|----------|----------------------|
| “Can we change button labels?” | `ui_copy.json` → quick_start_buttons; UI merges API + TS defaults. |
| “Can we change handoff wording?” | `handoff_phrases.json`. |
| “How does the system know it’s add-car?” | `markers.json` + functions like `_is_add_vehicle_request` in `triage.py`. |
| “When does it stop asking and send to the office?” | `triage_conversation` + `_should_handoff` + add-car exceptions — **code**. |
| “What if the customer changes topic mid-thread?” | `_classify_append_case_boundary` — **code**; sets `case_boundary` and may adjust draft. |

---

## 4. Red flags (drift / debt)

- **Same sentence** edited in **three places** (route, triage fallback, UI default) — productization debt.
- **New JSON keys** not read by loader — e.g. extra add-car keys.
- **Hardcoded client folder** in loader — blocks second broker.

---

## 5. One sentence pitch to a customer

“We separate **your office’s words** from **insurance logic** from **the engine** that tracks cases and handoffs — and we rerun automated scenarios before we change behavior.”

---

## 6. If you only read one code function

Read **`triage_conversation`** (start of function docstring + first ~120 lines after empty-input guard): it shows **fast vs LLM path**, **talk-to-agent** shortcut, **handoff vs next ask**, and where **handoff phrases** attach.

---

## 7. Reporting angle

For a **business walkthrough**, show:

1. `ui_copy.json` — customer experience.
2. `handoff_phrases.json` — assistant tone at handoff.
3. A **green guardrail run** — engineering discipline.

That trio answers “what will people see” and “how do we know it still works.”
