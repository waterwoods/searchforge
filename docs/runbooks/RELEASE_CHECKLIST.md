# Release Checklist — Chen Kui Insurance Unified Entry

**Use every demo, pilot touch, or production release** — must-check before saying “please try it” or “we’re live.”

**Before Founder QA (required deploy/config safety):** `bash scripts/run_deployment_qa_gate.sh` — see [DEPLOYMENT_QA_GATE.md](./DEPLOYMENT_QA_GATE.md) (latest revision @ 100%, CORS, Office Queue, Smart Claim Start).  
**Fast automated slice (API + CORS preflight):** `bash scripts/unified_intake_release_gate.sh '<Cloud Run URL>' '<exact frontend origin you will open>'`  
**Cloud Run sizing + intake flags (read-only):** `bash scripts/guardrail_cloudrun_runtime.sh`

Reference: [DEPLOYMENT_PLAYBOOK.md](./DEPLOYMENT_PLAYBOOK.md), [KNOWN_DEPLOYMENT_GOTCHAS.md](./KNOWN_DEPLOYMENT_GOTCHAS.md), DB-primary log signals: [UNIFIED_INTAKE_DB_OBSERVABILITY_SIGNALS.md](./UNIFIED_INTAKE_DB_OBSERVABILITY_SIGNALS.md).

---

## Default release discipline (full path — same for every feature)

Use this order so nothing important lives only in memory:

1. **Local develop** — implement on the usual path (e.g. `bash scripts/run_demo_local.sh` on **8001**; see `docs/ANDY_QUICK_START.md`).
2. **Local guardrail + local smoke** — before you trust the change: `bash scripts/guardrail_inbox_triage.sh`; when the API is up, `python3 scripts/test_inbox_triage_api.py --url http://localhost:8001`; if UI changed, `cd ui && npm run build`.
   - **New client pack only (short path):** after adding or swapping `configs/clients/<client_id>/`, run `bash scripts/second_client_pack_short_regression.sh '<client_id>'` (defaults to `socal_precision` when omitted). This is a **bounded** check (pack JSON, per-client cross-client scenarios, Add-Car contract slice, formal-submit intent notes, local persistence); it does **not** replace the full guardrail before a release.
3. **Cloud deploy** — backend: `bash scripts/deploy_rag_demo.sh`; frontend: `cd ui && vercel --prod` (order: usually backend first if both changed).
4. **Runtime guardrail (cloud)** — read-only drift check: `bash scripts/guardrail_cloudrun_runtime.sh` (when you have `gcloud` access).
5. **Deployment QA Gate (required before Founder QA)** — `bash scripts/run_deployment_qa_gate.sh` (or set `FRONTEND_ORIGIN` to the exact origin). Must print **READY FOR FOUNDER QA**. Catches old revision / wrong traffic / CORS / empty Office Queue / missing Start Claim surface. SSOT: [DEPLOYMENT_QA_GATE.md](./DEPLOYMENT_QA_GATE.md).
6. **Release gate (automated slice)** — `bash scripts/unified_intake_release_gate.sh '<Cloud Run URL>' '<exact production or preview origin you will open>'` (same origin you will use in the browser).
7. **Browser / manual verification** — open the **canonical** workbench URL; hard refresh; no CORS errors; one real paste → triage and workbench list sanity (sections C–D below).
8. **Only then** — share the link with brokers or customers (“green bar” in this doc).

Skipping steps 2, 5, 6, or 7 is the most common way to ship a “successful” deploy that still fails in the real browser.

---

## Unified Intake release acceptance gate (5–15 min)

Structure: **pre-deploy → post-deploy runtime → browser path → one workflow smoke.**  
**Pass criteria:** all relevant boxes checked for *your* change (backend-only can skip frontend build; still run API gate).

### A. Pre-deploy (alignment — catches most “low-level” failures)

- [ ] **What changed:** backend only / frontend only / both — plan deploy order (both touched → usually backend then frontend).
- [ ] **Diff / hygiene:** `git status` / `git diff --stat` reviewed for the release; no secrets or `.env*` pasted into tracked files; `.env.cloudrun` stays **gitignored** (never commit it).
- [ ] **`.env.cloudrun`:** not stale; `ALLOWED_ORIGINS` is a **comma-separated** list that includes **every origin you will actually open** (production **alias** and any **per-deploy** `https://ui-*….vercel.app` link the team uses). Omitting `ALLOWED_ORIGINS` from the deploy bundle can **drop** the variable and widen CORS — see gotchas.
- [ ] **Vercel production:** `VITE_API_BASE_URL` (Production) = **exact** Cloud Run HTTPS URL (no trailing slash). **Canonical check:** `gcloud run services describe fiqa-api --region us-west1 --format='value(status.url)'` — use that string or a verified equivalent `*.run.app` hostname (Vercel’s bundle may use the `PROJECT_NUMBER.REGION.run.app` form; both must reach the same revision).
- [ ] **Local quality bar (when code changed):** `cd ui && npm run build`; `bash scripts/guardrail_inbox_triage.sh`.

