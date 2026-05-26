# PRODUCT_ONLY_SAAS_SKELETON_SPRINT — Sprint Control Note

**Status:** Authority document for this convergence sprint.  
**Supersedes for this scope:** Other sprint notes when they conflict with **product-only boundary** decisions recorded here.  
**North star:** `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` (macro blueprint; this sprint operationalizes a slice of it).

---

## 1. OBJECTIVE

Define and partially implement the future **Product-only SaaS skeleton** for **Unified Intake**: clear boundaries between sellable product surface, lab/platform/R&D surface, deployment profiles, trust/audit/replay authority, and tenant/evolution path—without rewriting the monolith or changing triage semantics.

---

## 2. NON_GOALS

- No full multi-tenant implementation; no Stripe/auth productization in this sprint.
- No giant `triage.py` / resolver rewrites; no mass TSX refactors.
- No new “second brain” abstractions; no speculative DI frameworks.
- No promise that `UNIFIED_INTAKE_PRODUCT_ONLY=1` removes **every** legacy inline route on `app` (see §14 and Iteration Log); shrinking **included routers** is step one.

---

## 3. PRODUCT_DEFINITION

**Product (sellable wedge):** Add-Car-first **Unified Intake**—state-driven intake that turns messy customer input into a **formal service record** and **broker workbench** handoff, with explicit trust copy (no auto-outbound).

**Minimal product UX surface:** `ui` routes under Unified Intake (`UnifiedIntakePage`, Customer Entry, My Requests, Broker Workbench, Scenario Replay).

---

## 4. SYSTEM_MAP

| Layer | Key modules | Role |
|--------|-------------|------|
| HTTP entry | `services/fiqa_api/app_main.py` | FastAPI app, CORS, router mounting, many **inline** lab/API routes |
| Unified Intake API | `services/fiqa_api/routes/inbox_triage.py` | `/api/inbox/*` |
| Triage engine | `services/fiqa_api/inbox_triage/triage.py` | Rules + LLM paths, truth merge |
| Truth reads | `case_truth_repository.py` | DB-primary vs JSON façade |
| Resolver (parallel/test) | `active_vehicle_resolver.py` | Documented; mainline authority in `triage` + PG finalize |
| Sessions | `session_store.py`, `session_repository.py` | Pre-handoff persistence |
| Workbench list enrich | `workbench_enrichment.py` | Lane + PG mirror hints |
| Postgres service record | `db/service_record_repository.py`, `db/service_record_settings.py` | Persistence, flags |
| UI | `ui/src/pages/UnifiedIntakePage.tsx`, `BrokerWorkbenchTab.tsx`, `CustomerEntryTab.tsx`, `api/inboxTriage.ts`, `api/clientConfig.ts` | Product shell |
| Deploy | `services/fiqa_api/Dockerfile.cloudrun`, `scripts/deploy_rag_demo.sh`, `ui/vercel.json` | Cloud Run + static UI |
| Guardrails / replay | `scripts/guardrail_inbox_triage.sh`, `scripts/run_full_regression.py`, scenario JSON | Trust in **repeatable** behavior |

---

## 5. PRODUCT_ONLY_SURFACE

**API (contractual):** Prefix `/api/inbox/*` (triage, cases, client-config, sessions, attachments, wechat simulate, etc.), plus **shared infra** probes: `/health/live`, `/ready`, `/readyz`, `/healthz` (router), `/api/healthz`, `/health`, and **Qdrant health/info** as required by deployed embedding/RAG posture.

**UI:** Vercel app with `VITE_API_BASE_URL` → Cloud Run; workbench rewrite to SPA.

**Analytics (product-adjacent):** `GET /api/analytics/dashboard` — used by Scenario Replay tab (founder/diagnostic); keep on product profile unless we split “pilot UI” vs “customer-only shell” later.

**Optional org scope (Stage-1 tenancy prep):** `POST /api/inbox/triage` accepts header **`X-Org-Id`** (wired via `triage_inbox_http` → core `triage_inbox`); propagated into structured analytics when set.

---

## 6. LAB_VS_PRODUCT_BOUNDARY

| Lab / platform | Examples |
|----------------|----------|
| Code intelligence | `/api/agent/code_lookup`, `/api/codemap/*`, graph/golden-path routes on `app` |
| Multi-vertical agents | mortgage, ecommerce, jobhunter, ops_copilot |
| Experiment / steward / orchestrate | `experiment_router`, `steward_router`, `contract_v1` (`/api/v1/experiment/*`) |
| Ops / metrics / autotuner | `ops_*`, `black_swan`, `metrics`, `autotuner`, `/api/agent/run` unified |
| Debug | `debug_router`, `/debug/*` |
| Search/RAG entry | `search_router`, `query_router` — not on hot Unified Intake path (triage is not wired to `/api/query` in-repo grep) but still **platform** surface |
| Vitals | `health_monitor_router`, UI `/vitals` |

