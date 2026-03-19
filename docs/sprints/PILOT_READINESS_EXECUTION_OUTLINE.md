# Pilot Readiness + Sellability Sprint — Execution Outline

**Sprint:** 2026-03-14

---

## Workstreams

| # | Workstream | Owner | Scope |
|---|------------|-------|-------|
| 1 | Control docs | Planner | Blueprint, Execution Outline, SLA |
| 2 | Pilot / sellability audit | Product critic | What's strong, weak, blocks conversion |
| 3 | High-value improvements | Product narrative | Choose 1–3; no feature creep |
| 4 | Loop 1 implementation | Frontend / UX | Pilot header, trust framing, demo path |
| 5 | Loop 1 validation | Simulation / QA | Smoke check, guardrail, build |
| 6 | Loop 2 refinement | Product critic | One focused improvement if worthwhile |
| 7 | Final convergence | Release reviewer | Iteration log, pilot judgment |

---

## Sequence

1. **Phase A:** Create Blueprint, Execution Outline, SLA (control docs)
2. **Phase B:** Pilot / sellability audit (small-client perspective)
3. **Phase C:** Choose 1–3 improvements
4. **Phase D:** Loop 1 — implement, test, evaluate
5. **Phase E:** Loop 2 — refine if clearly worthwhile
6. **Phase F:** Optional loop 3 — only if gain is obvious
7. **Phase G:** Final pilot judgment + iteration log

---

## Testing / Simulation Plan

| Test | When | Pass criteria |
|------|------|----------------|
| `bash scripts/guardrail_inbox_triage.sh` | After each loop | PASS |
| `bash scripts/unified_intake_smoke_check.sh` | After loop 1 | Guardrail PASS; manual steps documented |
| `cd ui && npm run build` | After each UI change | Build succeeds |
| Manual: R1, R2, R3, SIM1, SIM2, SIM3 | After loop 1 | Scenarios run; handoff visible |

---

## Role Assignment

- **Planner / architect:** Control docs, scope guardrail
- **Product narrative:** Value positioning, pilot clarity copy
- **Frontend / UX:** Unified Intake header, trust block, demo path
- **Simulation / QA:** Guardrail, smoke check, build
- **Product critic:** Audit, critique, "worth it?" judgment
- **Release reviewer:** Iteration log, final pilot judgment
