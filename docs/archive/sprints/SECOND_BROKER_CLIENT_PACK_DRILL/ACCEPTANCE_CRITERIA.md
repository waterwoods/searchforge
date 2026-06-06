# Acceptance Criteria

- [x] New sprint folder `docs/sprints/SECOND_BROKER_CLIENT_PACK_DRILL/` with required docs (blueprint, pack spec, audit spec, scenario doc, gaps spec, execution outline, acceptance, founder notes, final report).
- [x] Fictional same-industry second broker **client_id** + full client pack (`ui_copy`, `handoff_phrases`, `reply_overrides`).
- [x] Drill scenario pack + automated runner; **passes** with `LLM_GENERATION_ENABLED=0`.
- [x] `scripts/guardrail_inbox_triage.sh` **PASS** after changes.
- [x] `ui` production build **PASS** (no frontend edits required for drill, but bar checked).
- [x] FINAL_REPORT answers: what swapped, what leaked, feasibility judgment, risks — **without overselling**.

## Explicit non-requirements

- [ ] Server-on-8001 API curl (optional; documented as unrun if no server).
- [ ] LLM-on deterministic assertions.
