# Implementation spec — Intent visibility, identity sync, late-turn heads

## Target intent visibility model

- **Source of truth:** `resolve_add_car_turn_intent` + `_resolve_add_car_handoff_phrase_key` in `triage.py` (unchanged contract).
- **API payload:** `add_car_turn_intent` object on Add-Car triage results:
  - `intent_family` — bounded category string.
  - `handoff_base_key` — intent routing stem before `_submitted` suffix.
  - `truth_notes` — optional constraint explanations.
  - `phrase_storage_key` — **effective** handoff phrase key used for template lookup (e.g. `add_car_timeline_submitted`).

## Root cause fixed (persist path)

- `case_store._validate_triage_result` previously copied **only** seven required fields; `save_case` spread that dict into the case, **dropping** `add_car_turn_intent`.
- **Fix:** validate required fields, then **pass through** a normalized `add_car_turn_intent` blob when present. Same normalization on **append** updates.

## Target identity / lifecycle sync model

- **Thread:** Prefer contact parsed from the **latest customer turn** when it completes patterns missed in full-thread merge order.
- **Record:** When `reply_truth_context` includes `record_contact_name` / `record_contact_phone` from the loaded case, **remove** `name` / `phone` from `still_needed_fields` so JSON matches “already on service record.”
- **Lifecycle:** If `formal_submitted_at` is present, this turn is **not** a new formal submit, and `handoff_ready` is false, set `lifecycle_status` to **`office_followup`** (not `collecting`) when the case lifecycle is already post-submit.

## Target late-turn reply-head model

- When **post-submit phrasing** is allowed and the reply is a **handoff** Add-Car reply, prepend a **one-clause** opener keyed by `intent_family` (timeline, quote detail, office receipt, materials claim, supplement, correction). **Skip** generic follow-up.
- Truth: openers **do not** claim verification, quote completion, or receipt beyond existing phrase rules.

## Acceptance criteria

- [x] `add_car_turn_intent` appears on **non-persist** `POST /api/inbox/triage` Add-Car responses when `is_add_car`.
- [x] `add_car_turn_intent` survives **`save_case` / persist** return payload and **append** updates.
- [x] Explicit **姓名/名字/手机** lines improve contact extraction; **case-backed** contact clears `still_needed` for name/phone where applicable.
- [x] Post-submit handoff replies for at least **timeline vs quote-detail** show **different Chinese openers** in spot checks (office-receipt covered by same mechanism).
- [x] `bash scripts/guardrail_inbox_triage.sh` passes.
