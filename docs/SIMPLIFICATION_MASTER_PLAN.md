# Simplification Master Plan — Unified Intake Paid Pilot

**Authority:** This is the **reduction roadmap** for SearchForge → sellable pilot SaaS.  
**Runtime truth still wins in:** [`docs/CURRENT_PRODUCT_SHAPE.md`](CURRENT_PRODUCT_SHAPE.md)  
**When this file conflicts with a sprint doc:** this file wins for *what to delete/hide*; CURRENT_PRODUCT_SHAPE wins for *what is deployed today*.

**Philosophy:** ONE PRODUCT · ONE DEPLOY · ONE DATABASE · ONE PRIMARY PATH · ONE SUPPORT STORY.

**Last inventory:** 2026-05-26 (repo scan + code grep).

---

## 1. CURRENT_REAL_PRODUCT

### What the product ACTUALLY is

**Unified Intake** — a broker-office SaaS wedge for California auto insurance intake:

| Surface | What it does |
|---------|----------------|
| Customer intake | Paste/text/image → classify → ask for gaps → structured case |
| Add-car workflow | Flagship path: vehicle scope, field strategy, handoff phrases |
| Broker workbench | Case list, triage, notes, drafts, office confirmation boundary |
| Session/case continuity | `session_id`, bindings, append flows, PG-backed vehicle row when configured |
| Support manifest | `GET /api/inbox/support/deployment-manifest` — operator truth without SSH |

**Customers pay for:** faster, safer intake → office-ready cases → broker control (no auto-send).  
**Operators support:** Postgres cases, API keys, deployment-manifest warnings, trial scripts.  
**Founders maintain:** monolithic `triage.py` + `inbox_triage.py` routes, client packs, guardrails.

### What it is NOT (stop pretending)

- SearchForge R&D platform (RAG lab, tuner, graph, vitals, jobhunter, mortgage)
- Enterprise IAM / multi-tenant admin
- “Trusted Assistant Platform” as a separate SKU (`docs/TRUSTED_ASSISTANT_PLATFORM_BLUEPRINT.md` is **investor theater** — useful framing, dangerous as build list)
- Full CRM, Stripe billing, workflow engine, event bus

---

## 2. CURRENT_REAL_DEPLOYMENT

### Topology (the only honest production story)

```
Browser (Vercel UI)
    → HTTPS → Cloud Run (FastAPI fiqa-api)
        → Postgres (SERVICE_RECORD_DATABASE_URL)
        → Qdrant (optional; notice/knowledge — not core triage gate)
```

### Required services

| Service | Paid pilot | Local demo |
|---------|------------|------------|
| Vercel | Yes | Optional (vite dev) |
| Cloud Run API | Yes | `run_demo_local.sh` :8001 |
| Postgres | **Required** | Optional (JSON fallback laptop-only) |
| Qdrant | Often configured | Demo ingest / RAG wedge |
| Redis / multi-region | **No** | Lab leftovers |

### Deployment modes

| Mode | Entry script | API flag | Persistence |
|------|--------------|----------|-------------|
| **Paid pilot** | `scripts/deploy_paid_pilot.sh` | `UNIFIED_INTAKE_PRODUCT_ONLY=1` | PG-primary only |
| Demo cloud smoke | `scripts/deploy_demo_cloud_smoke.sh` | product_only **off** | DEMO_MODE relaxed |
| Local founder demo | `scripts/run_demo_local.sh` | May be platform_full | JSON OK without DB |
| **Wrong path** | `scripts/deploy_rag_demo.sh` direct | Operator must not use as entry | Impl only |

### Required env (paid pilot — hard fail in validators)

See `pilot_safe_default_profile_v1()` in `services/fiqa_api/deployment_profile.py` and [`CURRENT_PRODUCT_SHAPE.md`](CURRENT_PRODUCT_SHAPE.md).

