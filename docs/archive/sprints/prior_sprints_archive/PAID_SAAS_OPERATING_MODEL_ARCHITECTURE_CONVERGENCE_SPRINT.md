# Paid SaaS Operating Model + Architecture Convergence Sprint

**SSOT ID:** `PAID_SAAS_OPERATING_MODEL_ARCHITECTURE_CONVERGENCE_SPRINT`  
**Created:** 2026-05-08  
**Status:** CONVERGENCE FREEZE (living document — revise only via explicit sprint charter)

**Discovery evidence (Phase 1):** `grep`/read of `app_main.py`, `deployment_profile.py`, `routes/inbox_triage.py`, `security/support_export_gate.py`, `security/request_identity.py`, `db/service_record_repository.py`, `db/service_record_settings.py`, `inbox_triage/pack_validation.py`, `inbox_triage/audit_export.py`, `platform_inline_routes.py`, `configs/clients/*`, `docs/goals/insurance_paid_pilot_goal.md`, prior sprint SSOTs (`FUTURE_SAAS_OPERATING_SYSTEM_*`, `REAL_SAAS_BOUNDARY_*`).  
**Quick validation (Phase 6 sample):** `python3 -m compileall -q services/fiqa_api` PASS; `pytest tests/test_deployment_profile.py tests/test_pack_validation.py` PASS.

---

## OBJECTIVE

Freeze **honest** operating-model and architecture truth for Unified Intake as a **future billable SaaS foundation** — not as aspirational “enterprise platform” theater. Converge on what is **sellable**, **operable**, **supportable**, and **deployable** today, with explicit evolution paths for tenant identity, auth, support exports, and replay — **without** pretending shipped capabilities exist.

---

## NON_GOALS

- Shipping full multi-tenant IAM, RBAC UI, OAuth customer login, Stripe, or self-serve signup.
- Expanding Unified Intake feature scope (“more AI”) as a substitute for operating truth.
- Replacing manual pilot economics with automated SaaS billing in this sprint.
- Claiming GDPR/SOC2/HIPAA readiness from current audit stubs.
- Building another vertical or “workflow builder.”

---

## SUCCESS_GATES

| Gate | Criterion |
|------|-----------|
| **G1 — Single SSOT** | This document is the authority for paid-SaaS convergence; contradictions resolved toward **code + env truth**. |
| **G2 — No fake tenancy** | Every doc and manifest states `X-Org-Id` / `client_asserted_org_id` as **untrusted assertion** until server-issued tenant exists. |
| **G3 — Support honesty** | Support export auth posture is explicit (`anonymous_ok` vs `api_key_required`); no implied enterprise SOC for `/api/inbox/support/*`. |
| **G4 — Deployment honesty** | `UNIFIED_INTAKE_PRODUCT_ONLY` meaning is **router + inline lab registration** via `register_platform_inline_routes` only when flag off; `INTAKE_SCHEMA_EPOCH` is operator-visible contract label. |
| **G5 — Replay honesty** | Distinguish regression/scripts vs live LLM; “Role C” simulation vs production replay; audit export = **stub** (`audit_export.py`). |
| **G6 — Business alignment** | Paid pilot goal doc remains aligned: first paid pilot tolerates **manual payment**, **single broker**, **no MT auth**. |

---

## BUSINESS_TRUTH_MODEL

| Truth | Statement |
|-------|-----------|
| **Revenue mechanism today** | Manual invoice (Zelle/Venmo/WeChat) per `docs/goals/insurance_paid_pilot_goal.md`; **no** recurring billing in product. |
| **Customer count truth** | Optimized for **one** paying broker pilot; “30/100 offices” are **stress simulations**, not committed SKU capacity. |
| **Value proposition** | Unified Intake triage + case persistence story + broker workflow fit — **not** “full insurance OS.” |
| **CAC / onboarding** | Founder-led onboarding with **filesystem client packs** (`configs/clients/<client_id>`); no automated provisioning. |
| **Pricing truth** | Not encoded in software; **pricing confusion** is a business risk until SKU packaging is explicit in contracts. |

---

## PRODUCT_TRUTH_MODEL

| Layer | Is SKU / sellable? | Notes |
|-------|-------------------|-------|
| **POST `/api/inbox/triage`** | **Yes** — core | Structured intake + triage output. |
| **Cases, session, append, notes, attachments** | **Yes** | Operational wedge for brokers. |
| **`GET /api/inbox/client-config`, scenario center, add-car rules** | **Yes** — configuration surface | Bound to `client_id` packs. |
| **WeChat binding routes** | **Conditional SKU** | Requires live credentials + client pack; simulation paths are **lab/dev**. |
| **Role C simulation** | **Demo / training** — not compliance replay | Lab narrative must not conflate with audit replay. |
| **`GET /api/analytics/dashboard`** | **Founder / operator** — not multi-tenant BI | In-process funnel; scope creep risk if sold as “enterprise analytics.” |
| **Platform routers** (search, agents, codemap, steward, …) | **Not Unified Intake SKU** | Absent when `UNIFIED_INTAKE_PRODUCT_ONLY=1`. |
| **RAG “SearchForge” demo** | **Adjacent** — not Unified Intake billing unit unless contracted separately. |

---

## TENANT_TRUTH_MODEL

| Concept | Today’s truth |
|---------|----------------|
| **`tenant_id_authoritative`** | **Always `None`** in `intake_tenant_truth()` — reserved for future JWT/API-key scope. |
| **`X-Org-Id`** | Stored as `client_asserted_org_id`; semantics **`client_asserted_org_id_not_tenant_authority_v1`**. |
| **`client_id`** | **Configuration / pack key** (`configs/clients/...`) and column on `service_records`; **not** cryptographic isolation. |
| **Row-level isolation** | **Not enforced** by Postgres RLS for tenants; single DB = **future** noisy-neighbor risk. |
| **“Org”** | **Organizational hint** for analytics/events — **not** an auth boundary. |

---

## SUPPORT_TRUTH_MODEL

| Element | Reality |
|---------|---------|
| **`UNIFIED_INTAKE_SUPPORT_API_KEY`** | Optional shared secret; if unset, **`assert_support_export_authorized` is a no-op** — routes **anonymously reachable** (documented in code). |
| **`GET /api/inbox/support/deployment-manifest`** | Operator manifest: git SHA, schema epoch, persistence report, auth posture — **no PII by design**. |
| **`GET /api/inbox/support/case-head/{case_id}`** | Minimal metadata for handoff — **explicitly not full message bodies**. |
| **L1/L2** | **Process**, not productized queues — no ticketing integration in codebase. |
| **Escalation** | Defaults to **founder / engineer** with DB + logs + git SHA from manifest. |

---

## REPLAY_TRUTH_MODEL

| Replay type | Truth |
|-------------|-------|
| **Deterministic regression** | Scripts + golden artifacts — **authoritative for CI narrative**. |
| **Live triage replay** | LLM + rules — **non-deterministic**; disputes need **schema epoch + git SHA + persistence mode**, not “verbatim replay.” |
| **`audit_export.record_intake_case_mutation`** | Forwards to `track_event` — **not** immutable compliance storage. |
| **`future_export_bundle_keys()`** | **Contract seed only** — no signed export pipeline shipped. |
| **Role C simulation** | **Synthetic customer** — must never be sold as “audit replay.” |

---

## OPERATOR_TRUTH_MODEL

| Operator concern | Mechanism today |
|------------------|-----------------|
| **Which build is running?** | `GET /health` → `deployment_profile`, git via `get_git_sha()` on support routes. |
| **Schema / contract drift** | `INTAKE_SCHEMA_EPOCH` in `deployment_profile.py`; surfaced on health + deployment-manifest. |
| **Persistence mode** | `unified_intake_case_persistence_report()` — env-driven matrix (PG vs JSON vs dual-write). |
| **Rollback** | **Env flags + redeploy** — no automated blue/green product layer. |
| **Founder overload** | **Single throat to choke** — scripts (`run_demo_local.sh`, `trial_readiness_check.sh`, guardrails) reduce but **do not remove** dependency. |

---

## DEPLOYMENT_TRUTH_MODEL

