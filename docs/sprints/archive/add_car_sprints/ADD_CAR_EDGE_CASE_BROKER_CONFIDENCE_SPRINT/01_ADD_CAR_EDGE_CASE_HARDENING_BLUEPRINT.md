# Add-Car Edge-Case Hardening Blueprint

## Why Add-Car needs edge-case hardening now

Add-Car is the flagship workflow: quote-ready rules, contact-lite, attachment/materials-sent handling, corrections, side questions, and workbench visibility already exist. The remaining risk before a real broker (Chen Kui style) touches it is **messy customer behavior**—not missing features, but confusing sequences that make the office doubt the summary or the draft.

## Why this matters before broker review

Brokers forgive “not perfect.” They do **not** forgive:

- Wrong primary workflow (e.g., renewal language on a new-car quote thread).
- Summaries that omit or mis-state vehicle facts after a correction.
- Replies that sound like the system ignored a price worry mid–add-car.

## What this sprint strengthens

- **Deterministic add-car path** when messages mix “cheap / 便宜 / 大概多少钱” with add-car markers.
- **Broker-facing vehicle line** for Chinese make/model phrases (e.g., 宝马) after a structural bug left those branches unreachable.
- **Correction vocabulary** (`不是这辆`, `另一辆`) so follow-up typing and summary hints stay honest.
- **Regression pack** (ACE01–ACE12) plus a small runner script for repeat audits.

## What this sprint intentionally does not do

- OCR, carrier APIs, quote engines, full CRM, enterprise ticketing, or broad non–add-car refactors.

## 10–20 point edge-case hardening breakdown (concrete)

1. **Why now:** Broker demo risk is “messy reality,” not missing screens.
2. **Broker confidence loss:** Primary intent feels wrong (renewal vs add-car).
3. **Messy behaviors that matter most:** Side questions, corrections, materials-sent, partial slots, price chips mid-flow.
4. **Trust-breaking failure:** Broker_next_step or summary contradicts the latest customer correction.
5. **Acceptable imperfection:** Cannot answer true premium; can acknowledge office will run numbers.
6. **High-value tests:** Mixed premium wording + add-car; zip-first; materials after quote-ready; dense single bubble.
7. **Reduces rework:** Correct workflow template + structured fields first; fewer wrong playbooks.
8. **Office trust:** Short, office-realistic lines on price sensitivity without abandoning slot collection.
9. **Realism:** Hesitation (“可能下周”) and multi-question bubbles handled without derailing.
10. **Fix now (this sprint):** Vehicle concrete extraction bug; add-car before premium in templates; price-sensitivity tack-on; correction markers; ACE pack + runner.
11. **Fix next:** Deeper “另一辆车” disambiguation when two full VIN/year chains conflict; richer driver-history tracking across many turns.
12. **Acceptable for broker review:** Single-message multi-question answered mainly by handoff + broker read of thread.
13. **Defer:** Full natural-language negotiation of coverage; automatic conflict resolution across long unrelated digressions.
14. **Founder manual tests:** Listed in `08_FOUNDER_INSPECTION_NOTES.md`.
15. **“Ready to show broker”:** Guardrail PASS + ACE all strong + no weak multi-turn regressions.