**UI mirror (Vercel):** `VITE_API_BASE_URL` + `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1` hides lab/simulation chrome (see `ui/src/config/productSurface.ts`).

### Health / readiness endpoints (operator confusion source)

| Path | Role |
|------|------|
| `/health/live`, `/api/healthz` | Liveness |
| `/readyz`, `/health/ready` | Readiness (Qdrant/DB honesty) |
| `/health` | JSON detail + `deployment_profile` + warnings |
| `/api/health/qdrant` | Vector dependency |
| `/api/inbox/support/deployment-manifest` | Support perimeter + posture |

**Trap:** Cloud Run front door may 404 on bare `/healthz`; use `/health/live` or `/api/healthz`.

---

## 3. CURRENT_REAL_PERSISTENCE

### Truth

| Layer | Paid pilot | Legacy (dev only) |
|-------|------------|-------------------|
| Cases / service records | Postgres `service_records` | `data/demo_cases.json` |
| Sessions | Postgres `intake_sessions` when DB URL set | In-memory if test flag |
| Vehicle entity | PG row + route finalizer `_finalize_response_with_pg_truth` | Heuristics pre-mirror |
| Analytics funnel | In-process counters | Not multi-instance truth |

### Dangerous (do not “simplify” without ops sign-off)

- `UNIFIED_INTAKE_JSON_READ_FALLBACK=1` in prod — silent JSON authority
- `UNIFIED_INTAKE_PG_DUAL_WRITE=1` — two write paths
- `UNIFIED_INTAKE_ALLOW_INMEMORY_SESSIONS_FOR_TESTS=1` with DB URL — multi-instance lies
- `active_vehicle_resolver.py` — **tested but not imported by `triage.py`** (dead wiring or future — pick one)

### Delete later (after revenue + migration proof)

- JSON case path entirely
- Dual-write flags and branches in `case_truth_repository.py`
- In-memory session backend in prod configs

---

## 4. TOP_COMPLEXITY_SOURCES

### Ranked — code mass

| Rank | Source | Lines / scale | Why exists | Who needs | Customer cares? | Support pain | Deploy pain | Action |
|------|--------|---------------|------------|-----------|-------------------|--------------|------------|--------|
| 1 | `triage.py` | ~6,426 | All intake logic in one file | Founders | Indirect | **High** regression | Low | **FREEZE** behavior; split **AFTER_REVENUE** |
| 2 | `routes/inbox_triage.py` | ~2,100 | HTTP + PG finalize + support | Ops/dev | Yes | Medium | Medium | **FREEZE** contracts |
| 3 | `app_main.py` + platform routers | ~1,150 + 15 routers | SearchForge heritage | R&D | No | Low if product_only | **High** if platform_full in prod | **KEEP** gated; product_only default |
| 4 | UI `App.tsx` lab routes | 20+ routes | R&D demos | Founders | No | Confusion | Bundle bloat | **HIDE** sidebar; **DELETE_LATER** routes |
| 5 | Tab D simulation (`UnifiedIntakePage`) | Bundled | QA/demo | Founders | No | Analytics leak | Vercel bundle | **HIDE** with `VITE_*` |
| 6 | Env matrix | 40+ `UNIFIED_INTAKE_*` | Migration safety | Ops | No | **High** misconfig | **High** | **FREEZE** tuple; validate script |
| 7 | Sprint docs | **992** `.md` under `docs/sprints` | Sprint habit | Agents | No | **Wrong mental model** | Low | **ARCHIVE** batches |
| 8 | Shell scripts | **197** `.sh` | Years of experiments | Andy | No | Which script? | Drift | **ARCHIVE** unused; 8 entry scripts |
| 9 | `results/*.md` | 15+ time slices | Lock-in reports | Nobody daily | No | Contradicts code | Low | **ARCHIVE** |
| 10 | Dual persistence | JSON + PG | Laptop demos | Devs | No | **Lost cases** | **High** | **DELETE_LATER** JSON in prod |
| 11 | Optional API keys | intake/support | Gradual rollout | Ops | Security | Anonymous endpoints | Medium | **KEEP**; enforce prod warnings |
| 12 | Broker HMAC token | `minimal_signed_broker_token` | Pilot perimeter | Ops | Medium | Secret rotation | Medium | **KEEP**; document only |
| 13 | `X-Org-Id` header | Hint / audit | “Sounds like tenancy” | Sales mistake | **High** expectation gap | Low | **FREEZE** docs: non-authoritative |
| 14 | Qdrant on `/readyz` | RAG demo | Chen Kui parallel | Partial | 503 warmup theater | **High** demo | **HIDE** from intake-core checklist |
| 15 | Platform blueprints | TRUSTED_ASSISTANT, FUTURE_SAAS | Fundraising narrative | Nobody ops | No | Scope creep | Low | **ARCHIVE** mentally |
| 16 | `active_vehicle_resolver` unwired | Module exists | Incomplete sprint | Devs | Vehicle bugs | Medium | Low | **DELETE_LATER** or wire — pick one |
| 17 | Scenario Logic Center UI | Founder tool | Pack review | No | Low | Low | **HIDE** in product_only UI |
| 18 | Add-car rules page | Config editing | Founders | No | Low | Low | **HIDE** pilot UI |
| 19 | 16 git stashes | Old branches | History | Andy | No | Resurrect dead code | Low | **DELETE** when safe |
| 20 | Node version drift | `engines >=20.19` | Vite 6 | CI/Vercel | No | Build fail | **High** recurring | **HARDEN** in CI + README |

