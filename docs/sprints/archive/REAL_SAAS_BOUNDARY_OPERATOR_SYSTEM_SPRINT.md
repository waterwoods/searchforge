# REAL SAAS BOUNDARY + OPERATOR SYSTEM SPRINT

**Branch:** `auto-evolution/real-saas-boundary-operator-system-20260507-0203`  
**SSOT role:** control note, execution journal, authority map, operator/support/deployment/trust reviews, converged readiness narrative, final report shell.  
**Principle:** Honesty > features. Operability > cleverness. Boundaries > sprawl.

---

## PHASE 0 — GIT + SPRINT AUTHORITY

### 0.1 Pre-sprint snapshot (do not silently absorb)

**Recorded:** 2026-05-07 ~02:03 (repo America/Los_Angeles workspace). Parent branch before checkout: `auto-evolution/100-offices-operational-chaos-20260507`.

| Class | Paths |
|--------|--------|
| **Tracked dirty (pre-sprint)** | `configs/demo.env.example`, `scripts/trial_readiness_check.sh`, `services/fiqa_api/app_main.py`, `services/fiqa_api/db/service_record_repository.py`, `services/fiqa_api/inbox_triage/active_vehicle_resolver.py`, `case_lifecycle.py`, `case_truth_repository.py`, `session_repository.py`, `session_store.py`, `routes/inbox_triage.py`, `tests/test_case_truth_repository.py`, `tests/test_intake_session_persistence.py`, `ui/src/api/inboxTriage.ts`, `triageResultContract.ts`, `caseLifecycleDisplay.ts`, `intakePure.ts` |
| **Untracked (pre-sprint; not auto-owned by this sprint)** | Many `docs/sprints/*`, `results/*`, `scripts/ci_smoke.sh`, `run_full_regression.py`, `deployment_profile.py`, `audit_export.py`, `pack_validation.py`, `structured_turn_obs.py`, `test_deployment_profile.py`, `test_pack_validation.py`, etc. |

**Sprint-owned changes (this execution):** SSOT doc; `/health` `deployment_profile` block (if not already present in WIP); `tests/test_deployment_profile.py` operator probe test; `deployment_profile.py` banner SSOT pointer.

### 0.2 Authority

- **Product boundary SSOT:** `UNIFIED_INTAKE_PRODUCT_ONLY` + `services/fiqa_api/deployment_profile.py` + gated `include_router` block in `app_main.py`.
- **Honesty caveat (explicit):** “Product-only” still registers **18** inline `@app` routes on `app` (lab, routing, embeddings, tuner, demo traffic, graph, agent chat). Enumerated in `PLATFORM_INLINE_ROUTES_UNGATED_IN_APP_MAIN`.
- **Replay/export authority (current):** Case/session truth in PG + in-memory funnel (`audit_export.py` stubs → `track_event` only; no WORM).

---

## PHASE 1 — SYSTEM REALITY_MAP

### 1.SYSTEM_REALITY_MAP

| Layer | Reality |
|--------|--------|
| **Runtime** | FastAPI `app_main.py`; default port 8000 env `PORT`/`MAIN_PORT`; demo scripts often 8001. |
| **Persistence** | Case/session persistence mode reported via `unified_intake_case_persistence_report()` on `/health`. |
| **Intelligence** | Unified Intake triage in `inbox_triage/`; vector/embed health tied to `EMBED_READY` / Qdrant. |
| **Analytics** | In-process funnel buffer + `GET /api/analytics/dashboard`; `track_event` / minimal events. |
| **Scope (AGENTS.md)** | Explicit **out of scope:** Stripe, auth, multi-tenant — **tenancy is aspirational, not shipped as SaaS isolation.** |

### 2.PRODUCT_SURFACE_MAP (sellable Unified Intake)

| Surface | Route / artifact |
|---------|------------------|
| **Core triage** | `POST /api/inbox/triage` |
| **Cases** | `GET/POST /api/inbox/cases*`, append, notes, attachments |
| **Session** | `GET /api/inbox/session/{session_id}` |
| **Client config** | `GET /api/inbox/client-config`, add-car rules, scenario center |
| **WeChat binding** | `/api/inbox/wechat/binding/*` |
| **Role-C sim** | `POST /api/inbox/simulation-role-c-customer` |
| **Founder analytics** | `GET /api/analytics/dashboard` |
| **Health** | `/health`, `/ready`, `/health/live`, `/health/ready`, `/api/healthz`, `/healthz`, `health_router` |

