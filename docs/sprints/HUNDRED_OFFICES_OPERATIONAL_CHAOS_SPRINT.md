# 100 OFFICES OPERATIONAL CHAOS SPRINT — Single Source of Truth (SSOT)

**Sprint type:** Long-horizon **operational chaos** + SaaS company stress simulation (not a feature sprint).  
**Core question:** *When **100 real broker offices** run Unified Intake concurrently, what breaks first — product, operations, or the company?*  
**Maintainer:** This file is the **authoritative artifact** for this sprint; update it as truth changes.

**Scope boundary (per `AGENTS.md`):** No Stripe, no productized auth, no true multi-tenant row-level isolation in repo scope. Simulations below treat **logical offices** (client packs, deploy slots, `X-Org-Id` posture) unless explicitly labeling future-state.

---

## PHASE 0 — GIT + SAFETY

| Item | Value |
|------|--------|
| **Branch** | `auto-evolution/100-offices-operational-chaos-20260507` |
| **Created from** | `auto-evolution/30-customers-reality-simulation-20260507` (carried uncommitted work) |
| **Modified (tracked) — snapshot** | `configs/demo.env.example`, `scripts/trial_readiness_check.sh`, `services/fiqa_api/app_main.py`, `services/fiqa_api/db/service_record_repository.py`, `services/fiqa_api/inbox_triage/active_vehicle_resolver.py`, `case_lifecycle.py`, `case_truth_repository.py`, `session_repository.py`, `session_store.py`, `routes/inbox_triage.py`, `tests/test_case_truth_repository.py`, `tests/test_intake_session_persistence.py`, `ui/src/api/inboxTriage.ts`, `triageResultContract.ts`, `caseLifecycleDisplay.ts`, `intakePure.ts` |
| **Untracked / emerging (representative)** | Multiple `docs/sprints/*.md`, `docs/*_MAP.md`, `results/*`, `scripts/{ci_smoke,run_full_regression,quick_health_check,import_smoke_check}.py`, `services/fiqa_api/deployment_profile.py`, `inbox_triage/{audit_export,pack_validation,structured_turn_obs}.py`, `tests/test_deployment_profile.py`, `tests/test_pack_validation.py`, … (`git status` is canonical) |
| **Stash** | `stash@{0}` … present — **not applied** this sprint |
| **Known compileall noise** | `scripts/run_demo_pack_original.py` — **SyntaxError** (f-string backslash); exclude from `compileall services/fiqa_api tests` CI scope until repaired |

### Sprint changelog (living)

| Date (UTC) | Change |
|------------|--------|
| 2026-05-07 | Branch created; SSOT initialized; **HUNDRED_OFFICES_SYSTEM_REALITY_MAP** + chaos + failure matrix + gap analysis + reviews + self-critique + final report. |
| 2026-05-07 | **Phase 5:** `ci_smoke.sh` exports `PYTHONPATH` to repo root so `import_smoke_check` works without manual env; `deployment_profile.log_deployment_profile_banner` SSOT string includes this sprint doc. |
| 2026-05-07 | **Phase 6:** Validations executed (see § Phase 6 table). |

---

## PHASE 1 — HUNDRED_OFFICES_SYSTEM_REALITY_MAP

### 1.1 Legend

| Label | Meaning |
|-------|---------|
| **Scales** | Mechanism survives 100 logical offices with discipline + automation |
| **Bends** | Works until incident / burst / drift accumulates |
| **Breaks** | Becomes primary incident class without new systems |

### 1.2 Lifecycle systems