### Ranked — documentation sprawl

| Source | Count | Verdict |
|--------|-------|---------|
| `docs/sprints/*.md` | 992 files | **DEAD WEIGHT** for onboarding; **ARCHIVE** in batches |
| `docs/*.md` (total) | 1389 | 90% not READ_FIRST |
| Parallel “REAL_SAAS / FUTURE_SAAS” SSOTs | 20+ | **PLATFORM FANTASY** — merge into this file |
| `PROJECT_DOC_SYSTEM_MAP` lists platform blueprint as PRIMARY | 1 | **Misleading** — demote to supporting |
| `ANDY_QUICK_START` vs 6 deploy runbooks | 6 | **Collapse** to CURRENT_PRODUCT_SHAPE + DEPLOYMENT_PLAYBOOK |

### Ranked — deploy / runtime forks

| Fork | Risk | Action |
|------|------|--------|
| `deploy_paid_pilot` vs `deploy_demo_cloud_smoke` vs raw `deploy_rag_demo` | Wrong posture | **KEEP** wrappers only |
| `platform_full` local default | False confidence | Warn on startup (exists) |
| `DEMO_MODE` + `ENV=prod` | Lie to brokers | Validator + warning (exists) |
| Vercel `VITE_API_BASE_URL` vs Cloud Run URL aliases | Network Error | **HARDEN** playbook |
| Readiness checks Qdrant vs intake-only trial | Failed trial_launch | Document **intake-core** subset |

---

## 5. PRODUCT_REDUCTION_CLASSIFICATION

