# Authenticated Multi-Office Foundation Sprint

**SSOT for sprint:** this file. **Created:** 2026-05-08. **Scope:** credible SaaS *boundary skeleton* (identity, org honesty, support/replay/deployment truth) — not full enterprise IAM.

---

## OBJECTIVE

Establish **runtime-honest** foundations so Unified Intake can evolve from “excellent pilot” toward **30–100 offices** without pretending headers are tenants or anonymous surfaces are “secure by obscurity.”

Concrete outcomes this sprint:

1. **Discovery maps** (auth surface, tenancy reality, support/replay, operator/deployment) grounded in repo grep/read — printed below and summarized in chat output.
2. **Threat model** (50 paths) and **trust model** that distinguish **client-asserted** metadata from **server-bound authority**.
3. **Design artifacts:** `AUTH_MODEL_V1`, `TENANT_ID_STRATEGY_V1`, `SUPPORT_EXPORT_V2`, `AUTH_ROLLOUT_PLAN`.
4. **Small safe code:** optional shared-secret gate for `/api/inbox/support/*`, **`auth_posture` on `GET /health`**, **`request_lineage.request_trace_id`** on support JSON, **explicit `X-Org-Id` semantics** (untrusted), **`audit_export` future bundle keys** extended toward signed exports, **CORS exposes `X-Request-ID`**.

---

## NON_GOALS

- Full OAuth / OIDC UI, self-serve signup, enterprise SSO, customer-facing RBAC console.
- Row-level security (RLS) implementation in Postgres **this sprint**.
- Per-office billing, Stripe, multi-region active-active.
- Replacing `client_id` pack routing with cryptographically bound tenant claims **without** a migration plan.
- Legal WORM storage, e-discovery pipelines, or SOC2 evidence packs **as shipped product** (design only where noted).

---

## SUCCESS_GATES

| Gate | Check |
|------|--------|
| G1 | Sprint SSOT (this file) exists with all required sections. |
| G2 | `AUTHENTICATION_SURFACE_MAP` + `TENANCY_REALITY_MAP` + support/replay + operator maps documented from code — no aspirational “we use JWT” unless wired. |
| G3 | `TOP_50_ATTACK_PATHS` + trust/support/authz designs (`AUTH_MODEL_V1`, etc.). |
| G4 | Code: `support_export_gate` + `auth_posture` on `/health` + support manifest/case-head lineage fields; **default env = backward compatible** (no key → anonymous support surface unchanged). |
| G5 | `compileall` + targeted pytest (`test_support_export_gate`, `test_deployment_profile`) pass; full `pytest` + `guardrail_inbox_triage.sh` + UI build + madge re-run before merge (operator duty). |

---

## ROLLBACK_PLAN

| Change | Rollback |
|--------|-----------|
| Optional `UNIFIED_INTAKE_SUPPORT_API_KEY` | Unset env → support routes behave as before (anonymous). |
| New JSON keys on support responses (`auth_posture`, `request_lineage`) | Clients must tolerate extras (standard JSON); remove keys only via revert commit. |
| `deployment_profile.auth_posture` on `/health` | Revert `app_main.py` health payload fragment. |
| `audit_export.future_export_bundle_keys` | Revert tuple extension (documentation-only consumers). |

---

## MIGRATION_STRATEGY

1. **Phase A — honesty & probes:** surface `auth_posture`, lineage IDs, schema epoch (already on manifest); document `X-Org-Id` as untrusted.
2. **Phase B — perimeter:** operators set `UNIFIED_INTAKE_SUPPORT_API_KEY` in staging/prod Cloud Run / reverse proxy; align internal runbooks.
3. **Phase C — tenant column:** add nullable `tenant_id` / `office_id` to service_record DDL **after** AUTH_MODEL_V1 defines issuance (avoid orphan columns).
4. **Phase D — auth middleware:** org-bound API keys or JWT with audience + tenant claim verification (**not** header-only).
5. **Phase E — RLS:** Postgres policies keyed off authenticated session tenant claim.

