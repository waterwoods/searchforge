# Operational SaaS Hardening Sprint — SSOT

**Title:** Operational SaaS Hardening Sprint: Support Key + Deploy Truth + Org Ownership Foundation  
**Authority:** This file is the **single source of truth** for this sprint.  
**Date:** 2026-05-08  

---

## Objective

Strengthen the **minimal real** operational SaaS foundation required before ~30 paying offices, real support load, deployment chaos, founder absence, and repeated onboarding—by making three truths explicit and survivable:

1. **Support truth** — what support can fetch, under what auth, with what lineage, without PII theater.
2. **Deployment truth** — what code, profile, persistence mode, and env hints are actually running.
3. **Org ownership truth** — honest posture that **`X-Org-Id` and `client_id` are not IAM**, until server-issued tenant exists.

---

## Non-goals

- More AI features, prompt work, new verticals  
- RBAC dashboards, enterprise IAM theater, fake multi-tenant marketing  
- Rewriting triage or speculative platform abstractions  
- True tenancy, RLS, compliance programs, SSO, billing  

---

## Current architecture truth

- **Single FastAPI app** (`services/fiqa_api/app_main.py`): Unified Intake routers always mounted (`inbox_triage`, analytics); platform routers and `register_platform_inline_routes` only when **`UNIFIED_INTAKE_PRODUCT_ONLY` is off**.
- **Health:** `GET /health` returns persistence report, deployment profile (schema epoch, product-only flag, auth posture, tenant truth, **operator_runtime_hints**), phase.
- **Readiness:** `GET /ready` tied to embedding/Qdrant unless `DEMO_MODE` relaxes intake path (`health/ready.py`).
- **Support surface:** `GET /api/inbox/support/deployment-manifest`, `GET /api/inbox/support/case-head/{case_id}` — optional shared secret (`UNIFIED_INTAKE_SUPPORT_API_KEY`).
- **Identity:** `IntakeClientAssertionMiddleware` stores **`X-Org-Id`** on `request.state`; `tenant_id_authoritative` is always `None` until a future auth model issues it.

---

## Current support truth

| Mechanism | Actual behavior |
|-----------|------------------|
| Support routes | Gated **only** if `UNIFIED_INTAKE_SUPPORT_API_KEY` set; else **anonymous_ok** (documented). |
| Headers | `X-Unified-Intake-Support-Key` or `Authorization: Bearer <key>`. |
| Manifest | Build SHA, `support_export_manifest_version`, schema epoch, replay lineage tuple, persistence report, auth posture, request trace id, tenant truth, **operator_runtime_hints** (non-secret env flags). |
| Case head | Metadata only — no message bodies. |
| `/health` | Same auth posture + persistence + hints without hitting support routes. |
| Prod warning | Log + `production_support_export_risk` in auth posture when prod-like without key. |
| Weak key hint | `support_operator_warnings` if key shorter than 24 chars; startup log warning. |

---

## Current deployment truth

| Signal | Source |
|--------|--------|
| Git SHA | `get_git_sha()` — manifest + `/version` |
| Product-only | `UNIFIED_INTAKE_PRODUCT_ONLY` → `deployment_profile.is_unified_intake_product_only()` |
| Schema epoch | `INTAKE_SCHEMA_EPOCH` constant (`deployment_profile.py`) |
| Inline leak count | `PLATFORM_INLINE_ROUTES_UNGATED_IN_APP_MAIN` (currently empty tuple; lab moved behind platform-full registration) |
| Persistence mode | `unified_intake_case_persistence_report()` (`service_record_settings.py`) |
| Env hints | `operator_runtime_hints()`: `demo_mode`, `env_equals_prod`, `fast_startup`, `unified_intake_product_only` |
| Cloud Run `/healthz` quirk | Documented: use `/health/live` or `/api/healthz` if top-level `/healthz` does not reach app |

---

## Current org truth

| Concept | Truth |
|---------|--------|
| `client_id` | Selects pack under `configs/clients/<id>/` — **not** cryptographic office identity. |
| `X-Org-Id` | Client assertion; stored for honesty APIs; semantics **`client_asserted_org_id_not_tenant_authority_v1`**. |
| `tenant_id_authoritative` | **Always null** today. |
| Case isolation | **No RLS**; `case_id` not namespaced by org in DB contract as multi-tenant SaaS. |

