# Founder Inspection Notes

## What changed you can feel

- Same business logic, but more client-distinct wording on high-traffic handoff overlays.
- `socal_precision` now keeps desk/business-day tone in three important handoff moments that were previously hardcoded in shared voice.

## Fast manual checks

1. Add-car + doc clarification:
   - ask `garaging proof 是什么意思` with quote-ready details
   - verify suffix tone differs by client
2. Add-car + coverage side question:
   - ask `coverage 能调吗` in same quote-ready turn
   - verify answer+handoff overlay differs by client
3. Payment correction urgency:
   - `其实已经付了，那我现在最要紧做什么？`
   - verify urgency line differs by client and no logic drift

## Move-now / move-later / keep-in-code

| Bucket | Items |
|---|---|
| Move now | Handoff overlay residual families selected in this sprint |
| Move later | Lower-frequency category one-liners (`unclear`, `informational`, `policy_delay_pending`) |
| Keep in code | Intent detection, routing, slot extraction, lifecycle logic |

## Commercial relevance

- Better A/B voice isolation without destabilizing the engine
- Stronger hot-plug credibility for same-industry clients
- Minimal blast radius: wording-only changes on existing config rails