---

## THREAT_MODEL

See **TOP_50_ATTACK_PATHS** (below). Themes: **global case enumeration**, **org spoofing via headers**, **support manifest reconnaissance**, **attachment abuse**, **deployment/schema mismatch replay**, **insider misuse**, **future noisy-neighbor** when JSON/in-memory paths linger.

---

## TRUST_MODEL

| Layer | Trusted today | Not trusted |
|-------|----------------|-------------|
| Network | Whatever perimeter ops configure (Cloud Run, IAP, VPN) — **not enforced in app** for most routes | “HTTPS therefore safe” |
| Headers | `X-Request-ID` for correlation | **`X-Org-Id`** — client asserted; **no crypto binding** |
| Case ID | Opaque string — **any caller who knows ID reads full case** on inbox API | Obscurity as access control |
| Support routes | After optional shared secret: possession of `UNIFIED_INTAKE_SUPPORT_API_KEY` | Still **not** per-office RBAC |
| Deployment manifest | Git SHA + persistence report — **honest process artifact**, not attestation | Does not prove binary ≡ git |

---

## OPERATOR_MODEL

- **Health:** `GET /health` → phase, `unified_intake_case_persistence`, `deployment_profile` (+ **`auth_posture`**).
- **Readiness:** `/ready`, `/health/ready`, `/healthz` variants — embedding/Qdrant coupling for demo stack.
- **Profile switch:** `UNIFIED_INTAKE_PRODUCT_ONLY` reduces mounted routers; platform routes via `register_platform_inline_routes` only when full platform.
- **Schema epoch:** `INTAKE_SCHEMA_EPOCH` in `deployment_profile.py` — contract label, not DB migration ID.
- **Support playbook:** use deployment-manifest + schema epoch before interpreting replay tickets.

---

## SUPPORT_MODEL

- **Today:** `GET /api/inbox/support/deployment-manifest`, `GET /api/inbox/support/case-head/{case_id}` — **minimal case metadata**, no message bodies.
- **Optional gate:** `UNIFIED_INTAKE_SUPPORT_API_KEY` → require header or Bearer (**implemented this sprint**).
- **Lineage:** responses include `request_lineage.request_trace_id` (matches `X-Request-ID`).
- **Gap:** no signed export bundle, no redacted transcript replay pack, no immutable WORM audit trail.

---

## TENANCY_MODEL

- **Real tenant (future):** server-issued identity binding **office/org** to requests + storage (Postgres RLS or equivalent).
- **Fake tenant today:** `org_id` stored on cases from **`X-Org-Id`** without verification — useful for analytics partitioning **only if perimeter guarantees honesty**.
- **`client_id`:** pack/config lane selector (`get_active_client_id()`), **not** cryptographic tenant isolation.
- **Deployment slicing:** `UNIFIED_INTAKE_PRODUCT_ONLY`, persistence env flags (`UNIFIED_INTAKE_DB_PRIMARY_*`, dual-write) — **deployment illusion** if env drifts between regions/instances.

---

## AUTHORITY_MODEL

| Action | Authority source today | Target (AUTH_MODEL_V1) |
|--------|------------------------|-------------------------|
| List/read/delete case | Anonymous HTTP (same network) | Scoped credential + tenant filter |
| Triage POST | Anonymous + optional org header | Same + verified tenant |
| Support export | Optional shared secret | Per-env key → later per-role keys |
| Operator platform routes | Product-only gate hides routers; full platform exposes wide surface | IAP/mTLS + RBAC |

---

## DEPLOYMENT_MODEL

- **Entry:** `services/fiqa_api/app_main.py` composes routers; inbox + analytics always mounted; platform routers conditional.
- **Persistence truth:** `service_record_settings.py` — DB URL, dual-write, JSON fallback flags; **`case_truth_repository`** mediates reads.
- **Persistence writes:** `service_record_repository.py` — Postgres shape; **no tenant column** in core path yet (verify DDL separately).
- **Branch/schema truth:** git SHA via `get_git_sha()` on manifest; **schema epoch** string for contract drift detection.

