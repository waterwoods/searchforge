# Execution Outline (Next 1–3 Weeks)

**Goal:** Ship **small** code/config changes that increase portability and reduce string drift, guided by this sprint’s docs — **no** framework migration.

---

## Week 1 — Correctness + portability fixes

| Day slice | Task | Done when |
|-----------|------|-----------|
| **A** | Patch `get_reply_templates()` to use `get_active_client_id()` for `reply_overrides.json`. | Second client folder works without code edit. |
| **B** | Move `REROUTE_MESSAGES` and `SOFT_ROUTE_STARTER_REPLIES` to JSON + load in `config_loader`; wire routes. | Strings editable without opening route file. |
| **C** | Resolve `add_car_rules` / `ask_driver_only` drift (implement or delete). | JSON matches engine behavior; scenarios green. |

**Validation:** `bash scripts/guardrail_inbox_triage.sh` + targeted add-car scripts you already use in sprints.

---

## Week 2 — Documentation + onboarding

| Task | Output |
|------|--------|
| Scenario inventory table | New section in `docs/trial/INDEX.md` or a `docs/standards/INBOX_TRIAGE_SCENARIO_INDEX.md` linking pack → runner. |
| “String classes” one-pager | Pointer from `CODE_CONFIG_UI_TEST_BOUNDARY_SPEC.md` to where each class lives. |
| Founder dry-run | Walk `FOUNDER_INSPECTION_NOTES.md` with a fresh reader; fix gaps. |

---

## Week 3 — Optional polish (only if trial needs it)

| Task | When to skip |
|------|--------------|
| Externalize **boundary** customer reply paragraphs | If copy is stable for Chen Kui trial. |
| Split `triage.py` into submodules (`engine/`, `flows/add_car.py`) | Only if onboarding pain is acute — **not** required for productization clarity. |

---

## Guardrail discipline

After each change:

1. `LLM_GENERATION_ENABLED=0` scenario runs (as in guardrail).
2. If triage API touched: `python3 scripts/test_inbox_triage_api.py` against local 8001 when available.

---

## Success criteria (lightweight)

- [ ] No known **hardcoded chen_kui** paths in config loaders (except safe default fallback).
- [ ] Route file contains **no** long Chinese business strings.
- [ ] Add-car rules JSON **matches** loader contract.
- [ ] Guardrail green on main branch.

---

## Anti-goals (do not do in this window)

- LangGraph / new orchestration framework.
- OCR, carrier APIs, multi-tenant auth.
- Full UI redesign.
