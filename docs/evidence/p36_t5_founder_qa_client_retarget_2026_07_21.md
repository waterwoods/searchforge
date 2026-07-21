# P36 T5 — Founder QA Client Retarget Evidence

**Date:** 2026-07-21  
**Task:** Route Founder QA clients (Vercel Preview + Mini Program QA) to isolated Cloud QA  
**Frozen QA API:** `https://fiqa-api-qa-g7zatxrycq-uw.a.run.app`  
**Production API (unchanged):** `https://fiqa-api-g7zatxrycq-uw.a.run.app`  
**Stop after T5:** yes (no Founder PAT; no Mini Program upload/publish)

Secret values are **not** included. No Production Vercel env mutation was performed by this task.

---

## 1. Discovery summary (pre-edit)

| Area | Location / behavior before T5 |
|------|-------------------------------|
| Founder Console | `ui/` route `/internal/founder-qa`; HTTP via shared `VITE_API_BASE_URL` → `ui/src/api/config.ts` |
| Vercel | Single `VITE_API_BASE_URL`; `vite.config.ts` only required HTTPS non-localhost on Vercel — **Preview could silently share Production URL** |
| Mini Program QA | `miniapp/config.qa.ts` + `QA_API_BASE_URL` pointed at **Production** `fiqa-api-g7zatxrycq-uw.a.run.app` |
| Profiles | Mini Program `local` \| `qa`; Build Gate locked QA host to Production URL (historical mis-name) |
| Auth | UI intake key via `VITE_UNIFIED_INTAKE_INTAKE_API_KEY`; Mini Program request headers unchanged |

---

## 2. Files changed

| Path | Change |
|------|--------|
| `ui/src/api/cloudBackendUrls.ts` | Frozen Cloud QA / Production URLs + fail-closed Vercel Preview/Production guard |
| `ui/src/api/cloudBackendUrls.test.ts` | Focused routing / cross-wiring tests |
| `ui/src/api/config.ts` | Re-export frozen URLs; document Preview vs Production |
| `ui/vite.config.ts` | Use new guard (Preview≠Production, missing Preview URL fails) |
| `ui/env.preview.example` | Operator template for Vercel **Preview** env only |
| `miniapp/config.qa.ts` | QA `apiBaseUrl` → Cloud QA |
| `miniapp/utils/config.ts` | `QA_API_BASE_URL` → Cloud QA; `PRODUCTION_API_BASE_URL` frozen; refuse Production leftovers on `apiProfile=qa` |
| `miniapp/utils/miniProgramBuildGate.ts` | Required QA host + forbid Production host |
| `miniapp/tests/configProfile.test.ts` | Cloud QA resolution + no Production fallback |
| `miniapp/tests/buildGate.test.ts` | Constants + Production rejection test |
| `miniapp/tests/requestErrors.test.ts` | Sample host → Cloud QA |
| `docs/runbooks/CLOUD_QA_RESOURCE_NAMES.md` | T5 client routing + operator steps |
| `docs/runbooks/DEPLOYMENT_PLAYBOOK.md` | Preview vs Production `VITE_API_BASE_URL` |
| `docs/product/p35_founder_qa_console_quickstart.md` | Shared QA URL |
| `docs/product/p20_slice1_manual_qa_script.md` | Legal domain host for Cloud QA |
| `docs/product/p20_production_loop_template.md` | Legal domain checklist |
| `docs/evidence/p36_t5_founder_qa_client_retarget_2026_07_21.md` | This evidence |

**Not changed / not committed:** `.env.cloudrun`, `.env.cloudrun.qa`, Vercel Production env, Secret Manager, Cloud Run services, databases.

---

## 3. Old → new QA routing

| Client | Old QA routing | New QA routing |
|--------|----------------|----------------|
| Mini Program `apiProfile=qa` | `https://fiqa-api-g7zatxrycq-uw.a.run.app` (Production) | `https://fiqa-api-qa-g7zatxrycq-uw.a.run.app` |
| Vercel Preview (intended) | Often same Production URL (no Preview-specific fail-closed) | Must be Cloud QA URL; build fails otherwise |
| Vercel Production | `https://fiqa-api-g7zatxrycq-uw.a.run.app` | **Unchanged** (guard refuses Cloud QA URL) |

