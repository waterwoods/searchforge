# Docs Clarity + Archive Boundary Report

**Sprint:** Docs Clarity + Archive Boundary  
**Date:** 2026-03-07  
**Scope:** California Auto Insurance Broker Assistant only

---

## 1. Primary docs

| Doc | Purpose |
|-----|---------|
| `AGENTS.md` | Single entry point for agents |
| `docs/PROJECT_DOC_SYSTEM_MAP.md` | Full doc map with PRIMARY markers |
| `docs/goals/insurance_paid_pilot_goal.md` | Master goal, scope, deliverables |
| `docs/ANDY_QUICK_START.md` | One file before running demo |
| `docs/ANDY_2MIN_BEFORE_DEMO.md` | 2-min pre-demo checklist |
| `docs/ANDY_IF_SOMETHING_GOES_WRONG.md` | Troubleshooting |
| `docs/runbooks/BROKER_VALUE_VALIDATION_MEETING_PACK.md` | Broker meeting runbook |
| `docs/runbooks/RUNTIME_PATH_STANDARD.md` | Port 8001/8000, recovery |
| `docs/BROKER_DEMO_QUALITY_STANDARD.md` | Quality bar before demo |
| `docs/BROKER_DEMO_DRIFT_GUARDRAIL.md` | Drift detection |
| `docs/business_rules/insurance_broker_pilot_rules.md` | Business rules |
| `docs/release/insurance_demo_gate_v1.md` | Release gate |

---

## 2. Historical/archive docs

**Moved to `docs/archive/`** (40 files):

- AGENT_ENTRY_EFFECTIVENESS_VERIFICATION_REPORT.md
- AGENT_ENTRY_POINT_INTEGRATION_SPRINT_REPORT.md
- DOCUMENTATION_OPERATING_SYSTEM_V1_REPORT.md
- LIVE_WORKFLOW_DEPTH_ACTIVATION_VERIFICATION_REPORT.md
- RUNTIME_PATH_STANDARDIZATION_SPRINT_REPORT.md
- BROKER_GUARDRAIL_DRIFT_SPRINT_REPORT.md
- BROKER_VALUE_VALIDATION_MEETING_PREP_REPORT.md
- BROKER_WORKFLOW_HELPER_SPRINT_REPORT.md
- BROKER_WORKFLOW_DEPTH_SPRINT_REPORT.md
- INSURANCE_AUTONOMOUS_RECOVERY_REPORT.md
- OFFLINE_SNAPSHOT_ALIGNMENT_SPRINT_REPORT.md
- INSURANCE_DEMO_REVALIDATION_REPORT.md
- BROKER_LONGTAIL_QUESTION_EXPANSION_REPORT.md
- COPY_TO_CLIENT_GUARDRAIL_SPRINT_REPORT.md
- INSURANCE_DEMO_EXECUTION_UPDATE.md
- SR22_PROOF_ACTIVATION_VERIFICATION_REPORT.md
- DEMO_EXCERPT_AND_PORT_FIX.md
- UNIFIED_BROKER_VALIDATION_SPRINT_REPORT.md
- WORKFLOW_ACTIVATION_PRESENTATION_SPRINT_REPORT.md
- DEMO_UI_ENHANCEMENT_REPORT.md
- INSURANCE_AUTONOMOUS_PROGRESS_REPORT_2.md
- ONLINE_QDRANT_CORPUS_STRENGTHENING_REPORT.md
- PILOT_READINESS_CONSOLIDATION_SPRINT_REPORT.md
- BROKER_ANSWER_ROBUSTNESS_SPRINT_REPORT.md
- INSURANCE_503_ROOT_CAUSE_REPORT.md
- QDRANT_CONFIG_DISCOVERY_REPORT.md
- AUTONOMOUS_SPRINT_Q4_REPORT.md
- INSURANCE_BROKER_DEMO_OPERATIONS_PACKAGE.md
- FINAL_READINESS_RISK_SWEEP_REPORT.md
- BROKER_PILOT_CORE_REPORT.md
- BROKER_VALUE_VALIDATION_REPORT.md
- INSURANCE_LIVE_OFFLINE_DEMO_RECOVERY_REPORT.md
- CURATED_CORPUS_REVALIDATION_REPORT.md
- BUSINESS_VALUE_TIGHTENING_SPRINT_REPORT.md
- LIVE_READINESS_RECOVERY_SPRINT_REPORT.md
- AUTO_INSURANCE_DIAGNOSIS_REPORT.md
- SR22_PROOF_OF_INSURANCE_VALUE_SPRINT_REPORT.md
- WSL_MEMORY_UNLOCK_REPORT.md
- OPENCLAW_STEP2_SMOKETEST.md
- OPENCLAW_MVP_SMOKETEST_RESULT.md
- OFFLINE_WORKFLOW_DEMO_PATH_SPRINT_REPORT.md
- INSURANCE_PAID_PILOT_READINESS_REPORT.md

