# Deployment Playbook — Chen Kui Insurance Unified Entry

**Purpose:** Repeatable release operations for backend (Cloud Run) and frontend (Vercel).  
**Use:** Reference doc. **Operational gate (5–15 min, demo/pilot-safe):** [RELEASE_CHECKLIST.md](./RELEASE_CHECKLIST.md) — pre-deploy alignment, post-deploy runtime, browser path, one workflow smoke. **Quick automated slice:** `bash scripts/unified_intake_release_gate.sh '<Cloud Run URL>' '<frontend origin>'`.

**Default habit (every meaningful change, same path):** local develop → `guardrail_inbox_triage.sh` (+ local API/UI checks) → deploy → `guardrail_cloudrun_runtime.sh` (optional but recommended) → `unified_intake_release_gate.sh` → manual browser verification on the **official** URL → only then customer/broker demo. The numbered sequence is spelled out at the top of [RELEASE_CHECKLIST.md](./RELEASE_CHECKLIST.md).

---

## 1. Scope of a Release

| Component | Host | Deploy Command |
|-----------|------|----------------|
| Backend | GCP Cloud Run | `bash scripts/deploy_rag_demo.sh` |
| Frontend | Vercel | `cd ui && vercel --prod` |
| Config | Baked into backend image | `configs/` copied in Dockerfile |

**Release = backend + frontend + env alignment.** Both must be live and aligned.

---

## 2. Pre-Deploy Checks

| Check | How |
|-------|-----|
| **Latest changed files** | `git status`, `git diff --stat` |
| **Local build** | `cd ui && npm run build` |
| **Local tests** | `bash scripts/guardrail_inbox_triage.sh`, `python3 scripts/test_inbox_triage_api.py --url http://localhost:8001` |
| **Which side changed** | Backend only / frontend only / both |
| **Env assumptions** | `.env.cloudrun` has QDRANT_*, OPENAI_API_KEY, ALLOWED_ORIGINS |
| **Vercel target** | Production alias (e.g. `ui-smoky-beta.vercel.app`) |
| **Cloud Run target** | `fiqa-api` in `us-west1` |

### Cloud Run runtime parity (anti-regression)

Live `fiqa-api` is tuned for Unified Intake stability: **memory 1Gi**, **concurrency 30**, **max 2** instances. **Min instances** defaults to **0** in `scripts/deploy_rag_demo.sh` (cost-safe); during pilot/demo you may set **min 1** so one instance stays warm (reduces first-request cold start). Overrides go in `.env.cloudrun` (`CLOUD_RUN_MEMORY`, `CLOUD_RUN_CONCURRENCY`, `CLOUD_RUN_MIN_INSTANCES`, etc.).

**Pilot warm instance (reversible):** apply without redeploying the image:

```bash
# Warm (pilot / demo): keep one instance
gcloud run services update fiqa-api --region us-west1 --project optimal-disk-472305-e2 --min-instances 1

# Rollback to cost-safe scale-to-zero
gcloud run services update fiqa-api --region us-west1 --project optimal-disk-472305-e2 --min-instances 0
```

Or set `CLOUD_RUN_MIN_INSTANCES=1` in `.env.cloudrun` before `bash scripts/deploy_rag_demo.sh` so the next full deploy keeps the same policy.

After any deploy or if something feels “reverted,” run (read-only; does not print DB URLs or API keys):

```bash
bash scripts/guardrail_cloudrun_runtime.sh
```

Strict DB-primary pilot flags (when Postgres is wired) should match: DB-primary reads/writes on, JSON case writes off, JSON read fallback off — the script prints whitelisted `UNIFIED_INTAKE_*` values only.

---

## 3. Backend Deploy Procedure

### Standard path

```bash
# 1. Load env
cp configs/demo.env.example .env.cloudrun   # if first time
# Edit .env.cloudrun: QDRANT_URL, QDRANT_API_KEY, OPENAI_API_KEY, ALLOWED_ORIGINS

# 2. Deploy
bash scripts/deploy_rag_demo.sh
```

