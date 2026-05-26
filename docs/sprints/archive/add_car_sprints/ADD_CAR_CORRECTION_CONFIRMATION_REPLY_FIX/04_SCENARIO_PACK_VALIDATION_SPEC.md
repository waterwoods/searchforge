# Scenario Pack / Validation Spec

## Pack updates

`configs/customer_entry_multi_turn_simulations.json`

| ID | Intent |
|----|--------|
| ACE13–ACE16 | Existing: Honda→Tesla, correction+ZIP, EN correction, X5→X3 + materials |
| **ACE17** | `不对，是 2024 Tesla` after `我想加车 2021 Honda` — must get explicit vehicle confirm + zip ask |
| **ACE18** | `不是X5，是X3` (comma) — correction detection + concrete |

## Manual / founder checks

1. Honda → Tesla (`不是这个，是 2024 Tesla`)
2. X5 → X3 with comma
3. Correction + ZIP same bubble (ACE14)
4. Correction + materials (ACE16 / broker stress BS12)
5. Partial / year-only correction (`是2024款的`) — expect **honest** “2024” only if no model in bubble (document as residual risk)
6. Mixed CN/EN (`Not that one — meant the 2024 Tesla`) — ACE15

## Commands

```bash
bash scripts/guardrail_inbox_triage.sh
PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py
PYTHONPATH=. python3 scripts/run_add_car_edge_case_simulations.py
```

## Deployment

Any change under `services/fiqa_api/inbox_triage/` requires **backend redeploy** for Vercel/API consumers. **No frontend redeploy** for this sprint.