**Org hinting:** `X-Org-Id` on triage → metadata on analytics events (not row-level RLS).

### 3.PLATFORM_SURFACE_MAP (non — product-only when flag off)

Routers behind `if not is_unified_intake_product_only()`: search, contract, query, kv experiment, vertical agents, code lookup/graph, steward, ops, metrics, lab, autotuner, unified `/api/agent/*` inline block, etc.

**Always mounted even in product-only:** inbox + analytics + `qdrant_*` + **inline lab/platform paths** (see `deployment_profile`).

### 4.DEPLOYMENT_BOUNDARY_MAP

| Boundary | Mechanism | Honesty grade |
|----------|-----------|---------------|
| **Router strip** | `UNIFIED_INTAKE_PRODUCT_ONLY=1` | **Partial** — removes most routers, not inline routes |
| **Readiness** | `/health/ready` checks `/api/inbox` routes when product-only | **Good** for “inbox loaded” |
| **Observability** | Langfuse `/obs/ping` still live in product-only | **Leak** |
| **Cloud health** | `/api/healthz` documented for Cloud Run front door | **Good** |

### 5.OPERATOR_SYSTEM_MAP

| Workflow | Today |
|----------|--------|
| **Demo / trial** | `run_demo_local.sh`, `trial_readiness_check.sh`, `guardrail_inbox_triage.sh`, `run_full_regression.py` |
| **Config** | `configs/clients/{client_id}` packs; `pack_validation.validate_client_pack_layout` |
| **Profile truth** | Log banner at startup; **`GET /health` → `deployment_profile`** (this sprint) |
| **Founder analytics** | Dashboard route + JSON export via API only |

### 6.SUPPORT_SYSTEM_MAP

| Need | Gap |
|------|-----|
| **Tenant-safe replay** | No per-tenant admin UI; support would use DB + logs |
| **Signed export** | `future_export_bundle_keys()` documented; **no signed bundle** |
| **“Why AI said X”** | Turn-level provenance incomplete for external audit narrative |

### 7.REPLAY_EXPORT_MAP

| Asset | Location |
|-------|----------|
| **Case read APIs** | `GET /api/inbox/cases/{id}`, attachments |
| **Session** | `GET /api/inbox/session/{session_id}` |
| **Triage stub** | `case_truth_repository` / cache scopes |
| **Audit hook** | `record_intake_case_mutation` → `track_event` |
| **Regression replay** | `llm_chaos_live_triage_check.py` + `FULL_REGRESSION.json` |

### 8.Onboarding (actual)

- Client pack files under `configs/clients/{id}` (`ui_copy.json`, `handoff_phrases.json` required by `pack_validation`).
- Env templates: `configs/demo.env.example` (and related runbooks in `docs/`).

### 9.TENANT_ASSUMPTION_MAP

| Assumption | Truth |
|------------|--------|
| **org_id** | Optional header for analytics metadata only |
| **Data isolation** | **Single-DB / founder-operated** — no tenant RLS |
| **Billing** | **None** |
| **AuthZ** | **None** on inbox routes |

### 10.TRUST_BOUNDARY_MAP

| Trust claim | Enforced by |
|-------------|-------------|
| **Product-only deploy** | Env + routers; **undermined** by 18 inline routes unless gated later |
| **Immutability** | **Not** — no WORM store |
| **PII / redaction** | Partially in triage paths; export contract not implemented |

---

## PHASE 2 — FAILURE SIMULATION (condensed codex)

### TOP_100_OPERATIONAL_FAILURE_MODES (indexed themes × depth)

**A. Support & humans (1–20):** ticket without case_id; wrong office pack; language mismatch; attachment malware; trainee deletes thread; shift handoff; VPN blocks WeChat callback; PDF only intake; customer refuses session id.

**B. Wrong truth / vehicle (21–35):** resolver picks wrong VIN year; dual policies; stale session binding; case merge bug; re-open closed case; duplicate FNOL; OCR garbage; bilingual plate confusion.

**C. Onboarding & config (36–50):** missing `handoff_phrases.json`; wrong `client_id` in prod; pack drift vs code; feature flag mismatch; demo env in prod; `UNIFIED_INTAKE_PRODUCT_ONLY=0` accidental; Qdrant down blocks `/ready`.

**D. Tenancy & data (51–65):** two brokers see same row; org_id spoof; no delete story; export has PII; cross-customer leak in analytics buffer; “test client” in prod data.

