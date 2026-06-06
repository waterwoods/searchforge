# Battery spec + issue harvest categories

## Battery cases (minimum)

| ID | Persona (zh) | `persona_id` | Difficulty (zh) | `difficulty` | Max turns |
|----|----------------|--------------|-----------------|--------------|-----------|
| C1 | 价格敏感型 | `price_sensitive` | 真实 | `realistic` | 6 |
| C2 | 价格敏感型 | `price_sensitive` | 刁钻 | `tough` | 8 |
| C3 | 老年客户型 | `elderly` | 刁钻 | `tough` | 8 |
| C4 | 家庭车辆型 | `family_vehicle` | 真实 | `realistic` | 6 |
| C5 | 材料先发型 | `materials_first` | 真实 | `realistic` | 6 |

**Shared settings:** `client_id`: `chen_kui`, `soft_route`: `add_car`, `persist_case`: `false`, stable `session_id` per case.

## Per-turn inspection checklist

1. **Role realism** — plausible customer; persona/difficulty visible in language and behavior.
2. **Add-Car discipline** — stays on add-vehicle / quote-prep; no major topic drift.
3. **State / triage coherence** — `collected_fields`, `still_needed_fields`, `lifecycle_status`, `quote_ready_status`, `broker_next_step`, `collection_stage` align with transcript.
4. **Right-rail story** — “received / missing / next” would remain understandable from API fields + draft.
5. **Handoff behavior** — post–`handoff_pending` replies truthful, not repetitive; still responsive to new info.
6. **Issue quality** — name the concrete failure; severity.

## Issue harvest categories

- **A. Persona realism** — weak persona/difficulty, synthetic tone, obvious fake PII/VIN patterns.
- **B. Triage / extraction quality** — wrong or stale `collected_fields` / `still_needed_fields`; corrections not absorbed; category mis-routing.
- **C. Handoff reply truth** — repetitive templates; “office phase” copy that ignores what the customer just said; misleading contact disclaimers.
- **D. State / lifecycle clarity** — collecting vs `handoff_pending` blur; `quote_ready_status` vs missing contact fields tension; odd `issue_category` jumps.
- **E. Demo / product clarity** — right rail or queue narrative would confuse; feels robotic.

## Acceptance criteria

- [ ] All five cases executed against a backend where Role C returns `llm_used: true` and triage returns structured fields.
- [ ] Each case has per-turn notes on the six checklist dimensions (at least where material).
- [ ] Issues classified; trivial noise omitted.
- [ ] Top issues ranked; one next-sprint recommendation tied to evidence.
