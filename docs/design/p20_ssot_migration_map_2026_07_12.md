# P20 SSOT Migration Map — P16 / P18 / P19 → P20

> Companion to `docs/design/p20_production_constitution_master_design_2026_07_12.md`.
> Purpose: classify each major older SSOT and record what P20 **inherits**, **upgrades**, **supersedes**, keeps as **historical-only**, and its **current authority**. Older documents are **not deleted or rewritten** — they remain evidence and specialized references.

**Date:** 2026-07-12 · **Status:** RATIFIED (with the Constitution) · **Branch:** `sprint/p16-trust-layer`

---

## 1. Authority classification legend

| Status | Meaning |
|--------|---------|
| **AUTHORITATIVE & CURRENT** | Still governs its domain; P20 defers to it. |
| **CURRENT BUT NARROW** | Correct within a specific module/topic; not cross-cutting. |
| **INHERITED** | Principles carried forward into P20 verbatim or lightly upgraded. |
| **SUPERSEDED** | Replaced by P20 or a later P19 doc; kept as history. |
| **HISTORICAL REFERENCE** | Useful record of how/why; not current truth. |
| **STALE / CONTRADICTORY** | Contains statements no longer true; must be annotated. |

Classification uses document content **plus** implementation evidence, commit history, and current product decisions — not filename dates alone.

---

## 2. Source-authority table (cross-phase)

