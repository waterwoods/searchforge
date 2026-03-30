# Execution Outline

## Loop 1: Audit
- Inspect hardcoded customer-visible long-tail lines in `triage.py`.
- Confirm existing phrase-map/override/fallback behavior in `config_loader.py`.
- Select low-risk batch of four wording families.

## Loop 2: Externalize
- Add four keys to industry `reply_templates`.
- Add client-specific wording differences for `socal_precision` overrides.
- Wire `triage.py` to read template keys before hardcoded fallback for all four families in zh/en.

## Loop 3: Validate A/B
- Build new A/B battery and runner.
- Assert client wording separation and no leakage.
- Include fallback and flagship add-car sanity assertions.

## Loop 4: Regression Guardrails
- Run new A/B battery.
- Run `scripts/guardrail_inbox_triage.sh`.
- Run directly affected prior batteries:
  - `scripts/run_small_batch_phrase_map_ab_scenarios.py`
  - `scripts/run_residual_copy_ab_scenarios.py`
  - `scripts/run_append_boundary_ab_scenarios.py`

## Loop 5: Founder Reporting
- Summarize what moved, where, risk profile, validation status, remaining in-engine items, and next sprint recommendation.
