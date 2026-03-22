# Acceptance Criteria

## Robustness

- [x] ACE01–ACE12 all classify **strong** (no handoff-timing notes unless intentionally documented).
- [x] Full multi-turn pack: **0 weak** simulations after ACE merge.
- [x] Guardrail script **PASS** including adversarial and mixed-intent sections.

## Broker confidence

- [x] Add-car + “便宜/大概多少钱” messages use **add-car** client draft path, not premium-review first.
- [x] Chinese make/model messages (e.g., 宝马) produce non-empty **vehicle concrete** when year+phrase present.

## Credible flagship behavior

- [x] Corrections with `另一辆` / `不是这辆` map to **correction** follow-up typing.
- [x] Materials-sent handoff tone remains **warm / verify** for add-car.

## Explicit non-goals (must remain true)

- [x] No new OCR, carrier API, or CRM features added in this sprint.

## Release readiness

- [ ] Backend deployed to broker-review environment (founder action).
- [x] Automated local validation complete.