**E. Replay & audit (66–80):** cannot reconstruct prompt; model version not pinned in export; LLM non-determinism; missing turn in PG; support reproduces different outcome; clock skew.

**F. Deploy & reliability (81–95):** partial rollback; inline lab route abused in prod DDoS; embedding warmup stall; chaos test passes but broker path fails; asset 404 on UI; Cloud Run `/healthz` confusion.

**G. Commercial & founder (96–100):** billing dispute without metering; founder-only keys; no on-call; SLA undefined; enterprise DPA not met.

### TOP_50_SUPPORT_FAILURES

Support cannot prove state (10); no role-based admin (5); logs scattered (5); no runbook for “append_blocked” (5); WeChat opaque to L1 (5); attachment access audit weak (5); duplicate cases (5); language (5); **product-only lie** — supports sees lab routes (5).

### TOP_30_TRUST_FAILURES

No cryptographic export; no model lineage in API; “AI said” without retrieval snapshot; lab telemetry mixed with prod; **deployment_profile leak count > 0** without customer communication; data retention undefined; impersonation; no break-glass audit.

### TOP_30_TENANCY_FAILURES

No auth; shared DB; org_id cosmetic; no per-tenant rate limit; no key rotation per office; founder sees all; **AGENTS.md declares multi-tenant out of scope** vs pilot expectations.

### TOP_20_DEPLOYMENT_HONESTY_FAILURES

Product-only with `/api/v1/agent/chat`; `/obs/ping` in prod intake; lab report reachable; demo traffic endpoint; tuner toggles; **customers told “locked down” but 18 paths exist**; health says ready while persistence wrong mode; dual ports 8000/8001 confusion.

---

## PHASE 3 — ROOT CAUSE / MATRICES

### FOUNDER_DEPENDENCY_MATRIX

| Area | Founder as infra |
|------|------------------|
| Pack edits | File PR / SSH |
| Profile truth | Env + logs (improving: `/health`) |
| Support deep dives | DB + code literacy |
| Trial gating | Manual checklist scripts |
| Tenant isolation | **Manual discipline** |

### SUPPORT_SCALING_MATRIX

| Factor | Scales? |
|--------|---------|
| L1 playbook | **No** — too many edge flags |
| Replay package | **No** |
| Self-serve audit | **No** |
| Dashboard | **Partial** — in-memory only |

### TENANT_BOUNDARY_GAPS

No RLS; no org provisioning API; **X-Org-Id** is analytics tag only.

### REPLAY_TRUST_GAPS

Structured turn obs partial (`structured_turn_obs.py` untracked WIP); no signed bundles; chaos replay ≠ legal replay.

### DEPLOYMENT_HONESTY_GAPS

Inline routes; `/health` previously silent on profile (**now includes `deployment_profile`**).

### PRODUCT_BOUNDARY_VIOLATIONS

**Product-only mode** still exposes graph, embeddings, agent chat, lab — documented in `deployment_profile` (honest documentation); **gating still TODO** for strict SaaS.

---

## PHASE 4 — CONVERGENCE PLAN

### REAL_SAAS_AUTHORITY_MAP

1. **Deploy truth:** `deployment_profile` module + `/health.deployment_profile` + startup banner.  
2. **Replay authority:** case/session APIs + future signed export contract (`audit_export.future_export_bundle_keys`).  
3. **Support flow:** runbook: triage → case id → `GET cases` → attach regression JSON if bug.  
4. **Onboarding:** `validate_client_pack_layout` + trial scripts.  
5. **Tenant story (target):** auth + RLS + org provisioning (not done).  
6. **Trust narrative:** “We log mutations to `track_event` today; WORM/export is roadmap.”

### OPERATOR_WORKFLOW_CONVERGENCE_PLAN

- Single checklist: guardrail → trial_readiness → full_regression before pilot.  
- Single health JSON for operators (`/health`).

### SUPPORT_REPLAY_CONVERGENCE_PLAN

- Standard support bundle fields from `future_export_bundle_keys` + case JSON + `git_sha` from deploy.

### PRODUCT_ONLY_BOUNDARY_PLAN

- Phase next: wrap inline `@app` handlers in `if not is_unified_intake_product_only()` **or** move to gated router (needs blast-radius review).

### TENANCY_FOUNDATION_PLAN

- Introduce real auth; map org → client_id; PG RLS; retire cosmetic header-only org.

### DEPLOYMENT_PROFILE_CONVERGENCE_PLAN

- CI assert: tuple length + `/health` includes profile (test added).  
- Optional: fail deploy if product-only + leak count > 0 (too strict for now).

