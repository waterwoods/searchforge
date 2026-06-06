# Deep Script Tier Map — P8 Physical Separation

**Purpose:** Visual separation of ~477 scripts into operator / founder / deploy / lab / archive tiers.  
**Historical paths preserved** at `scripts/` root — tiers are wrappers/stubs/symlinks only.

**Product truth:** [`README_OPERATOR.md`](./README_OPERATOR.md) (10 scripts)  
**Lab index:** [`LAB_SCRIPT_INDEX.md`](./LAB_SCRIPT_INDEX.md)

---

## Tier overview

```
scripts/
├── operator/     ← 10 product scripts (wrappers → root impl)
├── founder/      ← 3 demo/trial wrappers
├── deploy/       ← 6 deploy wrappers (→ deploy_paid_pilot.sh guidance)
├── lab/          ← 18+ LAB ONLY banner wrappers
├── archive/      ← historical stub pointer
└── *.sh (flat)   ← preserved for backward compat — use tiers to discover
```

---

## operator/ — Unified Intake paid pilot (10)

| Wrapper | Forwards to |
|---------|-------------|
| `run_demo_local.sh` | `scripts/run_demo_local.sh` |
| `deploy_paid_pilot.sh` | `scripts/deploy_paid_pilot.sh` |
| `validate_pilot_deploy_env.sh` | `scripts/validate_pilot_deploy_env.py` |
| `guardrail_inbox_triage.sh` | `scripts/guardrail_inbox_triage.sh` |
| `trial_launch_check.sh` | `scripts/trial_launch_check.sh` |
| `trial_readiness_check.sh` | `scripts/trial_readiness_check.sh` |
| `summarize_readiness_posture.sh` | `scripts/summarize_readiness_posture.sh` |
| `summarize_support_posture.sh` | `scripts/summarize_support_posture.sh` |
| `restore_8001_readiness.sh` | `scripts/restore_8001_readiness.sh` |
| `demo_pre_checklist.sh` | `scripts/demo_pre_checklist.sh` |

---

## founder/ — Demo and trial (3)

| Wrapper | Forwards to |
|---------|-------------|
| `run_demo_local.sh` | `scripts/run_demo_local.sh` |
| `demo_pre_checklist.sh` | `scripts/demo_pre_checklist.sh` |
| `founder_pre_trial_checklist.sh` | `scripts/founder_pre_trial_checklist.sh` |

**Canonical launch:** `trial_launch_check.sh` (in operator/) — see [`docs/FOUNDER_ONE_PATH.md`](../docs/FOUNDER_ONE_PATH.md)

---

## deploy/ — Cloud Run deploy guidance (6)

Every wrapper prints deploy guidance; paid pilot → `deploy_paid_pilot.sh`.

| Wrapper | Forwards to | Note |
|---------|-------------|------|
| `deploy_paid_pilot.sh` | root impl | **Canonical** |
| `deploy_rag_demo.sh` | root (deprecated) | Legacy name |
| `deploy_cloud_run.sh` | root (legacy) | SearchForge name |
| `deploy_cloud_run_core.sh` | root impl | **Not operator entry** |
| `deploy_and_verify_cloud_run.sh` | root (legacy) | Old verify |
| `deploy_demo_cloud_smoke.sh` | root | DEMO_MODE smoke only |

---

## lab/ — SearchForge R&D (18+)

All print: **`LAB ONLY — not part of Unified Intake paid pilot path`**

| Wrapper | Forwards to | Category |
|---------|-------------|----------|
| `start_all.sh` | `start_all.sh` | Multi-service :8011 |
| `dev_local.sh` | `dev_local.sh` | SearchForge dev :8000 |
| `start_services.sh` | `start_services.sh` | Old bootstrap |
| `deploy_rag_demo.sh` | `deploy_rag_demo.sh` | Deprecated deploy |
| `ci_smoke.sh` | `ci_smoke.sh` | ETF `/api/query` |
| `warmup_for_demo.sh` | `warmup_for_demo.sh` | Vector warmup |
| `seed_local_qdrant.sh` | `seed_local_qdrant.sh` | Qdrant seed |
| `seed_qdrant.sh` | `seed_qdrant.py` | Qdrant seed (py) |
| `run_full_regression.sh` | `run_full_regression.py` | Full regression |
| `run_canary_full_100.sh` | `run_canary_full_100.sh` | Canary lab |
| `wait_for_gpu_ready.sh` | `wait_for_gpu_ready.sh` | GPU |
| `gpu_worker_smoke.sh` | `gpu_worker_smoke.py` | GPU smoke |
| `verify_milvus_lane.sh` | `verify_milvus_lane.sh` | Milvus |
| `graph_verify.sh` | `graph_verify.sh` | Graph |
| `autotuner_demo.sh` | `autotuner_demo.py` | AutoTuner |
| `stop_all.sh` | `stop_all.sh` | Paired with start_all |
| `health_check.sh` | `health_check.sh` | Lab health |
| `host_resource_triage.sh` | (local) | Host sampling |

---

## archive/ — Historical pointer

Stub README only — impl remains at flat root. Do not add new scripts here.

---

## High-confusion flat scripts (no wrapper yet — use lab tier or ignore)

| Script | Tier intent | Use instead |
|--------|-------------|-------------|
| `run_*_battery*.py`, `run_*_simulation*.py` | lab | `guardrail_inbox_triage.sh` |
| `run_canary_*.py` | lab | N/A for pilot |
| `verify_qdrant*.py`, `migrate_local_qdrant*.py` | lab | Optional wedge |
| `deploy_vitals_*.sh` | lab/archive | N/A for intake pilot |
| `auto_rca.sh`, `black_swan*.sh` | lab | N/A for pilot |

---

## Product path reminder

```bash
bash scripts/run_demo_local.sh
bash scripts/deploy_paid_pilot.sh
bash scripts/trial_launch_check.sh
bash scripts/guardrail_inbox_triage.sh
```

See: [`docs/runbooks/OPERATOR_IGNORE_LIST.md`](../docs/runbooks/OPERATOR_IGNORE_LIST.md)

---

*P8 deep script tier map — wrappers only, no runtime change*
