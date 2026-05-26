# Mutation Scenario Pack

Machine-readable scenarios: **`mutation_scenario_pack.json`** (same directory).

Runner: `scripts/run_add_car_mutation_battery.py`

## IDs

| ID | Area | Intent |
|----|------|--------|
| MUT-Z01 | zip | `邮编95131` second turn (no space) |
| MUT-Z02 | zip | `zip95131` glued English |
| MUT-Z03 | zip | Single bubble: 2024 Tesla + 邮编 + 我自己开 + delivery |
| MUT-Z04 | zip | Bare `95131` as second turn |
| MUT-D01 | driver | `本人开` after near-complete first turn |
| MUT-D02 | driver | `我老婆开` after quote-ready first turn missing driver phrase |
| MUT-D03 | driver | `儿子开` after Lexus RX bubble |
| MUT-A01 | already_sent | Question: 材料要不要先发给你 |
| MUT-A02 | already_sent | Offer: 要不我发你微信你看下行不行 |
| MUT-A03 | already_sent | Statement: 我已经发你微信了 + 截图发你了 |

Total: **10** scenarios.
