# Pilot → Real SaaS Transition Sprint

**Single source of truth:** This file.  
**Date:** 2026-05-07  
**Repo:** SearchForge (California auto insurance broker assistant + Unified Intake; coexists with broader FIQA/SearchForge platform code)  
**Reviewer stance:** SaaS platform architect, AI operations architect, productization lead, technical founder, onboarding strategist, deployment strategist, operator workflow designer, audit/replay reviewer, trust/safety reviewer, multi-tenant planner.

**Companion (prior art, still valid):** `docs/sprints/SYSTEM_PRODUCTIZATION_CEO_REVIEW_SPRINT.md` — deep productization pass. This sprint **re-anchors** on the **commercial transition** from paid pilot to **repeatable SaaS operations**.

---

## OBJECTIVE

1. **Define** what must change for the system to evolve from **“strong pilot / advanced demo”** to **“real SaaS operational product”** that companies pay for monthly.
2. **List** architecture changes **required before scaling** (not nice-to-haves).
3. **Draw** explicit **product boundaries** (what is SKU vs lab vs R&D).
4. **Identify** missing **operational workflows** (CS, onboarding, office admin, support).
5. **Specify** mandatory **trust / audit / replay** systems for commercial and enterprise credibility.
6. **Design** the **onboarding / deployment / tenant / billing** structure at a decision-ready level.
7. **Classify** what should become **plugin**, **config**, **tenant layer**, **deploy unit**, **managed service**, **admin tool**, **replay artifact**, or **immutable truth**.

---

## NON_GOALS

- Micro-optimizing latency, HTTP handlers, or `triage.py` internals.
- Rewriting modules for cleanliness without a product boundary story.
- Final schema design for auth/billing (this sprint **names gaps and sequencing**).
- Committing to a specific cloud SKU or legal/compliance certification path (SOC 2, HIPAA, etc.) — only **posture** and **blockers**.

---

## CURRENT_SYSTEM_POSITION

**Repository truth:** One **FastAPI monolith** (`services/fiqa_api/app_main.py`) mounts **Unified Intake** (`routes/inbox_triage.py`) alongside **many other routers** (search, code graph, mortgage/ecommerce/jobhunter agents, ops lab, experiments). The **commercially shippable wedge** documented in `AGENTS.md` and `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` is **Unified Intake**: **Add-Car-first**, **state-driven intake** → **durable service record** → **formal submit / handoff**.

**Technical spine (intake):** `triage.py` (large orchestration engine) + facades (`case_truth_repository`, `case_store`, `entity_repository`, `session_store`/`session_repository`) + client/industry JSON packs (`config_loader.py`, `configs/clients/*`, `configs/industries/*`). Optional **Postgres** for cases, entities, sessions; env flags for DB-primary vs JSON/dual-write. **Qdrant** for retrieval-adjacent flows; intake is **not RAG-first** by product intent.

**Positioning gap:** Pilot docs still say **multi-tenant and Stripe are out of scope** (`docs/goals/insurance_paid_pilot_goal.md`, `AGENTS.md`). **Real SaaS** **requires** revising that boundary — either **managed instance-per-customer** (still “single tenant per deploy”) **or** **shared app + row-level tenancy + billing**.

---

## PILOT_STATUS

| Dimension | Status (2026-05-07) |
|-----------|---------------------|
| **Product narrative** | Strong: master outline, trial package, scenario/replay culture, workbench UX. |
| **Paid pilot mechanics** | Goal doc: manual payment, single broker, no auth — **appropriate for v0, incompatible with “SaaS company”.** |
| **Deploy** | **Vercel (UI) + Cloud Run (API) + Qdrant** documented; `deploy_rag_demo.sh` is the practical path; legacy `deploy_cloud_run.sh` still references `mortgage-agent-api` — **operator confusion risk**. |
| **Persistence** | **Postgres path exists** for cases/entities/sessions; `docs/DEPLOYMENT_READINESS.md` still notes **in-memory/SQLite not shared across instances** for some paths — **must be reconciled with production** before horizontal scale. |
| **Isolation** | **CLIENT_ID** per deployment / request; **no org-level auth**, **no tenant row key** in analytics/events as first-class product concept. |
| **Trust artifacts** | Formal submit / handoff boundaries **in product**; **replay** via UI simulation + script batteries; **audit export / tamper-evident log** **not** productized. |

