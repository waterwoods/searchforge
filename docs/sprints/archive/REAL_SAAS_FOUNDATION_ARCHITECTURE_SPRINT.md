# REAL_SAAS_FOUNDATION_ARCHITECTURE_SPRINT

**SSOT ID:** `REAL_SAAS_FOUNDATION_ARCHITECTURE_SPRINT`  
**Date:** 2026-05-07  
**Repo:** `searchforge`  
**Discovery method:** live code + config read + test/guardrail execution in this workspace  
**Branch context:** default workspace (not branch-pinned in doc)

---

## OBJECTIVE

Characterize SearchForge **Unified Intake / Inbox Triage pilot** exactly as runtime + persistence + tenancy + replay + deployment behave **today**, and document what is **honest SaaS foundation** versus **demo/lab coupling** versus **illusion** (marketing surface without authority). Produce operator/support/replay truth and a prioritized foundation backlog for **30–100+ offices**.

---

## NON_GOALS

- Building multi-tenant RLS, production IdP SSO, Stripe, or enterprise SOC2 controls in this sprint.
- “AI moat” features; scope is foundation truth, not cleverness.
- Claiming HIPAA/SOC/GDPR compliance from analytics hooks or scaffolding.
- Treating HTTP headers (`X-Org-Id`) or `client_id` strings as cryptographic tenant boundaries without auth.

---

## SYSTEM_REALITY_MAP

| Layer | Evidence (repo) | Runtime truth |
|-------|-----------------|---------------|
| **Entrypoint** | `services/fiqa_api/app_main.py` | Single FastAPI app; heavy startup (clients, bm25, embedding warmup via lifespan); routers gated by deployment profile |
| **Default scope (AGENTS.md)** | `AGENTS.md` L73–74 | Explicitly **out of scope:** Stripe, auth, multi-tenant |
| **Port / Cloud Run** | `Dockerfile.cloudrun` CMD + `PORT=8080` | uvicorn binds `host 0.0.0.0`, `PORT` from env; healthcheck uses **`/health/live`** (NOT top-level `/healthz` reliably on Cloud Run per inline comment) |
| **Product-only gate** | `deployment_profile.py` `UNIFIED_INTAKE_PRODUCT_ONLY` | Env flag **reduces mounted routers**; platform stack excluded when `true` (`app_main.py` ~L910+) |
| **Always mounted (product surface)** | `app_main.py` | `inbox_triage_router` (`/api/inbox/*`), `analytics_dashboard_router` |
| **Frontend product route** | `ui/src/App.tsx` | Unified Intake at `/workbench/unified-intake` **inside** same SPA as RAG labs, jobhunter, codemap |
| **Readiness ambiguity** | `app_main.py` `/ready`, `/readyz`, periodic embed promotion | Embedding + vector “ready” is **eventually consistent** tasks; Unified Intake may still run while phase is degraded for search stack |
| **Static SPA mount** | `app_main.py` ~L1007+ when `frontend/dist` exists | If present, catches non-API paths — **dual personality** vs `ui/` Vite dev |
| **Session persistence** | `session_repository.py` | **Without** `SERVICE_RECORD_DATABASE_URL`/`DATABASE_URL`: sessions effectively **gone** unless `UNIFIED_INTAKE_ALLOW_INMEMORY_SESSIONS_FOR_TESTS` (tests only) |

---

## TENANCY_REALITY_MAP

| Concept | Authority | SaaS verdict |
|---------|-----------|--------------|
| **`client_id`** | Request body + env default `config_loader.get_active_client_id`; persisted on case rows | **Config lane / brand pack**, NOT authenticated office identity |
| **`X-Org-Id`** | `inbox_triage.py` Header → **`org_id`** → analytics / metadata only (`_schedule_route_analytics`, case dict optional `org_id`) | **Unauthenticated attribution** → **spoofable** |
| **`org_id` in DB schema** | Grep across `service_record_repository` / migrations in spirit: **no `org_id` column** documented in prior sprint; still true for case/session rows inspected via settings | **No row-level tenant key** enforced in persistence |
| **Cross-tenant isolation** | Same deployment + knowing `session_id` / `case_id` | **No cryptographic boundary**: knowledge of identifiers is authorization |
| **WeChat binding** | Query params `session_id`, `client_id`; state signed (`wechat_binding.py`) | Binds identity to session **for that flow**, not enterprise IAM |