| Subsystem | Class | Notes |
|-----------|-------|-------|
| Unified Intake triage + workbench | **CORE SKU** | |
| Postgres cases/sessions | **CORE SKU** | |
| Client pack (`chen_kui`, etc.) | **CORE SKU** | |
| Intake + support API keys | **CORE SKU** | Coarse auth |
| deployment-manifest + warnings | **CORE SKU** | Support story |
| Minimal signed broker token | **SUPPORTING** | Optional but valuable |
| Guardrail + trial_launch scripts | **SUPPORTING** | |
| `validate_pilot_deploy_env.py` | **SUPPORTING** | |
| Health / ready / live | **SUPPORTING** | |
| Qdrant + RAG `/api/query` | **OPTIONAL** | Parallel demo wedge |
| Analytics dashboard API | **OPTIONAL** | Founder metrics |
| Assist layer (background thread) | **OPTIONAL** | |
| OCR / image paths | **OPTIONAL** | |
| WeChat sim | **OPTIONAL** | |
| Scenario replay Tab D | **INTERNAL ONLY** | Hide in prod UI |
| Scenario Logic Center | **INTERNAL ONLY** | |
| Add-car rules page | **INTERNAL ONLY** | |
| RAG lab / workbench labs | **DEAD WEIGHT** for pilot | Hide |
| Vitals, steward, autotuner, graph | **PLATFORM FANTASY** | Router-gated off product_only |
| Tenant/RLS sprint narratives | **PLATFORM FANTASY** | Docs ≠ IAM |
| `TRUSTED_ASSISTANT_PLATFORM_BLUEPRINT` | **PLATFORM FANTASY** | |
| `FUTURE_SAAS_OPERATING_SYSTEM_*` | **FUTURE ONLY** | |
| JSON case files in prod | **DANGEROUS** (classified as dead weight path) | |
| 992 sprint markdown files | **DEAD WEIGHT** | |
| `triage.py` monolith | **DANGEROUS** to refactor blindly | **FREEZE** |

---

## PHASE 3 — RECURRING FAILURE HUNT

| Problem | Why fixes fail | Why it returns | Make wrong path impossible |
|---------|----------------|----------------|----------------------------|
| Node / Vite mismatch | Vercel ≠ local Node; README stale | No CI gate on `engines` | `ui/package.json` engines + `npm run verify:deps` in release checklist |
| Deploy script drift | Operators call `deploy_rag_demo` | Too many scripts (197) | Only document 3 entries; tests on wrappers |
| product_only inconsistencies | Old sprint docs say inline routes leak | Docs not updated after wire closure | `PLATFORM_INLINE_ROUTES_UNGATED` empty; health reports leak count |
| JSON persistence lingering | Laptop demos need JSON | Copy-paste `.env` | `validate_pilot_deploy_env` + prod warnings |
| Env drift | 300-line `demo.env.example` | Every sprint adds vars | PILOT ONE PATH block only for operators |
| Old docs contradict runtime | 992 sprint files immutable | No archive discipline | This plan + `docs/sprints/README.md` banner |
| Multiple deploy stories | ANDY_QUICK_START vs DEPLOYMENT_READINESS vs playbooks | No single reduction SSOT | **This file** + CURRENT_PRODUCT_SHAPE |
| Simulation in product bundle | Same page as customer intake | No UI flag | `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1` |
| Platform routes in bundle | Single `App.tsx` imports all pages | No code-split by product | Hide nav first; lazy-split **AFTER_REVENUE** |
| Readiness vs intake-core | `/readyz` checks Qdrant | Demo stack needs vectors | `trial_readiness_check` documents subset; don't claim full stack for intake-only |

---

## PHASE 4 — FINAL CONVERGENCE

### THE_REAL_PRODUCT

Unified Intake: customer intake → add-car → broker workbench → Postgres truth → coarse API keys → support manifest.

### THE_REAL_DEPLOYMENT

Vercel + Cloud Run + Postgres. Entry: `deploy_paid_pilot.sh`. Flag: `UNIFIED_INTAKE_PRODUCT_ONLY=1`. Validate: `validate_pilot_deploy_env.py`.

### THE_REAL_SUPPORT_MODEL

deployment-manifest, operator warning codes, intake/support keys, case-head export — not enterprise replay or SIEM.

### THE_REAL_AUTH_MODEL

`UNIFIED_INTAKE_INTAKE_API_KEY`, `UNIFIED_INTAKE_SUPPORT_API_KEY`, optional HMAC broker token — **not** OAuth/SSO/RBAC.

