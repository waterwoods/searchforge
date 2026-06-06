# Scripts Directory

**Unified Intake operators:** read [`README_OPERATOR.md`](./README_OPERATOR.md) — **10 scripts matter**.

**Discoverability:** same 10 scripts also live under [`operator/`](./operator/) as thin wrappers (forwards to parent `scripts/`).

**Founder demo/trial:** [`founder/`](./founder/) — rehearsal wrappers (same behavior).

**SearchForge lab / regression:** [`lab/`](./lab/) wrappers print **LAB ONLY** banner → see [`LAB_SCRIPT_INDEX.md`](./LAB_SCRIPT_INDEX.md) and [`LAB_ONLY_SCRIPTS.md`](./LAB_ONLY_SCRIPTS.md).

**Deploy guidance:** [`deploy/`](./deploy/) wrappers point to `deploy_paid_pilot.sh` → see [`DEEP_SCRIPT_TIER_MAP.md`](./DEEP_SCRIPT_TIER_MAP.md).

**Historical stubs:** [`archive/`](./archive/) — do not add new scripts here.

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
