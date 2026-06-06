# FUTURE_SAAS_OPERATING_SYSTEM_SPRINT — Single Source of Truth

**Status:** Authority document for this operating-system sprint (onboarding, operator workflow, trust, tenant lifecycle, deployment convergence).  
**Does not supersede:** `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` (macro product/tech north star) or `docs/sprints/PRODUCT_ONLY_SAAS_SKELETON_SPRINT.md` (product-only boundary detail) — align all three.  
**Last updated:** 2026-05-07  

---

## 1. OBJECTIVE

Design and document the **operating model** of a future SaaS company built on SearchForge’s **Unified Intake** wedge (California auto broker intake → formal service record → workbench handoff), so that **onboarding, operations, trust, replay, tenancy, and deployment** scale without heroic manual work or hidden lab surfaces. Deliver **high-leverage, low-risk** scaffolding (contracts, validation, boundaries, documentation) — not a triage rewrite or feature dump.

---

## 2. NON_GOALS

- No Stripe, billing productization, or entitlement engine in this sprint.
- No full multi-tenant auth or row-level security implementation.
- No large `triage.py` / `active_vehicle_resolver` semantic rewrite (resolver is **not** mainline — see `active_vehicle_resolver.py` docstring and `docs/DEPRECATED_PATHS.md`).
- No mass TSX or demo UI redesign.
- No promise that **`UNIFIED_INTAKE_PRODUCT_ONLY=1`** removes every legacy **inline** route on `app_main.py` (routers are gated; many `@app.get/post` lab endpoints still register — see §13, §21).
- No “perfect” abstraction layers; optimize for **clarity and repeatability**.

---

## 3. PRODUCT_DEFINITION

**Commercial SKU (today):** **Unified Intake** — add-car-first, state-driven intake that converts messy customer text into a **structured service record**, **session continuity** (Postgres when configured), and **broker workbench** presentation, with explicit trust copy (no auto-outbound). **`client_id`** selects a **client pack** under `configs/clients/<id>/`. Optional header **`X-Org-Id`** on `POST /api/inbox/triage` for analytics / future tenancy (no auth binding).

**Adjacent sellable (often bundled in pilot):** Broker-facing **RAG demo** (citations, copy-to-WeChat) — see `docs/STANDARD_SCENARIO_PACKAGE.md` and paid pilot goal; **not** the same code path as triage hot path.

**Not the SKU:** LabOps agents, JobHunter, mortgage/ecommerce verticals, codemap/code intelligence, experiment orchestration — **platform / R&D**.

---

## 4. SYSTEM_MAP

| Layer | Primary modules | Role |
|-------|-----------------|------|
| HTTP entry | `services/fiqa_api/app_main.py` | FastAPI app, CORS, **conditional routers**, many **unconditional inline** lab/API routes |
| Deployment profile | `services/fiqa_api/deployment_profile.py` | `UNIFIED_INTAKE_PRODUCT_ONLY` — router subset + banner |
| Unified Intake API | `services/fiqa_api/routes/inbox_triage.py` | `/api/inbox/*`, org-scoped analytics hooks |
| Triage engine | `inbox_triage/triage.py` | Rules + LLM paths, merge/finalize |
| Truth reads | `inbox_triage/case_truth_repository.py` | DB-primary vs JSON façade, obs logging `UNIFIED_INTAKE_DB_OBS` |
| Sessions | `inbox_triage/session_store.py`, `session_repository.py` | Pre-handoff persistence |
| Postgres | `db/service_record_repository.py`, `db/service_record_settings.py` | Durable service records, flags |
| Resolver (parallel / tests) | `inbox_triage/active_vehicle_resolver.py` | Contract documented; **production path** = triage + PG finalize |
| Workbench | `inbox_triage/workbench_enrichment.py` | Lane + PG mirror hints |
| Config packs | `configs/common/*`, `configs/clients/*`, `inbox_triage/config_loader.py` | Copy, handoff, rules |
| Pack validation | `inbox_triage/pack_validation.py` | Onboarding fail-fast checks |
| Audit stub | `inbox_triage/audit_export.py` | Forward to `track_event`; future export keys |
| Analytics | `analytics/*`, `/api/analytics/dashboard` | Funnel + founder dashboard |
| UI | `ui/` (Vercel), `vercel.json` SPA rewrites | `VITE_API_BASE_URL` → Cloud Run |
| Cloud image | `services/fiqa_api/Dockerfile.cloudrun` | Full platform COPY; logical product-only = env + routes |
| Trust / regression | `scripts/guardrail_inbox_triage.sh`, `scripts/run_full_regression.py`, `configs/inbox_triage_scenarios.json` | Repeatable behavior |

