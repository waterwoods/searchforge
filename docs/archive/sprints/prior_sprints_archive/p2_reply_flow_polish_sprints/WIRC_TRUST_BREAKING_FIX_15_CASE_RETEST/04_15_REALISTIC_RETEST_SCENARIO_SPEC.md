# 15 Realistic Retest Scenario Spec

Machine-readable definitions live in **`retest_scenarios.json`** (same folder). Runner: **`scripts/run_wirc_trust_breaking_15_retest.py`** (`LLM_GENERATION_ENABLED=false`).

## Distribution (as required)

| Bucket | IDs | Focus |
|--------|-----|--------|
| Screenshot / VIN / registration: question vs sent | WTR-S01 … S05 | Trust-breaking phrases vs true 发微信了 |
| First-turn unusual | WTR-F01 … F04 | ZIP price, registration+订单截图, vague 加车, two-turn |
| Lexicon / mixed naming | WTR-L01 … L03 | Nissan Altima, 丰田塞纳, Model Y |
| Messy multi-turn | WTR-M01 … M03 | Correction + sent, follow-up 行驶证截图, try-this-vehicle |

## Per-scenario fields (JSON)

- `id`, `bucket`, `why`, `turns[]`
- `last_turn_expect`: `forbid_draft_substrings`, `require_draft_substrings_any`, optional `issue_category`, `handoff_ready`, `follow_up_type_not`

## Failure philosophy

Assertions emphasize **absence of false “already sent” copy** (`您是说发过了…`) and presence of **permission-answer or office-safe handoff** language. Some cases intentionally allow **unclear** category when no add-car anchor exists (e.g. WTR-S03) — still a pass if trust-breaking wording is absent.