**Verdict:** **Advanced pilot / demo-plus** with **credible intake spine**; **not** yet a **multi-customer SaaS business in a box**.

---

## WHAT_IS_THE_REAL_PRODUCT

**Commercial product (correct elevator):**  
**“Intake that becomes a real case in the office — with explicit handoff, structured truth, and regression you can run before every deploy — not a generic AI that answers insurance questions.”**

### Real operator value

- **Fewer clarification rounds** on Add-Car and append threads; **structured fields** and **lifecycle** (`waiting_on`, milestones) visible in workbench.
- **Replayable scenarios** — proof that **Chen pack ≠ SoCal pack** and that **releases didn’t break** the handoff contract.

### Real office value

- **Service record** the team can **continue** after customer stops typing; **formal submit** as the **promotion boundary** between “draft intake” and “what we rely on.”

### Real workflow value

- **Session → case binding**, **append vs new-case** rules, **resolver / vehicle identity** converging on **Postgres when enabled** — **office process**, not chat.

### Real business value

- **Billable unit** should align with **clarity + durability of the service record + handoff** (per master outline), **not** raw tokens.

### Evaluation of named capabilities

| Capability | Truly valuable | Replaceable / commodity | Lock-in / trust |
|------------|----------------|-------------------------|-----------------|
| **Unified Intake** | **Yes** — spine of the SKU | Generic chat UI is commodity | **Configs + scenarios + office habits** |
| **Office Workbench** | **Yes** for adoption | Spreadsheet + CRM is substitute | **Depth of case lifecycle + tone** |
| **Replay / simulation** | **Yes** for **sales + QA**; must stay **honest** (non-prod, version-pinned) | Manual testing | **Regression culture** as moat |
| **Truth system (PG + facades)** | **Yes** when enabled — reduces “model said it” risk | File JSON | **Operational trust** |
| **Lifecycle system** | **Yes** — differentiates from Q&A bots | — | **Handoff structure** |
| **Append / add-car flows** | **Yes** — core workflows | — | **Edge-case tests** |
| **Auditability** | **Under-built** — **blocker** for scale | External ticketing | **Enterprise** |
| **Handoff structure** | **Yes** — product differentiator | Email alone | **Templates + formal submit** |
| **Structured service records** | **Yes** — the durable object | — | **Integration surface** later |

**Illusion to avoid:** “Smarter AI replies” as the product — **commodity** and **trust-risk**. **Moat** is **domain-shaped intake + truth discipline + replay + packs**.

---

## SYSTEM_MAP

```
[ Browser: Unified Intake / Workbench / Simulation ]
        │  HTTP: /api/inbox/*, client config, analytics hooks
        ▼
[ routes/inbox_triage.py ]
   ├─ session_store / session_repository
   ├─ case_truth_repository (stub vs full; JSON vs Postgres)
   ├─ entity_repository + vehicle scope cache
   ├─ triage.py — conversation + policies (add-car, append, handoff, …)
   ├─ handoff / reply composers, assist_layer (additive)
   └─ analytics: minimal_events + funnel_events (JSON log lines)
        │
        ▼
[ TriageResult + case lifecycle ] → customer copy + workbench

[ Same process: search, code graph, other agents — same FastAPI app ]
```

**Knowledge:** Qdrant + retrieval; must **not** overwrite entity truth without rules (`docs/PLUGIN_ARCHITECTURE_MAP.md`).

---

## CURRENT_DEPLOYMENT_MODEL

| Layer | Model | Notes |
|-------|--------|------|
| **API** | GCP **Cloud Run** (`Dockerfile.cloudrun`, `deploy_rag_demo.sh`) | Stateless containers; secrets often env / optional Secret Manager |
| **UI** | **Vercel** SPA | `VITE_API_BASE_URL` → API |
| **Vector** | **Qdrant** Cloud or self-hosted | Collection e.g. `auto_insurance_demo_core` |
| **DB** | **Postgres** optional but **required** for real multi-instance / sessions | Flags: `UNIFIED_INTAKE_DB_PRIMARY_*`, `SERVICE_RECORD_DATABASE_URL` |
| **CI** | GitHub workflows | Contract CI — not full release automation for tenants |

