# ADD-CAR-FIRST PILOT CLOSING SPRINT — Blueprint

## Sprint goal

Sharpen Unified Intake toward an **Add-Car-first pilot**: make the flagship flow obvious in hero, tabs, empty state, pilot intro, and configurable copy—without rewriting triage or pretending non–Add-Car paths are equally mature.

## Why now

- Project truth (`docs/PROJECT_TRUTH_SWITCH.md`) already states Add-Car as the strongest monetizable path.
- The UI had begun signaling “推荐主路径” in places but still read like a **universal** intake portal (hero title, tagline, empty copy, pilot alert).
- Over-broad framing risks pilot mistrust; honest narrowing improves **sellability** and **scope clarity** for small-B brokers.

## Current business / product reality

- **Product:** Auto insurance customer unified intake + case organization + office handoff—not autonomous AI, not CRM, not agency OS.
- **Engine strength:** Add-Car / add-vehicle quote intake is the deepest, most productized loop (structured fields, transaction ribbon, result card, handoff copy).
- **Commercial path:** Chargeable pilot narrative should anchor on Add-Car; other intents remain supported but **de-emphasized** in messaging.

## Scope

- Add-Car-first **framing** on the customer entry surface (hero, brand tagline, empty state, tab suffix, input placeholder, quick-start badge).
- Top **pilot intro** alert: explicit Add-Car-first pilot language and honest maturity gradient for other intents.
- **Defaults + Chen Kui** `ui_copy.json`; new optional key `portal_add_car_button_badge` in `clientConfig.ts`.
- This sprint folder: blueprint, pilot spec, final report.

## Non-scope

- Triage engine, case store, config loader, app_main changes.
- Hardening all non–Add-Car intents to parity.
- Auth, billing, multi-tenant, CRM.

## Target outcome

A broker or first-time visitor can answer within seconds: **“The thing to try first is Add-Car.”** Founders can demo without over-promising universal automation.
