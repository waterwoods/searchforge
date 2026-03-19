# Deployment Manual Steps — Chen Kui Insurance Unified Entry

**Target:** Vercel (frontend) + Cloud Run (backend). Lightweight demo deployment.

---

## 1. Backend (Cloud Run)

### 1.1 Create `.env.cloudrun`

```bash
cp configs/demo.env.example .env.cloudrun
```

### 1.2 Fill required values in `.env.cloudrun`

| Variable | Required | Secret | Notes |
|----------|----------|--------|-------|
| `QDRANT_URL` | Yes | No | Qdrant Cloud or self-hosted URL |
| `QDRANT_API_KEY` | Yes (Cloud) | Yes | For Qdrant Cloud; empty for self-hosted |
| `QDRANT_COLLECTION` | Yes | No | Use `auto_insurance_demo_core` for Unified Intake |
| `OPENAI_API_KEY` | Yes (LLM) | Yes | For inbox triage LLM; omit for rule-only |
| `ALLOWED_ORIGINS` | Vercel | No | Comma-separated Vercel URL(s); unset = allow-all |

### 1.3 Deploy

```bash
bash scripts/deploy_rag_demo.sh
```

Note the Cloud Run URL printed at the end.

---

## 2. Frontend (Vercel)

### 2.1 Connect repo to Vercel

- Root directory: `ui/`
- Framework: Vite (auto-detected)

### 2.2 Set environment variable

In Vercel Project Settings → Environment Variables:

- `VITE_API_BASE_URL` = Cloud Run URL (no trailing slash)

### 2.3 Deploy

```bash
cd ui && vercel --prod
```

---

## 3. Post-deploy verification

- [ ] `curl <Cloud Run URL>/healthz` → 200
- [ ] `curl <Cloud Run URL>/readyz` — inspect (ok:false OK for triage-only; see KNOWN_DEPLOYMENT_GOTCHAS.md)
- [ ] Open `https://<vercel>.vercel.app/workbench/unified-intake`
- [ ] Paste "Notice: Policy will be cancelled in 7 days" → triage works
- [ ] No CORS errors in browser console

---

## 4. What still needs manual action

| Item | Where | Action |
|------|-------|--------|
| QDRANT_URL | .env.cloudrun | Fill with your Qdrant instance URL |
| QDRANT_API_KEY | .env.cloudrun | Fill if using Qdrant Cloud |
| OPENAI_API_KEY | .env.cloudrun | Fill for LLM triage (or omit for rule-only) |
| ALLOWED_ORIGINS | .env.cloudrun | Set Vercel URL(s) before deploy |
| VITE_API_BASE_URL | Vercel dashboard | Set Cloud Run URL after backend deploy |

---

## 5. Security note (Qdrant key rotation)

If Qdrant credentials were ever exposed in tracked files, rotate the API key. See `docs/QDRANT_KEY_ROTATION_NOTE.md`.

---

*See `docs/DEPLOYMENT_READINESS.md` for full checklist and cost notes.*
