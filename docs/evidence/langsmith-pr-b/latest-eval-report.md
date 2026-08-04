# Accident Story Golden Eval — 20260804T183705Z

**Dataset:** `accident_story_v1`  
**Pass rate:** 20/20 (100.0%)  
**Tracing enabled:** True  

| Fixture | Result | Questions | Missing | Injury | Fallback |
|---------|--------|-----------|---------|--------|----------|
| `all_three_missing` | PASS | 3 | `accident_datetime,accident_location,injury_status` | unknown | False |
| `complete_story` | PASS | 0 | `` | no | False |
| `empty_story` | PASS | 3 | `accident_description,accident_datetime,accident_location,injury_status` | unknown | False |
| `english_rear_end` | PASS | 0 | `` | no | False |
| `explicit_no_injury` | PASS | 2 | `accident_datetime,accident_location` | no | False |
| `hallucinated_field_rejected` | PASS | 1 | `accident_datetime` | no | True |
| `injury_conflict` | PASS | 1 | `injury_status` | unknown | False |
| `invalid_model_fallback` | PASS | 1 | `accident_datetime` | no | True |
| `missing_injury_only` | PASS | 1 | `injury_status` | unknown | False |
| `missing_location` | PASS | 1 | `accident_location` | no | False |
| `missing_time_injury` | PASS | 2 | `accident_datetime,injury_status` | unknown | False |
| `missing_time_location_injury_known` | PASS | 2 | `accident_datetime,accident_location` | no | False |
| `missing_time_only` | PASS | 1 | `accident_datetime` | no | False |
| `mixed_zh_en` | PASS | 1 | `accident_datetime` | no | False |
| `parking_lot_location_only` | PASS | 1 | `accident_datetime` | no | False |
| `side_swipe` | PASS | 0 | `` | no | False |
| `timeout_fallback` | PASS | 1 | `accident_datetime` | no | True |
| `unknown_injury` | PASS | 3 | `accident_datetime,accident_location,injury_status` | unknown | False |
| `vague_yesterday_time` | PASS | 1 | `accident_datetime` | no | False |
| `very_long_story` | PASS | 0 | `` | no | False |

## Failures

None.
