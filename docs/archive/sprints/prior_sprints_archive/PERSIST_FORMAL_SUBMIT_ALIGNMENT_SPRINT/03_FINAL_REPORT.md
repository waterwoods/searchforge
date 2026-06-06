# PERSIST / FORMAL-SUBMIT — Final report

## Implemented

- **`TriageRequest.formal_submit`** on `POST /api/inbox/triage` with documented semantics.
- **Add-Car lane detection:** `soft_route == add_car` or `_is_add_vehicle_request` over full thread text.
- **Persist rule:** For Add-Car lane, `save_case` only when `formal_submit` and (`handoff_ready` or rule-complete thread via `_extract_add_car_fields` + `_add_car_enough_for_handoff`). Other intents: unchanged (`handoff_ready` only).
- **Frontend:** `triageMessage(..., formalSubmit)`; customer entry sets `true` only when last system triage is `handoff_pending` in Add-Car lane; broker workbench + founder demo queue pass `true`.
- **Tests:** `scripts/test_inbox_triage_api.py` two-step Add-Car; `scripts/test_client_identity_append.py` adds `formal_submit: true`.

## Partial / honest limits

- **Natural-language Add-Car without `soft_route` and without phrases matching `_is_add_vehicle_request`:** Treated as non–Add-Car for the gate; could persist on first `handoff_ready` (pre-existing ambiguity).
- **Discrete “submitted_at” event** is still not stored; `created_at` remains the honesty proxy for timing copy.
- **Talk-to-agent** shortcut path unchanged (still optional persist on `persist_case` without this gate).

## Deploy

- **Backend:** `bash scripts/deploy_rag_demo.sh` (with `.env.cloudrun` sourced). Revision **`fiqa-api-00045-qrq`**. URLs: `https://fiqa-api-g7zatxrycq-uw.a.run.app` (also `https://fiqa-api-1013093472160.us-west1.run.app`).
- **Frontend:** `cd ui && vercel --prod --yes`. Alias **`https://ui-smoky-beta.vercel.app`** (deployment `ui-863x3pgl5-andys-projects-1f411b73.vercel.app`).

## Smoke (production API)

- Step 1: full Add-Car, `persist_case: true`, `formal_submit: false` → no `case_id`, `handoff_pending`.
- Step 2: formal line + `formal_submit: true` + turns → `case_id` returned, `handed_off`.

## Recommended next sprint

- Optional **explicit `submitted_at`** (or activity event) when formal submit persists, for queue scanability and copy truth.
- Tighten **Add-Car lane detection** if we see misclassified free-text Add-Car without button intent.
