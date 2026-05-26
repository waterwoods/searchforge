# System Productization / CEO-Level Architecture Review Sprint

**SSOT:** This document is the single source of truth for this sprint.  
**Date:** 2026-05-07  
**Repo:** SearchForge (California auto insurance broker assistant + Unified Intake, coexisting with broader platform code)  
**Reviewer stance:** Senior systems architect, productization lead, SaaS strategist, AI ops architect, technical founder advisor.

---

## OBJECTIVE

Determine whether this system can credibly evolve into:

- A **real multi-office / multi-customer SaaS platform**
- A **stable AI operations product** (trustworthy intake, auditable outcomes)
- A **multi-client intake backbone** (industry + client packs, regional/compliance variants)
- A **long-term maintainable** system under real CS and engineering throughput
- A **monetizable** B2B product with clear tiers and expansion paths

This sprint optimizes for **strategic clarity and product boundaries**, not micro-latency.

---

## NON_GOALS

- Rewriting `triage.py` or micro-optimizing HTTP handlers
- Resolving every open technical debt ticket
- Designing final auth/billing schemas (only identifying gaps and sequencing)
- Proving commodity RAG benchmarks against generic assistants

---

## SYSTEM_POSITIONING

### What this system *really* is (not “an AI chatbot”)

**Commercially defensible core (today):**  
**Unified Intake** — a **state-driven, add-car-first intake engine** plus **broker workbench** that turns messy customer messages into a **durable service record** (case) with explicit **handoff / formal-submit** semantics, backed by increasing **structured truth** (Postgres vehicle entity, case read/write facades) rather than “whatever the model said last.”

**Repository reality:** The same codebase **also hosts** a broader **SearchForge / FIQA** surface: code graph, search pipelines, multiple demo agents (mortgage, ecommerce, job hunter), ops plugins, Qdrant/Milvus, etc. **The product story that can ship to paying brokers is Unified Intake**; the rest is **platform option value** and **cognitive load**.

### Operator value

- Fewer rounds of “what did they mean?” for add-vehicle and adjacent lanes
- **Replayable** scenario testing and guardrails — repeatable “did we break Chen vs SoCal?” checks
- **Office-facing** structured fields and lifecycle (waiting_on, milestones) vs raw chat

### Workflow value

- Session → case binding → append vs new-case boundaries
- **Route orchestration** in `routes/inbox_triage.py` (session, stub vs full case reads, PG mirror, analytics hooks)
- **Resolver / vehicle identity** converging on PG when enabled; **finalize** path as API truth mirror

### Business value

- **Pilot-scale broker productivity** and **trust in handoff artifacts** — chargeable unit aligns with **service record clarity + formal submit**, not message tokens alone (per master outline).

### Repeatable moat (durable if maintained)

1. **Domain-shaped triage + regression batteries** (scenario libraries, cross-client isolation drills) — hard for generic chat wrappers to replicate without serious QA culture.
2. **Explicit truth layering** (LLM proposes; facades/DB own vehicle/case authority where configured) — reduces “hallucinated policy” as product risk.
3. **Client pack + industry pack** model (`config_loader.py`, `configs/clients/*`, `configs/industries/*`) — onboarding story is **folder + env**, not fork-per-broker **if** tails stay in config not code.

### Commodity layers

- Raw OpenAI calls, generic embeddings, “assistant with RAG” positioning without the above **truth + regression** story.
- **Hosting** on Cloud Run/Vercel/Qdrant — table stakes.

### Accidental complexity

- **Monolithic API entry** (`app_main.py`) mounting many unrelated product routes — increases attack surface, deploy coupling, and onboarding confusion (“what is this product?”).
- **`triage.py` on the order of ~6k+ lines** — high coupling; undermines the “configs first” narrative unless aggressively managed.
- **Parallel / duplicate plugin-style trees** (e.g. control plugin patterns in more than one path) — noise for operators and new hires.

---

## PRODUCT_IDENTITY

