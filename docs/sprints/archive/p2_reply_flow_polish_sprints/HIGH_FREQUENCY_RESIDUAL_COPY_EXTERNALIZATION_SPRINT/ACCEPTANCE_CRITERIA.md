# Acceptance Criteria

- [x] **No logic regressions:** `LLM_GENERATION_ENABLED=0` guardrail passes end-to-end.
- [x] **Add-Car flagship:** quote-ready single turn still **hands off** with correct per-client handoff phrase.
- [x] **New A/B battery:** `scripts/run_residual_copy_ab_scenarios.py` — 15/15 pass.
- [x] **Isolation:** `socal_precision` drafts for new paths do **not** contain Chen Kui caveat substrings where tests forbid them.
- [x] **Fallback:** `demo_broker` without new stitched keys still gets **engine defaults** for caveat text.
- [x] **Config documented:** `get_stitched_handoff_phrases` docstring lists new stitched keys.
- [x] **Commercial story:** Founder can explain what moved and why same-industry hot-plug is safer.

## Commands (reference)

```bash
LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_residual_copy_ab_scenarios.py
bash scripts/guardrail_inbox_triage.sh
LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_add_car_scenario_battery.py
```
