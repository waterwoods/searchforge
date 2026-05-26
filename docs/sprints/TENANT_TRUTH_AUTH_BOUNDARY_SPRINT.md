# Tenant Truth + Auth Boundary Sprint — SSOT

**SSOT path:** `docs/sprints/TENANT_TRUTH_AUTH_BOUNDARY_SPRINT.md`  
**Status:** Phase 0–7 documented; Phase 4 partial implementation (runtime honesty layer).  
**Last updated:** 2026-05-08  

---

## OBJECTIVE

Establish the **first layer of runtime truth** for Unified Intake: honest **tenant posture**, **request ownership hooks**, **support/replay boundary visibility**, and **migration-ready placeholders**—without pretending to ship enterprise IAM.

---

## NON_GOALS

- Full OAuth / SSO / self-serve signup / RBAC UI  
- Row-level security (RLS) in Postgres **implemented** in this sprint  
- Cryptographic multi-tenant isolation at the HTTP edge  
- “Fake” `tenant_id` derived only from `X-Org-Id` as if it were authoritative  
- Large refactors of case store, triage engine, or analytics pipeline  

---

## SUCCESS_GATES

| Gate | Criterion |
|------|-----------|
| G1 | Code discovery maps produced (tenant / auth / ownership / replay) grounded in repo |
| G2 | Threat catalog (≥50) covers spoofing, enumeration, replay, support abuse, deployment drift |
| G3 | **TENANT_TRUTH_V1** design: nullable authoritative tenant, org-bound ownership story, RLS-ready column naming |
| G4 | **AUTH_BOUNDARY_V1** design: product anonymous surface vs support key vs future JWT scope |
| G5 | Small implementation: request-state + manifest honesty + tests (no giant rewrite) |
| G6 | `compileall`, full `pytest`, `guardrail_inbox_triage.sh`, UI `npm run build`, `madge` — recorded |
| G7 | Self-critique lists (30/20 blocks) + explicit “what not to build yet” |

---

## TRUST_MODEL

| Layer | Trust today | Target V1 |
|-------|-------------|-----------|
| **Tenant authority** | None server-side | Nullable `tenant_id_authoritative`; future API key / JWT scope |
| **Org label** | Client header `X-Org-Id` (assertion) | Same + persisted **optional** org key on case when product chooses to store it |
| **Case ownership** | Knowledge of `case_id` / `session_id` UUID | Same + optional org/credential binding later |
| **Support export** | Shared secret optional (`UNIFIED_INTAKE_SUPPORT_API_KEY`) | Same + future scoped keys per org |
| **Replay** | Metadata-only support routes + same case store as product | Same + signed export bundles (future) |

---

## TENANT_TRUTH_MODEL

**Runtime definition (honest):**

- **`tenant_id_authoritative`**: always **`null`** until IAM issues tenant identity (API key claims, JWT `tid`, or mTLS SAN mapping).  
- **`client_asserted_org_id`**: normalized copy of `X-Org-Id` (max 256 chars), **not** proof of tenancy.  
- **`semantics`**: stable string token documenting meaning (`client_asserted_org_id_not_tenant_authority_v1`).

**Persistence:** Cases today do **not** store org_id in `case_store` / Postgres mirror (`grep` confirms no `org_id` in `inbox_triage/` persistence paths). Org flows to **analytics events** only via triage (`org_id` parameter on `triage_inbox`).  

---

## AUTH_BOUNDARY_MODEL

| Surface | Authentication | Authorization |
|---------|----------------|---------------|
| **Public product** (`/api/inbox/triage`, cases CRUD, session) | None | None — possession of UUID / network access |
| **Support export** (`/api/inbox/support/*`) | Optional shared secret | **Binary**: secret matches deployment OR anonymous pilot |
| **Health / deployment truth** (`/health`) | None | Information disclosure — posture + persistence mode |
| **Analytics dashboard** (`GET /api/analytics/dashboard`) | None | In-memory funnel — **no tenant partition** |
| **Platform-full** (when `UNIFIED_INTAKE_PRODUCT_ONLY` off) | Mixed legacy routes | Outside Unified Intake scope |

---

## REQUEST_OWNERSHIP_MODEL

