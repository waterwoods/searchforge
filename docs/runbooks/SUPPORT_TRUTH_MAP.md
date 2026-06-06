# Support Truth Map — Unified Intake

For operators supporting a broker pilot. **Not** enterprise SIEM / multi-tenant admin.

---

## Primary support surface

| Endpoint | Auth | Returns |
|----------|------|---------|
| `GET /api/inbox/support/deployment-manifest` | `UNIFIED_INTAKE_SUPPORT_API_KEY` | Posture, warnings, persistence mode, readiness hints |

**Use this first** when debugging prod without SSH.

---

## Warning codes (manifest)

Inspect `warnings[]` in manifest JSON. Common codes (see `deployment_profile.py`):

| Code class | Meaning | Action |
|------------|---------|--------|
| Persistence | JSON fallback, dual-write, in-memory sessions | Fix env; redeploy with `deploy_paid_pilot.sh` |
| Auth | Missing/weak keys, anonymous perimeter | Set intake + support keys |
| Demo | DEMO_MODE on prod-like env | Remove DEMO_MODE |
| Product | platform_full in prod | Set `UNIFIED_INTAKE_PRODUCT_ONLY=1` |

---

## Case support (coarse auth)

| Endpoint | Key |
|----------|-----|
| Intake triage / customer flows | `UNIFIED_INTAKE_INTAKE_API_KEY` |
| Support export / manifest | `UNIFIED_INTAKE_SUPPORT_API_KEY` |

Optional: HMAC broker token (`minimal_signed_broker_token`) — pilot perimeter, not OAuth.

**`X-Org-Id`:** audit hint only — **not** tenancy / RBAC.

---

## Health for support calls

| Question | Check |
|----------|-------|
| Is service up? | `/health/live` |
| Can broker intake work? | `/readyz` → `intake_path_ready` |
| Why 503 on old monitor? | May be `/ready` (full-stack) — ignore for intake |
| Vector/RAG broken? | `/api/health/qdrant` — intake triage may still work |

```bash
bash scripts/summarize_readiness_posture.sh --probe <URL>
bash scripts/summarize_support_posture.sh <URL>   # human summary; set support key for manifest
bash scripts/check_unified_intake_prod_posture.sh   # whitelisted env echo
bash scripts/guardrail_cloudrun_runtime.sh          # live Cloud Run posture
```

---

## Scripts operators actually need

| Script | When |
|--------|------|
| `trial_launch_check.sh` | Before first broker session |
| `trial_readiness_check.sh` | Package coherence |
| `guardrail_inbox_triage.sh` | After code change |
| `unified_intake_release_gate.sh` | After deploy |
| `restore_8001_readiness.sh` | Local 503 / embedding_warming only |

---

## What support is NOT

- No SSO / RBAC console
- No cross-office tenant admin UI
- No guaranteed multi-instance analytics funnel truth
- No obligation to fix Qdrant for intake-only pilots

---

## Escalation doc path

1. This map
2. [`OPERATOR_CHEAT_SHEET.md`](./OPERATOR_CHEAT_SHEET.md)
3. [`docs/ANDY_IF_SOMETHING_GOES_WRONG.md`](../ANDY_IF_SOMETHING_GOES_WRONG.md)
4. [`docs/CURRENT_PRODUCT_SHAPE.md`](../CURRENT_PRODUCT_SHAPE.md)
