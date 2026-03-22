# Case Persistence Review Blueprint

**Sprint:** Case Persistence Review + Workbench Polish  
**Product:** SearchForge → Chen Kui Insurance Unified Entry (Unified Intake)

## Purpose

Give founders and commercial stakeholders a single, accurate picture of **what survives a server restart**, **what is demo-grade vs production-grade**, and **what to build next** for a paid pilot.

## Scope

- Persisted **cases** (handoff-ready triage outcomes and follow-on updates).
- Persisted **in-progress sessions** (pre-handoff multi-turn state).
- **Attachments** (files + metadata).
- Explicitly **out of this blueprint’s implementation work:** demo queue loading UI (separate concern).

## Questions this blueprint answers

1. Are cases persisted? **Yes**, when `persist_case` is true and triage returns `handoff_ready` (normal path), or for the Talk-to-Agent fast path when persisting.
2. What is persisted? See `02_CURRENT_PERSISTENCE_ARCHITECTURE_SPEC.md`.
3. Where? JSON files under `data/` by default; env overrides supported.
4. Commercial gap? No multi-tenant RDBMS, no object store, no audit/encryption/compliance story—by design for current MVP.

## Success criteria (review)

- [ ] Spec matches code in `case_store.py`, `session_store.py`, and `inbox_triage` routes.
- [ ] Founder can explain persistence in one minute without saying “database” unless asked.
- [ ] Engineering has a clear target architecture for pilot hardening (`03_...`).

## References

- `services/fiqa_api/inbox_triage/case_store.py`
- `services/fiqa_api/inbox_triage/session_store.py`
- `services/fiqa_api/routes/inbox_triage.py`