### THE_REAL_PERSISTENCE_MODEL

Postgres-primary; JSON = dev-only; dual-write = forbidden in prod.

### STOP_BUILDING

OAuth, SSO, RBAC, Stripe, tenant admin UI, fake RLS, workflow engine, event bus, microservices split, multi-region HA, plugin marketplace, “AI operating system” layers.

### FREEZE (touch only with full regression)

- `triage.py` behavior
- PG schema / migrations
- Office enforcement semantics
- Token scope semantics
- Case/session continuity contracts
- Support manifest JSON shape
- Append flow logic

### HIDE (done or in progress this sprint)

- Lab sidebar items when `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1`
- Simulation tab when same
- Scenario logic / add-car rules nav in product-only UI

### ARCHIVE (batch moves to `docs/sprints/archive/`)

- KILL_LEGACY, PILOT_TO_REAL_SAAS, LONG_HORIZON_FUTURE_SAAS sprint docs (listed in `docs/sprints/README.md`)
- `results/*REPORT*.md` after banner in DOC_INDEX

### DELETE_LATER (post-revenue)

- JSON case path
- Unused lab UI routes and imports
- `active_vehicle_resolver` if never wired
- 800+ sprint files after git history sufficient

### AFTER_REVENUE_ONLY

- Split `triage.py` by vertical slice
- Lazy-load lab routes from bundle
- Gate inline routes permanently (already done for API)
- Multi-office DB column promotion
- Audit export bundles

---

## THE_10_HIGHEST_ROI_SIMPLIFICATIONS

| # | Action | Risk | Ops benefit | Founder sanity | Order |
|---|--------|------|-------------|----------------|-------|
| 1 | **Single operator doc path:** CURRENT_PRODUCT_SHAPE → DEPLOYMENT_PLAYBOOK → this plan | Low | Fewer wrong deploys | Stop reading 992 sprints | **Done** (docs) |
| 2 | **`VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1` on Vercel** — hide lab + simulation UI | Low | Brokers don't see R&D | One UI story | **Done** (code) |
| 3 | **Enforce deploy entry scripts** — never document `deploy_rag_demo` to humans | Low | Correct Cloud Run env | Less “why DEMO_MODE?” | Done (prior sprints) |
| 4 | **Batch-archive sprint docs** (50–100 files/quarter) | Low | — | Agents stop hallucinating wiring | Next |
| 5 | **Collapse `demo.env.example` to PILOT block + appendix** | Low | Faster `.env.cloudrun` | Less env anxiety | Next |
| 6 | **Demote platform blueprints from PROJECT_DOC_SYSTEM_MAP PRIMARY** | Low | — | Stops scope creep | Next |
| 7 | **Wire or delete `active_vehicle_resolver`** | Medium | Fewer vehicle bugs | One resolver story | Deferred |
| 8 | **Lazy-split lab pages from Vite bundle** | Medium | Smaller Vercel | Faster builds | AFTER_REVENUE |
| 9 | **Intake-only readiness profile** in trial scripts | Low | Trials pass without Qdrant | Less 503 panic | Next |
| 10 | **Delete JSON case path in prod configs** (config only, keep dev) | Medium | No lost cases | One persistence story | AFTER_REVENUE |

---

## INVENTORY SNAPSHOT (Phase 0)