---

## Current persistence truth

- **Modes:** `STRICT_PG_ONLY`, `PG_FIRST_BUT_NOT_STRICT`, `MIXED_STATE`, `UNKNOWN` — from env matrix (`SERVICE_RECORD_DATABASE_URL` / `DATABASE_URL`, `UNIFIED_INTAKE_DB_PRIMARY_*`, `UNIFIED_INTAKE_PG_DUAL_WRITE`, `UNIFIED_INTAKE_JSON_*`, `ENV=prod`).
- **Production-like:** `ENV=prod` or `UNIFIED_INTAKE_DB_PRIMARY_WRITES` → `is_production_mode()`; JSON case writes off when prod; JSON read fallback off when prod.
- **Sessions:** Postgres when DB URL set; else in-memory only if `UNIFIED_INTAKE_ALLOW_INMEMORY_SESSIONS_FOR_TESTS` — **not** for real prod.

---

## Fake SaaS patterns (call out)

1. Treating **`X-Org-Id` as tenant authority**  
2. Treating **`client_id` as auth**  
3. Assuming **`UNIFIED_INTAKE_PRODUCT_ONLY` = minimal attack surface** without reviewing any future inline routes  
4. Calling **`audit_export`** compliance-grade (it forwards to analytics today)  
5. Selling **manifest JSON** as legal hold / WORM (`replay_lineage` semantics say otherwise)  
6. Assuming **support bundle** exists when only manifest/case-head do  
7. **Perimeter-only** security for broker intake POST  
8. Implying **multi-tenant isolation** from headers alone  

---

## Rollout risks

- Deploy **without** support key on public URL → reconnaissance on manifest.  
- **`DEMO_MODE=true`** on production-shaped URL → readiness lies vs broker expectations.  
- **JSON/PG drift** across replicas during dual-write / fallback transitions.  
- **Wrong `ALLOWED_ORIGINS`** → silent frontend failures.  
- **Founder-only** knowledge of env matrix and Cloud Run secret wiring.  

---

## Rollback plan

- **Support key:** unset `UNIFIED_INTAKE_SUPPORT_API_KEY` → restores anonymous support routes (emergency only; document blast radius).  
- **Persistence:** flags documented in `service_record_settings.py` (`UNIFIED_INTAKE_JSON_READ_FALLBACK`, etc.).  
- **Product-only:** unset `UNIFIED_INTAKE_PRODUCT_ONLY` → larger surface (platform-full); rollback *to* product-only is the safer direction for pilots.  
- **Code rollback:** revert deploy to previous image / SHA; verify `deployment-manifest` git tuple matches.  

---

## Validation gates

After each batch:

1. `python3 -m compileall -q services/fiqa_api tests`  
2. `PYTHONPATH=. pytest tests/`  
3. `bash scripts/guardrail_inbox_triage.sh`  
4. `PYTHONPATH=. python3 scripts/run_full_regression.py`  
5. `cd ui && npm run build`  
6. `cd ui && npx --yes madge --circular --extensions ts,tsx src`  
7. `PYTHONPATH=. python3 scripts/support_deployment_manifest_smoke.py` (with server running; optional key)  

**Node/Vite:** If `npm run build` fails on Node 20, use Node 22 on PATH (documented in prior sprint notes).

---

## Deployment checklist

- [ ] `UNIFIED_INTAKE_PRODUCT_ONLY=1` for sellable pilot API surface (unless deliberate platform-full).  
- [ ] `UNIFIED_INTAKE_SUPPORT_API_KEY` set for any internet-exposed service (long random secret).  
- [ ] `SERVICE_RECORD_DATABASE_URL` + correct PG-primary flags for pilot persistence promise.  
- [ ] `ALLOWED_ORIGINS` matches real Vercel/host origins.  
- [ ] `DEMO_MODE` intentional per environment (not accidental on prod broker URL).  
- [ ] Post-deploy: `GET /health` → persistence + `deployment_profile` + hints; `GET /api/inbox/support/deployment-manifest` with key.  
- [ ] Record git SHA from manifest in ticket/runbook.  

---

## Support checklist