---

## 5. OPERATOR_WORKFLOW_MAP

| Workflow | Primary surfaces | Notes |
|----------|-------------------|--------|
| Environment / deploy | `Dockerfile.cloudrun`, deploy scripts, `.env.cloudrun`, Secret Manager | **Repeatability** risk: broad image, secrets sprawl |
| Client pack publish | `configs/clients/<id>`, `pack_validation`, `config_loader` | **Drift** if files missing — validation extended this sprint |
| Pilot onboarding | Manual email + URL (goal doc); DB URL + flags | **No** self-serve tenant signup |
| Intake monitoring | `/api/analytics/dashboard`, logs, `track_event` | PII / retention policy **gap** |
| Case / workbench | GET cases, workbench enrich, PG mirror fields | **Hydration gaps** logged to `UNIFIED_INTAKE_DB_OBS` |
| Replay / QA | Scenario JSON, guardrail, chaos regression | LLM off in guardrail; live LLM = **nondeterministic** |
| Incident / support | Scripts in `scripts/`, readiness probes | No ticketing integration |

**Friction:** Single founder-operator mental model; multi-step env and flags; inline lab routes in prod profile confuse security review.

---

## 6. CUSTOMER_LIFECYCLE_MAP

1. **Awareness** — demo / pilot pitch (broker).
2. **Trial** — shared URL + WeChat-aligned UX; optional Role C simulation.
3. **Intake** — anonymous/pre-handoff session → case creation → formal submit.
4. **Service** — broker workbench states (status, waiting_on); no productized SLA.
5. **Renewal / expand** — manual (second pilot = new `client_id` + ops duplicate).

**Gap:** No in-product org signup; identity = light binding (WeChat/phone hints), not auth.

---

## 7. ONBOARDING_LIFECYCLE

| Stage | Artifacts | Exit criterion |
|-------|-----------|----------------|
| Repo + env | `.env` / `.env.cloudrun`, `QDRANT_*`, `SERVICE_RECORD_DATABASE_URL` | `health` / `ready` / triage smoke |
| Client pack | `configs/clients/<client_id>` with `ui_copy.json`, `handoff_phrases.json` | `validate_client_pack_layout` clean |
| DB schema | `db/schema/stage1_service_record.sql` | Migrations applied (manual playbook) |
| UI | Vercel project, `VITE_API_BASE_URL` | SPA loads; CORS `ALLOWED_ORIGINS` |
| Validation | `guardrail_inbox_triage.sh`, optional `run_full_regression.py` | PASS before pilot traffic |

**Scalability blocker:** Every new tenant equivalent = manual pack + env + deploy checklist — acceptable for pilot, not for 100 offices without automation.

---

## 8. DEPLOYMENT_LIFECYCLE

1. **Build** — Cloud Build / `Dockerfile.cloudrun` (Python 3.11, fastembed baked, broad COPY).
2. **Configure** — Cloud Run service, secrets, `UNIFIED_INTAKE_PRODUCT_ONLY`, DB URL, Qdrant.
3. **Wire UI** — Vercel env to API base URL.
4. **Probe** — `/health/live`, `/health/ready` (product-only checks `/api/inbox` routes), `/api/healthz`.
5. **Promote** — **manual** today; no staged blue/green contract in repo.

**Simplification target:** Slim image + route manifest; single promotion runbook (future).

---

## 9. TENANT_LIFECYCLE

| Phase | Mechanism | Isolation |
|-------|-----------|-----------|
| Now | Single deploy; `client_id` pack; optional `X-Org-Id` | **Logical** only — `case_id` not namespaced by org |
| Pilot n+1 | New pack + same or forked deploy | Ops discipline |
| Future MT | Composite key `(org_id, record_id)`, auth, RLS | **Migration** required |

