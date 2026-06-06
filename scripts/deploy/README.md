# Deploy Scripts — Unified Intake Paid Pilot

**Paid pilot entry (only operator deploy):**

```bash
bash scripts/deploy_paid_pilot.sh
```

**Pre-deploy validate:**

```bash
PYTHONPATH=. python3 scripts/validate_pilot_deploy_env.py --env-file .env.cloudrun
```

---

## Wrappers in this directory

Each wrapper prints guidance and forwards to the canonical script or legacy impl.

| Wrapper | Points to | Note |
|---------|-----------|------|
| `deploy_paid_pilot.sh` | `scripts/deploy_paid_pilot.sh` | **Canonical paid pilot** |
| `deploy_rag_demo.sh` | deprecated → `deploy_paid_pilot.sh` guidance | Legacy name |
| `deploy_cloud_run.sh` | deprecated → `deploy_paid_pilot.sh` | SearchForge legacy |
| `deploy_cloud_run_core.sh` | impl only → use `deploy_paid_pilot.sh` | Not operator entry |
| `deploy_and_verify_cloud_run.sh` | deprecated → `deploy_paid_pilot.sh` | Old verify flow |
| `deploy_demo_cloud_smoke.sh` | `scripts/deploy_demo_cloud_smoke.sh` | Demo smoke only (DEMO_MODE) |

**Truth map:** [`docs/runbooks/DEPLOY_TRUTH_MAP.md`](../../docs/runbooks/DEPLOY_TRUTH_MAP.md)

**Do not use for broker trial:** lab deploy wrappers under `scripts/lab/`.
