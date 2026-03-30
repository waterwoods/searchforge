# PRE/POST-SUBMIT REGRESSION + CONTEXT + ROLE C 10-TURN — Final report

## Summary

Added a **deterministic regression pack** for Add-Car pre/post-submit reply oracles, wired it into **guardrail step 3c**, extended **Role C max turns** (with inject buffer), and implemented **`--truth-chain`** + preset **`sprint_10_turn`** so live batteries pass **`case_id`** after formal persist. Ran **four live 10-turn** variants against a **fresh uvicorn on port 8002** (repo code with `le=12`); default **8001** in this environment was still on an older cap (`le=10`) until restart.

## Directly verified

- `LLM_GENERATION_ENABLED=0` pre/post-submit regression script (all checks green).
- Live Role C × triage: C1–C4, 10 iterations each, `--truth-chain`, `chen_kui`, `http://127.0.0.1:8002`, ~3+ minutes wall time per variant batch (OpenAI-backed Role C).

## Strongest battery signal (sampled C1-style trace)

- **Post-submit phrasing** appeared after inject (`handed_off` / submitted-family copy once case existed).

## Weakest battery signal

- **Late-turn reply repetition**: same `add_car_quote_detail` / post-submit block repeated across many turns when the customer kept probing price/options — answers latest “topic” but with **low variety** and repeated contact-gap suffix.

## Top ranked issues

1. **Template repetition post-submit** (trust/demo) — same draft stem for many consecutive turns.
2. **Contact-gap tail noise** — “若姓名或电话尚未…” repeated even when thread may already contain contact (needs truth-aware gating).
3. **Ops drift** — long-lived demo server must **restart** to pick up Pydantic `max_turns` limits (422 until restart).

## Founder decision questions (short)

1. **Pre/post line tighter?** Yes for **deterministic** paths + batteries that now pass `case_id`; live qualitative still shows **quality** gaps (repetition), not truth inversion.
2. **Scripts missing context fixed?** **Role C battery** previously omitted `case_id`; **truth-chain** fixes that. Append route already used `reply_truth_context` from case.
3. **10-turn obvious problems?** **Repetition** and **generic quote-detail handoff** dominating late turns.
4. **Handoff replies “dumb”?** Less “wrong office receipt before submit” when truth-chain on; still **repetitive** after submit.
5. **Right rail / timeline?** Not UI-tested this sprint; API fields showed **handoff_pending** often with **post-submit** wording — possible **presentation** tension for rail (inferred).
6. **Next sprint?** **Post-submit reply routing variety + intent-specific stitching** (same truth, different surface), plus **contact-gap tail** gated on `still_needed_fields`.

## Worth it?

Yes: small diff, **regression lock** for wording, **battery realism** improved by persisted truth. Long-run robustness: **better for truth**, **still weak for conversational variety** at turn 8+.