- [ ] Collect **`X-Request-ID`** from broker/client if available.  
- [ ] `/health` → `unified_intake_case_persistence` + `auth_posture` + `operator_runtime_hints`.  
- [ ] `deployment-manifest` → `replay_lineage` + `git` + persistence — **not** message bodies.  
- [ ] `case-head/{case_id}` for lifecycle metadata only.  
- [ ] Never interpret **`client_asserted_org_id` as proof** of customer org.  
- [ ] If prod risk flag present → escalate operator to set support key.  

---

## Onboarding checklist

- [ ] Confirm **which env file** is canonical for deploy (`configs/demo.env.example` → `.env.cloudrun`).  
- [ ] Confirm **Node version** for UI build.  
- [ ] Single **client pack** id and demo URL.  
- [ ] Document **`X-Org-Id`** as optional analytics hint only.  
- [ ] Run **guardrail** + smoke script after first deploy.  

---

## PHASE 1 — Discovery matrices

### SUPPORT_TRUTH_MATRIX

| Capability | Supported? | Evidence / limit |
|------------|------------|------------------|
| Deployment manifest | Yes | `GET /api/inbox/support/deployment-manifest` |
| Case metadata without PII | Partial | `case-head` — no bodies |
| Shared secret gate | Optional | `UNIFIED_INTAKE_SUPPORT_API_KEY` |
| Per-office RBAC | **No** | Single shared key |
| Full case export over support wire | **No** | Use existing case APIs + governance |
| Legal hold | **No** | `support_replay_handoff_metadata_v1_not_legal_hold` |

### DEPLOYMENT_TRUTH_MATRIX

| Signal | Available | Where |
|--------|-----------|-------|
| Git SHA | Yes | `/version`, manifest, case-head |
| Schema epoch | Yes | `INTAKE_SCHEMA_EPOCH` |
| Persistence mode | Yes | `/health`, manifest |
| Product-only flag | Yes | manifest, `/health`, root |
| Demo vs prod env hint | Yes | `operator_runtime_hints` |
| Automatic staging/prod diff | **No** | Manual compare manifests |

### ORG_OWNERSHIP_MATRIX

| Field | Authority |
|-------|-----------|
| `client_id` | Pack selector — trust boundary is deploy/config |
| `X-Org-Id` | Untrusted assertion |
| `tenant_id_authoritative` | None issued |
| Case row org binding | Not a cryptographic multi-tenant boundary |

### PERSISTENCE_TRUTH_MATRIX

| Env region | Risk if wrong |
|------------|----------------|
| No DB URL | Sessions/cases not durable |
| Dual-write + JSON-first reads | Read-your-writes broken across instances |
| Prod without PG | Contradicts production contract |

### SUPPORT_ESCALATION_MAP

1. **L1:** `/health` + manifest + case-head — correlation IDs.  
2. **L2:** Engineer with deploy access — env, SHA, DB flags.  
3. **Founder:** Graph/engine quirks, client pack content, trial promises not in code.  

### OPERATOR_CONFUSION_MAP

| Confusion | Reality |
|-----------|---------|
| “Org header proves customer” | No |
| “Health ok = embeddings warm” | Not always — depends on `DEMO_MODE` / phase |
| “Product-only = no lab” | Was historically leaky; now inline routes gated via platform registration — still verify |
| “Manifest = compliance export” | No |

### ENV_DRIFT_MATRIX

| Pair | Drift symptom |
|------|----------------|
| Vercel `VITE_API_BASE_URL` vs Cloud Run URL | Broken UI |
| `ALLOWED_ORIGINS` vs browser Origin | CORS silence |
| `DEMO_MODE` vs broker promise | Ready vs broken retrieval |
| Replica A JSON vs Replica B PG | Inconsistent cases |

### TOP_30_REAL_OPERATIONAL_RISKS

