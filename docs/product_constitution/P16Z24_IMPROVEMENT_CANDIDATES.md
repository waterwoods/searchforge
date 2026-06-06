# P16-Z24 Improvement Candidates

| # | Improvement | Effort | Score lift | Risk | Chen Kui demo |
|---|-------------|--------|------------|------|---------------|
| 1 | Teen/family vehicle add without explicit "add car" phrase | S | +8 | Low | YES — first-turn routing |
| 2 | Mixed intent defer — stay on Add-Car when customer says "先专注加进去" | S | +12 | Low | YES — AC20 class |
| 3 | Chinese `office_broker_next_step` with human field labels | S | +6 | Low | YES — broker reads Chinese |
| 4 | Price-question office hint "(客户问了保费，先补齐信息再报价)" | S | +3 | Low | YES |
| 5 | Suppress remove_car lane when add-car defer signal on last turn | S | +10 | Low | YES |
| 6 | Quote-ready Chinese office line "信息齐全，可直接出报价" | S | +4 | Low | YES |
| 7 | Better spouse driver extraction on "她主驾" single-line | M | +4 | Med | Partial |
| 8 | Delayed delivery "还没定" → still_needed delivery_date consistently | M | +3 | Low | Partial |
| 9 | English broker_next_step localization (mirror office step) | M | +5 | Low | Partial — UI uses office field |
| 10 | Minimal opener proactive vehicle ask in client draft | M | +3 | Low | Partial |

**Applied in Phase 5 (safe only):** #1–#6
