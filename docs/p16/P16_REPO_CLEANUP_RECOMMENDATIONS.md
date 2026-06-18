# P16 Repository Cleanup Recommendations

**Date:** 2026-06-17  
**Sprint:** P16 Decision Freeze  
**Authority:** Recommendations only — **no files deleted automatically.**  
**New SSOT:** `docs/p16/P16_DECISION_FREEZE_V1.md`

---

## Summary

| Category | Count (approx.) | Action |
|----------|-----------------|--------|
| **KEEP** | 18 | Active authority or pilot ops |
| **ARCHIVE** | 95+ | Superseded sprint artifacts, governance closeout, deploy forensics |
| **REVIEW** | 12 | Conflicts with freeze; needs header or merge |

**Primary conflicts found:**

1. **Duplicate roadmaps** — four competing 30/90-day plans in `product_constitution/`
2. **Tech stack contradiction** — `P16_OCR_AND_UPLOAD_TECH_OPTIONS.md` recommends shadcn/ui and "Skip Ant Design"; freeze locks Ant Design 5
3. **Product scope contradiction** — `P16_ADD_CAR_PACKET_BUILDER_MASTER_SPEC.md` requires customer confirmation workflow; freeze defers it
4. **Governance sprawl** — 40+ push/promotion/clean-tree docs from P16 promotion sprint (June 2026)
5. **Deploy forensics sprawl** — 25+ preview blank-page / QA router docs in `trial/` (resolved incidents)

---

## KEEP

Active authority, pilot operations, or directly referenced by Decision Freeze V1.

