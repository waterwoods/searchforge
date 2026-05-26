# Founder Inspection Notes

Use this as a **live checklist** while clicking through Unified Intake or reading drafts alongside the battery.

## What to eyeball in the UI

- Does the **first reply** feel like a real assistant, or does it **repeat the customer’s sentence** back?
- On **handoff**, does the broker panel show **vehicle + ZIP + timing + driver** when the customer actually provided them?
- When the customer says **“发你微信了”**, does the product **verify** instead of nagging for the same slots?

## Scenarios worth manual re-check

| ID | Why manually re-check |
|----|------------------------|
| ACB-C03 | ZIP formatting (`邮编` prefix) — known automation gap in rule path. |
| ACB-M04 | Risk of **materials-sent** false positive + category flip. |
| ACB-E07 | Turn 1 operational question — should not look “broken” to a broker. |
| ACB-E05 | Long reply — check whether it feels helpful or chatty. |

## Single-slide story for Chen Kui

1. Show **ACB-C01** (clean two-turn).
2. Show **ACB-E01** (correction).
3. Show **ACB-E03** (materials sent).
4. Optionally show **ACB-M04** as “what we’re hardening next” if discussing roadmap honesty.

## Recording outcomes

When you re-run the battery after code changes, paste a one-liner here:

- Date:
- Command:
- Delta vs `run_results_rule_path.json`: (better / worse / mixed — which IDs)