| Topic | Truth |
|-------|-------|
| **`UNIFIED_INTAKE_PRODUCT_ONLY`** | **Reduces FastAPI included routers** to inbox + analytics + health/Qdrant probes; **does not** ship “separate microservices.” |
| **Lab inline routes** | **`register_platform_inline_routes`** only when **not** product-only (`platform_inline_routes.py` — includes `/obs/ping`, lab reports, etc.). |
| **`PLATFORM_INLINE_ROUTES_UNGATED_IN_APP_MAIN`** | **Empty tuple** — historical leaks documented as empty for auditors (`deployment_profile.py`). |
| **Ports** | `MAIN_PORT` / Cloud Run conventions; **8001** common for local demo per `AGENTS.md` — **branch/env illusion** if operators mix ports. |
| **`product_only` meaning** | **Sellable wire surface**, not a guarantee that **all** future `@app` decorators are impossible — discipline required at code review. |

---

## ONBOARDING_TRUTH_MODEL

| Stage | Truth |
|-------|-------|
| **Pack layout** | `validate_client_pack_layout` requires `ui_copy.json` + `handoff_phrases.json` under `configs/clients/<id>/`. |
| **Depth** | **Minimal** filesystem validation — does not validate JSON semantics, WeChat secrets, or DB migrations. |
| **Activation** | **Manual** URL handoff + env configuration (DB URLs, flags, optional support key). |
| **“Factory”** | **Metaphor only** — no automated tenant factory. |

---

## SECURITY_TRUTH_MODEL

| Control | Maturity |
|---------|----------|
| **Support export gate** | **Optional** API key — **not** OAuth/SSO. |
| **Tenant boundary** | **Honest null** — headers are assertions. |
| **PII in logs/events** | **Risk** — requires operator discipline; analytics/events need review per deployment. |
| **Case ID as secret** | **Not** — UUIDs can leak via URLs/support; **no** ACL on case read without future auth. |
| **WeChat OAuth** | Real crypto only when credentials configured; simulate path **dev/staging**. |

---

## ARCHITECTURE_CONVERGENCE_MODEL

**Real SaaS shape (target arc, not promised ship date):**

1. **Deployment:** Single FastAPI image with **profile flag** + env matrix; optional split **host** for lab vs customer runtime **later** — not required for pilot honesty.
2. **Tenant:** Nullable `tenant_id_authoritative` → future API keys / JWT claims; **RLS** in Postgres **after** stable org model.
3. **Support:** Manifest + case-head + schema epoch **today**; **Support System V2** = scoped keys + redacted export bundles + escalation playbook **incrementally**.
4. **Replay:** Split **marketing replay** vs **engineering regression** vs **legal hold** (future WORM) — three lanes.
5. **Onboarding:** Pack validator → env checklist → support handoff doc — **documented factory**, not Terraform-for-brokers yet.

---

## REALITY_CHECKS

| Check | Result |
|-------|--------|
| **Is multi-tenant isolation shipped?** | **No.** |
| **Is support surface always authenticated?** | **No** — key optional. |
| **Is tenant_id authoritative anywhere?** | **No** — always null. |
| **Is audit export compliance-grade?** | **No** — stub → events. |
| **Does product-only guarantee zero lab code paths?** | **Wire-level:** lab **registration** gated; **discipline** still needed for future inline routes. |

---

## SELF_CRITIQUE

This sprint doc cannot **manufacture** isolation or billing — it can only **freeze honesty** and prioritize **high-ROI, low-blast-radius** hardening. The largest honest gap remains **founder-shaped operations** until repeatability justifies investment in auth and provisioning.

---

## FINAL_DECISION

| Decision | Resolution |
|----------|------------|
| **What is the product (freeze)?** | **Unified Intake** = inbox triage + case/session lifecycle + client-pack configuration + operator health/manifest — **in product-only profile** as contracted surface. |
| **What is NOT the product?** | SearchForge platform agents, codemap, mortgage/job demos, full lab surface — **not** billable as Unified Intake unless separately contracted. |
| **What is LAB only?** | Platform-full routers, Role C **as “customer truth,”** WeChat **simulate** paths, non-GA experiments. |
| **What must NEVER ship as “enterprise”?** | Claims of SOC2/GDPR audit trails from `audit_export` stub; “tenant isolation” from `X-Org-Id` alone. |
| **What must stay product_only for paid SaaS hosting?** | Customer-facing Unified Intake deployments should run **`UNIFIED_INTAKE_PRODUCT_ONLY=1`** + configured DB + optional support key. |
| **What should be different host later (optional)?** | Founder analytics / lab obs — **if** customerData segregation policy requires it — **not mandatory for pilot honesty**. |
| **What must never touch customer runtime (policy)?** | Ad-hoc lab experiments and **ungated** debug endpoints — **forbidden** in paid profiles via review + flag. |

---

## FINAL_ONE_LINE

**Unified Intake is an honest single-tenant-shaped pilot with explicit schema and deployment manifests — not multi-tenant SaaS isolation until auth, RLS, and billing are deliberately built, not header-asserted.**

---

# PHASE 1 — REAL SYSTEM DISCOVERY (ARTIFACTS)

## PRODUCT_TRUTH_REALITY_MAP

**What could be charged for *today* (honest SKU envelope):**

- Broker-facing **intake + triage API** and **case persistence** (subject to contract).
- **Per-client configuration** via **filesystem packs** (`handoff_phrases`, `ui_copy`, optional reply layers).
- **Operator/support diagnostics**: deployment-manifest, case-head, `/health` persistence truth.

**What is NOT a SKU (do not price as product):**

- **Platform RAG / agents / codemap** — separate narrative.
- **“Tenant isolation”** — not implemented.
- **Analytics dashboard** as **enterprise BI** — it’s **founder/operator** tooling.

**What is lab / demo:**

- Role C **simulation**; WeChat **simulate-complete** (gated by env).
- Full **platform** API surface when `UNIFIED_INTAKE_PRODUCT_ONLY` unset.

**Platform illusion risks:**

- Calling **`client_id` “tenant.”**
- Calling **`X-Org-Id` “auth.”**
- Selling **schema epoch** as **automatic migration** — it’s a **label**, not Alembic.

**Features that **hurt** SaaS narrative if oversold:**

- Anonymous **support routes** when key unset.
- **Dual-write / JSON fallback** complexity told as “simple cloud.”

---

## TENANT_TRUTH_REALITY_MAP

| Item | Real / Fake |
|------|-------------|
| **Postgres `client_id` column** | **Real** as **pack/config discriminator** — **fake** as **cryptographic tenant.** |
| **`X-Org-Id`** | **Real** as **optional analytics hint** — **fake** as **security boundary.** |
| **`tenant_id_authoritative`** | **Explicitly null** — **honest.** |
| **Deployment slicing** | **Real** via env + product-only flag — **not** per-tenant clusters today. |
| **Org illusion** | Marketing language — **must map** to `client_id` + packs + DB rows. |
| **Future RLS** | **Compatible** if **`client_id` / org uuid** eventually enforced server-side — **not** compatible with **header-only** “tenant.” |

---

## SUPPORT_OPERATION_REALITY_MAP

| Topic | Truth |
|-------|-------|
| **Support tooling** | **HTTP manifest + minimal case-head** + git/epoch — **not** Zendesk. |
| **Replay for disputes** | **Partial** — case APIs + schema epoch; **no** signed narrative bundle. |
| **Operator truth** | **Env matrix + flags** — expertise-heavy. |
| **Founder dependency** | **High** — escalation defaults to **people who read Postgres + logs.** |
| **Rollback** | **Redeploy + flip env** — no productized rollback orchestrator. |
| **Angry broker** | **No SLA object** in code — contractual only. |

---

## DEPLOYMENT_TRUTH_REALITY_MAP

| Question | Answer |
|----------|--------|
| **Deployment truth** | **One image**, **many env vars**, **one boolean profile** (`UNIFIED_INTAKE_PRODUCT_ONLY`). |
| **Env illusion** | Same codepath **feels** different with DB flags — operators **must** read `unified_intake_case_persistence_report()`. |
| **Runtime truth** | FastAPI + optional Qdrant/embed readiness — `/ready` may **503** when vector stack unhealthy. |
| **Schema truth** | **`INTAKE_SCHEMA_EPOCH`** + Postgres DDL — **epoch is not a migration id.** |
| **Branch truth** | **Git SHA** on manifest — **not** same as “customer branch.” |
| **`product_only` meaning** | **Fewer routes registered** + startup banner — **sellable wire minimization.** |

