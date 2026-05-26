# THIRTY CUSTOMERS REALITY SIMULATION SPRINT — Single Source of Truth (SSOT)

**Sprint type:** Long-horizon reality simulation + SaaS operating stress (not micro-latency optimization).  
**Question:** What happens when Unified Intake has **30 real paying customers**?  
**Maintainer:** Update this file continuously; it overrides scattered notes for this sprint.

---

## PHASE 0 — GIT + SAFETY (snapshot)

| Item | Value |
|------|--------|
| **Branch** | `auto-evolution/30-customers-reality-simulation-20260507` |
| **Created from** | Prior HEAD on `auto-evolution/long-horizon-saas-operating-system-20260507` |
| **Dirty (modified) at branch cut** | `configs/demo.env.example`, `services/fiqa_api/app_main.py`, `db/service_record_repository.py`, `inbox_triage/active_vehicle_resolver.py`, `case_lifecycle.py`, `case_truth_repository.py`, `session_repository.py`, `session_store.py`, `routes/inbox_triage.py`, `tests/test_case_truth_repository.py`, `tests/test_intake_session_persistence.py`, `ui/src/api/inboxTriage.ts`, `triageResultContract.ts`, `caseLifecycleDisplay.ts`, `intakePure.ts` |
| **Untracked (examples)** | `docs/sprints/*.md` (multiple), `docs/*_MAP.md`, `services/fiqa_api/deployment_profile.py`, `audit_export.py`, `pack_validation.py`, `scripts/run_full_regression.py`, `results/*`, tests for deployment/pack, etc. |
| **Stash** | `stash@{0}` … `stash@{15}` present (see `git stash list`) — **not applied** for this sprint |
| **Safety note** | Multi-tenant auth, Stripe, and true per-org data isolation are **explicitly out of scope** per `AGENTS.md`; simulations below assume **logical** tenants (configured client packs, founder-operated infra) unless noted. |

### Sprint changelog (living)

| Date (UTC) | Change |
|------------|--------|
| 2026-05-07 | Branch created; SSOT initialized; `trial_readiness_check.sh`: `validate_client_pack_layout('chen_kui')`; **Node 22 PATH bootstrap** (nvm) so Vite 7 UI step passes when Cursor Node 20 is default; `deployment_profile` banner SSOT pointer extended. |

---

## PHASE 1 — THIRTY_CUSTOMERS_SYSTEM_REALITY_MAP

### 1.1 Product surface (what customers touch)

| Surface | Implementation anchors | Scales to 30? | Breaks at 30 when… |
|---------|------------------------|---------------|---------------------|
| Unified Intake workbench UI | `ui/src/features/intake/*`, API `routes/inbox_triage.py` | **Partially** — single-tenant mental model | Expectations diverge per office (copy, language, handoff rules) without **per-client packs**. |
| Simulation Assistant / scenarios | `configs/simulation_assistant_scenarios.json`, guardrail scripts | **Yes** for demos | Offices want **custom scenario packs**; support burden to author JSON. |
| “Health” / readiness | `trial_readiness_check.sh`, `trial_launch_check.sh`, guardrail | **Yes** for founder-led trial | **No** self-serve: each customer’s checkout still needs **human** interpretation of failures. |
| Analytics / events | `analytics/minimal_events`, `audit_export` (scaffold) | **Weak** — no BI product | Customers ask “prove ROI”; **aggregates + export** missing → trust gap. |

### 1.2 Operator workflow

| Step | Today | Founder-dependent? |
|------|-------|-------------------|
| Run demo | `run_demo_local.sh` | Ports, env, Node version (Vite 7 / Node 22 notes in prior sprints). |
| Load founder queue | UI | Queue content is repo config — **scales** until offices want their own. |
| Fix wrong vehicle / resolver | `active_vehicle_resolver.py`, case truth | **High** tribal knowledge — resolver authority converged in code but **edge cases** still need engineer. |
| Copy snapshot / log trial | Templates under `docs/trial/` | **Medium** — works if operator reads docs. |

### 1.3 Onboarding workflow