| Document | Original purpose | Current relevance | Authority status | Principles to inherit | Statements to supersede | Conflicts resolved by P20 |
|----------|------------------|-------------------|------------------|-----------------------|-------------------------|---------------------------|
| `docs/design/p20_production_skeleton_repository_audit_2026_07_12.md` | Code-reality production audit | Input truth for skeleton | **AUTHORITATIVE & CURRENT** (code reality) | Reuse %, R1–R12 risks, 10 skeleton components, 3 tracks | — | — |
| `docs/CURRENT_PRODUCT_SHAPE.md` | Runtime/deploy truth | Runtime SSOT | **AUTHORITATIVE & CURRENT** (runtime) | PG-primary posture, product-only flags, env gates | — | Runtime posture wins vs sprint docs |
| `docs/CASE_CONTRACT_V1.md` | Case data model | Case-truth model | **AUTHORITATIVE & CURRENT** (data) → **INHERITED** into §6/§14 | authoritative vs derived fields, provenance, append boundary, PG-primary | none critical | Feeds Customer Task Contract §6 |
| `docs/design/p19m0_unified_claim_mini_program_architecture_v1_2026_07_10.md` | MP target architecture | Frontend architecture | **AUTHORITATIVE & CURRENT** (MP) → **INHERITED** | MP-sole-surface, North Star, 3 Locks, adapter isolation, journey | none | H5-first (A) resolved: MP primary |
| `docs/design/p19m0_h5_to_mini_program_mapping_2026_07_10.md` | H5→MP capability map | Reuse map | **CURRENT BUT NARROW** → **INHERITED** | direct backend reuse, "map semantics not pixels" | "H5 as primary" residue | Reuse without rewrite (§4.17) |
| `docs/evidence/p19m_phase1_final_e2e_acceptance_2026_07_11.md` | Prototype acceptance | Validated behavior | **AUTHORITATIVE & CURRENT** (prototype verdict) | 181 tests green, CONDITIONAL GO loop, Cloud SQL SSOT | — | Prototype validity anchor (§28) |
| `docs/evidence/p19m2a_automated_e2e_readiness_audit_2026_07_11.md` | E2E readiness audit | Partly valid evidence | **HISTORICAL / VALID (E2E, idempotency, Workbench evidence)** · **STALE only for Neon / `--cloudrun-parity` routing conclusions** | E2E flow, idempotency, and Workbench readback evidence where still supported | old Neon / `--cloudrun-parity` routing conclusions (e.g. `run_demo_local.sh` uses Neon — predates same-day decommission) | **Do not classify the whole document as stale** — only its Neon/routing conclusions are stale (per P20 audit §1) |
| `docs/design/p19h3h_master_design_summary_2026_07_10.md` | H5-era master design | Principle source | **SUPERSEDED (frontend)** / **INHERITED (principles)** | §1b Structured-Task-First, §1c Production-grade, §1d Append-first Split-later, smooth-UX locks | "H5 Task Page is the primary structured intake"; "why not mini program now" | H5-first (A), Prototype-vs-Prod (B) |
| `docs/design/p19h3h_product_architecture_wecom_h5_workbench_2026_07_10.md` | H5+WeCom+Workbench architecture | History | **SUPERSEDED (frontend)** | channel-agnostic backend, workbench readback | H5 primary customer surface | A |
| `docs/design/p19h3h_claim_h5_task_state_machine_2026_07_10.md` | Claim 9-step spec | State machine ref | **CURRENT BUT NARROW** → **INHERITED** | claim steps/gates semantics | H5-specific UI | D (timeline vs state) |
| `docs/design/p19h3h_smooth_ux_idempotency_async_design_2026_07_10.md` | Idempotency/async design | Reliability ref | **CURRENT BUT NARROW** → **INHERITED** | submit intent UUID, photo hash dedup, disabled/loading | — | Reliability (§13) |
| `docs/design/p19h3h_evidence_chain_broker_review_design_2026_07_10.md` | Timeline/evidence/workbench | Evidence ref | **CURRENT BUT NARROW** → **INHERITED** | timeline source tags, workbench visibility | — | Event/Evidence (§8/§9) |
| `docs/design/p19h3i_claim_task_dashboard_always_return_h5_2026_07_10.md` | Dashboard + always-return H5 | History | **SUPERSEDED (H5 return)** | dashboard_summary → Task Home | "always return H5" as customer model | A |
| `docs/design/p19h3j_h5_wecom_channel_ux_policy_2026_07_10.md` | H5/WeCom channel UX policy | History | **SUPERSEDED (channel)** | WeCom = notify/light-confirm; forbidden chat-wizard | H5 dual-input primary | A |
| `docs/p19e3_channel_strategy_wecom_h5_miniprogram_recon.md` | Channel strategy recon (2026-07-06) | History | **SUPERSEDED** | channel responsibilities table, "Progress Card before App Home", "MP = port not rewrite" | "**NO mini program now**", "MP is V2", Spark % roadmap | A (Founder later chose MP-sole) |
| `docs/p19h_state_machine_temporal_audit_2026_07_10.md` | State machine / Temporal audit | Workflow-engine ref | **CURRENT BUT NARROW** → **INHERITED** | do not introduce Temporal now | — | G (workflow engine) |
| `docs/p19i*_workflow_kernel_*` | Generic workflow kernel recon | Kernel ref | **CURRENT BUT NARROW** → **INHERITED** | kernel as slot/gate SSOT | — | G |
| `docs/product_constitution/NORTH_STAR_V1.md` | Broker SaaS north star (P14-B) | Commercial north star | **HISTORICAL REFERENCE** / partial **INHERITED** | advisory-only, no auto-send, anti-goals (Stripe/multi-tenant now/OCR-first) | "broker paste is the product"; RAG `/demo` | C (case vs task), non-goals |
| `docs/product_constitution/P16_CUSTOMER_FIRST_CONSTITUTION.md` | Customer-first add-car rules | Principle source | **INHERITED (rules)** / **SUPERSEDED only for the Add-Car-only scope** | Eight Rules (login-less, phone-return, progress=missing, broker-closes, one-active, one-flow), role timing goals; **AND the inherited boundary that the platform is NOT a carrier claim system** | Only the **Add-Car-only scope** is superseded/expanded (Claim Intake is now the first vertical) | C; scope now = Insurance Task Platform. **"Superseded" applies ONLY to the Add-Car-only product scope — it is NOT permission to become a carrier claim system** (see §3 for the fully-inherited non-carrier boundary). |
| `docs/product_constitution/P16Z18_AI_BOUNDARY.md` | AI boundary (Z18) | AI boundary source | **INHERITED** | AI may draft/merge/suggest; humans confirm/execute; never auto-send/quote/coverage | LLM-off framing (still valid direction) | E (AI vs rules) |
| `docs/product_constitution/P16Z18_NEVER_BUILD.md` | Never-build list | Anti-scope | **INHERITED (pattern)** | "wire, don't rebuild"; no new service/platform | "WeChat bot / official integration = never build" (now WeCom/MP is the strategy) | Reuse (§4.17); note MP is now in-scope |
| `docs/product_constitution/CONTRACT_SIMPLICITY_AMENDMENTS.md` | UI simplicity amendments | UX ref | **INHERITED** | One Primary CTA (S11); ≤3 focal points | — | §4.8, §5 |
| `docs/goals/insurance_paid_pilot_goal.md` | Paid pilot goal (RAG era) | — | **STALE / CONTRADICTORY** | pilot discipline framing | RAG `/demo` as product; Qdrant-centric | C; superseded by Unified Intake + MP |
| `docs/CASE_CONTRACT_V1.md` MIGRATION_RULES | JSON→PG rules | — | **INHERITED** | PG-primary; JSON deprecated as SSOT | JSON-as-SSOT residue | §14 |
| `docs/wecom_q0_cloud_sql_migration_plan.md` | Cloud SQL migration plan | History | **HISTORICAL REFERENCE** | migration rationale | "plan only — do not execute" (executed); Neon rollback via Secret v2 (disabled) | §14 (Neon decommissioned) |
| `docs/wecom_q0_db_stability_decision.md` | Neon instability root-cause | History | **HISTORICAL REFERENCE** | pooling/connection lessons | "Neon is production DB" | §14 |
| `docs/evidence/legacy_db_decommission_audit_2026_07_11.md` | Neon decommission audit | DB truth | **AUTHORITATIVE & CURRENT** (DB) → **INHERITED** | Cloud SQL SSOT; Neon deleted; break-glass read-only | §11 checklist unchecked (superseded by §12–13 complete) | §14 |
| `docs/p18_9_conservative_ai_red_team_risk_review.md` | AI red-team safety rules | Trust boundary source | **INHERITED** | Ten Product Safety Rules §15; four-layer data model; forbidden phrasing; high-risk→manual | P18.8 "not wired" gaps (re-audit) | E, §10, §12 |
| `docs/p18_11_environment_strategy_and_dev_rules.md` | Environment strategy | Env ref | **INHERITED** | local=dev-only, QA=acceptance, PG=truth, per-loop declaration | hardcoded URLs/revs as examples | §18 |
| `docs/p18_7_end_to_end_business_flow_simulation.md` | Chen Kui E2E business flow | Business ref | **HISTORICAL REFERENCE** / **INHERITED** | broker 10s, one-flow, confirm-before-done | add-car-centric stories | C, §2 |

