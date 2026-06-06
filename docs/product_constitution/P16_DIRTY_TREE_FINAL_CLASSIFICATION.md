# P16 Dirty Tree Final Classification

**Date:** 2026-06-06  
**Mission:** P16-REPO-HYGIENE-SPRINT — Phase 1  
**Branch HEAD:** `517f728` (`sprint-a/broker-front-door`)  
**Total dirty paths:** **1769**

---

## 5-Minute Founder Summary

The **1,769 dirty paths** are almost entirely **documentation housekeeping** — an in-progress archival migration moving ~1,228 legacy sprint reports from `docs/` root into `docs/sprints/archive/` and `docs/archive/`. The committed HEAD at `517f728` is clean; the working tree is not promotion-safe until this migration is committed or stashed.

| Question | Answer |
|----------|--------|
| What % is documentation? | **94.5%** (docs + reports + sprint artifacts + archived content) |
| What % is code? | **1.5%** (source + tests) |
| What % is generated artifacts? | **0.2%** |
| What % is safe to commit immediately? | **94.5%** (SAFE_TO_COMMIT classification) |

**Status mix:** 1,228 deleted (`D`), 471 untracked (`??`), 70 modified (`M`).

---

## Category Summary

| Category | Count | % |
|----------|------:|--:|
| docs | 1321 | 74.7% |
| reports | 209 | 11.8% |
| sprint artifacts | 115 | 6.5% |
| scripts | 40 | 2.3% |
| archived content | 27 | 1.5% |
| source code | 24 | 1.4% |
| configs | 23 | 1.3% |
| unknown | 4 | 0.2% |
| generated files | 3 | 0.2% |
| tests | 3 | 0.2% |
| **Total** | **1769** | **100%** |

---

## Top 50 Directories Contributing to Dirtiness

| Rank | Directory | Paths |
|------|-----------|------:|
| 1 | `docs/sprints` | 1020 |
| 2 | `docs/product_constitution` | 384 |
| 3 | `docs/trial` | 32 |
| 4 | `docs/archive` | 28 |
| 5 | `ui/src` | 20 |
| 6 | `docs/runbooks` | 6 |
| 7 | `services/fiqa_api` | 6 |
| 8 | `GENTS.md` | 1 |
| 9 | `Dockerfile.ecommerce` | 1 |
| 10 | `Dockerfile.jobhunter` | 1 |
| 11 | `Makefile` | 1 |
| 12 | `README.md` | 1 |
| 13 | `configs/clients` | 1 |
| 14 | `configs/demo.env.example` | 1 |
| 15 | `configs/industries` | 1 |
| 16 | `demo_brain_report.html` | 1 |
| 17 | `docker-compose.yml` | 1 |
| 18 | `docs/3_LIVE_CHAINS_IMPLEMENTATION_SPRINT_REPORT.md` | 1 |
| 19 | `docs/ADD_CAR_NEW_QUOTE_FLOW_SCOUTING_REPORT.md` | 1 |
| 20 | `docs/ADD_CAR_NEW_QUOTE_GAP_CLOSING_SPRINT_REPORT.md` | 1 |
| 21 | `docs/ADD_CAR_NEW_QUOTE_VERTICAL_FLOW_SPRINT_REPORT.md` | 1 |
| 22 | `docs/ADVERSARIAL_REAL_USER_SIMULATION_SPRINT_REPORT.md` | 1 |
| 23 | `docs/ANALYTICS_SYSTEM_REPORT.md` | 1 |
| 24 | `docs/ANDY_QUICK_START.md` | 1 |
| 25 | `docs/AUTOTUNER_ALG_DELIVERY.md` | 1 |
| 26 | `docs/AUTOTUNER_DELIVERY_SUMMARY.md` | 1 |
| 27 | `docs/AutoTuner_ALG_INDEX.md` | 1 |
| 28 | `docs/AutoTuner_ALG_NOTES.md` | 1 |
| 29 | `docs/AutoTuner_ALG_QUICK_START.md` | 1 |
| 30 | `docs/AutoTuner_README.md` | 1 |
| 31 | `docs/BACKEND_REDEPLOY_DAY_SUMMARY_AUDIT_REPORT.md` | 1 |
| 32 | `docs/BROKER_CASE_QUEUE_TRIAGE_SPRINT_REPORT.md` | 1 |
| 33 | `docs/BROKER_DAILY_USE_END_TO_END_SIMULATION_SPRINT_REPORT.md` | 1 |
| 34 | `docs/BROKER_DAILY_USE_WORKFLOW_POLISH_SPRINT_REPORT.md` | 1 |
| 35 | `docs/BROKER_DEMO_CHECKLIST.md` | 1 |
| 36 | `docs/BROKER_DEMO_DRIFT_GUARDRAIL.md` | 1 |
| 37 | `docs/BROKER_DEMO_FALLBACK_SCRIPT.md` | 1 |
| 38 | `docs/BROKER_DEMO_OPERATOR_RUNBOOK.md` | 1 |
| 39 | `docs/BROKER_DEMO_QUALITY_STANDARD.md` | 1 |
| 40 | `docs/BROKER_DEMO_SCRIPT_15MIN.md` | 1 |
| 41 | `docs/BROKER_DEMO_WHAT_TO_SAY.md` | 1 |
| 42 | `docs/BROKER_FOLLOWUP_MESSAGE.md` | 1 |
| 43 | `docs/BROKER_HANDOFF_CLARITY_DAILY_CASE_SPRINT_REPORT.md` | 1 |
| 44 | `docs/BROKER_HANDOFF_CLARITY_GUIDE.md` | 1 |
| 45 | `docs/BROKER_INBOX_TRIAGE_API_SPRINT_REPORT.md` | 1 |
| 46 | `docs/BROKER_INBOX_TRIAGE_EXECUTION_REPORT.md` | 1 |
| 47 | `docs/BROKER_INVITE_MESSAGE.md` | 1 |
| 48 | `docs/BROKER_LONGTAIL_MEETING_SUBSET.md` | 1 |
| 49 | `docs/BROKER_MEETING_PACKAGE.md` | 1 |
| 50 | `docs/BROKER_PILOT_PACKAGE.md` | 1 |

---

## Status Breakdown

