# Execution Outline

**Sprint:** Handoff Timing Regression + Redeploy Sprint  
**Purpose:** Workstreams, implementation order, loop plan.

---

## Workstreams

1. **Control docs** — Blueprint, Simulation Spec, Evaluation, Fix Queue, Acceptance, Founder Notes
2. **Baseline audit** — Inspect current handoff logic; classify strong/weak
3. **Loop 1** — Run early-handoff regression pack; identify failures
4. **Loop 2** — Root-cause; decide fix-now/fix-next; apply 0–2 small fixes if justified
5. **Loop 3** — Retest; redeploy if changed; verify
6. **Founder verification** — Manual test list for Vercel

---

## Implementation Order

1. Create all 7 control docs
2. Baseline audit (inspect triage.py, run simulations)
3. Loop 1: Run handoff timing pack + guardrail
4. Loop 2: Classify; implement premium/payment "one more ask" if justified
5. Loop 3: Retest; redeploy
6. Founder test plan

---

## Loop Plan

| Loop | Action | Exit condition |
|------|--------|-----------------|
| 1 | Run simulations; classify | Clear failure/acceptable list |
| 2 | Root-cause; fix 0–2 | Fix-now addressed; fix-next documented |
| 3 | Retest; redeploy | Production truth verified |

---

## Validation Approach

- `bash scripts/guardrail_inbox_triage.sh`
- `PYTHONPATH=. python3 scripts/run_handoff_timing_simulations.py`
- `PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py`
- `bash scripts/deploy_rag_demo.sh` (if code changed)

---

*End of Outline*
