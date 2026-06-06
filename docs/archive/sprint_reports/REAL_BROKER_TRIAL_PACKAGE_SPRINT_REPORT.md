# Real Broker Trial Package Sprint Report

**Sprint:** Real Broker Trial Package Sprint  
**Created:** 2026-03-18  
**Execution mode:** Long-running structured execution

---

## 1. Sprint Theme

**What was chosen:** Turn the strongest product capabilities into a Real Broker Trial Package for a 1-week pilot with a real small insurance broker.

**Why now:** The product has package definition (STANDARD_SCENARIO_PACKAGE), scenario hardening (guardrail passes), and Chen Kui trial pack. The next step is operationalization: packaging, tightening, and validating so a broker can actually try it in real life.

---

## 2. Document Set Created

| Doc | Path |
|-----|------|
| Trial Package Blueprint | docs/trial/REAL_BROKER_TRIAL_PACKAGE_BLUEPRINT.md |
| Trial Scope Definition Spec | docs/trial/TRIAL_SCOPE_DEFINITION_SPEC.md |
| Trial Scenario Pack Spec | docs/trial/TRIAL_SCENARIO_PACK_SPEC.md |
| Trial Metrics / Success Criteria Spec | docs/trial/TRIAL_METRICS_SUCCESS_CRITERIA_SPEC.md |
| Broker Trial Workflow Spec | docs/trial/BROKER_TRIAL_WORKFLOW_SPEC.md |
| Execution Outline | docs/trial/EXECUTION_OUTLINE.md |
| Acceptance / Trial Readiness Criteria | docs/trial/ACCEPTANCE_TRIAL_READINESS_CRITERIA.md |
| Founder Trial Notes | docs/trial/FOUNDER_TRIAL_NOTES.md |
| Trial Package 10-20 Breakdown | docs/trial/TRIAL_PACKAGE_10_20_BREAKDOWN.md |
| Baseline Audit | docs/trial/BASELINE_AUDIT.md |
| Trial Observation Log Template | docs/trial/TRIAL_OBSERVATION_LOG_TEMPLATE.md |
| Founder Trial Script One Pager | docs/trial/FOUNDER_TRIAL_SCRIPT_ONE_PAGER.md |
| Broker Trial One Pager | docs/trial/BROKER_TRIAL_ONE_PAGER.md |
| Trial Index | docs/trial/INDEX.md |

---

## 3. Baseline Audit

**Current Trial Readiness:** Product strong (guardrail passes). Trial package clarity was weak; broker workflow partial; metrics missing. Now addressed.

**Biggest Weakness (Before):** No single Real Broker Trial Package definition.

**Biggest Trial-Value Gap (Before):** No practical template for what to record during trial.

**Biggest Broker Risk (Before):** Unclear workflow: what to do Day 1, how to review handoffs.

---

## 4. 10-20 Point Breakdown

See docs/trial/TRIAL_PACKAGE_10_20_BREAKDOWN.md. Key: Real Broker Trial Package; 5 core scenarios; 1-week; setup via trial_readiness_check.sh; success = 5+ conversations, 3+ scenario types.

---

## 5. Iteration Loop 1

**Fixed:** No single trial package entry point; no trial-readiness check script.

**Why:** Highest trial-readiness gain from minimal change.

**Became coherent:** docs/trial/ as single source; trial_readiness_check.sh validates docs + guardrail + UI.

**Worth it:** Yes.

---

## 6. Iteration Loop 2

**Fixed:** No practical observation log; Broker Day 1 checklist was brief.

**Improved:** TRIAL_OBSERVATION_LOG_TEMPLATE.md; expanded Day 1 checklist.

**Worth it:** Yes.

---

## 7. Iteration Loop 3

**Fixed:** Founder needed short pitch script; Broker needed one-page summary in Chinese.

**Improved:** FOUNDER_TRIAL_SCRIPT_ONE_PAGER.md; BROKER_TRIAL_ONE_PAGER.md; Founder Pre-Trial Checklist.

**Worth it:** Yes.

---

## 8. Optional Loop 4

**Used:** No. Package coherent. Stopping correct.

---

## 9. Validation Summary

run_inbox_triage_scenarios: 64/64. run_multi_turn_simulations: 41/41. guardrail: PASS. trial_readiness_check: PASS. UI build: Pass.

