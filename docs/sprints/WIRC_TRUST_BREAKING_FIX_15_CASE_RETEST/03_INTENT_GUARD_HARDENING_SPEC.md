# Intent Guard Hardening Spec

## Purpose

Separate two intents:

- **Prospective send** — “May I / should I / OK if I send …?”  
- **Completed send** — “I sent / already sent / 发你微信了 …”

## Primary functions

### `_is_prospective_send_offer_message(msg: str) -> bool`

**Runs before** any “already sent” or “screenshot_sent” style heuristic.

**Detects (non-exhaustive):**

- 要不要…发, 要不要先…(发|给你…)
- 我可以 / 可不可以 / 能不能 … 先发 / 发你
- 先发你…(行吗|可以吗|好不好|吗|嘛)
- 先给你…看 + question tone
- Clause with ? / 吗 / 行吗 / 可以吗 plus 截图|vin|材料|行驶证|registration|微信 and 发|给 (excluding completed phrases)
- English: `can/could/should/may I send`, `OK if I send`

**Explicit negatives:** if the message already contains high-confidence **completed** markers (发你了, 发过了, already sent, I’ve sent, …), return **False**.

### `_message_claims_completed_material_send(msg: str) -> bool`

**Returns True** only when wording asserts submission, e.g.:

- 发过了, 发你了, 发你微信了, 又发了, 已经发…, I sent / already sent / sent it (bounded heuristics)
- 发了 (with guards for 发了吗 questions and 发现 false positive)
- 截图/screenshot **together with** completion cues (发了, 发你了, sent, 微信了, …)
- Regex `发[你我您](微信)?[了过]`

**Always returns False** if `_is_prospective_send_offer_message` is True or English permission-to-send pattern matches.

## Call sites updated in this sprint

- `_derive_follow_up_type` — `already_sent` only via `_message_claims_completed_material_send`
- `_build_client_reply_draft` — short `unclear` zh/en branches
- `_build_conversation_summary` — “Client says already sent” via per-segment completion check; payment branch screenshot hint gated
- `_extract_cancellation_fields` — `screenshot_sent` via completion check per customer segment
- `_is_fast_path_candidate` — short completed-send fast path
- `triage_conversation` — `add_car_materials_sent` / `add_car_already_sent` broker copy aligned with completion detection

## Regression protection

- True positives: 材料发你微信了, 我已经把截图发你了, 发你了 (short) still map to completed send where appropriate.
- Guardrail scenario **HT13** (我已经发你微信了) must remain handoff-positive.
