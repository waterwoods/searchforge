# LONG_HORIZON_SAAS_OPERATING_SYSTEM_SPRINT — Sprint SSOT

**Authority:** This file is the **single source of truth** for this long-horizon “Unified Intake → SaaS operating skeleton” convergence. Earlier sprint notes (`PRODUCT_ONLY_SAAS_SKELETON_SPRINT.md`, `FUTURE_SAAS_OPERATING_SYSTEM_SPRINT.md`, etc.) remain historical; where they conflict with **explicit decisions here**, prefer **this** document after the reconciliation row in §0.5.

**Sprint archetype:** System / operator / tenancy / deployment **architecture** convergence — **not** a micro-optimization sprint.

**North star docs (unchanged):**  
`docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md`, `docs/UNIFIED_INTAKE_MVP_BOUNDARIES.md`, `AGENTS.md`.

---

## 0. Sprint control note

### 0.1 Objective

Evolve Unified Intake from **pilot-grade capability embedded in a platform monolith** toward a **credible SaaS company operating skeleton**: clear **product vs lab** boundaries, **operator** workflows, **onboarding** discipline, honest **deployment** posture, **replay/regression trust**, and a path to **multi-tenant** reality — without pretending auth, billing, or full isolation already exist.

### 0.2 Non-goals (this sprint doc + scoped code)

- No Stripe, no IAM product, no “real” multi-tenant row-level enforcement.
- No wholesale `triage.py` / resolver rewrites.
- No promise that **`UNIFIED_INTAKE_PRODUCT_ONLY=1` equals minimal attack surface** until inline `app` routes are gated or slimmed (see §1.6).

### 0.3 Definition — “fake SaaS” vs “real SaaS skeleton”

| Term | Meaning in this repo |
|------|----------------------|
| **Fake SaaS** | Env flag or slide deck claims (“product-only”) that **omit** lingering platform endpoints, founder-only scripts, single-tenant data, manual onboarding, no billing meter, no org-scoped IAM. |
| **Real SaaS skeleton** | **Documented** authority, honest deploy surface inventory, repeatable regression (`guardrail`, scenarios), onboarding checks (pack layout), optional org header hooks, separation narrative UI/API can defend in diligence. |

### 0.4 Evolution log (append during sprints)

