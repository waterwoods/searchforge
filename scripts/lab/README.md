# Lab Scripts — SearchForge R&D Only

**Status:** LAB ONLY — not Unified Intake paid pilot  
**Product path:** [`scripts/README_OPERATOR.md`](../README_OPERATOR.md) → `bash scripts/run_demo_local.sh`

---

## What lives here

| Item | Purpose |
|------|---------|
| Wrappers (`start_all.sh`, `ci_smoke.sh`, …) | Print **LAB ONLY** banner → forward to parent `scripts/` |
| `host_resource_triage.sh` | Host CPU/mem/Docker sampling (moved from repo root `triage.sh`) |
| Full index | [`LAB_SCRIPT_INDEX.md`](../LAB_SCRIPT_INDEX.md) |
| Parent-level lab scripts | [`LAB_ONLY_SCRIPTS.md`](../LAB_ONLY_SCRIPTS.md) |

---

## Do not use for broker trial

| Use instead | Not this |
|-------------|----------|
| `bash scripts/run_demo_local.sh` | `start_all.sh`, `dev_local.sh` |
| `bash scripts/deploy_paid_pilot.sh` | `deploy_rag_demo.sh`, `make up` |
| `bash scripts/trial_launch_check.sh` | `make ci`, `make gpu-smoke` |

---

## Related

- [`docs/archive/platform/README_LAB_INFRA.md`](../../docs/archive/platform/README_LAB_INFRA.md)
- [`docs/runbooks/OPERATOR_IGNORE_LIST.md`](../../docs/runbooks/OPERATOR_IGNORE_LIST.md)
