# Right rail spec — record summary + flow explainer

## Current weakness (pre-change)

- Collected and still-needed fields appeared as **flat tag lists**, similar to a form dump.
- **Why the case is on this step** and **who owns the next action** lived in separate boxes (skeleton + customer-next lane), easy to skim past.
- **Corrections** were visible mainly as a small tag on chat bubbles, not in the **record panel**.
- Simulation right column duplicated **step / owner / fields** without the same narrative structure as intake.

## Target structure (1.0)

| Section | Intent | Always / conditional |
|--------|--------|----------------------|
| A — Current step | `第 N 步：…` aligned with Amazon-style skeleton | Always (when panel shown) |
| B — Why here | Short lines from lifecycle, gaps, handoff_pending | Always |
| C — Received | Grouped: 车辆与提车 / 驾驶人 / 联系信息 / 材料与核实 / 其他 | When any collected ids; else fallback copy |
| D — Still needed | Same grouping; only true still-needed ids | When any; else explicit “no extra gaps” where appropriate |
| E — Latest update | `follow_up_type === correction` **or** newly appeared collected fields vs prior system turn | Conditional |
| F — Next owner | Process-oriented owner line + continue/append vs office path (portal) | Always in portal pre-handoff; simulation omits dual-path paragraph |

## Explanation goals

- **Record-first**: panel should beat the thread for understanding case state.
- **Business language**: steps and owners are process-oriented, not chatbot filler.
- **Scannable**: groups avoid long single-row tag soup.

## Correction-visibility goals

- Use **existing API signals** only: `follow_up_type`, diff of `collected_fields` vs previous system response.
- Do **not** invent field-level “old → new” strings without backend support.

## Acceptance criteria

- [x] Pre-handoff Add-Car progress card uses shared rail with sections A–F (E conditional).
- [x] Post-handoff structured snapshot uses **grouped** received/missing + optional E.
- [x] Simulation right column uses the **same** rail component (simulation density).
- [x] `npm run build` passes for `ui`.
- [x] New `record_rail_*` strings overridable via client `ui_copy`.
