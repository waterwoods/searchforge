# STRICT PRODUCT-ONLY WIRE CLOSURE + SUPPORT EXPORT SPRINT

**Control note · route inventory · wire boundary authority · support/replay authority · validation journal · final report**

| Field | Value |
| ----- | ----- |
| Branch | `auto-evolution/product-only-wire-closure-support-export-20260507-0222` |
| Sprint start | 2026-05-07 |
| Primary API entry | `services/fiqa_api/app_main.py` |
| Product-only env | `UNIFIED_INTAKE_PRODUCT_ONLY=1` (truth: `deployment_profile.is_unified_intake_product_only`) |
| Platform inline module | `services/fiqa_api/platform_inline_routes.py` |

---

## PHASE 0 — Git + SSOT hygiene (at sprint start)

### Pre-sprint git snapshot (recorded)

Worktree on prior branch `auto-evolution/real-saas-boundary-operator-system-20260507-0203` had **unrelated WIP** (triage persistence, resolver, UI contract edits, trial scripts, many untracked `docs/sprints/*` and `results/*`). This sprint branch was cut from that HEAD intentionally to keep momentum; **those files are not required deliverables of this sprint** unless listed under “changed files” in the final summary.

### SSOT

This document is the **single authoritative** sprint note for wire closure + support export for Unified Intake.

---

## PHASE 1 — FULL_ROUTE_INVENTORY (reality: `app_main` FastAPI)

### `include_router` surfaces (always mounted, all profiles)

| Router module | Prefix / notes |
| ------------- | -------------- |
| `health.ready` | `/readyz`, `/healthz` (duplicate name with inline — see leaks note) |
| `routes.health` (qdrant) | `/api/health/qdrant` |
| `routes.qdrant_info` | `/api/qdrant/version.tag` |
| `routes.inbox_triage` | `/api/inbox/*` |
| `routes.analytics_dashboard` | `/api/analytics/dashboard` |

### Inline `@app` routes (`app_main`, not from `APIRouter`)

| Path | Product-only | Notes |
| ---- | ------------ | ----- |
| `GET /version` | Yes | Git SHA |
| `GET /healthz` | Yes | Duplicate path also on `health_router` |
| `GET /` | Yes | **Product-only: honest reduced JSON** (no platform catalog) |
| `GET /health/live` | Yes | |
| `GET /api/healthz` | Yes | Cloud Run liveness alias |
| `GET /health/ready` | Yes | Checks `/api/inbox` routes when product-only |
| `GET /health` | Yes | Includes `deployment_profile` block |
| `GET /ready` | Yes | Vector/embed readiness |
| `GET /{full_path:path}` | If `frontend/dist` exists | SPA fallback; excludes `api/`, `health/`, etc. |
| `mount /reports` | If dir exists | Static reports |
| `mount /assets` | If SPA exists | Static |

### `include_router` when **not** product-only (`if not is_unified_intake_product_only()`)

`debug`, `search`, `contract_v1`, `query`, `kv_experiment`, `mortgage_agent`, `ops_copilot`, `ecommerce_agent`, `jobhunter`, `health_monitor`, `code_lookup`, `code_graph`, `best`, `experiment` (×2 prefix), `steward`, optional `graph_router`, `ops`, `ops_control`, `black_swan`, `metrics` (×2), `fiqa_metrics`, `quiet_experiment`, `ops_lab`, `labops`, `autotuner`, plus inline `POST/GET /api/agent/*` (v2/v3).

### Platform inline routes (moved to `platform_inline_routes.register_platform_inline_routes`)

Registered **only** when **not** product-only:

`GET /obs/ping`, `GET /api/lab/report`, `GET /api/metrics/mini`, `POST /api/lab/snapshot`, `POST /api/routing/flags`, `GET /api/routing/status`, `GET /api/graph/mermaid`, `POST /api/embeddings/encode`, `GET/POST /tuner/*`, `POST /api/demo/generate-traffic`, `POST /api/lab/prewarm`, graph golden-path/stats/stream-search, intelligence summary, analyze-node SSE, `POST /api/v1/agent/chat`.

---

## PRODUCT_ROUTE_INVENTORY

Intended **sellable** Unified Intake wire: `/api/inbox/*`, `/api/analytics/dashboard`, health/version endpoints above, Qdrant health/version tags, SPA static when deployed.

New **support** wire (this sprint): `GET /api/inbox/support/deployment-manifest`, `GET /api/inbox/support/case-head/{case_id}`.

---

## PLATFORM_ROUTE_INVENTORY

Everything in “not product-only” router block + entire `platform_inline_routes` module + deprecated `/ops/*` → 410 middleware.

---

## INLINE_ROUTE_LEAK_MAP (before → after)