---

## 10. Deployment / Release Judgment

**Backend changed:** No. **Frontend changed:** No. **Redeploy:** Not needed. **Founder can inspect now:** Yes.

---

## 11. Founder Showcase

| Scenario | Customer experience | Broker gets | Measure |
|---------|---------------------|-------------|---------|
| Cancellation risk | Notice -> screenshot -> confusion | Urgent; verify receipt | Same-day action |
| Missing document | Need dec+garaging; sent dec | Structured follow-up | Avoid re-ask |
| Add-car quote | Quote -> year -> zip | Collected chips | Enough to quote |
| Premium review | Too high -> bill -> remove? | Retention follow-up | Act on renewal |
| Claim intake | Accident -> hit-and-run | First-response | Next step |

---

## 12. Final Judgment

**Biggest gain:** Single coherent Real Broker Trial Package with docs, checklist, metrics template, founder script, broker one-pager, trial_readiness_check.sh.

**Biggest remaining weakness:** No inbox sync; broker must manually paste. Acceptable.

**Feels like real broker trial package:** Yes.

**Best next step:** Run trial with real broker; use observation log; gather value validation answers.

---

## 13. Iteration Log

Loop 1: Trial docs, script, links. Worth it. Loop 2: Observation log, Day 1 checklist. Worth it. Loop 3: One-pagers, pre-trial checklist. Worth it. Loop 4: Skipped.

---

## 14. Chinese Summary

**Why:** Product ready; need operational trial package for real broker.

**Method:** Doc-first, 3 loops, minimal change, trial_readiness_check.sh.

**Biggest gain:** Clear Real Broker Trial Package: definition, scope, scenarios, metrics, workflow, founder script, broker one-pager, observation log.

**Still missing:** No inbox sync. Acceptable. Next: real broker trial feedback.

**Next step:** Run 1-week trial; use observation log; iterate.

---

## 15. COPY/PASTE FOUNDER BLOCK

Biggest improvement: Single coherent Real Broker Trial Package with docs, checklist, metrics template, founder script, broker one-pager, trial_readiness_check.sh.

Biggest weakness: No inbox sync; broker must manually paste. Acceptable.

More sellable: Yes. Founder can approach broker with clear package.

Redeploy: No.

Inspect next: docs/trial/; run trial_readiness_check.sh; run_demo_local.sh; open workbench/unified-intake; read FOUNDER_TRIAL_SCRIPT_ONE_PAGER and BROKER_TRIAL_ONE_PAGER.

---

## 16. REQUIRED CROSS-WINDOW BLOCK

Trial-package maturity: Coherent. 8+ docs, trial_readiness_check.sh, founder script, broker one-pager, observation log.

Improvements: Single docs/trial/ entry; trial_readiness_check.sh; Broker Day 1 checklist; Observation log; One-pagers.

Weaknesses: No inbox sync; manual paste. Acceptable.

Direction: Correct.

Best next: Run 1-week trial; use observation log; gather feedback; iterate.

Tech: Python fiqa_api, React/Vite, Qdrant, SQLite. Port 8001/5173. Cloud Run + Vercel.

---

## 17. REQUIRED SHORT OVERVIEW

### Why

Product ready; need operational trial package for real broker.

### Method

Doc-first, 3 loops, minimal change, trial_readiness_check.sh.

### Biggest gain

Clear Real Broker Trial Package: definition, scope, scenarios, metrics, workflow, founder script, broker one-pager, observation log.

### Still missing

No inbox sync. Acceptable. Next: real broker trial feedback.

---

## 18. REQUIRED TIME / EFFORT SUMMARY

### Work done

Phase A: 8+ control docs. Baseline audit. Loop 1: trial docs, script, links. Loop 2: observation log, Day 1 checklist. Loop 3: one-pagers, pre-trial checklist.

### Improvements vs original

Single docs/trial/ entry; trial_readiness_check.sh; observation log; Broker Day 1 flow; Founder + Broker one-pagers.

### Time per loop

Phase A + baseline: ~20 min. Loop 1: ~15 min. Loop 2: ~10 min. Loop 3: ~10 min. Report: ~15 min.

### Next round

Real broker 1-week trial; feedback; iterate; consider inbox integration if requested.
