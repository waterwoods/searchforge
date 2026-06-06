# Refactor / Externalization Roadmap Spec

**Constraints:** No whole-system rewrite; preserve trial-ready behavior; prefer **docs + thin extraction** first.

---

## Near-term (high ROI now)

1. **Architecture docs** (this sprint folder) — make the brain legible to founders and new eng.
2. **Phrase / string inventory** — table: scenario → file → key → owner (product vs eng).
3. **Clarify `add_car_rules` keys** — ensure `get_add_car_rules` / `save_add_car_rules` include every key triage reads (`ask_driver_only` if product edits it in JSON).
4. **Comment block at top of `triage_conversation`** — ordered list of “reply transformation” steps (or link to `03_ADD_CAR_FLOW_DEEP_DIVE.md`).
5. **Route copy** — if brokers ask for copy tweaks often, move `REROUTE_MESSAGES` / `SOFT_ROUTE_STARTER_REPLIES` to `configs/clients/<id>/` in a follow-up PR.

---

## Mid-term

1. **Extract modules by domain** (behavior-neutral moves):
   - `inbox_triage/add_car_flow.py` — extraction + next-ask + add-car handoff patches
   - `inbox_triage/append_boundary.py` — `_classify_append_case_boundary` and friends
   - `inbox_triage/reply_phrases.py` — loading merge of templates + handoff + fallbacks
2. **Industry vs client pack layout** — document mandatory files per client; optional overrides.
3. **Consolidate simulation configs** — README index of which `run_*.py` covers which product promise (Standard Package vs add-car deep batteries).

---

## Later / optional

1. **Declarative workflow layer** — only if you add **many** new flows with shared patterns; evaluate against cost of keeping expert Python + tests.
2. **Heavier framework (LangGraph, Temporal, etc.)** — only with **multi-tenant**, **long-running** processes, or **human task queues** beyond current JSON demo scope.
3. **UI/API `flow_hint` field** — reduce duplicate “is this add-car?” logic between UI and backend.

---

## Explicit decisions (per sprint mission)

| Question | Answer |
|----------|--------|
| Is current architecture good enough for this stage? | **Yes** — bounded domain, strong test net, clear deployment unit. |
| Heavier framework needed **now**? | **No** — complexity lives in **business edge cases**, not in generic graph traversal. |
| Better next move than framework? | **Yes** — documentation, phrase inventory, optional mechanical file split of `triage.py`. |

---

## What should **remain as-is** for now

- Core **handoff vs collect** semantics proven by guardrail + batteries.
- **LLM + fast path** split — works for cost/latency tradeoffs.
- **JSON case store** — appropriate for pilot/demo; not a migration target until product scope demands relational DB + auth.

---

## What should **not** be done yet

- Rewriting triage into a graph DSL without product pause (high regression cost).
- Merging all copy into one giant JSON without migration tooling (merge conflicts, no review story).
- Broad UI redesign masquerading as “architecture.”