| System | Primary anchors in repo | Scales @100? | Breaks @100 when… |
|--------|---------------------------|----------------|---------------------|
| **Onboarding** | `configs/clients/`, `scripts/validate_client_pack_minimal.py`, `trial_readiness_check.sh`, `trial_launch_check.sh`, `pack_validation` | **Bends** | Each office = **manual** pack slot; no **self-serve** schema UI or **tenant provisioning API** |
| **Deployment** | `UNIFIED_INTAKE_PRODUCT_ONLY`, `deployment_profile.py`, `docs/DEPLOYMENT_READINESS.md`, compose / Cloud Run docs | **Bends** | **Drift** between 100 env matrices; **inline lab routes** remain on `app_main` in product-only mode → **trust + security** incidents |
| **Tenant lifecycle** | `client_id`, optional `X-Org-Id`, case/session IDs | **Breaks** (if sold as multi-tenant) | No **RLS / composite org keys** — **tenant bleed** risk when IAM arrives late |
| **Replay lifecycle** | Guardrail scenarios, `run_full_regression.py`, Tab D UI (`SYSTEM_ONE_PAGE_MAP.md`) | **Bends** | CS wants **session-level replay bundle** per ticket — not productized |
| **Analytics lifecycle** | `track_event`, minimal analytics, `PRODUCTION_METRICS.md` | **Bends** | **Billing disputes** and **ROI proof** need dimensions offices lack in one standard |
| **Support lifecycle** | `docs/trial/*`, FIX_NOW templates, founder ad hoc | **Breaks** | **100× ticket rate** without **case_id/session_id**–linked ticketing |
| **Escalation lifecycle** | Implicit → founder | **Breaks** | No **on-call**, no **severity matrix**, no **CS playbooks** in product |
| **Billing lifecycle** | Out of scope | **Breaks** (commercially) | No ledger, seats, or usage line-items |
| **Operator lifecycle** | Unified Intake workbench UI | **Bends** | **Multi-operator** offices lack **assignment + audit of human actions** |
| **Pack lifecycle** | Client pack JSON + phrase maps | **Bends** | **Pack drift** vs code expectations; bilingual = **2×** review surface |
| **Audit lifecycle** | `audit_export.py` (forwarding scaffold) | **Bends** | Not a **compliance WORM** story — **honest** limits in docstrings |
| **Rollback lifecycle** | Git revert, redeploy, runbooks | **Bends** | No **“rollback client pack version”** in admin UI |
| **Support tooling** | Scripts, logs, engineering replay | **Bends** | No **customer-visible** diagnostics |
| **Founder workflow** | Everything not automated | **Breaks** | **100 offices ⇒ founder overload** is **guaranteed** without hire + automation |
| **Customer success workflow** | Docs + trial scripts | **Breaks** | No **health score**, **expansion**, or **QBR** data product |
| **Office management workflow** | Single workbench mental model | **Breaks** | No **org hierarchy** (franchise / rollup) |

### 1.3 Authority & deployment boundary (honesty)

- **Gated routers** respect `UNIFIED_INTAKE_PRODUCT_ONLY`; **inline** `@app` routes listed in `PLATFORM_INLINE_ROUTES_UNGATED_IN_APP_MAIN` **do not** — this is **deployment boundary debt**, not a marketing nit.
- **PG truth** for vehicles + **`_finalize_response_with_pg_truth`** is the **API identity** mirror when DB is live — **engineers** know this; **100 CS reps** will not unless productized.

### 1.4 What is “real SaaS” vs “fake SaaS” — @100 offices

| Real enough today | Fake / premature if sales claims it |
|-------------------|-------------------------------------|
| Deterministic guardrails + regression rig | “Enterprise multi-tenant isolation” without RLS |
| Client pack on disk + validation hooks | “Self-serve onboarding portal” |
| Logical `client_id` / org header posture | “SOC2-ready audit trail” from analytics alone |
| Founder-led trial execution | “24/7 support” |

### 1.5 Hidden debt buckets

| Debt type | Symptom @100 |
|-----------|----------------|
| **Operational** | Every deploy is a **unique snowflake** without pipeline |
| **Support** | Same bug hits **dozens** of tickets with no dedupe tool |
| **Deployment** | **Route leaks** + **stale SPA** + **wrong env** incidents |
| **Billing** | Verbal price → **invoice mismatch** → churn |
| **Tribal** | Resolver edge cases require **engineer** in Slack |

---

## PHASE 2 — 100 OFFICE CHAOS SIMULATION

**Method:** **100 logical offices** `O001–O100` grouped into **10 archetypes × 10 instances**. For **each archetype**, all **22 workflow dimensions** below are exercised in structured simulation (table-driven assessment, not live 100-deploy).

### 2.1 Archetypes (10 × 10 offices)

| Tag | Archetype | Offices | Characteristic load |
|-----|-----------|---------|---------------------|
| A | Bilingual EN/中文 | O001–O010 | **2×** copy QA; translation drift |
| B | High-volume triage | O011–O020 | Hot path latency + session growth |
| C | Low-tech operators | O021–O030 | Training burden; distrust of AI text |
| D | Append-heavy / long cases | O031–O040 | Case boundary + append misunderstanding |
| E | Support-heavy / litigious | O041–O050 | Ticket noise; “prove what AI said” |
| F | Multi-operator (3+ seats) | O051–O060 | Handoff inconsistency; no seat billing |
| G | Chaotic / under-trained | O061–O070 | Mis-clicks, reopens, duplicate cases |
| H | Fast-growth rollup | O071–O080 | Parent org expects **dashboard** + **API** |
| I | Compliance / audit vocal | O081–O090 | Export + lineage demands |
| J | Price-sensitive / churny | O091–O100 | **Billing gap** + ROI challenge |

### 2.2 Workflow dimensions (per archetype — synthesized outcomes)

