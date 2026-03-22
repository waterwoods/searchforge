# Founder Inspection Notes

## What to inspect after this sprint

1. **Customer Entry (empty state)** — See “加车报价 · 快速填写（可选）”; fill 3 fields; submit; confirm office reply asks only for **remaining** gaps.
2. **Compare paths** — Same content: typed paragraph vs structured card → Workbench case sheet should be **equivalent** in structure.
3. **Quote-ready without contact** — Confirm contact block shows 待补 and human confirmation hint when appropriate.
4. **Correction path** — Scenario pack #4; vehicle updates, no “stuck” wrong car.
5. **Side question** — Scenario pack #5; broker_next_step acknowledges both threads.
6. **Handoff timing** — Run Simulation Assistant “Add-car” multi-turn or handoff scripts; no early handoff missing driver.

## “Good enough to show a real broker”

- Broker sees **one clear next action** and **what’s already known** without re-reading chat.
- Customer path does not **force** chat tricks; optional structure feels **professional**, not gimmicky.

## Signals that matter most

- Fewer “what’s the zip again?” moments in scripted runs.
- `quote_ready_status` aligns with mental model of “can I rate this?”
- Founder would **trust** the case card in front of a client.
