# Capability Contract 07 — Founder / Operator Control

**Capability:** Founder / Operator Control  
**Version:** V1 Ratified  
**Date:** 2026-05-31  
**Maps to:** Capability Map V1 §7

---

## SECTION 1 — Purpose

Why this capability exists.

Bridge **engine quality** to **broker trust** through guardrails, deploy validation, trial gates, and the founder operational path. Ensures script PASS does not falsely imply broker-ready; ensures prod persistence before payment; ensures guardrail regression blocks bad demos.

Operators and founders run the system; brokers experience the output.

---

## SECTION 2 — Primary User

Who uses it.

| User | Usage |
|------|-------|
| **Founder** (Andy) | Demo, deploy, trial support, Day 7 payment |
| **Operator / engineer** | Guardrail runs, deploy validation, fix-now from trial |
| **Broker** | Indirect — benefits from stable prod and quality gates |

---

## SECTION 3 — Inputs

What enters the capability.

| Input | Source |
|-------|--------|
| Guardrail scripts | `guardrail_inbox_triage.sh`, scenario batteries |
| Deploy validators | `validate_pilot_deploy_env.py`, `deploy_paid_pilot.sh` |
| Trial launch gate | `trial_launch_check.sh` |
| Readiness probes | `/readyz`, `intake_path_ready` |
| Founder path | `FOUNDER_ONE_PATH.md` |
| Observation log | Trial friction → fix-now queue |
| Runtime truth | `CURRENT_PRODUCT_SHAPE.md` |

---

## SECTION 4 — Outputs

What must come out.

| Output | Requirement |
|--------|-------------|
| Guardrail PASS/FAIL | 13/13 before demo/trial |
| Prod deploy validated | Postgres-primary; `/readyz` green |
| Two-gate launch | Script PASS + broker UX checklist PASS |
| Fix-now queue | Top 3 friction from trial log only |
| Case snapshot support | 复制案例快照 for L2 escalation |
| Founder time allocation | 40% trial support, 25% Week 1 UI fixes (P11) |
| Anti-drift enforcement | Reject scope outside constitution |

---

## SECTION 5 — Success Metrics

How success is measured.

| Metric | Target | Source |
|--------|--------|--------|
| Guardrail regression | 13/13 PASS weekly pre-trial | guardrail script |
| Prod `/readyz` | intake_path_ready before Day 0 | CURRENT_PRODUCT_SHAPE |
| Script vs UX gate | Both PASS before broker URL sent | P14-A two-gate model |
| Fix-now discipline | Top 3 only from trial evidence | Founder rules |
| Deploy uptime | No business-hours outage during trial | Observation log |
| Founder response | 24h L1 commitment in pilot terms | Payment blockers |

---

## SECTION 6 — Acceptance Criteria

How we know it works.

- [ ] `guardrail_inbox_triage.sh` PASS before any broker demo  
- [ ] `trial_launch_check.sh` PASS before Day 0  
- [ ] Broker UX launch checklist PASS (dry-run UI walkthrough)  
- [ ] `validate_pilot_deploy_env.py` PASS + prod `/readyz` before trial  
- [ ] Founder dry-run with observation log catches doc/UI gaps  
- [ ] No SIM1–SIM3 references in broker-facing materials  
- [ ] Fix-now queue limited to top 3 trial friction items  
- [ ] Stale RAG goal docs flagged/deprecated for agents  

---

## SECTION 7 — Current State

Score **0–100** today.

### Score: **68 / 100**

| Dimension | Score | Notes |
|-----------|-------|-------|
| Guardrail scripts | 90 | 13/13; automated regression |
| Founder path docs | 85 | FOUNDER_ONE_PATH, TRIAL_ONE_PATH mature |
| Trial launch script | 80 | PASS; still prints SIM leaks |
| Deploy validation | 55 | `.env.cloudrun` not prod-validated in checks |
| Broker UX gate | 30 | Missing formal checklist beyond script |
| Prod readiness | 55 | Strong docs; incomplete prod probe |
| Anti-scope discipline | 65 | SIMPLIFICATION clear; stale RAG goals remain |
| Support tooling | 70 | Case snapshot exists; under-promoted |

**Founder review:** Documentation convergence 70/100; deployment 55/100.

---

## SECTION 8 — Gap Analysis

What's missing.

| Gap | Severity |
|-----|----------|
| Script PASS ≠ broker-ready (no UX gate) | **P0** |
| Prod deploy not validated before trial | **P0** |
| SIM1–SIM3 in operator scripts leak to brokers | **P1** |
| Stale RAG goal docs mislead agents (AGENTS.md path) | **P1** |
| `.env.cloudrun` production validation SKIP | **P1** |
| Broker UX launch checklist not formalized | **P1** |
| 复制案例快照 under-promoted | **P2** |
| Single-founder support bottleneck | **P2** |
| L1 support doc incomplete | **P2** |

---

## SECTION 9 — Top 10 Improvements

Ranked.

| # | Improvement | ROI |
|---|-------------|-----|
| 1 | Formalize broker UX launch checklist (beside trial_launch_check) | Two-gate launch |
| 2 | validate + deploy paid pilot; verify `/readyz` | Persistence trust |
| 3 | Founder dry-run with observation log before Chen Kui Day 0 | Catches gaps |
| 4 | Remove SIM1–SIM3 from broker-facing operator output | Playbook trust |
| 5 | Deprecate/redirect `insurance_paid_pilot_goal.md` for agents | Anti-drift |
| 6 | Update TRIAL_ONE_PATH + playbook: remove Simulation dependency | Doc/UI parity |
| 7 | Promote 复制案例快照 in support section | Faster L2 |
| 8 | Weekly `/readyz` probe during trial month | Uptime confidence |
| 9 | L1 support doc: 24h response + founder WeChat | Payment blocker #19 |
| 10 | Add constitution to PROJECT_DOC_SYSTEM_MAP START HERE | SSOT navigation |

---

## SECTION 10 — Must Not Build

Prevent scope creep.

- Multi-tenant operator dashboard  
- Automated on-call paging system  
- CI/CD platform redesign  
- Repo-wide cleanup sprints during trial month  
- New operator scripts beyond 10-script surface  
- Internal analytics warehouse  
- Agent orchestration platform for ops  
- Self-serve broker admin portal  
- Enterprise SLA monitoring  
- P12/P13 strategy sprints before first payment  

---

*End of Capability Contract 07*
