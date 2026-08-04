# Accident Story — Five-Case Pilot Scorecard V1

**Generated:** 2026-08-04T21:40:27Z
**Environment:** Cloud QA + local office-workflow proof
**Office:** `qa_canary_synth` (synthetic only)

Raw stories and personal identifiers are **not** recorded here.

## Real pilot success criteria

| Criterion | Required | Observed |
|-----------|----------|----------|
| unknown-injury → no | 0 | 0 |
| unconfirmed AI shown as customer facts | 0 | 0 |
| raw PII telemetry violations (new traces) | 0 | 0 |
| manual fallback usability | 100% | PASS (kill switch + timeout case) |
| max follow-up questions | ≤3 | ≤3 |
| ≥4/5 completed without technical support | ≥4 | **5/5** QA |
| office next action identifiable every case | yes | yes |

## Case rows (Cloud QA)

| # | Scenario | Path | Q | Edits | Completed | Broker review | Latency ms | Fallback | Safety | Notes |
|---|----------|------|---|-------|-----------|---------------|------------|----------|--------|-------|
| 1 | Complete accident story | openai | 0 | — | yes | authority=customer_confirmed; next_action=yes; ref=case_a5c9a4f85a5 | 2595 | none | none | ok=True |
| 2 | Missing time and location | openai | 0 | accident_time_text,accident_location_text | yes | authority=customer_confirmed; next_action=yes; ref=case_b19fbf42bd2 | 1969 | none | none | ok=True |
| 3 | Unknown injury | openai | 3 | injury_status | yes | authority=customer_confirmed; next_action=yes; ref=case_5b956d85a2f | 3112 | none | none | ok=True |
| 4 | Conflicting facts | openai | 1 | injury_status | yes | authority=customer_confirmed; next_action=yes; ref=case_6cefa1ff79e | 1952 | none | none | ok=True |
| 5 | Live-model timeout → deterministic fallback | deterministic | 1 | — | yes | authority=customer_confirmed; next_action=yes; ref=case_7b6cba4a7a8 | 138 | timeout | none | ok=True |

## Aggregate

- QA passed: 5/5 gate=True
- Local passed: 5/5 gate=True
- Kill switch manual intake usable: True

