# Pilot verification & handoff credibility spec

Lightweight criteria used for this sprint’s assessment. Aligned with the master outline: Stage 1 = intake + structuring + explicit handoff; not quote engine or CRM.

## Customer trust criteria

| Criterion | “Pass” signal |
|-----------|----------------|
| Ease of entry | Add-Car is visually primary; empty state explains paths without hiding the flagship lane. |
| Case received | Post-handoff headline, status badge, and closure copy state office receipt in plain language. |
| No needless repetition | Copy explicitly says submitted points need not be repeated; append-to-same-record is bounded vs new issue. |
| Next step clarity | Timing/follow-up expectations and “your next step” lane are present where configured. |

## Office trust criteria

| Criterion | “Pass” signal |
|-----------|----------------|
| Clean record | Triage populates `broker_next_step`, collected/still-needed fields, and Add-Car-specific office hints where rule path applies. |
| Clear next action | Workbench surfaces case id, status strip (Add-Car), broker-next preview, and case staging tags consistent with triage. |
| Same record | Subtitle/copy ties customer portal and workbench to the same “服务记录” narrative; record id copyable on office side. |

## Pilot credibility criteria

| Criterion | “Pass” signal |
|-----------|----------------|
| Showable to a broker | Portal and closure read as operational intake, not a toy chat demo. |
| Defensible scope | Pilot can be sold as structured intake + handoff, not auto-binding or pricing. |
| Honest limitations | JSON persistence, auth/PII, and LLM-vs-rule parity are known and communicable (`PROJECT_TRUTH_SWITCH`). |

## Handoff credibility checklist

- [ ] Customer sees explicit “submitted to office” language after handoff.
- [ ] `client_reply_draft` on Add-Car handoff uses client `handoff_phrases` / stitched lines where applicable.
- [ ] **Materials / already-sent** in Add-Car context uses `add_car_materials_sent` style reassurance (verify via rule path).
- [ ] **Clarification** mid-flow does not prematurely claim full handoff when info is incomplete.
- [ ] Workbench shows **服务记录编号** + hint tying to customer result card.
- [ ] Append vs new-issue boundaries are visible to the customer after submit.

## Acceptance criteria (for this sprint as a verification gate)

1. **Rule-path engine**: `LLM_GENERATION_ENABLED=0 bash scripts/guardrail_inbox_triage.sh` passes (regression + multi-turn + broker stress including already-sent Add-Car).
2. **Targeted Add-Car battery**: `run_add_car_realistic_intake_scenarios.py` completes with expected quote-ready / handoff shapes for defined scenarios.
3. **Evidence-based report**: Final report separates directly verified (scripts), inferred (code/config review), and not verified (live browser/API on 8001 if unavailable).
