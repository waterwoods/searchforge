# SearchForge Asset Inventory & Commercialization Report

**Generated**: 2026-02-22  
**Scope**: Full codebase audit for commercialization, MVP selection, and 2–3 week execution plan  
**Primary Goal**: First paying customer via insurance-broker AI assistant

---

## 1. Executive Summary

### What Exists Overall

SearchForge is a **multi-domain RAG/search platform** with:

- **Core**: Single FastAPI backend (`services/fiqa_api/app_main.py`) serving 80+ API routes
- **Verticals**: Auto insurance (demo-ready), JobHunter (JD analysis), Mortgage (stress check), E-commerce (refund agent), Vitals (health monitoring), Code Lookup (codebase analysis)
- **Infrastructure**: Qdrant Cloud, OpenAI embeddings, translation (Argos), Docker, Cloud Run deployment
- **UI**: React + Vite + Ant Design, 20+ pages under `/workbench`, `/demo`, `/jobhunter`, `/vitals`, etc.

### What Is Most Promising

**California Auto Insurance Broker Assistant** (`/demo` + `mode=demo` API):

- Purpose-built for 陈奎 (insurance broker) acceptance
- Demo quick validate **PASSED** (2026-02-21): gov+insurer mix, 5 sources per query
- Has offline fallback, one-click ingest, Cloud Run deploy script
- Clear value: brokers need instant answers with official citations (dmv.ca.gov, insurance.ca.gov)

### What Is Most Fragmented

- **Collection naming**: `auto_insurance_v1`, `auto_insurance_v2_clean`, `auto_insurance_demo_core` — multiple collections, inconsistent defaults
- **Entry points**: Makefile targets `PORT=8000`, scripts use `8001`; `rag-api` vs `fiqa-api` naming
- **Deprecated code**: `app.py`, `app_v2.py`, `/ops/*` routes still present
- **Vertical sprawl**: 6+ domain agents; only insurance demo is close to sellable

### Immediate Recommendation

**Focus 100% on the Auto Insurance Broker Demo.** Freeze JobHunter, Mortgage, E-commerce, Vitals, Code Lookup. Finish insurance demo polish, add Stripe/payment, deploy publicly, and get your broker friend to try it.

---

## 2. Project Inventory Table

| Project / Module | Path | Type | Purpose | Status | Completion % | Demo-ready? | Monetization | Notes |
|------------------|------|------|---------|--------|--------------|-------------|--------------|-------|
| **Auto Insurance Demo** | `ui/src/pages/DemoPage.tsx`, `routes/query.py` (mode=demo) | vertical demo | CA car insurance Q&A for brokers | Working | **85%** | **yes** | **high** | Passes quick_validate; offline fallback; gov+insurer mix |
| **Auto Insurance Pipeline** | `pipelines/auto_insurance_ingest.py`, `quality_gate_auto_insurance.py` | pipeline | Crawl, clean, chunk, upsert to Qdrant | Working | 75% | partial | medium | Discovery run exists; one-click ingest works |
| **Auto Insurance Discovery** | `scripts/discover_auto_insurance_sources.py` | pipeline | Discover URLs from seeds | Working | 70% | no | low | 60 candidates, 11 passing; statefarm blocked by robots.txt |
| **Search Core / RAG** | `services/fiqa_api/services/search_core.py`, `routes/query.py` | core platform | Vector search, rerank, translation | Working | 90% | yes | high | Reusable; Qdrant Cloud, BGE embeddings |
| **JobHunter** | `services/fiqa_api/jobhunter/`, `routes/jobhunter.py`, `ui/JobHunterPage.tsx` | vertical agent | JD analysis, career chat, resume, applications | Working | 80% | partial | medium | Full stack; SQLite; complex; not broker-focused |
| **Mortgage Agent** | `services/fiqa_api/mortgage/`, `routes/mortgage_agent.py` | vertical agent | Stress check, safer homes, single-home agent | Working | 70% | partial | medium | Mock listings; Zillow-like; more technical |
| **E-commerce Agent** | `services/fiqa_api/ecommerce/`, `routes/ecommerce_agent.py` | vertical agent | Refund/return policy, NL→intent | Working | 65% | no | low | Mock orders; no dedicated UI in App |
| **Vitals / Health** | `services/vitals_ingest_lite/`, `vitals_viewer/`, `routes/health_monitor.py` | vertical service | Vitals ingest, dashboard | Working | 60% | partial | low | Separate services; care management |
| **Code Lookup Agent** | `services/fiqa_api/services/code_lookup_service.py`, `CodeLookupPage.tsx` | vertical agent | Codebase analysis, graph | Working | 75% | partial | low | Dev tool; not customer-facing |
| **Ops Copilot** | `services/fiqa_api/ops_copilot/` | vertical agent | System health, LabOps | Working | 60% | no | low | Internal ops; not sellable |
| **RAG Lab / Experiment** | `ui/RagLabRunPage`, `api/experiment/*` | lab | Run experiments, review jobs | Working | 70% | no | low | Internal tooling |
| **Metrics Hub** | `ui/MetricsHub.tsx`, `routes/metrics.py` | lab | KPI, demo summary, auto-insurance eval | Working | 70% | no | low | Internal |
| **Showtime / Workbench** | `ui/ShowtimePage`, `WorkbenchPage` | UI hub | Landing, lab entry | Working | 70% | no | low | Dev landing |
| **Deploy RAG Demo** | `scripts/deploy_rag_demo.sh` | deploy | Cloud Run deploy for fiqa-api | Working | 85% | yes | high | Uses .env.cloudrun |
| **Run Demo Local** | `scripts/run_demo_local.sh` | runnable | Start backend + UI for demo | Working | 90% | yes | high | Port 8001, 5173 |
| **Demo Quick Validate** | `scripts/demo_quick_validate.sh` | validation | 3-query validation (gov+insurer) | Working | 95% | yes | medium | Last PASS 2026-02-21 |
| **One-Click Demo Ingest** | `scripts/run_demo_ingest_oneclick.sh` | pipeline | Fetch→extract→embed→upsert demo_core | Working | 85% | yes | medium | Depends on discovery run |
| **Demo Prepare Tomorrow** | `scripts/demo_prepare_tomorrow.sh` | runnable | Snapshot + validate for offline pack | Working | 85% | yes | medium | For next-day demo |