**Truth:** tenancy today is **`deployment slicing`** (one customer per backend + env vars) plus **opaque IDs**, **not** SaaS tenancy.

---

## AUTH_REALITY_MAP

| Mechanism | Location | Reality |
|-----------|----------|---------|
| **End-user broker auth** | Not present | **None** |
| **API bearer / OAuth for triage** | Not present | **Open POST** `/api/inbox/triage` in typical deployments unless wrapped by gateway |
| **WeChat OAuth** | `inbox_triage.py` `/wechat/*` | Optional; scoped to linking person to session pack |
| **Support endpoints** | `GET /api/inbox/support/deployment-manifest`, `GET /api/inbox/support/case-head/{case_id}` | **Unauthenticated** in code shown — caller must rely on perimeter |

Verdict: **no real auth** inside application trust boundary — perimeter must enforce access if any sensitivity exists.

---

## REPLAY_REALITY_MAP

| Surface | Capability | Limits |
|---------|------------|--------|
| **Deterministic replay (tests)** | `scripts/run_multi_turn_simulations.py`, `tests/` | Rule/LLM-off packs; proves **intent engine**, not full LLM stochastic replay |
| **Role C replay** | `role_c_simulation_service.py`, routes in `inbox_triage.py` | Simulated customer; bounded turns |
| **Support “replay” aid** | `GET /support/case-head/{case_id}` | **Metadata only** (explicitly **no message bodies**) |
| **`source_text`** in PG | Comment in `service_record_repository.py` (~L778) | Queue skim — **not** full transcript |
| **Audit export scaffolding** | `audit_export.py` | Forwards **`track_event` only**; docstring forbids compliance claims |

Verdict: **no enterprise-grade deterministic production replay bundle** keyed by immutable audit lineage.

---

## OPERATOR_REALITY_MAP

| Workflow | Exists? | Gap |
|----------|---------|-----|
| **Know deployed SHA** | `GET /version`, `GET /healthz`, `/api/inbox/support/deployment-manifest` | Git SHA vs image tag discipline is **deployment process**, not cryptographic |
| **Know persistence posture** | `GET /health` includes `unified_intake_case_persistence` (`service_record_settings.unified_intake_case_persistence_report`) | ✅ strong operator honesty |
| **Know schema epoch** | `deployment_profile.INTAKE_SCHEMA_EPOCH` surfaced on manifest + `/health` (this sprint change) | Manual bump discipline required |
| **Onboarding without founder** | Client pack dirs under `configs/clients/` + env | Requires **engineering** — no self-serve provisioning API |
| **Rollback** | Feature flags/env (`*_WRITES`, `JSON_*`) documented in settings | Operational runbooks exist elsewhere; **not** one-click safer for non-engineers |

---

## SUPPORT_REALITY_MAP

| Capability | Evidence | Risk |
|------------|----------|------|
| **Deployment manifest** | `support_deployment_manifest` | **Public if API is open** → leak build fingerprint + persistence mode → low PII risk, high infra intel |
| **Case head export** | `support_case_head` | **Anyone with case UUID** may read headline metadata unless gateway blocks |
| **Explain “why AI said X”** | No structured rationale store | **Absent** beyond latest triage outputs |
| **Ticket-grade export** | Not implemented (`future_export_bundle_keys` in `audit_export.py`) | Legal hold / GDPR export **missing** |

---

## DEPLOYMENT_REALITY_MAP

| Topic | Evidence | Truth |
|-------|----------|-------|
| **Cloud Run Dockerfile** | `services/fiqa_api/Dockerfile.cloudrun` | `GIT_SHA` build-arg; HEALTHCHECK curls **`/health/live`** |
| **Cloud Run `/healthz` gotcha** | `app_main.py` `api_healthz_cloud_run_safe` | Documented GCP HTTP frontend mismatch for bare `/healthz` |
| **Product-only CI honesty** | `deployment_profile.log_deployment_profile_banner` | Startup log states profile |
| **Node/UI build gate** | `ui` Vite — this workspace `npm run build` **failed** on Node **20.18.2** (requires **≥20.19**): environment truth for CI |
| **`ready` coupling** | `ready()` checks embed + vector | Unified Intake may be **orthogonal** to “search ready” semantics |