---

## REALITY_CHECKS

1. **`GET /api/inbox/cases` paginates global queue** — no org filter in handler (`inbox_triage.py`).
2. **`GET /api/inbox/cases/{case_id}` returns full case** if ID known — no auth.
3. **`X-Org-Id` on POST `/triage`** — trimmed and stored as metadata — **not verified**.
4. **`GET /api/analytics/dashboard`** — in-memory funnel buffer — **unauthenticated** (product-only still mounted).
5. **Support case-head** — metadata only but **still ties to case_id enumeration risk** if anonymous.
6. **Product-only does not add auth** — it reduces route surface, not identity.

---

## SELF_CRITIQUE

- One shared support secret is **not** multi-office RBAC; it is a **blast-radius reducer** only.
- **`auth_posture` does not fix case enumeration** — it documents and optionally gates support-only paths.
- **Tenant migration not started in DDL** — strategy documented; premature columns risk fake SaaS (“column exists therefore isolated”).
- **Replay remains incomplete** — case-head lacks transcripts/model prompts/retrieval hashes.

---

## FINAL_DECISION

Ship **honest posture + optional support gate + lineage metadata** now; defer enterprise IAM until tenant issuance and DB boundaries are designed **together**.

---

## FINAL_ONE_LINE

**Unified Intake now exposes runtime-honest auth posture and optional support-route secrets; tenant isolation and verified org authority remain explicitly future work — no header-as-tenant pretense.**

---

# PHASE 1 — SYSTEM DISCOVERY (grounded)

## Files explicitly inspected / grep’d

| Area | Paths |
|------|--------|
| Inbox routes | `services/fiqa_api/routes/inbox_triage.py` |
| Analytics | `services/fiqa_api/routes/analytics_dashboard.py` |
| App composition | `services/fiqa_api/app_main.py` |
| Deployment profile | `services/fiqa_api/deployment_profile.py` |
| Case reads | `services/fiqa_api/inbox_triage/case_truth_repository.py` |
| PG persistence | `services/fiqa_api/db/service_record_repository.py`, `service_record_settings.py` |
| Audit/export scaffold | `services/fiqa_api/inbox_triage/audit_export.py` |
| Guardrail | `scripts/guardrail_inbox_triage.sh` |
| Middleware | `RequestIDMiddleware`, `LoggingMiddleware` in `app_main.py` |

---

## AUTHENTICATION_SURFACE_MAP

**Legend:** *anonymous* = no application-level credential verified on the handler.

### Unified Intake (always mounted)

| Route pattern | Auth today | Data sensitivity |
|---------------|------------|------------------|
| `POST /api/inbox/triage` | Anonymous | Creates/updates cases; accepts **`X-Org-Id`** (unverified) |
| `GET/POST/PATCH... /api/inbox/cases*` | Anonymous | **Full case** read/write paths; list is **global** |
| `GET /api/inbox/session/{id}` | Anonymous | Session recovery |
| `GET /api/inbox/support/deployment-manifest` | Anonymous **or** optional API key (env) | Deployment reconnaissance |
| `GET /api/inbox/support/case-head/{case_id}` | Anonymous **or** optional API key | Metadata; requires knowing `case_id` |
| WeChat binding routes | Partially gated (client pack mode + credentials) | Session identity binding |
| `GET /api/analytics/dashboard` | Anonymous | Aggregated funnel from in-memory buffer |

### Health / probes (representative)

| Route | Auth | Notes |
|-------|------|------|
| `GET /health`, `/ready`, `/healthz`, `/health/live`, `/api/healthz` | Anonymous | `/health` exposes persistence + deployment profile |
| Qdrant health | Anonymous | Infra probe |

### Platform-full only (`UNIFIED_INTAKE_PRODUCT_ONLY` off)

