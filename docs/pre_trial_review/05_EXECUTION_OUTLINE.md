# Pre-Trial Review Execution Outline

**Sprint:** Pre-Trial Review Sprint  
**Created:** 2026-03-18

---

## 1. Execution Mode

- **Document-driven review** + 2–3 loops of audit / classify / tighten
- **Target budget:** 25–50 minutes
- **Flow:** blueprint → review → classify → tighten → summarize

---

## 2. Workstreams

| # | Workstream | Steps |
|---|------------|-------|
| 1 | Control docs | Create 7 review docs |
| 2 | System review | Read scenario package, trial pack, logic center, guardrail results |
| 3 | Loop 1: Scenario readiness | Classify each scenario strong/medium/weak |
| 4 | Loop 2: Fix queue | Fix-now / fix-next / defer |
| 5 | Loop 3: First trial scope | Define 3–5 flows; include/exclude |
| 6 | Report | Pre-Trial Review Report + 中文宏观总结 |

---

## 3. Loop Plan

| Loop | Focus | Output |
|------|-------|--------|
| 1 | Scenario readiness | Per-scenario judgment |
| 2 | Fix queue | Practical grouped list |
| 3 | First trial scope | Exact flows to include/exclude |

---

## 4. Test Plan

| Check | Command |
|-------|---------|
| Guardrail | `bash scripts/guardrail_inbox_triage.sh` → PASS |
| Trial launch | `bash scripts/trial_launch_check.sh` → PASS |
| Demo | `bash scripts/run_demo_local.sh` |

---

*End of Execution Outline*
