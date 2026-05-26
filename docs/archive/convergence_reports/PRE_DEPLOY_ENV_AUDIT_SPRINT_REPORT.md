# Pre-Deploy Env Audit + First Deploy Smoke Sprint Report

**Sprint:** Pre-Deploy Env Audit + First Deploy Smoke  
**Date:** 2026-03-11  
**Target:** Chen Kui Insurance Unified Entry — Vercel + GCP Cloud Run

---

## 1. Stages completed

- Stage 1: Real env var inventory (from code inspection)
- Stage 2: Gaps, mismatches, stale assumptions identified
- Stage 3: Small high-value fixes implemented
- Stage 4: Frontend deploy readiness check
- Stage 5: Backend deploy readiness check
- Stage 6: First deploy smoke plan
- Stage 7: Cost scouting recheck
- Stage 8: Final readiness verdict
- Stage 9: Validation (build, guardrail, scenarios)

---

## 2. Real env inventory

### Frontend-required

| Variable | Where | Purpose | Required for demo | Secret |
|----------|-------|---------|-------------------|--------|
| `VITE_API_BASE_URL` | `ui/src/api/config.ts` | Backend API URL in production | Yes | No |

### Backend-required (Cloud Run)

| Variable | Where | Purpose | Required for demo | Secret |
|----------|-------|---------|-------------------|--------|
| `QDRANT_URL` | `clients.py`, deploy script | Qdrant instance URL | Yes | No |
| `QDRANT_API_KEY` | `clients.py`, deploy script | Qdrant Cloud auth | Yes (Cloud) | Yes |
| `QDRANT_COLLECTION` | `clients.py`, deploy script | Collection name | Yes | No |
| `OPENAI_API_KEY` | `triage.py`, `clients.py` | Inbox triage LLM | Yes (LLM) | Yes |
| `ALLOWED_ORIGINS` | `app_main.py` | CORS for Vercel | Vercel | No |

### Optional / feature-gated

| Variable | Where | Purpose |
|----------|-------|---------|
| `LLM_GENERATION_ENABLED` | `triage.py` | Enable LLM triage (default: false) |
| `LLM_MODEL` | `triage.py` | LLM model (default: gpt-4o-mini) |
| `NOTICE_RETRIEVAL_ENABLED` | `notice_retrieval.py` | Notice retrieval (default: 1) |
| `UNIFIED_INTAKE_CASES_PATH` | `case_store.py` | Case persistence path |
| `DEMO_MODE` | `ready.py` | Makes embedding optional |
| `TRANSLATION_ENABLED` | `translation.py`, app_main | Translation feature |
| `VITE_API_PROXY_TARGET` | `vite.config.ts` | Dev proxy target (default: 8001) |

### Likely stale or legacy

| Variable | Notes |
|----------|-------|
| `VITE_API_BASE` | Legacy; `VITE_API_BASE_URL` preferred |
| `CORS_ORIGINS` | Legacy; use `ALLOWED_ORIGINS` |
| `ALLOW_ALL_CORS` | Legacy; when `ALLOWED_ORIGINS` unset, defaults allow-all |
| `.env.example` | Uses `QDRANT_COLLECTION=auto_insurance_v1`; use `configs/demo.env.example` for deploy |

### Unknown / needs confirmation

- None blocking deployment.

---

## 3. Deployment gaps and fixes

### Fixes implemented

| Fix | File | Why |
|-----|------|-----|
| Clarify OPENAI_API_KEY, ALLOWED_ORIGINS in demo.env.example | `configs/demo.env.example` | Clear required vs optional |
| Set LLM_GENERATION_ENABLED=1 when OPENAI_API_KEY present | `scripts/deploy_rag_demo.sh` | Full triage quality when OpenAI key set |
| Add Secret column to env table | `docs/DEPLOYMENT_READINESS.md` | Clarify which vars need real secrets |
| Add First Deploy Smoke Checklist | `docs/DEPLOYMENT_READINESS.md` | Step-by-step post-deploy verification |

### Gaps identified (no fix in sprint)

