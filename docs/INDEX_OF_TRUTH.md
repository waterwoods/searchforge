# Index of Truth — Case Builder / Unified Intake

**Status:** Map each subject to one authoritative document  
**Date:** 2026-08-03  
**Rule:** When documents conflict, the authoritative row wins. Older docs are retained and marked — not deleted.

---

## Authoritative map

| Subject | Authoritative document | Older / related docs |
|---------|------------------------|----------------------|
| Agent entry / reading order | `AGENTS.md` | — |
| Runtime & deploy truth | `docs/CURRENT_PRODUCT_SHAPE.md` | Deploy playbooks under `docs/runbooks/` |
| P20 development law | `docs/product/p20_product_north_star.md` | `docs/product/p20_production_loop_template.md` |
| Case Builder product promise (this week) | `docs/product/CASE_BUILDER_NORTH_STAR_2026-08-03.md` | — |
| Six-day execution backlog | `docs/roadmap/SIX_DAY_PILOT_RELEASE_PLAN_2026-08-03.md` | — |
| Ranked backlog index | `docs/roadmap/CASE_BUILDER_MASTER_BACKLOG.md` | UX defects stay in UX ledger |
| Release labels / P0 gates | `docs/release/PILOT_READY_RELEASE_GATES_V1.md` | `docs/runbooks/RELEASE_CHECKLIST.md` (ops) |
| Codebase capability reality | `docs/reality/CURRENT_CODEBASE_REALITY_2026-08-03.md` | — |
| Founder printable packet | `docs/founder/CASE_BUILDER_SIX_DAY_EXECUTION_PACKET.md` | — |
| Frozen product decisions | `docs/product/decision_log.md` | P0 architecture freezes under `docs/product/p0_*` |
| Founder daily path | `docs/FOUNDER_ONE_PATH.md` | `docs/ANDY_QUICK_START.md` |
| Stage 1 closeout | `docs/evidence/STAGE1_FOUNDER_VALIDATED_CLOSEOUT.md` | Fast Lane evidence folders |
| Stage 2 closeout | `docs/evidence/STAGE2_FOUNDER_VALIDATED_CLOSEOUT.md` | stage2 phone evidence folders |
| Timing metrics closeout | `docs/metrics/REAL_USAGE_TIMING_V1_CLOSEOUT.md` | `CASE_VALUE_METRICS_SEMANTICS.md` |
| LangGraph FDE narrative | `docs/portfolio/FDE_CASE_STUDY_LANGGRAPH_V1.md` | Learning map below |
| Metrics FDE narrative | `docs/portfolio/FDE_CASE_STUDY_METRICS_V1.md` | — |
| FDE module explainability | `docs/portfolio/FDE_SIX_DAY_LEARNING_AND_DEMO_MAP.md` | — |
| UX risk ledger | `docs/product/ux_problem_ledger.md` | smoothness scorecard (supporting) |
| Mini Program architecture freeze | `docs/design/p19m0_unified_claim_mini_program_architecture_v1_2026_07_10.md` | mark: **prototype-era** for target surface; backend reuse still real |
| Paid-pilot commercial goal (historical) | `docs/goals/insurance_paid_pilot_goal.md` | mark: **historical** RAG-era goal; Case Builder NS wins for this week |
| Reduction roadmap | `docs/SIMPLIFICATION_MASTER_PLAN.md` | inventory date may lag; CURRENT_PRODUCT_SHAPE wins for deploy |
| Operator surface | `docs/runbooks/OPERATOR_SURFACE.md` | `OPERATOR_IGNORE_LIST.md` |
| Doc system map | `docs/PROJECT_DOC_SYSTEM_MAP.md` | points here for truth conflicts |

---

## Stale / class marks (do not delete)

| Document / class | Mark | Notes |
|------------------|------|-------|
| `docs/product_constitution/NORTH_STAR_V1.md`, `PROPOSED_NORTH_STAR.md`, P16Z* North Stars | **superseded** | P20 NS + Case Builder NS replace for current work |
| `docs/product_constitution/P16F_CONTEXT.md` and most P16* founder context packs | **historical** | Sprint-era Preview/CORS context |
| `docs/pilot/p19h3g_pilot_readiness_audit_chen_2026_07_10.md` | **historical** | Pre–Stage 1/2 Aug closeouts |
| `docs/trial/P16_*` pilot certification set | **historical** | Pre–Case Builder Stage freezes |
| `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` | **prototype-era** / macro blueprint | Not daily deploy truth |
| `docs/archive/platform/*` Trusted Assistant / OS blueprints | **historical** / investor framing | Dangerous as build list |
| `docs/archive/lab/langsmith_*`, `langgraph_*` | **lab-only** | Not Case Builder PR B |
| `mcp/README.md` + `mcp/*` servers | **lab-only** | Not product_only dependency |
| `docs/goals/insurance_paid_pilot_goal.md` RAG demo framing | **historical** | Superseded commercially by Case Builder NS for this week |
| UX ledger Critical rows still “Open” from July | **partially stale** | Stage phone GOs exist; ledger not fully rewritten — treat Case Builder reality SSOT as capability truth |

---

## Conflict resolution order

1. `docs/reality/CURRENT_CODEBASE_REALITY_2026-08-03.md` — what is actually true in code/evidence  
2. `docs/CURRENT_PRODUCT_SHAPE.md` — what is deployed / env law  
3. `docs/product/CASE_BUILDER_NORTH_STAR_2026-08-03.md` + six-day plan — what we are building this week  
4. `docs/product/p20_product_north_star.md` — how we build (Production Loop)  
5. Everything else — supporting or historical  