---

## PHASE 5 — IMPLEMENTATION LOG (high-ROI, low-risk)

| Date | Change | Rationale |
|------|--------|-----------|
| 2026-05-07 | `GET /health` includes `deployment_profile`: `unified_intake_product_only`, `platform_inline_route_leak_count` | Operators/support see **same truth** as logs without SSH |
| 2026-05-07 | `test_health_exposes_deployment_profile_operational_truth` | Regression-safe contract |
| 2026-05-07 | Banner SSOT pointer → this doc | Single sprint authority |

*(Pre-existing WIP on branch: inbox persistence, resolver, UI contracts — **not authored by this sprint slice**; see Phase 0 table.)*

---

## PHASE 6 — VALIDATION LOG

| Check | Command | Result |
|-------|---------|--------|
| compileall | `python3 -m compileall -q services/fiqa_api tests` | **PASS** |
| pytest (profile + pack) | `PYTHONPATH=. pytest tests/test_deployment_profile.py tests/test_pack_validation.py -q` | **PASS** (7 tests) |
| pytest (replay-adjacent) | `pytest tests/test_intake_session_persistence.py tests/test_case_truth_repository.py -q` | **PASS** (1 skip) |
| UI build | `cd ui && PATH=/home/andy/.nvm/versions/node/v22.22.0/bin:$PATH npm run build` | **PASS** |
| madge | `cd ui && npx --yes madge --circular --extensions ts,tsx src` | **PASS** (no cycles) |
| guardrail | `bash scripts/guardrail_inbox_triage.sh` | **PASS** |
| full regression | `PYTHONPATH=. python3 scripts/run_full_regression.py` | **PASS** — `http_p95_ms` **4514** < 6000; `wrong_vehicle_related` **0**; `pg_mismatch_turns` **0** |

**Loop 2 (repeat):** compileall + pytest profile/pack + persistence/case_truth — **PASS** after full_regression (no code changes between loops).

---

## PHASE 7 — OPERATOR + CEO REVIEW (condensed)

### SELF_CRITIQUE_REPORT_V4

- **30 offices:** survivable only with **heavy founder support** and shared DB discipline.  
- **100 offices:** **support + replay + tenancy** collapse without automation.  
- **Support collapse:** no packaged replay; lab/product confusion.  
- **Replay collapse:** non-deterministic LLM + incomplete turn capture.  
- **Onboarding collapse:** filesystem packs + no self-serve org.  
- **Founder bottleneck:** every boundary decision.  
- **Pilot pretending SaaS:** product-only **documentation** now honest; **mechanics** still leak routes.  
- **Enterprise fear:** no RLS, no DPA-grade export, “AI” without lineage.  
- **MRR block:** no billing, no isolation, no SSO.

---

## REAL_SAAS_READINESS_SCORECARD (honest 0–5)

| Dimension | Score | Note |
|-----------|-------|------|
| Deploy honesty | **3** | Documented leaks + `/health` truth |
| Replay | **2** | API read paths only |
| Supportability | **2** | Scripts exist; no L1 bundle |
| Tenancy | **1** | Header metadata only |
| Audit | **1** | Events only |
| Operator scale | **2** | Regression + guardrails |

---

## PHASE 8 — REAL_SAAS_BOUNDARY_OPERATOR_SYSTEM_FINAL_REPORT

1. **Discovered:** Product-only is **partial**; inbox + analytics are real; platform is **large**; inline routes are the **honesty gap**.  
2. **Implemented:** `/health` deployment profile payload + test + SSOT.  
3. **Clearer truth:** Operators can query profile without log grep.  
4. **SaaS gaps:** auth, RLS, billing, export.  
5. **Support gaps:** replay bundle, L1 runbooks.  
6. **Tenancy gaps:** org_id non-enforcing.  
7. **Replay/export gaps:** no signed export; chaos ≠ compliance replay.  
8. **Deploy honesty gaps:** 18 inline routes in product-only.  
9. **Founder bottlenecks:** pack + env + support escalation.  
10. **Next 10x:** **Gate or relocate inline platform routes** under product-only + **minimum support export JSON** (case + sha + contract version).

---

## EXECUTION JOURNAL (append-only)

| Timestamp | Note |
|-----------|------|
| 2026-05-07 | Branch created; Phase 0 baseline recorded; Phases 1–8 drafted; `/health` `deployment_profile` + `test_health_exposes_*`; Phase 6 double-loop green (guardrail + full_regression + UI). |
