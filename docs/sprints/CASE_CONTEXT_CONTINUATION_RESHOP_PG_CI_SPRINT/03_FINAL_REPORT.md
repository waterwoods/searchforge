# CASE-CONTEXT CONTINUATION + RE-SHOP + POSTGRES REGRESSION — Final report

## What was simulated

- **Guardrail**: full `scripts/guardrail_inbox_triage.sh` (scenarios, multi-turn, case boundary battery, persistence checks).
- **NA-Chinese battery**: `scripts/run_na_chinese_20_case_sprint_battery.py` (rule path, no persist) — spot-check structure.
- **High-risk battery + Postgres**: `scripts/run_disposable_pg_dual_write_regression.py --apply-schema` against **disposable** `postgres:16-alpine` on port **54339** (container removed after run).
- **Ad-hoc append checks**: `triage_for_append` with prior add-car + re-shop text; prior add-car + “我老婆那台也想加…”.

## What improved

1. **`_is_add_vehicle_request`** — New branch for **太贵/换公司/再报…** when merged text already has **quote/coverage/company/提车/year/zip/vehicle_context** signals (re-shop **without** requiring “上次报的价”). Spouse / referent pattern **也想加/也要加** + **那台** + household terms.
2. **`_classify_append_case_boundary`** — **Critical fix**: last-bubble-only `premium_review` markers no longer force **new_issue** on an **open add-car** thread when the message is classified as price / re-shop / re-quote follow-up (`_is_add_car_price_reshop_or_requote_followup`).
3. **Thin continuation** — **还缺啥** aligned with **还缺什么** in guardrails; **发了一次** allowed alongside **又发** for “已发 + 还缺什么” style turns.
4. **Config** — `markers.json` **add_vehicle**: **也想加**.
5. **Automation** — `scripts/run_disposable_pg_dual_write_regression.py`: psycopg schema apply + high-risk battery + **row counts** + PASS/FAIL.

## What persisted well

- Dual-write inserts for **16** `service_records`, **16** `structured_record_data`, **19** `record_messages`, **17** `state_history` on the regression run (counts depend on battery; script enforces minimum service_records).

## What remained weak

- **Single-turn** material echo (“registration 又发邮箱…”) still needs **case/thread** from product layer — not solved by rules alone.
- **Very thin** renewal-only wording (“续保太贵…”) without quote/carrier/coverage/year/zip can still avoid add-car routing — intentional ambiguity.
- **JSON remains authoritative**; no new read path.

## What was automated

- One-command disposable DB regression: `run_disposable_pg_dual_write_regression.py` (see script docstring for `docker run` example).

## Recommended next sprint

1. **API/UI thread context** for material-only follow-ups when `case_id` exists (S12-class).
2. **Read-path spike** or **dual-read parity** for a single office field — only when pilot-ready.
3. Wire regression script into **CI** (job with service container) when repo CI allows Docker.

## Timing

See chat output **§14** for start/end/elapsed.