### What success looks like

- Script exits 0
- Output shows Service URL
- `curl <URL>/health/live` → 200 (liveness; **do not rely on `/healthz` on Cloud Run** — Google’s edge often returns 404 HTML before the container)
- `curl <URL>/readyz` → JSON with `ok` field
- Optional alias: `curl <URL>/api/healthz` → 200 (same liveness semantics; reaches the container on Cloud Run)

### What `/readyz` means

| `ok` | Meaning |
|------|---------|
| `true` | Qdrant + embedding ready (full RAG path) |
| `false` | Qdrant or embedding not ready |

### What `/readyz` does NOT mean

- **In DEMO_MODE:** Qdrant and embedding are optional. Inbox triage (rule/LLM path) works even when `/readyz` is `not_ready`.
- **Triage path:** `POST /api/inbox/triage` does not require Qdrant. If `/readyz` fails but liveness (`/health/live`) passes, triage may still work.
- **Do not trust `/readyz` alone** to decide if the intake path is usable. Run one triage API check.

### When triage path works

- Liveness returns 200 (`/health/live` or `/api/healthz`; local dev may still use `/healthz`)
- `OPENAI_API_KEY` set (for LLM triage) or rule-only fallback
- `configs/` present in image (Dockerfile copies `configs/`)

### When not to trust it

- Liveness fails (`/health/live` and fallbacks) → service not running or not reachable
- CORS errors in browser → `ALLOWED_ORIGINS` mismatch
- Triage returns 500 → check logs, configs, OpenAI key

---

## 4. Frontend Deploy Procedure

### Standard path

```bash
cd ui
vercel --prod
```

### Verify production alias

- Vercel prints deployment URL (e.g. `https://ui-xxx.vercel.app`)
- **Production alias** (e.g. `ui-smoky-beta.vercel.app`) must point to this deploy
- In Vercel dashboard: Project → Settings → Domains — confirm production domain

### Confirm latest code is live

- Open production URL in browser
- Check for visible UI changes (e.g. new button, text)
- Hard refresh (Ctrl+Shift+R) to avoid cache
- If unsure: add a temporary visible marker, deploy, verify, remove

### Frontend env

| Variable | Required | Notes |
|----------|----------|-------|
| `VITE_API_BASE_URL` | Yes | Cloud Run URL (no trailing slash). Set in Vercel Project Settings → Environment Variables → Production |

---

## 5. Post-Deploy Verification

| Check | Command / Action |
|-------|------------------|
| Backend liveness | `curl <Cloud Run URL>/health/live` (or `/api/healthz`; see `KNOWN_DEPLOYMENT_GOTCHAS.md` § Cloud Run `/healthz`) |
| Backend ready | `curl <Cloud Run URL>/readyz` |
| Triage API | `python3 scripts/test_inbox_triage_api.py --url <Cloud Run URL>` |
| Frontend loads | Open `https://<Vercel URL>/workbench/unified-intake` |
| CORS | No CORS errors in browser console when UI calls API |
| Visible UI | Confirm expected UI changes |
| Top trial flow | Paste "Notice: Policy will be cancelled in 7 days" → Start case → verify triage |

---

## 6. Production Truth Checks

| Concept | Meaning |
|---------|---------|
| **Deployed** | Build succeeded, service/revision created |
| **Live** | Service responds, correct revision serving traffic |
| **Frontend live** | Production alias serves latest deploy; UI loads |
| **Backend live** | Cloud Run revision is active; API responds |
| **Aligned** | Frontend `VITE_API_BASE_URL` = backend URL; backend `ALLOWED_ORIGINS` includes frontend URL |

**"Build passed" ≠ "production truly live"** — always verify in browser and with one API call.

### Canonical workbench URL (founder)