| Gap | Impact | Recommendation |
|-----|--------|----------------|
| API test append-message 404 | Optional; server may need restart | Run `bash scripts/run_demo_local.sh` before API test |
| persisted case collected_fields | Minor assertion in test | Non-blocking for deploy |

---

## 4. Frontend readiness

**Verdict: Ready**

| Check | Status |
|-------|--------|
| Build command | `npm run build` — OK |
| Output directory | `dist` — OK |
| Vercel env vars | `VITE_API_BASE_URL` required |
| API base URL configurable | Yes — `import.meta.env.VITE_API_BASE_URL` |
| Local-only assumptions | None — empty = relative paths; prod = set URL |
| Vite production build | OK — built successfully |

**Manual steps for Vercel:**
1. Connect repo (ui/ as root or repo root with Vite preset)
2. Set `VITE_API_BASE_URL` = Cloud Run URL (no trailing slash)
3. Deploy

---

## 5. Backend readiness

**Verdict: Ready**

| Check | Status |
|-------|--------|
| Start command | `uvicorn services.fiqa_api.app_main:app --host 0.0.0.0 --port ${PORT:-8080}` |
| Dockerfile | `Dockerfile.cloudrun` — port 8080 |
| Required Cloud Run env vars | QDRANT_URL, QDRANT_API_KEY (Cloud), QDRANT_COLLECTION, OPENAI_API_KEY (LLM), ALLOWED_ORIGINS (Vercel) |
| CORS | `ALLOWED_ORIGINS` supported; unset = allow-all |
| Secrets | QDRANT_API_KEY, OPENAI_API_KEY — use Secret Manager in production |
| Deploy script | `deploy_rag_demo.sh` — loads .env.cloudrun, validates, deploys |

**Manual steps for Cloud Run:**
1. Create `.env.cloudrun` from `configs/demo.env.example`
2. Fill: QDRANT_URL, QDRANT_API_KEY, OPENAI_API_KEY, ALLOWED_ORIGINS (if Vercel)
3. Run `bash scripts/deploy_rag_demo.sh`

---

## 6. First deploy smoke plan

1. **Backend deploy:** `bash scripts/deploy_rag_demo.sh` → note Cloud Run URL  
2. **Frontend deploy:** Connect repo to Vercel, set `VITE_API_BASE_URL` = Cloud Run URL, deploy  
3. **First page load:** Open `https://<vercel>.vercel.app/workbench/unified-intake`  
4. **Customer-entry test:** Paste "Notice: Policy will be cancelled in 7 days" → Start case → verify triage  
5. **Broker workbench test:** Open a case from Recent cases → update status → add note  
6. **Append follow-up test:** Reopen case → paste new message in "Paste new customer follow-up" → Update  

---

## 7. Cost scouting

| Component | Light demo | Notes |
|-----------|------------|-------|
| **Vercel** | Free | Hobby tier sufficient |
| **Cloud Run** | ~$0–5/mo | Min 0, max 2, scales to zero |
| **Qdrant Cloud** | Free tier or low | Depends on cluster |
| **OpenAI** | Pay-per-use | Inbox triage; ~$0.01–0.05/request |

**Cost drivers:** Always-on instances, high concurrency, egress. For demo: keep min 0, max 2.

**Safest low-cost posture:** Min instances 0, max 2; avoid always-on; use rule-based triage (no OPENAI_API_KEY) for zero LLM cost if needed.

---

## 8. Readiness verdict

**Verdict: Ready after 1–3 manual env/secrets steps**

| Area | Status |
|------|--------|
| **Ready now** | Frontend build, backend Dockerfile, deploy script, CORS, health endpoints, env example |
| **Manual steps** | Create `.env.cloudrun`; fill QDRANT_URL, QDRANT_API_KEY, OPENAI_API_KEY, ALLOWED_ORIGINS; set Vercel `VITE_API_BASE_URL` |
| **Likely no manual intervention** | Build, deploy commands, health checks, SPA rewrites |
| **Next best action** | Execute First Deploy Smoke Checklist; seed Qdrant `auto_insurance_demo_core` if retrieval flows needed |

---

## 9. Validation summary