**Env gate:** `UNIFIED_INTAKE_PRODUCT_ONLY=1` mounts **core + inbox + analytics + qdrant health/info**; omits router includes listed in `deployment_profile.py`.

---

## 7. DEPLOYMENT_BOUNDARY

- **Cloud Run:** `services/fiqa_api/Dockerfile.cloudrun` — Python 3.11, `PORT=8080`, `GIT_SHA`, broad COPY of `agents/`, `experiments/`, etc. (platform image today; **product-only** is logical routing + ops env, not a separate slim image in this sprint).
- **Secrets:** `.env.cloudrun` git-ignored; optional Secret Manager via `deploy_rag_demo.sh` — doc’d in `configs/demo.env.example`.
- **UI:** `ui/vercel.json` SPA rewrites; API coupling only via `VITE_API_BASE_URL`.
- **Risk:** Product-only mode does not delete inline `@app.get/post` lab routes on `app_main` (see §14); true slim deploy needs follow-up refactor or route table generator.

---

## 8. TENANT_BOUNDARY

- **Now:** Single-tenant mental model: one deploy / one broker org; `client_id` selects **client pack** under `configs/clients/*`.
- **Future shared multi-tenant:** Reserve **`X-Org-Id`** (optional header) for org-scoped analytics and future row-level policy; no auth binding in this sprint.
- **Isolation risk:** `case_id` and session IDs are globally unique only by convention; future tenancy needs **composite keys** (org_id + id) in DB and APIs.

---

## 9. TRUST_BOUNDARY

| Source | Authority |
|--------|-----------|
| AI / LLM | Assist layer, narrative drafts — **non-authoritative** for structured truth |
| Rules / config packs | `configs/common`, `configs/clients/*`, inbox JSON packs — **declared** authority for copy and routing policy |
| DB truth | When `UNIFIED_INTAKE_DB_PRIMARY_READS` / dual-write flags on — **durable** service record |
| JSON case files | Local/dev and transitional; flagged weak in production without DB |
| Replay truth | Scenario packs + `run_full_regression.py` + guardrail scripts — **regression authority**, not legal audit |

---

## 10. AUTHORITY_BOUNDARY

- **Triage outcome shape:** Owned by `triage.py` + post-process in `inbox_triage.py` routes; **PG finalize** (`_finalize_response_with_pg_truth` family) overwrites client-visible vehicle truth when enabled.
- **Case read path:** `case_truth_repository.get_case_for_read` — single read façade.
- **Writes:** `case_store` / `service_record_repository` per `service_record_settings` flags.
- **Active vehicle:** Declared in `active_vehicle_resolver.py` docstring: mainline resolver path is **not** that module today—avoid double authority when changing vehicle logic.

---

## 11. AUDIT_BOUNDARY

- **Today:** `analytics/minimal_events.track_event` JSON logs; funnel buffer in triage analytics.
- **Gap:** No immutable append-only audit log, no export API for counsel/regulator; no signed replay artifacts.
- **Skeleton:** `inbox_triage/audit_export.py` — stable **function names / contracts** for future WORM store + export (implementation stub only).

---

## 12. CONFIG_PACK_BOUNDARY

- **Common vs client:** `configs/common/*` vs `configs/clients/<client_id>/*`; loader in `inbox_triage/config_loader.py`.
- **Validation:** `inbox_triage/pack_validation.py` — lightweight **existence / shape** checks (extend incrementally); version pinning strategy TBD (see §20 matrix).

---

## 13. ROUTER_SURFACE_MAP

| Prefix / router | Product-only (`UNIFIED_INTAKE_PRODUCT_ONLY=1`) |
|-----------------|-----------------------------------------------|
| `/api/inbox/*` | Yes |
| `/api/analytics/dashboard` | Yes (replay / founder) |
| `/health/*`, `/ready`, `/readyz`, `/api/healthz`, health router | Yes |
| `/api/health/qdrant`, `/api/qdrant/*` | Yes |
| `/api/v1/experiment/*` (contract_v1) | No |
| `/debug`, `/search`, `/api/query`, kv/mortgage/ecommerce/jobhunter/ops_copilot | No |
| `/api/codemap/*`, code_lookup, best | No |
| `/api/experiment`, steward, graph | No |
| `/api/*` ops, black_swan, metrics, lab, labops, autotuner | No |
| `/api/agent/*` (unified lab agent) | No |
| `/api/vitals/*` | No |
| Inline `app` routes `/api/lab/*`, `/api/metrics/mini`, graph, embeddings, etc. | **Still present** until follow-up (see risks) |

