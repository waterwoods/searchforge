# Trust-Breaking Add-Car Fix Blueprint

## Problem statement

Customers often ask **permission or offer** to send VIN / screenshot / registration materials using phrasing that includes words like 截图, 发你, or VIN. The system must **not** respond as if they already said “I sent it,” which sounds false and erodes broker trust.

## Target behavior

| Customer says (examples) | Must behave as |
|--------------------------|----------------|
| VIN 我可以先发你截图吗 | Offer / question → short yes + next intake step |
| 我先发你 VIN 截图行吗 | Same |
| 截图要不要先发你 | Same (no “您是说发过了吗”) |
| VIN 要不要先给你看一下 | Same |
| 要不要把行驶证截图先发你 | Same |
| 材料发你微信了 / 我已经把截图发你了 | Completed send → verify / office handoff tone |

## Non-goals (this sprint)

- UI redesign, OCR, carrier APIs, non–add-car features, full architecture rewrites.

## Implementation strategy (pattern-level)

1. **Intent guard expansion** — `_is_prospective_send_offer_message` recognizes CN/EN permission-to-send patterns (可以吗 / 行吗 / can I send / 要不要先给你看, etc.).
2. **Completed-send precision** — `_message_claims_completed_material_send` replaces loose `sent_markers` that treated bare **截图** or substring **发你** as “already sent.”
3. **Downstream consistency** — broker summary `context_hint`, payment-risk `collected_hint`, cancellation `screenshot_sent`, short `unclear` paths, and fast-path rules use the same completion detector and guard.
4. **First-turn tolerance** — narrow add-car routing when **VIN + prospective materials question**, or **行驶证/registration + prospective send**, so utterances are not dumped into generic unclear without an answer.
5. **Lexicon** — `vehicle_context` + `_extract_add_car_fields` + `_add_car_vehicle_concrete_from_scope` extended for Nissan Altima and common CN/EN mixed tokens used in trials.

## Verification

- `scripts/run_wirc_trust_breaking_15_retest.py` (15 cases, `LLM_GENERATION_ENABLED=false`).
- `bash scripts/guardrail_inbox_triage.sh`
- `PYTHONPATH=. python3 scripts/run_web_informed_add_car_realistic_battery.py`
