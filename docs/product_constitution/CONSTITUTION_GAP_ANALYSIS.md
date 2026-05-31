# Constitution Gap Analysis — P14-A

**Date:** 2026-05-31  
**Question:** What exists, what to reuse, rewrite, create, archive, and elevate to SSOT?

---

## 1. What Already Exists?

### Strong (reuse verbatim or with minor cross-links)

| Asset | Location | Constitution role |
|-------|----------|-------------------|
| Runtime/deploy truth | `CURRENT_PRODUCT_SHAPE.md` | Unchanged SSOT for ops |
| Customer product truth | `P11/CURRENT_PRODUCT_TRUTH.md` | Seed for constitution § Product |
| Broker sales | `BROKER_ONE_PAGER.md` | Broker-facing extract |
| Founder ops path | `FOUNDER_ONE_PATH.md` | Operational appendix |
| Trial process | `TRIAL_ONE_PATH.md` | Trial model appendix |
| Output standards | `standards/BROKER_INBOX_TRIAGE_STANDARD.md` | Capability 2–3 spec |
| Workbench standards | `standards/UNIFIED_INTAKE_MVP_STANDARD.md` | Capability 4 spec |
| MVP I/O model | `goals/UNIFIED_INTAKE_MVP_MASTER_GOAL.md` | Capability definitions |
| Payment/trial evidence | P10/P11 sprint audits | Evidence base for gaps |
| Customer journey | `P9_BROKER_SURFACE_PLAN.md` | Persona + outcomes |
| Reduction philosophy | `SIMPLIFICATION_MASTER_PLAN.md` | Anti-goals + scope |
| Doc hierarchy | `PROJECT_DOC_SYSTEM_MAP.md` | Navigation |

**Estimate:** ~70% of v1 constitution content already written across these files.

---

## 2. What Can Be Reused?

| Source doc | Reuse as |
|------------|----------|
| CURRENT_PRODUCT_TRUTH §1–5 | Constitution "Product Truth" section |
| P11 FINAL_VERDICT + WHAT_NOT_TO_DO | Anti-goals + 90-day rules |
| P10/P11 TOP_10_HIGHEST_ROI_ACTIONS | 14-day build list |
| CONFLICT_REPORT resolutions | Explicit constitution overrides |
| PROPOSED_NORTH_STAR | North Star section |
| PROPOSED_CAPABILITY_MAP | 7-capability model |
| CUSTOMER_LANGUAGE_GUIDE | Product rules vocabulary |
| STANDARD_SCENARIO_PACKAGE §4 | Scenario tier definitions |
| trial/ templates | Trial ROI instrumentation |

**Do not rewrite from scratch:** Core promise, anti-goals, deployment requirements, 6-field output model, 7-day trial structure.

---

## 3. What Must Be Rewritten?

| Document | Problem | Rewrite action |
|----------|---------|----------------|
| `goals/insurance_paid_pilot_goal.md` | Describes RAG demo, not workbench | Replace with pointer to constitution OR rewrite scope to Unified Intake |
| `business_rules/insurance_broker_pilot_rules.md` | R1–R5 are retrieval rules | Rewrite for triage + workbench rules OR mark deprecated |
| `UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` §2–3 | Add-Car-first GTM conflicts P11 | Add banner: "GTM wedge subordinate to product constitution" |
| `BROKER_TRIAL_PLAYBOOK.md` | Simulation Assistant dependency | Remove SIM requirement; use inline scenarios |
| `TRIAL_ONE_PATH.md` Day 0–1 | References hidden Simulation | Align with workbench-only path |
| `BROKER_ONE_PAGER.md` | Missing pricing; 5 vs 7 scenarios | Add $49/$99; clarify scenario tiers |
| `P9_BROKER_SURFACE_PLAN.md` §9 | SIM1–SIM3 in ideal trial | Update to scenario names |

**Priority:** insurance_paid_pilot_goal + business_rules (misleading for agents).

---

## 4. What Must Be Created?

| New asset | Purpose | Status |
|-----------|---------|--------|
| `UNIFIED_INTAKE_V1_CONSTITUTION_PROPOSAL.md` | Single product constitution SSOT | **This sprint** |
| `product_constitution/INDEX.md` | Entry point for constitution pack | Recommended |
| Pilot terms 1-pager (Chinese) | Blocker #9 in P11 | **Missing from repo** |
| Invoice template | Blocker #8 | **Missing from repo** |
| ROI observation field spec | "Minutes saved" standard field | Extend TRIAL_OBSERVATION_LOG_TEMPLATE |
| Broker UX launch checklist | Second gate beyond trial_launch_check | Extract from P10/P11 UI fixes |
| Constitution amendment process | Anti-drift | Light section in constitution |