---

## DOUBLE_BRAIN_MATRIX_V3

| # | Dimension | Brain A | Brain B | Typical conflict |
|---|-----------|---------|---------|-------------------|
| 1 | Case truth | Postgres `service_records` | JSON case files (`unified_intake_case_persistence_report` modes) | Read-your-writes / dual-write skew |
| 2 | Session truth | Postgres `intake_sessions` | In-memory (**tests only**) or none | Restart drops sessions |
| 3 | **Product SKU** | Unified Intake page + `/api/inbox/*` | Entire SPA + platform API surface | Overselling “product” vs “research stack” |
| 4 | **Deployment profile** | `UNIFIED_INTAKE_PRODUCT_ONLY` | Platform-full default | Wrong env → unintended attack surface |
| 5 | **Office identity** | `client_id` pack | Caller-supplied `client_id` + `X-Org-Id` | Wrong attribution / spoof |
| 6 | **Replay truth** | Test harness | Prod DB row shape | Cannot reproduce conversational LLM traces |
| 7 | **Health semantics** | `/ready` (embed/search) | Case persistence readiness | Healthy search but PG misconfigured |
| 8 | **Git identity** | `get_git_sha()` | Container `GIT_SHA` env | Mismatch when tag not injected |

---

## PRODUCT_ONLY_SURFACE_MAP

When **`UNIFIED_INTAKE_PRODUCT_ONLY=1`** (`deployment_profile.py`):

- **Included:** inbox API, analytics dashboard, health/Qdrant routes as mounted in `app_main.py`, **`/health`**, **`/version`**, SPA static if bundled.
- **Excluded:** debug, search, query, labs, steward, orchestration, kv experiment, ecommerce, jobhunter, code lookup, codemap graphs, ops routers, experiment orchestration defaults.
- **Inline platform routes:** only registered **`if not`** product-only via `platform_inline_routes.register_platform_inline_routes` (`deployment_profile.PLATFORM_INLINE_ROUTES_UNGATED_IN_APP_MAIN` is **empty** tuple — leak count **0**).

---

## TRUST_BOUNDARY_MAP

```
[ Browser / Broker ]
        │
        │  (typically NO app-level auth ─ open API unless gateway wraps)
        ▼
┌──────────────────── FastAPI services.fiqa_api.app_main ────────────────────┐
│  Trusted by default INSIDE boundary: ENV secrets, DATABASE_URL,               │
│  file-system JSON cases, embeddings, Redis/Qdrant as configured.           │
│  NOT verified: X-Org-Id, arbitrary client_id, case_id guesses.             │
└─────────────────────────────────────────────────────────────────────────────┘
        │
        ▼
[ Postgres │ JSON artifacts │ Vector store │ External LLM │ WeChat OAuth ]
```

**Founder dependence:** configuring env, client packs, deployments, interpreting persistence mode — **still high**.

---

## SaaS_MATURITY_SCORECARD (0–5, brutal)

| Pillar | Score | Note |
|--------|-------|------|
| **Tenant isolation** | 0–1 | Deployment slice only; header “org” is analytics |
| **AuthN / AuthZ** | 0 | None in-app |
| **Data durability clarity** | 3 | `unified_intake_case_persistence_report` is unusually honest |
| **Observability** | 2 | trace_id patterns exist; enterprise audit trail incomplete |
| **Replay / lineage** | 1 | Metadata-only support + scaffolding |
| **Operator ergonomics** | 2 | Manifest + persistence report; provisioning is manual |
| **Deployment honesty** | 3 | Profiles, health gotchas documented, SHA surfacing |
| **Support safety** | 1 | Unsigned unauthenticated metadata endpoints |

**Weighted judgment:** pilot **engineering system** leaning research platform; **not** multi-tenant SaaS.

---

## TOP_100_FAILURE_MODES

