# CONTACT-READINESS ALIGNMENT + LATE-REPLY DE-DUP + ROLE C RECHECK — Blueprint

## Sprint goal

Tighten Add-Car **truth** so `handoff_ready` does not contradict **contact identity** on long threads, reduce **late-turn repeated** post-submit / quote-style reply stems, and **recheck** with a short live Role C battery.

## Why now

Hardened Role C runs surfaced **TRUTH_HANDOFF_READY_CONTACT_GAP** and **REPLY_REPEATED_BLOCK** as dominant weaknesses: they hurt broker trust and long-turn demo quality more than new features would help right now.

## Read-first docs

- `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md`
- `docs/PROJECT_TRUTH_SWITCH.md` §6A
- `docs/sprints/TRUTH_INTENT_REPLY_THREE_LAYER_STANDARD_SPRINT/02_THREE_LAYER_STANDARD_SPEC.md`

## Scope

**In scope:** Add-Car only; contact/readiness alignment; bounded reply variation / de-dup; short backend Role C recheck; small sprint docs.

**Out of scope:** NLU redesign, CRM/workflow engine, broad UI, non–Add-Car lanes.

## Target outcome

- **Truth:** Fewer contradictions between “ready” and missing name/phone on **turn 4+** pre-submit; post-submit threads align `still_needed` with office-held identity when `formal_submitted_at` exists.
- **Reply:** More distinct stems on late post-submit turns via engine fallback pools + pack `zh_alt`/`en_alt` for `*_submitted` keys.
- **Validation:** Guardrail green; Role C 5-turn × 3 personas recheck with oracle summary.
