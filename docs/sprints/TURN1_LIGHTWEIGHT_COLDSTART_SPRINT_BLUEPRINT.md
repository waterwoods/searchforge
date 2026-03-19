# Turn 1 Lightweight First-Pass + Cold-Start Mitigation — Sprint Blueprint

**Sprint:** Turn 1 Lightweight First-Pass + Cold-Start Mitigation Sprint  
**Date:** 2026-03-14  
**Mode:** Practical, high-ROI industrial best-practice mitigations

---

## 1. Why Turn 1 Latency Is the Biggest Blocker Now

- **Observed:** Turn 1 feels 15–20+ seconds in real use
- **Impact:** Trust, first impression, willingness to try, willingness to pay
- **Root cause:** Turn 1 always uses LLM (intent classification) + cold start (5–15 s) + LLM (1.5–5 s)

---

## 2. Why These Two Strategies

| Strategy | Rationale |
|----------|-----------|
| **Lightweight Turn 1 first-pass** | Common/high-frequency first-turn intents (cancellation, payment, missing-doc, add-car short) have clear markers; rule path can classify safely in ~50–200 ms |
| **Cold-start mitigation** | Operationally reduce or remove cold-start pain; warmup + runbook + optional min_instances |

Industrial best-practice for this stage: make Turn 1 lighter when possible; remove cold-start pain.

---

## 3. What "Good Enough Improvement" Looks Like

- **Warm Turn 1:** 2–4 s acceptable (LLM path); 50–200 ms for lightweight path
- **Cold Turn 1:** Avoid 5–15 s surprise; pre-warm or min_instances
- **Quality:** No regression; guardrail + scenarios pass

---

## 4. What This Sprint Will and Will Not Do

| Will | Will NOT |
|------|----------|
| Add Turn 1 lightweight path for high-confidence intents | Open new product scope |
| Strengthen warmup + runbook | Overengineer or redesign architecture |
| Keep fallback to LLM when uncertain | Force all Turn 1 into lightweight |
| Test and validate | Add streaming, observability platform |

---

*See: Execution Outline, Acceptance Criteria*