1–10 **Tenancy spoofing:** 1 spoof `X-Org-Id`; 2 mix two offices on same env; 3 guess sequential `case_id`; 4 session fixation; 5 share browser profile across offices; 6 wrong `CLIENT_ID` env; 7 stale client pack deployed; 8 A/B handoff bleed across packs; 9 operator assumes `client_id` is IAM; 10 GDPR processor thinks org header is proof of tenant.

11–20 **Auth perimeter:** 11 public triage abused; 12 support manifest scraped; 13 case-head enumerated; 14 analytics spam; 15 prompt injection amplified; 16 WeChat simulate left on; 17 CORS wildcard in legacy apps; 18 missing gateway rate limits; 19 bot flood on append; 20 attachment upload path misuse.

21–30 **Persistence brain split:** 21 JSON-write + PG-read mismatch; 22 PG primary reads off during dual-write lag; 23 restart with in-memory sessions “enabled by mistake”; 24 no DB URL in prod silently; 25 dual-write halfway migration; 26 JSON fallback masks PG corruption; 27 two replicas write JSON local FS (if ever mounted RW); 28 clock skew `updated_at`; 29 partial migration orphan rows; 30 backup restores wrong order.

31–40 **Replay / explainability:** 31 cannot rebuild LLM prompt; 32 case metadata without transcript insufficient; 33 legal asks for verbatim thread; 34 “why append merged?” unexplained without internal logs; 35 model routing changed mid-case; 36 temperature nondeterministic; 37 assist layer differs by build; 38 OCR sidecar divergence; 39 role-c sim confused with prod data; 40 missing schema epoch on diagnosis (mitigated partially now).

41–50 **Deployment:** 41 wrong Dockerfile path; 42 `GIT_SHA` not injected; 43 health probes hit wrong path; 44 product-only=false in prod unintentionally; 45 platform routes exposed publicly; 46 Cloud Run concurrency mis-tuned CPU; 47 embedding warmup OOM; 48 vector down blocks `/ready`; 49 UI CDN serves old SPA; 50 backend/frontend semver skew.

51–60 **Operator / onboarding:** 51 new office needs founder to edit configs; 52 pack mismatch contract; 53 copy QA per client unsystematized; 54 WeChat prod credentials mix; 55 ENV typo `UNIFIED_INTAKE_DB_PRIMWRITES`; 56 playbook missing rollback; 57 no tenant provisioning checklist; 58 support trained on illusion of auth; 59 L1 guesses case UUID; 60 escalations bottleneck on founder.

61–70 **Support overload:** 61 duplicate tickets same case; 62 cannot correlate sessions; 63 export manual screenshots; 64 SLA timer missing; 65 language barrier; 66 angry broker + no audit trail pacifies poorly; 67 cross-office mis-triage escalation; 68 attachment virus scan absent; 69 PII in logs; 70 retention policy undeclared.

71–80 **Enterprise legal:** 71 DSR deletion undefined; 72 subprocessors list missing; 73 data residency unknown; 74 encryption-at-rest assumed; 75 key rotation story weak; 76 contract says SOC2 facts not evidenced; 77 AI disclaimer gap; 78 cross-border transfer for LLM vendor; 79 evidentiary chain for screenshots; 80 BAAs absent.

81–90 **Scaling / product coupling:** 81 monolith SPA couples labs with intake SKU; 82 single Postgres instance noisy-neighbor risk; 83 long transactions on triage path; 84 LLM latency tail vs broker expectations; 85 per-tenant cost metering absent; 86 feature flags ad hoc; 87 schema migrations without blue/green pairing; 88 content pack drift undetected; 89 regional latency unmanaged; 90 multi-office rollup analytics conflation.

91–100 **Econ, abuse, founder catastrophe:** 91 token budget runaway; 92 abuse detection absent; 93 cache poisoning on embedding inputs; 94 vector collection name mismatch across envs; 95 single key holder for production deploy; 96 on-call undocumented; 97 runbook staleness after rapid sprints; 98 operational knowledge tribal; 99 new hire cannot safely operate env matrix; 100 bus factor on client pack authoring (`configs/clients/`).

---