| File | Reason |
|------|--------|
| `docs/p16/P16_DECISION_FREEZE_V1.md` | **New SSOT** — scope + architecture freeze |
| `docs/p16/P16_REPO_CLEANUP_RECOMMENDATIONS.md` | This report |
| `docs/CURRENT_PRODUCT_SHAPE.md` | Runtime + deploy truth (AGENTS.md #2) |
| `docs/goals/insurance_paid_pilot_goal.md` | Commercial scope boundary |
| `docs/trial/INDEX.md` | Pilot operator entry |
| `docs/product_constitution/P16_ADD_CAR_PACKET_FIELD_CONTRACT.md` | Locked field contract (referenced by freeze) |
| `docs/product_constitution/P16_UPLOAD_FIRST_CUSTOMER_FLOW.md` | Upload-first flow (referenced by freeze) |
| `docs/product_constitution/P16_CUSTOMER_FIRST_CONSTITUTION.md` | Customer-first principles (timing/roles) |
| `docs/trial/P16_REAL_PILOT_DASHBOARD.md` | Active Chen Kui pilot tracker |
| `docs/trial/P16_TIME_SAVINGS_TRACKER.md` | Revenue milestone metrics |
| `docs/trial/P16_CASE_EVIDENCE_LOG.md` | Per-case evidence |
| `docs/trial/P16_REAL_CASE_WORKFLOW.md` | Human vs system steps |
| `docs/trial/P16_BROKER_FEEDBACK.md` | Broker experience log |
| `docs/trial/P16_OCR_KILL_TEST_RUNBOOK.md` | Operational runbook for extraction validation |
| `docs/trial/P16_OCR_KILL_TEST_REPORT.md` | Extraction GO/NO-GO evidence |
| `docs/trial/P16_COMMERCIAL_READINESS_REVIEW.md` | Commercial validation input |
| `docs/trial/P16_COMMERCIAL_RISK_REVIEW.md` | Risk register for pilot |
| `docs/runbooks/OPERATOR_SURFACE.md` | Operator target surface |

---

## ARCHIVE

Move to `docs/archive/p16/` (suggested). These are completed sprint artifacts, incident forensics, or superseded governance — valuable for history, not daily ops.

### Superseded roadmaps and build plans

| File | Reason |
|------|--------|
| `docs/product_constitution/P16Z2_30_DAY_ROADMAP.md` | Superseded by Decision Freeze V1 |
| `docs/product_constitution/P16Z25_30_DAY_ROADMAP.md` | Superseded by Decision Freeze V1 |
| `docs/product_constitution/P16Z25_90_DAY_ROADMAP.md` | Superseded by Decision Freeze V1 |
| `docs/product_constitution/ROADMAP_FROM_CONSTITUTION.md` | P14-era; conflicts with Trust Layer scope |
| `docs/product_constitution/P16_NEXT_14_DAY_BUILD_PLAN.md` | Pre-freeze build plan |
| `docs/product_constitution/P16Z25_NORTH_STAR.md` | Merge timing into freeze; archive original |

### Governance / promotion / push sprawl (product_constitution/)

| File | Reason |
|------|--------|
| `P16_FOUNDER_DECISION_MEMO.md` | Promotion decision — closed |
| `P16_EXECUTIVE_SUMMARY.md` | Promotion sprint summary |
| `P16_PUSH_PLAN.md` | Executed or superseded |
| `P16_PUSH_OR_NOT_PUSH.md` | Closed decision |
| `P16_PUSH_READINESS.md` | Closed gate |
| `P16_PUSH_PRESERVATION_PLAN.md` | Closed |
| `P16_PUSH_EXECUTION_READINESS.md` | Closed |
| `P16_PUSH_EXECUTION_REPORT.md` | Closed |
| `P16_PUSH_AND_RUNTIME_PREFLIGHT.md` | Closed |
| `P16_PUSH_AND_RUNTIME_EXECUTIVE_SUMMARY.md` | Closed |
| `P16_REMOTE_PRESERVATION_AUDIT.md` | Closed |
| `P16_REMOTE_PRESERVATION_FINAL.md` | Closed |
| `P16_REPO_PRESERVATION_FINAL_SUMMARY.md` | Closed |
| `P16_RELEASE_PRESERVATION_VERIFICATION.md` | Closed |
| `P16_RELEASE_INTEGRITY_CHECK.md` | Closed |
| `P16_RELEASE_VERIFICATION.md` | Closed |
| `P16_RELEASE_FREEZE_VALIDATION.md` | Superseded by this freeze |
| `P16_MAINLINE_PROMOTION_GATE.md` | Closed |
| `P16_MAINLINE_PROMOTION_READINESS_FINAL.md` | Closed |
| `P16_MAIN_PROMOTION_FINAL_GATE.md` | Closed |
| `P16_MAIN_PROMOTION_STATUS.md` | Closed |
| `P16_PROMOTION_READY_FINAL.md` | Closed |
| `P16_GOVERNANCE_CLOSEOUT_PRECHECK.md` | Closed |
| `P16_GOVERNANCE_CLOSEOUT_REPORT.md` | Closed |
| `P16_GOVERNANCE_FINALIZATION_PRECHECK.md` | Closed |
| `P16_GOVERNANCE_FINALIZATION_SUMMARY.md` | Closed |
| `P16_GOVERNANCE_FINAL_MEMO.md` | Closed |
| `P16_BRANCH_ACTION_PLAN.md` | Closed |
| `P16_BRANCH_ARCHAEOLOGY_PREP.md` | Closed |
| `P16_COMMIT_PLAN.md` | Closed |
| `P16_COMMIT_A_REPORT.md` | Closed |
| `P16_COMMIT_B_REPORT.md` | Closed |
| `P16_COMMIT_C_REPORT.md` | Closed |
| `P16_PRE_COMMIT_REVIEW.md` | Closed |
| `P16_AUDIT_REPORT_COMMIT.md` | Closed |
| `P16_CLEAN_TREE_CHECK.md` | Closed |
| `P16_CLEAN_TREE_FINAL_CHECK.md` | Closed |
| `P16_DIRTY_TREE_FINAL.md` | Closed |
| `P16_DIRTY_TREE_FINAL_CLASSIFICATION.md` | Closed |
| `P16_REPO_HYGIENE_EXECUTIVE_SUMMARY.md` | Closed |
| `P16_B3C8EC3_REVIEW.md` | Commit-specific |
| `P16_B3C8EC3_PUSH_REPORT.md` | Commit-specific |
| `P16_DEPLOY_ALIGNMENT_AUDIT.md` | Closed |
| `P16_MAINLINE_DIFF_REPORT.md` | Closed |

### Append integrity sprint (completed)

| File | Reason |
|------|--------|
| `P16_APPEND_BUG_PREFLIGHT.md` | Sprint complete |
| `P16_APPEND_ROOT_CAUSE.md` | Sprint complete |
| `P16_APPEND_REPRODUCTION.md` | Sprint complete |
| `P16_APPEND_REGRESSION_REPORT.md` | Sprint complete |
| `P16_APPEND_SIMULATION_REPORT.md` | Sprint complete |
| `P16_APPEND_COMMERCIAL_CERTIFICATION.md` | Sprint complete |
| `P16_APPEND_EXECUTIVE_SUMMARY.md` | Sprint complete |

### Phase 1 customer-first screen (completed)

| File | Reason |
|------|--------|
| `P16_PHASE1_CUSTOMER_FIRST_SCREEN_IMPLEMENTATION.md` | Sprint complete |
| `P16_PHASE1_CUSTOMER_FIRST_SCREEN_REVIEW.md` | Sprint complete |
| `P16_PHASE1_CUSTOMER_FIRST_SCREEN_SIMULATION.md` | Sprint complete |
| `P16_PHASE1_CUSTOMER_FIRST_SCREEN_CERTIFICATION.md` | Sprint complete |
| `P16_CUSTOMER_FIRST_P0_SUMMARY.md` | Absorbed into constitution |
| `P16_CUSTOMER_FIRST_CONSTITUTION_REVIEW.md` | Sprint complete |
| `P16_STATUS_VISIBILITY_ALIGNMENT_REPORT.md` | Sprint complete |

### Runtime gate / bundle reviews (completed)

| File | Reason |
|------|--------|
| `P16_RUNTIME_BUNDLE_REVIEW.md` | Closed |
| `P16_RUNTIME_GATE_REVIEW.md` | Closed |
| `P16_RUNTIME_RESOLUTION_REPORT.md` | Closed |
| `P16_RUNTIME_REVIEW_REPORT.md` | Closed |

### P16-Z24 simulation artifacts

| File | Reason |
|------|--------|
| `P16Z24_BEFORE_AFTER.md` | Pre-pilot simulation |
| `P16Z24_CASE_RESULTS.md` | Pre-pilot simulation |
| `P16Z24_CASE_QUALITY_SCORECARD.md` | Pre-pilot simulation |
| `P16Z24_AI_CUSTOMER_SCENARIOS.md` | Pre-pilot simulation |
| `P16Z24_IMPROVEMENT_CANDIDATES.md` | Pre-pilot simulation |
| `P16Z24_CHEN_KUI_DEMO_SET.md` | Pre-pilot simulation |

### Trial — deploy forensics / preview incidents (resolved)

| File | Reason |
|------|--------|
| `P16_PREVIEW_BLANK_PAGE_*` (8 files) | Incident resolved |
| `P16_PREVIEW_PHONE_LOOKUP_*` (5 files) | Incident resolved |
| `P16_QA_ROUTER_*` (5 files) | Incident resolved |
| `P16_QA_PREVIEW_RUNTIME_RECOVERY_SUMMARY.md` | Incident resolved |
| `P16_QA_ALIAS_VERIFICATION.md` | Incident resolved |
| `P16_PHONE_LOOKUP_RECOVERY.md` | Incident resolved |
| `P16_PHONE_RETURN_REHYDRATION_ROOT_CAUSE.md` | Incident resolved |
| `P16_CUSTOMER_REHYDRATION_REPRODUCTION.md` | Incident resolved |
| `P16_CUSTOMER_FIRST_CASE_REHYDRATION_INVESTIGATION.md` | Incident resolved |
| `P16_CASE_MEMORY_*` (4 files) | Sprint complete |
| `P16_APPEND_YEAR_FIELD_ROOT_CAUSE.md` | Fixed |
| `P16_DEMO_TAB_*` (3 files) | Sprint complete |
| `P16_DEPLOY_PRECHECK.md` | One-time |
| `P16_DEPLOYMENT_FINAL_VERDICT.md` | Closed |
| `P16_PREVIEW_DEPLOY_*` (2 files) | Closed |
| `P16_PREVIEW_ENV_AUDIT.md` | Closed |
| `P16_BACKEND_ACTIVE_CASE_AUTH_AUDIT.md` | Closed |
| `DEPLOY_FAILURE_ROOT_CAUSE.md` | Closed |

### Trial — pre-pilot simulation / certification (superseded by real pilot)

| File | Reason |
|------|--------|
| `P16_PRE_PILOT_*` (4 files) | Pre-pilot complete |
| `P16_PILOT_SIMULATION_REPORT.md` | Simulation only |
| `P16_FOUNDER_SIMULATION.md` | Simulation only |
| `P16_CUSTOMER_SIMULATION_*` (2 files) | Simulation only |
| `P16_STRESS_TEST_*` (3 files) | Pre-pilot complete |
| `P16_EDGE_CASE_PACK.md` | Pre-pilot complete |
| `P16_CHEN_KUI_PILOT_PLAN.md` | Superseded by REAL_PILOT_DASHBOARD |
| `P16_PILOT_CERTIFICATION.md` | Pre-pilot cert |
| `P16_PRE_COMMIT_VERIFICATION.md` | One-time |
| `P16_COMMIT_PRECHECK.md` | One-time |
| `P16_COMMIT_REPORT.md` | One-time |
| `P16_COMMIT_AND_QA_SMOKE_CERTIFICATION.md` | One-time |

### Trial — visibility / status truth sprints (completed)

| File | Reason |
|------|--------|
| `P16_VISIBILITY_*` (6 files) | Sprint complete |
| `P16_STATUS_TRUTH_*` (4 files) | Sprint complete |
| `P16_STATUS_SURFACE_*` (2 files) | Sprint complete |
| `P16_RUNTIME_VISIBILITY_AUDIT.md` | Sprint complete |
| `P16_OFFICE_VISIBILITY_*` (4 files) | Sprint complete |
| `P16_CUSTOMER_STATUS_SIMPLIFICATION_*` (2 files) | Sprint complete |
| `P16_CARD_PRESENTATION_AUDIT.md` | Sprint complete |
| `P16_WORKBENCH_RANKING_AUDIT.md` | Sprint complete |

### Already in docs/archive/ (no action)

Platform architecture blueprints under `docs/archive/sprints/` and `docs/archive/platform/` — already archived.

---

## REVIEW

These files conflict with Decision Freeze V1 or duplicate authority. Recommended action: add supersession header pointing to `docs/p16/P16_DECISION_FREEZE_V1.md`, then merge or archive.

| File | Conflict | Recommended action |
|------|----------|-------------------|
| `docs/product_constitution/P16_OCR_AND_UPLOAD_TECH_OPTIONS.md` | Recommends shadcn/ui, "Skip Ant Design" — freeze locks Ant Design 5 | Add **SUPERSEDED** header; archive after Trust Layer starts |
| `docs/product_constitution/P16_ADD_CAR_PACKET_BUILDER_MASTER_SPEC.md` | Requires customer confirmation workflow — freeze defers it | Add **PARTIAL** header; §2–§6 remain reference; confirmation rules overridden by freeze §4 |
| `docs/product_constitution/P16_PACKET_BUILDER_KILL_TEST_PLAN.md` | Pre-freeze scope | Align with Trust Layer 6-capability list or archive |
| `docs/product_constitution/P16Z18_CAPACITY_MODEL.md` | Broad capability model vs Trust Layer narrow scope | Keep for strategy; mark non-binding for V0 |
| `docs/product_constitution/P16Z18_CUSTOMER_FIRST_ARCHITECTURE.md` | May describe pre-upload chat-first flows | Review against upload-first freeze |
| `docs/product_constitution/P16_CUSTOMER_FIRST_GAP_REVIEW.md` | Code gap vs new scope | Re-run gap review after Trust Layer Sprint |
| `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` | Macro blueprint — may over-scope | AGENTS.md already marks "major sprints only"; add freeze cross-ref |
| `docs/SIMPLIFICATION_MASTER_PLAN.md` | Reduction roadmap | KEEP but ensure no conflict with Trusted Packet build |
| `docs/trial/P16_AI_PILOT_REVIEW.md` | May recommend features outside Trust Layer | Review P0s against freeze §6 |
| `docs/trial/P16_FIRST_INVOICE_READINESS.md` | Pre-freeze gate criteria | Align with freeze §8 acceptance criteria |
| `docs/trial/P16_INVOICE_READINESS_TRACKER.md` | May use old gates | Align with §9 revenue milestone |
| `docs/trial/P16_REAL_OCR_KILL_TEST_REPORT.md` | References gemini-2.0-flash | Update model string to 2.5 when code migrates |

---

## Suggested archive command (manual)

Do **not** run automatically. Example batch after founder approval:

```bash
mkdir -p docs/archive/p16/{governance,append,phase1,preview_incidents,pre_pilot,z24}

# Example moves (partial list):
git mv docs/product_constitution/P16_PUSH_PLAN.md docs/archive/p16/governance/
git mv docs/product_constitution/P16Z25_90_DAY_ROADMAP.md docs/archive/p16/governance/
# ... continue per tables above
```

---

## Index updates recommended

After archive pass:

1. Add `docs/p16/` to `docs/PROJECT_DOC_SYSTEM_MAP.md` START HERE table (position 2a for P16 scope)
2. Update `docs/trial/INDEX.md` to link Decision Freeze as scope authority
3. Update `AGENTS.md` optional row for P16 freeze doc

---

*End of P16 Repository Cleanup Recommendations*