| Stage | Mechanism | Real SaaS? |
|-------|-----------|------------|
| Pack on disk | `configs/clients/<id>/` | **Yes** as filesystem artifact; **Fake SaaS** as “customer self-service upload”. |
| Layout validation | `pack_validation.validate_client_pack_layout` + now **trial readiness** gate for `chen_kui` | **Real** fail-fast; still **no** semantic/schema validator in product UI. |
| Deep pack probe | `scripts/validate_client_pack_minimal.py` | **Operator script** — not in hosted product. |

### 1.4 Deployment workflow

| Concern | State | Notes |
|---------|-------|------|
| Product-only boundary | `UNIFIED_INTAKE_PRODUCT_ONLY`, `deployment_profile.py` | **Honest:** lists `PLATFORM_INLINE_ROUTES_UNGATED_IN_APP_MAIN` — platform routes still on app in product-only mode. |
| Cloud / Docker | `docs/CLOUD_RUN_DEPLOYMENT.md`, compose | **One deployment profile** per env today; 30 customers ⇒ **30× config drift risk** without automation. |
| Rollback | Runbooks, git | **Manual** founder skill — not a product button. |

### 1.5 Support workflow

| Channel | Maturity | At 30 customers |
|---------|----------|-----------------|
| Issue intake | FIX_NOW templates, observation log | **Ad hoc** — becomes **Linear/email soup** without ticket IDs tied to `case_id` / `session_id`. |
| Repro | Replay scripts, scenario runs | **Strong engineer path**; **weak** broker self-repro without export bundle. |
| Escalation | Founder | **Single bottleneck** — see Phase 7. |

### 1.6 Replay workflow

| Capability | Location | Gap |
|------------|----------|-----|
| Deterministic tests | `run_full_regression.py`, guardrail, pytest | **Good** for mainline. |
| Session replay UI for CS | **Missing** | Support asks “what did the model say turn 3?” — only logs/snapshots if captured. |

### 1.7 Billing workflow

| | |
|--|--|
| **State** | Out of scope per `AGENTS.md` (no Stripe). |
| **At 30 paying customers** | **Infeasible without** subscription metadata, usage meters, invoice line items ↔ sessions. |
| **Simulation conclusion** | Biggest “fake SaaS” gap if sales precedes engineering. |

### 1.8 Tenant workflow

| | |
|--|--|
| **Logical tenant** | `client_id` + `X-Org-Id` (HTTP variant) + analytics payload. |
| **DB isolation** | Not productized — **tenant bleed** is a **design failure mode** if one shared DB + weak filters. |

### 1.9 Audit / compliance workflow

| | |
|--|--|
| **audit_export** | Forwards to `track_event` only — docstring says **no compliance claims**. |
| **Customer asks for WORM export** | **Not met** — escalation to founder + manual SQL/JSON hack. |

### 1.10 Incident workflow

| | |
|--|--|
| Detection | Demo checks, broker reports, `embedding_warming` / 503 recovery scripts. |
| Commander | Founder — no on-call rotation in codebase. |
| Comms | Docs + manual — no status page. |

### 1.11 Rollback workflow

| | |
|--|--|
| Artifact | Git revert + redeploy. |
| **Product** | No “rollback pack version” for client configs in UI. |

### 1.12 Founder vs customer success workflow

| | |
|--|--|
| **Founder** | Writes packs, runs trials, triages LLM weirdness, explains deployment honesty. |
| **CS role** | Collapses onto founder until **playbooks + packaged exports + org Admin UI** exist. |

### 1.13 Summary: scales vs breaks vs debt

| **Scales** | **Breaks first** | **Hidden operational debt** | **Hidden product debt** |
|------------|-------------------|------------------------------|-------------------------|
| Guardrail + regression culture | Founder + support bandwidth | Per-customer config drift; Node/env mismatch | No self-serve onboarding; no audit export |
| Strong intake core & resolver direction | Trust when ROI unclear | Replay tooling only for engineers | Analytics story vs implementation |
| Honest deployment_profile banner | Billing / real tenancy expectations | Manual deploy/rollback | “SaaS” narrative ahead of SKU |

---

## PHASE 2 — 30 CUSTOMER SIMULATION

**Method:** 30 distinct customer IDs (C01–C30) grouped by **office archetype**. For each archetype, all **20 workflow dimensions** (onboarding → founder unavailable) are considered; cells summarize **friction**, **support load**, and **assumptions**.

