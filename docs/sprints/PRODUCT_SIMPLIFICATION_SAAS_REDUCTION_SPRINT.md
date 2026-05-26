# Product Simplification + SaaS Reduction Architecture Sprint — SSOT

**Authority:** This is the **only** authority for this sprint. Supersedes overlapping sprint narratives for reduction decisions; do not fork parallel “minimal SaaS” SSOTs without merging here first.

**Date:** 2026-05-23  
**Branch (inventory):** `sprint/scoped-broker-identity-office-operational-safety`  
**Philosophy:** Reduction + convergence + productization — **not** platform expansion.

---

## PHASE 0 — Git + inventory

### Git state (2026-05-23)

| Item | Value |
|------|--------|
| **Branch** | `sprint/scoped-broker-identity-office-operational-safety` |
| **HEAD** | `f14f755` — sprint: pilot SaaS survivability — deployment drift warnings + SSOT |
| **Dirty tree** | **Yes** — ~30 modified tracked files (inbox, security, deployment_profile, tests, UI intake); **~40+ untracked** sprint docs under `docs/sprints/`; **~35 untracked** `results/*.json|md`; new `services/fiqa_api/security/`, migrations, scripts |
| **Stashes** | **16** stashes on old branches (`frontend-phase1`, `resolver-*`, `latency-*`, `pg-*`, etc.) — **coexistence risk** when popping without branch context |
| **Coexistence risks** | Parallel sprint branches + stashes may reintroduce removed flags (`USE_RESOLVER_ONLY`), dual routing, or stale env bundles; **untracked sprint docs contradict each other** on wiring state (resolver, composer no-ops) |

### Sprint-document sprawl

| Metric | Count / note |
|--------|----------------|
| `docs/sprints/*.md` | **114+** files |
| Overlapping “minimal/real/future SaaS” SSOTs | **20+** untracked on current branch (e.g. `MINIMAL_PAID_SAAS_SURVIVABILITY`, `REAL_SAAS_FOUNDATION`, `FUTURE_SAAS_OPERATING_SYSTEM`, `HUNDRED_OFFICES_*`, `PAID_SAAS_OPERATING_MODEL_*`) |
| `results/*.md` time-sliced reports | **15+** FINAL/LATENCY/RESOLVER reports — **not** operator truth |
| Recommended doc truth | `AGENTS.md` → `PROJECT_DOC_SYSTEM_MAP.md` → **`UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md`** → this sprint SSOT for **reduction** |

### Overlapping architecture layers (honest stack)

```
[ Customer / broker UI: Unified Intake + legacy RAG demo ]
        ↓
[ FastAPI app_main — product_only vs platform_full ]
        ↓
[ /api/inbox/*  +  /api/analytics/*  +  health/Qdrant  +  (platform) 15+ legacy routers ]
        ↓
[ Security perimeter: optional intake key, support key, broker HMAC token, X-Org-Id hints, rate limit ]
        ↓
[ Orchestration: routes/inbox_triage.py (2.1k lines) → triage.py (6.4k lines) ]
        ↓
[ Persistence fork: Postgres service_records + intake_sessions  ||  JSON cases  ||  in-memory sessions ]
        ↓
[ PG vehicle entities + case_truth_repository facade + session_store ]
```

**Code mass (indicative):** `triage.py` 6,426 lines; `routes/inbox_triage.py` 2,119; `app_main.py` 1,126; **221** Python files under `services/fiqa_api`.

---

## PHASE 1 — Product truth discovery

### Classification key

| Class | Meaning |
|-------|---------|
| **A** | CORE PRODUCT — paid pilot value |
| **B** | SUPPORTING FOUNDATION — required to ship/support |
| **C** | OPTIONAL — useful but not SKU |
| **D** | PREMATURE — built before revenue justifies |
| **E** | ENTERPRISE THEATER — looks like platform, isn’t |
| **F** | RESEARCH/LAB — experiments, chaos, simulation |
| **G** | DANGEROUS COMPLEXITY — high regret if touched wrong |
| **H** | FOUNDER TRAP — burns Andy without customer $ |

### Major capabilities