**Doc debt:** `DEPLOY_AUDIT.md` / `deploy_cloud_run.sh` naming vs `deploy_rag_demo.sh` — **one golden path** needed for SaaS ops.

---

## CURRENT_OPERATOR_MODEL

- **Founder + runbooks:** `scripts/trial_launch_check.sh`, guardrails, demo checklist — **strong for 1–3 customers**, **fragile for 10+**.
- **Configuration:** **env vars + JSON packs** — no **self-serve “mode panel”** for non-engineers.
- **Support:** **No** ticket/incident integration, **no** customer-visible status page story.
- **Release:** Manual deploy; **no** per-tenant release channel (canary per org).

---

## CURRENT_TRUST_MODEL

- **Design intent:** LLM **proposes**; **facades / DB** **own** vehicle & case authority when configured; **formal submit** is a **product gate** (`UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md`).
- **AI disclosure:** Workbench + copy can **imply** automation; **explicit “what is AI vs rule vs DB” buyer-facing spec** still **missing as a product artifact**.
- **Escalation:** Human-in-loop fields and handoff — **partially** encoded; **no** unified escalation playbook **as product**.

---

## CURRENT_REPLAY_MODEL

- **UI:** Scenario replay tab / `persist_case: false` simulation — **same API semantics** as live where intended.
- **Scripts:** Scenario libraries, regression runners, guardrails — **high leverage**.
- **Gap:** **Pinned “replay contract”** (pack hash, flags, model id, git sha) **not** a **first-class export artifact** for customers — **internal-first**.

---

## CURRENT_ANALYTICS_MODEL

- **Implementation:** `track_event` → **JSON lines** on `analytics` logger; funnel helpers in route — **best-effort**, **not blocking** response.
- **Partitioning:** **No** `tenant_id` / `org_Id` as standard dimension — **blocks billing-grade metering** and **B2B product analytics**.
- **Risk:** Funnel definitions can drift vs triage flags; **version** funnel schema with product changes.

---

## CURRENT_PLUGIN_MODEL

**Real:** Client pack, industry pack, facades for case/entity/session stores, template hooks.  
**Incomplete:** `LLMAdapter` **not** fully institutionalized; `active_vehicle_resolver` **documented gap** vs `triage.py` (`docs/DEPRECATED_PATHS.md`, `PLUGIN_ARCHITECTURE_MAP.md`).  
**Risk:** **“Hot-swap”** is **true for copy**, **partially false for behavior** — much in **`triage.py`**.

---

## CURRENT_PACK_MODEL

- **Merge order:** common → industry → client (`config_loader.py`).
- **Isolation:** **No cross-client fallback** for sensitive structures — **correct** instinct.
- **UI:** `ClientConfigContext`, `clientConfig.ts`, `ui_copy` — **partial packs** can **look** like reference broker until completed.

---

## CURRENT_SCALING_LIMITS

| Horizon | Breaks first | Why |
|---------|----------------|-----|
| **~10 offices (single deploy)** | **Support + config errors** | Linear founder time; env/pack mistakes; **no admin shell** |
| **~10 offices (multi-instance)** | **Provisioning cost** | No **instance factory**; manual Cloud Run + DB per broker |
| **100 offices (shared app, no tenancy)** | **Data leakage + analytics + permissions** | **No row-level tenant key + auth** |
| **100 offices (shared DB, weak isolation)** | **Compliance + incident blast radius** | **Retrofitting tenant_id** on fat schema is expensive |

**Technical:** JSON case store as **authority** **does not** scale for **multi-tenant** cloud; **Postgres-primary** is the **required** direction for SaaS density.

---

## CURRENT_SAAS_GAPS

