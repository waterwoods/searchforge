# Stage 2 Founder-Validated Closeout — Known-Customer Prefill Confirm

**Status:** **STAGE 2 SLICE CLOSED**  
**Date:** 2026-08-03  
**Branch:** `stage2/known-customer-prefill-confirm`

## Validated commit

| Item | Value |
|------|--------|
| Validated commit | `8b6ca01` (`8b6ca010e539e228222d3271329b2dc51e75eec7`) |
| Environment | Cloud QA only (`fiqa-api-qa`) |

## QA case

| Item | Value |
|------|--------|
| Case ID | `case_09ad6254614a` |
| Case ref | `CLM-0036` |
| Persona / scenario | 陈明 · Camry · `chen_camry_stage2_phone` |
| Isolated identity | `wx_qaiso_71396323b411da18ec19` |
| Customer task / Cap2 | `已有保单资料，客户已确认` |

## Validated workflow

Known-customer invite (`chen_camry_stage2_phone`)  
→ isolated Active Case (does not steal Stage 1 case)  
→ policy context prefill  
→ CONFIRM_EXISTING  
→ durable confirmation + Cap2 / Brief wording `已有保单资料，客户已确认`  
→ no insurance-card upload fabrication  
→ no Stage 1 VIN / no `办公室处理中`

## Evidence folder (SSOT)

`docs/evidence/stage2-known-customer-confirmation/20260803T231041Z-final-phone/`

Supporting automated packs:

- `20260803T215214Z-isolation/`
- `20260803T223719Z-founder-path/`
- `20260803T224211Z-founder-rescan/`
- `20260803T224745Z-founder-url-proof/`
- `20260803T211908Z/` (preflight)

## What “Stage 2 closed” means

- Founder phone path for known-customer confirm-existing is accepted on Cloud QA.
- Stage 1 frozen case `case_4e5adf36c637` remains a separate baseline; Stage 2 phone used isolated identity/case.
- Demo invite durability + failed-`dit` fail-closed client behavior are part of the accepted slice on commit `8b6ca01`.

## What it does not mean

- Not Production release or waterwoods retarget.
- Not paid-pilot / customer validation.
- Not closure of all Low copy polish (see L3).

## Known non-blocking follow-ups

1. **Generic copy `请先完成这一步`** — Low; UX ledger **L3**; do not block Stage 2 close.
2. Experience upload still relies on DevTools when CI private key is absent (operator path).

## Ops posture after closeout

- QA: **minScale=0 / maxScale=2** (cost-saving default restored)
- Production: untouched
- waterwoods: untouched
