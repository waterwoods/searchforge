# Add-Car efficiency loop — spec

## Current inefficiency points (product-facing)

- Customers unsure what to say first; fragmented input.
- Brokers repeat questions when gaps and “done” are unclear.
- Office handoff and quote-prep readiness can feel implicit.

## North-star loop

**Help the customer start faster, help the system collect faster and more clearly, help the office take over faster and more reliably** — same service record, thread as audit trail.

## Priority order (design)

1. **Amazon-style flow** — step, progression, completion condition, next action.
2. **Zendesk-style state** — lifecycle and status scannable on customer and workbench surfaces.
3. **Intercom-style handoff** — received, not abandoned; clear office next step.
4. **Stripe-style page** — clarity supports the loop; polish is not the primary lever this sprint.

## Acceptance criteria

- [ ] Master outline documents immediate focus on Add-Car efficiency loop optimization (not feature sprawl).
- [ ] `PROJECT_TRUTH_SWITCH` or equivalent reflects that priority where appropriate.
- [ ] Add-Car right rail surfaces **完成条件（本步）** for step 2 with three bounded cases: gaps / handoff_pending / still collecting.
- [ ] Customer entry uses **shared** `computeAddCarFlowStep` for the top flow track vs rail.
- [ ] Chen Kui client pack includes flow-explain and record-rail strings so copy is pack-driven, not only code defaults.
- [ ] `bash scripts/guardrail_inbox_triage.sh` passes (backend contract unchanged for this sprint).