| Status | Count | Meaning |
|--------|------:|---------|
| `D` | 1,228 | Deleted from index (archival migration source) |
| `??` | 471 | Untracked (archival destination + new governance docs) |
| `M` | 70 | Modified tracked files |

---

## Category Detail

### DOCS — 1321 paths

| Status | Path | Safety |
|--------|------|--------|
| `M ` | `GENTS.md` | SAFE_TO_COMMIT |
| `??` | `docs/15_MINUTE_ENGINEER_ONBOARDING.md` | SAFE_TO_COMMIT |
| ` M` | `docs/ANDY_QUICK_START.md` | SAFE_TO_COMMIT |
| ` D` | `docs/AUTOTUNER_ALG_DELIVERY.md` | SAFE_TO_COMMIT |
| ` D` | `docs/AUTOTUNER_DELIVERY_SUMMARY.md` | SAFE_TO_COMMIT |
| ` D` | `docs/AutoTuner_ALG_INDEX.md` | SAFE_TO_COMMIT |
| ` D` | `docs/AutoTuner_ALG_NOTES.md` | SAFE_TO_COMMIT |
| ` D` | `docs/AutoTuner_ALG_QUICK_START.md` | SAFE_TO_COMMIT |
| ` D` | `docs/AutoTuner_README.md` | SAFE_TO_COMMIT |
| ` D` | `docs/BROKER_DEMO_CHECKLIST.md` | SAFE_TO_COMMIT |
| ` D` | `docs/BROKER_DEMO_DRIFT_GUARDRAIL.md` | SAFE_TO_COMMIT |
| ` D` | `docs/BROKER_DEMO_FALLBACK_SCRIPT.md` | SAFE_TO_COMMIT |
| `??` | `docs/BROKER_DEMO_FLOW.md` | SAFE_TO_COMMIT |
| ` D` | `docs/BROKER_DEMO_OPERATOR_RUNBOOK.md` | SAFE_TO_COMMIT |
| ` D` | `docs/BROKER_DEMO_QUALITY_STANDARD.md` | SAFE_TO_COMMIT |
| ` D` | `docs/BROKER_DEMO_SCRIPT_15MIN.md` | SAFE_TO_COMMIT |
| ` D` | `docs/BROKER_DEMO_WHAT_TO_SAY.md` | SAFE_TO_COMMIT |
| ` D` | `docs/BROKER_FOLLOWUP_MESSAGE.md` | SAFE_TO_COMMIT |
| ` D` | `docs/BROKER_HANDOFF_CLARITY_GUIDE.md` | SAFE_TO_COMMIT |
| ` D` | `docs/BROKER_INVITE_MESSAGE.md` | SAFE_TO_COMMIT |
| ` D` | `docs/BROKER_LONGTAIL_MEETING_SUBSET.md` | SAFE_TO_COMMIT |
| ` D` | `docs/BROKER_MEETING_PACKAGE.md` | SAFE_TO_COMMIT |
| `??` | `docs/BROKER_ONE_PAGER.md` | SAFE_TO_COMMIT |
| ` D` | `docs/BROKER_PILOT_PACKAGE.md` | SAFE_TO_COMMIT |
| ` D` | `docs/BROKER_PRODUCT_DESCRIPTION.md` | SAFE_TO_COMMIT |
| `??` | `docs/BROKER_TRIAL_PLAYBOOK.md` | SAFE_TO_COMMIT |
| ` D` | `docs/BROKER_VALUE_VALIDATION_MEETING_PACK.md` | SAFE_TO_COMMIT |
| ` D` | `docs/CASE_HANDOFF_MAINLINE_BLUEPRINT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/CHEN_KUI_FOUNDER_DEMO_SCRIPT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/CHEN_KUI_REPLY_STYLE_PROXY.md` | SAFE_TO_COMMIT |
| ` D` | `docs/CHEN_KUI_TRIAL_PACK.md` | SAFE_TO_COMMIT |
| ` D` | `docs/COMMERCIAL_PRODUCT_FRAMEWORK_OVERVIEW.md` | SAFE_TO_COMMIT |
| ` D` | `docs/CONFIG_EXTRACTION_GUIDE.md` | SAFE_TO_COMMIT |
| ` D` | `docs/CONTINUOUS_CUSTOMER_INTAKE_MVP.md` | SAFE_TO_COMMIT |
| ` M` | `docs/CURRENT_PRODUCT_SHAPE.md` | SAFE_TO_COMMIT |
| ` D` | `docs/CURRENT_SYSTEM_FILE_CLASSIFICATION.md` | SAFE_TO_COMMIT |
| ` D` | `docs/CUSTOMER_ENTRY_REPLY_STRATEGY.md` | SAFE_TO_COMMIT |
| `??` | `docs/CUSTOMER_LANGUAGE_GUIDE.md` | SAFE_TO_COMMIT |
| ` D` | `docs/DEEP_MULTI_TURN_TARGET.md` | SAFE_TO_COMMIT |
| ` D` | `docs/DEMO_FOR_CHENKUI_ACCEPTANCE.md` | SAFE_TO_COMMIT |
| ` D` | `docs/DEMO_OFFLINE_PACK.md` | SAFE_TO_COMMIT |
| ` D` | `docs/DEMO_SCRIPT.md` | SAFE_TO_COMMIT |
| `??` | `docs/DEMO_STORY.md` | SAFE_TO_COMMIT |
| ` M` | `docs/DEPLOYMENT_READINESS.md` | SAFE_TO_COMMIT |
| ` M` | `docs/DEPRECATED_PATHS.md` | SAFE_TO_COMMIT |
| ` M` | `docs/DOC_INDEX_RECOMMENDED.md` | SAFE_TO_COMMIT |
| ` D` | `docs/ENTITY_TRIAGE_INTEGRATION_PLAN.md` | SAFE_TO_COMMIT |
| ` D` | `docs/FIVE_BUSINESS_FLOWS_TARGETS.md` | SAFE_TO_COMMIT |
| ` D` | `docs/FOUNDER_DEMO_SOP.md` | SAFE_TO_COMMIT |
| `??` | `docs/FOUNDER_ONE_PATH.md` | SAFE_TO_COMMIT |
| ` D` | `docs/FRONTEND_TRANSLATION_INTEGRATION.md` | SAFE_TO_COMMIT |
| ` D` | `docs/FRONT_END_CONSOLIDATION_TARGET.md` | SAFE_TO_COMMIT |
| ` D` | `docs/FUTURE_EXTRACTION_POINTS.md` | SAFE_TO_COMMIT |
| ` D` | `docs/KNOWLEDGE_ARCHITECTURE_AND_CONFIG_LAYER.md` | SAFE_TO_COMMIT |
| ` D` | `docs/LANGSMITH_IMPLEMENTATION_SUMMARY.md` | SAFE_TO_COMMIT |
| ` D` | `docs/LIGHTWEIGHT_STATE_MACHINE_BLUEPRINT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/MATURE_INTAKE_SKELETON.md` | SAFE_TO_COMMIT |
| `??` | `docs/P8_DEEP_ISOLATION_PLAN.md` | SAFE_TO_COMMIT |
| `??` | `docs/P9_BROKER_SURFACE_PLAN.md` | SAFE_TO_COMMIT |
| ` D` | `docs/PLUGIN_ARCHITECTURE_MAP.md` | SAFE_TO_COMMIT |
| ` D` | `docs/PRE_DEMO_FLOW.md` | SAFE_TO_COMMIT |
| ` D` | `docs/PRODUCT_TRUTH_DOCUMENT.md` | SAFE_TO_COMMIT |
| ` M` | `docs/PROJECT_DOC_SYSTEM_MAP.md` | SAFE_TO_COMMIT |
| ` D` | `docs/PROJECT_TRUTH_SWITCH.md` | SAFE_TO_COMMIT |
| ` D` | `docs/QUICKSTART.md` | SAFE_TO_COMMIT |
| ` D` | `docs/REAL_CUSTOMER_PACK_BLUEPRINT.md` | SAFE_TO_COMMIT |
| `??` | `docs/ROOT_DIRECTORY_GUIDE.md` | SAFE_TO_COMMIT |
| ` M` | `docs/SIMPLIFICATION_MASTER_PLAN.md` | SAFE_TO_COMMIT |
| ` D` | `docs/SIMULATION_ASSISTANT_SPEED_LAYER_BLUEPRINT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/SPEED_ROUTING_MAINLINE_BLUEPRINT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/STAGE_1_SERVICE_RECORD_DB_BLUEPRINT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/TEST_COVERAGE_SUMMARY.md` | SAFE_TO_COMMIT |
| ` D` | `docs/TODAY_COMMERCIAL_PROGRESS_MASTER_SUMMARY.md` | SAFE_TO_COMMIT |
| `??` | `docs/TRIAL_ONE_PATH.md` | SAFE_TO_COMMIT |
| ` D` | `docs/TRUSTED_ASSISTANT_PLATFORM_BLUEPRINT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/UI_WHITESCREEN_FIX.md` | SAFE_TO_COMMIT |
| ` D` | `docs/UNIFIED_INTAKE_DEMO_READINESS.md` | SAFE_TO_COMMIT |
| ` D` | `docs/UNIFIED_INTAKE_MASTER_BLUEPRINT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/UNIFIED_INTAKE_MVP_BOUNDARIES.md` | SAFE_TO_COMMIT |
| ` D` | `docs/UNIFIED_INTAKE_MVP_SCENARIOS.md` | SAFE_TO_COMMIT |
| ` D` | `docs/approval_score_ml.md` | SAFE_TO_COMMIT |
| ` D` | `docs/auto_rewrite_pitch_2min.md` | SAFE_TO_COMMIT |
| ` D` | `docs/broker_value_feedback_form.md` | SAFE_TO_COMMIT |
| ` D` | `docs/broker_value_test_sheet.md` | SAFE_TO_COMMIT |
| ` D` | `docs/crowdstrike_role_mapping.md` | SAFE_TO_COMMIT |
| ` D` | `docs/jobhunter_frontend_setup.md` | SAFE_TO_COMMIT |
| ` D` | `docs/jobhunter_graph_trace_implementation.md` | SAFE_TO_COMMIT |
| ` D` | `docs/k8s_ecommerce_k8s_story.md` | SAFE_TO_COMMIT |
| ` D` | `docs/langgraph_single_home_diagram.md` | SAFE_TO_COMMIT |
| ` D` | `docs/langgraph_system_health_diagram.md` | SAFE_TO_COMMIT |
| ` D` | `docs/langsmith_graph_visualization.md` | SAFE_TO_COMMIT |
| ` D` | `docs/langsmith_implementation_summary.md` | SAFE_TO_COMMIT |
| ` D` | `docs/langsmith_setup.md` | SAFE_TO_COMMIT |
| ` D` | `docs/langsmith_view_graph_guide.md` | SAFE_TO_COMMIT |
| ` D` | `docs/mortgage_ai_demo.md` | SAFE_TO_COMMIT |
| ` D` | `docs/ops_actions_and_guardrails_map.md` | SAFE_TO_COMMIT |
| ` D` | `docs/ops_copilot_logging_audit_summary.md` | SAFE_TO_COMMIT |
| ` D` | `docs/ops_copilot_overview.md` | SAFE_TO_COMMIT |
| `??` | `docs/product_constitution/.p16y_results/` | SAFE_TO_COMMIT |
| `??` | `docs/product_constitution/.p16z20_results/` | SAFE_TO_COMMIT |