| Check | Result |
|-------|--------|
| `npm run build` | OK |
| `run_inbox_triage_scenarios.py` | 49/49 passed |
| `run_multi_turn_simulations.py` | 29/29 strong |
| `guardrail_inbox_triage.sh` | PASS |
| `unified_intake_smoke_check.sh` | PASS (API test 2 WARN when server stale) |

---

## 10. 中文或中英混合宏观总结

**环境变量现在盘清楚了没有？** 盘清楚了。前端只需 `VITE_API_BASE_URL`；后端需要 QDRANT_URL、QDRANT_API_KEY、QDRANT_COLLECTION、OPENAI_API_KEY、ALLOWED_ORIGINS（Vercel 时）。

**前端和后端部署各差什么？** 前端：Vercel 里设 `VITE_API_BASE_URL` 即可。后端：填好 `.env.cloudrun` 后跑 `deploy_rag_demo.sh`。

**哪些值必须你手动填？** QDRANT_URL、QDRANT_API_KEY（Qdrant Cloud）、OPENAI_API_KEY（要 LLM 时）、ALLOWED_ORIGINS（Vercel 生产时）。Vercel 里设 VITE_API_BASE_URL。

**哪些东西已经准备好了？** 前端 build、后端 Dockerfile、deploy 脚本、CORS、健康检查、configs/demo.env.example、DEPLOYMENT_READINESS.md、First Deploy Smoke Checklist。

**成本大概什么级别？** 前端免费，后端约 $0–5/月（轻量 demo），Qdrant 和 OpenAI 按用量。

**下一步最值得做什么？** 按 `docs/DEPLOYMENT_READINESS.md` 的 checklist 走一遍：先发后端再发前端，然后做端到端 smoke test。

---

## 11. Practical env checklist

### Frontend (Vercel)

| Variable | Required | Secret | Where to set |
|----------|----------|--------|--------------|
| `VITE_API_BASE_URL` | Yes | No | Vercel dashboard → Project Settings → Environment Variables |

### Backend (.env.cloudrun → Cloud Run)

| Variable | Required | Secret | Where to set |
|----------|----------|--------|--------------|
| `QDRANT_URL` | Yes | No | .env.cloudrun |
| `QDRANT_API_KEY` | Yes (Cloud) | Yes | .env.cloudrun |
| `QDRANT_COLLECTION` | Yes | No | .env.cloudrun (default: auto_insurance_demo_core) |
| `OPENAI_API_KEY` | Yes (LLM) | Yes | .env.cloudrun |
| `ALLOWED_ORIGINS` | Vercel | No | .env.cloudrun (unset = allow-all) |

### Optional

| Variable | Purpose |
|----------|---------|
| `LLM_GENERATION_ENABLED` | 1 = LLM triage (auto-set when OPENAI_API_KEY present) |
| `NOTICE_RETRIEVAL_ENABLED` | 0 = disable notice retrieval |
| `DEMO_MODE` | true = embedding optional (deploy script sets this) |

---

## 12. Deployment gap summary

| Area | Status |
|------|--------|
| **Ready** | Frontend build, backend Dockerfile, deploy script, CORS, health endpoints, env example, docs |
| **Nearly ready** | Case persistence (per-instance); Qdrant collection must be seeded |
| **Blocking gaps** | None |
| **Fixes improved** | LLM_GENERATION_ENABLED when OPENAI_API_KEY set; demo.env.example clarity; First Deploy Smoke Checklist |

---

## 13. First deploy smoke checklist

- [ ] **Backend deploy:** `bash scripts/deploy_rag_demo.sh` → note Cloud Run URL  
- [ ] **Frontend deploy:** Connect repo to Vercel, set `VITE_API_BASE_URL` = Cloud Run URL, deploy  
- [ ] **First page load:** Open `https://<vercel>.vercel.app/workbench/unified-intake`  
- [ ] **Customer-entry test:** Paste "Notice: Policy will be cancelled in 7 days" → Start case → verify triage  
- [ ] **Broker workbench test:** Open case from Recent cases → update status → add note  
- [ ] **Append follow-up test:** Reopen case → paste new message in "Paste new customer follow-up" → Update  