| Capability | Class | Customer value | Burden |
|------------|-------|----------------|--------|
| Unified Intake add-car triage + handoff | **A** | High — wedge | Route + triage monolith |
| Broker workbench (case list, status, notes) | **A** | High | UI surface area |
| Session continuity (`session_id`, binding) | **A** | High | Dual session backends |
| Case / service record persistence | **A** | High | JSON+PG matrix |
| PG vehicle entity truth | **A** | High (when PG on) | Resolver not wired; N+1 risk |
| Client pack / lane copy (`chen_kui`, etc.) | **A** | High | Config drift vs deploy |
| Standard 7-scenario demo package | **A** | High (sales) | Guardrail maintenance |
| `UNIFIED_INTAKE_PRODUCT_ONLY` router shrink | **B** | Indirect — deploy honesty | Must be default in prod |
| Health / readiness / deployment-manifest | **B** | Ops | Key rotation discipline |
| Minimal signed broker token (HMAC) | **B** | Pilot perimeter | Secret + binding ops |
| Intake + support API keys | **B** | Coarse auth | False sense of tenancy |
| `deployment_profile` warnings | **B** | Founder sanity | Many codes to learn |
| Postgres schema + migrations | **B** | Durability | DDL create-if-not-exists drift |
| Guardrail + trial_readiness scripts | **B** | Quality gate | Runtime cost |
| Legacy RAG broker demo (`/api/query`, Qdrant) | **C** | Chen Kui parallel wedge | Embedding warmup 503 theater |
| In-process analytics funnel | **C** | Founder metrics | Not multi-instance truth |
| Assist layer (background) | **C** | Polish | Thread + copy paths |
| WeChat binding / sim | **C** | Channel story | OAuth-ish edge cases |
| OCR / image triage | **C** | Scenario depth | Vendor paths |
| Tab D scenario replay (UI) | **F** | QA | Confuses “product funnel” |
| Platform routers (mortgage, jobhunter, ecommerce, vitals, steward, black_swan, autotuner, ops_lab) | **E/F** | None for pilot | Import smoke noise, attack surface |
| `X-Org-Id` as org truth | **E** | Hint only | Sales overpromise risk |
| “Tenant truth”, “RLS foundation” sprint docs | **E** | Narrative | Implementation ≠ IAM |
| `TRUSTED_ASSISTANT_PLATFORM_BLUEPRINT.md` | **E** | Investor doc | Scope creep magnet |
| Dual-write + JSON read fallback | **G** | Migration flexibility | Wrong prod config = “lost cases” |
| Monolithic `triage.py` | **G** | Behavior | Every change is regression roulette |
| 114 sprint markdown files | **H** | Illusion of progress | Wrong mental model |
| 16 git stashes | **H** | — | Resurrect dead paths |
| `results/` JSON report forest | **H** | — | Conflicts with code truth |
| Full regression / latency lock scripts | **H** | — | Founder runs instead of selling |
| Multi-office enforcement flags (opt-in) | **D** | Future | Hides legacy cases if mis-set |
| Audit export / signed replay bundles | **D** | Enterprise ask | Deferred in code — don’t build yet |
| Stripe / multi-tenant IAM | **Out** per goal doc | — | Correctly excluded |

### What creates fake SaaS illusion

- **`platform_full` default** in local import smoke (`deployment_profile=platform_full` unless env set).
- **Optional keys** that silently allow anonymous inbox/support when unset in prod-like mode (warnings exist — still dangerous).
- **Headers (`X-Org-Id`)** documented as non-authoritative yet persisted and shown in manifests — sounds like tenancy.
- **`INTAKE_SCHEMA_EPOCH`** — sounds like migrations; is a label.
- **Dual persistence** — sounds “cloud native”; is operational hazard.
- **20+ parallel “REAL_SAAS / FUTURE_SAAS” sprint docs** — sounds like shipped architecture.

---

## PHASE 2 — Reduction analysis

### TOP_50_SYSTEM_COMPLEXITY_SOURCES (aggressive)