Large surface: `/api/query`, `/search`, jobhunter, mortgage, experiment/steward, ops, metrics, agent routes, `platform_inline_routes` (lab/graph/tuner/etc.). **Treat as dangerous capability surface** for any internet-exposed deployment.

---

## TENANCY_REALITY_MAP

| Concept | Reality |
|---------|---------|
| **True tenant** | **None** at DB/API enforcement layer — no RLS, no verified tenant claim on reads |
| **Fake tenant** | `org_id` on cases from **`X-Org-Id`** — correlation key only |
| **org_id illusion** | Looks like multi-org SaaS; **no server-side proof** |
| **client_id illusion** | Pack/config selector; multiple “offices” could share a pack if misconfigured |
| **Deployment slicing** | Env flags + product-only router mount — **not** tenant isolation |

---

## SUPPORT_REPLAY_REALITY_MAP

| Capability | Today |
|------------|------|
| Replay truth | Role-C simulation + triage engine **in-process**; not a legal-grade replay tape |
| Support can | Read deployment manifest; read case-head metadata; operators with network access can hit full case APIs |
| Support cannot | Cryptographically prove export integrity; obtain signed redacted transcript bundle |
| Legal replay gaps | No immutable hash chain, no model/version pinning on messages, no WORM |
| Immutable lineage gaps | `audit_export.record_intake_case_mutation` → `track_event` only; **no tamper-evident store** |

---

## OPERATOR_DEPLOYMENT_REALITY_MAP

| Dimension | Truth |
|-----------|------|
| Operator | Uses `/health`, support manifest, logs; **no first-class operator RBAC in app** |
| Deployment | Cloud Run / scripts — **process/env truth** |
| Env truth | Persistence toggles are subtle (`UNIFIED_INTAKE_DB_PRIMARY_*`, dual-write, JSON fallback) |
| Runtime truth | Single-process demo OK; **multi-instance** requires DB-primary + no JSON illusion |
| Schema truth | `INTAKE_SCHEMA_EPOCH` + SQL migrations (repo); drift = operational risk |
| Branch truth | Git SHA on manifest — **build pipeline must tie image to commit** |

---

# PHASE 2 — TOP_50_ATTACK_PATHS