---

# PHASE 2 — OFFICE SIMULATIONS

## 30 OFFICE SIMULATION (representative failure modes)

**Scale assumption:** 30 independent broker offices sharing **one** deployment (worst case) or **few** clusters — **no** per-office auth.

1. **Config collision:** Two offices share **`client_id` copy-paste** → wrong handoff phrases / branding.
2. **Case ID overlap:** Impossible if UUIDs — **human error** mapping wrong case in support.
3. **Support key shared leak:** One fired employee keeps **`X-Unified-Intake-Support-Key`** → full manifest access.
4. **Anonymous support routes:** Pen tester hits **`/support/deployment-manifest`** without key — **intel leak** (build SHA, persistence mode).
5. **Wrong DB URL** in one region — **split-brain** cases if ever multi-region **without** Primary.
6. **`UNIFIED_INTAKE_PG_DUAL_WRITE` + JSON reads** — **read-your-writes** failures across instances.
7. **Pilot uses `anonymous_ok`** — compliance story **breaks** under scrutiny.
8. **Founder is L1–L3** — **response time** collapses under 30 Slack threads.
9. **Replay dispute:** Broker says “AI promised X” — you only have **non-deterministic** LLM + partial logs.
10. **Analytics:** Office thinks **dashboard** is **their** data — **actually** process-local / deployment-wide buffer semantics — **clarify in contract**.
11. **WeChat:** Half offices **live**, half **sim** — **support confusion.**
12. **Attachment malware** — **no** AV narrative in core product.
13. **`X-Org-Id` spoof** — analytics polluted; **no** security impact **claimed**, but **trust** impact.
14. **Stale frontend** talking to **new API** — contract mismatch; **epoch** helps **engineering**, not broker UX.
15. **Training misuse:** Role C used as **“recorded customer”** in sales — **ethical/legal** blur.
16. **Pricing confusion:** Per-seat vs per-office — **not** in software → **arguments**.
17. **Noisy neighbor:** One office spam triage — **shared** LLM/Qdrant — **latency** for all.
18. **Case PII export** — broker asks for **“all data”** — **no** packaged legal export.
19. **Rollback:** Bad deploy — **manual** revert; **no** canary.
20. **Locale:** Mixed zh/en packs — **wrong** templates bound to wrong `client_id`.
21. **Dual-write disabled mid-flight** — **orphan** records in one store.
22. **503 `/ready`** — broker thinks “down” — **actually** embed warmup.
23. **Support impersonation:** Email **“send case id”** — **no** caller identity proof on triage POST without auth.
24. **`case_id` in URL** — leaks in **referrer** / support tickets.
25. **Founder vacation** — **no** runbook depth → **outage extension**.
26. **Pilot abuse:** Unlimited API — **no** rate limit story.
27. **Pack validation passes** but **JSON invalid** — runtime errors **after** “green” onboarding.
28. **Observability gap:** **Langfuse** optional — **no** unified trace for broker incidents unless configured.
29. **Mobile WeChat WebView** — session cookie edge cases — **support burden**.
30. **Contract vs reality:** Sales promised **“tenant dashboard”** — product **does not exist**.

---

## 100 OFFICE SIMULATION (additional stress — compound failures)

31. **Support queue explosion** — SLA missed → **churn** regardless of tech.
32. **Database connection exhaustion** — noisy neighbor **writes**.
33. **Postgres disk** — attachment growth without **ops playbook**.
34. **Secrets rotation** — rotating support key without **customer comms** plan → false incidents.
35. **Multi-broker data residency** request — **single region** deployment **fails** procurement.
36. **Legal hold** — **no WORM** → **cannot** promise immutability.
37. **SOC2 questionnaire** — **pass** only with **honest** “partial controls.”
38. **VP Sales** invents **RBAC** on calls — engineering **firefight**.
39. **99 offices idle, 1 hot** — **cost attribution** impossible → **pricing fights**.
40. **Cross-office referral** (same customer) — **no** identity merge product.
41. **Schema epoch drift** between **API** and **mobile cache** — mysterious **400s**.
42. **Support asks for “replay package”** — you ship **case-head only** → **dissatisfaction**.
43. **Automated pen-test** finds **support routes** — **report blow-up**.
44. **International broker** — **out of scope** per goals doc → **deal confusion**.
45. **Feature flags per office** — **not** in product → **forking** codebases.
46. **On-call rotation** — **no** paging integration → **wake founder**.
47. **Customer-side proxy** strips **`X-Org-Id`** — analytics **wrong**, debugging **hard**.
48. **Concurrent edits** to same case — **last-write** ambiguity.
49. **Backup/restore test** never done — **first** disaster **is** the test.
50. **100 × weekly emails** “improve AI” — **product management** overload.

**(51–100)** Repetition with variation: **quota exhaustion**, **VPC egress blocks**, **LLM vendor outages**, **dependency CVE** emergency patches, **migrations** without maintenance windows, **CSV export** requests, **“why different answer than last week”** (model/prompt drift), **per-office custom prompts** unsupported, **jurisdictional** insurance compliance disclaimers, **chatbot** liability framing, **broker staff turnover** re-training, **API versioning** absence, **mobile browser** fragmentation, **PDF attachment** parsing failures, **OCR** variance, **language detection** errors, **duplicate customers**, **spam intake**, **malformed JSON** from buggy integrator, **HTTP timeouts**, **WebSocket** absence for live updates, **SEO crawlers** hitting public demo URLs, **credential stuffing** against demo, **accidental prod data** in staging, **staging mirrors prod** without scrubbing — **each** scales linearly with office count; **at 100**, **coordination** dominates **code**.

---

# PHASE 3 — CONVERGENCE LISTS (TOP 50 × 6)

## TOP_50_FAKE_SAAS_PATTERNS

1. Header-based **“tenant”** without server issuance.  
2. **`client_id` as security boundary.**  
3. **Dashboard** as **per-customer** analytics without isolation.  
4. **Support manifest** as **SOC2 control evidence.**  
5. **Schema epoch** sold as **auto-migration**.  
6. **Dual-write** described as **fully consistent**.  
7. **Role C** sold as **audit replay**.  
8. **Git SHA** as **customer versioning**.  
9. **`/health` ok** meaning **“HIPAA ready.”**  
10. **Optional support key** as **“military grade security.”**  
11. **In-memory sessions** in prod without acknowledgment.  
12. **JSON fallback** invisible to customer.  
13. **“Multi-office”** without **org graph**.  
14. **WeChat simulate** in prod **without label**.  
15. **Track_event** as **immutable audit**.  
16. **Single DB** as **data residency compliance**.  
17. **Product-only** as **zero attack surface** (ignore supply chain).  
18. **Case UUID** as **authorization**.  
19. **Manual invoice** as **“usage-based billing.”**  
20. **Founder on-call** as **“24/7 support.”**  
21. **Filesystem packs** as **“CMS for brokers.”**  
22. **Env flags** as **feature flags product**.  
23. **Qdrant readiness** as **application SLA**.  
24. **LLM output** as **deterministic**.  
25. **Triage categories** as **legal classification**.  
26. **Attachment upload** as **virus-safe**.  
27. **Public demo URL** as **same as paid**.  
28. **Copy-paste reply drafts** as **bound coverage**.  
29. **`X-Request-Id`** as **customer-facing incident ID** without mapping.  
30. **Postgres** presence as **backup strategy exists**.  
31. **Docker** as **multi-tenant orchestration**.  
32. **Cloud Run** as **HA story without regions**.  
33. **Static frontend** as **zero-downtime deploys**.  
34. **OpenAPI** as **contract guarantee** without versioning.  
35. **“Encryption at rest”** without **key custody** story.  
36. **TLS termination** as **end-to-end encryption**.  
37. **Obs ping** as **customer observability**.  
38. **Regression JSON** as **live incident reproduction**.  
39. **Pack validation** as **content QA**.  
40. **Broker testimonial** as **enterprise reference**.  
41. **Pilot pricing** as **ARR anchor**.  
42. **“Roadmap” slide** as **committed delivery**.  
43. **Internal Slack** as **customer status page**.  
44. **Email forwarding** as **support ticketing**.  
45. **Google Docs runbook** as **ISO process**.  
46. **“AI assistant”** label as **professional advice**.  
47. **Churn threat** driving **RBAC promise**.  
48. **Pen-test PDF** as **continuous assurance**.  
49. **Single-key API** as **tenant-scoped key**.  
50. **This document** used as **warranty** — it is **architecture honesty**, not a **legal obligation**.