1. `triage.py` monolith (~6.4k lines)  
2. `routes/inbox_triage.py` god-route (~2.1k lines)  
3. Dual case persistence (JSON file + Postgres + flags)  
4. Dual session persistence (memory + Postgres + test flag)  
5. `UNIFIED_INTAKE_*` env matrix (20+ flags in `demo.env.example`)  
6. `platform_full` vs `product_only` deployment split  
7. 15+ legacy FastAPI routers still in repo  
8. `platform_inline_routes` + NetworkX graph engine init  
9. Qdrant + embedding warmup readiness semantics  
10. `DEMO_MODE` vs `ENV=prod` contradiction paths  
11. `active_vehicle_resolver` unwired parallel to triage  
12. Stub vs full case read split (easy to misuse)  
13. `case_truth_repository` JSON fallback branches  
14. Client pack loader + multiple `client_id` lanes  
15. Field strategy JSON + `field_strategy.py` coupling  
16. Truth guardrails + conversion layer + reply composer stack  
17. Add-car LLM slot candidates + policy modules  
18. `routing_guard` + triage vehicle heuristics overlap  
19. Assist layer thread attachment  
20. WeChat binding state machine  
21. OCR / image pipeline branches  
22. Simulation Tab D in production page bundle  
23. `UnifiedIntakePage.tsx` thousand-line single file  
24. `inboxTriage.ts` growing API surface  
25. Analytics in-process buffer (non-durable)  
26. `early_dropoff` funnel semantics on mid-session turns  
27. Multiple health endpoints (`/healthz`, `/readyz`, `/health/live`, Qdrant probes)  
28. CORS `ALLOW_ALL_CORS` default legacy  
29. Shadow traffic / force override / watchdog plugins (no-op but mounted)  
30. GPU worker pool optional path  
31. LangSmith / observability hooks across agents  
32. Autotuner + ops_lab + black_swan routers  
33. Mortgage / jobhunter / ecommerce / vitals agents  
34. Code lookup + code graph + steward graph  
35. Contract v1 + experiment + KV experiment routes  
36. BM25 + search_core parallel search stacks  
37. Translation layer + demo query fixes  
38. `service_record_settings` production_mode inference rules  
39. Office ownership enforcement opt-in flags  
40. Broker token deploy binding + clock skew  
41. Rate limit middleware (IP-based only)  
42. Support export + deployment-manifest contract versioning  
43. Pack validation module (product-only gate)  
44. Structured turn observability (partial)  
45. Audit export stub (future enterprise)  
46. DB migrations folder + runtime DDL ensure  
47. 114 sprint documents  
48. 35+ `results/` JSON artifacts  
49. 16 git stashes  
50. Founder checklist chain (demo → guardrail → trial → launch → pre-trial)

### TOP_30_FAKE_PLATFORM_PATTERNS

1. “Tenant truth” objects with `tenant_id_authoritative=None`  
2. `X-Org-Id` persisted as ownership signal  
3. `INTAKE_SCHEMA_EPOCH` as faux migration ID  
4. Deployment-manifest as “compliance replay”  
5. `platform_full` API for a 1-SKU pilot  
6. Multi-vertical routers in same binary  
7. Steward / graph_run “AI ops” surface  
8. Black swan / quiet experiment ops routes  
9. TRUSTED_ASSISTANT_PLATFORM_BLUEPRINT monetization section pre-revenue  
10. “Client pack” described as platform extensibility vs copy config  
11. Analytics dashboard without auth = “internal BI”  
12. Org continuity DB columns before broker auth exists  
13. RLS sprint docs without Postgres RLS enabled  
14. Signed broker token marketed as identity vs perimeter secret  
15. Office slug lists in env (`EXPECTED_OFFICE_SLUGS`) without provisioning UX  
16. Dual API keys (intake vs support) implying IAM roles  
17. `audit_export.py` legal-hold language deferred but named  
18. Plugin architecture map implying plug-in marketplace  
19. Multi-agent operating model doc as org chart  
20. “Future SaaS operating system” sprint series  
21. Hundred-offices chaos simulation before 3 paying offices  
22. Product-only wire closure sprint — proves leak existed  
23. CEO review / system productization sprints  
24. Enterprise replay lineage strings in API JSON  
25. Case `current_owner` field always null — CRM theater  
26. LangSmith project naming per vertical  
27. GPU worker pool for intake pilot  
28. NetworkX code graph for broker product  
29. Autotuner in production app  
30. Separate “operator system” boundary sprint parallel to “minimal real SaaS”

### TOP_30_PREMATURE_ENTERPRISE_PATTERNS

1. Multi-office strict list flag before 2 offices pay  
2. Case office enforcement hard 403  
3. Org_id column promotion sprint ahead of broker login  
4. Token scope registry dict in health  
5. Support replay signed bundles  
6. WORM / immutable audit chain docs  
7. Per-org scoped support keys (designed, not needed)  
8. Row-level security narrative  
9. Per-broker cryptographic identity (beyond HMAC perimeter)  
10. OAuth broker SSO  
11. Stripe billing integration (correctly out of scope — don’t restart)  
12. Multi-tenant data residency statements  
13. Separate simulation product SKU  
14. Plugin marketplace architecture  
15. CRM / customer 360 fields in models  
16. Agency OS workflow engine  
17. Carrier execution integration  
18. Full IAM middleware stack  
19. Separate analytics warehouse  
20. Cross-region active-active  
21. Formal on-call paging integration  
22. SOC2 control mapping in manifests  
23. Per-office rate limit tiers  
24. Attachment virus scan pipeline  
25. Enterprise SSO for analytics  
26. Dedicated support portal UI  
27. Multi-industry packs beyond auto  
28. China/Europe expansion hooks  
29. Full observability tracing requirement for pilot  
30. 100-office operational chaos playbook

### TOP_30_FOUNDER_BURNOUT_PATHS