**Index:** `docs/archive/INDEX.md` explains purpose; points back to PROJECT_DOC_SYSTEM_MAP for current docs.

---

## 3. Low-value deletion candidates

**Do NOT delete yet.** Mark as candidates for future review:

| Doc | Why candidate |
|-----|---------------|
| `docs/langsmith_implementation_summary.md` | Possible duplicate of LANGSMITH_IMPLEMENTATION_SUMMARY.md (different case); unreferenced |
| `docs/CHECKLIST_PROMPT1.md` | Prompt-specific; likely superseded; verify no references |
| `docs/CURSOR_PROMPT_STEP5B_REVIEW.md` | One-time review; verify no references |

**Out of scope (not broker):** PROMPT*, OPERATOR_STEP*, STEP3*, STEP4*, STEP5*, jobhunter/*, vitals_*, ops_*, k8s_*, langsmith_*, etc. — left as-is.

---

## 4. Changes made

| File | Change | Why |
|------|--------|-----|
| `docs/archive/` | Created; 40 historical reports moved | Separate current from historical |
| `docs/archive/INDEX.md` | New | Explains archive purpose |
| `docs/PROJECT_DOC_SYSTEM_MAP.md` | Added PRIMARY table, archive section, updated reports path | Clarify source of truth |
| `docs/BROKER_REPORTS_INDEX.md` | New (replaces reports/INDEX.md for git) | reports/ is gitignored; index now in docs/ |
| `AGENTS.md` | Reports row → docs/BROKER_REPORTS_INDEX.md, archive pointer | Correct path; discoverability |
| `reports/INDEX.md` | Simplified; points to docs/BROKER_REPORTS_INDEX.md | Local use; reports/ gitignored |
| `scripts/guardrail_broker_demo.sh` | docs/RUNTIME_PATH_STANDARD.md → docs/runbooks/RUNTIME_PATH_STANDARD.md | Fix stale path |
| `scripts/restore_8001_readiness.sh` | Same path update | Consistency |
| `scripts/demo_pre_checklist.sh` | Same path update | Consistency |
| `scripts/dev_local.sh` | Same path update | Consistency |

---

## 5. Clarity result

| Aspect | Before | After |
|--------|--------|-------|
| Primary vs historical | Mixed in docs/ root | PRIMARY table in map; archive/ holds historical |
| Reports index | reports/INDEX.md (gitignored) | docs/BROKER_REPORTS_INDEX.md (in git) |
| Entry path | AGENTS.md → PROJECT_DOC_SYSTEM_MAP | Same; map now has explicit PRIMARY section |
| Runtime path refs | Some pointed to wrong path | All scripts use docs/runbooks/RUNTIME_PATH_STANDARD.md |

**Result:** Better. A new human or agent can tell:
- PRIMARY = PROJECT_DOC_SYSTEM_MAP § PRIMARY table
- Historical = docs/archive/
- Reports index = docs/BROKER_REPORTS_INDEX.md

---

## 6. Remaining confusion

- **PROMPT* / OPERATOR* / STEP* docs** — Many in docs/ root; not broker-specific; out of scope. Still mixed with broker docs.
- **Multiple meeting/demo docs** — BROKER_MEETING_PACKAGE, BROKER_DEMO_OPERATOR_RUNBOOK, BROKER_DEMO_SCRIPT_15MIN, BROKER_DEMO_CHECKLIST overlap. Map says BROKER_VALUE_VALIDATION_MEETING_PACK is primary; others are lighter. Could consolidate in future.
- **Out-of-scope docs** — jobhunter, vitals, ops, k8s, langsmith, etc. live in docs/; no separate folder. Low priority.

---

## 7. Recommended next step

**One clear next step:** Before the next broker demo, run `bash scripts/demo_pre_checklist.sh` and open `docs/ANDY_2MIN_BEFORE_DEMO.md`. Verify the doc path feels clear. If PROMPT/OPERATOR/STEP docs cause confusion, consider a future sprint to move them to `docs/other/` or similar.

---

*End of report*
