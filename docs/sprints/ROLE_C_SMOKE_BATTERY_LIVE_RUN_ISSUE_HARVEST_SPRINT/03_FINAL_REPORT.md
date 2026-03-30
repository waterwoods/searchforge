# Final report — ROLE C SMOKE BATTERY LIVE RUN + ISSUE HARVEST

## What was run

- **Backend:** `https://fiqa-api-g7zatxrycq-uw.a.run.app` (Cloud Run).
- **Client:** `chen_kui`.
- **Flow:** For each case, loop `POST /api/inbox/simulation-role-c-customer` then `POST /api/inbox/triage` with `persist_case: false`, `soft_route: add_car`, same `session_id` per case; full transcript passed as `conversation_turns` (prior turns only on triage request, matching `scripts/run_role_c_add_car_battery.py`).
- **Cases:** C1–C5 per `02_BATTERY_AND_ISSUE_HARVEST_SPEC.md` (34 customer turns total).
- **Verified:** `health/live` 200; Role C returns non-empty `customer_message` with `model` set; triage returns `lifecycle_status`, `collected_fields`, `still_needed_fields`, `quote_ready_status`, `client_reply_draft`, `issue_category`, `broker_next_step`.

## Issues found (summary)

See the Cursor sprint output titled **ROLE C SMOKE BATTERY LIVE RUN + ISSUE HARVEST Report** for the full classified list, rankings, and founder Q&A. This file is the durable sprint record; the chat report is the operator-facing digest.

## Highest-impact themes (evidence-backed)

1. **Contact extraction gap** — In C1/C2, customer turns explicitly gave name + phone (`李华` / `张伟` + `555-1234`); `collected_fields` did not reliably pick up `phone` (and in C2, neither name nor phone), while `still_needed_fields` and `broker_next_step` continued to demand them. C5 partially absorbed `phone` in one turn but left `name` missing after “我的名字是张伟” in the same message—**asymmetric extraction**.
2. **Handoff reply truth vs state** — Repeated post-handoff lines of the form “若姓名或电话尚未在本对话中写清…” appeared **after** the customer had supplied phone or name in that same session, which is **misaligned with the transcript** and reads as robotic.
3. **`issue_category` / routing** — Many post-handoff, add-car-relevant questions were labeled `missing_document` (C1, C2, C3, C5) even when the substance was timing, coverage education, or premium—**right-rail and broker signals risk looking like “缺材料”** when the customer is not in a missing-doc workflow.

## Recommended next sprint (single)

**Truth-aligned post-handoff replies + contact-field extraction hardening for conversational Chinese (Add-Car, handoff_pending).**

- **Why:** The battery surfaced **state/reply contradiction** (disclaimer vs actual `collected_fields`) and **sticky `still_needed`** for name/phone as the most user-visible defects; they undermine service-record credibility and the “office received you” story.

## What was not verified here

- Persistence / Postgres dual-write / workbench UI rendering (battery used `persist_case: false`).
- Localhost stack (8001 was not up in this environment; live Cloud Run used instead).