1. Choosing wrong env bundle on Cloud Run  
2. Interpreting 15 deployment warning codes under fire  
3. Reading conflicting sprint SSOTs  
4. Running full regression instead of selling  
5. Populating stash from wrong branch  
6. Chasing sub-5s latency while pilot needs reliability  
7. Wiring resolver vs deleting module — endless debate  
8. Maintaining platform_full local defaults  
9. Explaining headers-are-not-security to brokers  
10. Rotating three secrets (intake, support, HMAC) independently  
11. Dual-write debug without read-your-writes understanding  
12. Embedding 503 during demo (Qdrant path)  
13. Mixing Tab D simulation metrics with funnel  
14. Updating 114 sprint docs after each change  
15. Writing new sprint doc instead of updating this SSOT  
16. `results/` JSON as status dashboard  
17. Trial launch checklist vs demo checklist duplication  
18. Supporting anonymous support export incidents  
19. Re-litigating PG vs JSON in every thread  
20. OpenClaw + Cursor + ChatGPT parallel doc edits  
21. Fixing ecommerce tests for intake sprint  
22. Import smoke importing all vertical agents  
23. Node version PATH rituals for UI build  
24. Explaining fake tenancy to interested enterprise buyer  
25. Building office auth before first payment  
26. Scope creep from TRUSTED_ASSISTANT blueprint  
27. Perfecting assist copy vs handoff reliability  
28. Adding env flag instead of deleting code path  
29. Keeping dead code “for demos” in same deploy  
30. Fear-deleting platform routes without product_only default

### TOP_30_DEPLOYMENT_COMPLEXITIES

1. Port 8001 local vs 8000 Docker vs Cloud Run `PORT`  
2. `.env` vs `.env.cloudrun` load order  
3. `UNIFIED_INTAKE_PRODUCT_ONLY` not set in prod  
4. `SERVICE_RECORD_DATABASE_URL` missing in prod-like  
5. In-memory sessions with DB URL set (warning)  
6. `DEMO_MODE=true` with `ENV=prod`  
7. Intake key unset on public URL  
8. Support key unset on public URL  
9. Same key for intake and support  
10. CORS `*` with random frontends  
11. Vercel frontend + Cloud Run backend origin mismatch  
12. `UNIFIED_INTAKE_FRONTEND_ORIGIN` drift  
13. Qdrant optional vs required confusion  
14. `FAST_STARTUP` degraded ready vs usable  
15. Cold start min instances = 0  
16. Embedding warmup race on first triage  
17. JSON case path writable in prod  
18. Dual-write partial failure modes  
19. Schema epoch label vs actual DDL  
20. Migration 001 not applied but DDL ensure masks  
21. Git SHA in manifest vs rolling deploy  
22. Broker token deploy binding unbound in prod  
23. HMAC secret too short  
24. Multiple deployment profiles across offices sharing one URL  
25. `demo_cases.json` path on Cloud Run disk  
26. Attachment storage paths  
27. Translation enabled changing behavior  
28. `WORKER_URLS` GPU path accidental enable  
29. Frontend dist not mounted warning  
30. import_smoke always loads platform_full

### TOP_30_SUPPORT_COMPLEXITIES

1. Cannot prove which deploy answered without manifest  
2. `request_trace_id` missing from broker tickets  
3. Client-asserted org vs authoritative tenant confusion  
4. Case-head without real owner identity  
5. Anonymous support export in prod-like  
6. Session vs case ID confusion  
7. JSON fallback caused “vanished case”  
8. Multi-instance in-memory sessions  
9. Stub read vs full read mismatch in support tools  
10. Mixed EN/ZH logs  
11. Workbench test cases in pilot data  
12. Manifest stale vs running container  
13. No L1 script for embedding_warming  
14. Append boundary disputes need engineering  
15. OCR reproduction difficulty  
16. WeChat retry duplicates  
17. Analytics mistaken for customer KPIs  
18. Rate limit absent on abusive replay  
19. Office enforcement 403 surprises  
20. Legacy cases hidden by strict office list  
21. Broker token clock skew  
22. Wrong support key after rotation  
23. Partial Postgres outage + JSON fallback  
24. Simulation cases in support export  
25. Funnel early_dropoff false alarms  
26. Vehicle resolver unwired — RCA confusion  
27. assist copy vs truth field disputes  
28. Client pack mismatch FE/BE  
29. Attachment redaction inconsistency  
30. No single support bundle script for L1

### TOP_30_PRODUCT_SIMPLIFICATIONS (do these)

