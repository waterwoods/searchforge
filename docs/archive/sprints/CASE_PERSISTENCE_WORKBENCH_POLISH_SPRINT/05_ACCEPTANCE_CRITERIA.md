# Acceptance Criteria

## Part A — Documentation

- [ ] **Blueprint** states mission, scope, and pointers to code.
- [ ] **Current spec** lists persisted fields, file locations, env overrides, limits, and append semantics—consistent with `case_store.py` / `session_store.py`.
- [ ] **Future spec** names recommended DB (Postgres), object store for files, and what lives where—with a plausible migration sketch.
- [ ] **Execution outline** documents the three loops.
- [ ] **Founder notes** are readable without opening Python files.

## Part B — Workbench polish (constraints)

- [ ] **No** changes to demo queue loading, persistence, or debugging flows.
- [ ] At least **one** user-visible improvement toward office-tool feel (e.g. clearer follow-up language, less internal/developer tone in the case sheet).
- [ ] `npm run build` passes if frontend changed.

## Validation

- [ ] `bash scripts/guardrail_inbox_triage.sh` exits successfully.

## Final report

- [ ] Single report answers: persisted today vs future; what was polished; what remains weakest.
