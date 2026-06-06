> **HISTORICAL / ARCHIVE — P9 Broker Surface Collapse (2026-05-30)**
> **Read instead:** [`docs/TRIAL_ONE_PATH.md`](../../../TRIAL_ONE_PATH.md)

# Broker Trial Kickoff — Execution Outline

**Sprint:** Broker Trial Kickoff Readiness Sprint  
**Created:** 2026-03-18  
**Purpose:** Describe workstreams, implementation order, loop plan, and validation approach.

---

## 1. Workstreams

| Workstream | Owner | Deliverables |
|------------|-------|--------------|
| **Kickoff path** | Planner | Single entry; founder checklist; broker day-1 flow |
| **Evidence / issue capture** | Evidence worker | Capture structure; classification rules; fix-now template |
| **Demo / checklist** | Trial workflow worker | First 5–10 min demo; minimal flows; blockers |
| **Acceptance** | Release reviewer | Launch criteria; acceptable to defer |

---

## 2. Implementation Order

1. **Phase A** — Create control doc stack (Blueprint, Flow Spec, Evidence/Issue Spec, Demo/Checklist Spec, Execution Outline, Acceptance Criteria, Founder Final Kickoff Notes)
2. **Phase B** — Baseline audit (kickoff readiness, blockers, evidence weakness, issue-classification weakness)
3. **Phase C** — Loop 1: Single kickoff path
4. **Phase C** — Loop 2: Evidence / issue capture tightening
5. **Phase C** — Loop 3: Small final hardening
6. **Phase D** — Final convergence; deployment judgment

---

## 3. Loop Plan

| Loop | Target | Validation |
|------|--------|------------|
| **Loop 1** | Single kickoff path; founder path obvious; broker day-1 flow obvious | trial_launch_check.sh; run_demo_local.sh |
| **Loop 2** | Evidence capture useful; issue queue easier to fill; fix-now/fix-next/defer practical | FIX_NOW_QUEUE_TEMPLATE; trial_logs README |
| **Loop 3** | Reduce one last confusing element; improve one final founder/broker usability point | UI build; guardrail |

---

## 4. Validation Approach

| Check | When |
|-------|------|
| trial_launch_check.sh | After each loop |
| guardrail_inbox_triage.sh | After loop 1 |
| UI build | If UI touched |
| unified_intake_smoke_check.sh | Optional; requires live server |

---

*End of Execution Outline*
