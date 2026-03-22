# Founder Inspection Notes

## What to skim first

1. `scenario_battery.json` — 30 IDs (`ACEXP-001` … `030`); each row has `why_matters` / `expected_good_behavior`.
2. `09_FINAL_REPORT.md` — counts, weak list, rule map, 中文总结.
3. Raw JSON from:  
   `PYTHONPATH=. python3 scripts/run_add_car_expansion_rule_map_battery.py --json`

## Headline results (this run, rule path)

- **30/30** stayed `issue_category: customer_question` (Add-Car playbook).
- **29/30** ended `handoff_ready: true`. The single **no handoff** case is **ACEXP-027** (车型 “塞纳” not in the rule lexicon → model slot gap).
- **Materials split** behaved as designed: `already_sent` on 发微信/截图 patterns; **要不要 / 看看行吗** stayed `new_info` with a short permission lead + handoff.
- **Corrections** (011, 012, 015) show good customer-facing vehicle pivots; **013** still hands off but broker line degrades to generic “丰田”.

## Watch list for broker demo

1. **Concrete vehicle in broker line** — some dense or mixed messages collapse to “Run quote for 2024” (see ACEXP-024).
2. **Chinese model nicknames** — 塞纳 → needs lexicon or extraction tweak (027).
3. **Side question + handoff** — garaging answer works but **026** reply stacks redundant “收集信息” wording; polish candidate.
4. **English micro-phrases** — “only I drive” vs “only me” (004): broker step asks to confirm driver; acceptable but worth unifying markers.

## Chen Kui demo posture

- **Safe to show** end-to-end Add-Car with “happy path” and materials/correction stories.
- **Pre-brief** brokers that **edge Chinese trims / rare nicknames** and **broker_next_step brevity** are the main remaining sharp edges—not logic drift to wrong products.
