# Reply Template Fix Spec

## Config

`configs/industries/insurance/add_car_rules.json`

- **ask_zip.zh**: `先把邮编发我，我就能继续帮您报价。`
- **ask_vehicle.zh**: `先把年份和车型发我，我就能继续帮您报价。`

(English strings unchanged.)

## Code

`services/fiqa_api/inbox_triage/triage.py`

| Area | Change |
|------|--------|
| `_merged_and_last_customer_for_add_car_draft` | New helper: if input already has `[客户]` lines, use as merged; else wrap single utterance. |
| `_build_client_reply_draft` (add-car zh/en) | Use helper for `_extract_add_car_fields` and pass **merged** into `_get_add_car_acknowledgement`; hardcoded zh “zip missing” line aligned with rules tone. |
| `_get_add_car_acknowledgement` | If argument contains `[客户]`, take **last** segment for `msg` (fixes length gate + correction detection); add **rich `concrete`** branch before year-only thin ack. |
| `_is_add_car_vehicle_correction_signal` | `不是.{1,48}是` + vehicle token check; `不对[,，]?是` + vehicle; `搞错了` + `是` + vehicle/year. |
| `_get_next_ask_for_add_car` | Trailing space after ack **only for non-zh**; zh fallbacks aligned with new copy. |

## Handoff prefix (existing)

- `triage_conversation` already prepends **「好的，我按 {vc} 这台车继续。」** on add-car handoff when the last message is a vehicle correction; left intact.