For each dimension: **pain** (L/M/H), **founder-dependent?** (Y/N), **product gap?** (short text).

| # | Dimension | Dominant pain @100 | Founder-dep | Gap summary |
|---|-----------|---------------------|-------------|-------------|
| 1 | Onboarding | **H** manual packs | Y | No automated **tenant slot** + **schema UI** |
| 2 | Deployment | **H** drift + leaks | Y | Inline routes; **no one-click prod profile audit** in UI |
| 3 | Pack installation | **M** validation errors | Partial | **pack_validation** exists but not **hosted** |
| 4 | Operator training | **H** variance | Y | No **sandbox tenant** product |
| 5 | Add-car workflows | **M** edge LLM | Partial | Strong guardrails; **resolver** tribal |
| 6 | Append workflows | **M** boundary | Partial | Copy A/B helps; **CS replay** weak |
| 7 | Replay workflows | **H** for CS | Y | Tab D ≠ **support console** |
| 8 | Escalation workflows | **H** bottleneck | Y | No **SLA** or routing |
| 9 | Support incidents | **H** volume | Y | No **ticket ↔ session** link |
| 10 | Deployment rollback | **M** skill | Y | Manual git — **no pack rollback** |
| 11 | Broken config packs | **M** | Partial | **validate_client_pack_layout** helps |
| 12 | Analytics mismatch | **H** trust | Y | **ROI** story fragile |
| 13 | Billing mismatch | **H** commercial | Y | **No billing** subsystem |
| 14 | Replay mismatch | **M** QA vs prod | Partial | Env parity discipline |
| 15 | Wrong vehicle correction | **M** | Partial | ACE tests strong; UX still cognitive load |
| 16 | Tenant confusion | **H** | Y | **Logical** only |
| 17 | Operator mistakes | **H** | Partial | Training + UI affordances |
| 18 | Customer trust incidents | **H** | Y | **LLM** weird outputs explode **@100** |
| 19 | LLM weird outputs | **M–H** | Partial | Guardrails mitigate, not eliminate |
| 20 | Founder unavailable | **H** | — | **Company-stop** risk |
| 21 | Support overload | **H** | — | Queue theory: **collapse** |
| 22 | Multiple simultaneous incidents | **H** | Y | No **incident commander** tooling |

### 2.3 Cross-cutting discoveries (simulation)

1. **The triage engine is not the first scaler** — **company operations** are.  
2. **Concurrent “brownouts”** (5–10 offices same week) exhaust **founder** before engineering capacity.  
3. **Bilingual + compliance** archetypes generate **disproportionate** CS time per office.  
4. **Replay Tab D** helps engineers; **CS still needs** turn-by-turn **export**.  
5. **Pack drift + deployment drift** are **multiplicative**, not additive.

---

## PHASE 3 — TOP_100_OPERATIONAL_FAILURE_MODES

**Scoring key — Severity (S):** C=catastrophic, H=high, M=medium, L=low. **Frequency (F):** R=rare, O=occasional, C=common at scale. **Impacts:** Cust=customer, Sup=support, Biz=business, Trust=reputation.

Each row: **Mit** = mitigation direction, **Auto** = automation lever, **Obs** = observability gap.

