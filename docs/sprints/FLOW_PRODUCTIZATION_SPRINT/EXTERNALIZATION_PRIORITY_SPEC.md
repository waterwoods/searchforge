# Externalization Priority Spec

Priorities are ranked for **founder ROI**: trial messaging, second broker readiness, and reduced drift — **without** fragility.

---

## Move next (high ROI now)

| Item | Current state | Target | Effort |
|------|----------------|--------|--------|
| **Reply overrides path** | `get_reply_templates()` always merges `chen_kui/reply_overrides.json` | Merge `configs/clients/{CLIENT_ID}/reply_overrides.json` | Small code change |
| **Route-level soft copy** | `REROUTE_MESSAGES`, `SOFT_ROUTE_STARTER_REPLIES` in `routes/inbox_triage.py` | Load from client or `configs/industries/insurance/routing_copy.json` | Small: new JSON + loader |
| **Add-car rules schema** | `add_car_rules.json` has `ask_driver_only`; loader only knows 3 keys | Extend `get_add_car_rules()` + `_get_next_ask_for_add_car` **or** trim JSON | Small–medium |
| **String ownership doc** | Implicit | This sprint folder + boundary spec (done) | Doc only |
| **Scenario pack index** | Many `run_*.py` scripts | One markdown table: pack → script → purpose (see Execution Outline) | Doc only |

**Rationale:** Fixes **real portability bugs** (client overrides) and **reduces duplicate copy** (routes), without touching boundary math.

---

## Move later (medium ROI, more design)

| Item | Note |
|------|------|
| **Boundary narrative blocks** | Move ZH/EN paragraphs from `_apply_append_case_boundary` into `client` or `industry` JSON; keep **classification** in code. |
| **DRAFT_QUALITY_PHRASES / FORMAL_DRAFT_MARKERS** | Could join `markers.json` or a `quality_signals.json` — low urgency. |
| **Per-flow handoff timing knobs** | e.g. turn thresholds in config — only after second customer proves need. |
| **Category enum in config** | Possible, but touches every guardrail; defer. |

---

## Keep in code for now (stability)

| Item | Reason |
|------|--------|
| **`_classify_append_case_boundary` and domain sets** | Safety + scenario-locked; JSON would be a shadow language. |
| **`_should_handoff` and add-car first-turn exception** | Core product promise; scenarios encode it. |
| **Field extraction** (`_extract_add_car_fields`, claim/removal, etc.) | Regex/heuristics need tests, not spreadsheets. |
| **LLM normalization and guardrail merge** | Correctness-critical. |
| **`case_store` validation enums** | Data integrity. |

**Do not** over-externalize handoff **policy** until you have a clear second customer requirement.

---

## Risk check: over-externalizing

If moving a rule to JSON means:

- You need a new **interpreter** in code, or
- Failures become **silent** (bad JSON → wrong handoff),

→ **keep in Python** and use **scenarios** as the contract.

---

## Ordering for a 1–2 week execution slice

1. Fix **reply_overrides** client path (unblocks second client folder).
2. Externalize **routing/starter** strings from routes.
3. Align **add_car_rules** schema.
4. Add **scenario index** doc (onboarding + broker conversations).
5. (Optional) Extract **boundary client_reply** templates to JSON.

---

## “What should move next” checklist (copy-friendly)

- [ ] `reply_overrides.json` keyed by `CLIENT_ID`
- [ ] `REROUTE_MESSAGES` / `SOFT_ROUTE_STARTER_REPLIES` moved to config + loader
- [ ] `ask_driver_only` either supported in code or removed from JSON
- [ ] Scenario pack index committed under this sprint or `docs/trial/`
- [ ] (Later) Boundary reply strings externalized; logic stays put