*… and 1221 more paths in this category.*

### REPORTS — 209 paths

| Status | Path | Safety |
|--------|------|--------|
| ` D` | `docs/ADD_CAR_NEW_QUOTE_FLOW_SCOUTING_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/ANALYTICS_SYSTEM_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/BACKEND_REDEPLOY_DAY_SUMMARY_AUDIT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/BROKER_INBOX_TRIAGE_EXECUTION_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/DEPLOYMENT_SCOUT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/DOCS_CLARITY_ARCHIVE_BOUNDARY_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/DOCS_SECONDARY_CLEANUP_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/FINAL_PRODUCT_CRITIQUE_AND_POLISH_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/FOUNDER_DEMO_SOP_TRIAL_FEEDBACK_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/FRONTEND_REDEPLOY_CASE_REPORT_ACCEPTANCE_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/GIT_CLEANUP_MILESTONE_COMMIT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/MULTI_TURN_CUSTOMER_INTAKE_SIMULATION_REPORT.md` | SAFE_TO_COMMIT |
| `??` | `docs/P8_FINAL_AUDIT.md` | SAFE_TO_COMMIT |
| `??` | `docs/P9_FINAL_AUDIT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/PRODUCTION_LAUNCH_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/PRODUCT_AUDIT_UNIFIED_INTAKE_2026.md` | SAFE_TO_COMMIT |
| ` D` | `docs/REPO_AUDIT_MILESTONE_COMMIT_PLANNING_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/SIMULATION_ASSISTANT_SPEED_REALISM_AUDIT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/SPEED_LAYER_REDEPLOY_ACCEPTANCE_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/UNIFIED_INTAKE_MVP_PRODUCT_DEFINITION_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/UNIFIED_INTAKE_SCOUTING_COMPLETION_REVIEW_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/V4_ZERO_QUESTION_ENGINE_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/VERCEL_CORS_DEPLOY_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/WEEKEND_FINAL_PRODUCT_HEALTH_CHECK_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/offline_agent_eval_report.md` | SAFE_TO_COMMIT |
| ` D` | `docs/offline_ops_agent_eval_report.md` | SAFE_TO_COMMIT |
| ` D` | `docs/ops_rag_eval_report.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/BROKER_TRIAL_HANDOFF_TIMING_AUDIT/01_HANDOFF_TIMING_AUDIT_BLUEPRINT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/BROKER_TRIAL_HANDOFF_TIMING_AUDIT/BROKER_TRIAL_HANDOFF_TIMING_AUDIT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/CASE_CONTEXT_CONTINUATION_RESHOP_PG_CI_SPRINT/03_FINAL_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/CASE_PERSISTENCE_WORKBENCH_POLISH_SPRINT/CASE_PERSISTENCE_WORKBENCH_POLISH_FINAL_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/CLIENT_AWARE_HANDOFF_WIRING/CLIENT_AWARE_HANDOFF_TRIAGE_WIRING_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/CLIENT_CONFIGURATION_WIRING_SPRINT/CLIENT_CONFIGURATION_WIRING_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/CLIENT_PACK_OPERATING_MANUAL_PRODUCTIZATION_INDEX/FINAL_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/CROSS_CLIENT_COMPATIBILITY_ISOLATION_SPRINT/CLIENT_ISOLATION_AUDIT_SPEC.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/CROSS_CLIENT_COMPATIBILITY_ISOLATION_SPRINT/FINAL_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/FLOW_ARCHITECTURE_SUMMARY_ROADMAP/FINAL_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/FOUNDER_BROKER_TRIAL_EXECUTION_SPRINT/FOUNDER_BROKER_TRIAL_EXECUTION_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/MATURE_SKELETON_COMMERCIAL_INTAKE_BACKBONE/MATURE_SKELETON_COMMERCIAL_INTAKE_BACKBONE_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/MIXED_INTENT_SECONDARY_CASE_SPRINT/00_BASELINE_AUDIT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/MIXED_INTENT_SECONDARY_CASE_SPRINT/REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/NARROW_POSITIONING_AND_OPERATOR_VALUE_SPRINT/FINAL_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/PRODUCT_READINESS_GAP_ASSESSMENT_SPRINT/FINAL_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/PRODUCT_VALUE_REVIEW_SPRINT/PRODUCT_VALUE_REVIEW_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/SALES_READINESS_HARDENING/09_BASELINE_AUDIT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/SALES_READINESS_HARDENING/SALES_READINESS_HARDENING_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/SECOND_BROKER_CLIENT_PACK_DRILL/CURRENT_PORTABILITY_AUDIT_SPEC.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/SECOND_BROKER_CLIENT_PACK_DRILL/FINAL_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/SELLABLE_STANDARD_SCENARIO_PACKAGE/08_BASELINE_AUDIT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/SELLABLE_STANDARD_SCENARIO_PACKAGE/SELLABLE_STANDARD_SCENARIO_PACKAGE_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/SIMULATION_TAB_AND_FLOW_EXPLANATION_IMPLEMENTATION_SPRINT/03_FINAL_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/SMALL_BATCH_PHRASE_MAP_EXTERNALIZATION_SPRINT/FINAL_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/SMALL_BATCH_PHRASE_MAP_EXTERNALIZATION_SPRINT/RESIDUAL_COPY_AUDIT_SPEC.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/STAGE_1_SERVICE_RECORD_POSTGRES_FOUNDATION_SPRINT/03_FINAL_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/STANDARD_SCENARIO_PACKAGE_2/08_BASELINE_AUDIT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/STANDARD_SCENARIO_PACKAGE_2/STANDARD_SCENARIO_PACKAGE_2_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/TOP_COMMERCIAL_SCENARIOS_DEEPENING_SPRINT/TOP_COMMERCIAL_SCENARIOS_DEEPENING_MASTER_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/TOP_SCENARIOS_HARDENING_SPRINT/TOP_SCENARIOS_HARDENING_MASTER_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/TRUTH_INTENT_REPLY_THREE_LAYER_STANDARD_SPRINT/03_FINAL_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/TRUTH_LAYER_ENFORCEMENT_GAP_CHECK_SPRINT/03_FINAL_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/TRUTH_LAYER_REPLY_LAYER_INDUSTRIAL_STANDARD_SPRINT/03_FINAL_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/UNIFIED_INTAKE_UI_PROFESSIONALIZATION/00_BASELINE_AUDIT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/UNIFIED_INTAKE_UI_PROFESSIONALIZATION/UNIFIED_INTAKE_UI_PROFESSIONALIZATION_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/WEB_INFORMED_ADD_CAR_REALISTIC_BATTERY/FINAL_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/WORKBENCH_DETAIL_PARITY_SPRINT/03_FINAL_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/WORKBENCH_OFFICE_TOOL_PROFESSIONALIZATION/00_BASELINE_AUDIT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/WORKBENCH_OFFICE_TOOL_PROFESSIONALIZATION/WORKBENCH_OFFICE_TOOL_PROFESSIONALIZATION_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/ANSWER_ALIGNMENT_AUDIT_EXECUTION_OUTLINE.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/ANSWER_ALIGNMENT_AUDIT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/BACKEND_REDEPLOY_FOUNDER_TRIAL_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/CUSTOMER_ENTRY_TRUE_MULTI_TURN_REPAIR_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/EIGHT_QUESTION_INTEGRATION_AUDIT_ACCEPTANCE_CRITERIA.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/EIGHT_QUESTION_INTEGRATION_AUDIT_BLUEPRINT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/EIGHT_QUESTION_INTEGRATION_AUDIT_EXECUTION_OUTLINE.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/EIGHT_QUESTION_INTEGRATION_AUDIT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/FAQ_CORPUS_PRODUCTIZATION_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/FRONTEND_REDEPLOY_FOUNDER_DEMO_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/FUTURE_SAAS_OPERATING_SYSTEM_FINAL_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/HANDOFF_TIMING_REGRESSION_REDEPLOY/HANDOFF_TIMING_REGRESSION_REDEPLOY_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/HEALTH_ENDPOINT_ROOT_CAUSE_PERMANENT_FIX/CURRENT_HEALTH_ENDPOINT_AUDIT_SPEC.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/HEALTH_ENDPOINT_ROOT_CAUSE_PERMANENT_FIX/FINAL_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/HIGH_VALUE_QUESTION_REALISM_PRODUCT_POLISH_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/PERSIST_FORMAL_SUBMIT_ALIGNMENT_SPRINT/03_FINAL_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/PRODUCTION_DEPLOY_REMOTE_TIMESTAMP_PROOF_SPRINT/03_FINAL_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/REMOTE_DEMO_ENV_REBASELINE_PRECHECK_SPRINT/03_FINAL_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/ROLE_C_BACKEND_DEPLOY_SMOKE_CHECK_SPRINT/03_FINAL_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/SMALL_BUSINESS_READINESS_STRESS_TEST_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/THREE_CRITICAL_ENTRY_VALIDATION_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/TOP_SCENARIOS_HARDENING_PHASE2_MASTER_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/TURN1_SPEED_MITIGATION_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/WORKBENCH_HANDOFF_PROFESSIONALIZATION_TRIAL_HARDENING/00_BASELINE_AUDIT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/WORKBENCH_HANDOFF_PROFESSIONALIZATION_TRIAL_HARDENING/DEPLOY_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/WORKBENCH_HANDOFF_PROFESSIONALIZATION_TRIAL_HARDENING/WORKBENCH_HANDOFF_PROFESSIONALIZATION_TRIAL_HARDENING_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/add_car_sprints/ADD_CAR_20_30_SCENARIO_EXPANSION_RULE_MAP/09_FINAL_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/add_car_sprints/ADD_CAR_AMAZON_STYLE_TASK_FLOW_SKELETON_SPRINT/03_FINAL_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/add_car_sprints/ADD_CAR_ATTACHMENT_READY_LITE/00_BASELINE_AUDIT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/add_car_sprints/ADD_CAR_BATTERY_RERUN_MUTATION_STRESS/FINAL_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/add_car_sprints/ADD_CAR_BROKER_FIRST_STATE_FLOW_HARDENING_SPRINT/03_FINAL_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/add_car_sprints/ADD_CAR_COMMERCIAL_FLOW_HARDENING/00_BASELINE_AUDIT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/add_car_sprints/ADD_CAR_COMMERCIAL_FLOW_HARDENING/ADD_CAR_COMMERCIAL_FLOW_HARDENING_REPORT.md` | SAFE_TO_COMMIT |