## TOP_50_MISSING_CAPABILITIES

1 Real IdP SSO + session cookies  
2 Scoped API tokens per office  
3 Row-level **`tenant_id`** in DB + enforced on every query  
4 Immutable append-only **`audit_events`** store  
5 Signed support export payloads  
6 **PII-aware** logging redactor  
7 **Rate limiting** tiering  
8 Abuse detection dashboards  
9 **Deterministic replay** bundles (prompt+model ver+inputs hash)  
10 **Data retention jobs** implemented  
11 **Right-to-erasure workflow** documented + automated  
12 **SLA dashboards**  
13 Formal **SLO/error budget**  
14 Separate **SKU hosting** boundary (trim SPA)  
15 **Self-serve tenant provisioning API**  
16 **Billing metering** hooks  
17 **Role-based workspace** separation  
18 **SOC2-aligned** control matrix  
19 **Pen test** remediation loop  
20 **Secrets rotation** playbook  
21 **Multi-region failover** stance  
22 **Canary deploy** semantics matched to `/health`  
23 **Synthetic monitoring** vs real broker flows  
24 **Support impersonation WITH audit & consent**  
25 **Case transcript export** standardized  
26 **Attachment malware scanning** policy  
27 **LLM fallback** deterministic mode for regulated scenarios  
28 **Version negotiation** header for triage contract  
29 **Schema migration orchestration** tooling  
30 **Customer-visible status page**  
31 Office-level **RBAC for support tools**  
32 **Encryption scopes** documented  
33 **Vendor DPA inventory** automated  
34 **Model changelog** surfaced to brokers  
35 **Customer org hierarchy** mapping  
36 **Multi-office rollup analytics** authenticated  
37 **Pack validation gate** mandatory in CI (partial exists elsewhere)  
38 **Incident response** tabletop  
39 **Secrets scanning** enforced  
40 Dependency **SBOM publishing**  
41 **Feature flag service** persisted  
42 **Distributed tracing sink** enforced  
43 **Correlation ID** propagated UI→API→DB  
44 Worker queue for exports  
45 Replay **for append merge decisions** rationale field  
46 **Contract tests** frontend↔OpenAPI authoritative  
47 **Load test** triage SLA  
48 **Disaster recovery** tested restore  
49 **Cost caps** per customer  
50 **Executive dashboard** truthful vs flattering metrics  

---

## TOP_30_FOUNDATION_MOVES (prioritized low-regret)

1 **Perimeter gateway** authentication for all mutating inbox routes (+ support tools).  
2 **Stop treating `X-Org-Id` as tenant**: rename to **`client_attribution_hint`** internally or gate behind signed tokens.  
3 **Add `tenant_id` column nullable** → later backfill migration (no RBAC fantasies upfront).  
4 **Require API key** minimum for **`/support/*`** endpoints.  
5 **Append-only audit table** wired from `audit_export.record_intake_case_mutation` path.  
6 **Trim SPA SKU surface** deploy separate static host for Unified Intake.  
7 **CI gate**: product-only Dockerfile args + **`npm` version pin** enforced.  
8 **Operational runbook**: persistence mode escalation tree.  
9 **Signed export MVP** ZIP with manifest + hashed transcript subset.  
10 **Rate limits** baseline on triage POST.  
11 **`/ready`** split: **`/ready/intake`** vs `/ready/embeddings`.  
12 **Observability**: structured logs with `session_id`,`case_id` hashes only.  
13 **Formalize CLIENT pack semver** in manifest.  
14 **Dual-write retirement plan** single brain for cases.  
15 **Support UI** internal read-only with auth.  
16 **Replay harness** seed fixture per release tag.  
17 **Drift detection** pack vs env `CLIENT_ID`.  
18 **Pen test** scope statement honest.  
19 **Data map** PII fields inventory.  
20 **LLM config freeze** file per deploy in manifest.  
21 **Feature flag service** even if simple JSON in DB.  
22 **Escalation workflow** L1/L2 defined.  
23 **Customer comms** template for AI limitations.  
24 **Cost meter** per request token counts stored.  
25 **Branch protection** + required guardrails (already strong—extend to deploy).  
26 **Kubernetes/Cloud Run** min instances for tail latency.  
27 **Attachment storage** object store with signed URLs.  
28 **Multi-office analytics** require auth + org from token.  
29 **Contract version** increment automation on OpenAPI diff.  
30 **Founder checklist** automated into script with exit codes.

