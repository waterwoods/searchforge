# Continuation, re-shop slot-carry, and Postgres regression — Spec

## 1. Weakness families

| Family | Example phrasing | Typical failure (before) |
|--------|------------------|---------------------------|
| Append + price pushback | Prior: full add-car; last: “太贵了换一家公司再报一下价” | `premium_review` markers on **last bubble** only → append boundary classified as **new_issue** vs same add-car record |
| Re-shop without “上次报价” | “保费太高想换公司，zip …，还是那台 2023 Accord” | `_is_add_vehicle_request` sometimes **false** when “太贵/换公司” appears without contiguous add-car markers in the same clause |
| Thin readiness + sent | “微信发过了还缺啥” / “又发了一次…还缺什么” | Missed colloquial **还缺啥**; “发了一次” under-covered vs “又发” |
| Spouse second vehicle | “我老婆那台也想加…” | Under-triggered vs “还想加…” |

## 2. What context-carry should do

When `triage_conversation` or `triage_for_append` builds **merged** `[客户]` text:

- **Classification** should prefer Add-Car / `customer_question` when the **thread** still clearly concerns quote intake, not generic `unclear`.
- **Slots** (`_extract_add_car_fields`) already join all customer bubbles — carry is correct if `_is_add_vehicle_request` and category path stay on add-car.

## 3. What re-shop slot-carry should do

- If merged text includes **zip / year / vehicle_context / quote / 提车 / company / coverage** together with **太贵 / 换公司 / 再报**, treat as **add-car / re-quote** intent so structured fields remain populated from earlier bubbles.

## 4. What disposable Postgres regression should guarantee

- Schema from `services/fiqa_api/db/schema/stage1_service_record.sql` applies cleanly **without psql** (psycopg).
- With `UNIFIED_INTAKE_PG_DUAL_WRITE=1` and a fresh cases JSON path, the **high-risk Add-Car battery** completes and inserts:

  - `service_records` ≥ 16 (current battery size),
  - matching `structured_record_data` rows,
  - non-zero `record_messages` and `state_history` (append scenario exercises extra rows).

- Script exits **non-zero** on battery failure or under-count.

## 5. Acceptance criteria

- [x] Append re-shop follow-up on a prior add-car thread does **not** set `case_boundary=new_issue` solely because the last message matches `premium_review` markers.
- [x] Merged-thread re-shop phrasing keeps add-car detection when zip/year/model/context present.
- [x] Colloquial **还缺啥** and **发了一次** participate in thin add-car continuation matching where applicable.
- [x] `scripts/run_disposable_pg_dual_write_regression.py --apply-schema` passes against a disposable Postgres 16 instance.
- [x] `bash scripts/guardrail_inbox_triage.sh` passes after triage changes.

## 6. Explicit non-goals

- Fixing **single-turn** “registration 又发邮箱收到吗” without `case_id` / thread (product + API concern).
- Postgres **read** API or JSON authority cutover.
