# Guardrails — Broker Assistant

| Doc | Purpose |
|-----|---------|
| [BROKER_DEMO_DRIFT_GUARDRAIL](../BROKER_DEMO_DRIFT_GUARDRAIL.md) | Detect drift: guardrail scripts, what each checks, when to run |
| [UNIFIED_INTAKE_MVP_GUARDRAILS](./UNIFIED_INTAKE_MVP_GUARDRAILS.md) | Unified Intake MVP: scenario pack, output shape, drift detection |
| [BROKER_INBOX_TRIAGE_GUARDRAILS](./BROKER_INBOX_TRIAGE_GUARDRAILS.md) | (Legacy) Inbox triage — superseded by UNIFIED_INTAKE_MVP_GUARDRAILS |

## Scripts

- `scripts/guardrail_broker_demo.sh` — Question consistency, offline pack, workflow hints
- `scripts/guardrail_inbox_triage.sh` — Inbox triage scenario pack, output shape
- `scripts/demo_pre_checklist.sh --strict` — Fail on workflow-hint drift
- `scripts/demo_quick_validate.sh` — Live Q1–Q5 regression
