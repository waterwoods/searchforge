# Multi-Turn Continuity Guardrail Spec

**Purpose:** Prevent reintroduction of single-turn demo behavior into the multi-turn Customer Entry product.

**Scope:** Unified Intake / Customer Entry / Broker Workbench mainline.

---

## 1. Core Rules (Non-Negotiable)

| Rule | Meaning |
|------|---------|
| **First message must not bypass conversation engine** | The first user message must go through `triage_conversation(text, [])` or equivalent logic. Do not use `triage_message()` and then force `handoff_ready=True`. |
| **handoff_ready must not be forced by default** | `handoff_ready` must be derived from `_should_handoff()` or equivalent thresholds. Do not set `handoff_ready=True` unless the logic explicitly justifies it. |
| **Frontend must not treat first reply as final when more info needed** | When `handoff_ready=False`, the UI must allow continuation. Do not hide input, show "done" state, or handoff card prematurely. |
| **Button starters must preserve multi-turn continuity** | Quick-start buttons (add_car, remove_car, etc.) may set `soft_route` but must not bypass the conversation path. The first reply after a button click must still go through `triage_conversation`. |
| **Exceptions must be documented** | Any exception to these rules (e.g. Talk to Agent) must be documented with justification. |

---

## 2. Explicit Exceptions

| Exception | Justification |
|-----------|---------------|
| **Talk to Agent** | Customer explicitly requests human contact; immediate handoff is correct. |
| **triage_for_append** | Broker pastes into existing case; broker receives updated case (handoff-ready). Not a customer conversation flow. |
| **Add-car with full info on first turn** | MATURE_INTAKE_SKELETON: when year+model+zip present, hand off immediately. |

---

## 3. What to Check Before Changing Triage/Route

- [ ] Does the change affect first-turn behavior?
- [ ] Is `handoff_ready` still derived from thresholds, not forced?
- [ ] Does the change preserve `triage_conversation` as the main path for all customer messages?
- [ ] Are any new bypasses documented as exceptions?

---

## 4. Regression Tests

- `scripts/test_first_turn_continuity.py` — First-turn must not force handoff_ready (vague add-car, payment, missing-doc)
- `scripts/run_multi_turn_simulations.py` — Handoff timing (expected_handoff_after_turn)
- `configs/customer_entry_multi_turn_simulations.json` — Multi-turn scenario pack

When adding new triage logic, ensure multi-turn simulations and first-turn continuity test still pass.

---

## 5. Reference Docs

- `docs/MATURE_INTAKE_SKELETON.md` — Shared flow: detect → ask → enough? → hand off
- `docs/sprints/CUSTOMER_ENTRY_MULTI_TURN_ACCEPTANCE_CRITERIA.md` — What counts as true multi-turn
- `services/fiqa_api/inbox_triage/triage.py` — `triage_conversation`, `_should_handoff`

---

*End of guardrail spec*
