# Scripts Directory

**Unified Intake operators:** read [`README_OPERATOR.md`](./README_OPERATOR.md) — **10 scripts matter**.

**SearchForge lab / regression:** see [`LAB_ONLY_SCRIPTS.md`](./LAB_ONLY_SCRIPTS.md) — safe to ignore for paid pilot.

---

## Quick start (product)

```bash
bash scripts/run_demo_local.sh
# → http://localhost:5173/workbench/unified-intake
```

| Role | Command |
|------|---------|
| Founder demo | `bash scripts/demo_pre_checklist.sh` |
| Broker trial launch | `bash scripts/trial_launch_check.sh` |
| Deploy paid pilot | `bash scripts/deploy_paid_pilot.sh` |
| Intake guardrail | `bash scripts/guardrail_inbox_triage.sh` |
| 503 recovery | `bash scripts/restore_8001_readiness.sh` |

**Do not use:** `start_all.sh` (legacy SearchForge, port 8011) — use `run_demo_local.sh` (port 8001).
