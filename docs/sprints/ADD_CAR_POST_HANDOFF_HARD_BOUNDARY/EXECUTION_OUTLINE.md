# Execution Outline — Add-Car Post-Handoff Hard Boundary Sprint

## Loops executed

1. **Baseline audit** — customer closure UI hid chat; append only on workbench; boundary logic already in `triage_for_append`.  
2. **Scenario design** — extended `configs/case_boundary_append_scenarios.json` to **23** cases (CB-19–23 post-handoff focused).  
3. **Implement** — premium as cross-domain from add-car; zh/en draft suffix for new_issue; customer same-case Collapse + copy; broker list tags.  
4. **Retest** — `scripts/guardrail_inbox_triage.sh`, `scripts/run_case_boundary_battery.py`, `scripts/run_add_car_transaction_clarity_scenarios.py`, `cd ui && npm run build`.  
5. **Loop 4** — not run (marginal ROI after guardrail green).

## Artifacts

| Artifact | Path |
|----------|------|
| Rule changes | `services/fiqa_api/inbox_triage/triage.py` |
| UI | `ui/src/pages/UnifiedIntakePage.tsx` |
| Copy + API whitelist | `configs/clients/chen_kui/ui_copy.json`, `config_loader.py`, `clientConfig.ts` |
| Scenarios | `configs/case_boundary_append_scenarios.json` |
| Runner | `scripts/run_case_boundary_battery.py` |