1. **Default `UNIFIED_INTAKE_PRODUCT_ONLY=1`** everywhere pilot runs  
2. **One persistence truth:** Postgres-only prod; JSON dev-only  
3. **One deploy shape:** Cloud Run + Vercel + 3 secrets max  
4. **One SKU:** Unified Intake add-car pilot  
5. **Wire or delete** `active_vehicle_resolver`  
6. **Split** `UnifiedIntakePage` — hide Tab D behind route flag  
7. **Auth analytics** or remove from public deploy  
8. **Archive** 90% of sprint docs to `docs/archive/sprints/`  
9. **Delete** `results/` from git tracking (gitignore)  
10. **Single env template** — `configs/pilot.prod.env.example` only  
11. **Collapse** health to `/health/live` + manifest for ops  
12. **Document** support L1 script linking manifest fields  
13. **Remove** platform router imports from product-only import path  
14. **Freeze** mortgage/jobhunter/ecommerce/vitals routers  
15. **Simplify** broker identity story: HMAC token OR intake key, not 5 mechanisms  
16. **Stop** persisting `X-Org-Id` as if ownership (keep hint, rename in API)  
17. **Rate limit** support export  
18. **Mandatory** keys in prod-like (fail readiness, not warn only)  
19. **One case read API** for workbench (stub internal only)  
20. **Extract** triage orchestration facade (no behavior change)  
21. **Kill** dual-write after PG cutover  
22. **Rename** `INTAKE_SCHEMA_EPOCH` → `contract_epoch` in docs  
23. **Consolidate** checklists: trial_launch only  
24. **Separate** RAG demo deploy artifact from intake API image  
25. **UI copy** single client pack for pilot  
26. **Disable** assist by default in pilot  
27. **Chaos/sim** npm script, not production bundle  
28. **Founder dashboard:** manifest + 3 metrics only  
29. **PR checklist:** product_only + pg url + keys  
30. **This SSOT** only for reduction decisions

### TOP_30_THINGS_TO_FREEZE