### 2.1 Customer roster (30)

| ID | Archetype | Primary stress |
|----|-----------|----------------|
| C01 | Small broker (2 staff) | Training floor; one person is “power user.” |
| C02 | Small broker + IC | Founder busy; slow ticket response. |
| C03 | Bilingual (EN/ZH) | Copy/pack quality; mixed-language threads. |
| C04 | Bilingual (ES/EN) | Same + **no ES pack** in default product ⇒ friction. |
| C05 | Low-tech office | UI fear; “where did the AI get that?” trust. |
| C06 | Low-tech + paper | Export/print expectations — audit gap. |
| C07 | High-volume intake | Latency + queue discipline; operator mistakes. |
| C08 | High-volume + after-hours | Expectation of 24/7 — support SLA missing. |
| C09 | Messy append-heavy | Thread drift; wrong vehicle; resolver stress. |
| C10 | Multi-operator (3 seats) | Handoff consistency; no SSO/seat billing. |
| C11 | Multi-operator + churn | New hires need training pack version. |
| C12 | Support-heavy | Tickets dominate;.need case_id-linked support. |
| C13 | Support-heavy + escalations | CEO calls founder directly. |
| C14 | Compliance-sensitive | Audit **demand** vs scaffold **supply**. |
| C15 | Compliance + carriers | Evidence format per carrier — not modeled. |
| C16 | Price-sensitive | “What per seat?” — billing gaps exposed. |
| C17 | High-growth (adding producers) | Onboarding N times; pack ops bottleneck. |
| C18 | Multi-location brand | Sub-brands want different handoff_phrases. |
| C19 | Multi-location franchise | **Tenant isolation** concern (even if “out of scope”). |
| C20 | DTC / high digital | API-first expectations; webhooks missing. |
| C21 | Legacy AMS mindset | CSV/import — not product path. |
| C22 | Mixed personal/commercial | Line boundary mistakes in triage — policy gap. |
| C23 | Renewal-heavy office | Date sensitivity; analytics on “time saved” weak. |
| C24 | Subrogation / claims adjacent | Edge intents; playbook not in STANDARD_SCENARIO_PACKAGE. |
| C25 | Founder’s friend pilot | Lenient now; turns demanding after paywall. |
| C26 | Churn-risk after bad turn | Replay + apology workflow — manual. |
| C27 | LLM-skeptical principal | Wants deterministic-only mode — partial product fit. |
| C28 | Over-trusting staff | Operator misuse sends wrong draft — liability fear. |
| C29 | Boutique luxury | White-glove copy; micromanage `ui_copy.json`. |
| C30 | Roll-up acquiring offices | **30 → 100 path**: integration PM needed; product has no tenant admin. |

### 2.2 Universal workflow matrix (dimensions 1–20)

Legend: **H** = high friction/load, **M** = medium, **L** = low (for *majority* of customers in that archetype after first 90 days).

| # | Workflow | Typical friction | Hidden assumption | Product gap |
|---|----------|------------------|-------------------|-------------|
| 1 | Onboarding | M–H | “Founder configures pack” | No self-serve |
| 2 | Deployment | H | Single Cloud Run / one profile truth | Drift across customers |
| 3 | Pack setup | M | JSON + git comfort | No schema UI |
| 4 | Operator training | H | English-first docs | i18n runbooks weak |
| 5 | Add-car | M | California auto rules in prompts | Edge vehicle combos |
| 6 | Append / long thread | H | Resolver + memory correctness | Truth/repair UX for CS |
| 7 | Replay | M–H | Engineer runs scripts | No CS replay UI |
| 8 | Escalation | H | Founder on path | No ticket routing |
| 9 | Support incident | H | “Screenshot + Slack” | No structured intake |
|10 | Deployment rollback | H | Git literate ops | Not productized |
|11 | Broken client pack | M | Caught by **pack_validation** (layout) | Semantic errors slip |
|12 | Wrong vehicle correction | M–H | Operator trusts UI | Needs obvious “repair” |
|13 | Audit export | **H** | Compliance wording | **audit_export** scaffold only |
|14 | Analytics discrepancy | H | “Events = truth” | No SLAs on metrics |
|15 | Billing dispute | **H** | Stripe exists | Out of scope → crisis |
|16 | Operator mistake | M | Training + guardrails | Provenance unclear to user |
|17 | Customer trust | H–H | Human-in-loop promise | Any auto-send fear |
|18 | LLM weirdness | M–H | Model drift | Playbook + flags |
|19 | PG mismatch | M | Tests pass locally | Env parity |
|20 | Founder unavailable | **H** | Bus factor = 1 | No second-line |

