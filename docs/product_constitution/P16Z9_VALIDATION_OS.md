# P16-Z9 Phase 8 — Validation Operating System

**Date:** 2026-06-02  
**Sprint:** P16-Z9 SSOT Consolidation  
**Integrates:** Role D (P16-Z7) · Claims battery · Observation log · P16-Y · Guardrail

---

## Validation stack (run order)

```
1. guardrail_inbox_triage.sh     ← API + scenario smoke (every PR)
2. trial_launch_check.sh         ← pre-trial / pre-demo (includes append sim when wired)
3. run_p16y_case_battery.py      ← single-turn intelligence ≥88
4. run_role_d_memory_battery.py  ← multi-day memory reread ≥80, needs_wechat ≤2/10
5. Observation log (founder)     ← commercial proof (3+ real multi-turn cases)
```

**Rule:** Skip no step when touching `triage.py`, append UX, or BrokerWorkbenchTab.

---

## Layer 1 — Guardrail (continuous)

| Script | Path | When |
|--------|------|------|
| `guardrail_inbox_triage.sh` | `scripts/operator/` | Pre-merge, pre-demo |
| `demo_pre_checklist.sh` | `scripts/` | Local demo |
| `test_inbox_triage_api.py` | `scripts/` | API contract |

**Gate:** PASS required for any intake change.

---

## Layer 2 — Trial launch (pre-Chen Kui)

| Script | Adds beyond guardrail |
|--------|----------------------|
| `trial_launch_check.sh` | Deploy env, readiness, append sim (Z4/Z6) |
| `trial_readiness_check.sh` | Supporting — not duplicate pre-trial if launch check used |
| `validate_pilot_deploy_env.py` | Postgres / product_only profile |

**Gate:** FP-004 off, cold URL, append path exercised.

---

## Layer 3 — P16-Y single-turn battery

| Asset | Purpose |
|-------|---------|
| `scripts/run_p16y_case_battery.py` | 50-case regression |
| `configs/p16y_50_cases.json` | Fixtures |
| `P16Y_RUBRIC.md` | Scoring |

| Metric | Threshold | Blocks |
|--------|-----------|--------|
| Overall avg | **≥88** | Deploy if engine change |
| Y44, Y45 | **≥85** each | Append/summary changes |
| Regressions | **0** new failures | Any triage edit |

**When:** Every `triage.py` / classification change.

```bash
LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_p16y_case_battery.py
```

---

## Layer 4 — Role D multi-day battery (P16-Z7)

| Asset | Purpose |
|-------|---------|
| `scripts/run_role_d_memory_battery.py` | 10 journeys × 3 days |
| `configs/role_d_journeys.json` | Office scenarios D01–D10 |
| `configs/role_d_claims_battery.json` | Claims CL01–CL10 |
| `ROLE_D_*.md` | Phase reports |
| `.role_d_results/role_d_battery.json` | Machine output |

### Primary metrics

| Metric | Baseline (Z7) | Target (post-Z8) | Meaning |
|--------|---------------|-------------------|---------|
| Memory score | 60.7/75 | ≥65 | End-state case quality |
| Reread score | 68.9/100 | **≥80** | Broker-readable without WeChat |
| Needs WeChat | 4/10 journeys | **≤2/10** | Commercial claim |
| Category match | 5/10 | ≥7/10 | Lane stability |

### Journey tiers (prioritize fixes)

| Tier | IDs | Notes |
|------|-----|-------|
| Must pass | D08, D09, D04, D05 | Premium, correction, UW, claim |
| Must fix | D10, D07, D01, D02 | Payment, remove-car |
| Claims critical | CL01, CL02, CL05 | FNOL, total loss, mixed pivot |

```bash
LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_role_d_memory_battery.py
```

**When:** After deploy of Z6 UI; after Z8 engine slice; weekly during trial.

---

## Layer 5 — Claims battery (integrated in Role D)

| Source | Scope |
|--------|-------|
| `ROLE_D_CLAIMS_REPORT.md` | CL01–CL10 stress |
| `P16Z6_CLAIMS_VALIDATION.md` | Engine-only C1–C10 |
| `P16Z8_CLAIMS_MEMORY.md` | Field extensions plan |

| Metric | Baseline | Target |
|--------|----------|--------|
| Keyword retention Turn 2+ | 36% | ≥50% |
| Turn 1 FNOL | Ready | Maintain |
| `waiting_on: carrier` | 0% auto | Heuristic suggest 5/9 phrases |

**Rule:** Do not maintain separate claims runner — extend `role_d_claims_battery.json` only.

---

## Layer 6 — Observation log (commercial validation)

| Requirement | Detail |
|-------------|--------|
| **What** | Real broker cases: case_id, turns, time saved, WeChat re-read? Y/N |
| **When** | Day 0 supervised + 3× unsupervised two-turn minimum before "GO" |
| **Who** | Founder |
| **Where** | `docs/trial/` templates + spreadsheet per trial INDEX |

### Observation log fields (minimum)

| Field | Purpose |
|-------|---------|
| `case_id` | Traceability |
| `turns` | 1 vs 2+ |
| `lane` | cancel / payment / claim / add-car |
| `reopened_wechat` | Y/N — Role D proxy |
| `time_saved_min` | ROI evidence |
| `deploy_url` | Proves not local-only |

**Gate:** 3 logged multi-turn cases with `reopened_wechat=N` before marketing memory claims.

---

## Role D integration workflow

```
Deploy change
     │
     ▼
guardrail PASS
     │
     ▼
p16y ≥88 (if engine)
     │
     ▼
role_d battery ──► update ROLE_D_FOUNDER_SUMMARY.md scores
     │
     ├── reread ≥80 AND needs_wechat ≤2/10 ──► GO commercial
     │
     └── fail ──► map failures to Z8 domain (payment/remove/merge/waiting/claims)
                    │
                    ▼
              engine slice (max 3 days) ──► re-run role_d only
                    │
                    ▼
              founder 3 real cases in observation log
```

---

## CI recommendation (not implemented in Z9)

| Check | Trigger |
|-------|---------|
| guardrail | every PR |
| p16y ≥88 | triage.py / markers.json |
| role_d | nightly on main + manual pre-release |

---

## Validation SSOT files

| File | Update when |
|------|-------------|
| `ROLE_D_FOUNDER_SUMMARY.md` | Each battery run |
| `.role_d_results/role_d_battery.json` | Committed after official runs |
| `P16Z9_FOUNDER_SUMMARY.md` | Quarterly or post-major ship |
| `CASE_INTELLIGENCE_MATURITY_MODEL.md` | L5 gate when Role D sustained ≥80 |

---

## What validation explicitly does NOT include

| Excluded | Why |
|----------|-----|
| 10+ add-car lab batteries | OPERATOR_IGNORE_LIST |
| SimulationAssistant scenarios | Orphan |
| Local-only manual paste | Constitution FP-008 |
| LLM path by default | Rules-first pilot |

---

*End of P16-Z9 Phase 8 — Validation Operating System*