1. Platform routers (no new routes)  
2. `triage.py` behavior — refactor-only with guardrail  
3. Field strategy schema  
4. Standard 7 scenarios package  
5. `TriageResult` HTTP contract (additive only)  
6. PG entity schema  
7. Support manifest JSON shape  
8. Broker token wire format  
9. Client pack IDs (`chen_kui`, etc.)  
10. Guardrail bash script steps  
11. Trial readiness script composition  
12. `deployment_profile` warning code strings  
13. Case append boundary rules  
14. Handoff policy module  
15. Truth guardrails tests  
16. OCR path for current scenarios  
17. WeChat sim for demo  
18. RAG demo mode (separate freeze)  
19. Analytics event names (don't rename)  
20. Office slug env hint (no enforcement default)  
21. Migration 001 SQL  
22. Session payload shape  
23. Workbench API endpoints list  
24. Copy-to-client guardrail  
25. CI smoke script scope  
26. Madge check on UI  
27. Import smoke entrypoint  
28. `INTAKE_SCHEMA_EPOCH` value until contract change  
29. Product-only inline route leak list (empty)  
30. Non-goals in `insurance_paid_pilot_goal.md`

### TOP_30_THINGS_TO_REMOVE_FROM_SKU (customer-facing)

1. Mortgage agent  
2. JobHunter agent  
3. Ecommerce agent  
4. Health vitals monitor  
5. Ops copilot  
6. Steward graph  
7. Black swan / ops lab  
8. Autotuner API  
9. Code lookup / code graph  
10. KV experiment  
11. Contract v1 demo API  
12. Best-of search playground  
13. Platform inline demo routes  
14. Tab D scenario replay (customer deploy)  
15. Multi-client pack picker in pilot UI  
16. Analytics dashboard URL for brokers  
17. “Tenant” language in UI  
18. Office enforcement toggle in broker UI  
19. Simulation metrics in funnel reports  
20. GPU worker features  
21. Shadow traffic controls  
22. NetworkX graph features  
23. Multi-port documentation (8000/8001) in broker docs  
24. JSON case export for brokers  
25. Support case-head without redaction policy doc  
26. Enterprise replay bundle promises  
27. Per-office custom deploy variants  
28. RAG + intake mixed landing page  
29. Developer debug trace routes  
30. “Platform” wording in sales deck

### TOP_30_THINGS_TO_DELAY_6_MONTHS

1. Per-broker OAuth  
2. Postgres RLS  
3. Signed audit export  
4. Multi-office hard enforcement default  
5. Stripe billing  
6. Separate analytics service  
7. Plugin marketplace  
8. CRM integration  
9. Carrier API execution  
10. Multi-industry packs  
11. China/Europe  
12. 100-office chaos automation  
13. Full triage.py rewrite  
14. WORM storage  
15. Per-org support keys  
16. Enterprise SSO  
17. Attachment malware scanning  
18. Multi-region active-active  
19. Formal SOC2 mapping  
20. Customer-facing analytics  
21. Separate simulation product  
22. AI ops steward  
23. Autotuner production use  
24. Code graph product features  
25. GPU inference path  
26. Full IAM `current_owner`  
27. Legal-hold replay  
28. Office provisioning UI  
29. Automated broker onboarding  
30. Second paid SKU beyond add-car intake

---

## PHASE 3 — Convergence architecture

### 1. Minimal paid pilot architecture

```
[Vercel: Unified Intake UI — workbench + customer entry only]
    │  Authorization: Bearer broker token OR intake API key (office deploy)
    ▼
[Cloud Run: single service, UNIFIED_INTAKE_PRODUCT_ONLY=1]
    │  Routes: /api/inbox/*, /health/live, /api/inbox/support/* (keyed)
    ▼
[Postgres: service_records + intake_sessions + intake_entities]
    │  No JSON case writes in prod
    ▼
[Optional: Qdrant only on separate "demo RAG" service — not intake image]
```

### 2. Minimal deployment architecture

- **One** Cloud Run service (intake)  
- **One** Vercel project (UI)  
- **One** Postgres instance (pilot DB)  
- **Secrets (3):** `SERVICE_RECORD_DATABASE_URL`, `UNIFIED_INTAKE_INTAKE_API_KEY`, `UNIFIED_INTAKE_SUPPORT_API_KEY` (+ optional `UNIFIED_INTAKE_BROKER_TOKEN_HMAC_SECRET`)  
- **Env:** `ENV=prod`, `UNIFIED_INTAKE_PRODUCT_ONLY=1`, `UNIFIED_INTAKE_DB_PRIMARY_WRITES=1`, `UNIFIED_INTAKE_JSON_CASE_WRITES=0`  
- **Local:** `run_demo_local.sh` on 8001 only — document nowhere else for brokers  

### 3. Minimal support architecture

- L1: `GET /api/inbox/support/deployment-manifest` + `case-head/{id}` with support key  
- Required fields in tickets: `case_id`, `request_trace_id`, timestamp, office slug (hint)  
- No broker-facing support portal — founder + manifest  
- Runbook: `docs/trial/FOUNDER_LAUNCH_NOTES.md` + this SSOT §support  

### 4. Minimal broker identity architecture

- **Pilot:** signed broker token (HMAC) scoped to deploy binding + office slug claim **OR** shared intake key per office deploy  
- **Not:** OAuth, JWT sessions, RLS, `X-Org-Id` as security boundary  
- **Honesty string** in API: client hints ≠ tenant authority  

### 5. Minimal persistence architecture

- Postgres **only** for cases, sessions, vehicle entities in prod  
- JSON file: **local dev fallback only**, gitignored data dir  
- In-memory sessions: **tests only**  
- **Delete** dual-write after 30 days stable PG  

### 6. Minimal replay architecture

- Engineering replay: manifest + case-head + `request_trace_id` in logs  
- **No** signed bundles, no legal-hold language  
- `contract_epoch` label bumps on breaking API changes only  

### 7. Minimal analytics architecture

- Process-local funnel for founder weekly review **or** disable in prod  
- Do **not** sell analytics to brokers in pilot  
- Fix `early_dropoff` noise before trusting metrics  

### 8. Minimal onboarding architecture

- Manual email: URL + intake key + 3 steps + Chen Kui scenario order  
- `trial_launch_check.sh` once before first broker  
- No self-serve signup  

### 9. Minimal operator architecture

- Andy + manifest + guardrail PASS + deployment warnings = 0 critical  
- No separate “operator console” product — support routes only  

### 10. Minimal office architecture

- **One office per deploy** for pilot; office slug in token/config  
- Multi-office: **separate deploys** before shared multi-tenant DB  

### What can be safely deleted, frozen, isolated, or hidden?

| Action | Targets |
|--------|---------|
| **Delete later** (post-migration) | JSON case writes, dual-write, unwired resolver or triage duplicate, platform router registrations in product image, `results/` tracked artifacts |
| **Freeze** | Platform routers, new env flags, TriageResult breaking changes, scenario package definitions |
| **Isolate** | RAG demo (separate service or `product_only` off on demo-only deploy), simulation UI route, ecommerce/jobhunter tests in CI subset |
| **Hide** | Tab D, analytics URL, debug trace, ops routes, enterprise language in manifest consumer docs |

---

## PHASE 4 — Target product shape (“Small Real SaaS”)

| Dimension | Target |
|-----------|--------|
| **SKU** | One: Unified Intake — Add-Car pilot for CA auto brokers |
| **Deployment** | Cloud Run (API) + Vercel (UI) + Postgres |
| **Persistence truth** | Postgres only in prod |
| **Support flow** | Manifest + case-head + founder runbook |
| **Replay story** | Trace ID + epoch + git SHA — engineering only |
| **Onboarding** | Manual URL + key + 7 scenarios |
| **Operator** | Founder + scripts, no platform ops UI |
| **Identity** | HMAC broker token or intake API key per deploy |
| **NOT** | Multi-SKU platform, many ports/modes, tenancy theater, enterprise IAM |

**Smallest real product sentence:**  
*Add-car intake that turns messy customer messages into a durable service record and broker workbench handoff — deployed as one honest API surface with Postgres truth and coarse perimeter secrets.*

---

## PHASE 5 — Safe reduction roadmap

### A. Immediately simplify now (low migration risk)

| Item | Risk | Mitigation |
|------|------|------------|
| Set `UNIFIED_INTAKE_PRODUCT_ONLY=1` in Cloud Run + `demo.env.example` default | Low | import_smoke in CI with flag on |
| Archive sprint doc sprawl to `docs/archive/sprints/` index | None | Keep this SSOT |
| gitignore `results/*.json` | Low | Keep scripts writing locally |
| Hide Tab D behind `?sim=1` or separate route | Low | UI-only |
| Document 3-secret pilot env template | None | Link from AGENTS.md |
| Mandatory keys in `trial_readiness_check` fail | Med | Staged: warn → fail |

### B. Freeze for later

Platform routers, new analytics events, office enforcement default-on, audit export, triage behavioral changes without guardrail.

### C. Hide from customer-facing product

Analytics, simulation, debug, platform language, tenant headers in UI copy.

### D. Keep internally only

Manifest, support export, guardrail scripts, deployment warnings, founder checklists.

### E. Delete later after migration

JSON case primary path, dual-write, in-memory sessions in any prod-like env, unwired resolver duplicate, platform router code paths from default image.

### F. Never build (pilot phase)

Stripe, OAuth broker login, RLS, signed legal replay, multi-tenant admin, plugin marketplace, agency OS.

### G. Only build after real revenue

Second office on shared DB, per-broker auth, customer analytics, self-serve onboarding, second vertical SKU.

**Risk summary**

| Risk type | Highest items |
|-----------|----------------|
| Operational | Wrong env matrix, anonymous keys |
| Migration | JSON→PG cutover without read-your-writes |
| Founder | Doc sprawl, running regressions not sales |
| Support | Tenancy language, missing trace IDs |
| Customer confusion | Simulation tab, fake multi-office |

---

## PHASE 6 — SELF_CRITIQUE_REPORT_V12

This sprint and codebase exhibit:

1. **Architecture ego:** 6k-line triage module defended as “central engine” instead of split behind stable policy interfaces.  
2. **Fake future-proofing:** `INTAKE_SCHEMA_EPOCH`, tenant truth structs, audit export stubs.  
3. **Platform fantasy:** `platform_full` default; 15 routers for a broker intake pilot.  
4. **Complexity addiction:** 20+ new sprint SSOT files on one branch without archiving old ones.  
5. **Over-abstraction:** Case truth repository + case store + session repository + session store facades for one office.  
6. **Unnecessary scalability:** GPU pool, shadow traffic, autotuner — zero pilot customers.  
7. **Hidden support costs:** Optional keys + header hints → multi-hour “is my data stolen?” calls.  
8. **Hidden deployment costs:** 8001 vs 8000 vs Cloud Run PORT — founder cognitive tax.  
9. **Hidden cognitive load:** Stub vs full read, resolver wired vs not, docs saying opposite things.  
10. **AI startup theater:** “Future SaaS operating system”, “hundred offices chaos”, “CEO productization review” before 3 paying offices.

**Verdict:** System is **technically pilot-viable** (tests/guardrails pass) but **commercially over-built** in surface area and **operationally under-honest** in defaults (platform_full, optional auth).

---

## PHASE 7 — Validation + reality check

### Commands run (2026-05-23)

| Check | Result |
|-------|--------|
| `python3 -m compileall -q services/fiqa_api tests` | **PASS** |
| `PYTHONPATH=. python3 -m pytest tests/ -q` | **PASS** (1 skipped; full suite ~3.2 min) |
| `bash scripts/guardrail_inbox_triage.sh` | **PASS** (13/13 scenarios + A/B batteries) |
| `bash scripts/trial_readiness_check.sh` | **PASS** (includes guardrail + UI build) |
| `PYTHONPATH=. python3 scripts/import_smoke_check.py` | **PASS** (note: `deployment_profile=platform_full` without env) |
| `cd ui && npx madge --circular --extensions ts,tsx src` | **PASS** (no cycles) |
| `support_deployment_manifest_smoke.py` | **Not run** (requires live server + key) |

### Reality questions

**If only 3 offices paid us, would this architecture still make sense?**  
**Partially.** Postgres + product-only + workbench + guardrails — yes. Platform routers, dual persistence, 114 sprint docs, unwired resolver, in-process analytics — **no**. Prefer **3 separate deploys** (one DB each) over shared multi-tenant complexity.

**If we had to support this ourselves for 2 years, what would we regret?**  
- Not defaulting `product_only` and mandatory keys on day one  
- Leaving `triage.py` monolithic  
- Letting JSON persistence linger  
- Writing enterprise sprint docs instead of one support L1 page  
- Letting brokers see simulation/analytics  
- Optional auth warnings instead of hard failures  

---

## PHASE 8 — FINAL OUTPUT

### 1. What the REAL product actually is

Add-car-first **Unified Intake**: messy customer input → structured service record → broker workbench handoff, with PG-backed vehicle truth when configured.

### 2. What creates REAL customer value

Reliable triage + handoff copy, case continuity, workbench, client-pack tone, scenario-tested add-car flows, official citations path (RAG demo adjunct).

### 3. What creates fake value

Platform routers, tenant headers, enterprise replay narrative, multi-vertical agents, in-process analytics as “product BI”, 114 architecture sprint documents.

### 4. Biggest unnecessary complexities

`triage.py` size, dual persistence, platform_full default, sprint doc sprawl, unwired resolver duplicate, env flag matrix.

### 5. Biggest founder traps

Stashes + conflicting docs, optional auth, running latency locks vs selling, maintaining platform mode locally.

### 6. Biggest deployment burdens

Port/env multiplicity, Qdrant readiness coupling, keys unset, product_only off, JSON fallback in prod.

### 7. Biggest support burdens

Tenancy confusion, missing trace IDs, stub vs full case, anonymous support export, manifest vs reality drift.

### 8. Biggest fake enterprise patterns

Tenant truth with null authority, RLS docs without RLS, audit export deferral, multi-office enforcement before revenue.

### 9. What should be frozen

Platform routes, TriageResult contract, 7 scenarios, guardrail scripts, field strategy, PG entity schema.

### 10. What should be hidden

Tab D simulation, analytics, debug routes, enterprise API fields in broker-facing docs.

### 11. What should be deleted later

JSON primary cases, dual-write, platform routers from intake image, unwired resolver or duplicate triage logic, tracked `results/` noise.

### 12. What should NOT be built

OAuth, Stripe (now), RLS, signed legal replay, plugin marketplace, multi-SKU platform console.

### 13. Minimal ideal architecture

Product-only FastAPI → inbox routes → triage engine → Postgres (cases, sessions, entities) → Vercel UI.

### 14. Minimal ideal deployment model

One Cloud Run + one Vercel + one Postgres + 3 secrets + `product_only=1`.

### 15. Minimal ideal support model

Support key + manifest + case-head + trace ID runbook for founder.

### 16. Minimal ideal persistence model

Postgres-only prod; JSON dev-only; no in-memory except tests.

### 17. Minimal ideal broker identity model

HMAC token per deploy **or** intake API key; honest non-tenant headers; no OAuth in pilot.

### 18. What breaks at 30 offices

Shared DB without RLS, in-process analytics, founder key rotation, single Cloud Run instance session assumptions if memory enabled, support without partitioned deploys.

### 19. What breaks at 100 offices

Everything above plus triage monolith deploy risk, guardrail runtime, doc/onboarding impossibility, rate limits, case list perf, office enforcement flags, operational chaos (already simulated in docs — premature).

### 20. Next 3 months

1. Default product_only + PG-only prod for pilots  
2. Wire or delete vehicle resolver  
3. Archive sprint sprawl; gitignore results  
4. Mandatory keys in trial readiness  
5. Hide simulation from broker UI  
6. Sell 1–3 paid pilots — not new platform routes  

### 21. Next 12 months

After **3+ paying offices:** consider shared DB with real auth, durable analytics, second SKU only if add-car retention proves out; delete platform code from main deploy artifact.

### 22. FINAL_ONE_LINE

**Ship one honest intake SKU on Postgres with product-only API defaults — delete the platform fantasy from the default path, not from the repo, until revenue buys the next complexity.**

---

## Appendix — Coexistence: other sprint SSOTs

| Document | Status |
|----------|--------|
| This file | **Authority for reduction sprint** |
| `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` | **Authority for product direction** |
| `docs/goals/insurance_paid_pilot_goal.md` | **Authority for scope/non-goals** |
| `docs/sprints/MINIMAL_PAID_SAAS_SURVIVABILITY_SPRINT.md` | Historical — merge findings here |
| Other `docs/sprints/*SAAS*` | Archive candidates — do not treat as parallel SSOT |

---

*Validation snapshot: branch `sprint/scoped-broker-identity-office-operational-safety`, 2026-05-23.*