1. Global **case enumeration** via `GET /api/inbox/cases` pagination.  
2. **Case ID brute-force / leak** → `GET /api/inbox/cases/{id}` full exfiltration.  
3. **Org spoofing**: send attacker-chosen `X-Org-Id` → pollutes analytics / future tenant migration.  
4. **Cross-org read** (today): all offices share one queue if single deployment.  
5. **DELETE test case** mis-flagged `workbench_test` → data loss (business logic gap).  
6. **Support manifest** reconnaissance (build SHA, persistence mode) — **target selection**.  
7. **Anonymous support case-head** (when no secret): metadata leak + confirms ID exists.  
8. **Attachment upload abuse** (size/type/path) — DoS / malware staging if perimeter weak.  
9. **Rate-limit bypass** — no app-level limit cited on triage path.  
10. **Session fixation** — predictable `session_id` if client weak (depends on FE).  
11. **WeChat binding simulate** — enabled if `WECHAT_BINDING_ALLOW_SIMULATE` in prod by mistake.  
12. **CORS `*` + anonymous API** — browser-driven abuse from malicious sites (CSRF-like patterns).  
13. **Analytics dashboard** leak — business funnel metrics.  
14. **Health endpoint**used for **version/persistence fingerprinting**.  
15. **Platform-full route leak** if `UNIFIED_INTAKE_PRODUCT_ONLY` accidentally off.  
16. **Inline platform routes** (`platform_inline_routes`) — graph/embeddings/tuner exposed.  
17. **`/api/query` RAG** abuse — cost + data exfil if collections sensitive.  
18. **Jobhunter / mortgage** surfaces — unrelated data paths when enabled.  
19. **Ops metrics / black swan** — DoS, operational manipulation.  
20. **Experiment/steward** — arbitrary job execution surface.  
21. **Agent endpoints** — tool invocation where configured.  
22. **Report static mount** `/reports` — informational disclosure.  
23. **SPA fallback** — path confusion less likely but large attack surface on same origin.  
24. **JSON case file read fallback** misconfiguration — stale reads vs Postgres.  
25. **Dual-write drift** — PG vs JSON inconsistency → wrong replay.  
26. **Missing DB URL in prod** — health warns but triage may degrade oddly.  
27. **In-memory sessions** test flag in prod — session bleed across processes = **fake persistence**.  
28. **Support export abuse** — operator key stolen → **all offices** on that deployment.  
29. **Shared support key** — no per-office scoping.  
30. **Insider** broker exports cases via API they already legitimately use.  
31. **Log injection** via triage text → SIEM noise (availability).  
32. **Prompt injection** via customer text → downstream tools (LLM path).  
33. **Case append** boundary bypass attempts (`case_boundary` logic stress).  
34. **Attachment OCR path** resource exhaustion.  
35. **Regulator audit request** — cannot produce authoritative replay tape today.  
36. **Stale schema replay** — old export interpreted with new triage code.  
37. **Deployment mismatch** — wrong image with same `case_id` store.  
38. **Manifest recon → CVE targeting** specific git SHA.  
39. **GraphQL / OpenAPI** discovery if exposed — FastAPI `openapi.json` on default (verify deployment).  
40. **TLS termination misconfig** — plaintext internal hop (infra).  
41. **Qdrant key exposure** in env → collection dump.  
42. **OpenAI key exposure** → cost abuse.  
43. **Founder debug routes** in prod (`/debug/trace`) when platform on.  
44. **Replay impersonation** — support cannot prove “customer said X” without transcript signing.  
45. **Multi-tenant noisy neighbor** (future) — one office’s load blocks others **without quotas**.  
46. **Header injection** via proxies stripping `X-Org-Id` vs app trust mismatch.  
47. **Cache poisoning** (if CDN in front of API) — low likelihood but standard SaaS risk.  
48. **Webhook / callback** forging on WeChat path if state secret weak.  
49. **Race on case creation** — duplicate cases / binding confusion.  
50. **Supply chain** — dependency compromise in lockfiles (general).

---

# PHASE 3 — DESIGNS

## AUTH_MODEL_V1 (incremental)

| Mechanism | Purpose | Now | Later | Never (this product phase) |
|-----------|---------|-----|-------|----------------------------|
| **Request trace** | Correlate logs/support | `X-Request-ID` + `request_lineage` | Distributed trace propagation | — |
| **Support shared secret** | Gate narrow operator JSON | `UNIFIED_INTAKE_SUPPORT_API_KEY` | Per-env **rotated** keys + audit | Fake “enterprise SSO” UI |
| **Org-bound API key** | Office-scoped automation | Design only | Issued per office; server-side map | Header-only “tenant” |
| **JWT / OIDC** | Human broker sessions | Out of scope | After mobile/web auth decision | DIY crypto tokens |
| **mTLS / IAP** | Edge auth | Infra | Cloud Run IAM / BeyondCorp | — |
| **RBAC** | Support vs broker vs admin | Out of scope | Policy engine | Giant in-app role UI |

**Request identity fields (target):** `trace_id`, `credential_kind`, `tenant_id` (nullable), `scopes[]`, `support_ticket_id` (optional, for support replay workflow).

---

## TENANT_ID_STRATEGY_V1

- **`tenant_id` nullable** until issuance exists; **never** infer solely from `X-Org-Id`.
- **Migration sequence:** (1) add nullable column + backfill from verified mapping table; (2) dual-read; (3) enforce on write; (4) RLS.
- **RLS compatibility:** policies use `current_setting('app.tenant_id')` or Supabase-style session claims — **set only after verified JWT/API key middleware**.
- **Org-bound reads:** replace global `list_recent_cases_for_read` with tenant-filtered queries once authority exists.

---

## SUPPORT_EXPORT_V2