| Asset | “Owner” today | Enforcement |
|-------|----------------|-------------|
| **`session_id`** | Whoever knows UUID | No server auth |
| **`case_id`** | Whoever knows UUID | No org binding on read paths |
| **`client_id`** | Config (`CLIENT_ID` env) + optional request field | Soft routing for copy/rules — not isolation |
| **Request trace** | `X-Request-ID` / generated UUID in middleware | Propagated on response header |

**Lineage stops:** at process boundary — no cross-service signed lineage yet.

---

## SUPPORT_MODEL

- **Gate:** `assert_support_export_authorized` (`support_export_gate.py`).  
- **Manifest:** `GET /api/inbox/support/deployment-manifest` — deployment + persistence + auth posture + request lineage + **tenant_truth** (this sprint).  
- **Case head:** `GET /api/inbox/support/case-head/{case_id}` — minimal metadata if key passes (or anonymous pilot).  
- **Gap:** Support key is **global per deployment**, not org-scoped.

---

## REPLAY_MODEL

- **Product replay:** Clients replay via normal triage + session APIs — same trust as product.  
- **Support “replay handoff”:** `case-head` exposes workflow/status — **not** full transcript redaction pipeline.  
- **Legal / immutable:** `audit_export.record_intake_case_mutation` forwards to `track_event` — **explicitly not WORM** (`audit_export.py` docstring).  
- **Gap:** No signed export bundle; no immutable audit chain.

---

## THREAT_MODEL

See **TOP_50_AUTH_AND_TENANCY_FAILURES** below.

---

## DEPLOYMENT_MODEL

- **`UNIFIED_INTAKE_PRODUCT_ONLY`:** Shrinks mounted routers; inbox + analytics + health remain (`deployment_profile.py`, `app_main.py`).  
- **`INTAKE_SCHEMA_EPOCH`:** Operator label for contract/schema generation — **not** a DB migration ID.  
- **Support posture:** Surfaced under `deployment_profile.auth_posture` on `/health` and support JSON.

---

## ROLLBACK_PLAN

| Change | Rollback |
|--------|----------|
| **Middleware / tenant_truth JSON** | Revert `request_identity.py`, `app_main.py`, `inbox_triage.py` support payloads; restore manifest version string if external consumers pin it |
| **Manifest version `support_export_v2`** | External ticket parsers expecting `support_export_v1` only — document bump or dual-read |

---

## MIGRATION_PLAN

1. **Now:** Runtime honesty (`tenant_truth`, state flags).  
2. **Next:** Persist optional `org_id` / `tenant_id` columns on `service_records` + dual-write when product commits to org truth.  
3. **Then:** API keys with **org scope** + rate limits per key.  
4. **Later:** JWT / IdP — **not** before org persistence + scoped support keys.

---

## TENANT_TRUTH_REALITY_MAP *(discovery)*

| Item | Classification |
|------|----------------|
| **`tenant_id` / authoritative tenant** | **Absent** — always null in new runtime API |
| **`X-Org-Id`** | **Client assertion** — copied to request state; documented untrusted (`support_export_gate.py`, `request_identity.py`) |
| **`org_id` in triage** | **Analytics / funnel metadata** — passed into `triage_inbox`, **not** persisted on case documents |
| **`client_id`** | **Product config slice** (handoff phrases, UI copy) — **not** a security boundary |
| **`deployment_profile` / `INTAKE_SCHEMA_EPOCH`** | **Deployment / contract slicing** — operator truth, not tenant RBAC |
| **Postgres `case_id`** | **Opaque primary key** in DB mirror — **no tenant column** in repository grep scope |

---

## AUTH_BOUNDARY_REALITY_MAP *(discovery)*

| Route class | Anonymous OK? | Notes |
|-------------|-----------------|-------|
| `POST /api/inbox/triage` | Yes | Core product |
| `GET /api/inbox/cases`, `GET /api/inbox/cases/{id}` | Yes | **Enumeration risk** — lists recent cases |
| `GET /api/inbox/session/{id}` | Yes | Session recovery |
| `GET /api/analytics/dashboard` | Yes | **Global funnel** — no tenant filter |
| `GET /api/inbox/support/*` | Yes **if** secret unset | **Dangerous** on public Internet |
| `GET /health`, `/healthz`, `/readyz` | Yes | Posture / phase leakage |
| Platform routes (non–product-only) | Mixed | Legacy lab/search surface |