1. **Tenant / org model** in data Plane (**or** **automated single-tenant instances**).
2. **AuthN/AuthZ** (office admin vs producer vs read-only).
3. **Billing + metering** (even if v1 is **manual invoice + usage spreadsheet** — **data must exist**).
4. **Audit export + immutability story** (minimal viable).
5. **Product-only deploy surface** (strip lab routes from **customer-facing** binary).
6. **Central feature-flag / env matrix** with **role-based** controls.
7. **Onboarding automation** (DB migrate, seed Qdrant, CLIENT_ID, smoke tests).
8. **Support tooling** (impersonation **safely**, read-only prod triage, replay package).
9. **Regional / data residency** path (even if “US-only v1”).
10. **API keys / rate limits** per customer.

---

## CURRENT_BUSINESS_MODEL

**As documented:** First **paid pilot**, **manual payment**, **testimonial** — **deliberately simple**.  
**For SaaS transition:** Need **repeatable pricing**: e.g. **onboarding fee + per-office monthly**, later **meter on formalized cases** once analytics trustworthy. **Avoid** **per-token** positioning.

---

## CURRENT_DEPLOYMENT_COSTS

**Rough (from `docs/DEPLOYMENT_READINESS.md`):** Vercel hobby ~free; Cloud Run ~$0–5/mo light; Qdrant free/low tier; **OpenAI pay-per-use** dominates variable cost at volume. **Hidden cost:** **engineering + founder support** per broker without automation.

---

## TENANCY_REVIEW

| Question | Recommendation |
|----------|----------------|
| Single-tenant per office? | **Possible** via **instance per customer** (strong isolation, higher ops) or **org_id** rows (true SaaS engineering). |
| Shared multi-tenant? | **Requires** **tenant_id everywhere** + **auth** + **RLS or strict query discipline** + **analytics partition**. |
| Hybrid? | **Plausible:** **e.g. enterprise instance**, **SMB shared** — **two playbooks**, expensive. |
| Vector DB | **Per-tenant collection** or **tenant partition** in metadata — **must not** leak across brokers. |
| Replay | **Same engine**; **separate** storage / flags so **simulation never poisons prod**. |
| Analytics | **Partition by org** — mandatory for SaaS. |
| White-label | **Partial** (copy from API); **full** (domain, theme, email) **later**. |
| Regional packs | **Config**-level first; **data residency** is **separate** sale. |

**Cheapest workable SaaS path:** **Automated instance-per-customer** (Terraform/ClickOps template + health checks) **before** **big multi-tenant rewrite**, unless **committed team + revenue** for **B**.  
**Safest onboarding path:** **One golden template** + **read-only smoke suite** + **checklist**.  
**Easiest support path:** **Structured logs + case id + replay export** (not raw “check the server”).

---

## BILLING_REVIEW

- **Today:** No Stripe — **fine for pilot**.
- **SaaS-ready:** Need **entitlements** (which packs, caps on cases/messages), **invoice line items** aligned to **formalized cases** or **seats**.
- **Upsell hooks:** **Audit export**, **advanced analytics**, **SLA**, **extra environments** (staging).

---

## AUDITABILITY_REVIEW

**Must exist (minimum viable):**

- **Immutable (or append-only) record** after **formal submit**: who/when/what changed on **service record** + **vehicle entity**.
- **Versioned config** applied to a case (client pack version / git sha).
- **Export:** JSON/CSV **per case** and **per org** for disputes.

**Enterprise stretch:** SIEM integration, tamper-evident storage, **SOC2** controls.

---

## REPLAYABILITY_REVIEW

**Must replay:** **Triage decisions** affecting **case creation, append vs new, vehicle key, handoff readiness** — inputs + **non-secret** config snapshot + model version.  
**Must version:** **Industry/client pack**, **feature flags**, **prompt/templates** where LLM used.  
**Legal/ops exposure:** **Customer-visible copy** that **overstates certainty** vs structured truth.

---

## SUPPORTABILITY_REVIEW

**Gaps:** No **first-class** “support bundle” (case dump + redacted logs + replay script); **no** **runbook** for **tenant-safe** prod read-only access.

---

## ONBOARDING_REVIEW

**Friction today:** Manual env, **knowledge of repo**, Qdrant seed, **CLIENT_ID** wiring.  
**SaaS need:** **Provisioning runbook → API**: create org, DB schema/migrate, deploy pointer, seed retrieval, smoke **green**, hand **URL + admin invite**.

---

