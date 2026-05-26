# Deployment Readiness + Vercel/GCP Cost Scouting Sprint Report

## 1. Stages completed

- Stage 1: Deployment target defined (Vercel + Cloud Run)
- Stage 2: Broad deployment readiness scouting
- Stage 3: Deployment gaps classified
- Stage 4: High-value fixes prioritized
- Stage 5: Improvement loop 1 (config, deploy script, docs)
- Stage 6: Improvement loop 2 (vercel.json, runbook section)
- Stage 7: Skipped (no further high-value gaps)
- Stage 8: Cost scouting
- Stage 9: Readiness verdict
- Stage 10: Documentation (DEPLOYMENT_READINESS.md, runbook §16)
- Stage 11: Audit + validation (build, guardrail, scenarios)

---

## 2. Deployment target

| Component | Host | Port / Notes |
|-----------|------|---------------|
| Frontend | Vercel | SPA, `ui/` root, `npm run build` → `dist` |
| Backend | GCP Cloud Run | fiqa_api, port 8080, min 0 / max 2 instances |
| Vector DB | Qdrant Cloud | Required for retrieval-assisted flows |
| Case store | In-memory / SQLite | Per-instance; acceptable for demo |

---

## 3. Repo / config / runtime findings

### Frontend (Vercel)

- **Build:** `npm run build` (Vite) works; output `dist`
- **API base URL:** `VITE_API_BASE_URL` in production; empty in dev → Vite proxy
- **vercel.json:** SPA rewrites for `/workbench/*`; explicit build/output added
- **Blockers:** None

### Backend (Cloud Run)

- **Dockerfile.cloudrun:** Exists; port 8080; fastembed pre-download; health check
- **CORS:** `ALLOWED_ORIGINS` supported; deploy script now passes it
- **Health:** `/healthz`, `/readyz`; DEMO_MODE makes embedding optional
- **Blockers:** Qdrant + OpenAI required for full Unified Intake

### Deployment scripts

- **deploy_rag_demo.sh:** Loads `.env.cloudrun`; validates Qdrant; deploys to Cloud Run
- **deploy_and_verify_cloud_run.sh:** Full deploy + health + query test
- **configs/demo.env.example:** Template for `.env.cloudrun`

### Gaps identified

1. **CORS:** Deploy script did not pass `ALLOWED_ORIGINS` → fixed
2. **OPENAI_API_KEY:** Deploy script did not pass it → fixed
3. **QDRANT_COLLECTION:** Default was fiqa_10k_v1; Unified Intake needs `auto_insurance_demo_core` → demo.env.example updated
4. **Documentation:** No compact deployment checklist → created

---

## 4. Deployment gaps and improvement loops

### Loop 1

| Fix | Where | Why |
|-----|-------|-----|
| Pass `ALLOWED_ORIGINS` to Cloud Run | deploy_rag_demo.sh | Vercel frontend needs CORS |
| Pass `OPENAI_API_KEY` to Cloud Run | deploy_rag_demo.sh | Inbox triage LLM |
| Clarify CORS in demo.env.example | configs/demo.env.example | Clear guidance |
| Set QDRANT_COLLECTION for Unified Intake | configs/demo.env.example | `auto_insurance_demo_core` |

### Loop 2

| Fix | Where | Why |
|-----|-------|-----|
| Add build/output to vercel.json | ui/vercel.json | Explicit Vite config |
| Add deployment section to runbook | UNIFIED_INTAKE_MVP_RUNBOOK.md §16 | One-place deployment steps |
| Create DEPLOYMENT_READINESS.md | docs/ | Compact checklist, env vars, cost |

---

## 5. Cost scouting

| Component | Light demo (few testers) | Notes |
|-----------|---------------------------|-------|
| **Vercel** | Free | Hobby tier; static + serverless |
| **Cloud Run** | ~$0–5/mo | Min 0, scales to zero; cold start ~5–15s |
| **Qdrant Cloud** | Free tier or low | Depends on cluster size |
| **OpenAI** | Pay-per-use | Inbox triage, jobhunter; ~$0.01–0.05/request |

**Cost drivers:** Always-on instances, high concurrency, egress, logs. For demo: keep min 0, max 2.

---

## 6. Readiness verdict

