# Final report — CONTACT-READINESS ALIGNMENT + LATE-REPLY DE-DUP + ROLE C RECHECK

## What was fixed

- **Truth / readiness:** Add-Car `handoff_ready` is cleared (turn **≥ 4**, pre-submit only) when name/phone remain in `still_needed_fields`; `next_best_question` nudges contact; after **`formal_submitted_at`**, name/phone are removed from `still_needed_fields` so post-submit truth matches office-visible record semantics.
- **Oracle:** `TRUTH_HANDOFF_READY_CONTACT_GAP` limited to pre-submit + turn ≥ 4 (turns 1–3 allowed quote-complete without contact in-bubble per MATURE_INTAKE).
- **Reply de-dup:** Post-submit fallback **pools** with per-turn rotation; **post-submit `zh_alt`** selection when pack provides alternates; Chen Kui `*_submitted` keys gained `zh_alt`/`en_alt` where missing.

## What improved

- Guardrail **PASS** (full pipeline).
- Role C 5-turn recheck: **0** `REPLY_REPEATED_BLOCK` across three personas; **0** heuristic warnings on family_vehicle + materials_first runs; price_sensitive/tough still showed **2** `TRUTH_HANDOFF_READY_CONTACT_GAP` on turns 4–5 (pre-submit path where thread had not yet obtained case_id + gate/oracle alignment — see weak spots).

## What remains weak

- **Tough persona / late pre-submit:** Can still surface contact-gap oracle until formal submit exists in the thread — expected until customer or system captures identity or user submits to office.
- **Append path** (`triage_for_append`) still forces `handoff_ready=True` by design — not changed in this sprint.

## Recheck result

- **Environment:** Local `http://127.0.0.1:8001`, `CLIENT_ID=chen_kui` via `--client-id chen_kui`.
- **Cases:** (1) price_sensitive / tough / 5 turns / truth-chain, (2) family_vehicle / realistic / 5 / truth-chain, (3) materials_first / realistic / 5 / truth-chain.
- **Verified:** No repeated-block oracle hits; post-submit threads cleaner on `still_needed` when `formal_submitted_at` present.

## Recommended next sprint

- Optional: align **append** flow with contact truth or document exception explicitly.
- Intent layer: further **split** generic vs timeline vs receipt on turns 5–8 when LLM collapses intent.

## Sprint timing (authoritative: operator log)

- Start: 2026-03-29 session (bounded hardening)
- End: same session after guardrail + Role C recheck
- Elapsed: ~60–90 minutes (implementation + validation)