---

## 3. Best Monetization Candidate

### California Auto Insurance Broker Assistant

**Why this one**

- Built for a real user (陈奎, insurance broker)
- Solves a concrete pain: brokers need instant, cited answers to client questions (最低保额、注册暂停、合规查询)
- Demo already passes acceptance; UI, backend, and data pipeline exist
- Small brokers are underserved; low competition for niche AI tools

**Why now**

- Demo quick validate passed; `auto_insurance_demo_core` has gov+insurer sources
- One-click ingest and deploy scripts are in place
- 2–3 weeks of polish is enough to reach “paying friend” stage

**Customer**

- Independent CA auto insurance brokers
- Small agencies (1–5 agents) without internal knowledge bases

**Pain point**

- Clients ask the same questions (最低保险、SR-22、注册恢复); brokers waste time searching DMV/CDI sites
- Need answers with official URLs for compliance and trust

**Already built**

- `ui/src/pages/DemoPage.tsx` — 3 sample questions, Live/Offline, gov/insurer badges
- `POST /api/query` with `mode=demo`, `collection=auto_insurance_demo_core`
- Translation (zh→en for search, en→zh for display)
- `scripts/run_demo_ingest_oneclick.sh`, `deploy_rag_demo.sh`
- Offline fallback via `demo_fallback.json`

**Missing**

- LLM answer generation (optional; retrieval + snippets may be enough for MVP)
- Payment (Stripe or similar)
- Auth / multi-tenant (can start single-tenant)
- Public demo URL and simple landing
- 1–2 more broker-specific questions/scenarios

---

## 4. Freeze / Keep / Finish Matrix

### Freeze for now

| Item | Path | Reason |
|------|------|--------|
| JobHunter | `jobhunter/`, `JobHunterPage.tsx` | Feature-rich but complex; not broker-focused |
| Mortgage | `mortgage/`, `MortgageAssistantPage`, `SingleHomeStressPage` | Mock data; different vertical |
| E-commerce | `ecommerce/` | No UI; mock orders |
| Vitals | `vitals_ingest_lite`, `vitals_viewer`, `VitalsDashboardPage` | Care management; different vertical |
| Code Lookup | `code_lookup_service`, `CodeLookupPage` | Dev tool |
| Ops Copilot | `ops_copilot/` | Internal |
| RAG Lab / Experiment | `RagLabRunPage`, experiment API | Internal |
| Deprecated | `_deprecated/`, `app_v2.py`, `/ops/*` | Legacy; do not extend |

### Keep as reusable foundation