---

## TOP_50_FOUNDER_DEPENDENCIES

1. Env matrix **in head**.  
2. DB credential **rotation**.  
3. Explaining **dual-write** to brokers.  
4. Support escalations **without** L1 scripts.  
5. Deciding **SKU** boundaries live on sales calls.  
6. **Git** fluency for **incident** correlation.  
7. **Postgres** console access **default**.  
8. **Cloud console** access **default**.  
9. **Client pack** authoring **QA**.  
10. **WeChat** credential lifecycle.  
11. **Prompt** changes **without** PM layer.  
12. **LLM vendor** relationship.  
13. **Cost** monitoring per customer **manual**.  
14. **Contract** redlines **technical**.  
15. **Demo** environment **parity** checks.  
16. **Pilot** → **paid** conversion conversations.  
17. **Analytical** dashboard interpretation.  
18. **Guardrail** script execution before releases.  
19. **Manual** deploy approvals.  
20. **Customer** training deck updates.  
21. **Incident** customer comms.  
22. **Regression** triage when CI flaky.  
23. **Data** export requests **ad hoc**.  
24. **Partner** API expectations **management**.  
25. **Security** questionnaire answers **personal**.  
26. **Roadmap** prioritization **political**.  
27. **Engineering hiring** bottleneck **wearing founder hat**.  
28. **Finance** invoice matching **manual**.  
29. **Tax** / **payment** edge cases **founder**.  
30. **Localization** requests **scope creep**.  
31. **Mobile** device debugging **remote**.  
32. **Browser** cache instructions **to brokers**.  
33. **VPN** issues **outside** product.  
34. **Customer IT** blocking endpoints **escalation**.  
35. **PDF** parsing bug reports **interpretation**.  
36. **Third-party** insurer site changes **RAG** drift.  
37. **Benchmark** promises **unintentional**.  
38. **Press** inquiry **technical**.  
39. **Investor** diligence **architecture**.  
40. **Internal** dogfood **nonexistent** at scale.  
41. **On-call** replacement hiring **delayed**.  
42. **Documentation** drift **discovered** by customer.  
43. **Version** skew **detected** by angry email.  
44. **Feature** expectation **from one pilot** applied **globally**.  
45. **Technical debt** interest payments **personal**.  
46. **Code review** bottleneck **founder**.  
47. **Vendor** outage comms **founder-facing-customer**.  
48. **Legal** disclaimer wording **founder+lawyer** loop.  
49. **Community** (WeChat groups) support **informal load**.  
50. **Sleep** as **single point of failure**.

---

## TOP_50_SUPPORT_FAILURES

1. **No** ticketing IDs mapped to **request_trace_id**.  
2. **Anonymous** support surface leak.  
3. **Case-head** insufficient for **“why.”**  
4. **No** PII-redacted **full export**.  
5. **LLM** nondeterminism **unexplained** to broker.  
6. **503** misread as **bug**.  
7. **Latency** variance **unbounded** narrative.  
8. **Attachment** issues **unreproducible**.  
9. **WeChat** path **opaque** to L1.  
10. **Session** loss **blamed on product** (browser).  
11. **Wrong `client_id`** config **hours** to find.  
12. **Epoch** mismatch **invisible** to support UI.  
13. **No** **runbook** for **dual-write** failures.  
14. **No** **customer-facing status page**.  
15. **Email** threads **lose** **case_id** context.  
16. **Escalation** to engineer **always**.  
17. **Cannot** **replay** exact **LLM** tokens.  
18. **Cannot** prove **negative** (“AI never said”).  
19. **Langfuse** absent → **no** trace.  
20. **Logs** retention **undefined**.  
21. **PII** accidentally in **track_event** payload.  
22. **Org id** spoof **confuses** analytics — **looks** like **data corruption**.  
23. **Mobile** screenshots **only** evidence.  
24. **Customer** expects **phone** support — **not** offered.  
25. **Timezone** mishandling in **timestamps**.  
26. **CSV** export **requested** — **not** standard.  
27. **Bulk case** search **slow** without indexes ops tuned.  
28. **Delete case** **irreversible** — **no** trash bin story.  
29. **Merge cases** — **not** supported.  
30. **Permissions** — **everyone** admin in broker shop **— ambiguous responsibility**.  
31. **Language** mismatch **support** burden.  
32. **Copy-paste** drafts **legally** sensitive.  
33. **Insurance** compliance **questions** → **no** legal team on vendor side.  
34. **Customer** shares **case_id** in **public** chat → **social engineering** risk.  
35. **Rotating** API keys **breaks** integrations **without** notice.  
36. **Documentation** says **“tenant”** → **wrong mental model**.  
37. **Dashboard** numbers **disagree** with **broker** perception.  
38. **Training** new broker staff — **no** academy.  
39. **Version** upgrade **without** release notes **customer-readable**.  
40. **Silent** **prompt** change **post-deploy**.  
41. **Regression** passed but **customer** issue **real** — **trust** hit.  
42. **False positive** triage category — **manual rework**.  
43. **Integration** partner **blames** your API — **no** **shared** trace.  
44. **Capacity** — **cannot** **answer** “how many cases/day.”  
45. **SLO** — **cannot** **commit** numerically.  
46. **Data residency** question — **honest** **no**.  
47. **Subprocessors** list — **manual** maintenance.  
48. **DPA** asks for **items** **not** built.  
49. **Insurance carrier** **requires** **audit** trail **you don’t have**.  
50. **Angry** customer **public** review — **no** **PR** playbook.

---

## TOP_50_OPERATOR_FAILURES

1. Deploy **without** reading **persistence report**.  
2. **Mixed** **8000/8001** docs.  
3. **Forgot** **support** key in prod → **later** **key** breaks **scripts**.  
4. **Assumed** **product_only** in prod **but** flag **unset**.  
5. **Qdrant** down → **churn** **ready** **phase** confusion.  
6. **EMBED_READY** false → **silent** **quality** drop.  
7. **Artifacts** dir missing → **503** **health/ready**.  
8. **Database** migration **manual** **skipped**.  
9. **Dual-write** flag **toggled** mid-day.  
10. **JSON** files **left** **writable** alongside PG **—** **split** truth.  
11. **Git** **dirty** deploy **—** **unreproducible** **SHA**.  
12. **Secrets** in **env** **without** **rotation** calendar.  
13. **No** **staging** that **matches** prod **flags**.  
14. **Customer** **given** **admin** **paths** **by** mistake.  
15. **Rollback** **plan** = **“redeploy previous”** **without** **verification**.  
16. **Backups** never **restored** **in drill**.  
17. **Disk** **full** **Postgres** **crash**.  
18. **Connection** pool **defaults** **too** **small**.  
19. **Logging** **volume** **cost** **surprise**.  
20. **Image** **tag** **`:latest`** **in prod**.  
21. **Multiple** **parallel** **deployments** **same** **DB**.  
22. **Cron** **job** **missing** **for** **cleanup**.  
23. **Attachment** storage **unbounded**.  
24. **SSL** **misconfigured** **on** **frontend**.  
25. **CORS** **misconfigured** **blocking** **broker**.  
26. **Rate** **limit** **absent** → **abuse** **overnight**.  
27. **Observability** **paywall** **surprise**.  
28. **LLM** **quota** **exhausted** **silent** **fallback** **to** **rules** **—** **undisclosed**.  
29. **Feature** **branch** **merged** **without** **guardrail**.  
30. **Customer** **env** **vars** **typo** **—** **hours** **lost**.  
31. **Pack** **files** **not** **in** **git** **deploy** **artifact**.  
32. **Wrong** **REGION** **latency**.  
33. **Cold** **start** **timeouts** **not** **tuned**.  
34. **Health** **check** **too** **shallow** **—** **traffic** **routed** **to** **bad** **instance**.  
35. **Canary** **nonexistent** **—** **all** **customers** **get** **bad** **release**.  
36. **Database** **index** **missing** **—** **queries** **slow** **at** **scale**.  
37. **Vacuum** **never** **run**.  
38. **Analyze** **never** **run**.  
39. **Partitioning** **not** **planned**.  
40. **Secrets** **logged** **by** **debug** **flag** **left** **on**.  
41. **Personal** **AWS** **keys** **on** **laptop** **—** **SOC** **fail**.  
42. **SSH** **open** **to** **world** **on** **jump** **box**.  
43. **Firewall** **rules** **too** **permissive**.  
44. **Vendor** **dependency** **unpinned**.  
45. **Docker** **image** **CVE** **ignored**.  
46. **Compliance** **packet** **promised** **—** **not** **delivered**.  
47. **Customer** **data** **copy** **to** **staging** **without** **scrub**.  
48. **Internal** **slack** **bot** **posts** **case** **titles** **—** **PII** **leak**.  
49. **On-call** **handoff** **missed**.  
50. **Postmortem** **never** **written** **—** **repeat** **incident**.