1. Anonymous support manifest on public internet  
2. Leaked support shared secret  
3. Prod broker URL with `DEMO_MODE=true` masking dependency failures  
4. No DB URL — session loss  
5. Dual-write without DB-primary reads  
6. Wrong CORS — “app broken” with no server error  
7. Founder-only Cloud Run secret layout  
8. Manual gcloud env patches overwritten by next deploy bundle  
9. Qdrant collection mismatch  
10. Missing OpenAI key — silent quality degradation  
11. Support interprets org header as legal tenant  
12. Case ID enumeration across offices (same deploy)  
13. Stale client pack on one region  
14. `/ready` vs `/health` confused in probes  
15. Fast startup hiding init failures  
16. JSON fallback masking PG failure  
17. WeChat redirect URI mismatch  
18. Attachment storage path drift  
19. Schema epoch not bumped when contract changes  
20. Trial sold as multi-tenant isolated  
21. Support key too short / reused across envs  
22. Node version drift breaks UI build  
23. Regression scripts skipped under time pressure  
24. Logging PII in verbose modes  
25. Multiple offices one deployment — data commingled  
26. Replay disputes without trace IDs  
27. Operator assumes RLS exists  
28. Disk full on JSON path  
29. Cold start + timeout too low  
30. Founder unavailable during Sev1 — no runbook  

### TOP_20_SUPPORT_FAILURES

1. No trace ID captured  
2. Manifest not fetched before interpreting replay  
3. Org header taken as proof  
4. Expecting message bodies on support routes  
5. Wrong base URL / port  
6. 401 on manifest — key not configured client-side  
7. Comparing staging manifest to prod ticket  
8. Assuming compliance export  
9. Escalating without persistence mode snapshot  
10. Ignoring `production_support_export_risk`  
11. Conflating `/healthz` with deep health  
12. Not documenting git SHA on ticket  
13. Expecting per-broker RBAC  
14. Missing `X-Request-ID` from UI  
15. Spoofed `X-Org-Id` mis-attributed in narrative  
16. Case-not-found without checking persistence mode  
17. Dual-write race misread as bug  
18. DEMO_MODE misunderstanding  
19. Support key shared in Slack permanently  
20. No rollback owner  

### TOP_20_DEPLOYMENT_FAILURES

1. Wrong `.env` copied  
2. `ALLOWED_ORIGINS` omitted → permissive default  
3. Secret Manager vs literal env mismatch on redeploy  
4. Wrong Cloud Run region/service  
5. Product-only flag wrong  
6. DB migrate not applied  
7. JSON writes left on while claiming PG-primary  
8. Min instances / concurrency wrong  
9. `/healthz` probe path wrong for platform  
10. Image tag not matching git expectation  
11. Frontend built against wrong API URL  
12. Support key not injected  
13. `DEMO_MODE` wrong  
14. Qdrant URL unreachable from Cloud Run  
15. Embedding warmup timeout  
16. Rolling deploy across mixed schema  
17. Asset CDN vs API split confusion  
18. Rollback without manifest verification  
19. Two pilots one service — config clash  
20. CI not enforcing smoke  

### TOP_20_FAKE_SAAS_PATTERNS

1. Header-as-tenant  
2. client_id as IAM  
3. Manifest as SOC2 evidence  
4. audit_export as WORM  
5. Single shared key as “enterprise RBAC”  
6. Marketing multi-tenant without RLS  
7. Assuming product-only = pen-test safe without checking routes  
8. Health ok = all subsystems ok  
9. Case JSON as source of truth while PG primary  
10. Treating replay lineage as subpoena-grade  
11. Implying SSO  
12. Per-office billing readiness  
13. Automatic tenant provisioning  
14. Data residency promises  
15. Noise isolation between offices on shared deploy  
16. “Encrypted at rest” narrative without explicit scope  
17. Support tooling as audit trail  
18. Analytics as authorization  
19. Contract tests as legal guarantees  
20. Founder narrative overriding code truth  

### TOP_20_FOUNDER_DEPENDENCIES

1. Cloud Run project wiring  
2. Which URL is canonical for pilot  
3. Client pack semantics & copy  
4. Trial commercial promises  
5. Secret rotation cadence  
6. When to enable LLM vs rules-only  
7. Escalation to model/vendor issues  
8. Manual DB interventions  
9. Interpreting ambiguous broker tickets  
10. WeChat / OAuth app ownership  
11. Vercel project env vars  
12. Qdrant cluster choice  
13. Cost caps / API limits  
14. Partner integrations roadmap  
15. Legal language around PII  
16. Prior incident context  
17. Priority among pilots  
18. Feature flags not in manifest  
19. Internal analytics interpretation  
20. Hiring/training support staff  

---

## PHASE 2 — Highest ROI hardening (this sprint)

Implemented or reinforced:

