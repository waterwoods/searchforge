# Baseline Audit Spec — Add-Car Correction Replies

## Scope

`services/fiqa_api/inbox_triage/triage.py` — add-car acknowledgement, vehicle concrete extraction, next-ask composition.

## Findings (pre-fix)

| # | Issue | Symptom | Root cause |
|---|--------|---------|------------|
| 1 | **Wrong `last_customer` passed into acknowledgement** | `_build_client_reply_draft` used `single_ctx = f"[客户] {text}"` when `text` was already merged → duplicate `[客户]` segments; **or** passed **full merged string** as `last_customer_msg` to `_get_add_car_acknowledgement`. | `len(msg) > 120` **suppressed** the whole acknowledgement on long threads; correction logic never ran on the **latest bubble**. |
| 2 | **Comma between 不是…是** | e.g. `不是X5，是X3` did **not** match the narrow regex `不是[^，。\n]{0,40}是`. | First correction regex excluded comma; no fallback with vehicle tokens. |
| 3 | **Colloquial correction phrasing** | `不对，是 2024 Tesla` / `搞错了，是…` skipped the **“我按 … 这台车继续”** path. | `_is_add_car_vehicle_correction_signal` did not include these patterns. |
| 4 | **Thin non-correction ack** | Sometimes only year echoed when merged text had a longer `concrete` but slot flags were incomplete. | Branch order favoured year-only before a rich `concrete` label. |
| 5 | **UX** | Space between Chinese ack and next ask (`继续。 先把`) | Prefix always added a trailing space before the ask. |

## Broker side

- `_extract_add_car_vehicle_concrete(merged_text)` and structured fields already leaned on merged customer text; broker summary was often **already** closer to correct than the **client draft** when the draft path mishandled `last_customer`.

## Safest low-risk fix

- Normalize **merged vs last bubble** for add-car drafts; make `_get_add_car_acknowledgement` **defensively** parse the last `[客户]` segment when the first argument looks like merged text.
- Broaden **correction markers** only when **vehicle tokens** are present (avoid random 不是…是 sentences).
- Prefer **rich `concrete`** over year-only when slots are incomplete.
- **Chinese** next-ask: no extra space after acknowledgement.