| Lens | Statement |
|------|-----------|
| **Elevator (correct)** | “Intake that becomes a **real case** in the office, with **rules + replay**, not a chatbot.” |
| **Wrong elevator** | “Our AI answers insurance questions” (commodity; also not the bounded pilot contract). |
| **SKU (now)** | Single-industry (CA auto insurance), single or few clients per deploy, add-car flagship lane. |
| **SKU (future platform)** | Packaged **intake + workbench spine** + optional RAG lane; **tenant/org** boundary TBD. |

---

## SYSTEM_MAP

```
[ Browser: Unified Intake / Workbench UI ]
        |  HTTP: /api/inbox/* (+ client config, analytics logger)
        v
[ routes/inbox_triage.py ]
   ├─ session_store / session_repository (turns, binding)
   ├─ case_truth_repository (stub vs full; JSON vs Postgres)
   ├─ entity_repository + active_vehicle_request_cache_scope
   ├─ triage_conversation (triage.py) — core engine
   ├─ handoff / reply composers (client finalize)
   ├─ assist_layer (additive)
   └─ analytics (structured logging events)
        |
        v
[ TriageResult + case lifecycle ] → customer copy + broker workbench

[ Parallel in same app: search, code graph, other agents — same FastAPI app ]
```

**Persistence:** Case facade (`case_truth_repository`, `case_store`) with env-driven DB-primary and dual-write; sessions on disk/DB per implementation; vehicle entity in Postgres when enabled.

**Knowledge:** Qdrant + retrieval proxy in docker-compose; RAG is **adjacent** to add-car pilot core (inbox triage is not “RAG-first” by design).

---

## PRODUCTIZATION_REVIEW

### Strengths

- **Three-tier config** (common / industry / client) with **no cross-client fallback** for sensitive structures — correct instinct for multi-broker expansion.
- **Guardrail scripts** bundling scenarios and **A/B client isolation** — rare and commercially narratable.
- **Hot-plug story is real** for **new client directory + `CLIENT_ID`** (not arbitrary Python hot-swap).
- **Master outline** (`UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md`) is an unusually strong **product compass**; aligns engineering with “not a CRM.”

### Gaps / “fake boundaries”

- **“Hot-swap industry”** is **partially** true: industry JSON exists, but **large behavioral surface** still lives in **code** (`triage.py`), not packs — migrations will feel like **engineering projects**, not CS config edits.
- **`LLMAdapter`** boundary documented in plugin map but **not fully institutionalized** — multi-provider and test doubles remain **risk** under provider pricing or outage pressure.
- **`active_vehicle_resolver` vs triage** — documented **convergence gap** (`DEPRECATED_PATHS.md`, `SYSTEM_ONE_PAGE_MAP.md`): **duplicate authority** risk until one path wins.
- **Frontend default copy** can **mask thin client packs** — product still “looks like” reference broker until `ui_copy` is complete.

### Questions — answered candidly

| Question | Verdict |
|----------|---------|
| Many broker **offices**? | **Yes via many deploys or future tenancy**; not one auth-isolated multi-tenant app today. |
| Many **industries**? | **Architecturally plausible**; **economically** requires extracting policy from `triage.py` into `IndustryPack` contracts. |
| Regional / compliance packs? | **Configs + templates** yes; **audit + data residency** not yet first-class. |
| **Tenant isolation**? | **Not in product scope today** (explicit in AGENTS.md); isolation = **per instance / env paths** at pilot stage. |
| White-label? | **Partially** — UI copy from API; **no** full tenant theming / domain isolation productized. |
| Multiple AI providers? | **Feasible** with adapter; **not done** as clean plug-in yet. |
| Future RAG plugins? | **Yes behind interface**; must **never overwrite** entity truth without rules — docs already warn. |

---

## CEO_LEVEL_OBSERVATIONS

### What is the actual business?

**B2B workflow SaaS for broker teams** (starting Chinese-speaking CA auto cohort) that sells **reliability of intake → case handoff**, backed by **operational QA** (replay/guardrails), **not** unlimited generative Q&A.

### Who pays and why?

- **Broker principal / office** pays for **time saved**, **fewer dropped leads**, and **trusted artifacts** for producers.
- Sticky when **workbench + case history + tone** match their office; **lock-in** = deployed **packs + integrations + training**, not raw model choice.

### What blocks scaling revenue?

