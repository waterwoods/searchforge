# Current Case vs New Issue — Detection Spec

## Signals

### Prior thread domain (`_infer_prior_case_domain`)

Order of precedence:

1. **add_car** — customer add/quote markers **or** system line contains add-car handoff cues (`办公室会尽快出价`, `报价资料`, `Run quote`, …).
2. **claim** — claim intake markers in customer text.
3. **remove_car**, **premium**, **payment**, **missing_doc** — existing marker sets.
4. **generic** — fallback.

### Last message domains (`_last_message_issue_domains`)

- **claim** — `_is_claim_intake_request`
- **remove_car** — `_is_remove_vehicle_request`
- **add_car** — `_is_add_vehicle_request`
- **billing** — 账单 / 扣款 / autopay / invoice / past due / …
- **office** — 周末 / 营业时间 / office hour / …

### Pivot phrases (`_TOPIC_PIVOT_STRONG`)

Chinese/English cues that the customer may be **changing topic** (还有一个问题, 另外一个, 加车先这样, …).

## Decision order (`_classify_append_case_boundary`)

1. **Early new_issue:** `last_domains ∩ cross_domains(prior) ≠ ∅`  
   Cross-domain matrix is asymmetric (e.g. add_car ↔ claim/billing/remove_car).
2. **Follow-up short-circuit:** `correction` (unless cross-topic pivot like 不是理赔 / 另外一个保险), `already_sent`, `clarification_question`.
3. **Add-car same-thread guards:** coverage/collision wording; short factual fields; extra-vehicle phrases (`另一台`, `再加`, …).
4. **Office on add_car** → `borderline`.
5. **Pivot with empty domains** → `borderline`.
6. **Pivot + add_car-only on add_car prior** → `borderline` (unless extra-vehicle exception).
7. **generic prior + hit + pivot** → `borderline`.

## Outputs

| Field | new_issue | borderline |
|-------|-----------|------------|
| `case_boundary` | `new_issue` | `borderline` |
| `client_reply_draft` | Continuity line + domain-specific second sentence | Ask office + invite scope clarification |
| `broker_next_step` | Prefix `Case boundary: possible new issue…` | Prefix `Case boundary unclear…` |
| `conversation_summary` | Prefix `Boundary: new_issue (prior=…; last=…)` | Prefix `Boundary: borderline (prior=…)` |
| `human_confirmation_required` | false (broker prefix only) | true + `case_topic_boundary` in `human_confirmation_fields` |

Same-case: **omit** `case_boundary`; do not prefix broker line.
