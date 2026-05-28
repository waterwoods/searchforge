# E2E Proof Spec — Timestamp Invariants

## Preconditions

- API base URL (e.g. `http://127.0.0.1:8001`).
- `GET /readyz` returns `ok: true` (after warmup if needed).

## Step 1 — Formal submit (Add-Car)

1. `POST /api/inbox/triage` with full handoff-ready Add-Car text, `persist_case: true`, `formal_submit: false` → expect **no** `case_id`, `lifecycle_status` `handoff_pending`.
2. `POST /api/inbox/triage` with formal-submit phrase, `persist_case: true`, `formal_submit: true`, plus `conversation_turns` echoing step 1 → expect `case_id`, `lifecycle_status` `handed_off` (or equivalent office-visible state).

**Assert**

- `formal_submitted_at` present and equals `created_at` on first persist.
- `updated_at` present (typically same instant as create on first write).

## Step 2 — Append

`POST /api/inbox/cases/{case_id}/append-message` with non-empty `new_message`.

**Assert**

- `formal_submitted_at` unchanged vs step 1.
- `updated_at` strictly newer than after step 1 (allow ≥1s sleep if comparing strings).
- State remains coherent (e.g. lifecycle may move to `office_followup`; no loss of `case_id`).

## Automation

- Full battery: `python3 scripts/test_inbox_triage_api.py --url <base>`.
- Timestamp delta check: optional small httpx script with `sleep(1)` between create and append.

## UI (optional)

If a deployed UI matches this API: confirm portal/workbench show first formal time vs recent activity. If not deployed, API proof stands alone.
