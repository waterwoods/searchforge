# Deployment Readiness — Vercel + GCP Cloud Run

**Purpose:** Lightweight shareable demo. Frontend on Vercel, backend on Cloud Run.

**Current product shape:** [`docs/CURRENT_PRODUCT_SHAPE.md`](./CURRENT_PRODUCT_SHAPE.md) — what is required for paid pilot vs local demo.

**Release system:** Use `docs/runbooks/RELEASE_CHECKLIST.md` every release. Reference `docs/runbooks/DEPLOYMENT_PLAYBOOK.md` for full procedure.

---

## 1. Deployment Target

| Component | Host | Notes |
|-----------|------|-------|
| Frontend | Vercel | SPA (Vite), `ui/` directory |
| Backend | GCP Cloud Run | fiqa_api, port 8080 |
| Vector DB | Qdrant Cloud or local | Optional for **intake SaaS** paid pilot; required for RAG/notice retrieval flows |

---

## 2. What Is Ready

- **Frontend:** `npm run build` works; `VITE_API_BASE_URL` configurable for production
- **Backend:** `Dockerfile.cloudrun` exists; `deploy_paid_pilot.sh` (paid) / `deploy_demo_cloud_smoke.sh` (demo only)
- **CORS:** Backend supports `ALLOWED_ORIGINS` for Vercel (unset = allow-all for demo)
- **Health:** `/healthz`, `/readyz` endpoints
- **Vercel:** `vercel.json` has SPA rewrites for `/workbench/*`

---

## 3. Required Before Deploy

### Backend (.env.cloudrun)

| Variable | Required | Secret | Notes |
|----------|----------|--------|-------|
| `SERVICE_RECORD_DATABASE_URL` | **Yes (paid pilot)** | Yes | Postgres case/session truth |
| `UNIFIED_INTAKE_*` keys | **Yes (paid pilot)** | Partial | See `CURRENT_PRODUCT_SHAPE.md` — use `deploy_paid_pilot.sh` |
| `QDRANT_URL` | No (intake SaaS) / Yes (RAG) | No | Optional when `UNIFIED_INTAKE_INTAKE_CORE_READINESS=1` (set by `deploy_paid_pilot.sh`) |
| `QDRANT_API_KEY` | If Qdrant Cloud URL set | Yes | Omit when running intake-only without vectors |
| `QDRANT_COLLECTION` | If QDRANT_URL set | No | Use `auto_insurance_demo_core` for notice/knowledge wedge |
| `OPENAI_API_KEY` | Yes (LLM triage) | Yes | For inbox triage LLM; omit for rule-only local tests |
| `ALLOWED_ORIGINS` | Vercel | No | Comma-separated Vercel URL(s); unset = allow-all (demo only) |

### Frontend (Vercel env)

| Variable | Required | Notes |
|----------|----------|-------|
| `VITE_API_BASE_URL` | Yes | Cloud Run service URL (no trailing slash) |

---

## 4. Deploy Commands

```bash
# Backend
cp configs/demo.env.example .env.cloudrun
# Edit .env.cloudrun: Postgres URL, API keys, OPENAI_API_KEY, ALLOWED_ORIGINS
# QDRANT_* optional for intake-only SaaS (deploy_paid_pilot sets intake-core readiness)
bash scripts/deploy_paid_pilot.sh

# Frontend (Vercel)
# In Vercel dashboard: set VITE_API_BASE_URL = <Cloud Run URL>
vercel --prod
```

---

## 5. Post-Deploy Checks

- [ ] `curl <Cloud Run URL>/healthz` → 200
- [ ] `curl <Cloud Run URL>/readyz` — inspect (ok:false OK for triage-only; see runbooks/KNOWN_DEPLOYMENT_GOTCHAS.md)
- [ ] Open `https://<vercel>.vercel.app/workbench/unified-intake`
- [ ] Paste "Notice: Policy will be cancelled in 7 days" → triage works
- [ ] No CORS errors in browser console

---

## 6. Cost (Rough)

| Component | Light demo | Notes |
|-----------|------------|-------|
| Vercel | Free | Hobby tier sufficient |
| Cloud Run | ~$0–5/mo | Min instances 0, scales to zero |
| Qdrant Cloud | Free tier or low | Depends on cluster |
| OpenAI | Pay-per-use | Inbox triage, jobhunter |

---

## 7. First Deploy Smoke Checklist

1. **Backend deploy:** `bash scripts/deploy_paid_pilot.sh` → note Cloud Run URL
2. **Frontend deploy:** Connect repo to Vercel, set `VITE_API_BASE_URL` = Cloud Run URL, deploy
3. **First page load:** Open `https://<vercel>.vercel.app/workbench/unified-intake`
4. **Customer-entry test:** Paste "Notice: Policy will be cancelled in 7 days" → Start case → verify triage
5. **Broker workbench test:** Open a case from Recent cases → update status → add note
6. **Append follow-up test:** Reopen case → paste new message in "Paste new customer follow-up" → Update

---

## 8. Gaps / Risks

- **Case persistence:** In-memory/SQLite; not shared across Cloud Run instances. Acceptable for demo.
- **Qdrant collection:** Must be seeded with `auto_insurance_demo_core` for retrieval flows.
- **CORS:** If frontend URL changes, update `ALLOWED_ORIGINS` on Cloud Run.
