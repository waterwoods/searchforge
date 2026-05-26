# ADD-CAR-FIRST PILOT CLOSING SPRINT — Final report

## What changed

- **`ui/src/api/clientConfig.ts`:** Add-Car-first defaults for portal hero, tagline, empty headline/secondary, tab suffix, input placeholder; new `portal_add_car_button_badge` (default `推荐主路径`).
- **`ui/src/pages/UnifiedIntakePage.tsx`:** Pilot intro (`PILOT_INTRO`) rewritten for Add-Car-first pilot + honest non-parity; quick-start badge reads from config; inline fallbacks aligned with new defaults.
- **`configs/clients/chen_kui/ui_copy.json`:** Mirrored portal strings + `portal_add_car_button_badge` for pack fidelity.

## What improved

- **Obvious flagship path** on first paint (hero + empty state + tab suffix).
- **Less “universal assistant”** illusion via tagline, placeholder, and pilot alert.
- **Trust through narrowing:** explicit “不以全能助手为承诺” and maturity caveat for non–Add-Car.

## What remains

- **Engine:** Non–Add-Car intent depth still variable—only messaging addressed here.
- **Broker workbench:** Still generic in places; optional future sprint to echo Add-Car-first in workbench chrome only.
- **Validation:** Full `guardrail_inbox_triage.sh` not re-run this sprint (no triage edits); run before pilot sign-off per `PROJECT_TRUTH_SWITCH.md`.

## Pilot / revenue proximity

This sprint moves **explanation and demo narrative** materially closer to a sellable Add-Car-first pilot. It does **not** by itself prove operational readiness (ops runbooks, broker training, persistence/PII posture)—those stay separate.

## Recommended next sprint

**“Add-Car pilot ops + workbench echo”** — align broker tab headline/empty state with Add-Car-first language; run guardrail + one broker dry-run script; optional: single-page “pilot scope” sheet for handout.