## OFFICE_ADMIN_REVIEW

**Missing:** **Office-level** settings (users, roles, handoff recipients, template overrides) **without** code deploy. **Producer vs admin** UX not fully separated.

---

## OPERATOR_EXPERIENCE_REVIEW

- **Confusion:** “What is SearchForge vs Intake?” **Monolith** surfaces **too many** routes for **broker operator**.
- **Training cost:** Dense workbench + bilingual flows — need **guided mode** + **defaults**.
- **Should be admin-only:** Lab routes, experiment toggles, destructive migrations.

---

## MULTI_OFFICE_REVIEW

**Within one broker:** Multiple **producers** sharing cases — needs **permissions** and **case assignment** (even lightweight). **Not** a full CRM — but **“who owns this case?”** matters at **10+ users**.

---

## DEPLOYMENT_TOPOLOGY_OPTIONS

| Option | Pros | Cons |
|--------|------|------|
| **A. Instance-per-customer** | Strong isolation, simpler mental model, **no** row-level rewrite | **Ops automation** required; cost per idle instance |
| **B. Shared multi-tenant** | Better margin at scale | **Big** eng: auth, tenant_id, RLS, noisy neighbor |
| **C. Cell-based** (tenants grouped per cell) | Balance | **Two-tier** ops complexity |

**Recommendation:** Default **A** until **MRR + compliance forces B**, per prior CEO review — **still valid**.

---

## PRODUCTIZATION_ROADMAP (high level)

1. **Truth + single vehicle authority** → **shrink triage policies** → **product-only deploy** → **tenant/instance automation** → **audit + metering** → **integrations**.

---

## SYSTEM_SIMPLIFICATION_OPPORTUNITIES

- **Split deploy:** **“intake-api”** image vs **“full lab”** image — same codebase, **different router mounts**.
- **Extract:** Add-car / append / handoff **policy modules** from **`triage.py`** — **config-facing contracts**.
- **Wire or delete** `active_vehicle_resolver` — **one authority**.
- **Simulation:** Keep **clearly non-prod**; optional **export last run** as **replay artifact**.
- **Analytics:** **Tenant dimension** + **schema version** in every event.

---

## TOP_10_BLOCKERS_TO_REAL_SAAS

1. **No tenant boundary** in persistence + analytics (**or** **non-automated** instance-per-customer).
2. **Monolith API** — lab + intake **same** process — **security + story + blast radius**.
3. **`triage.py` gravity** — **pack narrative** weakens; **every fork** is **engineering**, not CS.
4. **AuthZ absent** — **cannot** sell **team** product safely.
5. **Audit / export** absent — **enterprise** and **disputes** fail.
6. **Deployment / provisioning** manual — **does not** scale to **N customers**.
7. **Session/case scale docs** vs code — **multi-instance** readiness **must be single truth**.
8. **Analytics** not **partitioned** — **no honest metering**.
9. **LLM variance** **unpinned** in prod narrative — **trust** incidents.
10. **Operator dependence** on founder — **no** admin **or** **playbook** at volume.

---

## TOP_10_HIGH_LEVERAGE_MOVES

1. **Instance factory** (or **tenant_id spike**) — **unblocks revenue ops**.
2. **Product-only router set** — **cut attack surface** + **clear SKU**.
3. **Single vehicle authority** — **trust** + **less double maintenance**.
4. **Formal “Trust spec” PDF** for buyers — **AI/rule/DB** + **immutability**.
5. **Case + config export** — **support** + **audit MVP**.
6. **Pack validator CI** — **faster safe onboarding**.
7. **Replay pin bundle** (hash flags + pack + sha) — **sales + QA**.
8. **Analytics `org_id` + version** — **future billing**.
9. **Role-based workbench** — **adoption** in multi-user offices.
10. **LLM adapter + golden fixtures** — **provider + release safety**.

---

## TOP_10_REAL_SAAS_MOVES

Ranked by **ROI × leverage** (ROI: H/M/L; Eng complexity: H/M/L; Operational leverage: H/M/L; Product leverage: H/M/L; Business leverage: H/M/L):