---

## PHASE 3 — TOP_50_FAILURE_MODES

**Format:** Id · Name · **Sev** (S/C/M) · **Prob@30** (H/M/L) · Customer / Ops / Trust impact · Mitigation · Automation angle.

### Cluster A — Tenancy & data (1–10)

1. **Tenant bleed** — S · H · Catastrophic / legal · **Mitigation:** org-scoped queries, keys, audits · **Auto:** integration tests per org.
2. **Cross-customer config mix-up** — S · M · Wrong handoff phrases · **Mitigation:** `client_id` validation, pack checksum in responses · **Auto:** CI matrix per client pack.
3. **`X-Org-Id` ignored downstream** — S · L–M · Silent wrong analytics · **Mitigation:** assert org on write paths · **Auto:** contract tests.
4. **Shared DB “soft delete” failures** — S · L · Resurrection of wrong case · **Mitigation:** hard tenancy filters · **Auto:** fuzz tests.
5. **Backup/restore wrong tenant** — S · L · Trust collapse · **Mitigation:** runbooks · **Auto:** restore drills.
6. **Feature flag global toggles experiment LIVE** — C · M · Unexpected behavior · **Mitigation:** per-env flags · **Auto:** flag lint.
7. **Stale embed index serving mixed clients** — C · L · Wrong retrieval · **Mitigation:** namespace per client · **Auto:** health checks.
8. **Org admin impersonation (future)** — S · L · Fraud · **Mitigation:** RBAC design now · **Auto:** audit trail.
9. **Support exports PII to wrong ticket** — S · M · GDPR-style incident · **Mitigation:** export workflow + redaction · **Auto:** watermark exports.
10. **Cron job double-processing** — C · L · Duplicate side effects · **Mitigation:** idempotency keys · **Auto:** job ledger.

### Cluster B — Billing & commercial (11–15)

11. **Invoice ≠ usage** — S · H at real SaaS · **Mitigation:** meter definition · **Auto:** usage pipeline.
12. **Per-seat overages undocumented** — C · M · **Mitigation:** pricing page honesty · **Auto:** seat telemetry.
13. **Trial → paid gap** — C · H · **Mitigation:** launch checklist + contract · **Auto:** billing state machine.
14. **Refund disputes** — C · M · **Mitigation:** support script · **Auto:** link sessions to invoice line.
15. **Tax/VAT neglect** — C · L–M · **Mitigation:** accountant · **Auto:** billing vendor.

### Cluster C — Replay / analytics / drift (16–25)

16. **Replay mismatch** — C · M · “Your export wrong” · **Mitigation:** version git SHA in export · **Auto:** golden replay CI.
17. **Analytics mismatch** — C · H · ROI disputes · **Mitigation:** definitions doc + BigQuery? · **Auto:** daily reconciliation job.
18. **Pack drift** — C · H · Sudden tone change · **Mitigation:** pack semver · **Auto:** diff alerts on deploy.
19. **LLM drift** — C · M · **Mitigation:** eval harness + pinned prompts · **Auto:** scenario battery on every release.
20. **Resolver regression** — C · M · Wrong vehicle · **Mitigation:** guardrail + case truth tests · **Auto:** expanded chaos sessions.
21. **Caching staleness** — C · M · **Mitigation:** TTL + ETag · **Auto:** cache bust tests.
22. **Clock skew on logs** — M · L · **Mitigation:** UTC standard · **Auto:** NTP monitoring.
23. **Truncated logs** — M · M · **Mitigation:** log limits policy · **Auto:** structured logging budget.
24. **Wrong deployment profile** — C · M · Lab routes exposed · **Mitigation:** `deployment_profile` banner + external grep CI · **Auto:** route inventory test.
25. **Feature detection mismatch FE/BE** — C · M · **Mitigation:** contract versioning · **Auto:** OpenAPI snapshots.