- **`operator_runtime_hints`** on `/health` and support JSON — cheap drift detection (`demo_mode`, `env_equals_prod`, `fast_startup`, product-only).  
- **Weak support key warnings** — posture JSON + startup log.  
- **Clearer middleware ordering comment** — reduces operator misreading of trace vs org assertion order.  
- **`configs/demo.env.example`** — documented support key purpose.  
- **`scripts/support_deployment_manifest_smoke.py`** — deterministic smoke for operators.  

Rejected (this sprint): IAM systems, RLS, per-tenant keys, billing, SSO.  

---

## PHASE 3 — Implementation notes

See commits touching:

- `services/fiqa_api/deployment_profile.py` — `operator_runtime_hints()`  
- `services/fiqa_api/security/support_export_gate.py` — short-key warning list  
- `services/fiqa_api/routes/inbox_triage.py` — manifest + case-head hints  
- `services/fiqa_api/app_main.py` — `/health`, startup warnings  
- `services/fiqa_api/security/request_identity.py` — middleware docstring  
- `configs/demo.env.example` — support key block  
- `scripts/support_deployment_manifest_smoke.py`  
- `tests/test_deployment_profile.py`, `tests/test_support_export_gate.py`  

---

## PHASE 5 — Tabletop simulations (summary)

For each scenario: **breaks first → survives → founder-dependent → support cannot answer**

| Scenario | Breaks first | Survives | Founder-dependent | Support gap |
|----------|--------------|----------|-------------------|-------------|
| Anonymous support exposure | Intel leak via manifest | Core intake if unrelated | Secret injection | Whether leak abused |
| Leaked support key | Manifest + case-head scrape | Still no RBAC row gates | Rotate secret | Blast radius |
| Wrong deployment profile | Extra routes / confusion | Inbox still works if mounted | Which SKU sold | Platform vs product bugs |
| product_only mismatch | Unexpected endpoints | Documented hints now | Policy | Endpoint enumeration |
| JSON/PG confusion | Wrong/stale case | Persistence mode on `/health` | Repair DB | Data reconciliation |
| Onboarding failure | UI CORS / wrong API URL | Demo offline mode partial | Vercel/env | Full chain debug |
| Founder unavailable | Sev1 decisions stall | Runbooks + manifests | Architecture tradeoffs | Vendor/model root cause |
| Angry broker escalation | Trust loss | Factual persistence/manifest | Commercial | Legal promises |
| Replay dispute | No trace id | lineage tuple + SHA | Model nondeterminism | “Exact replay” guarantee |
| Deployment rollback | Brief errors | Prior image | Verify DB compat | Partial migrations |
| Wrong env matrix | Silent degradation | Hints surface DEMO/prod | Fix env | Which flag wrong |
| Org confusion | Wrong analytics story | tenant_truth semantics | Future auth design | “Whose case” legally |
| Multi-office chaos | Shared deploy commingling | Optional org hint only | Multi-instance strategy | Per-office isolation proof |
| Support export misunderstanding | Wrong compliance expectation | Semantics strings | Legal | Retention policy |
| Startup warning ignored | Preventable incidents | Logs exist | Culture | — |

---

## PHASE 6 — Self critique lists

### TOP_20_STILL_FAKE_SAAS_PATTERNS

(Overlap intentional — reinforcement.) Header tenant, client IAM, manifest-as-compliance, audit_export=WORM, RBAC from one key, multi-tenant marketing, pen-test safe product-only myth, health=full subsystem truth, analytics as auth, SSO implications, billing readiness, auto provisioning, residency promises, noisy-neighbor safety, encryption theater, support as legal audit, contract tests as law, founder narrative vs code, enterprise workbook without RLS, “office” without isolation proof.

### TOP_20_MISSING_REAL_FOUNDATIONS

Per-org auth, RLS, billing, automated manifest diff CI, signed exports, support RBAC, tenant provisioning API, KMS envelope encryption story, backup/restore drills, SLO/error budget, on-call rotation, structured audit sink, rate limiting per tenant, secret rotation automation, multi-region story, data deletion workflow, formal DPA path, pen-test scope doc, customer-managed keys, incident commander playbook, stakeholder comms templates.

### TOP_20_SUPPORT_TRUTHS