| Item | Path | Reason |
|------|------|--------|
| Search core | `search_core.py`, `qdrant_adapter` | Shared RAG engine |
| Query route | `routes/query.py` | Core API; demo mode is a flag |
| Translation | `utils/translation.py` | zh/en support |
| Clients | `clients.py` (OpenAI, Qdrant) | Shared infra |
| UI layout | `AppLayout`, `AppSider` | Base layout |
| Deploy script | `deploy_rag_demo.sh` | Reusable for any fiqa-api deploy |

### Finish immediately

| Item | Path | Action |
|------|------|--------|
| Demo polish | `DemoPage.tsx`, `demoCopy.ts` | Refine copy, add 1–2 broker scenarios |
| Demo collection | `auto_insurance_demo_core` | Ensure 30+ docs; re-run one-click ingest if needed |
| Payment | New | Add Stripe (or similar) for first paid tier |
| Landing | New or `ShowtimePage` | Simple “Insurance Broker AI” landing |
| Public URL | Cloud Run | Deploy and share demo URL with broker friend |

---

## 5. 2–3 Week MVP Plan

### Week 1: Demo hardening and broker feedback

**Objective**: Demo is stable, presentable, and validated with your broker friend.

**Deliverables**

- Run `bash scripts/run_demo_local.sh` and confirm Live mode works
- Run `bash scripts/demo_quick_validate.sh` — must PASS
- If `auto_insurance_demo_core` is thin: run `bash scripts/run_demo_ingest_oneclick.sh`
- Add 1–2 broker-specific questions to `DemoPage` (e.g., SR-22, 保费上涨)
- Schedule 30-min demo with broker friend; capture feedback

**Acceptance**

- [ ] Demo loads at http://localhost:5173/demo
- [ ] All 3 sample questions return ≥3 sources with gov+insurer mix
- [ ] Broker friend sees value and can articulate 1–2 improvements

---

### Week 2: Payment and landing

**Objective**: Can collect payment and have a simple public presence.

**Deliverables**

- Add Stripe (or Paddle/LemonSqueezy) for a “Pro” or “Broker” tier
- Create minimal landing page: “CA Auto Insurance Broker AI — instant answers with official citations”
- Deploy backend to Cloud Run: `bash scripts/deploy_rag_demo.sh`
- Deploy frontend (Vercel/Netlify or static) pointing to Cloud Run API
- Share public URL with broker friend

**Acceptance**

- [ ] Landing page live with CTA
- [ ] Payment flow completes (even if $0 trial)
- [ ] Public demo URL returns 200 for `/healthz` and `/api/query`

---

### Week 3: First paying customer

**Objective**: Broker friend becomes first paying customer.

**Deliverables**

- Implement feedback from Week 1 (e.g., more questions, better snippets)
- Add simple auth (e.g., email + magic link) if needed for paid tier
- Create “Broker Pro” offer: e.g., $29/mo for unlimited queries
- Send personalized invite to broker friend with discount
- Document onboarding: “How to use” in 3 steps

**Acceptance**

- [ ] First payment received
- [ ] Broker can run 5+ real client questions and get usable answers
- [ ] One testimonial or quote for landing page

---

## 6. Missing Pieces Before Selling

### Before demo to broker friend

- [ ] Backend running and reachable (local or Cloud Run)
- [ ] `auto_insurance_demo_core` has ≥20 docs (gov + insurer)
- [ ] Demo quick validate PASS
- [ ] 3 sample questions work; optional: LLM answer generation

### Before asking for payment

- [ ] Payment integration (Stripe or similar)
- [ ] Simple terms of use / privacy policy
- [ ] Clear pricing (e.g., $29/mo)

### Before public deploy

- [ ] Cloud Run deploy verified
- [ ] Frontend deployed and wired to backend
- [ ] CORS and env vars correct for production
- [ ] `.env.cloudrun` has real Qdrant + OpenAI keys

### Optional (can defer)

- Multi-tenant auth
- Usage limits / rate limiting
- LLM answer generation (retrieval-only may suffice for MVP)

---

## 7. Recommended Next Actions

1. **Run demo locally and validate**
   ```bash
   cd /home/andy/searchforge
   bash scripts/run_demo_local.sh
   # In another terminal:
   bash scripts/demo_quick_validate.sh
   ```
   Confirm PASS. If fail, check `auto_insurance_demo_core` and re-run one-click ingest.

2. **Schedule 30-min demo with broker friend**
   - Use http://localhost:5173/demo (or Cloud Run URL if deployed)
   - Ask: “What questions do your clients ask most?” — add 1–2 to the demo

