# Acceptance Criteria

- [x] After **vehicle correction**, Chinese reply **starts with** explicit effective vehicle: **「好的，我按 … 这台车继续。」** when model/year (or resolvable label) is available.
- [x] **No** reliance on year-only acknowledgement when a **≥5 character** concrete vehicle label is available from merged extraction (unless correction path already returned).
- [x] **Comma** between 不是…是 (e.g. `不是X5，是X3`) still counts as vehicle correction.
- [x] **不对…是** and **搞错了…是** (with vehicle/year) count as vehicle correction.
- [x] **Long threads**: if a caller mistakenly passes full merged text as `last_customer_msg`, acknowledgement still uses the **last** `[客户]` bubble (no silent drop from `len > 120`).
- [x] **Chinese** next-ask lines: no stray space between `。` and the next sentence.
- [x] **ask_zip / ask_vehicle** Chinese copy uses **继续帮您报价** where configured.
- [x] `bash scripts/guardrail_inbox_triage.sh` **PASS**
- [x] `PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py` — **0 weak**
- [x] `PYTHONPATH=. python3 scripts/run_add_car_edge_case_simulations.py` — **0 weak**