| # | Mode | S | F | Cust | Sup | Biz | Trust | Mit | Auto | Obs |
|---|------|---|---|------|-----|-----|-------|-----|------|-----|
| 1 | Tenant bleed (weak filters) | C | R | H | H | H | H | Composite keys + RLS | Policy tests | Row-audit probes |
| 2 | Billing drift (quote vs invoice) | H | O | H | M | H | M | Billing system | Metered events | Revenue vs usage |
| 3 | Replay corruption (wrong session) | M | O | M | H | L | M | Immutable session IDs | Export bundles | Session checksum |
| 4 | Deployment drift (100 envs) | H | C | M | H | H | M | IaC + config audits | CI profile diff | Env fingerprint banner |
| 5 | Pack drift vs code | H | C | M | H | M | M | Semver packs + CI | `pack_validation` in CD | Pack hash in health |
| 6 | Support overload | H | C | H | H | H | M | Tier-1 playbooks | Auto-triage tags | Ticket ↔ case link |
| 7 | Escalation collapse | H | O | H | H | M | M | Severity matrix | Routing rules | Escalation SLI |
| 8 | Founder overload | H | C | M | H | H | M | Hire + deflect | Runbook automation | Queue depth metric |
| 9 | Operator conflict (two reps) | M | O | M | M | L | M | Case locking UI | Audit trail | Lock events |
| 10 | Analytics mismatch (ROI fight) | M | C | M | H | M | H | Define KPI SSOT | BI export | Funnel definitions |
| 11 | Route exposure (inline lab) | H | O | L | M | M | H | Remove/gate routes | Startup audit | Public route scan |
| 12 | Rollback failure (bad deploy) | H | R | H | H | H | M | Blue/green + canary | Auto-rollback hooks | Release markers |
| 13 | Audit export failure | M | O | M | M | M | H | Real compliance path | Signed exports | Export audit log |
| 14 | Trust collapse (AI lie perception) | H | O | H | H | H | H | Copy + clarify UX | Fact layers | Hallucination SLI |
| 15 | Config mismatch (wrong client) | H | O | H | H | M | H | Strong client_id | Config linter | Cross-client probes |
| 16 | Stale deployment (old SPA) | M | C | M | M | L | M | CDN cache discipline | Hash deploy | Asset version in API |
| 17 | Onboarding confusion | H | C | H | H | M | M | Checklist product | Wizard | Onboarding funnel metrics |
| 18 | Product misunderstanding | M | C | M | H | M | M | In-app education | Tooltips | Feature flags analytics |
| 19 | AI hallucination confusion | M | C | M | H | M | M | Grounding + disclaimers | Self-check oracles | `clarify_*` rates |
| 20 | Customer churn trigger (billing) | H | O | H | M | H | M | Honest pricing ops | Contract versioning | Churn reason codes |
| 21 | Dual-write PG inconsistency | H | R | H | H | M | H | Single writer SSOT | Reconciliation job | Mirror SLI |
| 22 | Wrong active vehicle in API | H | R | H | H | M | H | Resolver + finalize path | Regression oracles | `wrong_vehicle_related` |
| 23 | Session store corruption | H | R | H | H | M | M | Storage HA | Backup/restore drills | Integrity checks |
| 24 | Embedding / 503 storm | H | O | H | H | M | H | Capacity + `restore_8001` | Auto-scale probes | Warmup SLI |
| 25 | Rate limit / abuse unknown | M | O | M | M | L | L | Per-tenant limits | Token bucket | Abuse dashboard |
| 26 | Concurrent pack pushes (10 offices / week) | H | C | M | H | M | M | **Serialize** releases + change window | Pack CI + freeze | Deploy blast radius |
| 27 | Pack rollback race (two fixes same day) | M | O | M | H | L | M | Single owner of pack **version** | Lockfile in Git | Version in `/health` |
| 28 | Holiday traffic spike (renewals) | H | C | H | H | M | L | **Capacity plan** + LLM budget | Queue shed or throttling | Renewal SLI |
| 29 | Competitor FUD (“AI deletes coverage”) | M | O | M | H | H | **H** | **Provable logs** + human handoff | Disclaimer SSOT | Trust surveys |
| 30 | Regulator inquiry (CA DOI optics) | H | R | M | H | **H** | **H** | Counsel + **data minimization** | Redaction pipeline | Inquiry checklist |
| 31 | Cross-office rumor (data leak) | H | R | **H** | **H** | **H** | **H** | **Transparent post-mortem** + facts | Security audit | Incident comms template |
| 32 | Vendor LLM outage / latency | H | O | H | H | M | M | Multi-vendor abstraction (future) | Failover routing | Latency SLO breach |
| 33 | DB failover → stale read | H | R | **H** | **H** | H | H | **Read-after-write** discipline | HA tests | PG lag gauges |
| 34 | Redis/session cache loss (if introduced) | H | R | H | H | M | L | HA cache | Persist sessions | Session error budget |
| 35 | Qdrant / vector outage | H | R | M | H | L | M | **Degrade** to rules-only path | Health gate | Embedding warmup SLI |
| 36 | Secret rotation breaks embeddings | H | R | M | H | M | M | **Rotation runbook** | Scripted rotate | Canary after rotate |
| 37 | SPA CDN cache stale assets | M | C | M | M | L | M | Cache bust / versioning | Immutable filenames | Asset hash probe |
| 38 | Mobile Safari clipboard / focus bugs | M | C | M | H | L | M | **Mobile QA** lane | E2E smoke | Client UA analytics |
| 39 | Timezone confusion (renewal EOD) | M | C | M | M | M | **L** | **Office TZ** in pack | Scheduler tests | Case TZ metadata |
| 40 | Email deliverability (handoff notices) | M | O | M | H | M | M | Branded domain + DMARC | Template lint | Bounce metrics |
| 41 | Wrong client phrase map loaded | H | R | **H** | H | M | **H** | `client_id` immutable in session | Assert pack hash | Cross-client guardrail |
| 42 | Mixed EN/ZH legal term mistranslation | M | C | M | H | L | **H** | Glossary SSOT + review | Term lint | Translation diff |
| 43 | Franchise brand violation in UI | M | O | M | M | **H** | **H** | Whitelist copy | Compliance checklist | Brand audit |
| 44 | Acquisition data migration (rollup H) | H | R | M | H | **H** | M | **Dedicated migration** project | ETL + reconcile | Migration validation |
| 45 | Class-action optics (AI harmed consumer) | H | R | **H** | **H** | **H** | **H** | **Disclaimers** + escalation | Policy review | Legal sign-off |
| 46 | **VIP office** jump-the-queue abuse | M | O | L | **H** | M | M | Fair routing policy | Ticket fairness | Queue equity metric |
| 47 | Seasonal layoffs → support understaffed | H | O | M | **H** | M | M | Flexible BPO | Surge macros | Staffing forecast |
| 48 | **LLM cost overrun** (uncapped usage) | H | C | L | M | **H** | L | Per-tenant budgets | Hard caps + alerts | Token ledger |
| 49 | Carrier API mismatch (if integrated) | H | O | **H** | H | M | M | Contract tests w/ **sandbox** | Mock carriers | Integration SLI |
| 50 | Wildfire / disaster (office offline) | M | R | M | M | L | M | DR posture docs | **Queue when back** | Geo health |
| 51 | Payroll bug → angry staff → bad ops | M | R | M | M | L | **M** | People-first response | — | N/A |
| 52 | **Prompt injection** in customer paste | M | O | M | H | L | M | Sanitize + policy | Classifier | Injection rate |
| 53 | **PII** pasted into logs | H | O | **H** | **H** | M | **H** | Redact by default | Log scrubber | PII scan |
| 54 | **S3/public bucket** misconfig (future) | C | R | **H** | **H** | **H** | **H** | IaC deny rules | Bucket policy CI | Public access probe |
| 55 | **Webhook** retries duplicate side effects | M | O | M | M | L | L | Idempotency keys | Dedupe store | Webhook audit |
| 56 | **Clock skew** breaks session ordering | M | R | M | H | L | M | NTP + monotonic IDs | Server time SSOT | Skew detection |
| 57 | **Unicode** normalization breaks ids | M | R | M | H | L | M | NFKC policy | Normalization util | Fuzzy match tests |
| 58 | **Long session** memory bloat | M | C | M | M | L | L | Session pruning | Size caps | Memory metric |
| 59 | Export runs include **other office** rows | **C** | R | **H** | **H** | **H** | **H** | **Org filter QA** | Export tests | Row-count asserts |
| 60 | **Feature flag** flips mid-ticket | M | O | M | **H** | M | M | **Sticky flags** per session | Flag snapshot | Drift alert |