---

## 3. Explicit supersession statements (required by mission)

| Item | Status | Where it lived | P20 ruling |
|------|--------|----------------|------------|
| **H5-first architecture** | **SUPERSEDED** | `p19h3h_*`, `p19h3i`, `p19h3j` | Native Mini Program is the sole formal customer task surface; H5 = fallback/QA/reference. |
| **H5 + WeCom dual-input** | **SUPERSEDED** | `p19h3j`, `p19e3` | Structured intake happens in the Mini Program; WeCom = entry/notify/reminder/comms; no parallel chat wizard. |
| **"No mini program now / MP is V2"** | **SUPERSEDED** | `p19e3` §1, §9–10 | Founder decision (P19M-0, D1) makes MP the target and current surface. |
| **Neon runtime statements** | **HISTORICAL / STALE** | `wecom_q0_*`, `p19m2a` | Neon decommissioned 2026-07-11; Cloud SQL sole SSOT. Do not reintroduce. |
| **`run_demo_local.sh` uses Neon / `--cloudrun-parity` routing conclusions (p19m2a)** | **STALE (only these conclusions)** | `p19m2a_automated_e2e_readiness_audit` | These specific Neon/routing conclusions predate the same-day decommission fix and are stale. The rest of P19M-2A (E2E, idempotency, Workbench readback evidence) remains **historical/valid**; do not classify the whole document as stale. |
| **Mini Program prototype architecture** | **INHERITED** | `p19m0_unified_claim_mini_program_architecture_v1` | Carried forward as the frontend architecture foundation. |
| **Append-first, Split-later** | **INHERITED** | `p19h3h` §1d | Frozen product principle §4.9. |
| **Structured Task First; Production-grade, not AI demo** | **INHERITED** | `p19h3h` §1b/§1c | Frozen principles §4.2, §4.19. |
| **Cloud SQL SSOT** | **INHERITED** | decommission audit, `CURRENT_PRODUCT_SHAPE` | Frozen §14. |
| **Unverified WeChat publication claims** | **UNRESOLVED — Gate C** | `p19m0` Lock 2, final acceptance | OFFICIAL VALIDATION REQUIRED; never asserted as fact. |
| **P16 "not a claim system" / add-car-only scope** | **SUPERSEDED/EXPANDED (Add-Car-only scope ONLY)** · **BOUNDARY FULLY INHERITED (not a carrier system)** | `P16_CUSTOMER_FIRST_CONSTITUTION` | The **Add-Car-only scope is superseded/expanded** — Claim Intake is now the first vertical of the Insurance Task Platform, and customer-first *rules* remain inherited. **The boundary remains fully inherited that the platform is NOT: a carrier claim system, formal carrier filing, coverage adjudication, a liability/fault decision, or a carrier replacement.** ⚠ Future Agents must NOT read "superseded" as permission to build a carrier claim system. |
| **"WeChat bot / official integration = never build"** | **SUPERSEDED (scope)** | `P16Z18_NEVER_BUILD` #19 | WeCom cards + Mini Program are the deliberate current strategy; the never-build *pattern* (no new service/platform rewrite) still holds. |
| **RAG `/demo` as paid product** | **SUPERSEDED** | `insurance_paid_pilot_goal` | Product = Unified Intake / Insurance Task Platform. |

