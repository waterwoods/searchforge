# Final report — ADD-CAR REALISTIC NA-CHINESE SIMULATION AUDIT

## What was tested

- **Engine**: `triage_conversation` with `LLM_GENERATION_ENABLED=0`, `CLIENT_ID=chen_kui` (rule path = pilot-safe deterministic behavior).
- **Harness**: Ad hoc battery (see `02_…`) + full `scripts/guardrail_inbox_triage.sh` after edits.
- **Code inspected**: `UnifiedIntakePage.tsx` (Add-Car UX), `inboxTriage.ts` types, `clientConfig.ts` copy keys, `triage.py` add-car routing/extraction, `markers.json`, `reply_templates.json`.

## What failed (pre-fix highlights)

1. **VIN 还没拿到** with a space (`VIN 还没`) → **false VIN collected** → premature quote-ready / wrong broker guidance.
2. **VIN 车行说还要等两天** → **unclear** (“内容不完整”) or wrong VIN flag — missing add-car markers / VIN-delay logic.
3. **配偶 + quote 怎么报 + 要不要驾照** → **missing_document** (驾照追件模板) — wrong office narrative.
4. **上次报的价太贵 + company/coverage** → **premium_review** draft — wrong thread vs new-quote price pushback.

## What improved (post-fix)

- VIN extraction respects **spaced negatives** and **dealer-not-ready-yet** phrasing.
- **可以先报 / 报的价** markers support common NA-Chinese shortcuts.
- Multi-driver quote questions route to **add-car customer_question** with add-car drafts.
- Quote-price objection with re-shop/coverage wording routes through **add-car** intent.
- **Guardrail: PASS** (full suite).

## What remains / fragile

- **Acknowledgement echo**: some drafts prepend a long **verbatim echo** of the customer bubble + punctuation glitches (`？。`) — office-realistic but rough; tune `_get_add_car_acknowledgement` / stitching later.
- **G already_sent** on a **single** turn still **collects** more vehicle slots before handoff — acceptable for data completeness, but can feel **repetitive** vs “你已发什么、办公室核对”.
- **LLM-enabled** deployments not re-audited here; rule path is what guardrails enforce.
- **Continuation** (same thread, weak prior context in synthetic turns) needs real multi-turn UI/API tests beyond this battery.

## Recommended next sprint

**Add-Car reply polish sprint**: shorten acknowledgements, fix `？。`, add-car **already_sent** single-turn handoff when vehicle context complete, and a small **NA-Chinese phrase pack** in client config for broker tone A/B.