- **Single-tenant mental model** per deploy → ops linearly expensive unless **tenant layer** or **managed multi-instance** playbook matures.
- **Trust incidents** (wrong vehicle, wrong boundary) destroy **niche** community trust faster than in generic SaaS.

### What blocks enterprise trust?

- No **enterprise IAM**, **audit export**, **SLA-grade** backup story, **data residency** options — **expected at this stage**, but **on the roadmap-critical path** for **multi-agency** deals.

---

## MAINTAINABILITY_REVIEW

### God modules and coupling

| Area | Risk | Direction |
|------|------|-----------|
| `triage.py` (~6k+ LOC) | **Extreme** — onboarding time, bug regression fear | Extract **policies**: add-car, append, handoff, intent heads; keep **orchestrator** thin |
| `app_main.py` | **Monolith entry** — many routers | **Split deploy units** or **feature-flagged** modules; minimal: **document “product surface” vs lab** |
| `routes/inbox_triage.py` | Large but **orchestration-appropriate** | Continue **facades**; avoid new business rules here |

### Hidden coupling

- **Analytics definitions** tied to funnel semantics — changing triage flags can **silently skew** “success.”
- **Stub vs full case reads** — **correct perf pattern**; must stay **documented** to prevent “quick fix” merges that spike latency or break truth.

### Duplicated authority

- Resolver module vs in-triage extraction — **strategic debt** called out in repo docs; **pick one**.

---

## SCALABILITY_REVIEW

### Technical scale (throughput)

- **Cloud Run + stateless API** — fine for **pilot** traffic.
- **Postgres case + entity** path — **appropriate**; needs **indexing, pooling, migration discipline** as volume grows.
- **JSON file case store** — **explicitly non-scalable** for multi-tenant cloud; **acceptable** for local/single pilot; **blocker** for **true SaaS density**.

### Organizational scale (team + CS)

- **Config-only onboarding** competes with **“triage.py needs a patch”** reality — org scale requires **stricter boundaries** and **Tools for non-engineers** (limited DSL, not full visual programming).

---

## SAAS_READINESS_REVIEW

### Current posture

**Not SaaS-multi-tenant today** — deliberate: `AGENTS.md` lists **multi-tenant out of scope**; **CLIENT_ID** selects pack per **deployment**.

### Paths to “real SaaS”

1. **Instance-per-tenant (v1 SaaS economics weak but clear)**  
   One Cloud Run service + DB schema per broker; **strong isolation**, higher ops cost.
2. **Row-level multi-tenancy (true SaaS)**  
   Add **`org_id` / `tenant_id`** everywhere: cases, sessions, entities, analytics, configs; **auth**, **billing**, **quotas** — **major program**, not a sprint.

### Feature-flag boundaries

Env flags for DB-primary, JSON fallback, LLM on/off — **good**; need **central matrix** (who can toggle what in prod) for **operator trust**.

---

## TENANCY_REVIEW

| Dimension | Today | Risk |
|-----------|-------|------|
| Data isolation | **Deploy/env path**; DB emerging | Cross-env misconfig **leaks** pilot data |
| Office isolation | **Logical** within one broker | **N/A** multi-office |
| Analytics partitioning | Logger JSON lines | **No per-tenant billing-grade** events |
| Replay / simulation | Same engine as prod | Must **never** pollute prod stores — ensure **flags/paths** |
| Plugin isolation | **Low** — same process | **Noisy neighbor** in monolith |
| API isolation | **Single API** surface | **Rate limits / API keys** not productized |

**Before scaling customers:** **tenant_id in persistence + auth**, or **hard per-customer instances** with automation.

---

## PLUGIN_ARCHITECTURE_REVIEW

### What is real

- **Client / industry JSON packs** + loader merge order — **real**, tested.
- **Entity and case facades** — **real** plugin boundaries for persistence swaps.

### What is incomplete

- **LLM provider plug-in**
- **RAG retriever plug-in** (interface sketched in docs)
- **Vehicle resolver** — **code exists but not the single authority in triage** (per docs)

### Hot-swap viability

