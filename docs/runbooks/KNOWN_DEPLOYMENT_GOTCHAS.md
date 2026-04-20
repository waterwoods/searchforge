# Known Deployment Gotchas

**Purpose:** Document repeated pitfalls so future releases avoid them.

---

## 1. Cloud Run: Top-Level `/healthz` Returns Google 404 (Not Your App)

| Symptom | `curl https://<service>.run.app/healthz` returns **HTML** “Error 404 (Not Found)!!1” from Google; `/readyz` and `/health/live` return JSON **200** from FastAPI |
|---------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Root cause** | The request **does not reach the container**. Google’s HTTP frontend in front of Cloud Run handles `/healthz` and responds with its own 404 page. This is **not** missing FastAPI routes (the app defines `/healthz` and it works locally). |
| **How to check** | Compare response bodies: Google 404 is HTML; app 404 is usually `{"detail":"Not Found"}`. |
| **Canonical contract** | **Liveness:** `GET /health/live` (or `GET /api/healthz` alias). **Readiness / deps:** `GET /readyz`. |
| **Avoid next time** | Use `scripts/deploy_rag_demo.sh` (checks `/health/live` first). Do not treat `/healthz` on Cloud Run as ground truth. |

**References:** Internal sprint `docs/sprints/HEALTH_ENDPOINT_ROOT_CAUSE_PERMANENT_FIX/`; Stack Overflow and Cloud Run discussions on reserved / colliding paths.

---

## 2. `/readyz` False-Negative for Intake Path

| Symptom | `/readyz` returns `ok: false` (Qdrant/embedding not ready) |
|---------|-----------------------------------------------------------|
| **Likely cause** | Qdrant Cloud down, embedding model not loaded, Redis timeout |
| **How to check** | `curl <URL>/readyz` — inspect `clients` object |
| **How to fix** | For intake-only: none. Triage works without Qdrant in DEMO_MODE. For full RAG: fix Qdrant/embedding. |
| **Avoid next time** | Do not block release on `/readyz` when only triage is needed. Run `test_inbox_triage_api.py` instead. |

**Key:** Inbox triage uses rule/LLM path. It does not require Qdrant. `DEMO_MODE=true` makes Qdrant optional for readiness. When DEMO_MODE=true, `/readyz` returns `ok: true` and `intake_path_ready: true`; GPU is also non-blocking.

---

## 3. Qdrant Lazy-Init Confusion

| Symptom | `/readyz` flaky; sometimes ready, sometimes not |
|---------|-----------------------------------------------|
| **Likely cause** | Qdrant connection checked at startup; cold start or network delay |
| **How to check** | Retry `/readyz` after 30–60s; check Cloud Run logs |
| **How to fix** | Wait for cold start; or use DEMO_MODE if triage-only |
| **Avoid next time** | Deploy script already waits; if triage is the goal, verify triage API, not readyz. |

---

## 4. Configs Missing from Docker Image

| Symptom | Triage returns 500; logs show "config file not found" or empty markers |
|---------|----------------------------------------------------------------------|
| **Likely cause** | `configs/` not copied in Dockerfile; `.dockerignore` excluding configs |
| **How to check** | `docker build -f services/fiqa_api/Dockerfile.cloudrun .` then `docker run ... ls /app/configs` |
| **How to fix** | Ensure `COPY configs/ /app/configs/` in Dockerfile; config_loader uses `configs/` relative to repo root |
| **Avoid next time** | Dockerfile.cloudrun already has `COPY configs/`. If adding new COPY steps, verify configs path. |

---

## 5. Frontend Build Succeeds but Production Alias Stale

| Symptom | `vercel --prod` succeeds but production URL shows old UI |
|---------|---------------------------------------------------------|
| **Likely cause** | Production domain points to old deployment; Vercel preview vs production |
| **How to check** | Open production URL; hard refresh; check Vercel dashboard → Deployments → which deploy is "Production" |
| **How to fix** | Vercel dashboard → Domains → ensure production domain points to latest; or promote deployment |
| **Avoid next time** | After `vercel --prod`, open the printed URL and confirm visible changes. |