| Rank | Move | ROI | Eng | Ops Lev. | Prod Lev. | Bus Lev. |
|------|------|-----|-----|----------|-----------|----------|
| 1 | **Tenant strategy decision + MVP** (A: instance factory **or** B: `org_id` spike end-to-end one path) | H | H | H | H | H |
| 2 | **Product-only deployment profile** | H | M | H | M | H |
| 3 | **Single vehicle resolution authority** | H | M | H | H | M |
| 4 | **Audit export MVP** (case + entity + activity) | M | M | H | M | H |
| 5 | **Analytics partition key + schema version** | M | L | M | M | H |
| 6 | **Triage policy extraction** (add-car + append first) | H | H | M | H | M |
| 7 | **Onboarding runbook → scripted provision** | H | M | H | M | H |
| 8 | **LLM adapter boundary + golden JSON** | M | M | M | M | M |
| 9 | **Workbench roles (admin vs producer)** | M | M | H | H | M |
| 10 | **Replay artifact export** | M | L | M | H | M |

---

## ROADMAPS (by work type)

### 30 days

| Type | Tasks |
|------|--------|
| **Engineering** | Product-only deploy profile; **vehicle authority** convergence spike; analytics `org_id`/`tenant_id` field (even if constant); fix deploy script **naming golden path**. |
| **Platform** | Document **one** provisioning checklist; **Secret Manager** pattern default; **staging** template. |
| **Product** | Ship **Trust spec** v0; **simulation** labeled **non-prod** unambiguously. |
| **Business** | **Second paid pilot** terms; **pricing** draft (office + onboarding). |
| **Onboarding** | **Pack completeness checklist**; **smoke script** after deploy. |
| **Operational** | **Incident log** template; **support bundle** manual process. |

### 90 days

| Type | Tasks |
|------|--------|
| **Engineering** | Begin **triage policy extraction**; **audit export API**; **LLM adapter** skeleton + tests. |
| **Platform** | **Instance factory v0** **or** **multi-tenant read path** for one entity (cases). |
| **Product** | **Admin read-only** mode panel sketch; **role-based** workbench MVP. |
| **Business** | **Metering pilot** on **formalized cases** (spreadsheet ok if pipeline honest). |
| **Onboarding** | **Self-serve staging** per customer optional. |
| **Operational** | **Playbook** for **10 customers**. |

### 1 year

| Type | Tasks |
|------|--------|
| **Engineering** | Full **tenant** model **or** **mature** multi-instance; **integration** MVP (export to AMS/email/calendar). |
| **Platform** | **SSO** roadmap; **regional** deploy option. |
| **Product** | **Enterprise** audit narrative; optional **white-label**. |
| **Business** | **Tiered** SKUs; **partner** channel (MGAs/agencies). |
| **Onboarding** | **90% scripted** provisioning. |
| **Operational** | **CS hire** readiness — dashboards + runbooks. |

---

## PHASE_9_VALIDATION — SELF_CRITIQUE_REPORT

| Question | Answer |
|----------|--------|
| Optimizing the wrong thing? | **Risk yes** if continuing **latency** / **micro-refactor** without **tenancy + trust artifacts**. |
| Building too much platform? | **Risk yes** — **monolith lab** alongside intake **signals** platform; **commercial SKU** should stay **narrow**. |
| Overestimating AI value? | **Yes** if marketing **“smarter assistant”** vs **“case spine + replay”**. |
| Underestimating onboarding/support? | **Yes** — **N× manual deploy** **kills** margin before **code** does. |
| Underestimating tenant isolation? | **Yes** — **one** cross-tenant leak **ends** niche broker trust. |
| Underestimating operator trust? | **Yes** — **vehicle wrong once** **>** **100 slick turns**. |
| What kills the product even if eng is strong? | **Support collapse**, **trust incident**, **unclear buyer** (“is this ChatGPT?”), **pricing** misaligned with **value unit**. |

---