---

## TOP_50_ENTERPRISE_ILLUSIONS

1. **SOC2 Type II** **next** **quarter** (without controls).  
2. **Multi-region** **active-active** **soon**.  
3. **RBAC** **on** **roadmap** **next** **month**.  
4. **SSO** ** SAML** **easy**.  
5. **Dedicated** **single-tenant** **cloud** **for** **same** **price**.  
6. **HIPAA** **BAA** **available**.  
7. **FedRAMP** **path**.  
8. **Data** **residency** **EU** **support**.  
9. **Private** **LLM** **included**.  
10. **On-prem** **optional**.  
11. **Air-gapped** **deploy** **standard**.  
12. **Pen-test** **remediation** **SLA** **48h**.  
13. **24/7** **NOC** **included**.  
14. **Named** **CSM** **for** **all** **tiers**.  
15. **Custom** **SLA** **99.99%**.  
16. **Legal** **indemnity** **unlimited**.  
17. **IP** **assignment** **clean** **without** **lawyer**.  
18. **GDPR** **Article** **30** **register** **automated**.  
19. **DPAs** **with** **all** **subprocessors** **signed**.  
20. **Immutable** **audit** **log** **customer-accessible**.  
21. **eDiscovery** **export** **one-click**.  
22. **ISO27001** **cert** **on** **file**.  
23. **Bug** **bounty** **program**.  
24. **Formal** **CVE** **response** **SLA**.  
25. **Vendor** **questionnaire** **500** **questions** **no** **problem**.  
26. **Insurance** **carrier** **certification** **guaranteed**.  
27. **Broker** **EO** **coverage** **extends** **to** **vendor**.  
28. **Multi-org** **hierarchy** **model**.  
29. **Delegated** **admin** **per** **office**.  
30. **Fine-grained** **permissions** **matrix**.  
31. **Workflow** **builder** **for** **brokers**.  
32. **Integration** **with** **AMS** **360** **next** **sprint**.  
33. **Salesforce** **AppExchange** **soon**.  
34. **SIEM** **integration** **native**.  
35. **Kafka** **events** **stream** **real-time**.  
36. **Data** **warehouse** **sync**.  
37. **BI** **tool** **certified**.  
38. **Customer** **managed** **keys** **BYOK**.  
39. **Column-level** **encryption** **productized**.  
40. **Field-level** **masking** **UI**.  
41. **AI** **bias** **audit** **report**.  
42. **Model** **cards** **for** **every** **release**.  
43. **Human-in-the-loop** **mandatory** **gates**.  
44. **Formal** **verification** **of** **prompts**.  
45. **Zero** **trust** **architecture** **diagram** **truth**.  
46. **Least** **privilege** **everywhere** **enforced**.  
47. **Annual** **DR** **drill** **customer-invited**.  
48. **Hot** **standby** **RPO** **zero**.  
49. **Enterprise** **pricing** **predictable** **without** **usage** **metering**.  
50. **Procurement** **cycle** **short** **because** **product** **feels** **enterprise**.

---

## TOP_50_PRODUCT_SCOPE_RISKS

1. **Bundling** **SearchForge** **lab** **into** **Intake** **price**.  
2. **Promising** **multi-tenant** **dashboard**.  
3. **Selling** **“AI accuracy”** **numerically**.  
4. **Expanding** **to** **home** **insurance** **without** **schema**.  
5. **Custom** **LLM** **fine-tunes** **per** **broker** **day** **one**.  
6. **Embedding** **carrier** **APIs** **—** **massive** **scope**.  
7. **OCR** **as** **perfect** **truth**.  
8. **WeChat** **as** **only** **channel** **—** **US** **broker** **pushback**.  
9. **Email** **channel** **parity** **unfinished**.  
10. **Mobile** **native** **app** **expectation**.  
11. **White-label** **branding** **depth**.  
12. **Per-state** **regulatory** **modules**.  
13. **Spanish** **support** **assumed**.  
14. **Voice** **intake** **mentioned** **on** **deck**.  
15. **Quote** **generation** **—** **out** **of** **scope** **danger**.  
16. **Claims** **processing** **—** **wrong** **product**.  
17. **Policy** **admin** **system** **replacement** **narrative**.  
18. **CRM** **replacement** **narrative**.  
19. **“Automate** **the** **broker”** **—** **trust** **collapse**.  
20. **Underwriting** **decision** **support** **—** **EO** **risk**.  
21. **Marketing** **campaign** **features**.  
22. **Lead** **gen** **from** **intake** **—** **privacy** **war**.  
23. **Cross-sell** **engine**.  
24. **Commission** **tracking**.  
25. **Agency** **management** **reporting**.  
26. **Accounting** **integrations**.  
27. **Payroll** **integrations**.  
28. **License** **renewal** **tracking**.  
29. **Producer** **appointment** **workflows**.  
30. **Carrier** **appointment** **analytics**.  
31. **COI** **generation** **—** **maybe** **adjacent** **but** **high** **risk**.  
32. **Document** **templates** **legal** **enforceability** **claimed**.  
33. **E-signature** **—** **vendor** **scope**.  
34. **Customer** **portals** **for** **insureds** **—** **support** **explosion**.  
35. **Multi-language** **legal** **disclaimers** **machine-translated**.  
36. **Compliance** **copilot** **for** **agents** **—** **EO** **minefield**.  
37. **Real-time** **rate** **comparison** **—** **data** **licensing** **hell**.  
38. **Telematics** **integration** **—** **no**.  
39. **IoT** **—** **no**.  
40. **Blockchain** **—** **please** **no**.  
41. **“Platform** **ecosystem”** **before** **second** **customer**.  
42. **App** **store** **for** **broker** **plugins**.  
43. **Workflow** **marketplace**.  
44. **AI** **agent** **that** **binds** **coverage** **—** **no**.  
45. **Automatic** **policy** **issuance** **—** **no**.  
46. **Integration** **with** **state** **DMV** **APIs** **beyond** **RAG**.  
47. **Deep** **integration** **with** **WeChat** **Pay** **—** **fintech** **scope**.  
48. **Internationalization** **—** **goal** **doc** **says** **US-only**.  
49. **Franchise** **billing** **models** **—** **finance** **complexity**.  
50. **PE** **rollup** **story** **before** **NPS** **exists**.

---

# PHASE 4 — ARCHITECTURE CONVERGENCE (DETAILED)

## WHAT IS THE REAL SAAS SHAPE (HONEST CURRENT + TARGET)

- **Deployment:** One **monolith** API + static SPA; **profile flag** for surface reduction; **not** k8s service mesh today.  
- **Tenant:** **`client_id` + optional asserted org** — evolve to **server-issued** stable tenant id.  
- **Support:** **Manifest + minimal case metadata + git/epoch** — evolve to **scoped keys** + **export bundles** + **ticketing correlation**.  
- **Replay:** **Regression artifacts** + **live nondeterministic** — separate **legal** lane later.  
- **Onboarding:** **Pack files + env** — evolve to **validated** packs + **checklist** + **staging** slot.  
- **Pricing:** **Contractual** — software tracks **usage** poorly today.  
- **Scaling:** **Vertical** + **few env knobs** — **RLS** + **rate limits** before **100 offices** honestly.  
- **Org shape:** **Flat** — **no** **hierarchy** table.  
- **IAM evolution:** See below — **no** **big-bang** **IdP**.  

