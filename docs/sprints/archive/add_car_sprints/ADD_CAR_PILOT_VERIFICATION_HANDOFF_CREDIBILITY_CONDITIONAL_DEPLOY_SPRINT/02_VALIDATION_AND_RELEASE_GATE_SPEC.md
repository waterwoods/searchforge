# Validation & release gate spec

## A. Customer-path validation

| Criterion | “Pass” signal |
|-----------|----------------|
| Add-Car entry clear | Hero / quick-start / structured lane present; copy states flagship path (`ui_copy.json`, `UnifiedIntakePage.tsx`). |
| Intake believable | Multi-turn Add-Car simulations complete without incoherent state; progress + submit CTA align with “报送”. |
| Next step understood | Post-handoff sections: result card, service record id, office timing, “无需重复” style reassurance where configured. |
| Service record feel | Closure headline + received summary + `broker_next_step` visible when engine provides them. |

## B. Handoff credibility validation

| Criterion | “Pass” signal |
|-----------|----------------|
| Office “received” | Copy: 办公室已收到 / 已提交办公室处理; toast + closure narrative. |
| `already_sent` / 我发过了 | `follow_up_type` already_sent paths; reply templates (`reply_templates.json`) + triage branches (`triage.py`); broker stress BS7, BS11, HT13, MT29, ACE03, LC-D1, etc. pass in guardrail. |
| 无需重复 trust | `handoff_closure_processing_add_car` and post-handoff thread hint deemphasize re-repeating submitted content. |
| Office next action | `broker_next_step` populated on handoff paths in scenarios. |

## C. Office/workbench continuity validation

| Criterion | “Pass” signal |
|-----------|----------------|
| Same record narrative | Workbench subtitle + queue card + case id hint align with customer closure (`office_workbench_*`, `add_car_case_record_id_label`). |
| State / next step | Queue preview uses `broker_next_step`; customer side shows status strip / result card when Add-Car. |
| Practical continuity | Same `case_id` from API for append/saved cases (persistence scripts in guardrail). |

## D. Release-readiness validation

| Criterion | “Pass” signal |
|-----------|----------------|
| Friend/broker safe to try | Guardrail `scripts/guardrail_inbox_triage.sh` PASS; no known regression on Add-Car + already_sent + append boundary. |
| Acceptable pilot limits | JSON persistence, limited auth/PII — explicit in `PROJECT_TRUTH_SWITCH.md`; not hidden from pilot. |
| Release-blocking | Any guardrail FAIL, broken handoff on happy path, or false already_sent on common Add-Car turns. |

## Deployment decision rule

- **PASS** → May deploy frontend + backend; verify health/readiness after deploy.
- **PASS WITH CAUTIONS** → May deploy with written pilot boundaries; do not claim production SaaS maturity.
- **FAIL** → Do **not** deploy; list minimum fixes.

**Operational rule:** Do not claim deployment success unless commands actually complete and post-deploy checks are recorded. Missing credentials or skipped steps must be stated explicitly.