### Cluster D — Operations (26–35)

26. **Support overload** — C · **H** · **Mitigation:** tier-1 playbooks · **Auto:** suggested replies from FAQ RAG.
27. **Rollback failure** — S · M · **Mitigation:** blue/green · **Auto:** smoke after promote.
28. **Missing exports** — C · H · **Mitigation:** export worker spec · **Auto:** signed URL pipeline.
29. **Unresolved escalation** — C · H · **Mitigation:** SLA timers · **Auto:** paging integration.
30. **On-call fatigue (founder)** — C · **H** · **Mitigation:** hire ops · **Auto:** sane alerting thresholds.
31. **Dependency outage (LLM vendor)** — C · M · **Mitigation:** degrade mode copy · **Auto:** circuit breaker metrics.
32. **Secrets leak in logs** — S · L · **Mitigation:** redaction · **Auto:** secret scan CI.
33. **DB migration mistake** — S · L · **Mitigation:** expand/contract · **Auto:** migration linter.
34. **Quota exhaustion** — C · M · **Mitigation:** customer comms · **Auto:** quota dashboard.
35. **Customer runs old UI bundle** — C · L · **Mitigation:** version footer · **Auto:** cache headers.

### Cluster E — People & trust (36–45)

36. **Operator misuse** — C · H · Sends wrong draft · **Mitigation:** prominent confirm UI · **Auto:** optional second approver.
37. **Client misunderstanding** — C · H · Expects autopilot · **Mitigation:** onboarding language · **Auto:** in-product disclosure.
38. **Route exposure** — C · M · Attack surface · **Mitigation:** product-only tighten over time · **Auto:** external pen test schedule.
39. **Founder bottleneck** — C · **H** · Everything queues · **Mitigation:** hire + docs · **Auto:** async workflows.
40. **Internal political blocker** — C · M · Broker principal veto · **Mitigation:** champion enablement · **Auto:** N/A.
41. **Bad press / social** — C · L · **Mitigation:** comms template · **Auto:** sentiment monitoring (later).
42. **Latency SLO miss** — C · M · `run_full_regression` cap stress · **Mitigation:** perf budget · **Auto:** p95 dashboard.
43. **Incorrect product narrative sold** — C · H · **Mitigation:** sales cheat sheet grounded in code · **Auto:** “claim ↔ code” matrix in SSOT.
44. **Partner integration broken** — C · M · **Mitigation:** sandbox envs · **Auto:** partner conformance tests.
45. **Legal hold request** — S · L · **Mitigation:** WORM design · **Auto:** legal export job.

### Cluster F — Edge technical (46–50)

46. **PG mismatch in prod** — C · M · **Mitigation:** env parity checklist · **Auto:** schema drift detector.
47. **Unicode / emoji corruption** — M · L · **Mitigation:** encoding tests · **Auto:** corpus fuzz.
48. **Race on session write** — C · L · **Mitigation:** transaction boundaries · **Auto:** stress tests.
49. **Malicious prompt injection (broker pastes email)** — C · M · **Mitigation:** policy layer docs · **Auto:** classifiers (careful scope).
50. **Certificate / TLS expiry** — S · L · **Mitigation:** Infra as code alerts · **Auto:** cert monitor.

---

## PHASE 4 — TOP_30_MISSING_PRODUCT_CAPABILITIES (ranked)

**Columns:** Rank · Capability · SaaS · Ops · Trust · Difficulty · Regression risk · ROI · Notes (del vs simplify vs config vs product-only)