## AUTH_EVOLUTION_PATH

| Stage | Mechanism | Build now? |
|-------|-----------|------------|
| **Perimeter** | Cloud Run / VPC / IP allowlist where applicable | **Yes** (ops) |
| **Support keys** | `UNIFIED_INTAKE_SUPPORT_API_KEY` required in prod **policy** | **Yes** (config + runbooks) |
| **Org-bound identity** | Move from **`X-Org-Id` assertion** to **signed** org context **later** | **No** full IdP |
| **JWT** | Service-issued tokens with **tenant claim** | **Later** |
| **IdP** | SAML/OIDC for **broker staff** | **Much later** |
| **NOT now** | Full **OAuth** customer login UI, **RBAC** matrix product | **Explicit non-goals** |

## TENANT_EVOLUTION_PATH

1. **Keep** `client_id` **as** config key **+** DB discriminator.  
2. **Persist** **server-side** **org_id** when sales assigns **—** stop relying on **header alone**.  
3. **Nullable** **`tenant_id_authoritative`** **already** in schema — **populate** only with **verified** issuance.  
4. **RLS** **after** **stable** **tenant key** + **migration** plan **—** not **header RLS**.  
5. **Support replay:** attach **manifest** triple (**git**, **epoch**, **persistence mode**) **to** every **export**.  

## SUPPORT_SYSTEM_V2 (TARGET INCREMENTS)

- **Support export** with **redaction** profiles **+** **actor** + **deployment** + **schema** lineage fields (`audit_export.future_export_bundle_keys` direction).  
- **Escalation:** define **L1** scripts (**manifest**, **health**, **flags**) **—** **L2** **DB** **read-only** **playbook**.  
- **Support-safe tools:** **read-only** **SQL** **recipes**, **no** **write** **in** **prod** **without** **two-person** rule **(process)**.  

## ONBOARDING_FACTORY_MODEL (OPERATIONAL, NOT SOFTWARE MAGIC)

1. **Pack validation** (filesystem) **→** **extend** to **JSON schema** validation **incrementally**.  
2. **Deployment template:** **single** **reference** **compose/env** **file** per **hosting** choice.  
3. **Env generation:** **scripted** **from** **template** **—** **human** **sign-off**.  
4. **Rollout checklist:** **flags**, **DB**, **support** **key**, **epoch** **display** **in** **health** **probe**.  
5. **Rollback checklist:** **prior** **image** **tag** **+** **flag** **flip** **matrix**.  
6. **Activation:** **broker** **UAT** **3** **cases** **minimum**.  
7. **Support handoff:** **internal** **doc** **with** **manifest** **curl** **examples**.  
8. **Operator readiness:** **trial_readiness_check** **PASS** **gate**.  

---

# PHASE 5 — SMALL SAFE IMPLEMENTATIONS (ALLOWLIST)

**Examples aligned with repo direction:** product boundary tightening; **require** support key in prod via **runbook** + optional **assert** behind **`ENV=prod`** (careful — behavior change); deployment lineage already on **health**; **org-bound replay metadata** via existing **`tenant_truth`** on manifests; pack layout validator **extensions**; **product-only** route tests (`test_deployment_profile.py` pattern).

**Disallow:** giant IAM, **fake** self-serve signup, **OAuth** frontends per goals doc scope.

---

# PHASE 6 — VALIDATION (SPRINT EXECUTION)

| Check | Result (2026-05-08) |
|-------|---------------------|
| **compileall** `services/fiqa_api` | **PASS** |
| **pytest** `test_deployment_profile.py` `test_pack_validation.py` | **PASS** |
| **Full pytest / npm build / madge / guardrail scripts** | **Not re-run in full** in this session — **required** before **release** per `AGENTS.md` |

---

# PHASE 7 — REMAINING GAPS (TOP 50 remaining risks + TOP 30 × 6 categories)

## TOP_50_REMAINING_RISKS

1. No server-issued **tenant_id_authoritative** (always null).  
2. Support export routes **anonymous_ok** when support key unset.  
3. LLM triage **nondeterminism** vs broker dispute expectations.  
4. Dual-write / JSON / PG **read-your-writes** hazards across instances.  
5. Founder-shaped **L1–L3** support scaling limit.  
6. No **usage metering** → pricing fights at scale.  
7. No **rate limiting** → abuse + noisy neighbor.  
8. Single Postgres → **noisy neighbor** latency + IO.  
9. **audit_export** is stub → **no compliance WORM**.  
10. No **SIEM** / centralized security analytics.  
11. **Schema epoch** label vs **actual** DB migration discipline gaps.  
12. Attachment storage **unbounded** → cost + malware handling undefined.  
13. **Secrets** sprawl across env + founder laptops (process risk).  
14. **Staging ≠ prod** parity for flags repeatedly observed risk class.  
15. Incident **customer comms** process not productized.  
16. Legal **export bundle** not implemented (`future_export_bundle_keys` only).  
17. **Data residency** promises incompatible with single-region pilot.  
18. No **RBAC** for broker staff in product.  
19. No **OAuth / SSO** per scope guardrail — intentional gap remains **risk** when oversold.  
20. No **automated billing** — revenue reconciliation manual.  
21. No **versioned public API** contract — breaking changes surprise integrators.  
22. No **customer-facing status page**.  
23. No **on-call** paging integration — founder SPOF.  
24. **Runbook drift** vs deployed reality (docs/code mismatch class).  
25. Third-party **LLM vendor** outage / quota → unresolved SLA narrative.  
26. **CVE / dependency** response not formalized.  
27. **Support key rotation** without integration hooks → breakage risk.  
28. **Multi-region / DR** absent — procurement mismatch risk.  
29. **Backup restore** drills unproven → disaster truth unknown.  
30. **Sales scope creep** vs frozen SKU boundary.  
31. **Trust erosion** when marketing uses “tenant” language incorrectly.  
32. **PII** accidental inclusion in events/logs — policy not enforced in code.  
33. **case_id** treated as credential in broker workflows — social engineering.  
34. **WeChat** credential complexity — ops fragility.  
35. **Mobile / WebView** session edge cases — support load.  
36. **OCR** variance — expectations risk.  
37. **Prompt** changes without release notes — customer distrust.  
38. **Analytics** misinterpreted as per-customer BI.  
39. **Product-only** discipline depends on code review — future inline route regression risk.  
40. **Langfuse** optional — tracing gaps when disabled.  
41. **Qdrant/embed** readiness coupling — “app down” perception from `/ready`.  
42. **Instrumented regression** vs live divergence — false confidence.  
43. **Customer IT** blocks headers/paths — integration failures outside control.  
44. **Concurrent editing** — undefined semantics on case updates.  
45. **Cross-office** identity collision stories — no merge product.  
46. **Insurance compliance** wording — EO exposure if product implies advice.  
47. **Internationalization** pressure vs US-only goal doc.  
48. **Pen-test** findings on optional-auth surfaces — enterprise procurement friction.  
49. **DPA / subprocessors** maintenance burden — failure mode is **deal stall**.  
50. **This convergence doc** misread as **warranty** → liability illusion (operational misinterpretation risk).

## TOP_30_NOT_ENTERPRISE_READY

1. **No SSO**  
2. **No org hierarchy**  
3. **No audit WORM**  
4. **No DPA automation**  
5. **No SOC2 program**  
6. **No SIEM**  
7. **No dedicated single-tenant offering**  
8. **No formal RBAC**  
9. **No field-level ACL**  
10. **No data residency options**  
11. **No contractual SLA instrumentation**  
12. **No enterprise billing**  
13. **No procurement integrations**  
14. **No vendor risk portal**  
15. **No formal DR drills**  
16. **No customer-managed keys**  
17. **No tamper-proof logs**  
18. **No legal hold workflow**  
19. **No eDiscovery exporter**  
20. **No pen-test fix SLA process**  
21. **No 24/7 staffing**  
22. **No formal change advisory board**  
23. **No ISO docs**  
24. **No subprocessors diligence pack maintained**  
25. **No uptime calculation agreed**  
26. **No multi-region failover**  
27. **No zero-downtime DB migration strategy productized**  
28. **No formal API deprecation policy**  
29. **No enterprise support tiers encoded**  
30. **No centralized identity for broker users**

