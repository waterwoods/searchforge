# Externalization Priority Spec

Prioritized by **portability ROI / regression safety**. This sprint executes only the top tier.

## Tier A — Done this sprint (high ROI, low risk)

| Item | Before | After |
|------|--------|--------|
| Reply overrides | Always merged `configs/clients/chen_kui/reply_overrides.json` | `configs/clients/{client_id}/reply_overrides.json` when file exists; no cross-client override bleed |
| Soft-route copy | Hardcoded dicts in `routes/inbox_triage.py` | `configs/common/soft_route_inbox.json` + code defaults |
| `ask_driver_only` | Present in JSON, partially bypassed by loader/publish | Loaded in `get_add_car_rules`; preserved on publish |

## Tier B — Move later (medium ROI)

- Per-client soft-route overrides (if a second office needs different reroute wording).
- Expand `scenario_logic_center.json` maintenance process (documentation + owner).
- Gradual reduction of `_FALLBACK_MARKERS` in `triage.py` after marker JSON parity tests.

## Tier C — Keep in code until strong need

- Full handoff state machine as data.
- LLM prompt bodies as files (possible, but needs versioning discipline).
- Splitting triage into multiple modules (do with a dedicated refactor sprint + identical guardrail output).

## Config vs code boundary rule

**Config:** Wording, lists of phrases, ordered prompts where behavior is “say this next.”  
**Code:** Ordering, guards, “if mixed intent then …”, append/new-case boundary, persistence side effects.