**Not invented in this sprint (gap noted):** Legal terms, invoice PDF, UI fixes (implementation sprint).

---

## 5. What Should Be Archived?

Already archived (keep archived):

- `docs/archive/p9_broker_surface/**` — 40+ pre-P9 broker/trial specs
- `docs/archive/platform/**` — platform blueprints
- `docs/archive/sprints/**` — historical execution

**Additional archive candidates (do not delete — banner + pointer):**

| Path | Reason |
|------|--------|
| `docs/pre_trial_review/` | Superseded by trial_launch_check + TRIAL_ONE_PATH |
| `docs/goals/BROKER_ASSISTANT_MASTER_GOAL.md` | RAG era; superseded by UNIFIED_INTAKE_MVP |
| Duplicate 30-day plans | Merge P10 + P11 into one post-constitution plan |

**Do NOT archive (still active):**

- P10/P11 sprint folders — discovery evidence until constitution merged
- MASTER_OUTLINE — macro reference with subordination banner

---

## 6. What Should Become SSOT?

### Proposed SSOT Stack (Post P14-A)

```
┌─────────────────────────────────────────────────────────┐
│  UNIFIED_INTAKE_V1_CONSTITUTION (NEW — product truth)   │
├─────────────────────────────────────────────────────────┤
│  CURRENT_PRODUCT_SHAPE (runtime/deploy — unchanged)     │
├─────────────────────────────────────────────────────────┤
│  FOUNDER_ONE_PATH │ BROKER_ONE_PAGER │ TRIAL_ONE_PATH    │
│  (operational extracts — link up, don't duplicate)      │
└─────────────────────────────────────────────────────────┘
```

| Domain | SSOT | Subordinate docs |
|--------|------|------------------|
| **Product constitution** | `UNIFIED_INTAKE_V1_CONSTITUTION_PROPOSAL.md` | Master outline, sprint audits |
| **Runtime** | `CURRENT_PRODUCT_SHAPE.md` | DEPLOYMENT_READINESS, env example |
| **Broker customer** | `BROKER_ONE_PAGER.md` | CURRENT_PRODUCT_TRUTH (merge or redirect) |
| **Founder ops** | `FOUNDER_ONE_PATH.md` | OPERATOR_SURFACE |
| **Trial** | `TRIAL_ONE_PATH.md` | BROKER_TRIAL_PLAYBOOK |
| **Engineering quality** | standards/ + guardrails | MVP goals |
| **Reduction** | SIMPLIFICATION_MASTER_PLAN | P8/P9 audits |

**Update PROJECT_DOC_SYSTEM_MAP.md** START HERE table to add constitution as item #2 for founders (product truth before runtime for sales conversations).

---

## 7. Gap Severity Summary

| Gap | Severity | Owner |
|-----|----------|-------|
| No single constitution file | **High** | P14-A (done) |
| Stale RAG goal docs | **High** | Rewrite sprint |
| Add-Car vs cancellation GTM | **High** | Constitution resolves |
| UI default tab | **High** | Implementation (not P14-A) |
| Pricing/terms missing | **Medium** | Founder commercial |
| ROI measurement template | **Medium** | Trial template update |
| P12/P13 absent | **Low** | N/A — use P10/P11 |
| Scenario count drift | **Low** | Constitution clarifies tiers |

---

## 8. Reuse vs Create Decision Matrix

| Need | Reuse | Create | Rewrite |
|------|-------|--------|---------|
| North Star | P11 product truth | Constitution header | Master outline banner |
| 7 capabilities | MVP goal + standards | Constitution map | — |
| Anti-goals | P11 WHAT_NOT_TO_DO | Constitution section | — |
| Trial model | TRIAL_ONE_PATH | — | Remove Simulation dep |
| Commercial | P11 payment blockers | Terms + invoice | BROKER_ONE_PAGER |
| Deployment | CURRENT_PRODUCT_SHAPE | — | — |
| Business rules | — | Triage rules v2 | insurance_broker_pilot_rules |

---

*End of constitution gap analysis*
