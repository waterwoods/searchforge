# Concentration vs Scatter Analysis

Honest judgment of **where the architecture helps** and **where it hurts**, with **severity** and **when to fix**.

---

## A. Too concentrated

### A1. `triage.py` as the single flow brain

- **What:** ~3630 lines (single module, as of 2026-03-22) mixing classification, extraction, reply composition, handoff policy, append boundary, and many sprint-named edge cases.
- **Severity:** **High** for *maintainability and onboarding*; **medium** for *runtime* (it’s still one import, predictable to deploy).
- **Blocks progress?** No — it has shipped trial hardening. It **slows** safe change without tests.
- **Fix now vs later:** **Later** for split; **now** for documentation + naming (this sprint). Optional near-term: extract **pure helpers** (e.g. add-car only module) without changing behavior.

### A2. Handoff / “next ask” policy embedded in one function

- **`triage_conversation`** chains: base triage → would_handoff → next_ask override → handoff phrase selection → multiple `if handoff and is_add_car` patches.
- **Severity:** **High** for reasoning about *order of operations* (“which patch wins?”).
- **Blocks progress?** Only when two commercial requirements **fight** in the same branch — mitigated today by scenario batteries.
- **Fix now vs later:** **Near-term** — add a short **inline decision table** in code comments or a linked doc section listing patch priority; mid-term consider a **small ordered list** of “reply transformers” (still Python, not a new framework).

### A3. Route-level copy (`REROUTE_MESSAGES`, `SOFT_ROUTE_STARTER_REPLIES`)

- **What:** Customer-facing strings in `routes/inbox_triage.py`.
- **Severity:** **Low–medium** (duplicates the pattern of config elsewhere).
- **Fix now vs later:** **Mid-term** — move to client config pack for white-label parity.

---

## B. Too scattered

### B1. Customer-facing language in three places

- **Where:** `handoff_phrases.json`, `reply_templates` / overrides, `ui_copy.json`, **and** many **hardcoded** strings in `triage.py` and `routes/inbox_triage.py`.
- **Severity:** **Medium** — founders and CS can’t “find the sentence” in one CMS.
- **Blocks progress?** No for demo; **yes** for **fast copy iteration** without eng.
- **Fix now vs later:** **Near-term** — publish a **phrase inventory** (spreadsheet or markdown index) mapping **feature → file → key**; **mid-term** — migrate high-churn phrases to config.

### B2. Add-car “rules” split between code order and config text

- **Where:** Slot **gating** and **turn-2 driver ask** live in code; **prompt text** in `add_car_rules.json`.
- **Severity:** **Low** — honest architecture if documented (logic vs copy).
- **Blocks progress?** No.
- **Fix now vs later:** **Keep** as-is; document. Optionally align `ask_driver_only` through `config_loader` (see Add-Car deep dive).

### B3. Scenario packs vs sprint JSON batteries

- **Where:** `configs/inbox_triage_scenarios.json` vs `docs/sprints/.../scenario_battery.json` vs multiple `run_*.py` entrypoints.
- **Severity:** **Medium** for **discoverability** (“which script do I run?”).
- **Blocks progress?** No — `guardrail_inbox_triage.sh` is the spine.
- **Fix now vs later:** **Near-term** — index in one README under `docs/sprints/FLOW_ARCHITECTURE_SUMMARY_ROADMAP` or `docs/guardrails/` pointing to all add-car runners.

### B4. UI “looks like add-car” heuristic

- **Where:** `triageResultLooksLikeAddCar` in UI duplicates some product judgment already implied by backend fields.
- **Severity:** **Low** — drift risk if backend renames fields.
- **Fix now vs later:** **Later** — prefer a single explicit `flow_hint` from API if drift becomes painful.

---

## C. What matters now vs later

| Item | Now | Later |
|------|-----|-------|
| Understand flow brain location | Yes | — |
| Document patch order / ownership | Yes | — |
| Split `triage.py` into packages | — | Yes, when team size or flow count grows |
| Unified phrase CMS | Partial index | Full externalization |
| LangGraph / state machine framework | No | Only if workflow count explodes |
