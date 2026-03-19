# Logic Visibility / Review Spec

**Sprint:** Scenario Logic Center Sprint  
**Created:** 2026-03-18  
**Purpose:** Define how the center should present scenario logic for founder and broker review.

---

## 1. Presentation Principles

| Principle | Meaning |
|-----------|---------|
| **Readable at a glance** | Scenario name + business goal + maturity in one line |
| **Expandable** | Route, ask-next, handoff, broker_next_step in expandable section |
| **No raw JSON dump** | Human-readable labels; config paths as secondary |
| **Three levels visible** | Business / Operational / Configuration |

---

## 2. What Should Be Readable at a Glance

- Scenario name
- Business goal (one line)
- Maturity chip (strong / medium / weak)
- Fix-now / fix-next / defer (if any)
- Config layer badge (common / industry / client)

---

## 3. What Should Be Expandable

| Section | Content |
|---------|---------|
| **How recognized** | Main markers or route (e.g. add_vehicle, payment, strong_cancellation) |
| **What we ask next** | Next-best-question behavior (1–2 things) |
| **When we hand off** | Handoff threshold (e.g. year+model+zip for add-car) |
| **Broker next step** | Full broker_next_step text |
| **Client prep** | What client should send (when applicable) |
| **Config source** | File path (e.g. markers.json, category_templates.json) |

---

## 4. How to Show Route / Ask-Next / Handoff / Broker Next Step

| Element | Display |
|---------|---------|
| **Route** | "Detected via: add_vehicle + vehicle_context markers" |
| **Ask-next** | "Asks for: year, model, VIN, zip, delivery, driver (in order)" |
| **Handoff** | "Hands off when: year+model + (zip OR delivery OR driver)" |
| **Broker next step** | Full sentence, bold |

---

## 5. How to Show Fix-Now / Fix-Next / Defer

| Status | Chip color | When |
|--------|------------|------|
| Fix now | Red | Blocks trial or breaks trust |
| Fix next | Orange | High value, 1–2 sprints |
| Defer | Gray | Lower priority; document for later |
| (none) | — | No known issue |

---

## 6. How to Show Common / Industry / Client Layers

| Layer | Badge | Meaning |
|-------|-------|---------|
| Common | `common` | Shared workflow; all clients |
| Industry | `industry` | Insurance-specific; configs/industries/insurance/ |
| Client | `client` | Chen Kui specific; configs/clients/chen_kui/ |

---

## 7. What Is Above the Fold

- Summary header: "Scenario Logic Center — X scenarios for Chen Kui Unified Intake"
- Grouping: Standard package (7) | Extended (5) | Fallback (1)
- Quick status: "Strong: 5 | Medium: 6 | Weak: 2" (example)

---

## 8. What Is Still Too Detailed to Show Now

- Full marker lists (link to markers.json)

- Full LLM prompt text
- Internal triage.py function names (except as config source)
- Per-category reply template variants (zh_with_item, zh_without_item, etc.)

---

*See also: `04_SCENARIO_STATUS_HEALTH_SPEC.md`, `05_EXECUTION_OUTLINE.md`*