## TOP_30_SUPPORT_GAPS

1. No ticketing integration — trace IDs not mapped to Zendesk/Jira IDs.  
2. No redacted full-case export for legal/support bundles.  
3. No customer-legible “replay story” for nondeterministic LLM outputs.  
4. L1 playbooks exist informally, not as enforced scripts + checks.  
5. Weak trace correlation from broker symptom → `request_trace_id` → internal logs.  
6. No customer-facing incident or correlation ID surfaced consistently in UI.  
7. No public status page — outages perceived as “silent failures.”  
8. No paging/on-call integration — escalation latency unpredictable.  
9. No SLA clock encoded — deadlines exist only in contracts (if at all).  
10. Attachment diagnostics shallow — reproducing OCR/upload failures is hard.  
11. Mobile reproduction kits absent — WebView/session bugs costly to debug remotely.  
12. Multilingual support scripts incomplete vs bilingual brokers.  
13. No training academy — every office trains differently.  
14. No CRM links — cases don’t round-trip to AMS/HubSpot automatically.  
15. Case merging/splitting unsupported — duplicates inflate workload.  
16. Permissions model absent — who may view which case is socially enforced only.  
17. PII scrubbing pipeline for exports absent — manual redaction risk.  
18. Legal export workflow missing — “send everything” requests stall.  
19. Retention policies not operationalized in product tooling.  
20. Subprocessors mapping not maintained as operational artifact.  
21. Support key rotation without automated notifier to integrations.  
22. Webhooks/notifications for case state absent — brokers chase manually.  
23. Bulk operations absent — scale hurts ops when correcting mistakes.  
24. Safe read-only SQL tooling wrappers absent — engineers tempted toward risky prod queries.  
25. Performance profiling per case missing — “slow case” investigations expensive.  
26. Customer analytics truth unclear — dashboard vs broker intuition conflicts.  
27. Noise vs defect separation weak — support burns on UX misunderstandings.  
28. Executive summaries for incidents absent — founders narrate each time.  
29. Support impersonation story absent — only shared-secret posture exists.  
30. Escalation tiers not contractually aligned with tooling reality.

## TOP_30_DEPLOYMENT_GAPS

1. No canary deployments — everyone gets each release equally.  
2. No blue/green — rollback is redeploy prior artifact (manual).  
3. No automated rollback orchestrator beyond CI/CD habits.  
4. Weak staging vs prod env parity for persistence flags.  
5. Secrets rotation cadence undefined — drift risk.  
6. DB migrations not uniformly gated by CI smoke + checklist.  
7. Multi-instance deployments unsafe if JSON-first reads/writes ever enabled.  
8. Observability vendor optional — traces inconsistent.  
9. Cost caps absent — LLM/Qdrant spend surprises possible.  
10. Rate limiting absent at edge — abuse risk.  
11. Regional DR absent — enterprise procurement mismatch.  
12. Artifact pinning inconsistent — `:latest` anti-pattern risk.  
13. Staging data hygiene weak — risk of confusing test/real cases mentally.  
14. Network egress controls not productized — customer VPC requirements hard.  
15. Dependency pinning policy incomplete — supply-chain surprises.  
16. Image scanning gate not guaranteed in all pipelines.  
17. Runtime threat detection absent — runtime integrity not monitored.  
18. Autoscaling tuning undocumented — cold start vs cost tradeoffs unclear.  
19. Connection pool sizing per tier absent — thundering herd risk.  
20. Backup verification absent — restores may fail first real disaster.  
21. Restore runbook often unexercised — RTO/RPO fiction.  
22. Load testing not continuous — surprises at traffic spikes.  
23. SLO definitions absent — error budgets meaningless.  
24. Deployment windows undefined — customer-visible instability risk.  
25. Customer notification process for maintenance absent.  
26. Multi-team RACI for incidents informal — confusion during outages.  
27. Infrastructure-as-code incomplete — drift between consoles and repo.  
28. Config drift detection absent — “works on my deploy” class failures.  
29. Edge CDN + API versioning alignment absent — cache skew risk.  
30. Database capacity planning per customer tier absent.

## TOP_30_OPERATOR_GAPS

1. Single-throat bottleneck on founder/lead engineer.  
2. Runbook currency — docs lag flags and code.  
3. No formal on-call rotation — fatigue risk.  
4. No paging integration — incidents discovered late.  
5. Chaos drills absent — untested failure recovery.  
6. Env matrix SSOT scattered across scripts vs single checked-in table.  
7. Customer-specific flag tracking informal — “who has dual-write on?” unknown without digging.  
8. Incident templates incomplete — each incident bespoke.  
9. Postmortems optional — repeat failures likely.  
10. KPI dashboard for ops absent — leading indicators invisible.  
11. Customer comms ownership unclear during incidents.  
12. License tracking for dependencies weak — renewal/legal surprises.  
13. Cost observability partial — surprise bills possible.  
14. Manual UI deploy steps — human error class.  
15. Browser cache guidance for brokers under-documented — false bug reports.  
16. Secrets-in-CI hygiene varies — leak class risk.  
17. Access reviews informal — stale credentials linger.  
18. Least privilege in cloud consoles not enforced — blast radius large.  
19. Database hygiene (vacuum/index) not automated — gradual degradation.  
20. Log retention choices not aligned with legal/support needs.  
21. PII in logs audit cadence weak — accidental logging risk.  
22. Support key lifecycle ownership unclear — unauthorized continued access.  
23. Access logs for support routes absent — cannot prove who exported what.  
24. Customer-facing change logs absent — upgrades feel mysterious.  
25. Versioning discipline for prompts/config bundles informal.  
26. Dependency upgrade cadence uneven — security debt accumulates.  
27. CVE monitoring not systematic — reactive patching.  
28. Vendor subscription renewals (LLM, observability) can lapse silently.  
29. Laptop endpoint security expectations for operators undefined.  
30. Handoff between sales promises and deployable reality ungoverned.

## TOP_30_ONBOARDING_FAILURES

1. Incomplete packs still pass too late — only filesystem presence checked deeply today.  
2. JSON typos in packs discovered at runtime, not validation time.  
3. WeChat credentials discovered missing during go-live week.  
4. Wrong `DATABASE_URL` / service record URL — persistence surprises.  
5. Wrong flags for reads vs writes — split-brain symptoms.  
6. Customer IT firewall blocks endpoints — emergency reroutes.  
7. No training videos — adoption variance.  
8. Language mismatch — Chinese/English expectations mis-set.  
9. Unclear SLA — disappointment when informal response times slip.  
10. Success metrics not agreed — pilot ends ambiguously.  
11. UAT cases too shallow — real traffic exposes gaps.  
12. Founder-only kickoff scheduling bottleneck delays revenue.  
13. No internal champion on broker side — tool abandonment risk.  
14. Data migration expectations unrealistic — scope explosion.  
15. Parallel pilot commitments overload founder capacity.  
16. Support contacts unclear — customers route randomly.  
17. Legal review delays contract — timeline slips.  
18. Branding assets arrive late — broker trust suffers.  
19. Wrong `client_id` in demo URL — confused testing.  
20. Prod vs staging confusion — accidental “tests” in prod narrative.  
21. Mobile testing omitted — WebView bugs dominate early support.  
22. Attachment size limits unknown — failures feel like “bugs.”  
23. Concurrent user assumptions wrong — performance disappointment.  
24. No rollback rehearsal — first rollback is high stress.  
25. Customer expects AMS integrations early — relationship damage.  
26. Internal broker staff untrained — inconsistent usage patterns.  
27. Escalation path unclear — frustration spikes.  
28. Pricing dispute before value proof — churn before traction.  
29. Scope creep during kickoff — engineering dragged.  
30. Sales-to-CS handoff missing — expectations not operationalized.

## TOP_30_TENANCY_GAPS

