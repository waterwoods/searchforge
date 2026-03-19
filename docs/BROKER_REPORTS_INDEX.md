# Broker Reports Index

Broker-related sprint and diagnosis reports. **Current** = still useful for reference. **Archive** = historical; see `docs/archive/`.

---

## Current (in docs/)

| Report | Purpose |
|--------|---------|
| [Client Identity Persistence Sprint Report](./sprints/CLIENT_IDENTITY_PERSISTENCE/CLIENT_IDENTITY_PERSISTENCE_SPRINT_REPORT.md) | client_id on cases; append/reopen use case.client_id; end-to-end A→B lifecycle; 7 control docs; Loop 1–3 |
| [Broker Trial Kickoff Readiness Sprint Report](./BROKER_TRIAL_KICKOFF_READINESS_SPRINT_REPORT.md) | Kickoff-ready: 7 kickoff docs; trial_launch_check prints kickoff pointer; first 3–5 flow; Map-to; trust-breaking vs acceptable; Loop 1–3 |
| [Trial Launch + Fix-Now Queue Sprint Report](./TRIAL_LAUNCH_FIX_NOW_QUEUE_SPRINT_REPORT.md) | Launch-ready: trial_launch_check.sh single entry; FIX_NOW_QUEUE_TEMPLATE; Copy case snapshot; 9 control docs; Loop 1–3 |
| [Trial Execution Readiness + Last-Mile Hardening Report](./TRIAL_EXECUTION_READINESS_LAST_MILE_SPRINT_REPORT.md) | Trial execution: founder_pre_trial_checklist.sh; case card Your next move top; observation friction classification; 8 control docs; Loop 1–3 |
| [Real Broker Trial Package Sprint Report](./REAL_BROKER_TRIAL_PACKAGE_SPRINT_REPORT.md) | Real Broker Trial Package: 8+ control docs, trial_readiness_check.sh, founder script, broker one-pager, observation log; 1-week pilot packaging |
| [Sellable Standard Scenario Package Report](./sprints/SELLABLE_STANDARD_SCENARIO_PACKAGE/SELLABLE_STANDARD_SCENARIO_PACKAGE_REPORT.md) | Standard scenario package: 7 core scenarios, canonical STANDARD_SCENARIO_PACKAGE.md, workbench part of package, founder demo path; packaging over new features |
| [Workbench Handoff Readiness Report](./sprints/workbench_handoff_readiness/WORKBENCH_HANDOFF_READINESS_REPORT.md) | Workbench handoff readiness: Recent customer messages, correction/already_sent badges; 7 control docs; Loop 1–2; broker can understand case faster |
| [Multi-Turn Stress Test + Gap Analysis](./sprints/MULTI_TURN_STRESS_TEST_GAP_ANALYSIS_SPRINT_REPORT.md) | Multi-turn scenario stress test: 39 MT + 13 mixed-intent + 23 long-context; strengths/weaknesses; LC-AC3, billing multi-turn; founder test script; pilot-usable |
| [Minimal Production Backbone Master Report](./sprints/minimal_production_backbone/MINIMAL_PRODUCTION_BACKBONE_MASTER_REPORT.md) | Backbone formalization: lifecycle_status coherence, origin_session_id traceability, 8 control docs, pilot-ready foundation |
| [Add-Car Rules Center Ready Deployment](./sprints/add_car_rules_center_ready_deployment/02_EXECUTION_OUTLINE.md) | Rules Center deploy: control docs, pre-deploy PASS, manual deploy steps |
| [FOUNDER_DEMO_SOP_TRIAL_FEEDBACK_REPORT](./FOUNDER_DEMO_SOP_TRIAL_FEEDBACK_REPORT.md) | Founder Demo SOP + Real Trial Feedback: demo path, SOP, top 3 scenarios, feedback questions; Loop 1–2; ready for Chen Kui trial |
| [TURN1_LIGHTWEIGHT_COLDSTART_SPRINT_REPORT](./sprints/TURN1_LIGHTWEIGHT_COLDSTART_SPRINT_REPORT.md) | Turn 1 lightweight first-pass + cold-start mitigation: high-frequency intents use rule path; warmup runbook |
| [CASE_HANDOFF_MAINLINE_SPRINT_REPORT](./CASE_HANDOFF_MAINLINE_SPRINT_REPORT.md) | Case handoff mainline: unified "Case handoff" block; case focus + one-liner at top; Customer Entry handoff moment; Simulation Assistant mirrors Workbench |
| [REAL_CUSTOMER_PACK_MAINLINE_SPRINT_REPORT](./REAL_CUSTOMER_PACK_MAINLINE_SPRINT_REPORT.md) | Real Customer Pack: 8 messy/short/mixed scenarios (R1–R8) in Simulation Assistant; realism blueprint; demo value |
| [LIGHTWEIGHT_STATE_MACHINE_SPRINT_REPORT](./LIGHTWEIGHT_STATE_MACHINE_SPRINT_REPORT.md) | Lightweight state machine, field progress, follow-up type strategy; follow_up_type + collection_stage derivation; SIM1–SIM15 pass |
| [STRUCTURED_OUTPUT_VISIBILITY_BUG_HARVEST_TRIAL_READINESS_SPRINT_REPORT](./STRUCTURED_OUTPUT_VISIBILITY_BUG_HARVEST_TRIAL_READINESS_SPRINT_REPORT.md) | Case focus visibility, queue card case focus, structured-field inference; 15/15 sim pass; Chen Kui trial walkthroughs |
| [SIMULATION_ASSISTANT_SCENARIO_EXPANSION_BUG_HARVEST_SPRINT_REPORT](./SIMULATION_ASSISTANT_SCENARIO_EXPANSION_BUG_HARVEST_SPRINT_REPORT.md) | Simulation Assistant expansion: 15 scenarios (SIM9–SIM15), bug harvest, eval visibility, guardrail step 8 |
| [VISUAL_SIMULATION_ASSISTANT_SPRINT_REPORT](./VISUAL_SIMULATION_ASSISTANT_SPRINT_REPORT.md) | Visual Simulation Assistant: script-driven replay, 8 scenarios, eval tags (Normal/Needs review/Off-flow); QA + demo prep |
| [BROKER_DAILY_USE_END_TO_END_SIMULATION_SPRINT_REPORT](./BROKER_DAILY_USE_END_TO_END_SIMULATION_SPRINT_REPORT.md) | Full broker day simulation: queue → reopen → append → continue; run_daily_use_simulation.py; smoke step 21 |
| [BROKER_DAILY_USE_WORKFLOW_POLISH_SPRINT_REPORT](./BROKER_DAILY_USE_WORKFLOW_POLISH_SPRINT_REPORT.md) | Daily-use polish: "what changed" after append; queue Last update from activity; Just updated badge; Updated tag |
| [PASTE_NEW_MESSAGE_INTO_EXISTING_CASE_SPRINT_REPORT](./PASTE_NEW_MESSAGE_INTO_EXISTING_CASE_SPRINT_REPORT.md) | Paste new customer follow-up into existing case; append-message endpoint; FA1–FA5 simulations |
| [LIGHTWEIGHT_TICKET_FOLLOWUP_UX_SPRINT_REPORT](./LIGHTWEIGHT_TICKET_FOLLOWUP_UX_SPRINT_REPORT.md) | Lightweight ticket/follow-up: Resume here, due-state, last meaningful update, queue Last update |
| [BROKER_CASE_QUEUE_TRIAGE_SPRINT_REPORT](./BROKER_CASE_QUEUE_TRIAGE_SPRINT_REPORT.md) | Broker queue triage: readiness badge, compact flow-specific preview, Work now/Waiting or parked, queue legend |
| [BROKER_WORKFLOW_COHESION_SPRINT_REPORT](./BROKER_WORKFLOW_COHESION_SPRINT_REPORT.md) | Unified broker workflow language; strengthen "Your next move" for add-car, renewal, claim, missing-document; cross-flow consistency |
| [STRUCTURED_WORKBENCH_EXPANSION_SPRINT_REPORT](./STRUCTURED_WORKBENCH_EXPANSION_SPRINT_REPORT.md) | Extend structured intake to renewal + claim; collected/still_needed for premium review and claim intake |
| [BROKER_WORKBENCH_STRUCTURED_INTAKE_UI_SPRINT_REPORT](./BROKER_WORKBENCH_STRUCTURED_INTAKE_UI_SPRINT_REPORT.md) | Broker Workbench: surface collected/still_needed chips for add-car; graceful fallback |
| [FOUNDER_DEMO_QUEUE_LIVE_ROBUSTNESS_PROOF_SPRINT_REPORT](./FOUNDER_DEMO_QUEUE_LIVE_ROBUSTNESS_PROOF_SPRINT_REPORT.md) | Founder demo queue + live robustness: 13 seeds (claim, messy-user, mixed-intent), 3/5/full-tour order, story, cheat sheet |
| [COMPLEX_ADVERSARIAL_SIMULATION_SPRINT_REPORT](./COMPLEX_ADVERSARIAL_SIMULATION_SPRINT_REPORT.md) | Mixed-intent + long-context stress test: 23 scenarios, 5 fixes, claim+payment rule, summary correction/sent hints |
| [ADVERSARIAL_REAL_USER_SIMULATION_SPRINT_REPORT](./ADVERSARIAL_REAL_USER_SIMULATION_SPRINT_REPORT.md) | Adversarial messy-user stress test: 27 scenarios, 8 marker fixes, guardrail extended |
| [FRONT_END_NATURALNESS_PROGRESSION_CONSOLIDATION_SPRINT_REPORT](./FRONT_END_NATURALNESS_PROGRESSION_CONSOLIDATION_SPRINT_REPORT.md) | Front-end consolidation: remove-car acknowledgement + flow-specific handoff; 5 flows more unified; cheat sheet, proof walkthroughs |
| [CUSTOMER_ENTRY_CONVERSATIONAL_UX_SPRINT_REPORT](./CUSTOMER_ENTRY_CONVERSATIONAL_UX_SPRINT_REPORT.md) | Customer Entry conversational UX: add-car acknowledgement + progressive ask; claim empathy; warmer handoff; 5-flow proof |
| [FIVE_BUSINESS_FLOWS_MULTI_TURN_UX_STRESS_SPRINT_REPORT](./FIVE_BUSINESS_FLOWS_MULTI_TURN_UX_STRESS_SPRINT_REPORT.md) | 5 flows multi-turn stress: 29 variants; other_received/other_corrected handoff; renewal, payment, claim, missing doc warmer handoff |
| [FIVE_BUSINESS_FLOWS_VERTICALIZATION_SPRINT_REPORT](./FIVE_BUSINESS_FLOWS_VERTICALIZATION_SPRINT_REPORT.md) | 5 flows verticalized: add car, renewal/premium, **claim intake (new)**, notice/payment, document chase; simulation packs, acceptance criteria |
| [BROKER_HANDOFF_CLARITY_DAILY_CASE_SPRINT_REPORT](./BROKER_HANDOFF_CLARITY_DAILY_CASE_SPRINT_REPORT.md) | Broker handoff clarity guide, Collected/Still needed, daily-use case maturity, regression D1–D4 |
| [MULTI_TURN_CUSTOMER_INTAKE_SIMULATION_REPORT](./MULTI_TURN_CUSTOMER_INTAKE_SIMULATION_REPORT.md) | Multi-turn intake: 12-scenario simulation pack, guardrail coverage, broker handoff quality |
| [UNIFIED_INTAKE_WORKFLOW_MATURITY_SPRINT_REPORT](./UNIFIED_INTAKE_WORKFLOW_MATURITY_SPRINT_REPORT.md) | Unified Intake: case card presentation, smoke-flow helper, future-compatibility placeholders |
| [UNIFIED_INTAKE_MVP_UI_SPRINT_REPORT](./UNIFIED_INTAKE_MVP_UI_SPRINT_REPORT.md) | Unified Intake MVP v1: UI flow (paste → triage → result), quick-fill, runbook update, validation |
| [UNIFIED_INTAKE_MVP_PRODUCT_DEFINITION_REPORT](./UNIFIED_INTAKE_MVP_PRODUCT_DEFINITION_REPORT.md) | Unified Intake MVP v1: product definition, workflow, input/output models, scenarios, boundaries |
| [BROKER_INBOX_TRIAGE_EXECUTION_REPORT](./BROKER_INBOX_TRIAGE_EXECUTION_REPORT.md) | Inbox triage MVP: doc pack, workflow, scenario pack, prototype, guardrails |
| [BROKER_PRIMARY_DOCS_AND_MULTI_AGENT_SPRINT_REPORT](./BROKER_PRIMARY_DOCS_AND_MULTI_AGENT_SPRINT_REPORT.md) | Broker primary docs consolidation; multi-agent operating model v1 |
| [DOCS_CLARITY_ARCHIVE_BOUNDARY_REPORT](./DOCS_CLARITY_ARCHIVE_BOUNDARY_REPORT.md) | Previous sprint: primary vs archive, changes made |
| [DOCS_SECONDARY_CLEANUP_REPORT](./DOCS_SECONDARY_CLEANUP_REPORT.md) | Supporting/ boundary, root noise reduction |
| [CONFIG_EXTRACTION_SPRINT_REPORT](./CONFIG_EXTRACTION_SPRINT_REPORT.md) | Markers + handoff phrases extracted to config |
| [REPLY_TEMPLATE_EXTRACTION_SPRINT_REPORT](./REPLY_TEMPLATE_EXTRACTION_SPRINT_REPORT.md) | add_car, payment_lapse_expiration, missing_document reply templates extracted |
| [CORE_REPLY_TEMPLATE_EXPANSION_SPRINT_REPORT](./CORE_REPLY_TEMPLATE_EXPANSION_SPRINT_REPORT.md) | english_notice_confusion, premium_review, remove_vehicle reply templates extracted |
| [CLIENT_PACK_FOUNDATION_SPRINT_REPORT](./CLIENT_PACK_FOUNDATION_SPRINT_REPORT.md) | Package model: common base → industry pack → client pack; cancellation_warning extracted; config structure |
| [RETRIEVAL_KNOWLEDGE_LAYER_FOUNDATION_SPRINT_REPORT](./RETRIEVAL_KNOWLEDGE_LAYER_FOUNDATION_SPRINT_REPORT.md) | Retrieval boundaries: what goes into RAG vs rules/config; knowledge package model; first slice DMV/SR-22 |
| [KNOWLEDGE_INGESTION_FIRST_LIVE_RETRIEVAL_SPRINT_REPORT](./KNOWLEDGE_INGESTION_FIRST_LIVE_RETRIEVAL_SPRINT_REPORT.md) | First live retrieval: dmv_sr22 ingested into Qdrant; ingestion + validation scripts; retrieval boundary (6a) |
| [RETRIEVAL_FLOW_EXPANSION_SPRINT_REPORT](./RETRIEVAL_FLOW_EXPANSION_SPRINT_REPORT.md) | Second retrieval path: declaration page / garaging proof; 2 retrieval-assisted explanation paths; product proof |

---

## Archive (historical)

All sprint/diagnosis reports have been moved to `docs/archive/`. See [docs/archive/INDEX.md](./archive/INDEX.md).

Examples:
- Documentation Operating System v1
- Agent Entry-Point Integration
- Runtime Path Standardization
- 503 root cause, live/offline recovery
- Broker pilot core, value validation
- Guardrail drift, copy-to-client, workflow depth
- **COPY_TO_CLIENT_UPGRADE_SPRINT_REPORT** — 客户可准备 → 您可准备 dedicated section
- Qdrant config, corpus strengthening
- And 30+ others

---

## Script Outputs

- `results/demo_pre_checklist/` — Pre-demo checklist runs
- `results/demo_quick_validate/` — Validation runs
- `results/auto_insurance/` — Deployment, E2E, secrets reports
Deployment, E2E, secrets reports
eports
Deployment, E2E, secrets reports
