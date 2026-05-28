# FRONTEND INDUSTRIALIZATION SPRINT — Blueprint

## Sprint goal

Move **Unified Intake** (customer entry) measurably closer to a **production-grade small-B** product by strengthening four skeletons: **PAGE**, **FLOW**, **STATE**, and **HANDOFF**, without a broad redesign or backend scope creep.

## Why now

Per `docs/PROJECT_TRUTH_SWITCH.md`, the product is unified intake + case organization + office handoff; **Add-Car** is the strongest flow. Pilot and broker trust still depend on the portal feeling like a **formal business tool**, not a chat demo. Prior sprints added copy and cards; this sprint tightens **composition, progression, visible case state, and handoff parity** across intents.

## Scope

- Customer Entry in `ui/src/pages/UnifiedIntakePage.tsx` (and supporting `ui/src/api/clientConfig.ts` defaults).
- Page hierarchy, flow progression, status scanability, office next-step and case reference clarity.
- **Add-Car** remains the flagship path; changes must not weaken it.

## Non-scope

- Triage engine, case store, or API redesign.
- Auth, billing, multi-tenant CRM.
- Large design-system rewrites or new documentation beyond this sprint folder.

## Current gap (pre-sprint)

- Hero and long tagline competed with the **active transaction** once a session started.
- **Flow** was implicit (chat bubbles + progress card) without a single **step model**.
- **Non–Add-Car** flows lacked the same **status strip** treatment as Add-Car.
- **Handoff** showed `broker_next_step` mainly for Add-Car; generic flows had weaker **office-next** visibility; service record ID was tied to Add-Car framing.

## Target outcome

- Clearer **page discipline** when a session is active (lighter hero).
- Explicit **three-beat flow** (start → collect → submit) always visible.
- **Zendesk-like** status strip for non–Add-Car intake where Add-Car already had chips.
- **Intercom-like** handoff: office next step for **all** intents when API provides it; **case ID** shown whenever persisted.