- **Signed export bundle** (CMS-style detached signature or JWS) over canonical JSON + manifest.
- **Redacted support view** — transcript hashes, not raw PII, unless ticket class allows.
- **Support-safe replay** — model ID, prompt template version, retrieval doc IDs **hashed**, schema epoch embedded.
- **Immutable metadata** — WORM storage or external SIEM with hash chain (future).
- **Deployment lineage** — image digest + git SHA + config flags snapshot.
- **Schema lineage** — `INTAKE_SCHEMA_EPOCH` + DB migration id.

---

## AUTH_ROLLOUT_PLAN

1. **Document** anonymous surfaces (runbooks).  
2. **Enable** `UNIFIED_INTAKE_SUPPORT_API_KEY` in staging → validate dashboards/alerts.  
3. **Pilot** single broker — perimeter + IP allowlist **still required**.  
4. **Feature flag pattern** — env-based (no fake UI flags).  
5. **Safe failure** — wrong key → **401** on support only; **do not** break triage FE.  
6. **Backwards compatibility** — unset key preserves legacy anonymous support behavior.

---

# PHASE 4 — IMPLEMENTATION NOTES (this sprint)

| Item | Location |
|------|----------|
| Support gate + posture dict | `services/fiqa_api/security/support_export_gate.py` |
| Request lineage helper | `services/fiqa_api/security/request_identity.py` |
| Wired on support routes + `/health` | `inbox_triage.py`, `app_main.py` |
| Future bundle keys | `inbox_triage/audit_export.py` |
| CORS | `X-Request-ID` exposed |

---

# PHASE 5 — OPERATOR / SUPPORT SIMULATIONS

## 30 OFFICE SIMULATION (narrative outcomes)

| Scenario | What happens today | Failure mode |
|----------|---------------------|--------------|
| Angry broker | Hits `/cases` — sees **everyone** if shared deployment | Trust incident |
| Leaked `case_id` | Full read via `/cases/{id}` | Certain breach |
| Support escalation | Uses manifest + case-head | Metadata-only; may need full case → **PII policy** |
| Tenant confusion | Two offices same deployment | **No isolation** |
| Replay request | Engineer uses stub + logs | **No signed replay** |
| Regulator audit | Ask for tamper-evident trail | **Fails** — events are best-effort track_event |
| Deployment mismatch | Wrong binary + old PG | Wrong AI behavior / schema drift |
| Stale schema rollback | Epoch changes | Manifest helps; **no automatic replay guard** |
| Support impersonation | Shared secret only | **Cannot distinguish** individuals |
| Org isolation failure | Spoofed `X-Org-Id` | Wrong analytics / wrong future tenant backfill |

## 100 OFFICE SIMULATION

Amplifies: **noisy neighbor** on triage latency, **support queue overload**, **key rotation** pain with single shared secret, **compliance** variance by state/broker, **runbook** drift between regions.

---

# PHASE 6 — VALIDATION COMMANDS

```bash
python3 -m compileall -q services/fiqa_api
PYTHONPATH=. python3 -m pytest tests/test_support_export_gate.py tests/test_deployment_profile.py -q
bash scripts/guardrail_inbox_triage.sh
cd ui && npm run build && npx --yes madge --circular --extensions ts,tsx src
# Optional: PYTHONPATH=. python3 -m pytest  # full suite
```

---

# PHASE 7 — RISK & GAP LISTS

## TOP_30_REMAINING_RISKS