1. No authoritative server-issued tenant identifier in requests.  
2. No Postgres RLS — shared tables are faith-based separation at app layer only.  
3. No per-tenant encryption keys — only deployment defaults.  
4. No per-tenant rate limits — noisy neighbor unbounded.  
5. No per-tenant LLM budget enforcement — cost attribution impossible.  
6. No per-tenant feature flags productized — customization becomes forks.  
7. Header spoofing possible for `X-Org-Id` — analytics integrity only, but disputes arise.  
8. Misconfigured exports could theoretically blend customer narratives — process risk.  
9. Shared object storage bucket story undefined for future attachments scale.  
10. No tenant provisioning API — humans create IDs.  
11. No tenant deletion workflow — retention chaos long-term.  
12. No tenant merge/split — acquisitions fail at data layer story.  
13. No org-domain verification — anyone can assert org-like identifiers socially.  
14. No service accounts per office — automation identity absent.  
15. No SCIM — enterprise HR-driven provisioning fantasy incompatible.  
16. IP allowlists not productized — sensitive deployments can’t lock down easily.  
17. No per-tenant audit export — enterprise asks stall.  
18. No per-tenant backup story — DR promises fragile.  
19. No per-tenant schema migration strategy — global migrations only.  
20. Shared queues futures risk — if introduced without isolation, cross bleed.  
21. Shared cache futures risk — same concern for horizontal scale-out.  
22. Idempotency keys not tenant-scoped — cross-customer id collision class risk in integrations.  
23. Support tools can fat-finger wrong `case_id` / tenant context — human error.  
24. Test tenants colliding with prod naming conventions — mistaken routing risk.  
25. Staging tenant hygiene weak — test data confusions.  
26. No tenant metadata service — “who is client X?” lives in spreadsheets.  
27. Founder mental map is not SSOT — bus factor + inconsistency.  
28. No hierarchical org structure — franchise/RPG scenarios unsupported honestly.  
29. No delegated admin roles — every broker staff is implicit superuser of their workflow.  
30. Future RLS migration path unpurchased — engineering liability when forced by incident.

## TOP_30_REPLAY_GAPS

1. No signed export bundles — evidentiary chain weak.  
2. No standardized raw LLM trace export for disputes — vendor/tooling dependent.  
3. No immutable storage — tamper resistance unproven.  
4. Nondeterminism not broker-legible — “why different?” escalations costly.  
5. Role C simulation can be confused with production truth if mis-marketed.  
6. Prompt snapshots not bound per case message uniformly — causality unclear.  
7. Model/version fields not consistently persisted per turn for all paths.  
8. Attachment checksum chain-of-custody absent — integrity disputes hard.  
9. No customer-readable replay narrative export — engineering-only artifacts.  
10. No legal hold workflow — discovery requests become panic.  
11. Redaction profiles not automated — manual effort + mistakes.  
12. No diff viewer between regression golden vs live output — arguments persist.  
13. No cross-device session replay — state discrepancies unexplained.  
14. Trace IDs not consistently surfaced to broker UX — support friction.  
15. No export SLA — enterprise timelines unmet.  
16. Consent granularity for exports absent — privacy friction.  
17. No broker employee access log for case views — insider abuse ambiguity.  
18. No cryptographic timestamping — repudiation risk in disputes.  
19. No third-party witness storage — trust model is internal-only.  
20. No standardized dispute evidence package — each fight bespoke.  
21. No regulator-friendly narrative generator — enterprise procurement stalls.  
22. Weak correlation across sessions for same individual — story fragmentation.  
23. Deterministic rebuild from inputs only where scripted regression exists — partial coverage.  
24. Divergent stores (JSON vs PG) can yield incomplete histories — replay ambiguity.  
25. Versioned triage contract per case not stored as first-class row — contract drift hunting via logs only.  
26. No exactly-once messaging semantics — duplication edge cases under stress.  
27. No tamper detection on historical JSON/files — integrity debates linger.  
28. Partial mitigation reliance on manifest triple — necessary but insufficient for legal-grade replay.  
29. Live LLM outputs may lack retrieval citations packaged for audit — narrative gap vs RAG demo promises.  
30. Post-incident reproduction across releases hard — config + model drift stacks.

---

# PHASE 8 — FINAL OUTPUT (REQUIRED ANSWERS)

*(Duplicate this section in chat by the agent — see assistant message.)*

1. **REAL SaaS now:** Single deployable **Unified Intake** module with **honest** health/manifest **lineage**, optional **support gate**, **explicit** non-authoritative **tenant** fields — **pilot-grade**, **not** enterprise-isolated SaaS.  
2. **Fake SaaS:** **Tenant isolation**, **enterprise IAM**, **immutable audit**, **usage-based billing**, **multi-tenant analytics truth** — **not** shipped.  
3. **Real tenant truth:** **`client_id`** **+** **Postgres** **discriminator** **+** **filesystem** **packs**; **`tenant_id_authoritative` = null**.  
4. **Tenant illusion:** Treating **`X-Org-Id`** **or** **`client_id`** **as** **security** **boundary**.  
5. **Real support system:** **Manifest + case-head + dual auth posture reporting + schema epoch + git SHA.**  
6. **Support illusion:** **Enterprise** **ticketing**, **signed legal export**, **deterministic** **“replay button.”**  
7. **Real replay lineage:** **Regression** **artifacts** **+** **operator** **manifest** **triple** **(git/epoch/persistence)** **for** **engineering** **triangulation**.  
8. **Replay illusion:** **Guaranteed** **verbatim** **AI** **replay** **for** **disputes**.  
9. **Breaks at 30 offices:** **Founder/support throughput**, **config collisions**, **anonymous support intel**, **no rate limits**, **no per-customer cost accounting**.  
10. **Breaks at 100 offices:** **Operational coordination**, **DB noisy neighbor**, **incident** **and** **legal** **requests** **without** **enterprise** **artifact** **pipeline**.  
11. **Enterprise sales breaks on:** **SOC2/SSO/data residency/audit** **expectations** **vs** **honest** **capabilities**.  
12. **Biggest founder dependency:** **Escalation path defaults to founder** for **auth/env/incident** **story** **not** **productized**.  
13. **Biggest onboarding blocker:** **Manual** **env** **+** **contractual** **scope** **clarity** — **not** **missing** **UI** **wizard**.  
14. **Biggest support blocker:** **No redacted full export + no ticketing correlation + nondeterministic AI narrative**.  
15. **Biggest tenancy blocker:** **No server-issued tenant identity + no RLS**.  
16. **Biggest deployment blocker:** **Env/persistence flag complexity** **without** **customer-visible** **“mode”** **UX**.  
17. **Biggest enterprise blocker:** **Compliance + IAM artifacts** **don’t** **exist** **at** **required** **maturity**.  
18. **Best 10× leverage:** **Require support keys + staged readonly DB playbooks + freeze SKU narrative** **before** **scaling offices**.  
19. **Best next sprint:** **Operational close:** **prod policy for support key**, **runbook SSOT env matrix**, **JSON schema validation** **for** **packs** **(small)**.  
20. **Best 3-month roadmap:** **Pilot #2 revenue**, **harden support exports**, **tenant id issuance design**, **rate limits**, **dispute export MVP** **(redacted)**, **explicit** **API** **versioning** **plan** — **no** **big** **IdP**.  
21. **Should NOT be built yet:** **Full SAML**, **RBAC UI**, **self-serve signup**, **Stripe**, **RLS** **without** **tenant** **issuance**, **another vertical**.  
22. **FINAL_ONE_LINE:** **Unified Intake is a pilot-honest intake monolith with manifests and nullable tenant authority — charge for workflow value, not for imaginary isolation.**

---

## REFERENCES

- `services/fiqa_api/deployment_profile.py` — `INTAKE_SCHEMA_EPOCH`, `is_unified_intake_product_only`, empty inline leak tuple.  
- `services/fiqa_api/app_main.py` — router gating, `/health` deployment_profile block.  
- `services/fiqa_api/security/support_export_gate.py` — optional API key behavior.  
- `services/fiqa_api/security/request_identity.py` — client assertion honesty.  
- `services/fiqa_api/routes/inbox_triage.py` — support manifest + case-head.  
- `docs/goals/insurance_paid_pilot_goal.md` — business scope truth.