| Area | Verdict | Notes |
|------|---------|-------|
| **Frontend** | Ready | Build works; VITE_API_BASE_URL configurable |
| **Backend** | Ready | Dockerfile.cloudrun, deploy script, CORS |
| **End-to-end** | Nearly ready | Requires Qdrant + OpenAI + ALLOWED_ORIGINS |
| **Demo environment** | Ready after 1–3 manual steps | Create .env.cloudrun, set Vercel env, deploy |

**Go / nearly-go:** Ready to deploy after filling `.env.cloudrun` and setting Vercel `VITE_API_BASE_URL`.

---

## 7. Validation summary

- `npm run build` — OK
- `PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py` (LLM_GENERATION_ENABLED=0) — 49/49 passed
- `PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py` — 29 strong
- `bash scripts/guardrail_inbox_triage.sh` — PASS

---

## 8. Remaining blocker(s)

- **None blocking.** Manual steps: create `.env.cloudrun`, seed Qdrant `auto_insurance_demo_core`, set Vercel env, deploy.

---

## 9. Recommended next step

1. Create `.env.cloudrun` from `configs/demo.env.example`
2. Set `ALLOWED_ORIGINS` to Vercel URL(s) before first deploy
3. Deploy backend: `bash scripts/deploy_rag_demo.sh`
4. Deploy frontend: connect repo to Vercel, set `VITE_API_BASE_URL`, deploy
5. Smoke test: open `/workbench/unified-intake`, paste cancellation warning

---

## 10. 中文或中英混合宏观总结

**发到 Vercel + GCP 的准备度：** 基本就绪。前端和后端都有现成配置，差的是填好环境变量和部署。

**前端：** 可以直接发。`npm run build` 正常，`VITE_API_BASE_URL` 在 Vercel 里设成 Cloud Run 地址即可。

**后端：** 可以直接发。`Dockerfile.cloudrun` 和 `deploy_rag_demo.sh` 都有，这次补了 CORS（ALLOWED_ORIGINS）和 OPENAI_API_KEY 的传递。

**还要补的：** (1) `.env.cloudrun` 里填 QDRANT_URL、QDRANT_API_KEY、QDRANT_COLLECTION=auto_insurance_demo_core、OPENAI_API_KEY、ALLOWED_ORIGINS；(2) Vercel 里设 VITE_API_BASE_URL。

**粗略成本：** 前端免费，后端约 $0–5/月（轻量 demo），Qdrant 和 OpenAI 按用量计费。

**下一步最值得做：** 按 `docs/DEPLOYMENT_READINESS.md` 的 checklist 走一遍，先发后端再发前端，然后做一次端到端 smoke test。

---

## 11. Practical deployment checklist

- [ ] **Frontend readiness:** `cd ui && npm run build` succeeds
- [ ] **Backend readiness:** `Dockerfile.cloudrun` exists; `deploy_rag_demo.sh` runs
- [ ] **Env vars:** Create `.env.cloudrun` from `configs/demo.env.example`; set QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION=auto_insurance_demo_core, OPENAI_API_KEY, ALLOWED_ORIGINS
- [ ] **API URL / CORS:** Vercel `VITE_API_BASE_URL` = Cloud Run URL; Cloud Run `ALLOWED_ORIGINS` = Vercel URL(s)
- [ ] **Deploy commands:** Backend `bash scripts/deploy_rag_demo.sh`; Frontend `vercel --prod` (or connect repo)
- [ ] **Post-deploy:** `curl <Cloud Run>/healthz` → 200; open `/workbench/unified-intake`; paste cancellation message → triage works; no CORS errors

---

## 12. Deployment gap summary

| Area | Status |
|------|--------|
| **Strongest ready** | Frontend build, backend Dockerfile, deploy script, CORS support, health endpoints |
| **Acceptable but partial** | Case persistence (per-instance); Qdrant collection must be seeded |
| **Weak/blocking** | None |
| **Fixes improved** | CORS + OpenAI pass-through in deploy; QDRANT_COLLECTION guidance; deployment docs |

---

## 13. Cost summary

| Component | Cost band | Drivers |
|-----------|-----------|---------|
| **Frontend (Vercel)** | Free | Hobby tier |
| **Backend (Cloud Run)** | $0–5/mo | Min 0, max 2, 512Mi, 1 CPU |
| **Main cost drivers** | Qdrant, OpenAI, egress | Usage-based |
| **Safest low-cost posture** | Min instances 0, max 2; avoid always-on |