**Capability leakage:** Health exposes persistence mode + schema epoch + auth posture — intentional for operators; reduces obscurity.

---

## REQUEST_OWNERSHIP_REALITY_MAP *(discovery)*

| Question | Answer |
|----------|--------|
| Who owns **case**? | **Storage layer** — first writer wins; API trusts `case_id` in path |
| Who owns **session**? | **Whoever holds `session_id` UUID** |
| Where **request lineage** ends? | Single process — `request_trace_id` from middleware |
| What **support** sees? | Whatever deployment key unlocks + **any** `case_id` guessed/leaked |
| What **operator** sees? | `/health`, logs, support manifest |

---

## SUPPORT_REPLAY_REALITY_MAP *(discovery)*

| Topic | Truth |
|-------|-------|
| **Replay truth** | Rule-based + LLM triage reproducibility — **not** bit-identical without frozen models |
| **Immutable gap** | No WORM; analytics/events are best-effort |
| **Legal replay gap** | No signed export; `future_export_bundle_keys` is a **checklist only** |
| **Escalation gap** | Support key is global — **cannot prove** “this org only” |
| **Lineage gap** | Support JSON includes `request_trace_id` + `tenant_truth` snapshot — **no** chain to customer consent record |

---

## TOP_50_AUTH_AND_TENANCY_FAILURES

1. Org spoofing via `X-Org-Id`  
2. Case enumeration (`GET /cases`)  
3. UUID guessing / brute force on large id space (mitigated only by entropy)  
4. Session hijack via leaked `session_id`  
5. Support replay abuse **without** org authorization  
6. Support key leak → full deployment manifest + any case-head  
7. Anonymous support surface on public pilot  
8. Tenant bleed via shared DB + no RLS  
9. Stale `INTAKE_SCHEMA_EPOCH` vs actual DDL  
10. Stale `support_export_manifest_version` consumers  
11. Leaked `request_trace_id` correlating tickets  
12. Leaked support export JSON in Slack/email  
13. Auth bypass by forgetting `assert_support_export_authorized` on new route  
14. Replay impersonation — caller claims prior case without proof  
15. Support impersonation — anyone with key acts as global operator  
16. Noisy neighbor — single deployment serves many brokers (future)  
17. Fake tenant illusion — UI shows “office” but server has no tenant  
18. Deployment mismatch — wrong Git SHA vs ticket  
19. **Org metadata never persisted** — cannot reconcile broker later  
20. **GET /cases** exposes cross-office queue in multi-broker deployment  
21. Analytics dashboard global buffer — cross-session visibility  
22. CORS `*` in dev — CSRF-like patterns from browser (limited by API shape)  
23. Attachment URLs guessable if ids leak  
24. `workbench_test` delete path — operational mistake deletes test case  
25. Rate limit absence — enumeration acceleration  
26. Logging middleware logs paths — case ids in logs  
27. Error responses include `request_id` — correlation aid for attacker  
28. Product-only vs full profile drift in incidents  
29. Dual-write off — JSON vs PG inconsistency replay confusion  
30. LLM non-determinism — “replay” disputes  
31. **Light identity** (`person_link_key`) — not cryptographic identity  
32. WeChat binding simulate endpoint — dev paths in prod if misconfigured  
33. `CLIENT_ID` env single-tenant demo assumption  
34. Shared Qdrant/collections — future multi-tenant noisy neighbor  
35. Health endpoint DDoS noise  
36. **No mTLS** internal service auth  
37. Missing **per-org billing** guardrails  
38. **No OCSP / key rotation** story for support API key  
39. Operator mistakes pasting manifest into public gist  
40. Schema migration without epoch bump — client replay breaks silently  
41. **Founder** holds support key — bus factor  
42. Edge cache misconfiguration exposing stale manifest  
43. **Webhook** (future) forgery without signing  
44. **Export** bundle signature alg placeholder only  
45. **GDPR** delete — not modeled  
46. **Subprocessors** list — not in runtime  
47. **Replay** dispute — no authoritative transcript hash  
48. **Multi-office** illusion — one deployment, one case list  
49. **Enterprise** IdP — explicitly out of scope  
50. **Zero-trust** internal RPC — not applicable yet  

---

## TENANT_TRUTH_V1 *(design)*