---

## 10. TRUST_BOUNDARY

| Source | Authority |
|--------|-----------|
| Rules + config packs | Declared policy for copy, routing, handoff |
| `triage.py` + route post-process | Structured output; **PG finalize** overwrites client-visible vehicle truth when enabled |
| LLM / assist | **Non-authoritative** for immutable facts — narrative only |
| Postgres (when flags on) | Durable service record |
| JSON case files | Dev / transitional; weak in prod without DB |
| Regression scripts | **Behavioral** authority, not legal audit |

---

## 11. AUDIT_BOUNDARY

- **Today:** `minimal_events.track_event`, funnel buffer, `audit_export.record_intake_case_mutation` (stub → `track_event`).
- **Not today:** Immutable WORM log, signed exports, regulator-ready bundle.
- **Contract hint:** `future_export_bundle_keys()` in `audit_export.py`.

---

## 12. REPLAY_BOUNDARY

- **Deterministic replay:** `LLM_GENERATION_ENABLED=0` scenario runs (`run_inbox_triage_scenarios.py` inside guardrail).
- **Live replay:** `run_full_regression.py` + chaos — performance + shape; **LLM variability** if enabled.
- **Marketing risk:** Calling non-script paths “replay” without disclaimers.

---

## 13. PRODUCT_ONLY_SURFACE

**Always mounted (relevant):** `inbox_triage_router` (`/api/inbox/*`), `analytics_dashboard_router`, health/Qdrant routers, core health endpoints.

**Routers omitted when `UNIFIED_INTAKE_PRODUCT_ONLY=1`:** Lab/search/query/metrics ops/experiment/steward/etc. — see `app_main.py` conditional block.

**Critical caveat:** **Inline** routes on `app` (e.g. `/api/lab/report`, `/api/metrics/mini`, `/api/routing/flags`, `/api/embeddings/encode`, `/api/v1/graph/*`, `/tuner/*`, `/api/demo/*`, `/api/v1/agent/chat`, …) are largely **outside** that `if not product_only` block and **still register** in product-only mode unless removed in a follow-up. Operators must not assume router gating alone minimizes attack surface.

---

## 14. ADMIN_SURFACE

- **Founder / operator:** Analytics dashboard API, scenario replay UI paths, deploy logs, `UNIFIED_INTAKE_DB_OBS` signals.
- **No** dedicated admin RBAC or audit UI.

---

## 15. BILLING/METERING_SURFACE

- **None** productized. Pilot: manual invoice (Zelle/Venmo/WeChat).  
- Analytics events are **not** a billable meter — privacy and definition drift risk if used as such.

---

## 16. CONFIG_PACK_LIFECYCLE

- **Layout:** `configs/clients/<client_id>` — required files for onboarding checks: `ui_copy.json`, `handoff_phrases.json` (enforced by `validate_client_pack_layout` after this sprint).
- **Versioning:** No semver pin in API; **drift** risk pack vs deployed `GIT_SHA`.
- **Validation:** Expand incrementally (shape checks) — avoid startup failure in prod until smoke-tested.

---

## 17. INSTANCE_FACTORY_MODEL

**Target:** Provision “one intake instance” per tenant = **deploy slot** + **client pack** + **DB namespace** + **UI env** + **secrets**.  
**Today:** Manual factory; **future:** templated Terraform/Cloud Run module + schema migration job + pack repo path.

---

## 18. SUPPORT_WORKFLOW

1. Reproduce with scenario or `curl` + session id.
2. Check `UNIFIED_INTAKE_DB_OBS` logs and PG mirror fields on workbench.
3. Readiness / embedding issues — `docs/ANDY_QUICK_START.md`, `restore_8001_readiness.sh`.
4. **Gap:** No customer-facing ticket ID linking case ↔ support thread.

---

## 19. ROLE_BOUNDARY_MAP