- **Configs:** high for **copy/templates**; medium for **behavior** until `triage.py` shrink + policy classes.
- **Python plugins:** **not** arbitrary hot-swap; expect **reviewed releases**.

---

## DEPLOYMENT_TOPOLOGY_REVIEW

**Documented:** Vercel (UI) + GCP Cloud Run (API) + Qdrant; docker-compose for local/full stack (Qdrant, optional Milvus/Redis, rag-api).

### Assessment

- **Pros:** Fast **demo-to-URL**; scales to **pilot**; clear runbooks.
- **Cons:** **Monolith** deploy ties **Unified Intake** to **experimental routers** — security, startup time, cognitive load.
- **Recommendation:** **Binary “product mode”** build or **split services** before **external SOC2-style** demands.

---

## UX_REVIEW

- **Unified demo + workbench** — strong **founder demo** narrative.
- **Tab D (scenario replay)** — correctly **non-production funnel** (per system map); must stay **obviously QA** to avoid prospect confusion.
- **Risk:** **Density of controls** for broker staff — future **role-based** simplification (producer vs admin).

---

## OPERATOR_REVIEW

- **Strengths:** Scripts for demo readiness, guardrails, trial checklists — **operator maturity** above average for early-stage.
- **Gaps:** **No unified admin console** for “which client pack / flags / LLM mode is live?” beyond env — **runbook reliance**.

---

## AI_TRUST_BOUNDARIES

### Design intent (aligned with moat)

- **LLM** suggests structured triage JSON and assist copy; **does not** own **vehicle truth** or direct entity writes when PG path is authoritative.
- **Formal submit / handoff** is a **product gate**, not a model stop sequence.

### What would make an office trust this?

- **Stable vehicle line** matching **PG mirror**; **append/new-case** boundaries **predictable**; **replay** shows **same outcome** tomorrow.

### What would break trust?

- Customer-visible copy **ahead of** structured truth; **silent vehicle switches**; **non-reproducible** LLM flips without logged inputs.

### Legal / compliance angle

- **Insurance advice** boundaries — product must stay **intake + routing**, not **binding coverage advice**; **citations** and **human review** for regulated content.
- **Immutability:** **Formal submit snapshot**, **case activity**, **OCR artifacts** — define what is **append-only** vs editable; **audit export** for disputes.

### What must never be “only AI”?

- **Coverage decisions**, **price quotes**, **final carrier binding** — **human/compliance** domain.
- **Vehicle key / primary summary** when PG enabled — **database wins**, not model prose.

---

## AUDITABILITY_REVIEW

- **Case activity** and structured logging exist — **foundation**.
- **Gaps:** **Tamper-evident logs**, **tenant-scoped audit API**, **export to SIEM** — **enterprise checklist items**.

---

## ANALYTICS_REVIEW

- **Implementation:** `minimal_events.track_event` — JSON lines via logging; **no third-party pipeline** — good for **PII caution**, weak for **self-serve product analytics**.
- **Funnel events** depend on **definitions** (`PRODUCT_TRUTH_DOCUMENT` referenced in system map) — **must version** with product.

**Risk:** **early_dropoff** noise on mid-session turns called out in system map — **fix or gate** before CEO metrics reviews.

---

## REPLAYABILITY_REVIEW

- **Scenario runners + Role C simulation** — **strong differentiator** for **QA and sales proof**.
- **Requirement:** Replay must **pin** pack version + flags + model version as much as possible — **“same inputs → same structured result”** for rule mode; **bounded variance** disclosed for LLM mode.

---

## COST_STRUCTURE_REVIEW

| Cost | Driver |
|------|--------|
| **LLM** | Per-turn triage + assist; **mitigate** with rule mode, caching, shorter contexts |
| **Vector** | Qdrant Cloud/hosting; **low** if intake stays non-RAG-first |
| **Compute** | Cloud Run; **ok** at pilot |
| **People** | **Engineering on `triage.py`** — dominant **hidden** cost |

---

## MONETIZATION_ANALYSIS

### Near-term (matches current goal docs)

- **Paid pilot** per broker: **manual invoicing**, **per-seat or flat office fee**, scoped to **add-car intake + workbench**.

### Mid-term

