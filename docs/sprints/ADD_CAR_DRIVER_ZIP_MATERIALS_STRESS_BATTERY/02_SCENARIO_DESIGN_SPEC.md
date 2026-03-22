# Scenario Design Spec

## Count and balance

- **19 scenarios** total (within 10–20).
- **6** ZIP-focused (`ADZM-Z01`–`Z06`, `Z06` = glued `zip95131`)
- **5** driver-focused (`ADZM-D01`–`D05`)
- **4** materials-focused (`ADZM-M01`–`M04`)
- **4** mixed (`ADZM-X01`–`X04`), including multi-turn

## Design rules

1. **Language:** Simplified Chinese with natural California broker-office context (WeChat tone, occasional English tokens like `zip`, `registration`, `dec page`).
2. **Add-Car anchor:** Every thread must clearly be add-to-policy / 加车 intent (explicit phrase or vehicle + 想加进保单).
3. **One primary stress per scenario** even when multiple slots appear (documented in `focus` array).
4. **Mixed cases** intentionally stack ZIP + driver + materials in one or two bubbles to mimic “dense” real messages.

## IDs

- Prefix **`ADZM`** = Add-Car Driver / ZIP / Materials stress battery.

## Fields in JSON (per scenario)

- `id`, `name`, `focus[]`, `why_matters`, `expected_good_behavior`, `failure_looks_like`, `turns[]` with `role` / `text`.

## Multi-turn conventions

- Turn 1 may be minimal (“想加车”); Turn 2 carries slots — tests **merged customer text** extraction.
- System replies are simulated by the runner (appended as `system` turns) so Turn 2 sees realistic context.

## Realism notes

- **90210** included in one mixed case: still matches CA-style `9xxxx` strict pattern used in triage (five-digit ZIP starting with 9).
- **主要驾驶人是我老婆** included deliberately to test phrasing **without** the character 开 after 老婆.