| Role | Product surface | Must not rely on |
|------|-----------------|------------------|
| Customer (insured) | Intake UI, triage copy | Admin APIs |
| Broker (pilot) | Workbench, drafts | Lab routes |
| Founder / ops | Analytics, scripts, deploy | Undocumented inline APIs |
| Engineer | Full repo | Assuming prod omits lab **inline** routes |

---

## 20. SAAS_READINESS_MATRIX

| Dimension | Current (2026-05-07) | Next hardening |
|-----------|----------------------|----------------|
| Router isolation | Product-only omits lab **routers** | Strip or gate **inline** lab routes |
| Tenancy | `client_id` + optional `X-Org-Id` | Composite DB keys + auth |
| Audit | Logging + stub export keys | WORM + export job |
| Onboarding | Manual + pack validation | Scripted tenant checklist |
| Billing | Manual | Stripe / meter (later) |
| Multi-office | Single workbench mental model | Org hierarchy, assignment |
| Deploy | One Cloud Run + Vercel | Staged promote, slim image |

---

## 21. TOP_20_SCALING_RISKS

1. Inline `app_main` lab routes exposed in product-only mode.  
2. Global `case_id` without `org_id` composite — migration debt.  
3. JSON/PG dual-path confusion under flag churn.  
4. No automated tenant provisioning.  
5. Analytics/PII in logs without retention policy.  
6. CORS / `ALLOWED_ORIGINS` misconfiguration.  
7. Full-platform Docker image — slow deploy, large blast radius.  
8. Qdrant/embedding readiness flapping — support load.  
9. LLM nondeterminism undermines “replay” narrative.  
10. `active_vehicle_resolver` vs triage **double-authority** if someone wires resolver back without PG finalize alignment.  
11. Workbench PG hydration gaps (`PG_LIST_HYDRATION_GAP`).  
12. No per-tenant rate limits / abuse controls.  
13. Secret sprawl across `.env.cloudrun` and Vercel.  
14. Client pack drift vs code version (no API semver).  
15. Session fixation / shared-browser support scenarios unclear.  
16. Single-region deploy — latency + DR gap.  
17. No formal SLO/error budget for triage.  
18. Support tooling disconnected from case IDs.  
19. Manual DB migrations on scale-out.  
20. Founder bottleneck on onboarding checklist execution.  

---

## 22. TOP_20_PRODUCTIZATION_OPPORTUNITIES

1. Gate or remove inline lab routes under product-only.  
2. Slim `Dockerfile.cloudrun.intake` COPY set.  
3. Tenant onboarding runbook as script-driven checklist (exit codes).  
4. OpenAPI export for **product-only** paths only.  
5. `X-Intake-Contract-Version` response header (declared compatibility).  
6. Expand `pack_validation` to schema shape.  
7. Wire `record_intake_case_mutation` at critical case transitions (audit trail seed).  
8. Founder-auth gate on analytics dashboard (when auth exists).  
9. Single-page operator doc: env vars + meanings.  
10. Automated migration runner in deploy.  
11. Staging slot with same flags as prod.  
12. Org-scoped case list API (after schema).  
13. Explicit “lab vs product” in UI footer from deploy metadata.  
14. Customer-facing status page (deps: API, Qdrant).  
15. Pack version field in triage response metadata.  
16. Integration webhooks for CRM (later).  
17. Role-based workbench (manager vs agent) — product design.  
18. Export bundle worker from `audit_export` keys.  
19. Cost meter dashboard (LLM tokens) for pilot transparency.  
20. Self-serve “add office” — future revenue lever.  

---

## 23. TOP_10_OPERATIONAL_FAILURE_MODES

1. **503 ready** — embeddings/Qdrant not ready.  
2. **Wrong API URL in Vercel** — silent UI failure.  
3. **DB URL missing in prod** — session/case persistence silent degradation.  
4. **Flags changed mid-pilot** — PG/JSON mismatch.  
5. **Secret not mounted** on Cloud Run revision.  
6. **Redis assumed local** — lab metrics endpoints brittle.  
7. **Guardrail skipped** — regressions ship.  
8. **Manual schema drift** — insert failures.  
9. **CORS lockout** after domain change.  
10. **On-call = founder** — no runbook rotation.  

---