| Rk | Capability | SaaS | Ops | Trust | Diff | Regr | ROI | Notes |
|----|------------|------|-----|-------|------|------|-----|------|
| 1 | True multi-tenant isolation + auth | ●●● | ●●● | ●●● | ●●●●● | ●●●●● | ●●●●● | **Missing** (scope); simulate before selling “enterprise”. |
| 2 | Billing + usage metering | ●●● | ●●● | ●●● | ●●●● | ●●● | ●●●●● | **Missing** — blocks real SaaS economics. |
| 3 | Signed case export (WORM-ready) | ●●● | ●●● | ●●● | ●●●● | ●●● | ●●●● | **Missing** — `audit_export` is honest scaffold. |
| 4 | CS replay UI (turn-level) | ●●● | ●●● | ●●● | ●●● | ●●● | ●●●● | Tier-1 can’t self-serve repro. |
| 5 | Org admin: pack versioning UI | ●●● | ●●● | ●● | ●●●● | ●●● | ●●●● | Replace git ops for CS. |
| 6 | Ticket ↔ `case_id` linking | ●● | ●●● | ●● | ●● | ●● | ●●● | Kill Slack archaeology. |
| 7 | Schema validation for client packs | ●● | ●●● | ●● | ●●● | ●● | ●●● | Extend `pack_validation`. |
| 8 | SLA / status page | ●● | ●●● | ●●● | ●● | ● | ●●● | Trust at scale. |
| 9 | Deterministic “no-LLM” mode SKU | ●● | ●● | ●●● | ●●● | ●●● | ●● | For skeptics — **product** not delete. |
|10 | Second-line support runbooks in-app | ● | ●●● | ●● | ● | ● | ●●● | Reduce founder bottleneck. |
|11 | Seat / SSO | ●●● | ●● | ●● | ●●●● | ●●● | ●●● | Standard mid-market expectation. |
|12 | Per-customer analytics dashboard | ●●● | ●● | ●●● | ●●● | ●● | ●●● | Else “trust gap”. |
|13 | Deployment profile **zero** ungated routes | ●● | ●●● | ●● | ●●● | ●●● | ●●● | Harden `app_main` over time. |
|14 | Automated pack diff on deploy | ● | ●●● | ●● | ●● | ● | ●●● | Ops win. |
|15 | Idempotent webhooks (carrier) | ●● | ●● | ●● | ●●● | ●●● | ●● | Future vertical pressure. |
|16 | Training mode / sandbox tenant | ●● | ●●● | ●● | ●● | ● | ●●● | Onboarding scale. |
|17 | Incident command templates | ● | ●●● | ●●● | ● | ● | ●● | Mostly **docs** — quick ROI. |
|18 | Redaction pipeline for exports | ●● | ●●● | ●●● | ●●● | ●● | ●●● | Legal safety. |
|19 | Mobile-friendly operator UI | ●● | ● | ●● | ●●● | ●●● | ●● | Some offices phone-first. |
|20 | Formal RBAC | ●●● | ●● | ●●● | ●●●● | ●●●● | ●●● | With multi-seat. |
|21 | Customer-visible changelog | ● | ● | ●●● | ● | ● | ●● | Cheap trust. |
|22 | Locale packs beyond ZH | ●● | ● | ●● | ●● | ● | ●● | ES etc. |
|23 | Programmatic “health” API for IT | ●● | ●● | ●● | ●● | ● | ●● | MSP customers. |
|24 | Backup verification job | ● | ●●● | ●●● | ●● | ● | ●●● | Ops — not glamorous. |
|25 | Cost caps / LLM budget alerts | ●● | ●●● | ● | ●● | ● | ●● | Protect margin. |
|26 | **Delete:** unused lab endpoints in prod SKU | ● | ●● | ● | ●● | ●●● | ●● | **Simplify** sellable surface. |
|27 | **Simplify:** one “golden” deployment doc | ● | ●●● | ● | ● | ● | ●●● | Reduce tribal knowledge. |
|28 | **Configurable:** feature flags per org | ●● | ●● | ● | ●●● | ●● | ●● | |
|29 | Product-only **honesty** in sales deck | ●●● | ● | ●●● | ● | ● | ●●●● | **Not code** — leverage. |
|30 | Hiring field CS + pay for playbook time | ●●● | ●●● | ●●● | ● | ● | ●●●● | Organizational “capability”. |

**Actually missing vs feels missing:** Billing, tenancy, audit export are **actually missing**. “Faster 200ms” **feels** urgent but is **lower ROI** vs support/export at 30 customers. **Delete/simplify:** platform routes in product SKU over time; consolidate deployment docs. **Configurable:** per-org flags and pack semver.

---

## PHASE 5 — IMPLEMENTATION (this sprint batch)

**Allowed scope respected:** No speculative AI rewrites; no giant refactors.