---

## 14. SAAS_READINESS_MATRIX

| Dimension | Current | Target (skeleton) |
|-----------|---------|---------------------|
| Router isolation | Monolith includes all routers | Env-gated **router** subset ✅ (this sprint) |
| Inline lab routes | Many on `app` | Documented + untangled ❌ follow-up |
| Tenancy | client_id pack only | `X-Org-Id` hook + DB composite keys ⚠ partial |
| Auth | None productized | Out of scope this sprint |
| Audit | Logging only | Stub `audit_export` ✅ |
| Config validation | Runtime failures | `pack_validation` starter ✅ |
| Deploy image size | Full platform COPY | Product-only **logical** profile first; slim image later |
| Replay trust | Strong scripts | Keep guardrails + regression |

---

## 15. TOP_10_SYSTEM_RISKS

1. **Double authority** on vehicle/active entity between triage heuristics, PG finalize, and resolver module drift.  
2. **JSON vs PG** truth divergence when flags change mid-pilot (`case_truth_repository` merge rules).  
3. **Monolith inline routes** bypass product-only router gate—accidental exposed lab surface.  
4. **CORS / ALLOWED_ORIGINS** drift on deploy (`deploy_rag_demo.sh` warns).  
5. **No org_id** in durable keys—future multi-tenant migration breakage.  
6. **Analytics** as PII channel (session/case in logs) without retention policy.  
7. **Replay** depends on LLM off scenarios; live LLM nondeterminism undermines “replay” marketing if oversold.  
8. **Vercel env** mis-set → wrong API or stale client pack cache.  
9. **Health probes** (`/health/ready` artifact check) tied to experiment route in full profile—product-only uses `/api/inbox` check.  
10. **Scope creep** in AGENTS.md (“out of scope: multi-tenant”) vs this sprint’s **preparation**—must stay documentation + hooks only.

---

## 16. TOP_10_SIMPLIFICATION_OPPORTUNITIES

1. Extract inline `app_main` lab routes behind a single `lab_routes` router or feature flag.  
2. Split Docker image: `Dockerfile.cloudrun.intake` with minimal COPY.  
3. Single **OpenAPI export** for product-only paths (customer-facing doc).  
4. Consolidate duplicate health endpoints documentation for operators.  
5. Move vitals / analytics behind founder auth when auth exists.  
6. Retire unused agent verticals from default `app_main` imports (lazy import).  
7. Client pack schema validation at startup (fail fast).  
8. Explicit **version** header on triage responses (`X-Intake-Contract-Version`).  
9. DB migration runner in deploy playbook for service record schema.  
10. Remove `active_vehicle_resolver` from mental “production path” docs if mainline stays in triage.

---

## 17. TOP_10_PRODUCTIZATION_MOVES

1. Ship **`UNIFIED_INTAKE_PRODUCT_ONLY`** in staging/prod for pilot API.  
2. **Publish product-only OpenAPI** snippet for integrators.  
3. **Onboarding runbook:** one env file + one DB URL + one client pack id.  
4. **Trust copy** already in UI; align API errors with same tone (400/403).  
5. **Case export** JSON endpoint (future) behind org auth.  
6. **Replay bundle** export (scenario id + config hash) for support.  
7. **Git SHA** already in Docker build — surface on `/version` for support.  
8. **Scenario guardrail** as CI gate (already exists—enforce on main).  
9. **Org header** propagation to analytics (this sprint).  
10. **Separate Vercel project** “customer portal” vs “founder console” when ready.

---

## 18. CONVERGENCE_TARGET_SELECTION

**Primary convergence target:** `app_main.py` **router inclusion policy** + **`deployment_profile`** + **`health/ready`** semantics + **telemetry org hook** + **audit/config stubs**.  
**Deferred:** Inline route table, slim Dockerfile, OpenAPI product slice automation.

---

## 19. ITERATION_LOG

| Date | Change |
|------|--------|
| 2026-05-07 | Implemented `deployment_profile`, conditional lab mounts, `health/ready` product check, `audit_export` / `pack_validation`, `triage_inbox` core + `triage_inbox_http` (`X-Org-Id` header). Validations: `compileall`, `pytest tests/test_pack_validation.py`, guardrail PASS, `run_full_regression.py` PASS (`http_p95_ms` 4922 &lt; 6000), UI `npm run build` (Node 22 on PATH via `env PATH=.../v22.../bin:$PATH`), madge no cycles, `test_minimal_analytics` / `test_inline_image` / `test_real_user_simulation` PASS, `test_contract_v1` PASS. |