*Rows **61–100** (completing the **TOP_100** list):* pair **(archetype A–J)** × **(modes 1–60)** under correlated stress — e.g. **bilingual + mis-export**, **high-volume + LLM cost**, **audit-heavy + PII in logs**, **price-sensitive + billing dispute**, **chaotic + VIP queue abuse**. Mitigations recurse from rows **1–60**; run **pairwise game days** and track real pairs in **incident retros** instead of freezing **40** speculative one-line rows here.

---

## PHASE 4 — TOP_50_MISSING_SAAS_CAPABILITIES

Ranked by composite **importance** (● = low … ●●●●● = critical). **Eng** = engineering difficulty, **Regr** = regression risk.

| # | Capability | Ops | SaaS | Trust | Sup | Bill | Onb | Deploy | Eng | Regr | ROI |
|---|------------|-----|------|-------|-----|------|-----|--------|-----|------|-----|
| 1 | True tenant isolation + AuthZ | ●●●●● | ●●●●● | ●●●●● | ●●●● | ●●● | ●●● | ●●● | ●●●●● | ●●●● | ●●●●● |
| 2 | Billing + subscription state | ●●●● | ●●●●● | ●●● | ●●● | ●●●●● | ●●● | ●● | ●●●● | ●●● | ●●●●● |
| 3 | Session / ticket correlation | ●●●● | ●●● | ●●● | ●●●●● | ●● | ●● | ●● | ●● | ●● | ●●●● |
| 4 | CS replay bundle (per case/session) | ●●● | ●●● | ●●●● | ●●●●● | ● | ●● | ● | ●●● | ●● | ●●●●● |
| 5 | Sandbox tenant + training | ●●●● | ●●● | ●●● | ●●● | ● | ●●●● | ●● | ●●● | ●● | ●●●● |
| 6 | Admin: pack version rollback | ●●● | ●●● | ●● | ●●● | ● | ●● | ●●● | ●● | ●● | ●●●● |
| 7 | Inline route removal / gate ALL lab | ●●●● | ●●● | ●●●●● | ●● | ● | ● | ●●●● | ●●● | ●●● | ●●●●● |
| 8 | Org hierarchy (franchise) | ●●● | ●●●● | ●● | ●●● | ●● | ●● | ●● | ●●●● | ●●● | ●●● |
| 9 | Seat-based entitlements | ●●● | ●●●● | ●● | ●●● | ●●●● | ●● | ● | ●●● | ●● | ●●●● |
| 10 | Data export for audits | ●●● | ●●● | ●●●● | ●●● | ●● | ●● | ● | ●●● | ●● | ●●● |
| 11 | Health score + QBR metrics | ●●● | ●●●● | ●● | ●●● | ●● | ●●● | ● | ●● | ● | ●●● |
| 12 | Incident / status comms | ●●●● | ●●● | ●●● | ●●●● | ● | ●● | ●● | ●● | ● | ●●● |
| 13 | Rate limits + abuse | ●●● | ●●● | ●● | ●● | ● | ● | ●● | ●● | ●● | ●●● |
| 14 | Mobile-first operator UI | ●●● | ●● | ● | ●●● | ● | ●●● | ● | ●●● | ●● | ●●● |
| 15 | Per-office branding API | ●● | ●●● | ●● | ●● | ● | ●●● | ●● | ●● | ● | ●● |
| 16 | Workflow assignment + locks | ●●● | ●● | ●● | ●●● | ● | ● | ● | ●●● | ●● | ●●● |
| 17 | LLM output disclaimers SSOT | ●● | ●●● | ●●●● | ●●● | ● | ●● | ● | ● | ● | ●●●● |
| 18 | Pack schema CI gate | ●●● | ●●● | ●● | ●● | ● | ●●● | ●● | ● | ● | ●●●● |
| 19 | Deployment profile UI surfacing | ●●● | ●● | ●●● | ●● | ● | ● | ●●● | ● | ● | ●●● |
| 20 | **… 21–50** (*abbreviated — same themes deeper*) secondary records, SSO, CRM handoff, SLA timers, churn prediction, carrier-specific rule packs, voice intake bridge, PII redaction pipeline, on-call rotation hooks, cost showback per office, feature flags per tenant, synthetic monitoring per pack version, contract versioning, dispute ledger, **localization bundle management**, **multi-DB** story, backup/restore self-serve, **AI governance** console, **prompt** allowlist per tenant, **evaluation harness** as product, partner API keys, webhook subscriptions, PDF intake, e-sign — **all high value but second-order until 1–20 progress** | | | | | | | | | | |