## STRATEGIC_RISK_MATRIX

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Data isolation failure** | M | Catastrophic | Instance-per-customer **or** RLS + audits; **no** ambiguous shared DB |
| **triage.py unbounded growth** | H | High | **Policy extraction** + **hard module budget** |
| **LLM trust incident** | M | High | Truth spec; **DB wins**; **replay pins**; **disclosure** |
| **Ops overload at 10 customers** | H | High | **Factory** + **admin tools** + fewer **manual** envs |
| **Wrong analytics → wrong price** | M | Medium | **Version** events; **manual** reconcile before automated billing |
| **Scope creep to CRM** | M | High | **Master outline** gate; **say no** in PR review |
| **Security: lab routes in prod** | M | High | **Product-only** deploy |
| **Founder bottleneck** | H | Medium | **Documentation** + **hired ops** path |

---

## FINAL_RECOMMENDATION

**Treat Unified Intake as the only commercial SKU short-term.** **Force** a **tenant strategy** (prefer **automated single-tenant** until scale demands **shared multi-tenant**). **Ship** **minimum audit + partitioned analytics** before **automated billing**. **Slim** the **deploy surface** for **customer** environments. **Shrink `triage.py` into policies** so **packs become honest**.

---

## FINAL_DECISION

**Proceed** to **real SaaS posture** by **sequencing**: (1) **product-only deploy** + **vehicle authority**, (2) **tenant MVP** (**instance factory** default), (3) **audit export + analytics org dimension**, (4) **pricing tied to formalized cases / seats**. **Defer** **generic platform/GTM** for **SearchForge lab** until **intake revenue** compounds.

---

## PILOT_TO_REAL_SAAS_FINAL_REPORT

1. **What this system REALLY is** — **A vertical intake and workbench product** (Add-Car flagship) that turns messy messages into a **durable service record** with **handoff discipline**; the repo **also** hosts **broader SearchForge/FIQA** surfaces that **must not** define the **paid SKU**.

2. **What makes it commercially viable** — **Painkillers**: **bilingual/thread-heavy broker ops**, **formal submit artifact**, **replay/regression culture** — **sold as reliability**, not **clever chat**.

3. **What the moat is** — **Domain scenarios + explicit truth layering + pack isolation + operator playbooks** — **not** the embedding model.

4. **What the biggest illusion is** — That **“better AI”** wins; **winner is predictable case truth** and **office trust**.

5. **What is overbuilt** — **Single process** carrying **many non-intake routers** and **R&D agents** for **buyers who only need intake**.

6. **What is underbuilt** — **Tenancy/auth**, **audit export**, **provisioning automation**, **billing-grade analytics**, **admin UX**.

7. **Biggest scaling blocker** — **No operational tenancy model** (**data + metering + support**) at **10–100 customers**.

8. **Biggest onboarding blocker** — **Manual provisioning** + **pack/env complexity** without **validator + factory**.

9. **Biggest trust blocker** — **Any** systematic drift between **customer-facing copy** and **structured truth**; **unbounded LLM variance** without **pins/disclosure**.

10. **Best deployment strategy** — **Golden path**: **Vercel + Cloud Run + Postgres + Qdrant** with **product-only** container; **repeat via template** per customer until **multi-tenant** justified.

11. **Best SaaS strategy** — **Start** **managed instance-per-customer** with **clear upgrade** to **shared infra** when **economics + compliance** align.

12. **Best tenant strategy** — **`org_id` in events + DB** **even** on single-tenant deploys (future-proof); **full** row-level isolation when **one** shared DB.

13. **Best monetization strategy** — **Onboarding fee + monthly per office**; later **usage on formalized cases**; **avoid** raw token pricing.

14. **Best product niche** — **CA auto broker offices**, **Add-Car + append**, **Chinese-speaking clientele** — **narrow** and **deep**.

15. **Best next engineering move** — **Product-only FastAPI profile** + **single vehicle authority**.

16. **Best next product move** — **Buyer-facing Trust spec v1** (AI vs rules vs DB; immutability after submit).

17. **Best next business move** — **Second paying office** with **time-saved evidence** and **replay proof**.

18. **Final productization judgment** — **Pilot-grade intake is real; SaaS company is not automatic** — **winning** means **choosing** **tenancy**, **shrinking** **monolith scope for customers**, and **shipping** **auditability** **before** **“platform”** ambitions.

---

*End of PILOT_TO_REAL_SAAS_TRANSITION_SPRINT.md — single source of truth for this sprint.*