Manifest is not legal hold; case-head has no bodies; support key is shared-secret not IAM; trace ID matters; persistence mode must be snapshot; org header is lying-client-safe; prod without key is flagged; git SHA is deploy truth anchor; schema epoch is contract label not migration id; DEMO_MODE changes readiness meaning; CORS issues masquerade as app bugs; dual-write needs DB-primary reads; JSON fallback can lie; `/health` ≠ always `/ready`; weak keys warned; rotate leaked keys; compare env hints across ticket and live; product-only reduces routers; inline routes historically risky — verify; escalation needs founder on ambiguous promises.

### TOP_20_DEPLOYMENT_TRUTHS

Env files can be overwritten by deploy script bundles; Secret Manager bindings conflict with literal deploy; Cloud Run has `/healthz` quirks; Node 22 often required for UI build; Qdrant optional in DEMO_MODE; product-only is env-flag; persistence matrix is complex; prod implies strict PG; support routes optional gate; git SHA can be unknown if image stripped; schema epoch must bump on contract change; ALLOWED_ORIGINS is deployment truth; FAST_STARTUP can hide failures; replicas need shared DB for consistency; rollback needs manifest SHA check; DEMO_MODE on prod URL is policy bug; client pack is filesystem-deployed truth; inline routes only when platform-full; readiness probes must match SKU; founder docs may lag code.

### TOP_20_OPERATOR_TRUTHS

Read `/health` before SSH; manifest before replay interpretation; hints reveal DEMO/prod mismatch; never paste support key to customers; logs may contain PII if verbose; guardrail scripts are cheap insurance; full regression is long but catches triage drift; madge catches UI cycles; smoke script is fast; prod support anonymity is recon risk; dual-write flags confuse everyone — snapshot; case JSON path != PG authority when strict PG; rotating secrets needs Cloud Run revision; min instances trade cost vs cold start; Vercel env is build-time; browser Origin matters not hostname guesses; DB URL visible to platform admins; rollback is revision pinned; inline lab routes absent in product-only when platform not registered; Graph engine may load in platform-full.

### TOP_20_ONBOARDING_TRUTHS

One canonical env template exists; UI API base must match Cloud Run; client pack id must match sales; X-Org-Id optional and untrusted; support key optional locally required publicly; DEMO_MODE must match demo story; DB optional locally not for paid pilot persistence promise; Node version documented; first success path = guardrail + smoke; founders must name canonical URL; trial scope ≠ enterprise scope; replay semantics documented in manifest; attachment paths environment-specific; WeChat needs redirect precision; LLM key optional but quality drops; Qdrant optional in demo mode; product-only recommended for pilots; secrets belong in Secret Manager; documentation lags — verify with `/health`; onboarding repeats fail without checklist; multi-office single deploy commingles unless architecture changes.

### TOP_20_ENTERPRISE_ILLUSIONS

SOC2 done, SSO ready, tenant isolation, RLS on, GDPR complete, HIPAA ready, magic multi-tenant, pen-test irrelevant, zero-trust achieved, SIEM integrated, DR tested, contractual SLA met, unlimited scale, data residency guaranteed, BYOK done, procurement artifacts ready, finance-grade billing, audit-grade exports, tenant SCIM, granular RBAC, no founder involvement.

### TOP_20_REAL_ADVANTAGES

Honest persistence reporting; optional support gate; deployment manifest for tickets; schema epoch label; product-only surface flag; replay lineage semantics explicit; tenant truth honesty layer; guardrail scripts; regression harness; client pack configurability; intake focus; case-head lightweight; trace middleware; CORS explicit; Cloud Run path quirks documented; startup prod/support warnings; env hints for drift; cheap smoke script; tests for support gate; operational sprint culture; clear non-goals.

### TOP_20_THINGS_NOT_TO_BUILD_YET

Full IAM, RLS, per-tenant billing, SSO, enterprise audit warehouse, multi-region active-active, customer KP API, complex RBAC UI, tenant admin portal, usage-based metering UI, magic compliance pack, over-engineered feature flags service, proprietary workflow engine, speculative data lake, premature microservices split, heavy ABAC, custom IdP, organization hierarchy CRM, noisy analytics PII store, automated legal hold, pen-test scope expansion without revenue, founder-less complex onboarding wizard, multi-vertical hub.

---

## PHASE 7 — Final convergence