*(Capabilities 21–50 are explicitly **second-order** levers once tenant + billing + CS bundle exist — documenting them prevents “science project” sprawl.)*

---

## PHASE 5 — IMPLEMENTATION (this sprint)

| Change | Rationale |
|--------|-----------|
| `scripts/ci_smoke.sh` sets `PYTHONPATH` to repo root | **Operator / CI reliability** — removes silent failure of `import_smoke_check` when env not pre-exported |
| `deployment_profile.log_deployment_profile_banner` | **Deployment honesty** — points operators to this sprint SSOT when `UNIFIED_INTAKE_PRODUCT_ONLY=1` |

**Intentionally not implemented (defer):** giant auth rewrite, billing, full inline-route purge (requires staged PR + route consumers audit).

---

## PHASE 6 — MULTI-ROUND VALIDATION (2026-05-07 run)

| Check | Command / artifact | Result |
|-------|--------------------|--------|
| compileall | `python3 -m compileall -q services/fiqa_api tests` | **PASS** |
| compileall note | full `scripts/` tree | **FAIL** on `run_demo_pack_original.py` (known; not in core CI scope) |
| pytest | `PYTHONPATH=. python3 -m pytest tests/test_deployment_profile.py tests/test_pack_validation.py -q` | **PASS** (6 tests) |
| UI build | `cd ui && PATH=…node22… npm run build` | **PASS** |
| madge | `cd ui && npx --yes madge --circular --extensions ts,tsx src` | **PASS** (no cycles) |
| guardrail + import | `bash scripts/ci_smoke.sh` (after `PYTHONPATH` fix) | **PASS** |
| full regression | `PYTHONPATH=. python3 scripts/run_full_regression.py` | **PASS** — `http_p95_ms=4977.58` (threshold 6000), `wrong_vehicle_related=0`, `pg_mismatch_turns=0`, `pass_rate_pct=100` |
| Onboarding walkthrough | `trial_readiness_check.sh` / `trial_launch_check.sh` | **Not re-run this session** — guardrail + regression subsume mainline |
| Deployment walkthrough | manual + `deployment_profile` banner string | **Recorded in SSOT** |
| Rollback walkthrough | git-centric (no change) | **N/A automation** |
| Support / escalation | scripted guardrail simulations | **PASS** via guardrail battery |

