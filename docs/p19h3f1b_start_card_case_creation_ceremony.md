# P19H-3f-1b — Start Card = Case Creation Ceremony

**Date:** 2026-07-09  
**Branch:** `sprint/p16-trust-layer`  
**Type:** Product contract (docs + tests) — no schema, no deploy

---

## Hard rule

```text
Formal customer-facing Claim case MUST emit Start Card.
No Start Card means no customer-facing formal Claim case has started.
```

Start Card copy marker: `【事故记录已开始 ✅】`  
Disclaimer: `这不代表已经向保险公司正式报案。`

---

## Equivalent Start Ceremony surfaces

| Surface | Behavior |
|---------|----------|
| **WeCom explicit start** | Customer says 我要理赔 / 开始理赔 / 新事故 → system creates Claim → emits Start Card |
| **H5 Task Page** | H5 page itself is equivalent Start Ceremony; must append to existing formal case, not silently create random case |
| **Future mini program** | Mini program start page is equivalent Start Ceremony |
| **Broker-created case** | Broker side must mark as formal; customer receives Start Notice on next customer-facing interaction if applicable |

---

## What is NOT Start Ceremony

- Random narrative → holding ack only (`【尚未开始事故记录】`)
- Random photo → `wecom_media_intake` holding
- Injury quick-reply alone (no open Claim) → holding gate
- Insurance Q&A → safe consultation reply

---

## Related

- `docs/p19h3f_case_boundary_start_end_card_trust_contract_recon.md`
- `docs/evidence/p19h3f1_case_boundary_policy_2026_07_09.md`
- `tests/test_p19h3f1_case_boundary_policy.py`

**Next:** P19H-3f-1b Deploy + smoke · then P19H-3f-2 True End Card on Broker Done