| Change | Rationale |
|--------|-----------|
| `scripts/trial_readiness_check.sh` | Fail-fast **chen_kui** pack layout; **prefer `~/.nvm/.../v22.x/bin` on PATH** before UI build (`SKIP_NVM_NODE22_FOR_UI=1` to disable). Removes **false FAIL** on machines where default `node` is 20.x. |
| `services/fiqa_api/deployment_profile.py` | SSOT pointer to this sprint doc in product-only warning banner — **deployment honesty continuity**. |

**Deferred (high value, higher risk):** removing `PLATFORM_INLINE_ROUTES_UNGATED_IN_APP_MAIN`, full `audit_export` worker, Stripe.

---

## PHASE 6 — MULTI-ROUND VALIDATION

**Commands (authoritative for this sprint closeout):**

| Step | Command | Result (2026-05-07) |
|------|---------|----------------------|
| compileall | `python3 -m compileall -q services/fiqa_api` | **PASS** |
| pytest (targeted) | `PYTHONPATH=. pytest tests/test_pack_validation.py tests/test_deployment_profile.py -q` | **PASS** (6 tests) |
| trial readiness | `bash scripts/trial_readiness_check.sh` | **PASS** (includes new pack gate + UI build with Node 22 bootstrap) |
| guardrail (standalone) | `bash scripts/guardrail_inbox_triage.sh` | **PASS** (included above) |
| UI build | `cd ui && npm run build` with Node **22.22** on `PATH` | **PASS** |
| madge | `cd ui && npx --yes madge --circular --extensions ts,tsx src` | **PASS** (no cycles) |
| full regression | `PYTHONPATH=. python3 scripts/run_full_regression.py` | **PASS** — `http_p95_ms` **4699.97** (< 6000); `wrong_vehicle_related` **0**; `pg_mismatch_turns` **0**; pass_rate **100%** |

**Simulations performed (desk checklist):**

- [x] Onboarding: incomplete `chen_kui` pack caught by readiness check (design intent verified by code path).
- [x] Deployment: product-only ungated route list reviewed (from `deployment_profile.py`).
- [x] Support: 30-archetype roster + failure-mode clustering (this doc).
- [x] Rollback: manual git-centric (no product change).
- [x] Billing: explicit “out of scope” crisis in simulation — recorded in Phase 4.

---

## PHASE 7 — OPERATOR / SUPPORT / CEO REVIEW (condensed answers)

| Role | Top insight |
|------|-------------|
| Operator | Training + wrong-vehicle repair UX dominate day-to-day pain at 30 offices. |
| Support | Need **case-linked** tickets + replay — Slack screenshots don’t scale. |
| Onboarding | Pack layout gate helps; **semantic** pack authoring still founder-led. |
| Deployment | Profile honesty is good brand; **ungated routes** are a long-tail risk. |
| Replay | Engineering-strong; **customer-facing** replay absent. |
| Billing | **Blocker** for “paying customers” narrative without new systems. |
| Customer success | Playbooks exist as docs, not in-product **workflows**. |
| CEO | **Moat** is workflow + trust + CA insurance domain coupling — **not** raw model accuracy; **scale** limited by founder bus factor and missing tenant/billing. |

**Scale questions**

| | At 30 | At 100 |
|--|-------|--------|
| **What breaks** | Support + onboarding throughput; trust on ROI metrics | Tenancy, billing, hire pipeline — **company** breaks before **code** |
| **Founder overload** | Every escalation + pack edit | Sales + CS + incidents collapse |
| **Trust collapse** | Overpromised “audit” / autopilot | Data bleed or invoice disputes |
| **Onboarding scale** | Manual JSON packs | Must have admin UI + validation |
| **Hiring operators** | Docs suffice for 5–10; messy beyond | Need certification + sandbox |

---

## PHASE 8 — SELF_CRITIQUE_REPORT_V2

| Claim | Critique |
|-------|----------|
| **Fake SaaS** | No auth, Stripe, or per-org product admin — **pilot SaaS** at best. |
| **Hidden monolith** | Unified FastAPI app + inline routes — operationally **one blast radius**. |
| **Founder-only ops** | Deploy, rollback, ambiguous triage → still **you**. |
| **Fake tenancy** | `client_id` + headers ≠ **database-enforced isolation**. |
| **Fake onboarding** | Validation is **files exist**, not “broker can self-integrate.” |
| **Fake supportability** | No CS tooling; engineer replay ≠ CS replay. |
| **Fake deployment safety** | Honest banners ≠ automated safe rollout/rollback product. |
| **Fake replay guarantees** | Tests + chaos **sample** behavior, not legal guarantees. |
| **Fake audit** | `audit_export` explicitly **not** compliance. |