---

## 20. VALIDATION_MATRIX

| Check | Command | Expected |
|-------|---------|----------|
| Python bytecode | `python3 -m compileall services/fiqa_api` | 0 errors |
| UI build | `cd ui && npm run build` | success |
| Madge | `cd ui && npx --yes madge --circular --extensions ts,tsx src` | no cycles |
| Guardrail | `bash scripts/guardrail_inbox_triage.sh` | PASS |
| Regression | `PYTHONPATH=. python3 scripts/run_full_regression.py` | PASS (per repo caps) |
| Pytest (targeted) | `pytest tests/test_pack_validation.py` (if added) or existing | PASS |

---

## 21. SELF_CRITIQUE_REPORT

- **Complexity:** Reduced **conceptual** complexity via one deploy flag and one doc; code complexity barely changed.  
- **Authority:** Clarified router vs inline route gap honestly—risk remains until inline routes are gated.  
- **SaaS risk:** Single-tenant path clearer; multi-tenant still blocked on auth + DB keys.  
- **Product/lab confusion:** Improved for **included routers**; not for inline handlers.  
- **Onboarding:** `pack_validation` helps catch missing client dirs early—still need runbook cross-link.  
- **Trust/audit:** Stubs only; no immutable store.  
- **Double-brain:** No new second pipeline; resolver doc already warns.  
- **Abstraction noise:** Kept modules tiny and named for future fill-in.

---

## 22. FINAL_DECISION

Adopt **`UNIFIED_INTAKE_PRODUCT_ONLY`** as the **supported** way to run a **reduced API surface** for Unified Intake pilot SaaS; treat full `app_main` as **platform** default for R&D. Plan follow-up sprint for **inline route** separation or middleware denylist.

---

## 23. FINAL_ONE_LINE

**We converged the sellable Unified Intake API behind an explicit deploy flag and documentation, hooked optional org telemetry, and named the audit/config/replay gaps without pretending the monolith’s inline lab routes are already gone.**

---

## PRODUCT_ONLY_SAAS_SKELETON_FINAL_REPORT

### 1. What changed technically

- New: `services/fiqa_api/deployment_profile.py` — product-only detection and documented router policy.  
- `app_main.py`: lab/platform routers mounted only when **not** product-only; `health/ready` route-load check respects profile.  
- New: `audit_export.py`, `pack_validation.py`; HTTP `triage_inbox_http` reads optional `X-Org-Id` and passes `org_id` into core `triage_inbox` (analytics emission).

### 2. What changed architecturally

- **Explicit product vs platform** router grouping at FastAPI include level; documented **inline route** debt.

### 3. What changed operationally

- Operators can set `UNIFIED_INTAKE_PRODUCT_ONLY=1` on Cloud Run for a smaller **included-router** attack/service surface; must still understand inline lab endpoints remain.

### 4. What changed product-wise

- Clearer **boundary narrative** for what “pilot SaaS” means vs full SearchForge platform.

### 5. What SaaS risks were reduced

- Fewer accidental **platform** endpoints when product flag is on; **org** header path for future tenancy.

### 6. What trust risks remain

- No cryptographic audit chain; LLM nondeterminism; JSON fallback paths if misconfigured.

### 7. What still blocks real SaaS

- Auth, billing, true multi-tenant data model, immutable audit export, customer-only UI split, slim production image.

### 8. What should happen next

- Gate or relocate **inline** `app_main` lab routes; add product-only **OpenAPI** slice; startup **pack validation** opt-in env.

### 9. What should NOT happen next

- Large triage/resolver rewrite without replay green; new parallel “platform” intake API.

### 10. What the new product boundary is

- **`/api/inbox/*` + analytics dashboard + standard health/qdrant probes** when `UNIFIED_INTAKE_PRODUCT_ONLY=1`.

### 11. What the new deployment boundary is

- Same Cloud Run container with **env-driven** router set; secrets still via `.env.cloudrun` / Secret Manager.

### 12. What the future tenant strategy is

- **Single-tenant deploy** today; **`X-Org-Id` + composite DB keys** tomorrow.

### 13. What the future product-only architecture is

- **Thin API**: intake + workbench + sessions + client pack + optional founder analytics; everything else behind separate service or disabled flag.

### 14. What the next 10x leverage point is

- **One product-only Docker image + automated OpenAPI contract test** so every merge proves pilot surface compatibility.

### 15. FINAL_ONE_LINE

**Product-only Unified Intake is now an explicit env-flag router profile, not a hope that operators guess which `/api/*` paths are safe.**