**If fail:** fix env / allowlist / Vercel vars **before** deploy — redeploying with wrong `ALLOWED_ORIGINS` **replaces** the previous list.

### B. Post-deploy runtime (automated + quick curls)

- [ ] **Deploy succeeds:** backend script exit 0 / Vercel deploy shows production.
- [ ] **Liveness:** `curl -sf --max-time 15 '<Cloud Run URL>/health/live'` → **pass** (HTTP 200).  
  **Do not** use top-level `/healthz` on Cloud Run as the primary check — Google edge often returns HTML 404 before the container.
- [ ] **Readiness (informational):** `curl -sf '<Cloud Run URL>/readyz'` — if `ok` is false, triage may still work (Qdrant path); do **not** block pilot on this alone if liveness + triage test pass (see playbook).
- [ ] **Triage API:** `python3 scripts/test_inbox_triage_api.py --url '<Cloud Run URL>'` → **PASS**.
- [ ] **Required before Founder QA:** `bash scripts/run_deployment_qa_gate.sh` → **READY FOR FOUNDER QA** ([DEPLOYMENT_QA_GATE.md](./DEPLOYMENT_QA_GATE.md)).
- [ ] **Optional but high value:** `bash scripts/unified_intake_release_gate.sh '<Cloud Run URL>' '<https://your-exact-frontend-origin>'` — combines liveness + triage + **CORS preflight** for `GET /api/inbox/cases`.
- [ ] **When you have gcloud:** `bash scripts/guardrail_cloudrun_runtime.sh` — memory/concurrency parity + shows `ALLOWED_ORIGINS` and whitelisted `UNIFIED_INTAKE_*` flags (no secrets).

**If fail:** logs `gcloud run services logs read fiqa-api --region us-west1`; fix keys/config/CORS; cold-start: wait + retry liveness or set min instances for demo (playbook §2).

### C. Browser-path (manual — catches alias, cache, and “empty workbench” illusions)

- [ ] Open the **canonical** workbench URL your pilot will use (bookmark the **production alias**, not a random preview URL, unless that preview origin is in `ALLOWED_ORIGINS`).
- [ ] **Hard refresh** (Ctrl+Shift+R) — avoid stale bundle false positives.
- [ ] DevTools → **Console / Network:** no CORS errors on `/api/inbox/cases` or `/api/inbox/triage`.
- [ ] **Symptom check:** “empty queue” with no errors vs “Network Error” — if CORS: preflight for your **page origin** was rejected; expand `ALLOWED_ORIGINS` and redeploy/patch backend.

**Manual CORS preflight (optional):** see [KNOWN_DEPLOYMENT_GOTCHAS.md](./KNOWN_DEPLOYMENT_GOTCHAS.md) §6a — `OPTIONS` to `/api/inbox/cases?limit=1` with real `Origin` header must return **200**.

**If fail:** align origin ↔ `ALLOWED_ORIGINS` ↔ `VITE_API_BASE_URL`; see gotchas §6–7.

### D. One real workflow smoke (manual)

- [ ] **Customer path:** paste a canonical trial line (e.g. cancellation notice) → Start case → triage response looks sane.
- [ ] **Workbench:** list shows expected cases (not stuck loading); open one row if present.
- [ ] **If UI changed:** visibly confirm the expected control/copy on production.
- [ ] **DB-primary pilot (if enabled):** if workbench rows show `pg_mirror_state` warnings or odd behavior, check Cloud Run logs for `UNIFIED_INTAKE_DB_OBS` (see observability doc).

**If fail:** separate “browser/CORS” vs “API 500” vs “persistence/flags” using Network tab + server logs; do not declare success from API-only scripts if the workbench path fails.

---

## Green bar (“safe to invite broker / customer”)

- **Backend:** `/health/live` OK; `test_inbox_triage_api.py` PASS.
- **Alignment:** frontend origin(s) in `ALLOWED_ORIGINS`; `VITE_API_BASE_URL` matches Cloud Run.
- **Browser:** workbench loads on the **same** origin you verified; no CORS errors; one paste/triage cycle OK.

Until all three are true, **do not** say “please try the link.”

---

## Backend deploy (reminder)

- [ ] `bash scripts/deploy_rag_demo.sh` — exits 0; note printed **Service URL**

## Frontend deploy (reminder)

- [ ] `cd ui && vercel --prod` — succeeds
- [ ] Production domain / alias in dashboard points at this deployment

---

**Do not claim success until the Unified Intake release acceptance gate is satisfied for your scenario.**