3. **Add Stripe (or alternative)**
   - Create Stripe account and product (e.g., “Broker Pro $29/mo”)
   - Add checkout button to a minimal landing or DemoPage
   - Start with test mode; switch to live when ready

4. **Deploy to Cloud Run**
   ```bash
   cp configs/demo.env.example .env.cloudrun
   # Edit .env.cloudrun with QDRANT_*, OPENAI_API_KEY
   bash scripts/deploy_rag_demo.sh
   ```
   Note the service URL for the frontend.

5. **Create minimal landing page**
   - Title: “CA Auto Insurance Broker AI”
   - Value prop: “Instant answers with official citations (DMV, CDI)”
   - CTA: “Try Demo” → demo URL; “Get Pro” → payment
   - Can be a single HTML page or a small React route

---

## Appendix A: Runnable Entry Points

| Command | Purpose |
|---------|---------|
| `bash scripts/run_demo_local.sh` | Start backend (8001) + UI (5173) for demo |
| `bash scripts/run_demo_ingest_oneclick.sh` | One-click ingest to `auto_insurance_demo_core` |
| `bash scripts/demo_quick_validate.sh` | Validate 3 queries (gov+insurer) |
| `bash scripts/demo_prepare_tomorrow.sh` | Snapshot + validate for offline pack |
| `bash scripts/deploy_rag_demo.sh` | Deploy fiqa-api to Cloud Run |
| `set -a; source .env.cloudrun; set +a; TRANSLATION_ENABLED=1 TRANSLATION_PROVIDER=argos python3 -m uvicorn services.fiqa_api.app_main:app --host 0.0.0.0 --port 8001` | Manual backend start |
| `cd ui && npm run dev` | UI only (port 5173) |
| `make dev-api` | Docker compose up rag-api (port 8000) |
| `make smoke` | Health check (expects port 8000) |

---

## Appendix B: Deployment Clues

| Item | Path / Value |
|------|--------------|
| Backend Dockerfile | `services/fiqa_api/Dockerfile.cloudrun` |
| Env template | `configs/demo.env.example` |
| Secrets file | `.env.cloudrun` (git-ignored) |
| Required env | `QDRANT_URL`, `QDRANT_API_KEY`, `QDRANT_COLLECTION`, `OPENAI_API_KEY` |
| Demo collection | `auto_insurance_demo_core` |
| Default collection | `auto_insurance` → `auto_insurance_v2_clean` (or `demo_auto_insurance` → `auto_insurance_demo_core`) |
| Vite proxy | `/api`, `/healthz` → `http://127.0.0.1:8001` |

---

## Appendix C: Env / Config Dependencies

| Variable | Used By | Default / Note |
|----------|---------|----------------|
| `QDRANT_URL` | Backend | Required for Cloud |
| `QDRANT_API_KEY` | Backend | Required for Qdrant Cloud |
| `QDRANT_COLLECTION` | Backend | `fiqa_10k_v1` in .env.cloudrun; demo uses `auto_insurance_demo_core` |
| `OPENAI_API_KEY` | Backend | For embeddings + LLM |
| `LLM_GENERATION_ENABLED` | Backend | `true` to enable answer generation |
| `TRANSLATION_ENABLED` | Backend | `1` for zh/en |
| `TRANSLATION_PROVIDER` | Backend | `argos` |
| `VITE_API_BASE_URL` | UI | Empty = use Vite proxy |
| `VITE_API_PROXY_TARGET` | UI | `http://127.0.0.1:8001` |

---

## Appendix D: Suspected Broken or Missing Pieces

| Item | Location | Issue |
|------|----------|-------|
| Port mismatch | Makefile uses 8000; scripts use 8001 | `run_demo_local.sh` uses 8001; `make smoke` expects 8000 |
| `rag-api` vs `fiqa-api` | Makefile `SERVICE=rag-api` | Docker compose service name; app is fiqa_api |
| `auto_insurance_v1` | Old reports | Only 17 docs; superseded by `auto_insurance_demo_core` |
| Demo fallback `answer` | `demo_fallback.json` | Empty strings; snapshot ran without LLM |
| `/api/jobhunter/preferences` | JobHunter | Referenced in UI comment; may not exist |
| `langgraph.checkpoint.sqlite` | app_main | Optional; graph_run import fails if missing |
| Redis | clients.py | Connection refused; non-critical |
| `rank-bm25` | search/bm25 | Optional; hybrid search degraded if missing |

---

*End of report*