- **Packaged onboarding fee** (config + scenarios + training) + **monthly platform**
- **Usage-based** (cases formalized, messages after free tier) — only after **metering** is trustworthy

### Pricing traps

- **Per-token billing** without **truth guarantees** — anchors product as **commodity AI**.

---

## PRODUCT_TIERING (strawman)

| Tier | Includes |
|------|-----------|
| **Pilot** | Single office, managed instance, guardrails, manual support |
| **Growth** | Multi-instance playbook or **soft multi-tenant**, client pack tooling, SSO roadmap |
| **Enterprise** | Audit exports, residency, SLA, carrier integrations — **only after** core tenancy solid |

---

## ROADMAP_ANALYSIS

### Traps

- **Chasing generic RAG quality** instead of **case truth + boundaries**
- **Building full CRM** — explicitly **out of vision**; **scope creep kills** focus
- **Premature multi-tenant** without **per-org revenue** to pay for the complexity

### Winning sequence

1. **Lock add-car** as **reference vertical** with **measurable office outcomes**
2. **Shrink triage** into **policies + configs**
3. **Tenancy or managed multi-instance automation**
4. **Selective** second vertical after **pack contract** is proven

---

## TOP_PRODUCTIZATION_RISKS

1. **`triage.py` gravity** — every new intent **pins** you harder — **undermines pack story**
2. **Monolith API** — security / story / scaling **drag**
3. **No tenant_id** — **blocks** true SaaS economics
4. **LLM + trust incidents** without **replay pins** — **reputational**
5. **Analytics truth** — **wrong dashboard** → **wrong decisions**
6. **Operator dependence on founders** — **runbooks** don’t scale to **10 brokers**
7. **Partial client packs** — **accidental** cross-broker tone leakage
8. **Cost surprises** at LLM-heavy **append threads**

---

## TOP_10X_OPPORTUNITIES

1. **“Replay-as-contract”** — sell **regression-as-a-service** with every deploy (confidence)
2. **Case spine integrations** (AMS, raters) — **workflow moat** once intake trusted
3. **Instance provisioning automation** — **fake SaaS** that **prints MRR** faster than big rewrite
4. **Pack SDK + validator** — **non-engineers** can **safely** ship copy/rules
5. **Explainable handoff packet** — PDF/structured export brokers **show carriers**
6. **Role-based workbench** — **adoption** unlock
7. **LLM adapter + golden fixtures** — **provider arbitrage + test speed**
8. **Tenant analytics + billing hooks** — **required** for **true platform**
9. **Narrow “only intake” pricing** — **clarity** beats **platform pretense**
10. **Second vertical** **only** via **proven pack interfaces** — **optional huge TAM**, not mandatory now

---

## ARCHITECTURAL_SIMPLIFICATIONS

1. **Split or flag** non–Unified-Intake routers from **production broker deploy**
2. **Modularize `triage.py`** by **intent lanes** and **shared utilities**; **stop** adding tails inline
3. **Wire or delete** `active_vehicle_resolver` — **one authority**
4. **Consolidate** duplicate control/plugin scaffolding
5. **Thin `app_main.py`** — composition root only, **no** feature logic
6. **Front-load** `IndustryRegistry` / `ClientPack` **typed objects** — reduce **dict soup**

---

## PRODUCTIZATION_ACTION_PLAN

### TOP_10_PRODUCTIZATION_ACTIONS (ranked by leverage × feasibility)

| Rank | Action | ROI | Risk | Complexity | Horizon |
|------|--------|-----|------|------------|---------|
| 1 | **Triage policy extraction** (first: add-car + append) | Eng+Product | Med | High | 90d |
| 2 | **Single vehicle authority** (resolver + finalize) | Trust | Med | Med | 30d |
| 3 | **Product-only deploy profile** (exclude lab routes) | Biz+Ops | Low | Med | 30d |
| 4 | **LLM adapter + golden JSON tests** | Eng+Trust | Low | Med | 60d |
| 5 | **Tenant_id + auth spike** (or instance factory) | Biz | High | High | 90d–1yr |
| 6 | **Analytics schema versioning + noise fixes** | Product | Low | Low | 30d |
| 7 | **Pack validator CI** (client/industry completeness) | Ops | Low | Low | 30d |
| 8 | **Admin “mode panel”** (read-only in prod) | Ops | Med | Med | 90d |
| 9 | **Audit export MVP** | Enterprise | Med | Med | 90d |
| | **RAG behind retriever interface** | Future | Med | Med | Discretionary |