---

## 4. Environment variable names

| Variable | Scope | Expected value |
|----------|-------|----------------|
| `VITE_API_BASE_URL` | Vercel **Preview** | `https://fiqa-api-qa-g7zatxrycq-uw.a.run.app` |
| `VITE_API_BASE_URL` | Vercel **Production** | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| `VITE_UNIFIED_INTAKE_INTAKE_API_KEY` | Vercel Preview | QA intake key (from `.env.cloudrun.qa`; never commit) |
| `VITE_ENABLE_QA_TOOLS` | Vercel Preview | `1` (Founder Console surface) |
| Mini Program `apiProfile` | DevTools / Experience | `qa` for Founder QA builds |

---

## 5. Test results

```bash
cd miniapp && npx tsx --test tests/configProfile.test.ts
# pass 7 / fail 0

cd miniapp && npx tsx --test --test-name-pattern='Production backend|permanent Preview|Cloud QA' \
  tests/buildGate.test.ts tests/configProfile.test.ts
# pass focused T5 assertions

cd ui && npx tsx --tsconfig tsconfig.json src/api/cloudBackendUrls.test.ts
# cloudBackendUrls.test.ts: PASS
```

**Note:** Full `miniapp` suite still reports pre-existing local failures unrelated to T5 URL retarget:

- Build Gate disk PASS blocked by local compile condition `service-home` (private DevTools config)
- Golden UI tests require `P26H_UI_FIXTURE_JSON` env (not set in this run)

---

## 6. QA URL verification

| Check | Result |
|-------|--------|
| `config.qa.ts` / `QA_API_BASE_URL` | Cloud QA URL |
| Build Gate required host | `fiqa-api-qa-g7zatxrycq-uw.a.run.app` |
| `GET https://fiqa-api-qa-g7zatxrycq-uw.a.run.app/health/live` | HTTP 200 |
| `GET …/readyz` | HTTP 200, `intake_path_ready=true` |
| Production constant | Still `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| Production `/health/live` | HTTP 200 (read-only) |

---

## 7. Production non-mutation statement

- No `vercel env` / `vercel --prod` commands were run.
- No `gcloud` mutations on `fiqa-api`, secrets, or databases.
- Production Cloud Run remains `fiqa-api-00233-scz` / generation `233`.
- Cloud QA remains `fiqa-api-qa-00002-rx9` (unchanged this task).

---

## 8. Manual operator steps still required

### Vercel Preview (required for Founder Console on Preview)

```bash
cd ui
vercel env add VITE_API_BASE_URL preview
# paste: https://fiqa-api-qa-g7zatxrycq-uw.a.run.app

vercel env add VITE_UNIFIED_INTAKE_INTAKE_API_KEY preview
# paste QA key from .env.cloudrun.qa (not Production)

vercel env add VITE_ENABLE_QA_TOOLS preview
# paste: 1

vercel --yes   # Preview redeploy only — do NOT use --prod
```

**Do not** change Vercel Production `VITE_API_BASE_URL`.

### WeChat Mini Program

1. Confirm DevTools / Experience `apiProfile=qa` (gitignored `config.local.ts`).
2. Add request合法域名: `fiqa-api-qa-g7zatxrycq-uw.a.run.app`.
3. Clean-cache compile in DevTools before any future Experience upload.
4. **Do not** upload/publish a Mini Program release as part of T5.

### CORS (if Preview browser calls fail)

Ensure `ALLOWED_ORIGINS` on **fiqa-api-qa** includes the Preview origin(s). Do not patch Production `fiqa-api` for this.

---

## 9. Three WeChat Component Gates

**Not triggered.** T5 changed config/constants/tests/docs only — no Mini Program component (`index.ts` / `.json` / `.wxml` / `.wxss`) was added or modified.