**Biggest illusions:** “We’re a SaaS platform” (vs **sellable vertical workflow product** in pilot clothing).  
**Biggest hidden operational debt:** Per-customer config + env drift without automation.  
**Biggest hidden support risk:** unstructured channels at `case_id` volume.  
**Biggest scaling blocker:** **Commercial + identity layer** absent.

---

## PHASE 9 — THIRTY_CUSTOMERS_REALITY_FINAL_REPORT

1. **What this company REALLY is:** A **CA broker Unified Intake** product — structured triage, human-in-loop drafts, domain-scenario maturity — wrapped in **founder-operated** infra.  
2. **What its moat REALLY is:** **Domain workflow + trust design + regression culture**, not generic LLM chat.  
3. **Breaks first @30 customers:** **Support + onboarding** (people/process), then metrics trust.  
4. **Breaks first @100:** **Tenancy + billing + hiring** — company systems, not the triage loop.  
5. **Biggest support blocker:** No **ticket ↔ case** + replay for CS.  
6. **Biggest onboarding blocker:** **Semantic** pack authoring + self-serve admin.  
7. **Biggest deployment blocker:** **Single-founder** ops + ungated platform routes in product-only mode.  
8. **Biggest trust blocker:** **Audit/ROI** promises vs implementation honesty.  
9. **Biggest operator blocker:** **Wrong vehicle / thread repair** clarity at high volume.  
10. **Biggest billing blocker:** **No billing subsystem** — debt if “paying” customers precede build.  
11. **Biggest replay blocker:** **CS-facing** replay/export missing.  
12. **Biggest founder bottleneck:** **Escalations + pack + infra** funnel to one person.  
13. **Best simplification:** **Tighten sellable API surface** (reduce ungated routes over time).  
14. **Best automation:** **Pack validation + CI matrix** across N reference clients.  
15. **Best SaaS move:** **Org admin + schema-valid packs** before Stripe.  
16. **Best onboarding move:** **Sandbox tenant + training checklist** wired to readiness scripts.  
17. **Best deployment move:** **Route inventory test in CI** matching `deployment_profile`.  
18. **Best trust move:** **Customer-visible versioning** (git SHA / contract version in UI footer + exports).  
19. **Best monetization move:** Price **per producer seat** with **usage caps** once metering exists.  
20. **Best next 10× leverage:** **Signed case export + org-scoped data model** (even before full fancy UI).

---

## FINAL SPRINT OUTPUT (rolling closeout)

*Update after each validation batch.*

| Field | Value |
|-------|--------|
| **Branch** | `auto-evolution/30-customers-reality-simulation-20260507` |
| **Changed files (this batch)** | `docs/sprints/THIRTY_CUSTOMERS_REALITY_SIMULATION_SPRINT.md` (new), `scripts/trial_readiness_check.sh`, `services/fiqa_api/deployment_profile.py` |
| **Validations** | compileall PASS; pytest targeted PASS (6); trial_readiness PASS; UI build + madge PASS (Node 22); full_regression PASS (`http_p95_ms` ~4700) |
| **Simulations performed** | 30-customer archetype roster; workflow matrix; failure clustering; multi-role review |
| **Failure modes discovered** | TOP_50 list §PHASE 3 |
| **Productization gaps** | TOP_30 §PHASE 4 |
| **Operational reviews** | §PHASE 7 |
| **Major discoveries** | Scale is **organizational + commercial** before raw code throughput; “honest scaffolding” (`audit_export`, deployment banner) is **correct** and must be **sold accurately** |
| **Remaining risks** | Tenant bleed, billing absence, founder bus factor, CS tooling gap |
| **Recommended next 10× leverage** | Signed export + org-scoped persistence model |
| **FINAL_ONE_LINE** | **At thirty real customers, this system breaks first in support and onboarding—not in the triage loop—unless tenancy, billing, and case-level operator tooling catch up to the product story.** |