| Date (UTC) | Change |
|------------|--------|
| 2026-05-07 | **Phase 0–3** authored; **deployment_profile** extended with countable `PLATFORM_INLINE_ROUTES_UNGATED_IN_APP_MAIN` + strengthened startup banner; `tests/test_deployment_profile.py` added. Prior branch work preserved (inbox/session/repository deltas). |
| 2026-05-07 | **Phase 6 closeout:** `compileall` PASS; `pytest` `test_deployment_profile` + `test_pack_validation` (6) PASS; **guardrail** PASS; **UI build** PASS with Node **22.22** on `PATH` (default Node 20.18 fails Vite 7); **madge** no cycles; **`run_full_regression.py`** PASS (`http_p95_ms` **4790**, `wrong_vehicle_related` **0`). |

### 0.5 Reconciliation vs prior sprint authority

| Topic | Prior claim | Long-horizon position |
|-------|-------------|------------------------|
| Product-only deploy | Router subset suffices for “v1” | **Insufficient for honesty** unless inline routes inventoried/gated — now **counted in code** (`platform_inline_route_leak_count`). |
| Multi-tenant | Out of scope (AGENTS.md) | Still **no AuthZ** — **`X-Org-Id`** is **telemetry/onboarding posture only** until composite keys land. |

---

## PHASE 0 — Git + safety (recorded)

### 0.A Branch

`auto-evolution/long-horizon-saas-operating-system-20260507`

### 0.B Repo snapshot notes (examples from sprint start discovery)

Recording policy: **dirty / untracked** lists are machine-specific snapshot at kickoff — use `git status` before release.

Typical tracked areas for this lineage:  
`services/fiqa_api/routes/inbox_triage.py`, `inbox_triage/*`, `app_main.py`, `ui/src/pages/UnifiedIntakePage.tsx`, `ui/src/api/inboxTriage.ts`.

**Stashes:** Operator should run `git stash list` locally; merge policy is founder-owned.

**Rule:** Avoid committing unrelated **`results/`** JSON noise or ephemeral lock files unless adopting a disciplined artifact policy.

---

## PHASE 1 — SAAS_OPERATING_SYSTEM_MAP

### 1.1 Layer stack

```mermaid
flowchart TB
    subgraph exposure [Exposure]
      UI[Vite SPA ui/]
      API[FastAPI app_main]
    end
    subgraph product [Declared product surface]
      IN[/api/inbox/*]
      AN[/api/analytics/dashboard]
      HL[health + qdrant probes]
    end
    subgraph lab [Lab / platform]
      WK[Workbench routes codemap rag-lab vitals]
      OPS[Ops metrics autotuner labops]
      IL[Inline app routes see 1.6]
    end
    UI -->|VITE_API_BASE_URL| API
    API --> product
    API --> lab
```

### 1.2 UI routes — product-adjacent vs lab (`ui/src/App.tsx`)

| Category | Paths | SaaS honesty |
|---------|-------|---------------|
| **Unified Intake shell** | `workbench/unified-intake` | Core product UX. |
| **Demo / intake-adjacent** | `demo` (top-level) | Sellable demos; clarify vs production SKU. |
| **Scenario / replay UI** | `workbench/scenario-logic-center`, add-car rules | **Pilot / founder** tooling — bounded under “professional services” narrative until isolated. |
| **Lab/workbench** | `workbench/*` (Retriever, SearchLab, Mortgage, JobHunter, Code Map, …), `rag-lab/*`, `lab/metrics` | Clearly **platform** — not billable SKU without repackaging. |
| **Observability** | `vitals` | Depends on ingest routes — **often absent** under product-only API profile. |

**Product-vs-lab verdict:** SPA ships **everything** — **routing is not SKU packaging**. Real boundary is API + entitlement + CDN config (future), not Router entries alone.

### 1.3 API — product-only router gate (`app_main.py`)

**Always mounted (current policy):**

- Unified Intake: `inbox_triage_router` → `/api/inbox/*`
- Founder/analytics dashboard: `analytics_dashboard_router` → `/api/analytics/dashboard`
- Health/Qdrant: `health_router`, `qdrant_health_router`, `qdrant_info_router`
- Inline health family: `/health/live`, `/api/healthz`, `/health/ready`, `/health`, `/ready`, `/healthz`, `/version`, `/` (SPA mount optional)

**Gated off when `UNIFIED_INTAKE_PRODUCT_ONLY=1`:**  
`debug_router`, `search`, `query`, KV experiment, vertical agents (`mortgage`, `ecommerce`, `jobhunter`), `experiment`, `steward`, `code_lookup`, `code_graph`, `best`, ops/metrics/black_swan/autotuner/quiet/lab routers, unified `/api/agent/*` registration block (v2/v3 handlers).

### 1.4 Core flows mapped to modules

| Flow | Primary modules |
|------|-----------------|
| **Onboarding (client pack)** | `configs/clients/{id}`, `pack_validation.validate_client_pack_layout`, `routes/inbox_triage` client-config |
| **Triage authority** | `inbox_triage/triage.py`, post-process + PG truth in `inbox_triage.py` |
| **Resolver / vehicle truth** | `active_vehicle_resolver.py` (parallel doc), merge + finalize in triage/route layer |
| **Session (pre-case)** | `session_store.py`, `session_repository.py` |
| **Case lifecycle** | `case_lifecycle.py`, `case_store.py`, `case_truth_repository.py` |
| **Persistence** | `db/service_record_repository.py`, `db/service_record_settings.py` |
| **Replay / regression** | `configs/inbox_triage_scenarios.json`, `scripts/run_inbox_triage_scenarios.py`, `scripts/guardrail_inbox_triage.sh`, `scripts/run_full_regression.py` |
| **Analytics** | `analytics/minimal_events.py`, funnel buffers, dashboard route |
| **Audit (future)** | `inbox_triage/audit_export.py` → forwards to events today (**no compliance claim**) |

### 1.5 Tenancy / office / billing (as-is)

| Lifecycle | Reality today | Skeleton hooks |
|-----------|---------------|----------------|
| **Tenant** | Single deploy ↔ single org mentally | Optional `X-Org-Id` on triage (telemetry path) |
| **Office** | Config copy + branding JSON | Same pack system — **no per-office IAM** |
| **Billing** | None | Trial/pilot commercial motion external |
| **Pack lifecycle** | Git-tracked JSON in repo | `pack_validation` for CI/onboarding checklist |

### 1.6 **Major discovery:** inline platform routes (**product-only dishonesty gap**)

**Problem:** Numerous **lab/platform** endpoints are declared with `@app.route` **below** the `include_router` gate and thus **remain reachable** even when `UNIFIED_INTAKE_PRODUCT_ONLY=1`.

**Authoritative inventory (code):** tuple `PLATFORM_INLINE_ROUTES_UNGATED_IN_APP_MAIN` in `services/fiqa_api/deployment_profile.py` — **must stay aligned** with `grep '^@app\\.' services/fiqa_api/app_main.py` (excluding pure health/root/version and SPA `{full_path}`).

**Operational implication:** Operators **must not** assume the env flag is a **WAF** — it is **router-subset + documented debt**.

### 1.7 Operational debt tags

| Debt | Severity |
|------|----------|
| Inline ungated platform routes under product-only | **Trust / security / sales honesty** |
| SPA includes full lab NAV | **Positioning clarity** |
| No immutable audit ledger | **Regulatory / disputes** |
| Single-tenant identifiers in DB/API | **10+ customer scaling** |

---

## PHASE 2 — DOUBLE_BRAIN_MATRIX_V2 (authority & duplication risks)

Legend: **A** = authoritative for customer-visible truth; **I** = input only; **D** = durable store; **R** = regression-only.

| Concern | Primary owner | Shadow / alternate | Risk |
|---------|---------------|--------------------|------|
| **Triage outcome** | `triage.py` + route post-process | LLM abstain paths, assist layer | Divergent narratives if guardrails loosen |
| **Vehicle / add-car resolver** | Triage merge + PG finalize doc path | `active_vehicle_resolver.py` tests | Double edits if engineers fix “wrong brain” |
| **Case reads** | `case_truth_repository` | JSON façade / legacy reads | Split-brain stale UI |
| **Writes** | `case_store`, `service_record_repository` flags | Silent DB-down fallback | Operational “looks saved” dishonesty |
| **Persistence mode** | `service_record_settings` env | Founder toggles | Undocumented env = founder knowledge |
| **Replay authority** | Scenario JSON + deterministic LLM-off runs | Manual demo | Regression ≠ contractual audit yet |
| **Onboarding authority** | `configs/clients` + pack validation | Forked demo.env | Broken pack onboarding |
| **Analytics** | `track_event`, dashboard aggregates | Logs only | Attribution gaps for billing disputes |
| **Deploy authority** | `Dockerfile.cloudrun`, `deploy_rag_demo.sh` | “Demo mode” healthy without full SKU | Overselling uptime/fitness |
| **Operator authority** | Founders/scripts | Non-runbook edits | KMS (founder-memory-system) coupling |

---

## PHASE 3 — Operator workflow simulations (desk + platform)

Symbols: ⚠ friction, ▢ missing boundary, ◆ debt, ⧫ trust gap, ? product confusion risk.

### 3.1 New broker **office** onboarding

- ⚠ SPA shows **full lab NAV** unless build-per-SKU hides it.
- ⧫ Tenant claims premature — **office** ≠ **deploy** isolation.
- **Replay:** Scenario pack unaffected — **trust** rests on demos not enterprise isolation.

### 3.2 New **customer pack** onboarding

- ▢ `validate_client_pack_layout` checks **presence** — not semantics quality.
- ◆ Editing JSON without rerun guardrail → rollout risk.

### 3.3 **Add-car** workflow

- ? Customers may confuse “draft card” vs “bound coverage.”
- ⧫ Resolver ambiguity — broker must corroborate (docs already say broker edit).

### 3.4 **Multi-turn append**

- ⚠ Continuity regressions guarded by §scripts first-turn/`pre_post_submit` oracle — good skeleton.
- ◆ Split-brain if PG primary toggles drift mid-session.

### 3.5 **Wrong-vehicle correction**

- Depends on finalize path + resolver doc — **scaling** hinges on deterministic truth logs (missing).

### 3.6 **Replay / audit**

- ✅ Strong **regression replay** (`guardrail`).
- ⧫ **`audit_export` is explicitly non-compliance**.
- Replay **cannot** adjudicate billing alone.

### 3.7 **Escalation workflow**

- Triage escalation flags surfaced — **routing to human queue**: still **broker workflow**, not ticketing SaaS.

### 3.8 **Support incident**

- No multi-customer ticketing; **depends on founders** interpreting logs/events.

### 3.9 **Operator mistake** (mis-config env)

- `UNIFIED_INTAKE_DB_PRIMARY_READS` rollback semantics live in repo — **implicit operator knowledge.**

### 3.10 **Deployment rollback**

- Cloud Run revision rollback exists — **schema** rollback not automated narrative.

### 3.11 **Broken pack onboarding**

- `pack_validation` returns issues list — needs **wired operator UX** / CI gate for SaaS onboarding team.

### 3.12 **Missing config workflow**

- Runtime may degrade gracefully — surfaced clarity varies; founders debug via logs.

### 3.13 **Tenant isolation failure** (simulated)

- **Global** `case_id` / sessions without org composite keys → cross-tenant read risk if auth added late incorrectly.

### 3.14 **Analytics discrepancy**

- Minimal events ≠ accounting ledger — disputes need export discipline (future).

### 3.15 **Billing dispute** (simulated)

- **No metered usage** artifact — skeletal trust gap.

---

## PHASE 4 — TOP_20_SAAS_PRODUCTIZATION_MOVES

Rank axes: ROI, ops leverage, SaaS readiness, trust, engineering difficulty, regression risk, deploy complexity (↑ = harder/higher risk).

| # | Move | ROI | Leverage | SaaS-ready | Trust | Eng | Regress | Deploy |
|---|------|-----|----------|------------|-------|-----|---------|--------|
| 1 | Gate or relocate **inline `@app`** lab routes behind product-only OR split ASGI mounts | ●●●● | ●●● | ●●●● | ●●●● | ●●● | ●●● | ●●● |
| 2 | **SPA SKU builds** — hide lab routes for prod bundle | ●●● | ●●● | ●●● | ●●● | ●● | ●● | ●● |
| 3 | **`org_id` composite** keys in DB/API | ●●● | ●● | ●●●● | ●●●● | ●●●● | ●●●● | ●● |
| 4 | **Immutable audit stream** (+ export API) beyond `track_event` | ●●● | ●●● | ●●● | ●●●● | ●●●● | ●● | ●●● |
| 5 | Tenant-scoped admin for **pack publish** pipeline | ●●● | ●●●● | ●●● | ●●● | ●●● | ●● | ●● |
| 6 | Automated **trial billing** metering (events → ledger) | ●●●● | ●●● | ●●●● | ●●●● | ●●● | ●● | ●● |
| 7 | **Runbook-linked** readiness checks (`trial_launch_check`) as CI gate per SKU | ●●● | ●●●● | ●●● | ●●● | ● | ● | ● |
| 8 | Separate **Docker image SKU** slimming deps | ●● | ●● | ●●● | ●●● | ●●● | ●● | ●●● |
| 9 | Structured **tenant onboarding** checklist API | ●●● | ●●●● | ●●● | ●●● | ●● | ● | ● |
| 10 | **Escalation** export to ticketing (Zendesk webhook) — narrow | ●● | ●●● | ●● | ●●● | ●● | ●● | ● |
| 11 | Replay UI behind **feature flag + auth** | ●● | ● | ●●● | ●●● | ●● | ● | ●● |
| 12 | Consolidate resolver **single authority doc** enforced in CODEOWNERS | ●● | ●● | ●● | ●●● | ● | ● | ● |
| 13 | **Health endpoint catalog** SKU-specific advertised surface | ●● | ●●● | ●●● | ●●● | ● | ● | ● |
| 14 | Postgres migration **version pinning** playbook | ●●● | ●●● | ●●● | ●●● | ●● | ●● | ●●● |
| 15 | **Support** playbook + log correlation IDs across UI/session/case | ●●● | ●●●● | ●●● | ●●● | ●● | ● | ● |
| 16 | Deprecate **mock** portions of `/api/graph/mermaid` fallback in prod SKU | ● | ● | ●● | ●●● | ● | ● | ● |
| 17 | Separate **analytics** warehouse + PII stance | ●●● | ●●● | ●●● | ●●●● | ●●●● | ●● | ●● |
| 18 | Tenant **sandbox** namespaces for scenario abuse | ●● | ●● | ●●● | ●●● | ●●● | ●● | ●● |
| 19 | Formal **support SLAs** + status page honesty | ●●● | ●● | ●●●● | ●●●● | ● | ● | ●●● |
| 20 | **Delete** dormant vertical routers from ingestion image | ●● | ●● | ●●● | ●● | ●● | ●●● | ●●● |

### 4.A Three highest ROI (judgment)

1. **Org-scoped identifiers + tenancy model** aligned with Postgres (no auth yet okay).  
2. **Inline `@app` platform route gating** — removes largest “honesty gap”.  
3. **SKU SPA + Docker** — aligns sales touch with executable reality.

### 4.B Three highest trust wins

1. Immutable **audit/export** trajectory.  
2. **Ingress truth table** advertised per deploy (automate from FastAPI introspection eventually).  
3. **Billing meter** lineage from events → invoice artifacts.

### 4.C Three biggest operational blockers

1. Founder-only env / flags knowledge (`service_record_settings`).  
2. **Monolith cognition load** — every operator trains on repo topology.  
3. **Supporting multi-customer incidents** sans ticketing+metering linkage.

### 4.D Three biggest scaling blockers

1. **Identifier + row-level tenancy** mismatch.  
2. **SPA + API** SKU drift.  
3. **Operational graph intelligence** lacks single observability backbone.

---

## PHASE 5 — Implementation (approved batch; low-risk / high honesty)

### 5.1 What shipped in this lineage

| Item | Files | Why |
|------|-------|-----|
| **Countable inline-route inventory + startup honesty** | `deployment_profile.py` | Moves “everyone kinda knew” → **logged + enumerable** artifact for CEOs/SRE/onboarding engineers. |
| **Tests** | `tests/test_deployment_profile.py` | Prevents accidental empty inventory / regressions on helper. |

**Deferred (correctly)** — wrapping 15+ inline handlers in conditional blocks: **valid** next sprint — requires golden OpenAPI/route diff regression.

---

## PHASE 6 — MULTI-LOOP VALIDATION (record outcomes after each CI run)

| Gate | Command / artifact | Sprint closeout expectation |
|------|-------------------|---------------------------|
| bytecode compile | `python3 -m compileall services/fiqa_api` | PASS |
| targeted pytest | `pytest tests/test_deployment_profile.py tests/test_pack_validation.py` | PASS |
| guardrail | `bash scripts/guardrail_inbox_triage.sh` | PASS (deterministic tiers) |
| full regression | `PYTHONPATH=. python3 scripts/run_full_regression.py` | Run before external pilot promotion |
| UI build | `cd ui && npm run build` | PASS |
| madge UI | `cd ui && npx --yes madge --circular --extensions ts,tsx src` | no cycles |

**Recording policy:** Paste actual summaries into Evolution log §0.4 when executed in CI or locally.

---

## PHASE 7 — DEPLOYMENT + OPERATIONS REVIEW

### Cloud Run profile (`docs/CLOUD_RUN_DEPLOYMENT.md`)

- **`DEMO_MODE`** relaxes readiness semantics — SaaS SKU must redefine **SKU-specific readiness** (embedding optional vs required).  
- **Image carries platform COPY context** — “product-only routing” ≠ minimal supply chain footprint.  
- **Secrets**: `.env.cloudrun`/Secret Manager documented — **rotation + least privilege remain manual**.  

### Operational honesty checkpoints

| Check | Finding |
|-------|---------|
| Router exposure vs inline | ⚠ Gap inventoried (**Phase 5 partial fix** counts + logs). |
| Health checks | Multiple `/health*` variants historically confused Cloud Run fronts — **`/health/live`** + `/readyz` doc’d. |
| Rollback safety | GCP revision rollback — **database forward-only** caveat. |
| Tenancy assumptions | **Single-tenant mentally** unless composite org keys introduced. |

---

## PHASE 8 — SELF_CRITIQUE_REPORT (“brutal”)

### 8.1 What remains **fake SaaS**

- **SPA** still embodies **research platform UX** for unified navigation.  
- **Product-only env** omits gated routers yet **explicit count** (`N` inline routes — see code) exposes continued platform DNA.  
- **No Stripe / auth / metering / audit ledger**.

### 8.2 Monolith debts

- `app_main.py` **triple duty**: health SPA + platform + Unified Intake.  
- Scenario + graph + tuner + embeddings live in **same interpreter**.

### 8.3 Founder-knowledge coupling

- DB primary flags, embeddings posture, Redis assumptions for `/api/metrics/mini`.

### 8.4 Product-only violation vectors

- Ungated **`/api/v1/agent/chat`** and **`/api/embeddings/encode`** are **dangerous demos** masquerading as neighbors to `/api/inbox`.

### 8.5 Scaling fracture points

| Customers | Stress |
|-----------|--------|
| **10** | Support load + onboarding mistakes + env drift—not technical alone. |
| **100** | DB contention + **absence of org partitioning** hurts incident blast radius assumptions. |
| **1000** | **Compliance + cost metering + abuse** overwhelm event JSON logs. |

### 8.6 Operational dishonesty to avoid in sales

- Calling regression assets “audit grade.” Claiming **`UNIFIED_INTAKE_PRODUCT_ONLY` is airtight isolation**. Implying **automatic CRM/coverage binding**.

---

## PHASE 9 — LONG_HORIZON_SAAS_OPERATING_SYSTEM_FINAL_REPORT (20 answers)

**This section satisfies the FINAL_REPORT deliverable.**

1. **What this product REALLY is:** Add-car-first Unified Intake transforming pasted conversation into structured broker work surface — **assistive**, not transactional insurance.  
2. **Moat REALLY is:** Scenario-hardened **California auto broker** vertical fluency + **repeatable demos** tied to scripted regression corpus — ephemeral without continued workflow capture.  
3. **Fake SaaS remains:** SPA breadth, inline platform endpoints, absent billing/IAM narrative.  
4. **Biggest operational blocker:** **Founder-mediated** env + playbook execution — need **SKU CI gates**.  
5. **Biggest trust blocker:** Lack of **durable immutable decision trail per case turn**.  
6. **Biggest onboarding blocker:** **Pack semantics** QA not systematic — filenames alone insufficient.  
7. **Biggest deployment blocker:** **Single image semantics** pretending multiple SKUs.  
8. **Biggest scaling blocker:** Identifier design **sans org partitioning**.  
9. **Best monetization path:** Per-seat broker + onboarding fee + professional pack tuning — metering by **validated triage completions** upstream of billing integrations.  
10. **Best operator workflow improvement:** **Support correlation ID** bridging UI/session/case in ops dashboard.  
11. **Best next productization move:** **Gate inline lab routes** or serve **thin ASGI** for product SKU.  
12. **Best next architecture move:** **Extract intake service boundary** library + package with explicit contracts.  
13. **Best next business move:** **Pilot contract** narrowing claims (see `docs/UNIFIED_INTAKE_MVP_BOUNDARIES.md` safe statements).  
14. **Best next deployment move:** **Published route manifest** emitted at container start from introspected routes + diff vs SSOT tuple.  
15. **Best next onboarding move:** **CI fails** if pack invalid — operator cannot merge silently broken client.  
16. **Best next replay/audit move:** **Persist signed scenario replay bundles** artifact per release tag.  
17. **Best next tenancy move:** **Design composite keys now** (`org_id`,`case_id`) even if reads remain open.  
18. **Best simplification move:** **Remove lab nav entries** from default production SPA config.  
19. **What should be deleted:** Dormant inline mock fallbacks reachable in prod SKU for graph if unused — after telemetry proves zero hits.  
20. **Final productization judgment:** **Strong pilot engine** becoming **sellable SaaS** requires **narrowing executable surface honesty** (`PHASE 5` incremental) plus **economics primitives** (`PHASE 4` top moves) — this sprint elevated **truth visibility**, not pretending scope expanded.

---

## Sprint closeout block (maintainers paste fresh results here)

_Last updated manually per run._

* **branch:** `auto-evolution/long-horizon-saas-operating-system-20260507`  
* **changed files (this sprint slice):**
  - `docs/sprints/LONG_HORIZON_SAAS_OPERATING_SYSTEM_SPRINT.md` (created — SSOT)
  - `services/fiqa_api/deployment_profile.py` (`/obs/ping` + 16 platform routes inventoried; startup banner cites count + SSOT)
  - `tests/test_deployment_profile.py` (new)
  - *(Other modified/untracked paths on this workstation pre-existed branch WIP — not claimed by this sprint slice.)*
* **validations (2026-05-07 run):**

| Gate | Result |
|------|--------|
| compileall (`deployment_profile.py`) | PASS |
| pytest `test_deployment_profile` + `test_pack_validation` | PASS (6) |
| `scripts/guardrail_inbox_triage.sh` | PASS |
| UI `npm run build` | PASS (Node **22.22** on PATH — **Node 20.18 default fails** Vite 7) |
| madge circular (`ui/src`) | PASS (no cycles) |
| `scripts/run_full_regression.py` | PASS (`http_p95_ms` 4790.45, thresholds OK) |

* **simulations performed:** Guardrail tiers = **64** rule scenarios + **69** multi-turn + adversarial + mixed-intent + long-context + case-boundary + simulation assistant + broker stress + handoff timing + cross-client A/B batteries (exact counts in guardrail stdout — **all PASS** this run).  
* **operational reviews completed (documented in SSOT):** Phase 7 deploy/ops tabletop; Phase 8 self-critique; Phase 9 final 20-answer report.  
* **major discoveries:** **`UNIFIED_INTAKE_PRODUCT_ONLY=1` still exposes 18 enumerated inline lab/platform/observability surfaces** (see `deployment_profile.PLATFORM_INLINE_ROUTES_UNGATED_IN_APP_MAIN`; health/version/root not counted) — surfaced at startup for operator honesty. SPA still ships full lab NAV (positioning ≠ API gate).  
* **remaining risks:** Inline route removal needs route-diff regression before gating; Node version drift breaks `npm run build` in naive CI shells; Postgres dual-write parity not exercised here (`skipped_pg_consistency_check`).  
* **recommended next 10× leverage:** **Conditionally mount** (`if not product_only`) the tuple in §`deployment_profile` by refactor-migrating handlers off bare `app` — pair with **OpenAPI snapshot diff** in CI.  
* **FINAL_ONE_LINE:** *Counted and logged every product-only “surface leak,” mapped pilot→SaaS skeleton honestly, and green-lit guardrail + full regression without pretending auth or billing existed.*

*End of SSOT sprint document — iterate only through §0.4 evolution log.*