1. Global case list without tenant filter.  
2. Full case read by ID without auth.  
3. `X-Org-Id` spoofing.  
4. Single shared support secret — no per-office scope.  
5. Analytics endpoint unauthenticated.  
6. Platform-full accidental exposure.  
7. JSON/PG dual-track drift.  
8. In-memory session flag misuse in prod.  
9. No rate limits on triage.  
10. Attachment abuse DoS.  
11. LLM prompt injection operational risk.  
12. No WORM audit.  
13. No signed exports.  
14. Replay lacks model lineage.  
15. OpenAPI public discovery.  
16. CORS wildcard in dev patterns copied to prod.  
17. Weak rotation story for API keys.  
18. No per-user support attribution.  
19. `case_id` GUID predictability (if ever weak).  
20. Multi-instance cache incoherence (in-memory analytics).  
21. Secrets in env logs.  
22. Third-party key compromise (OpenAI/Qdrant).  
23. Supply chain.  
24. RLS absent — any SQL bug is cross-tenant.  
25. No budget caps per office.  
26. Insider export.Runs without detective controls.  
27. Session hijack if `session_id` leaks.  
28. WeChat simulate flag in prod.  
29. Health fingerprinting aids attackers.  
30. Regulatory evidence gap.

## TOP_20_FAKE_SAAS_PATTERNS

1. Treating **`X-Org-Id` as tenant**.  
2. Calling pack **`client_id` a tenant**.  
3. Claiming product-only mode is “secure multi-tenant.”  
4. Equating **TLS with auth**.  
5. **Dashboard metrics** as “product analytics suite” without access control.  
6. **Git SHA on manifest** as binary attestation.  
7. **case-head** as “full replay.”  
8. **Dual-write** without read parity guarantees.  
9. **track_event** as compliance audit.  
10. **Env flag** theater without CI enforcement.  
11. **Header-based RBAC** without tokens.  
12. **Single DB** + column prefix pretending RLS.  
13. **Demo in-memory** paths in prod.  
14. **Obscure URLs** as security.  
15. **“We’ll add auth later”** without tenant migration plan.  
16. **Shared API key** as enterprise SSO.  
17. **Analytics buffer** as data warehouse.  
18. **Support manifest** as contract SLA proof.  
19. **Schema epoch** without migration automation.  
20. **Spa + same origin** assumptions for API CSRF.

## TOP_20_NOT_ENTERPRISE_READY_AREAS

1. No identity provider integration.  
2. No SCIM / HRIS mapping.  
3. No SOC2 evidence automation.  
4. No per-tenant audit export SLA.  
5. No DPA-grade data map.  
6. No encryption-at-rest customer-managed keys story.  
7. No formal IR playbooks in product.  
8. No RBAC/ABAC.  
9. No pen-test boundary defined.  
10. No tenant-specific retention policies **enforced in storage**.  
11. No zero-trust service mesh.  
12. No formal change management tied to schema epoch.  
13. No multi-region failover **for case store**.  
14. No legal hold workflow.  
15. No dedicated security logging sink with integrity.  
16. No bug bounty scope.  
17. No SSO for operators.  
18. No contract-driven SLO dashboards per tenant.  
19. No enterprise billing hooks.  
20. No formal access reviews.

## TOP_20_SUPPORT_GAPS

1. No signed bundle.  
2. No redaction tiers.  
3. No ticket ↔ trace correlation standard.  
4. No runbook-generated manifest fetch automation.  
5. No per-support-agent auth.  
6. No time-bound ephemeral credentials.  
7. No customer-approved export consent log.  
8. No transcript-only extracts.  
9. No attachment malware scan hook documented.  
10. No “safe mode” degraded triage flag for incidents.  
11. No support-facing case search by tenant.  
12. No immutable incident timeline.  
13. No integration with Zendesk/Intercom identity.  
14. No support UI — curl-only.  
15. No locale/regulatory tagging on cases.  
16. No automatic PII detector on exports.  
17. No lineage for LLM retries.  
18. No snapshot of routing flags per request.  
19. No customer-visible incident status page linkage.  
20. No training data for support engineers on fake vs real tenancy.

## TOP_20_OPERATOR_GAPS