| Before | After |
| ------ | ----- |
| 18 documented “ungated” inline lab/graph/tuner paths still live with `UNIFIED_INTAKE_PRODUCT_ONLY=1` | **0** — handlers moved behind `register_platform_inline_routes` |
| `GET /` advertised autotuner, black_swan, etc. under product-only | **Honest** product-only root payload |

---

## PRODUCT_ONLY_HONESTY_MATRIX (abbrev.)

| Scenario | Risk (pre) | Mitigation (post) |
| -------- | ---------- | ----------------- |
| Enterprise asks for API catalog | Root listed non-mounted routes | Product-only `/` lists only mounted surfaces |
| Security scan hits `/api/lab/report` | 200 in product-only | **404 / not mounted** |
| Support needs SHA + persistence mode | Scattered env inspection | `GET /api/inbox/support/deployment-manifest` |
| Replay needs case metadata without dump | Full case = PII-heavy | `GET /api/inbox/support/case-head/{id}` (no bodies) |

---

## SUPPORT_REPLAY_ROUTE_MAP

| Need | Route | PII |
| ---- | ----- | --- |
| Build / profile | `/version`, `support/deployment-manifest` | No |
| Wrong-vehicle context | `GET /api/inbox/cases/{id}` (full — existing) | Yes |
| Escalation head | `support/case-head/{id}` | Minimal metadata only |
| Founder funnel | `GET /api/analytics/dashboard` | Aggregated |

---

## OPERATOR_BOUNDARY_MAP

| Actor | Can observe |
| ----- | ----------- |
| L1 | Health, manifest, case-head, public inbox docs |
| L2 | Full case GET, session GET, triage replay via existing APIs |
| Founder | Platform routers + lab inline when profile off |

---

## PHASE 2 — Failure catalogs (simulation-derived)

### TOP_50_PRODUCT_ONLY_FAILURES (representative 12; full 50 reserved for backlog grooming)

1. Root JSON lying about mounted routes  
2. Lab report exposed under “product-only”  
3. Embeddings encode exposed  
4. Graph SSE stream exposed  
5. Routing flag mutation exposed  
6. Langfuse obs ping exposed  
7. Demo traffic generator path exposed  
8. Tuner stubs on wire  
9. `/healthz` duplicated across router + inline  
10. SPA catch-all ordering surprises  
11. `/reports` static in regulated tenants (policy)  
12. Analytics dashboard unauthenticated (founder-only in practice)  
… *(38 more: auth gap, tenant gap, rate limits, OpenAPI drift, staging parity, … — documented for follow-on)*  

### TOP_30_SUPPORT_EXPORT_FAILURES (representative 6)

1. No single manifest JSON for tickets  
2. No contract version on wire  
3. Case export = full PII dump or nothing  
4. No “why AI said this” chain ID  
5. No signed export bundle  
6. Founder-only DB/psql reads  
…  

### TOP_20_REPLAY_TRUST_FAILURES (representative 5)

1. No immutable turn ledger export  
2. No WORM storage  
3. LLM prompt not bundled  
4. Session/case ID linkage undocumented in export  
5. Redaction policy undefined  
…  

### TOP_20_OPERATOR_FAILURES (representative 5)

1. Two health endpoints for same name  
2. Cloud Run `/healthz` edge case  
3. Product vs staging OpenAPI not diffed in CI  
4. Graph engine init although product-only  
5. CORS `*` in dev leaking to prod config mistakes  
…  

### DEPLOYMENT_HONESTY_REVIEW

`UNIFIED_INTAKE_PRODUCT_ONLY` now matches **router + inline** reality for lab/graph/tuner. Remaining honesty gaps: duplicate `/healthz`, optional `graph_engine` load on import for product-only, analytics without auth.

---

## PHASE 3 — SUPPORT / REPLAY / EXPORT discovery

### SUPPORT_ESCALATION_MAP

Incident → `/health` + `support/deployment-manifest` → `case-head` or full `cases/{id}` → founder if platform-only regression.

### REPLAY_GAP_MATRIX

| Gap | Status |
| --- | ------ |
| Turn-level signed export | Not built |
| Prompt capture | Not built |
| Manifest w/ SHA | **Done** (manifest route) |

### SUPPORT_EXPORT_GAP_MATRIX

| Gap | Status |
| --- | ------ |
| Stable manifest version key | **Done** (`support_export_manifest_v1`) |
| Redaction policy | Partial (case-head) |

### TRUST_EVIDENCE_CHAIN_MAP

`track_event` / funnel buffer → no WORM; `audit_export.record_intake_case_mutation` scaffold only.

### FOUNDER_DEPENDENCY_MATRIX_V2

Platform routes, Postgres forensics, Langfuse, graph still founder-leaning.

---