---

## 6. CORS Mismatch After Vercel URL Change

| Symptom | Browser console: "CORS policy" or "blocked by CORS" |
|---------|----------------------------------------------------|
| **Likely cause** | `ALLOWED_ORIGINS` does not include the real Vercel URL |
| **How to check** | Open frontend; F12 → Network; failed request shows CORS error |
| **How to fix** | Add `ALLOWED_ORIGINS=https://<real-vercel-url>.vercel.app` to `.env.cloudrun`; redeploy backend |
| **Avoid next time** | After first Vercel deploy, copy exact URL (no trailing slash) into ALLOWED_ORIGINS. |

### 6a. “Old tab has data, new tab shows zero” (workbench)

| Symptom | One browser tab shows cases; a **new** tab on a **different** URL shows an empty queue |
|---------|----------------------------------------------------------------------------------------|
| **Likely cause** | New tab’s **Origin** is not in `ALLOWED_ORIGINS` → `GET /api/inbox/cases` fails CORS → list stays at initial empty state; old tab still holds earlier successful fetch in React state. |
| **Quick server-side check** | `curl -sS -D - -o /dev/null -X OPTIONS "https://<api>/api/inbox/cases?limit=1" -H "Origin: https://<page-origin>" -H "Access-Control-Request-Method: GET"` — disallowed origins often return **400** on preflight; allowed return **200** with `access-control-allow-origin` matching the Origin. |
| **Fix** | Use the production alias URL (see Deployment Playbook), or add the deployment hostname to `ALLOWED_ORIGINS` in `.env.cloudrun` and redeploy backend so the allowlist is not narrower than live. |

---

## 7. Backend/Frontend Version Mismatch

| Symptom | Frontend expects new API fields; backend returns old shape |
|---------|-----------------------------------------------------------|
| **Likely cause** | Deployed backend but not frontend, or vice versa |
| **How to check** | Compare API response shape with frontend types; check deploy order |
| **How to fix** | Deploy both; ensure frontend `VITE_API_BASE_URL` points to correct backend |
| **Avoid next time** | When both change, deploy backend first, then frontend. Use checklist. |

---

## 8. Env/Secrets Drift

| Symptom | Works locally, fails in production |
|---------|------------------------------------|
| **Likely cause** | `.env.cloudrun` not updated; Vercel env not set for production |
| **How to check** | `gcloud run services describe fiqa-api --format='yaml(spec.template.spec.containers[0].env)'`; Vercel → Settings → Environment Variables |
| **How to fix** | Update `.env.cloudrun` and redeploy; or `gcloud run services update ... --update-env-vars` |
| **Avoid next time** | Keep `configs/demo.env.example` as template; document required vars. |

---

## 9. "Deployed" vs "Fully Live and Aligned"

| Symptom | Deploy script says success but users see errors |
|---------|-----------------------------------------------|
| **Likely cause** | Did not run post-deploy verification; assumed success from script exit |
| **How to check** | Run checklist: `/health/live` (or `/api/healthz`), `/readyz`, triage API, browser, CORS |
| **How to fix** | Run full post-deploy verification; fix misalignments |
| **Avoid next time** | Use RELEASE_CHECKLIST.md every release. Never skip manual browser check for UI changes. |

---

## 10. Browser/Manual Verification Still Needed

| Symptom | All scripts pass but founder sees broken UI |
|---------|--------------------------------------------|
| **Likely cause** | Scripts test API only; UI bugs, routing, or cache not covered |
| **How to check** | Human opens production URL; runs top trial flows |
| **How to fix** | Fix UI/routing; redeploy; verify again |
| **Avoid next time** | Require human browser verification for every user-visible change. |
