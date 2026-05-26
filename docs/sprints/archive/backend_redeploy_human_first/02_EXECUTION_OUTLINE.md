# Backend Redeploy for Human-First Entry Flow — Execution Outline

**Sprint:** Backend Redeploy for Human-First Entry Flow

---

## Phase A — Control Docs

1. Sprint Blueprint (`01_SPRINT_BLUEPRINT.md`)
2. Execution Outline (this doc)
3. Acceptance / Operational Criteria (`03_ACCEPTANCE_CRITERIA.md`)

---

## Phase B — Pre-Deploy Validation

### Files to Inspect

- `configs/industries/insurance/markers.json` — payment markers present
- `services/fiqa_api/inbox_triage/triage.py` — human-first logic
- `services/fiqa_api/routes/inbox_triage.py` — soft_route fallback, SOFT_ROUTE_STARTER_REPLIES

### Validation Scripts (run before deploy)

| Script | Purpose |
|--------|---------|
| `PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py` | Inbox triage scenarios |
| `PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py` | Multi-turn simulations |
| `PYTHONPATH=. python3 scripts/audit_state_field_accuracy.py` | State field accuracy |
| `PYTHONPATH=. python3 scripts/verify_speed_routing.py` | Speed routing |
| `bash scripts/guardrail_inbox_triage.sh` | Guardrail |
| `bash scripts/unified_intake_smoke_check.sh` | Unified intake smoke |

**If any fails:** Stop, explain blocker, do not deploy.

---

## Phase C — Backend Redeploy

```bash
bash scripts/deploy_rag_demo.sh
```

**Capture:** success/failure, backend URL, revision, warnings/errors, health results.

---

## Phase D — Post-Deploy Verification

| Check | Endpoint / Action |
|-------|-------------------|
| Health | `curl <URL>/healthz` |
| Readiness | `curl <URL>/readyz` |
| Payment case | `POST /api/inbox/triage` with "付款有问题" |
| Quote case | `POST /api/inbox/triage` with "我才买了一个2026年的丰田花冠，大约半年的保费是多少？" |
| Missing-doc case | `POST /api/inbox/triage` with "我上周已经发过了，怎么还在追材料？" |

---

## Phase E — Optional Second Loop

Only if one small, high-value, low-risk issue revealed. Do NOT broaden scope.

---

## Phase F — Final Report

- Backend live or not
- Latest logic live or not
- Can founder test on Vercel now
- Biggest remaining risk
- Exact next frontend checks

---

## Likely Loop Count

- **Minimum:** 1 (deploy + verify)
- **Maximum:** 2 (if one small fix needed)
