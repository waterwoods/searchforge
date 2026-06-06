# Append Boundary Strings Externalization Blueprint

## Purpose

After Add-Car stitched phrases became client-overridable, **append / continuation / new-issue boundary** replies were still assembled from a single hardcoded Chinese (and English) block inside `_apply_append_case_boundary`. That forced **Client B** (same industry) to surface **Chen-style「办公室」** wording whenever the engine classified `new_issue` or `borderline`—undermining the “hot-plug client pack” story on the **append path**.

## Non-goals

- Do **not** move `_classify_append_case_boundary` or domain/pivot rules into JSON.
- Do **not** change broker-facing English tags (`Case boundary:…`, `Boundary: new_issue…`) in this sprint unless product asks later.
- No new DSL; no large orchestration refactor.

## Target behavior

1. **Classification stays in code**; only **customer-visible stitched paragraphs** for append boundary outcomes are configurable per client.
2. **No cross-client fallback** for boundary copy: missing keys use **engine defaults** (same strings Chen Kui had before), not another client’s file.
3. **`triage_for_append`** passes `client_id` into boundary application so persisted case identity continues to drive wording.

## Success signal

- Client A (`chen_kui`) may omit `stitched.append_boundary` and keep prior behavior via defaults.
- Client B (`socal_precision`) supplies `stitched.append_boundary` and **A/B tests** show **no forced「办公室」** on boundary paths while logic flags stay identical.

## References

- Implementation: `services/fiqa_api/inbox_triage/triage.py` (`_APPEND_BOUNDARY_DEFAULTS`, `_merged_append_boundary_copy`, `_apply_append_case_boundary`).
- Config: `configs/clients/<client_id>/handoff_phrases.json` → `stitched.append_boundary`.
- Validation: `scripts/run_append_boundary_ab_scenarios.py`, `append_boundary_ab_scenario_battery.json`; `scripts/guardrail_inbox_triage.sh` step `[12b]`.
