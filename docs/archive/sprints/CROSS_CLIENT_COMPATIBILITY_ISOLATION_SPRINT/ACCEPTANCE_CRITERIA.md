# Acceptance Criteria

## Must pass

- [x] Guardrail `scripts/guardrail_inbox_triage.sh` — **PASS** (including new cross-client step).
- [x] `LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_cross_client_ab_scenarios.py` — **12/12**.
- [x] Add-Car flagship behavior unchanged for Chen Kui when `stitched` matches prior defaults (materials-sent, prospective-send, why-still-chasing strings equivalent to old engine text for A).

## Product

- [x] **Judgment documented:** what isolates vs what still leaks (append boundary).
- [x] **At least one** client B path that previously showed generic 办公室 on materials-sent **no longer does** when B’s `stitched` is set.

## Documentation

- [x] All required docs under `docs/sprints/CROSS_CLIENT_COMPATIBILITY_ISOLATION_SPRINT/`.
- [x] Final report matches requested section structure (see `FINAL_REPORT.md`).

## Explicit non-requirements

- UI build was not required (no UI files changed).
- Full removal of 办公室 from every Chinese path (append still shared).
