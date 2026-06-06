# P16-Z12 Phase 2 — Backend Deploy Blocker

**Date:** 2026-06-02

---

## Can backend deploy proceed?

**NO** — stopped before `gcloud run deploy`.

---

## Blocker

`bash scripts/deploy_paid_pilot.sh` calls `validate_pilot_deploy_env.py` under paid-pilot posture. Local `.env.cloudrun` fails:

```
FAIL pilot deploy env (.env.cloudrun):
  - UNIFIED_INTAKE_INTAKE_API_KEY must be set (24+ char random)
  - UNIFIED_INTAKE_SUPPORT_API_KEY must be set (24+ char random)
```

**No secrets invented.** Keys are not in:

- `.env`, `.env.cloudrun.test` (checked — absent)
- GCP Secret Manager (only OpenAI, Qdrant, DB URL secrets exist)
- Live Cloud Run env (intake/support keys never bound on `fiqa-api-00080-q48`)

---

## Safe reuse options (documented, not executed)

| Option | Viability |
|--------|-----------|
| Reuse from Cloud Run describe | ❌ Keys were never deployed to Cloud Run |
| Secret Manager bind for intake keys | ❌ Secrets do not exist yet — must be created in GCP + IAM |
| Deploy without validator | ❌ `deploy_paid_pilot.sh` hard-fails validation |
| Skip keys (open perimeter) | ❌ Validator requires keys for paid pilot; operational risk if bypassed |

---

## Exact manual fix required (Andy)

1. **Generate two distinct random secrets** (24+ chars each), e.g.:
   ```bash
   openssl rand -hex 24   # run twice — intake vs support
   ```
2. **Append to `.env.cloudrun`** (gitignored):
   ```
   UNIFIED_INTAKE_INTAKE_API_KEY=<value1>
   UNIFIED_INTAKE_SUPPORT_API_KEY=<value2>
   ```
3. **Re-validate:**
   ```bash
   PYTHONPATH=. python3 scripts/validate_pilot_deploy_env.py --env-file .env.cloudrun
   ```
4. **Add Preview origin to CORS** in `.env.cloudrun` `ALLOWED_ORIGINS`:
   ```
   https://ui-d7pyq2yau-andys-projects-1f411b73.vercel.app
   ```
   (Keep existing origins; comma-separate.)
5. **Deploy:**
   ```bash
   bash scripts/deploy_paid_pilot.sh
   ```

**Optional (recommended for prod hygiene):** Create Secret Manager secrets `fiqa-unified-intake-api-key` and `fiqa-unified-intake-support-api-key`, grant Cloud Run SA accessor, extend `deploy_cloud_run_core.sh` `--set-secrets` — out of scope for this sprint (no code changes requested).

---

## Command attempted

```bash
PYTHONPATH=. python3 scripts/validate_pilot_deploy_env.py --env-file .env.cloudrun
# exit 1 — deploy not invoked
```

---

## If keys are added

Canonical deploy path:

```bash
bash scripts/deploy_paid_pilot.sh
```

Post-deploy verify:

```bash
curl -sS https://fiqa-api-g7zatxrycq-uw.a.run.app/readyz
# Confirm GIT_SHA / revision updated; DEMO_MODE=0; UNIFIED_INTAKE_PRODUCT_ONLY=1
```