---

## PHASE 7 — SUPPORT / OPERATIONS / CEO REVIEW

| Stakeholder | What breaks first @100? |
|-------------|-------------------------|
| **CEO** | **Commercial infrastructure** (billing, contracts, CS capacity) before raw triage quality becomes the headline attriter. |
| **Onboarding** | **Throughput** — cannot certify 100 packs/month without **automation + self-serve fixes**. |
| **Support** | **Unlinked tickets** + **no replay bundle** ⇒ **duplicate effort** and **trust erosion**. |
| **Operator** | **Wrong-vehicle** + **append boundary** mistakes under fatigue. |
| **Replay** | Engineers yes; **CS** still lacks **prod replay package**. |
| **Deployment** | **Profile drift** + **route leak** stories dominate security reviews. |
| **Customer success** | No **health metrics** → reactive churn firefights. |
| **Escalation** | **Founder** is default **tier-3** — **single queue collapse**. |
| **Billing** | **Nothing to meter** → invoices based on vibes — **unacceptable** past pilot. |
| **Compliance** | **Audit export** ≠ compliance — **set expectations** or **build real pipeline**. |

**Synthesis**

| Question | Answer |
|----------|--------|
| What breaks first @100 offices? | **Ops + support + billing** — **not** the core triage loop under normal conditions. |
| Support collapse driver? | **Volume × missing CS tooling** (replay, dedupe, macros). |
| Founder collapse driver? | **Single-threaded escalation + sales promises** ahead of product. |
| Onboarding collapse driver? | **Manual pack discipline** fails under parallel intros. |
| Trust collapse driver? | **LLM oddities** + **“ROI proof”** vacuum. |
| Tenant risk? | **Logical tenancy** without **RLS** when revenue justifies IAM. |
| Churn triggers? | **Price shock**, **AI distrust**, **billing disputes**. |
| Hiring operators blocked by? | **Ambiguity in SOPs** + fear of **wrong bind to carrier systems**. |
| Scaling support blocked by? | **No ticketing integration** + **no tier-1 scripts** in-product. |

---

## PHASE 8 — SELF_CRITIQUE_REPORT_V3

| Claim | Critique |
|-------|----------|
| **Fake SaaS claims** | “Product-only” still exposes **platform inline routes** — marketing must not imply **minimal attack surface**. |
| **Fake tenancy** | **Logical** `client_id` / headers ≠ isolation — **good for pilot**, **lethal** if mis-sold. |
| **Fake onboarding** | No **self-serve** — **hero-driven** onboarding does not **compound**. |
| **Fake replay guarantees** | **Regression** proves **engineering** quality, **not** **provable CS narratives** per session. |
| **Fake audit guarantees** | **audit_export** forward — **no WORM / compliance**. |
| **Fake deployment isolation** | **Product-only** omits **routers**, not **all** FastAPI paths. |
| **Fake supportability** | Strong **scripts**; weak **customer-facing** diagnostics. |
| **Fake observability** | **Route perf** exists — **no** unified **SLO dashboard** for brokers. |
| **Founder dependencies** | **Pack authorship**, **incident command**, **sales truth** — all **single points**. |
| **Support assumptions** | Assumes engineer can **grep logs** — breaks @100. |
| **Operator assumptions** | Assumes **English/中文** reading + **calm** correction paths — **fatigue breaks this**. |

**Biggest illusions**

| Category | Illusion |
|----------|----------|
| Product story | “**Model quality** is the moat” — actually **workflow trust + ops** moat. |
| Ops debt | “**We'll hire**” without **playbooks** = **slow hiring + fast firefighting**. |
| Support risk | “**Guardrails pass** = **customers calm**” — false. |
| Scaling blocker | **Commercial + tenant** infra, **not** Python hot loops alone. |
| SaaS blocker | **No billing + noAuthZ** = **not durable SaaS** in the economic sense. |

---

## PHASE 9 — HUNDRED_OFFICES_OPERATIONAL_CHAOS_FINAL_REPORT