---

## 50_ENTERPRISE_OFFICE_SIMULATIONS

| # | Scenario | Expected today | Failure / stress |
|---|----------|----------------|------------------|
| 1 | Angry broker demands quote now | Triage may hand off | No SLA clock |
| 2 | Wrong vehicle thread | Engine attempts correction | No locked identity record |
| 3 | Replay request for last week | `/support/case-head` only | No transcript |
| 4 | Legal export | None | Manual engineering |
| 5 | Tenant bleed fear (two offices) | Same deployment sees both if IDs known | No isolation |
| 6 | Support escalation | Slack to founder | No ticket system linkage |
| 7 | Billing dispute | Out of scope | Stripe absent |
| 8 | Onboarding failure (bad env) | `MIXED_STATE` persistence modes | Operators misread `/health` |
| 9 | Pack mismatch (`client_id`) | Wrong copy | QA burden |
| 10 | Contract says dedicated DB | Might still be JSON | Legal mismatch |
| 11 | Rollback after bad deploy | Redeploy old image | No automated blue/green coupling |
| 12 | Audit “who changed status” | Activity partial | Not immutable |
| 13 | Why AI said this | No rationale store | Support improvises |
| 14 | Why case changed | Derived lifecycle | Hard to narrative |
| 15 | Why append merged | Boundary heuristics | Black box to L1 |
| 16 | Operator turnover | Few runbooks | Risk |
| 17 | Support overload | No triage SLA | Cascading backlog |
| 18 | Founder OOO deploy | Possibly blocked | Bus factor |
| 19 | Deployment mismatch frontend/backend | Observable via errors | SKU packaging weak |
| 20 | ENV mismatch staging/prod flags | Persistence surprise | Incident |
| 21 | Wrong runtime (platform-full exposed) | Security widening | Compliance failure |
| 22 | Stale pack | Cached config | Wrong rules |
| 23 | Client override drift vs repo | Editing server files | Divergence |
| 24 | Multi-office growth 5→30 | Operational load | Thin tooling |
| 25 | Enterprise questionnaire security | Mostly “no” answers | Lose deal honestly |
| 26 | PII in analytics | Depends on payloads | Potential leak |
| 27 | Data retention ask | Undefined | Stall |
| 28 | Deletion request | Undefined | Stall |
| 29 | Export all data | Undefined | Stall |
| 30 | Compliance SOC2 | Minimal controls | Stall |
| 31 | SLA 99.9% | No basis | Negotiation loss |
| 32 | Replay lineage | Git SHA only partial | Incomplete |
| 33 | Deterministic replay | Tests only | N/A prod |
| 34 | Branch mismatch local vs prod | Happens daily | Debugging tax |
| 35 | Release mismatch UI/API | SPA old bundle | Weird bugs |
| 36 | Auth spoof attempt | Mostly succeeds inside perimeter | Disaster |
| 37 | Spoof `X-Org-Id` | Accepted | Attribution lies |
| 38 | Support views wrong tenant | No auth walls | Incident |
| 39 | Insider threat export | Reads case metadata | Sensitive |
| 40 | DMV/SR‑22 tangent | Routed | Complexity |
| 41 | OCR wrong VIN | Trust bugs possible | Litigation fear |
| 42 | Duplicate cases same customer | Merge heuristics | Broker confusion |
| 43 | Attachment malware | Likely unscanned | IT blocks feature |
| 44 | Concurrent edits two agents | Race potential | Strange states |
| 45 | Midnight cron job DB down | Depends on infra | Drops writes |
| 46 | Postgres failover | Untested hypothesis | Loss |
| 47 | Embedding model update mid-day | Semantic drift hard to isolate | Replay impossible |
| 48 | Lawyer demands model card | Possibly informal | Procurement delay |
| 49 | Procurement reviews subprocessors | Incomplete list | Block |
| 50 | Acquire firm wants merge analytics | Attribution spoofable | Bad business intel |