**Next 30 days:** Items **2, 3, 6, 7**  
**Next 90 days:** Items **1, 4**, start **5** or **instance factory**  
**Next year:** **5** to completion, **integrations**, **enterprise audit**

---

## FINAL_RECOMMENDATION

**Invest behind Unified Intake as the product** — **monetize** the **case spine + trust boundary + replay culture**. **Treat the broader SearchForge surface** as **R&D or separate deploy**, not **one customer-facing SKU**.

**Do not** declare multi-tenant SaaS readiness until **persistence + analytics + auth** share a **tenant key** or you **operationalize** **one-instance-per-customer** at low marginal cost.

---

## FINAL_DECISION

**Proceed** with **productization** toward **managed multi-broker intake platform**, with **explicit choice** incoming: **(A)** automated **per-tenant instances** vs **(B)** **shared infra + row-level tenancy**. **Default** to **A** until **$MRR and compliance** justify **B**.

**Hold** “generic AI research platform” positioning for **the same brand** unless **separately funded** — it **dilutes** broker trust and **inflates** scope.

---

## SYSTEM_PRODUCTIZATION_CEO_FINAL_REPORT

1. **What this system REALLY is** — **Unified Intake**: state-driven **broker intake → durable service record** with **handoff truth disciplines**; repo also contains **broader RAG/code-intel platform** that should not define the **commercial SKU**.

2. **What its moat is** — **Domain triage + regression/isolation culture + explicit non-model truth for vehicle/case** when configured — **not** generic chat quality.

3. **What is over-engineered** — **Monolithic `app_main` constellation** of many agents/features **for the broker product promise**; duplicate plugin scaffolding; **optimization depth** in areas **secondary to tenancy/story**.

4. **What is under-built** — **Tenant/auth/billing**, **audit exports**, **unified provider adapter**, **operator admin**, **automated instance provisioning**.

5. **Biggest business opportunity** — **Vertical intake spine + integrations** for **small broker offices** with **high thread volume** and **bilingual operations** — **pain is acute** and **under-served by CRMs**.

6. **Biggest technical risk** — **`triage.py` collapse under feature load** → **slow releases**, **trust bugs**, **pack story becomes false advertising**.

7. **Biggest scaling blocker** — **No real tenancy or cheap instance factory** → **linear ops cost per broker**.

8. **Biggest trust blocker** — **Any drift** between **customer copy** and **structured truth**; **unpinned LLM behavior** in production without disclosure.

9. **Best product niche** — **CA auto broker offices** (esp. **Chinese-speaking customer base**) **add-car intake + append** with **human handoff**.

10. **Best monetization path** — **Pilot flat fee → monthly per office + onboarding package**; later **meter on formalized cases** once **analytics honest**.

11. **Best SaaS path** — **Short term:** scripted **per-customer Cloud Run + DB**; **Long term:** **tenant row scope** + **SSO** when **deal size** supports.

12. **Best simplification opportunities** — **Product-only deploy artifact**; **split triage**; **delete duplicate resolver path**; **declutter** unrelated routers.

13. **Most important next architecture move** — **Enforce single authority** for **vehicle resolution + API finalize**, then **extract triage policies** behind **industry/client contracts**.

14. **Most important next product move** — **Publish a buyer-facing “trust spec”**: what is AI vs rule vs DB; what is **immutable** after submit.

15. **Most important next business move** — **Close second paid pilot** with **documented time saved** and **replay proof**, not **feature breadth**.

16. **Final productization judgment** — **Strong wedge, credible skeleton for a vertical SaaS spine**, **not yet** a **multi-tenant SaaS platform** — **intentionally**. **Strategic success** depends on **refusing** **platform sprawl** **while** **forcing** **`triage.py` to shrink** and **tenancy to appear** in **data paths** before **sales outrun ops**.

---

*End of SSOT document.*