## PHASE 4 — CONvergence plans (single truths)

### PRODUCT_ONLY_WIRE_AUTHORITY

- **Env:** `UNIFIED_INTAKE_PRODUCT_ONLY`
- **Code:** `deployment_profile.is_unified_intake_product_only()` gates `include_router` batch + **calls** `register_platform_inline_routes` only when false.
- **SSOT doc:** this file.

### SUPPORT_EXPORT_CONTRACT_V1

- **Version:** `support_export_manifest_version: support_export_v1`
- **Manifest:** `GET /api/inbox/support/deployment-manifest`
- **Case head:** `GET /api/inbox/support/case-head/{case_id}`

### REPLAY_CONTRACT_V1

*Deferred* — use existing `GET /api/inbox/cases/{id}` + session APIs; document redaction in runbooks.

### OPERATOR_WORKFLOW_CONVERGENCE

1. Probe `/health/live`  
2. Pull manifest  
3. Pull case-head or full case  
4. Compare `git.commit` across environments  

### DEPLOYMENT_BOUNDARY_CONVERGENCE_PLAN

1. Optional lazy graph engine init in product-only (future)  
2. Deduplicate `/healthz` (future)  
3. CI OpenAPI diff product vs full (future)  

---

## PHASE 5 — Implemented (this sprint)

- Extract platform inline routes → `platform_inline_routes.py`; call only when not product-only.  
- Empty `PLATFORM_INLINE_ROUTES_UNGATED_IN_APP_MAIN`; banner logs **info** when zero leaks.  
- Product-only honest `GET /`.  
- Support routes: `support/deployment-manifest`, `support/case-head/{case_id}`.  
- Shared `json_safe_utils.json_safe` for platform graph SSE payloads.  
- Removed dead imports (`obs`, golden_path, etc.) from `app_main` where unused.

---

## PHASE 6 — Validation log

| Check | Result |
| ----- | ------ |
| `python3 -m compileall` (`services/fiqa_api`) | OK |
| `pytest tests/test_deployment_profile.py` | OK |
| `bash scripts/guardrail_inbox_triage.sh` | PASS |
| `cd ui && npx --yes madge --circular --extensions ts,tsx src` | No cycles |
| `npm run build` (ui) | **Skipped here:** host Node 20.18.2; Vite 7 requires **≥20.19** (use Node 22 on `PATH` per prior sprint runbooks) |
| `PYTHONPATH=. python3 scripts/run_full_regression.py` | PASS (`http_p95_ms` 5870.54 &lt; 6000; `wrong_vehicle_related` 0) |
| Product-only smoke (`UNIFIED_INTAKE_PRODUCT_ONLY=1`) | `GET /api/lab/report` → **404**; `GET /api/inbox/support/deployment-manifest` → **200**; `GET /` → Unified Intake honest root |

---

## PHASE 7 — Walkthrough notes

### SUPPORT_READINESS_REVIEW

L1 can collect manifest + case-head for tickets; PII minimization honored on case-head.

### REPLAY_READINESS_REVIEW

Full replay still needs case + session endpoints; export bundle v2 TBD.

### DEPLOYMENT_HONESTY_REVIEW_V2

Inline lab leak count **0**; profile matches wire for moved routes.

### OPERATOR_SCALING_REVIEW

Manifest JSON reduces founder dependency for SHA/profile.

### SELF_CRITIQUE_REPORT

Graph engine still loads at import; duplicate `/healthz`; no auth on support routes (same as rest of inbox — **tenant zero** product).

---

## STRICT_PRODUCT_ONLY_WIRE_CLOSURE_SUPPORT_EXPORT_FINAL_REPORT

1. **Discovered** — 18+ unguarded inline platform routes under product-only + dishonest `/`.  
2. **Wire leaks** — lab/graph/tuner/demo/embeddings/obs/ping.  
3. **Implemented** — platform extract, honest root, support manifest + case-head, deployment_profile banner update.  
4. **Support/export gaps** — signed bundle, redaction policy, WORM.  
5. **Replay gaps** — prompt/turn export, evidence chain.  
6. **Founder dependencies** — DB digging, platform profile, Langfuse.  
7. **SaaS honesty** — product-only wire matches mount set for lab/graph block.  
8. **Operator scalability** — manifest endpoint.  
9. **Biggest remaining SaaS blocker** — **no tenant/auth** on customer-facing + support surfaces.  
10. **Next 10x leverage** — **auth + tenant boundary** + CI OpenAPI product profile diff.

---

### Appendix: quick grep anchors

- Product gate: `is_unified_intake_product_only` in `app_main.py`  
- Platform routes: `platform_inline_routes.register_platform_inline_routes`  
- Support: `/api/inbox/support/` in `routes/inbox_triage.py`  