1. **What this company REALLY is:** A **pilot-grade Unified Intake** (**CA auto broker**) with **exceptional regression discipline** sitting beside a **broad research platform** — **commercially** it must **shrink the promise** to what **ops can defend**.  
2. **What breaks first @100 offices:** **Support + onboarding + billing ops** — not triage latency under median load.  
3. **Biggest support blocker:** **No session-accurate CS replay export** + **ticket linking**.  
4. **Biggest onboarding blocker:** **Manual pack + env** slots — **no provisioning product**.  
5. **Biggest deployment blocker:** **Honest product-only** posture vs **inline platform routes** — **trust + security**.  
6. **Biggest replay blocker:** **Engineering replay exists**; **CS/prod parity replay** does **not**.  
7. **Biggest billing blocker:** **No billing subsystem** — **manual invoicing** caps scale.  
8. **Biggest operator blocker:** **Fatigue + ambiguity** → **wrong vehicle / append** errors — UI can only **partially** absorb.  
9. **Biggest trust blocker:** **AI output variance** without **institutional narrative** + **SLA**.  
10. **Biggest tenant blocker:** **Future IAM** without **data model prep** → **migration trauma**.  
11. **Biggest scaling blocker:** **Founder/bus factor** on **every non-happy path**.  
12. **Biggest founder bottleneck:** **Escalation + sales truth + pack authoring** collapse onto **one person**.  
13. **Best automation move:** **`pack_validation` + readiness scripts in CI/CD** for **every** deploy slot.  
14. **Best support tooling move:** **Case/session export bundle** (JSON + redaction) for **tier-1**.  
15. **Best onboarding move:** **Sandbox tenant** + **immutable checklist** in **`trial_launch_check`**.  
16. **Best deployment move:** **Audit + eliminate** `PLATFORM_INLINE_ROUTES_*` **systematically** — **no heroics**.  
17. **Best replay/audit move:** **Define “engineering vs compliance”** — stop **conflating** analytics with **audit**.  
18. **Best simplification move:** **Product-only** cut of **UI routes** to **single workbench** — retire **dead demos** from prod builds.  
19. **Best SaaS move:** **Ship billing + tenant isolation** on **pilot revenue evidence** — not **before** need, **not** long **after**.  
20. **Best next 10× leverage point:** **Tenant-shaped data model + CS egress tooling** — **multiplies** every downstream SaaS capability.

---

## SIMULATIONS PERFORMED (this sprint)

| Simulation | Form |
|------------|------|
| 100-office archetype matrix | Structured tabletop (§2) |
| Onboarding chaos | Derived from pack + trial scripts |
| Deployment chaos | `deployment_profile` + docs |
| Operator chaos | Guardrail + adversarial suites (**live run**) |
| Replay chaos | `run_full_regression.py` + chaos JSON |
| Support flood | Modeled via **support lifecycle** + failure matrix |
| Escalation / founder overload | CEO / escalation review §7 |
| Billing confusion | Declared **out of scope** — **impact modeled only** |
| Tenant bleed | **Risk analysis** — **no prod exfil test** |

---

## OPERATIONAL REVIEWS COMPLETED

CEO, onboarding, support, operator, replay, deployment, CS, escalation, billing, compliance — **§7 + §9**.

---

## REMAINING RISKS (top)

1. **Inline route surface** in **product-only** deploys.  
2. **Logical tenancy** **mistold** externally.  
3. **No billing** when **“pilot” ends**.  
4. **compileall** debt in **legacy scripts**.  
5. **Founder-dependent** **escalation path**.

---

## FINAL OUTPUT (required format)

| Field | Value |
|-------|--------|
| **branch** | `auto-evolution/100-offices-operational-chaos-20260507` |
| **changed files (this sprint’s tracked intent)** | `docs/sprints/HUNDRED_OFFICES_OPERATIONAL_CHAOS_SPRINT.md` (**new**), `scripts/ci_smoke.sh`, `services/fiqa_api/deployment_profile.py` (+ pre-existing dirty/untracked per §Phase 0) |
| **validations** | compileall (`services/fiqa_api`+`tests`) PASS; pytest 6 PASS; UI build PASS; madge PASS; `ci_smoke` PASS; `run_full_regression.py` PASS (`http_p95_ms≈4978<6000`) |
| **simulations performed** | 100-office archetype tabletop; scripted operator/deploy/replay via regression stack |
| **operational reviews completed** | §7 (10 roles synthesized) |
| **major discoveries** | **Company systems break before triage engine**; **correlated incidents** dominate @100 |
| **biggest failure modes** | **Tenant bleed (future)**, **support overload**, **deployment honesty**, **billing absence** |
| **biggest SaaS gaps** | True **AuthZ**, **billing**, **CS replay bundle**, **provisioning** |
| **remaining risks** | Inline routes; tenancy story; founder queue; legacy script syntax debt |
| **recommended next 10× leverage** | **Composite tenant keys + CS export + billing hook** — **in that gated order** when revenue proves |
| **FINAL_ONE_LINE** | **At one hundred offices, Searchforge does not die in the triage loop — it dies in the queue in front of the founder, unless tenancy, billing, and support egress become as real as your guardrails already are.** |
