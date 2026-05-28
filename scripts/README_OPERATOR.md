# Operator Scripts — Unified Intake (The 10 That Matter)

**Purpose:** The only shell entry points for paid pilot, broker trial, and 2am ops.  
**Full surface:** [`docs/runbooks/OPERATOR_SURFACE.md`](../docs/runbooks/OPERATOR_SURFACE.md)  
**Ignore the rest:** ~460 other files in `scripts/` are lab, regression batteries, or historical SearchForge flows.

---

## The 10 scripts

| # | Script | When |
|---|--------|------|
| 1 | `bash scripts/run_demo_local.sh` | Start local workbench (`:8001`) |
| 2 | `bash scripts/deploy_paid_pilot.sh` | Paid pilot Cloud Run deploy |
| 3 | `PYTHONPATH=. python3 scripts/validate_pilot_deploy_env.py` | Pre-deploy env gate |
| 4 | `bash scripts/guardrail_inbox_triage.sh` | Intake regression guardrail |
| 5 | `bash scripts/trial_launch_check.sh` | **Before first broker trial** (single launch entry) |
| 6 | `bash scripts/trial_readiness_check.sh` | Posture + build readiness |
| 7 | `bash scripts/summarize_readiness_posture.sh` | Local/live readiness summary |
| 8 | `bash scripts/summarize_support_posture.sh` | Support manifest human summary |
| 9 | `bash scripts/restore_8001_readiness.sh` | Recovery from 503 / embedding_warming |
| 10 | `bash scripts/demo_pre_checklist.sh` | Pre-demo founder checklist |

---

## Founder trial — one path

```bash
bash scripts/trial_launch_check.sh
# then read docs/trial/FOUNDER_LAUNCH_NOTES.md
```

`founder_pre_trial_checklist.sh` still works (execution-depth checklist). For **launch**, prefer `trial_launch_check.sh`.

---

## Engineer extras (not operator daily)

| Script | When |
|--------|------|
| `PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py` | Scenario pack regression |
| `python3 scripts/test_inbox_triage_api.py` | API smoke (server on 8001) |
| `bash scripts/demo_quick_validate.sh` | Quick intake API validate |

---

## Lab / historical — do not use as operator entry

See [`scripts/LAB_ONLY_SCRIPTS.md`](./LAB_ONLY_SCRIPTS.md).

Examples: `start_all.sh`, `dev_local.sh`, `deploy_rag_demo.sh`, `deploy_cloud_run_core.sh`, `make ci`, `make gpu-smoke`.