- **Bookmark:** `https://ui-smoky-beta.vercel.app/workbench/unified-intake` (production alias).
- **Avoid** opening ad-hoc `https://ui-<hash>-….vercel.app` links unless that exact origin is listed in Cloud Run `ALLOWED_ORIGINS` — the browser sends the **page** origin on API calls; a hash URL not in the allowlist produces CORS failure, an empty queue (failed `GET /api/inbox/cases`), while an older tab that already loaded data can still show the previous in-memory list until refresh.

---

## 7. Known Deployment Gotchas

See [KNOWN_DEPLOYMENT_GOTCHAS.md](./KNOWN_DEPLOYMENT_GOTCHAS.md) for full list. Summary:

- `/readyz` false-negative for intake path (DEMO_MODE)
- `configs/` must be in Docker image (verify Dockerfile)
- Vercel production alias may be stale
- ALLOWED_ORIGINS must match real Vercel URL
- **Multi-origin CORS:** Browsers send the **page origin** (e.g. a per-deploy `https://ui-<hash>-….vercel.app` link from the Vercel dashboard), not only the production alias. Put the alias **and** any deployment/preview origins you actually open in one comma-separated `ALLOWED_ORIGINS` value. After a frontend deploy, confirm the latest production deployment URL with `cd ui && vercel ls` and add it if the team uses that link.
- **Deploy drift:** `bash scripts/deploy_rag_demo.sh` sends `--set-env-vars` as a fixed bundle from `.env.cloudrun`. If `ALLOWED_ORIGINS` is set there, it **replaces** the live value on the next full deploy—keep the list complete, or re-apply a patch with `gcloud run services update fiqa-api --region us-west1 --project optimal-disk-472305-e2 --update-env-vars '^@^ALLOWED_ORIGINS=…'`. If `ALLOWED_ORIGINS` is omitted from that bundle, Cloud Run drops the variable and the app falls back to permissive demo CORS (`app_main.py`).
- Local success ≠ production success
- Browser/manual verification required for user-visible changes

---

## 8. Manual Smoke Checks

Before claiming success:

1. Open production frontend URL
2. Customer Entry: paste cancellation notice → verify triage
3. Broker Workbench: load case → verify status/notes
4. Simulation Assistant: run one scenario
5. No CORS errors in console

---

## 9. Roll-Forward / Retry Guidance

| Situation | Action |
|-----------|--------|
| Backend deploy failed | Check gcloud auth, project, logs; fix `.env.cloudrun`; retry |
| Frontend build failed | Fix build errors; `vercel --prod` again |
| CORS errors | Add/update `ALLOWED_ORIGINS` in `.env.cloudrun`; redeploy backend |
| `/readyz` not ready, triage needed | If liveness OK, run triage API test; triage may work |
| Production alias wrong | Vercel dashboard → Domains → assign production |

---

## 10. When to Stop and Not Claim Success

- Do **not** claim success if:
  - CORS errors in browser
  - Triage API returns 500
  - Frontend shows old UI (alias not updated)
  - `ALLOWED_ORIGINS` does not include frontend URL
  - No manual browser verification for user-visible changes

---

## Quick Reference

| Task | Command |
|------|---------|
| Backend deploy | `bash scripts/deploy_rag_demo.sh` |
| Frontend deploy | `cd ui && vercel --prod` |
| Triage API test | `python3 scripts/test_inbox_triage_api.py --url <URL>` |
| Local guardrail | `bash scripts/guardrail_inbox_triage.sh` |

---

## How to Use This System

| Artifact | When to use |
|----------|-------------|
| **Playbook** | Reference when unsure; first-time deploy; troubleshooting |
| **Checklist** | **Every release** — must-check before saying success |
| **Cursor prompt template** | Every meaningful deploy; paste into Cursor for standardized release flow |
| **Human browser verification** | Every user-visible change; every trust-related change |

**Fastest release rhythm (small team):** Checklist every release; playbook as reference; Cursor template when using Cursor for deploy; always do manual browser check for UI/trust changes.
