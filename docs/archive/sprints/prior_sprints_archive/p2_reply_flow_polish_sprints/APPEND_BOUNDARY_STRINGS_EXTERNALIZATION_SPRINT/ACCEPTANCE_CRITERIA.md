# Acceptance Criteria

## Must pass

1. **`triage_for_append`** boundary **classification** unchanged: `scripts/run_case_boundary_battery.py` — **23/23** (no `client_id` param; uses env default client for stitched—defaults match legacy Chinese).
2. **Cross-client A/B:** `scripts/run_cross_client_ab_scenarios.py` — **12/12**, including **`ab_10`** Client B without required **办公室** in customer draft.
3. **New append boundary A/B:** `scripts/run_append_boundary_ab_scenarios.py` — **12/12**.
4. **Full guardrail:** `bash scripts/guardrail_inbox_triage.sh` — **PASS** (includes `[12b]`).

## Product checks

- Client A may omit `stitched.append_boundary` and retain pre-sprint customer wording on boundary paths.
- Client B with `append_boundary` uses **second-broker voice** on `new_issue` / `borderline` customer drafts.
- `demo_broker` without `append_boundary` still produces coherent **default** boundary copy (engine defaults).

## Explicit non-requirements

- Broker-only English `Case boundary:` prefixes unchanged.
- No change to `_classify_append_case_boundary` outcomes.