*… and 109 more paths in this category.*

### SPRINT ARTIFACTS — 115 paths

| Status | Path | Safety |
|--------|------|--------|
| ` D` | `docs/3_LIVE_CHAINS_IMPLEMENTATION_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/ADD_CAR_NEW_QUOTE_GAP_CLOSING_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/ADD_CAR_NEW_QUOTE_VERTICAL_FLOW_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/ADVERSARIAL_REAL_USER_SIMULATION_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/BROKER_CASE_QUEUE_TRIAGE_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/BROKER_DAILY_USE_END_TO_END_SIMULATION_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/BROKER_DAILY_USE_WORKFLOW_POLISH_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/BROKER_HANDOFF_CLARITY_DAILY_CASE_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/BROKER_INBOX_TRIAGE_API_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/BROKER_PRIMARY_DOCS_AND_MULTI_AGENT_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/BROKER_TRIAL_KICKOFF_READINESS_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/BROKER_WORKBENCH_STRUCTURED_INTAKE_UI_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/BROKER_WORKFLOW_COHESION_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/BUILD_INFO_BAR_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/CASE_HANDOFF_MAINLINE_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/CHEN_KUI_REAL_MESSAGE_FOUNDER_PACK_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/CLIENT_PACK_FOUNDATION_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/COMPLEX_ADVERSARIAL_SIMULATION_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/CONFIG_EXTRACTION_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/CONTINUOUS_CONVERSATIONAL_INTAKE_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/CORE_REPLY_TEMPLATE_EXPANSION_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/CRITICAL_MULTI_TURN_QUALITY_POLISH_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/CUSTOMER_CONVERSATIONAL_INTAKE_QUALITY_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/CUSTOMER_ENTRY_CONVERSATIONAL_UX_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/CUSTOMER_ENTRY_ISSUE_PROGRESSION_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/CUSTOMER_ENTRY_NEXT_STEP_GUIDANCE_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/CUSTOMER_ENTRY_PATTERN_BORROWING_UX_REFINEMENT_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/CUSTOMER_ENTRY_REPLY_STRATEGY_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/CUSTOMER_ENTRY_TAB_MVP_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/EXPRESSION_ROBUSTNESS_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/FINAL_PILOT_CONFIDENCE_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/FIVE_BUSINESS_FLOWS_MULTI_TURN_UX_STRESS_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/FIVE_BUSINESS_FLOWS_VERTICALIZATION_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/FIVE_CORE_FLOWS_DEEP_MULTI_TURN_STRUCTURED_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/FOUNDER_DEMO_QUEUE_LIVE_ROBUSTNESS_PROOF_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/FRONT_END_NATURALNESS_PROGRESSION_CONSOLIDATION_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/KNOWLEDGE_ARCHITECTURE_CONFIG_LAYER_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/KNOWLEDGE_INGESTION_FIRST_LIVE_RETRIEVAL_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/LIGHTWEIGHT_STATE_MACHINE_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/LIGHTWEIGHT_TICKET_FOLLOWUP_UX_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/MATURE_INTAKE_SKELETON_ALIGNMENT_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/MISSING_DOCUMENT_STRUCTURED_INTAKE_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/PASTE_NEW_MESSAGE_INTO_EXISTING_CASE_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/PRODUCTION_BUILD_INFO_AND_CASE_UX_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/READINESS_REPAIR_EDGE_CASE_CONFIDENCE_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/REAL_BROKER_TRIAL_PACKAGE_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/REAL_CUSTOMER_PACK_MAINLINE_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/REAL_HUMAN_DEMO_READINESS_MANUAL_SMOKE_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/REPLAY_SIZE_REPEATED_REPLY_AUDIT_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/REPLY_TEMPLATE_EXTRACTION_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/RETRIEVAL_FLOW_EXPANSION_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/RETRIEVAL_KNOWLEDGE_LAYER_FOUNDATION_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/RETRIEVAL_RUNTIME_STABILITY_PRODUCT_PROOF_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/SECOND_KNOWLEDGE_SLICE_3_AGENT_SIMULATION_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/SECOND_TURN_FOLLOWUP_QUALITY_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/SIMULATION_ASSISTANT_AUDIT_MULTI_TURN_DEPTH_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/SIMULATION_ASSISTANT_DEEP_TRIAL_SCENARIOS_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/SIMULATION_ASSISTANT_SCENARIO_EXPANSION_BUG_HARVEST_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/SIMULATION_ASSISTANT_SPEED_LAYER_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/SPEED_ROUTING_MAINLINE_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/STATE_FIELD_ACCURACY_AUDIT_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/STRUCTURED_OUTPUT_VISIBILITY_BUG_HARVEST_TRIAL_READINESS_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/STRUCTURED_WORKBENCH_EXPANSION_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/TODAY_SPRINT_PLAN_REVIEW.md` | SAFE_TO_COMMIT |
| ` D` | `docs/TRIAL_EXECUTION_READINESS_LAST_MILE_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/TRIAL_LAUNCH_FIX_NOW_QUEUE_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/UNIFIED_INTAKE_DRAFT_QUALITY_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/UNIFIED_INTAKE_EXTENDED_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/UNIFIED_INTAKE_MVP_UI_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/UNIFIED_INTAKE_USABILITY_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/UNIFIED_INTAKE_WORKFLOW_MATURITY_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/VISUAL_SIMULATION_ASSISTANT_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| `??` | `docs/product_constitution/POST_SPRINT_HEALTH_CHECK.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/CLIENT_IDENTITY_PERSISTENCE/CLIENT_IDENTITY_PERSISTENCE_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/CONFIGURATION_LAYER_SPRINT/CONFIGURATION_LAYER_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/MIXED_INTENT_SECONDARY_CASE_SPRINT/MIXED_INTENT_SECONDARY_CASE_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/ANSWER_ALIGNMENT_AUDIT_SPRINT_BLUEPRINT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/AUTO_INSURANCE_FAQ_INTAKE_CORPUS_SPRINT_BLUEPRINT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/BACKEND_REDEPLOY_DEMO_WARMUP_SPRINT_BLUEPRINT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/BACKEND_REDEPLOY_DEMO_WARMUP_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/BACKEND_REDEPLOY_FOUNDER_TRIAL_SPRINT_BLUEPRINT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/CLIENT_IDENTITY_PERSISTENCE_DEPLOY_SPRINT_BLUEPRINT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/CUSTOMER_ENTRY_MULTI_TURN_REPAIR_SPRINT_BLUEPRINT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/FAQ_CORPUS_PRODUCTIZATION_SPRINT_BLUEPRINT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/FOUNDER_DEMO_SOP_TRIAL_FEEDBACK_SPRINT_BLUEPRINT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/FRONTEND_REDEPLOY_FOUNDER_DEMO_SPRINT_BLUEPRINT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/HIGH_VALUE_QUESTION_REALISM_SPRINT_BLUEPRINT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/MULTI_TURN_STRESS_TEST_GAP_ANALYSIS_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/PILOT_READINESS_SELLABILITY_SPRINT_BLUEPRINT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/PILOT_READINESS_SELLABILITY_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/REASSURE_THEN_ROUTE_SPRINT_BLUEPRINT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/REASSURE_THEN_ROUTE_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/THREE_CRITICAL_ENTRY_SPRINT_BLUEPRINT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/TURN1_EXPERIENCE_SPRINT_BLUEPRINT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/TURN1_EXPERIENCE_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/TURN1_LIGHTWEIGHT_COLDSTART_SPRINT_BLUEPRINT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/TURN1_LIGHTWEIGHT_COLDSTART_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/UNIFIED_INTAKE_FOCUS_MODE_SPRINT_BLUEPRINT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/UNIFIED_INTAKE_FOCUS_MODE_SPRINT_REPORT.md` | SAFE_TO_COMMIT |
| ` D` | `docs/sprints/archive/add_car_sprints/ADD_CAR_CLEAR_SUBMISSION_CONFIRMATION_HANDOFF/10_ADD_CAR_CLEAR_SUBMISSION_CONFIRMATION_HANDOFF_SPRINT_REPORT.md` | SAFE_TO_COMMIT |

*… and 15 more paths in this category.*

### SCRIPTS — 40 paths

| Status | Path | Safety |
|--------|------|--------|
| `??` | `scripts/DEEP_SCRIPT_TIER_MAP.md` | REVIEW_REQUIRED |
| `??` | `scripts/LAB_SCRIPT_INDEX.md` | REVIEW_REQUIRED |
| ` M` | `scripts/README.md` | REVIEW_REQUIRED |
| ` M` | `scripts/README_OPERATOR.md` | REVIEW_REQUIRED |
| `??` | `scripts/archive/` | REVIEW_REQUIRED |
| ` M` | `scripts/check_unified_intake_prod_posture.sh` | REVIEW_REQUIRED |
| ` M` | `scripts/demo_pre_checklist.sh` | REVIEW_REQUIRED |
| ` M` | `scripts/demo_quick_validate.sh` | REVIEW_REQUIRED |
| `??` | `scripts/deploy/` | REVIEW_REQUIRED |
| ` M` | `scripts/deploy_paid_pilot.sh` | REVIEW_REQUIRED |
| ` M` | `scripts/dev_local.sh` | REVIEW_REQUIRED |
| `??` | `scripts/founder/` | REVIEW_REQUIRED |
| ` M` | `scripts/founder_pre_trial_checklist.sh` | REVIEW_REQUIRED |
| ` M` | `scripts/health_check.sh` | REVIEW_REQUIRED |
| ` M` | `scripts/import_smoke_check.py` | REVIEW_REQUIRED |
| `??` | `scripts/lab/` | REVIEW_REQUIRED |
| `??` | `scripts/operator/` | REVIEW_REQUIRED |
| `??` | `scripts/p16z11_founder_output.sh` | REVIEW_REQUIRED |
| `??` | `scripts/post_sprint_check.sh` | REVIEW_REQUIRED |
| ` M` | `scripts/restore_8001_readiness.sh` | REVIEW_REQUIRED |
| ` M` | `scripts/run_append_boundary_ab_scenarios.py` | REVIEW_REQUIRED |
| ` M` | `scripts/run_cross_client_ab_scenarios.py` | REVIEW_REQUIRED |
| ` M` | `scripts/run_demo_local.sh` | REVIEW_REQUIRED |
| `??` | `scripts/run_p16y_case_battery.py` | REVIEW_REQUIRED |
| `??` | `scripts/run_p16z20_add_car_simulation.py` | REVIEW_REQUIRED |
| `??` | `scripts/run_p16z21_tournament_simulation.py` | REVIEW_REQUIRED |
| `??` | `scripts/run_p16z235_founder_reality_sprint.py` | REVIEW_REQUIRED |
| `??` | `scripts/run_p16z24_add_car_sprint.py` | REVIEW_REQUIRED |
| ` M` | `scripts/run_residual_copy_ab_scenarios.py` | REVIEW_REQUIRED |
| `??` | `scripts/run_role_d_memory_battery.py` | REVIEW_REQUIRED |
| ` M` | `scripts/run_small_batch_phrase_map_ab_scenarios.py` | REVIEW_REQUIRED |
| ` M` | `scripts/start_all.sh` | REVIEW_REQUIRED |
| ` M` | `scripts/start_demo_app.sh` | REVIEW_REQUIRED |
| ` M` | `scripts/stop_all.sh` | REVIEW_REQUIRED |
| ` M` | `scripts/summarize_readiness_posture.sh` | REVIEW_REQUIRED |
| `??` | `scripts/summarize_support_posture.sh` | REVIEW_REQUIRED |
| ` M` | `scripts/trial_launch_check.sh` | REVIEW_REQUIRED |
| ` M` | `scripts/trial_readiness_check.sh` | REVIEW_REQUIRED |
| ` M` | `scripts/validate_pilot_deploy_env.py` | REVIEW_REQUIRED |
| ` D` | `triage.sh` | REVIEW_REQUIRED |

### ARCHIVED CONTENT — 27 paths

| Status | Path | Safety |
|--------|------|--------|
| ` M` | `docs/archive/INDEX.md` | SAFE_TO_COMMIT |
| `??` | `docs/archive/README_LEGACY_SEARCHFORGE_LAB.md` | SAFE_TO_COMMIT |
| `??` | `docs/archive/broker_demo/` | SAFE_TO_COMMIT |
| `??` | `docs/archive/lab/` | SAFE_TO_COMMIT |
| `??` | `docs/archive/mvp_era/` | SAFE_TO_COMMIT |
| `??` | `docs/archive/p7_reports/` | SAFE_TO_COMMIT |
| `??` | `docs/archive/p9_broker_surface/` | SAFE_TO_COMMIT |
| `??` | `docs/archive/platform/AUTOTUNER_ALG_DELIVERY.md` | SAFE_TO_COMMIT |
| `??` | `docs/archive/platform/AUTOTUNER_DELIVERY_SUMMARY.md` | SAFE_TO_COMMIT |
| `??` | `docs/archive/platform/AutoTuner_ALG_INDEX.md` | SAFE_TO_COMMIT |
| `??` | `docs/archive/platform/AutoTuner_ALG_NOTES.md` | SAFE_TO_COMMIT |
| `??` | `docs/archive/platform/AutoTuner_ALG_QUICK_START.md` | SAFE_TO_COMMIT |
| `??` | `docs/archive/platform/AutoTuner_README.md` | SAFE_TO_COMMIT |
| `??` | `docs/archive/platform/CASE_HANDOFF_MAINLINE_BLUEPRINT.md` | SAFE_TO_COMMIT |
| `??` | `docs/archive/platform/LIGHTWEIGHT_STATE_MACHINE_BLUEPRINT.md` | SAFE_TO_COMMIT |
| `??` | `docs/archive/platform/PLUGIN_ARCHITECTURE_MAP.md` | SAFE_TO_COMMIT |
| ` M` | `docs/archive/platform/README_LAB_INFRA.md` | SAFE_TO_COMMIT |
| `??` | `docs/archive/platform/REAL_CUSTOMER_PACK_BLUEPRINT.md` | SAFE_TO_COMMIT |
| `??` | `docs/archive/platform/SIMULATION_ASSISTANT_SPEED_LAYER_BLUEPRINT.md` | SAFE_TO_COMMIT |
| `??` | `docs/archive/platform/SPEED_ROUTING_MAINLINE_BLUEPRINT.md` | SAFE_TO_COMMIT |
| `??` | `docs/archive/platform/STAGE_1_SERVICE_RECORD_DB_BLUEPRINT.md` | SAFE_TO_COMMIT |
| `??` | `docs/archive/platform/TRUSTED_ASSISTANT_PLATFORM_BLUEPRINT.md` | SAFE_TO_COMMIT |
| `??` | `docs/archive/platform/UNIFIED_INTAKE_MASTER_BLUEPRINT.md` | SAFE_TO_COMMIT |
| `??` | `docs/archive/platform_future/` | SAFE_TO_COMMIT |
| ` M` | `docs/archive/root_archaeology/INDEX.md` | SAFE_TO_COMMIT |
| `??` | `docs/archive/sprint_reports/` | SAFE_TO_COMMIT |
| `??` | `docs/archive/sprints/` | SAFE_TO_COMMIT |

### SOURCE CODE — 24 paths

| Status | Path | Safety |
|--------|------|--------|
| ` M` | `services/fiqa_api/app_main.py` | REVIEW_REQUIRED |
| ` M` | `services/fiqa_api/db/service_record_repository.py` | REVIEW_REQUIRED |
| ` M` | `services/fiqa_api/deployment_profile.py` | REVIEW_REQUIRED |
| ` M` | `services/fiqa_api/health/ready.py` | REVIEW_REQUIRED |
| ` D` | `services/fiqa_api/inbox_triage/active_vehicle_resolver.py` | REVIEW_REQUIRED |
| ` M` | `services/fiqa_api/inbox_triage/case_store.py` | REVIEW_REQUIRED |
| ` M` | `ui/src/App.tsx` | REVIEW_REQUIRED |
| ` M` | `ui/src/api/clientConfig.ts` | REVIEW_REQUIRED |
| ` M` | `ui/src/api/inboxTriage.ts` | REVIEW_REQUIRED |
| ` M` | `ui/src/api/request.ts` | REVIEW_REQUIRED |
| `??` | `ui/src/components/intake/CustomerIntakeProgressSummary.tsx` | REVIEW_REQUIRED |
| ` M` | `ui/src/components/intake/UserCaseListProgressPanel.tsx` | REVIEW_REQUIRED |
| `??` | `ui/src/components/intake/customerPortalPresentation.tsx` | REVIEW_REQUIRED |
| ` M` | `ui/src/components/layout/AppSider.tsx` | REVIEW_REQUIRED |
| `??` | `ui/src/components/layout/LabDevBanner.tsx` | REVIEW_REQUIRED |
| ` M` | `ui/src/features/intake/components/BrokerWorkbenchTab.tsx` | REVIEW_REQUIRED |
| ` M` | `ui/src/features/intake/components/CustomerEntryTab.tsx` | REVIEW_REQUIRED |
| ` M` | `ui/src/features/intake/components/MyRequestsTab.tsx` | REVIEW_REQUIRED |
| ` M` | `ui/src/features/intake/components/WorkbenchSummary.tsx` | REVIEW_REQUIRED |
| ` M` | `ui/src/features/intake/constants/index.ts` | REVIEW_REQUIRED |
| ` M` | `ui/src/features/intake/types/index.ts` | REVIEW_REQUIRED |
| ` M` | `ui/src/features/intake/utils/intakePure.ts` | REVIEW_REQUIRED |
| ` M` | `ui/src/pages/UnifiedIntakePage.tsx` | REVIEW_REQUIRED |
| ` M` | `ui/src/vite-env.d.ts` | REVIEW_REQUIRED |

### CONFIGS — 23 paths

| Status | Path | Safety |
|--------|------|--------|
| ` M` | `Dockerfile.ecommerce` | REVIEW_REQUIRED |
| ` M` | `Dockerfile.jobhunter` | REVIEW_REQUIRED |
| ` M` | `Makefile` | REVIEW_REQUIRED |
| ` M` | `README.md` | REVIEW_REQUIRED |
| `??` | `agents/README.md` | REVIEW_REQUIRED |
| ` M` | `configs/clients/chen_kui/ui_copy.json` | REVIEW_REQUIRED |
| ` M` | `configs/industries/insurance/markers.json` | REVIEW_REQUIRED |
| `??` | `configs/p16y_50_cases.json` | REVIEW_REQUIRED |
| `??` | `configs/p16z20_add_car_customers.json` | REVIEW_REQUIRED |
| `??` | `configs/p16z235_add_car_customers.json` | REVIEW_REQUIRED |
| `??` | `configs/p16z24_add_car_customers.json` | REVIEW_REQUIRED |
| `??` | `configs/role_d_claims_battery.json` | REVIEW_REQUIRED |
| `??` | `configs/role_d_journeys.json` | REVIEW_REQUIRED |
| `??` | `docker-compose.product.yml` | REVIEW_REQUIRED |
| ` M` | `docker-compose.yml` | REVIEW_REQUIRED |
| `??` | `engines/README.md` | REVIEW_REQUIRED |
| `??` | `experiments/README.md` | REVIEW_REQUIRED |
| ` M` | `jobhunter-clipper/README.md` | REVIEW_REQUIRED |
| ` M` | `k8s/README.md` | REVIEW_REQUIRED |
| `??` | `mcp/README.md` | REVIEW_REQUIRED |
| `??` | `ml_models/README.md` | REVIEW_REQUIRED |
| `??` | `modules/autotuner/README.md` | REVIEW_REQUIRED |
| `??` | `orchestrators/README.md` | REVIEW_REQUIRED |

### UNKNOWN — 4 paths

| Status | Path | Safety |
|--------|------|--------|
| ` D` | `"docs/\347\224\265\345\225\206\345\224\256\345\220\216Agent_\344\273\243\347\240\201\350\265\204\344\272\247\345\213\230\346\237\245\346\212\245\345\221\212.md"` | REVIEW_REQUIRED |
| `??` | `pipelines/` | REVIEW_REQUIRED |
| `??` | `ui/src/features/intake/prototypes/` | REVIEW_REQUIRED |
| `??` | `ui/src/routes/` | REVIEW_REQUIRED |

### GENERATED FILES — 3 paths

| Status | Path | Safety |
|--------|------|--------|
| ` M` | `configs/demo.env.example` | DO_NOT_COMMIT |
| ` D` | `demo_brain_report.html` | DO_NOT_COMMIT |
| `??` | `docs/archive/root_archaeology/demo_brain_report.html` | DO_NOT_COMMIT |

### TESTS — 3 paths

| Status | Path | Safety |
|--------|------|--------|
| ` D` | `tests/test_active_vehicle_resolver.py` | REVIEW_REQUIRED |
| ` M` | `tests/test_deployment_profile.py` | REVIEW_REQUIRED |
| ` M` | `tests/test_operator_surface_collapse.py` | REVIEW_REQUIRED |

