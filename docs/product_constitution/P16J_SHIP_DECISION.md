# P16-J Ship Decision

**Date:** 2026-05-31  
**Frame:** Today is launch day. Founder decides what ships.

---

## Decision matrix

| Channel | Choice | Label |
|---------|--------|-------|
| **Local product_only demo** | **B** | Ship after **1 day** |
| **Vercel Preview (broker URL)** | **C** | Ship after **1 week** |
| **Production (`ui-smoky-beta`)** | **D** | **Refuse to ship** |
| **Chen Kui unsupervised trial** | **D** | **Refuse to ship** |
| **First payment / invoice** | **D** | **Refuse to ship** |

---

## A. Ship immediately — why NOT

Would require all of:

- Andy completed authenticated Preview walkthrough (**not done**)
- Preview URL loads without SSO for broker (**not true**)
- Commercial pack in broker's hands (**missing**)
- Production reflects `901b0df` + product_only flag (**false**)

Engine and local UI are ready; **distribution and commercial layers are not**.

---

## B. Ship after 1 day — local / internal preview

**Recommended for Sprint A UI acceptance.**

**What ships:** Founder approval of **local** or **private** demo (`run_demo_local.sh`, screen share, recorded walkthrough).

**1-day checklist:**

1. Andy 15-min walkthrough on local `:5173` — log pass/fail per P16-I §7
2. Screenshot package for Chen Kui supervised kickoff deck
3. Trigger Preview redeploy with `901b0df` + persisted env vars

**Risk:** Low — no external broker dependency.

---

## C. Ship after 1 week — external Preview

**Recommended for broker-visible Preview URL.**

**Week holds:**

| Day | Action |
|-----|--------|
| 1 | `vercel deploy` from `901b0df`; persist `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1` |
| 1–2 | Andy authenticated E2E on Preview (paste ×3, demo queue, copy, append) |
| 2–3 | **P16-K Commercial pack** — $49/$99, pilot terms, invoice template |
| 3–5 | Optional: relax Preview SSO or provide broker allowlist |
| 5–7 | Supervised Chen Kui Day 0 scheduled (not unsupervised) |

**Why not immediate:** Preview may still serve pre-P16-I bundle; SSO blocks cold validation; no terms/price.

---

## D. Refuse to ship — production & payment

**Production:** `ui-smoky-beta` returns 200 but **wrong UX** (客户报送 default, Simulation visible, no P16-I simplification). Sending Chen Kui there would **destroy trust**.

**Payment:** North Star §9 requires commercial artifacts + trial proof — **zero layers met**.

---

## Explanation (founder voice)

Sprint A **built the right product locally**. P16-I fixed the story the 10-second test was failing — single surface, paste-first, cancellation copy, one copy button. I would **demo this to Chen Kui on a call today** from my laptop.

I would **not** email him a URL today. Preview login wall + uncertain deploy + no invoice = embarrassment risk.

I would **not** touch Production until we promote the same bundle and env flags — frozen is correct.

**Launch day truth:** Ship the **story** now; ship the **URL** in a week with commercial pack.

---

*End of P16-J Ship Decision*
