# P16-Z13 Phase 2 — Deploy Readiness

**Date:** 2026-06-02

---

## Result

**PASS**

---

## Command

```bash
PYTHONPATH=. python3 scripts/validate_pilot_deploy_env.py --env-file .env.cloudrun
```

Exit code: **0**

```
OK pilot deploy env (.env.cloudrun)
  Unified Intake SaaS posture (product_only + Postgres-primary)
  Postgres cases enabled (when SERVICE_RECORD_DATABASE_URL set)
  Product-only API surface — lab/RAG routers not mounted
  Intake + support API keys required
  Intake triage does not require Qdrant (vectors = optional wedge)
  Vectors optional in intake mode (QDRANT_* not required for deploy)
```

---

## Blockers cleared (vs P16-Z12)

| Item | Z12 | Z13 |
|------|-----|-----|
| `UNIFIED_INTAKE_INTAKE_API_KEY` | ❌ | ✅ |
| `UNIFIED_INTAKE_SUPPORT_API_KEY` | ❌ | ✅ |
| Keys differ | n/a | ✅ |
| `CLOUD_RUN_USE_SECRET_MANAGER` | ❌ | ✅ `=1` (OpenAI/DB/Qdrant via SM; avoids OPENAI literal type conflict) |
| Qdrant preflight | ❌ 404 | ✅ Skipped (Qdrant lines commented; `UNIFIED_INTAKE_INTAKE_CORE_READINESS=1`) |

---

## Missing items

None for validator. Operational notes:

- Qdrant URL in `.env.cloudrun` is **commented** until cluster URL/key are valid again.
- Each new Vercel preview hostname must be appended to `ALLOWED_ORIGINS` before browser triage works.

---

## Exact deploy command

```bash
bash scripts/deploy_paid_pilot.sh
```