| # | Category | Finding |
|---|----------|---------|
| 1 | Runtime paths | 8001 local (`run_demo_local.sh`), 8000 Docker, recovery `restore_8001_readiness.sh` |
| 2 | Deployment paths | `deploy_paid_pilot.sh`, `deploy_demo_cloud_smoke.sh`, `deploy_and_verify_cloud_run.sh` |
| 3 | Persistence paths | PG via `SERVICE_RECORD_DATABASE_URL`; JSON via `UNIFIED_INTAKE_CASES_PATH` |
| 4 | UI routes | **CORE:** `/workbench/unified-intake`, `/demo`; **LAB:** 20+ under `/workbench/*`, `/rag-lab/*`, tests |
| 5 | Platform/lab routes | See `App.tsx` imports — all in one bundle |
| 6 | Startup modes | `FAST_STARTUP`, `DEMO_MODE`, `UNIFIED_INTAKE_PRODUCT_ONLY` |
| 7 | Health endpoints | §2 table |
| 8 | Support endpoints | `/api/inbox/support/deployment-manifest`, `case-head`, export gates |
| 9 | Scripts | 197 shell — **8 operator entries** in AGENTS.md |
| 10 | Docs | 1389 md; PRIMARY should be ≤10 files |
| 11 | Sprint docs | 992 files — **misleading if read as truth** |
| 12 | Env vars | 40+ intake/record flags; pilot tuple = 11 keys |
| 13 | Middleware | intake_api_gate, support_export_gate, case_office_access, rate limit |
| 14 | Analytics | `/api/analytics/dashboard`, in-process funnel |
| 15 | Simulation | Tab D + `ScenarioReplayTab` + Role C LLM |
| 16 | Dead code | `active_vehicle_resolver` unwired from triage |
| 17 | Duplicate systems | JSON vs PG cases; platform_full vs product_only |
| 18 | Legacy fallbacks | JSON read fallback, in-memory sessions |
| 19 | “Future” systems | FUTURE_SAAS, TENANT_RLS, HUNDRED_OFFICES sprint docs |
| 20 | Enterprise theater | TRUSTED_ASSISTANT platform blueprint, tenant truth narratives |

---

## Iteration log (Phase 1 safe reductions — 2026-05-26)

| Change | Type |
|--------|------|
| `docs/SIMPLIFICATION_MASTER_PLAN.md` | Created (this file) |
| `ui/src/config/productSurface.ts` | Product-only UI gate |
| `AppSider.tsx` | Hide lab nav when `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1` |
| `UnifiedIntakePage.tsx` | Hide simulation tab + CTA when product-only UI |
| `configs/demo.env.example` | Vercel UI flag documented |
| `docs/PROJECT_DOC_SYSTEM_MAP.md` | Point to reduction SSOT; demote platform blueprint |
| `docs/sprints/README.md` | Point to reduction SSOT |
| `AGENTS.md` / `CURRENT_PRODUCT_SHAPE.md` | Cross-links |
| `tests/test_simplification_master_plan_doc.py` | Guard doc presence |

### Phase 2 validation (2026-05-26)

| Check | Result | Notes |
|-------|--------|-------|
| `compileall services/fiqa_api tests` | **PASS** | `scripts/run_demo_pack_original.py` has pre-existing SyntaxError if whole `scripts/` compiled |
| `pytest` (full) | **PASS** | 1 skipped |
| `guardrail_inbox_triage.sh` | **PASS** | |
| `run_full_regression.py` | **PASS** | `http_p95_ms` ≈ 5291 &lt; 6000 |
| `npm run build` (ui) | **PASS** with Node **v22.22.0** on PATH | Default shell Node **v20.18.2** fails Vite — recurring trap #1 |
| `madge --circular` | **PASS** | |

---

## Related

| Doc | Role |
|-----|------|
| [`CURRENT_PRODUCT_SHAPE.md`](CURRENT_PRODUCT_SHAPE.md) | Runtime/deploy SSOT |
| [`DEPRECATED_PATHS.md`](DEPRECATED_PATHS.md) | Legacy behavior map |
| [`DOC_INDEX_RECOMMENDED.md`](DOC_INDEX_RECOMMENDED.md) | Navigation without deletes |
| [`docs/sprints/PRODUCT_SIMPLIFICATION_SAAS_REDUCTION_SPRINT.md`](sprints/PRODUCT_SIMPLIFICATION_SAAS_REDUCTION_SPRINT.md) | Prior sprint inventory (historical) |