---

## 4. Reconciliation of major conflicts (A–H)

| # | Conflict | P20 resolution |
|---|----------|----------------|
| **A** | H5 vs Native Mini Program | Mini Program = formal customer task surface; WeCom = entry/comms/reminders; H5 = fallback/QA/reference; dual-input is **not** the target. |
| **B** | Prototype vs Production | Validated prototype capabilities are reusable; the production skeleton adds reliability, contracts, tenant boundary, observability, auth, reusable UI. Production-first ≠ build every future feature; pilot-sized implementation must still follow durable boundaries. |
| **C** | Case vs Task | Customers experience **Tasks**; internals manage **Cases, Evidence, Timeline, Workflow**. Task identity ≠ case identity. "Everything becomes a Task" = the *customer interaction pattern* is task-oriented, **not** one DB table named `task`. |
| **D** | Timeline vs Current State | The backend **state machine maintains the authoritative current workflow projection** over persisted facts and transitions; the **Timeline is the append-only historical audit**. Current state may be validated/reconstructed from facts/events where appropriate, but full-history replay is **not** required per request. The timeline is **not** the sole current-state store, and current state does **not** exist independently of the historical audit; summaries remain derived. |
| **E** | AI vs Rules | AI may extract/classify/prefill/detect-missing/detect-contradiction/summarize/recommend/brief with confidence+provenance. AI may **not** decide phase, submit, set broker_done, decide liability/coverage, overwrite confirmed facts silently, or file to a carrier. |
| **F** | Multi-tenant timing | One codebase; tenant boundary designed now; full tenant admin UI deferred; authoritative isolation mandatory before the second broker; `tenant_id` server-derived, never from a spoofable client header. |
| **G** | Workflow engine | Current state machine remains; Temporal/Camunda **not** introduced now; a future execution engine only when operational complexity justifies it; Task Contract, Case State, Evidence, Timeline, business rules stay product-owned. |
| **H** | Frontend framework | Native Mini Program remains; WeChat native components first; TDesign selectively for commodity UI; no whole-app framework rewrite; Task UI Kit is product-specific and stays ours. |

---

## 5. Where each future Agent should look

| Need | Primary SSOT | Secondary |
|------|--------------|-----------|
| Product principles / governance | **P20 Constitution** | this migration map |
| Code reality / risks | P20 audit | git history |
| Runtime/deploy posture | `CURRENT_PRODUCT_SHAPE.md` | runbooks |
| Case data model | `CASE_CONTRACT_V1.md` | schema SQL |
| MP architecture | `p19m0_unified_claim_mini_program_architecture_v1` | h5→MP mapping |
| Reliability patterns | `p19h3h_smooth_ux_idempotency_async_design` | audit §11 |
| AI safety | `p18_9_conservative_ai_red_team_risk_review` §15 | `P16Z18_AI_BOUNDARY` |
| DB truth | `legacy_db_decommission_audit_2026_07_11` | env strategy |

---

*P20 SSOT Migration Map — RATIFIED (with the P20 Constitution, 2026-07-12). No documents deleted or rewritten. Classifications may be refined by future versioned amendment.*