- **`tenant_id_authoritative`:** `Optional[str]` — null until token/key proves tenant.  
- **Org-bound ownership:** Persist `org_key` / `tenant_id` on case **when product commits**; until then, document “metadata-only”.  
- **RLS compatibility:** Reserve column names `tenant_id`, `org_id` on `service_records` in future migration; no implicit trust in headers.  
- **Deployment slicing:** Keep `deployment_profile` external to tenant row — config stays env-driven.  
- **Support compatibility:** Support responses include `tenant_truth` **for the HTTP request**, not for the case (case has no org yet).

---

## AUTH_BOUNDARY_V1 *(design)*

- **Request identity:** `request_trace_id` + optional `client_asserted_org_id` + null `tenant_id_authoritative`.  
- **API key ownership:** Single deployment support key → future **scoped keys** (`org_id` claim).  
- **Support scope:** Manifest + case-head — **global** today.  
- **Operator scope:** Health + logs — operational.  
- **Replay scope:** Product APIs + support metadata — **no** cryptographic replay seal.  
- **Org-bound access:** **Future** — must bind case rows + authorize queries.

---

## REQUEST_LINEAGE_V2 *(design)*

| Lineage | V1 today | V2 target |
|---------|----------|-----------|
| Request | `request_trace_id` | + parent span id if tracing backend |
| Support | same trace in support JSON | + support ticket id external ref |
| Replay | schema epoch + git sha | + transcript content hash |
| Deployment | `INTAKE_SCHEMA_EPOCH`, profile flags | + image digest |
| Schema | epoch string | + migration id |
| Actor | none | + `actor_type`: customer / broker / support_bot |

---

## SUPPORT_EXPORT_V3 *(design)*

- Redacted replay bundle  
- Support-safe export (PII rules)  
- Immutable metadata (WORM target)  
- Deployment lineage  
- Schema epoch lineage  
- Actor lineage  

**Today:** `support_export_v2` adds **`tenant_truth`** block — incremental step, not V3.

---

## AUTH_ROLLOUT_PLAN

| Stage | Action |
|-------|--------|
| **Backwards compatibility** | Additive JSON fields only; optional middleware |
| **Pilot** | Anonymous support OK only behind network ACL / VPN |
| **Product-only** | Same tenant_truth semantics |
| **Fallback** | Remove key env → anonymous (document risk) |
| **Migration** | Add DB columns → dual-write → enforce filters |
| **Partial rollout** | Per-environment keys; feature flags for “enforce org on case read” |

---

## PHASE 5 — REALITY SIMULATIONS

### 30-office simulation

| Scenario | Outcome |
|----------|---------|
| Angry broker | Disputes handoff — **no authoritative tenant** to adjudicate |
| Leaked `case_id` | Competitor reads case via **GET /cases/{id}** |
| Leaked support key | **Full manifest + any case-head** |
| Support impersonation | Global key — **cannot prove org** |
| Replay dispute | LLM variance — **no signed transcript** |
| Tenant confusion | Two offices, one deployment — **shared case list** |
| Stale deployment | Epoch/SHA mismatch in ticket — operator confusion |
| Org mismatch | Header says office A, case has **no org column** |
| Export leak | Paste JSON to client — **posture + trace leak** |
| Operator mistake | Deletes wrong test case — **limited** by `workbench_test` |

### 100-office simulation

All 30-office risks **amplified** + **noisy neighbor** on shared DB + **support queue overload** + **key rotation** pain + **analytics** useless without partition keys.

---

## PHASE 6 — VALIDATION *(2026-05-08)*

| Check | Result |
|-------|--------|
| `python3 -m compileall` (changed modules) | PASS |
| `pytest tests/` | PASS (100%) |
| `bash scripts/guardrail_inbox_triage.sh` | PASS |
| `npm run build` (`ui/`, Node **22.22** on PATH) | PASS |
| `npx madge --circular --extensions ts,tsx src` | **No circular dependency** |
| Default Node 20.18 on PATH | **Fails** Vite 7 — use Node 22+ per prior sprint docs |

---

## PHASE 4 — IMPLEMENTATION *(this repo)*

**Shipped (small / safe):**