## 24. TOP_10_TRUST_FAILURE_MODES

1. Customer told “submitted” but case not in DB (write path / flags).  
2. Vehicle shown in UI disagrees with PG truth (finalize order bug).  
3. Broker relies on LLM text as binding policy.  
4. Replay script passes but live LLM path fails customer.  
5. Analytics oversold as compliance audit.  
6. `org_id` header spoofed — no auth (analytics pollution).  
7. Attachment handling error → data loss perception.  
8. Workbench “mirrored” wrong — PG drift.  
9. Scenario pack stale vs code — false confidence.  
10. Product-only **claimed** minimal surface while inline routes exist — **trust with security reviewers**.  

---

## 25. ITERATION_LOG

| Date | Change |
|------|--------|
| 2026-05-07 | Created this SSOT; aligned with repo inspection (`app_main`, inbox triage, case truth, sessions, service records, deployment profile, guardrails, PRODUCT_ONLY sprint, paid pilot goal). |
| 2026-05-07 | Tightened `validate_client_pack_layout` to require `ui_copy.json` and `handoff_phrases.json` under each client pack. |
| 2026-05-07 | Validation matrix executed — see §26 (compileall scoped; guardrail + full regression PASS). |

---

## 26. VALIDATION_MATRIX

| Check | Command | Result (2026-05-07) |
|-------|---------|---------------------|
| Python syntax (scoped) | `python3 -m compileall -q services/fiqa_api services/core` | **PASS** |
| Pack tests | `PYTHONPATH=. pytest tests/test_pack_validation.py -q` | **PASS** (3 tests) |
| UI build | `PATH="$HOME/.nvm/versions/node/v22.22.0/bin:$PATH" cd ui && npm run build` | **PASS** (Vite 7; Node 22 required) |
| Madge (UI cycles) | `cd ui && npx --yes madge --circular --extensions ts,tsx src` | **PASS** (no cycles) |
| Inbox guardrail | `bash scripts/guardrail_inbox_triage.sh` | **PASS** |
| Full regression | `PYTHONPATH=. python3 scripts/run_full_regression.py` | **PASS** (`http_p95_ms` 4946.46 &lt; 6000; assertions passed) |

**Note:** Full-tree `python3 -m compileall -q services scripts` fails on **pre-existing** syntax errors in `services/chaos_injector/app.py` and `scripts/run_demo_pack_original.py` — do not use until those files are fixed; use scoped compile paths for triage-related changes.

**Not run this pass:** API smoke against live server (guardrail **SKIP** — nothing on :8001); optional broader pytest / onboarding scripts.

---

## 27. SELF_CRITIQUE_REPORT

- **SaaS risk reduced?** Partially — documentation and pack validation reduce onboarding variance; **inline route exposure** remains the largest unmitigated gap.  
- **Commercial SKU clarified?** Yes — Unified Intake + optional RAG demo; lab stack explicit.  
- **Onboarding friction?** Reduced via required pack files check; full automation still missing.  
- **Replay ambiguity?** Documented; not eliminated (LLM).  
- **Architecture noise?** Minimal code churn — good.  
- **What still blocks a real SaaS company?** Tenant auth, billing, automated provisioning, honest minimal API surface, multi-office org model.

---

## 28. FINAL_DECISION

**Ship documentation + incremental validation as the wedge.** Prioritize a **follow-up sprint** to **gate or relocate inline `app_main` lab routes** when `UNIFIED_INTAKE_PRODUCT_ONLY=1` — that is the highest-leverage trust + security convergence move after this sprint. Defer billing and multi-tenant DB keys until pilot revenue justifies.

---

## 29. FINAL_ONE_LINE

**Unified Intake is a pilot-grade product with a platform-sized monolith footprint — converge ops by documenting truth boundaries, tightening onboarding checks, and planning inline-route removal before scaling tenants.**

---

## Appendix: Phase 2 — Discovery Answers (A–K)

