# Real Broker Trial — Start Here

**Product:** Unified Intake broker-office pilot (1 week)  
**Single launch command:** `bash scripts/trial_launch_check.sh`

---

## Do this (founder launch path)

| Step | What |
|------|------|
| 1 | Run `bash scripts/trial_launch_check.sh` — must PASS |
| 2 | Read [`FOUNDER_LAUNCH_NOTES.md`](FOUNDER_LAUNCH_NOTES.md) — say, inspect, collect |
| 3 | Bring [`BROKER_TRIAL_ONE_PAGER.md`](BROKER_TRIAL_ONE_PAGER.md) for broker |
| 4 | Copy [`TRIAL_OBSERVATION_LOG_TEMPLATE.md`](TRIAL_OBSERVATION_LOG_TEMPLATE.md) |
| 5 | Post-trial: [`FIX_NOW_QUEUE_TEMPLATE.md`](FIX_NOW_QUEUE_TEMPLATE.md) → `results/trial_logs/` |

**Support escalation:** [`docs/runbooks/SUPPORT_TRUTH_MAP.md`](../runbooks/SUPPORT_TRUTH_MAP.md) + `bash scripts/summarize_support_posture.sh <URL>`

---

## Alternate entry (execution depth)

`bash scripts/founder_pre_trial_checklist.sh` — runs readiness + prints pre-trial steps.  
Use when rehearsing **before** launch; for **first broker trial**, prefer `trial_launch_check.sh` above.

Deep execution notes: [`FOUNDER_FINAL_TRIAL_NOTES.md`](FOUNDER_FINAL_TRIAL_NOTES.md)

---

## Core specs (verified by `trial_readiness_check.sh`)

These 12 docs must exist — reference when scoping or hardening; **not** day-one reading:

| Doc | Purpose |
|-----|---------|
| [REAL_BROKER_TRIAL_PACKAGE_BLUEPRINT.md](REAL_BROKER_TRIAL_PACKAGE_BLUEPRINT.md) | Package rationale |
| [TRIAL_SCOPE_DEFINITION_SPEC.md](TRIAL_SCOPE_DEFINITION_SPEC.md) | Duration, in/out |
| [TRIAL_SCENARIO_PACK_SPEC.md](TRIAL_SCENARIO_PACK_SPEC.md) | 5 core + 2 extended scenarios |
| [TRIAL_METRICS_SUCCESS_CRITERIA_SPEC.md](TRIAL_METRICS_SUCCESS_CRITERIA_SPEC.md) | Metrics + value questions |
| [BROKER_TRIAL_WORKFLOW_SPEC.md](BROKER_TRIAL_WORKFLOW_SPEC.md) | Broker daily workflow |
| [FOUNDER_TRIAL_NOTES.md](FOUNDER_TRIAL_NOTES.md) | Inspect, pitch, demo |
| [TRIAL_EXECUTION_BLUEPRINT.md](TRIAL_EXECUTION_BLUEPRINT.md) | Last-mile hardening |
| [LAST_MILE_RISK_SPEC.md](LAST_MILE_RISK_SPEC.md) | Trust-breaking risks |
| [FOUNDER_BROKER_TRIAL_RUNBOOK_SPEC.md](FOUNDER_BROKER_TRIAL_RUNBOOK_SPEC.md) | Founder runbook spec |
| [HANDOFF_OFFICE_NEXT_ACTION_SPEC.md](HANDOFF_OFFICE_NEXT_ACTION_SPEC.md) | Office handoff |
| [TRIAL_OBSERVATION_TO_ITERATION_SPEC.md](TRIAL_OBSERVATION_TO_ITERATION_SPEC.md) | Observation → fix queue |
| [FOUNDER_FINAL_TRIAL_NOTES.md](FOUNDER_FINAL_TRIAL_NOTES.md) | Inspect, run, say, watch |

---

## Launch specs (verified by `trial_launch_check.sh`)

| Doc | Purpose |
|-----|---------|
| [TRIAL_LAUNCH_BLUEPRINT.md](TRIAL_LAUNCH_BLUEPRINT.md) | Launch-readiness rationale |
| [TRIAL_LAUNCH_CHECKLIST_SPEC.md](TRIAL_LAUNCH_CHECKLIST_SPEC.md) | Checklist spec |
| [FOUNDER_LAUNCH_NOTES.md](FOUNDER_LAUNCH_NOTES.md) | **Single founder launch entry** |
| [FIX_NOW_QUEUE_TEMPLATE.md](FIX_NOW_QUEUE_TEMPLATE.md) | Post-trial queue template |
| [BROKER_TRIAL_ONE_PAGER.md](BROKER_TRIAL_ONE_PAGER.md) | Broker-facing one-pager |
| [TRIAL_OBSERVATION_LOG_TEMPLATE.md](TRIAL_OBSERVATION_LOG_TEMPLATE.md) | Day-by-day log |

Also: [FIX_NOW_QUEUE_SPEC.md](FIX_NOW_QUEUE_SPEC.md) — fix now/next/defer rules

---

## Optional kickoff deep-dive

[`kickoff/`](kickoff/) — kickoff flow, evidence capture, demo checklist (optional after launch path above).

---

## Archived specs (historical — ignore unless linked from a sprint)

[`archive/specs/`](archive/specs/) — execution outlines, acceptance criteria duplicates, evidence pack templates, baseline audit.

---

## Related

- [`docs/STANDARD_SCENARIO_PACKAGE.md`](../STANDARD_SCENARIO_PACKAGE.md)
- [`docs/CHEN_KUI_TRIAL_PACK.md`](../CHEN_KUI_TRIAL_PACK.md)
- [`docs/ANDY_QUICK_START.md`](../ANDY_QUICK_START.md)
- [`docs/runbooks/OPERATOR_SURFACE.md`](../runbooks/OPERATOR_SURFACE.md)

---

*End of trial index*