1. No GitOps-enforced `UNIFIED_INTAKE_PRODUCT_ONLY`.  
2. No automated drift detection PG vs JSON.  
3. No per-deploy canary case replay suite mandatory gate.  
4. No unified secrets rotation calendar.  
5. No cost anomaly alerts per deployment.  
6. No synthetic probe for triage SLO from **each** office region.  
7. No formal rollback playbook tied to schema epoch.  
8. No infra-as-code parity checklist.  
9. No on-call escalation tied to persistence mode flips.  
10. No database backup restore drills documented in product repo.  
11. No rate dashboard for LLM tokens per tenant.  
12. No incident “kill switch” besides env redeploy.  
13. No automated OpenAPI diff on release.  
14. No dependency CVE gate explanation to founders.  
15. No multi-env promotion pipeline standard.  
16. No capacity model for 100 offices.  
17. No tracing sampling strategy.  
18. No log retention uniformity across brokers.  
19. No configuration registry for client packs per office.  
20. No operator RBAC inside Cloud consoles documented per sprint.

---

# PHASE 8 — FINAL OUTPUT (also repeated in PR / chat)

## What is REAL SaaS now

- Explicit **deployment + persistence honesty** on `/health`.  
- **Optional cryptographic-grade secret gate** (shared key) for **narrow** support JSON paths — reduces drive-by recon when configured.  
- **Request trace IDs** end-to-end on responses + support JSON lineage.  
- **Documented** (and JSON-enforced semantics string) that **`X-Org-Id` is not authority**.

## What is still fake SaaS

- **Header-based “org”** without verified issuance.  
- **Global case APIs** as if each caller were naturally scoped.  
- **Analytics** as cross-tenant aggregate with no auth.  
- **“Tenant” language** anywhere implying isolation without RLS + verified credentials.

## What is still deployment illusion

- Same binary + same DB for “multi-office” without hard partitions.  
- **Schema epoch** without automated enforcement blocking incompatible readers.  
- **Git SHA** without reproducible build provenance discipline.

## What is still auth illusion

- Most Unified Intake routes **still anonymous** at app layer.  
- **One support key** ≠ per-office enterprise IAM.

## What is still replay illusion

- No signed bundles; **case-head** is not a transcript; **audit_export** is **not** WORM.

## What breaks at 30 offices

- **Operational noise** on shared queues; **wrong-office data exposure** risk; **support** scalability on manual curl workflows; **cost** attribution blur.

## What breaks at 100 offices

- **Noisy neighbor** latency; **secret rotation** chaos; **compliance** fragmentation; **incident blast radius** without tenant partitions.

## What breaks at enterprise sales

- **No SSO/RBAC**, **no tenant audit exports**, **no formal DPA data controls**, **no security attestations** tied to product behavior.

---

## Best next 10× leverage

**Verified tenant on every case read/write** (API key or JWT) + **Postgres RLS** + **replace global `/cases` list** with scoped queries.

## Best next sprint

**Tenant issuance MVP**: nullable `tenant_id`, migration script from approved office registry, middleware verifying office API keys, **filter list/read Case APIs** — still no OAuth UI.

## Best next 3-month roadmap

1. Office registry + API keys + audit log sink.  
2. RLS + remove JSON fallback in prod paths.  
3. Signed support export v2 + redaction pipeline.  
4. Rate limits + attachment policy enforcement.  
5. Operator SSO via IAP / BeyondCorp — **not** bespoke login UI.

## What should NOT be built yet

- Customer self-serve multi-tenant admin portal.  
- DIY JWT minting without IdP.  
- Per-broker Stripe billing.  
- “AI compliance officer” narrative features without storage proof.

## Biggest founder dependency

Choosing **real identity source** (broker IdP vs SearchForge-issued keys) **before** schema churn becomes expensive.

## Biggest enterprise blocker

**Tenant-isolated auditability** (who accessed which case when, provably).

## Biggest security blocker

**Anonymous full case read/list** on the default application surface.

## Biggest support blocker

**No signed, redacted export** tied to ticket + trace + schema epoch.

## Biggest tenancy blocker

**No server-verified tenant claim** bound to persistence layer.

---

## FINAL_ONE_LINE (duplicate)

**Unified Intake now exposes runtime-honest auth posture and optional support-route secrets; tenant isolation and verified org authority remain explicitly future work — no header-as-tenant pretense.**