---

## SELF_CRITIQUE_REPORT_V4

**What we still fake**

- Pretense that optional org header constitutes tenant provenance anywhere except marketing slides.
- Conflation of **`client_id` pack lane** with “office authenticated user.”

**Still dangerous**

- Open **`/support/*`** metadata leakage surface if perimeter absent.
- Dual-brain persistence (JSON vs Postgres) transitional paths without strict ops policing.

**Founder-only today**

- Client pack authoring + env matrix decisions; correcting mis-deployed profile flags; interpreting persistence mode anomalies.

**Non-SaaS**

- Single SPA hosting platform labs beside paying SKU collapses positioning and ACL story.

**30-customer breakage**

- Support volume without ticketing + export tooling; spoofed analytics confusing growth metrics.

**100-customer breakage**

- DB isolation absent; noisy neighbor cost; impersonation/abuse unmanaged.

**Enterprise scrutiny**

- No IAM, SBOM-lite only, vague subprocessors stance, no SOC mapping.

**Legal scrutiny**

- Retention/export/deletion story incomplete; transcript authority unclear.

**Support overload collapse**

- L1 lacks transcript export + deterministic replay slices; escalation to founders becomes default policy.

---

## FINAL_DECISION

**Freeze the fiction:** externally sell this as **“single-tenant managed pilot platform with optional PG durability + strong engineering visibility into persistence mode”**, not multitenant SaaS.

**Investment order:** perimeter auth → real `tenant_id` + RLS-shaped query discipline → immutable audit append → signed exports → SKU-split UI deployments.

---

## FINAL_ONE_LINE

**SearchForge Unified Intake is a powerful domain-specific triage engine with unusually honest persistence telemetry, embedded in a broader research/monolith codebase, lacking in-application identity or row-level tenancy—so SaaS readiness is “infra-sliced pilot,” not multitenant SaaS, until perimeter auth and authoritative tenant-bound persistence land.**

---

## IMPLEMENTATION_DELTA (THIS SPRINT, CODE)

### `INTAKE_SCHEMA_EPOCH` surfaced

- **`services/fiqa_api/deployment_profile.py`** — constant `INTAKE_SCHEMA_EPOCH` + accessor `intake_schema_epoch()`
- **`GET /health`** (`app_main`) — nested under `deployment_profile.intake_schema_epoch`
- **`GET /api/inbox/support/deployment-manifest`** — field `intake_schema_epoch`
- **`GET /api/inbox/support/case-head/{case_id}`** — field `intake_schema_epoch`

### Validation executed (workspace)

| Check | Result |
|-------|--------|
| `python3 -m compileall` touched modules | ✅ |
| `pytest tests/test_deployment_profile.py` | ✅ |
| **`pytest tests/`** full tree | ✅ (DeprecationWarning unrelated) |
| `bash scripts/guardrail_inbox_triage.sh` | ✅ PASS |
| `npm run build` (`ui`) | ❌ blocked: Node **20.18.2** < Vite required **≥20.19** |

---

## EVIDENCE_INDEX (PRIMARY FILES)

- `services/fiqa_api/app_main.py` — routers, `/health`, product-only branching, SPA mount, Cloud Run health commentary  
- `services/fiqa_api/deployment_profile.py` — `UNIFIED_INTAKE_PRODUCT_ONLY`, `INTAKE_SCHEMA_EPOCH`, inline route leak inventory  
- `services/fiqa_api/routes/inbox_triage.py` — triage POST, **`X-Org-Id`**, support manifest, persistence writes, analytics scheduling  
- `services/fiqa_api/db/service_record_settings.py` — Postgres/JSON posture matrix  
- `services/fiqa_api/inbox_triage/session_repository.py` — durable vs test-only sessions  
- `services/fiqa_api/inbox_triage/audit_export.py` — non-compliance explicit  
- `AGENTS.md` — declared out-of-scope: auth, multitenant  
- `services/fiqa_api/Dockerfile.cloudrun` — Cloud Run conventions  
- `ui/src/App.tsx` — SKU vs lab route coupling  

---

*End SSOT.*