| Decision | Outcome |
|----------|---------|
| Production-ready | Single-tenant-shaped pilot with honest health/manifest, optional support secret, PG-primary **when configured**, explicit non-IAM org posture. |
| Pilot-only | Multi-office isolation promises, compliance exports, RBAC support tooling. |
| Safe to sell | Intake triage + workbench **with documented limits**; operational runbooks + manifest discipline. |
| Never promise | Tenant isolation, SSO, audit-grade exports from current support wire. |
| Breaks at 30 offices | Shared-deploy commingling, support volume without rotation/training, env drift. |
| Breaks at 100 offices | Need real tenancy + billing + automation — **not built**. |
| Breaks at enterprise procurement | IAM/compliance/DPAs — **not built**. |
| Founder knowledge still needed | Commercial scope, vendor limits, secret ops, ambiguous incidents. |
| Operational closure gaps | No automated env/manifest diff; no on-call; no formal IR. |
| Real moat | Domain intake + broker workflow + honest ops posture — not fake tenancy. |
| Real operational wedge | Manifest + persistence truth + guardrails + regression — **truth over theater**. |

---

## Self critique (sprint-level)

This sprint documents more truth than it cryptographically enforces. The highest leverage remaining work is **perimeter + auth evolution** when revenue justifies — not more JSON fields. Honesty fields can still be ignored by humans under panic.

---

## Convergence criteria

- [x] SSOT file exists and matches code inspected.  
- [x] Support/deployment/org/persistence matrices drafted without invented capabilities.  
- [x] Small rollback-safe code improvements merged with tests.  
- [x] Operator smoke script added.  
- [ ] Full validation suite green at merge time (record in iteration log).  

---

## Final decision

Ship **honest operational instrumentation** (hints, warnings, smoke, docs) as the minimal SaaS hardening layer; defer **real multi-tenant and IAM** until explicit product commitment.

---

## FINAL_ONE_LINE

**Unified Intake is operationally survivable when operators trust `/health` + support manifest honesty — not when headers pretend to be tenants.**

---

## PHASE 8 — Final output (required)

1. **What became more real:** `operator_runtime_hints`, weak-key warnings, demo env documentation, support/manifest smoke script, clarified middleware truth in code comments.  
2. **What is still fake:** Multi-tenant isolation, IAM, compliance exports, RBAC support, billing.  
3. **Biggest support improvements:** Env hints on manifest/health; weak key visibility; smoke script.  
4. **Biggest deployment improvements:** Same hints reduce DEMO/prod confusion; example env documents support key.  
5. **Biggest org-ownership improvements:** Unchanged cryptography — still honesty-only; hints reinforce profile context.  
6. **Biggest remaining support risks:** Anonymous manifest if key unset; shared secret leakage; human ignores warnings.  
7. **Biggest remaining deployment risks:** Env bundle overwrite; CORS; DB flag drift across replicas.  
8. **Biggest remaining auth/tenant risks:** Spoofable org header; shared deploy case commingling; no RLS.  
9. **Biggest founder dependency:** Secret/layout knowledge and commercial promise boundaries.  
10. **What breaks at 30 offices:** Support repetition without tooling/training; config drift.  
11. **What breaks at 100 offices:** Architecture limits — need real tenancy + ops scale.  
12. **What breaks at enterprise sales:** IAM/compliance expectations vs actual stack.  
13. **Best next 10x leverage:** Server-issued org/session tokens **when pilot revenue clears**.  
14. **Best next sprint:** Gate intake mutations behind minimal API key or broker JWT **without full IAM theater**.  
15. **Best next 3-month roadmap:** PG-primary everywhere sold; support key mandatory in prod templates; CI manifest snapshot; backup drill; train support on matrices in this doc.  
16. **What should NOT be built yet:** Fake RBAC dashboard, multi-tenant marketing without RLS, compliance modules.  
17. **FINAL_ONE_LINE:** Same as § FINAL_ONE_LINE above.

---

## Iteration log

| When | Validations | Result |
|------|-------------|--------|
| 2026-05-08 | compileall; pytest; guardrail; full regression | PASS |
| 2026-05-08 | ui build + madge | PASS with NVM Node 22 PATH before Cursor Node 20 |
| 2026-05-08 | support_deployment_manifest_smoke.py | needs live API; pytest covers manifest |
