# Remote proof spec — formal submit + append timestamps

## Preconditions

- Cloud Run base URL (HTTPS), e.g. `https://fiqa-api-….run.app`.
- `GET {base}/readyz` returns 200 with intake readiness acceptable for demo.

## Step 1 — Formal submit (Add-Car)

1. `POST {base}/api/inbox/triage` with a **full** Add-Car message, `persist_case: true`, `formal_submit: false`.
   - Expect: no `case_id`, `handoff_ready: true`, `lifecycle_status: handoff_pending`.
2. `POST {base}/api/inbox/triage` with formal-submit line, `persist_case: true`, `formal_submit: true`, and `conversation_turns` mirroring step 1 + system draft.
   - Expect: `case_id` present.
   - Expect: `lifecycle_status` office-visible (e.g. `handed_off`).
   - Expect: `formal_submitted_at` non-empty; matches `created_at` on first persist.
   - Expect: `updated_at` non-empty.

## Step 2 — Append / follow-up

1. Optional: sleep 2–3s so clock delta is obvious.
2. `POST {base}/api/inbox/cases/{case_id}/append-message` with a non-empty `new_message`.
   - Expect: 200, same `case_id`.
   - Expect: `formal_submitted_at` **unchanged** vs Step 1.
   - Expect: `updated_at` **changed** and strictly newer than Step 1 (ISO-8601 `Z` strings sort lexicographically).

## Step 3 — UI sanity (if not doing full click-through)

- Load `https://ui-smoky-beta.vercel.app` (or current production alias).
- Confirm production JS references the same Cloud Run host as Step 1.
- Confirm bundle contains timing surfaces (`formal_submitted_at` / labels).
- `OPTIONS` + `POST` CORS from Vercel `Origin` to `/api/inbox/triage` should succeed with matching `access-control-allow-origin`.

## Automation reference

- `scripts/test_inbox_triage_api.py --url <base>` — Test 13 covers formal-submit + append; add an explicit `updated_at` check in a one-off script if the script is ever trimmed.
