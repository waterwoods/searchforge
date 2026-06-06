# Acceptance Criteria — Post-Handoff Add-Car Hard Boundary

## Must pass (automated)

- [x] `bash scripts/guardrail_inbox_triage.sh` — **PASS** (includes case boundary 23/23).
- [x] `LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_case_boundary_battery.py` — **23/23**.
- [x] `LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_add_car_transaction_clarity_scenarios.py` — **8/8**.
- [x] `cd ui && npm run build` — **success**.

## Product (manual founder inspection)

- [ ] After Add-Car handoff, customer sees **status chip** + closure copy + clear **提交新问题**.  
- [ ] Optional **same-case append** works when `case_id` present; unrelated topics trigger warning toast when classified `new_issue`.  
- [ ] Workbench list shows **追加 · …** tag with correct color when follow-up applied.  
- [ ] New **续保/保费** pivot after add-car handoff classifies as **new_issue** with续保-specific draft + portal suffix.

## Explicitly out of scope

- Automatic case splitting, customer auth, carrier APIs.
