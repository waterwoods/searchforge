# Fix Priority Spec — Outcomes From This Sprint Only

This sprint is **eval-only**. Use this table to queue **future** work if product owner agrees.

## Fix-now (none from mutation pack)

No **Trust-breaking** results on mutation scenarios. No automated regression on batteries.

## Fix-next (polish)

1. **MUT-A01 / MUT-A02 customer reply:** When the customer asks whether to send materials or offers to WeChat-send, prefer a short office line (“可以发微信/发截图即可”) instead of repeating the generic quote-ready handoff block.
2. **ACB-E07 (office hours):** First bubble is unrelated to insurance workflow; current `unclear` + “内容不完整” is **broker-awkward** for a simple hours question—route to FAQ or a neutral “联系办公室” answer (separate sprint).

## Acceptable (monitor)

- **Broker line “Run quote for 2021”** when make/model shorthand is `RAV4` only (model inference)—acceptable if office habit is to confirm full make/model on callback.

## Defer

- LLM-on paraphrase storms, OCR, carrier API, UI redesign.

## Single best next fix (if choosing one)

**Clarify materials Q&A on quote-ready threads** (MUT-A01/MUT-A02 pattern): preserves trust (already fixed) and improves **perceived** intelligence for Chen Kui demos.
