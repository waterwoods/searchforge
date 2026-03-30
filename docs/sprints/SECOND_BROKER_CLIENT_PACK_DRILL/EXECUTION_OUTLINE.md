# Execution Outline

1. **Read** INDEX + blueprint; confirm scope is drill-only.
2. **Audit** using CURRENT_PORTABILITY_AUDIT_SPEC + code paths in `config_loader.py`, `triage.py`, `inbox_triage.py`, UI client config.
3. **Author** SECOND_BROKER_CLIENT_PACK_SPEC and add `configs/clients/socal_precision/*.json`.
4. **Minimal code** only if drill is blocked — this sprint added `转接人工` to shared talk-to-agent detection.
5. **Author** `drill_scenarios.json` + `scripts/run_second_broker_drill.py`.
6. **Validate**
   - `PYTHONPATH=. python3 scripts/run_second_broker_drill.py`
   - `bash scripts/guardrail_inbox_triage.sh`
   - `cd ui && npm run build` if UI touched (unchanged this sprint; run for regression signal).
7. **Write** PORTABILITY_GAPS_SPEC + FINAL_REPORT (honest judgment).
8. **Founder pass** FOUNDER_INSPECTION_NOTES + optional live `?client=socal_precision` smoke with server on 8001.
