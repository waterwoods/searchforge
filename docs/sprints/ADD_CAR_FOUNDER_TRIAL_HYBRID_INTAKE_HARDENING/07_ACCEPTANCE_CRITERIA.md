# Acceptance Criteria

## Stronger realism

- [ ] Add-car can start from **quick button**, **structured card**, or **free text** without conflicting backends.
- [ ] Composed structured message reads like a **real customer** text, not internal JSON.

## Stronger usefulness

- [ ] First turn from structured card reduces typical turns to **quote-ready** vs vague one-liner (founder judgment + sims stable).

## Stronger broker trust

- [ ] Workbench still shows **quote_ready_status**, collected/still needed, broker_next_step — no regression.
- [ ] No fake “we quoted you” language; boundaries remain honest.

## Time-saving value

- [ ] `next_best_question` and `still_needed_fields` still drive follow-up; hybrid does not bypass collection rules.

## Commercial readiness (for *more serious* broker review — not perfection)

- [ ] Guardrail + multi-turn + stress + handoff timing scripts pass locally.
- [ ] `npm run build` succeeds for UI.

## Explicit non-goals (must remain true)

- [ ] No new scenarios required for acceptance.
- [ ] No OCR / carrier API.
