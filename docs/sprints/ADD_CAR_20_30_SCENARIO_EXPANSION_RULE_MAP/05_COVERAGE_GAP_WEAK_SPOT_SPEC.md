# Coverage Gap / Weak Spot Spec

## Questions this sprint must answer

1. Which **Add-Car patterns** are already **very strong** on the rule path?
2. Which patterns are **still weak** (acceptable but fragile)?
3. Which realistic behaviors remain **under-covered** by tests or logic?
4. What is the **single best next fix** if only one engineering pass is allowed?
5. Is Add-Car **strong enough for a serious broker demo** (Chen Kui–style viewing)?

## How gaps are identified

- Compare **expected_good_behavior** vs observed runner output per scenario.
- Cross-check **ACEXP** (30) with **ACB** (17) and **ADZM** (22) when `--include-existing-batteries` is used.
- Flag recurring failure modes (same root cause across ≥2 scenarios).

## Output

Consolidated findings live in **`09_FINAL_REPORT.md` §6–§7**. This file is the **spec**; the report is the **filled instance** for this run date.

## Known risk areas to watch (hypotheses)

- **Mixed-intent** first messages (office hours + add-car; garaging proof + add-car) may stress primary flow selection.
- **Two-vehicle confusion** threads may produce broker summaries that lag the customer’s final resolution.
- **Price anxiety** may interact with category guardrails (premium_review vs add_car).

These are validated against actual JSON in the final report.