- `IntakeClientAssertionMiddleware` + `IntakeTenantTruth` + `intake_tenant_truth()` in `services/fiqa_api/security/request_identity.py`  
- Middleware registration **before** `RequestIDMiddleware` so inbound order is CORS → RequestID → client assertion → …  
- `GET /health` `deployment_profile.tenant_truth`  
- `GET /api/inbox/support/deployment-manifest` and `case-head` include **`tenant_truth`**  
- `POST /api/inbox/triage` reads org from `request.state` with header fallback  
- **`support_export_manifest_version`:** `support_export_v2`  
- Tests: `test_deployment_profile.py`, `test_support_export_gate.py`  

---

## SELF_CRITIQUE

### TOP_30_REMAINING_SECURITY_GAPS

*(abbreviated — see THREAT 1–50)* — Top themes: **no authoritative tenant**, **global case list**, **global support key**, **no RLS**, **no rate limits**, **analytics global**, **no signed exports**, **LLM non-determinism**, **org not persisted**, **health info disclosure**, **log leakage**, **single deployment multi-broker illusion**.

### TOP_20_FAKE_TENANT_PATTERNS

1. Treating `X-Org-Id` as proof  
2. Calling `client_id` a tenant  
3. Assuming `case_id` implies customer auth  
4. Assuming product-only mode adds tenant isolation  
5. Using schema epoch as tenant boundary  
6. Using Git SHA as org identity  
7. Believing support manifest proves customer consent  
8. Believing analytics sessions imply one broker  
9. Mapping `person_link_key` to legal identity  
10. Trusting WeChat simulate path in prod  
11. Using env `CLIENT_ID` as security boundary  
12. Confusing deployment profiles with authz  
13. Expecting RLS from Postgres URL alone  
14. Thinking triage rules enforce tenancy  
15. Thinking attachments are per-tenant encrypted  
16. Using session id as authentication  
17. Believing `workbench_test` flag protects prod cases  
18. Thinking CORS origins equal tenant isolation  
19. Expecting `request_trace_id` to be secret  
20. Treating sprint docs as runtime enforcement  

### TOP_20_SUPPORT_RISKS

Global key; anonymous pilot; case-head without org check; manifest leakage; ticket paste exposure; no scoped keys; no rotation; no audit of key usage; founder-held secret; no SOC2 workflow; attachment paths; dispute resolution; SLA confusion; multi-tenant future pricing; customer visible operator mistakes; escalation to eng without triage; PII in logs; third-party Slack integrations; email forwarding of exports; stale manifest in ticket.

### TOP_20_REPLAY_GAPS

No signed transcript; LLM drift; model version not in case JSON; no hash of customer text; support replay missing bodies; no time-travel DB; dual-write skew; schema epoch vs code mismatch; no legal hold flag; no export encryption; no customer approval; no broker approval; no retention TTL; no redaction pipeline; no fork/rebase metaphor; no deterministic fixture replay in prod; no cross-region replay; no checksum on attachments; no witness cosignature; no chain of custody.

### TOP_20_OPERATOR_DEPENDENCIES

Founder config; manual key distribution; manual epoch communication; manual Cloud Run URL management; env var discipline; Runbook adherence; log grep skills; dispute mediation; customer comms; broker training; demo vs prod discipline; Node version on PATH; DB credential rotation; Qdrant health interpretation; embedding warmup patience; GPU worker optional confusion; product-only toggle understanding; support ticket hygiene; git SHA correlation; incident severity judgment.

### TOP_20_NOT_ENTERPRISE_READY_AREAS

Tenant authority; org persistence; RLS; scoped API keys; SSO; audit log immutability; SIEM integration; DPA/GDPR tooling; pen test cycle; bug bounty; rate limiting; WAF; SOC2; multi-region; encryption at rest policy; key management service; data residency; contractual SLA; formal RBAC; vendor risk program.

---

## FINAL_DECISION

**Adopt** a **honesty-first tenant truth layer**: nullable authoritative tenant, explicit semantics strings, request state for `X-Org-Id`, and support/health JSON extensions — **without** claiming multi-tenant isolation. **Defer** RLS, org-scoped keys, and persisted org on cases until a dedicated schema + migration sprint.

---

## FINAL_ONE_LINE

**Unified Intake now admits the truth: there is no server-side tenant authority yet—only client assertions, UUID possession, and an optional support secret—so we surface that honestly in runtime APIs while laying nullable hooks for real IAM.**

---

# FINAL OUTPUT *(also printed in sprint completion — mirror below)*

See **§ FINAL OUTPUT (printed)** in chat response.
