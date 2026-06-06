# Hot-Plug Strategy Fit Spec

## The core idea

**Hot-plug (client pack + industry layer) is not the customer-facing value proposition.**  
Customers buy **faster, calmer intake and handoff**. Hot-plug is how **SearchForge** sells the **same narrow product** to the **next** CA auto office without rewriting the engine.

## What should remain universal (common engine)

- **Triage semantics:** categories, urgency model, workflow backbone keys, append/boundary **logic** (not necessarily every string).
- **API contracts:** triage payload shape, `client_id` on requests, client-config endpoint for UI.
- **Validation discipline:** guardrail scripts, A/B scenario batteries—**repeatability** is part of the product.

## What should be client-pack specific

- **Voice and identity:** titles, welcome copy, quick-start starters, office labels (办公室 vs 本所, etc.).
- **Handoff and stitched phrases:** add-car handoff, talk-to-agent, **append boundary** customer-visible blocks (per append boundary externalization sprint).
- **Reply overrides** where tone must differ without forking the whole template tree.

## What makes same-industry replication faster

- **Clone pack:** `configs/clients/chen_kui/` → `configs/clients/<new_id>/` per `SAME_INDUSTRY_MIGRATION_CHECKLIST.md`.
- **Industry markers** shared across CA auto brokers; **avoid** broker names inside industry files (known leak called out in second broker drill).
- **Engine last:** only when config cannot express the requirement—prevents per-broker forks of `triage.py`.

## Cross-industry expansion: not the current priority

- Hot-plug proves **process replication within one vertical**, not “any insurance anywhere.”
- **Positioning stays:** CA auto, pasted text, small office. Expansion **after** two paying references in the same niche is strategically safer than horizontal sprawl.

## Connection map (founder)

| Layer | Customer hears | Internal role |
|-------|------------------|---------------|
| Positioning | Intake + handoff workbench | Revenue story |
| Workbench + scenarios | 7 high-frequency flows | Proof in demo |
| Client pack | “Sounds like our office” | Trust + closing |
| Guardrails / drills | Silent | Prevents lying by accident |

---

*Evidence: `docs/sprints/SECOND_BROKER_CLIENT_PACK_DRILL/FINAL_REPORT.md`, `docs/sprints/archive/p2_reply_flow_polish_sprints/APPEND_BOUNDARY_STRINGS_EXTERNALIZATION_SPRINT/FINAL_REPORT.md`, `docs/sprints/CLIENT_PACK_OPERATING_MANUAL_PRODUCTIZATION_INDEX/SAME_INDUSTRY_MIGRATION_CHECKLIST.md`.*