| ID | Answer |
|----|--------|
| **A. True commercial SKU?** Unified Intake (add-car path → service record → workbench) + broker RAG demo as adjacent; pilot billed manually. |
| **B. Lab/R&D?** LabOps agents, codemap, experiments, steward, jobhunter/mortgage/ecommerce, most inline graph/embedding/tuner endpoints. |
| **C. Future operational debt?** Inline lab routes in prod profile; manual tenant onboarding; no migration runner; analytics as PII sink. |
| **D. Onboarding scalability?** Manual pack + env + deploy; validation previously shallow — improved with required JSON files. |
| **E. Supportability?** No ticket↔case link; readiness/embed flaps; DB flag matrix opaque to brokers. |
| **F. Replay trust?** Strong for rule-based scenarios; weak for live LLM paths; marketing must distinguish. |
| **G. SaaS isolation?** No auth; `org_id` header advisory; case IDs not org-scoped in DB. |
| **H. Multi-office workflows?** No org hierarchy, routing, or RBAC — single workbench assumption. |
| **I. Second paid pilot?** Process/manual duplication, not hard technical wall — **trust + ops checklist** matter more than code. |
| **J. Ten offices?** Need provisioning automation + isolated config + support runbooks + rate limits. |
| **K. 100 offices?** **Multi-tenant data model, auth, billing, regional DR, SRE staffing** — not in current codebase scope. |

---

## Appendix: Phase 3 — Operator Workflows (1–15) — Friction Summary

| # | Workflow | Friction / gaps |
|---|----------|-----------------|
| 1 | Customer intake | Channel fragmentation (WeChat vs web); no auth |
| 2 | Add-car | Complex resolver story — doc clarity needed |
| 3 | Append | `append_allowed` / boundary actions — operator training |
| 4 | Formal submit | **Trust** that DB row matches UI |
| 5 | Replay/review | LLM vs script paths |
| 6 | Case correction | Overwrite chain tests exist — ops playbooks thin |
| 7 | Office handoff | Not productized — manual |
| 8 | Manager review | No RBAC |
| 9 | Support/debug | Founder-dependent |
| 10 | Trust dispute | No export — **audit gap** |
| 11 | Audit/export | Stub only |
| 12 | Config/pack update | File-based; no canary |
| 13 | Deployment/update | Manual promote |
| 14 | Tenant onboarding | Checklist not executable as one command |
| 15 | Pilot expansion | Business + ops, not codegen |

---

## Appendix: Phase 4 — SaaS Skeleton Convergence (bullets)

1. **Topology:** Cloud Run API + Vercel static UI + Qdrant + Postgres.  
2. **Product router surface:** `/api/inbox/*`, `/api/analytics/dashboard`, health/Qdrant.  
3. **Env profile:** `UNIFIED_INTAKE_PRODUCT_ONLY`, DB flags, Qdrant, `ALLOWED_ORIGINS`.  
4. **Minimal runtime:** Triage + persistence + analytics; no lab routers **if** inline routes fixed.  
5. **Onboarding package:** Client pack dir + validated JSON files + DB schema.  
6. **Tenant contract:** `client_id` + optional `X-Org-Id` (analytics until auth).  
7. **Replay truth:** Scenario JSON + guardrail + regression script outputs.  
8. **Audit contract:** `audit_export` keys + future WORM.  
9. **Org/team roles:** Not implemented — design Reserve broker/manager/admin.  
10. **Admin hierarchy:** Founder analytics only.  
11. **Pack validation:** Directory + required files; shape next.  
12. **Config versioning:** Git SHA + manual; API header TBD.  
13. **Promotion:** Manual — target blue/green.  
14. **Instance factory:** Manual **tenant recipe** → automate.  
15. **MT path:** Add `org_id` column + RLS + auth gate.

---

## Appendix: Phase 7 — Deployment / Operations Review

- **Cloud Run:** Single service; `Dockerfile.cloudrun` copies entire platform tree — **large artifact**, long cold paths.  
- **Vercel:** SPA rewrite to `/`; API decoupled — **good**; env mismatch = **critical** risk.  
- **Secrets:** `.env.cloudrun` pattern + optional Secret Manager — document who rotates.  
- **Rollback:** Revision-based — **viable** if `GIT_SHA` tracked.  
- **Isolation:** **Incomplete** without inline route removal + tenancy keys.

---

*End of SSOT*
