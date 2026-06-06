# P16-R Phase 4 — P16-O Parity Check

**Date:** 2026-06-01  
**Sprint:** P16-R Deployment Parity & Reality Closure  
**Scope:** Customer Entry simplification (message-first landing)

---

## What P16-O means (acceptance strings)

| Marker | Meaning |
|--------|---------|
| `请把您的需求发给我们` | Message-first headline |
| `发送给办公室` | Single primary CTA |
| `我们不会自动回复` | Trust line (ui_copy) |
| Absent: 3-button category grid as hero | UX reduction |
| Absent: `办理加车报价` as empty-state hero | Cancellation-first wedge |

---

## Source inspection

| Location | P16-O present? | Evidence |
|----------|----------------|----------|
| `CustomerEntryTab.tsx` @ `d05e94d` | ✅ | `portalMessageFirstHeadline` render path in empty state |
| `CustomerEntryTab.tsx` @ `901b0df` | ❌ | `git show HEAD:…` had **0** `portalMessageFirstHeadline` at P16-Q |
| `configs/clients/chen_kui/ui_copy.json` | ✅ | `portal_message_first_headline`, `portal_send_cta` |
| `UnifiedIntakePage.tsx` | ✅ | product_only hides customer tab on broker deploy |

---

## Bundle inspection

| Bundle | File | `请把您的需求发给我们` | `发送给办公室` | `办理加车报价` |
|--------|------|------------------------|----------------|----------------|
| **Local** `dist/` | ui_copy + chunks | ✅ (1 file hit) | ✅ (via copy) | strings may exist in dead paths |
| **Preview latest** | `index-CKPYkrkL.js` | **1** | **1** | 7 |
| **Preview old** | `index-97qCgvUS.js` | **0** | **0** | 8 |
| **Production** | `index-ctrXdUgj.js` | **0** | **0** | 8 |

**Method:** `vercel curl --deployment <url>` + `grep -o` on JS; Production via public `curl`.

---

## UI inspection (deployed)

| URL | Cold access | Customer empty state |
|-----|-------------|----------------------|
| Preview `ui-iwnyo9ufa` | **401** — browser UI not verified cold | Bundle confirms P16-O **if** user passes SSO |
| Preview `ui-waterwoods` alias | **401** | Same deployment as latest Preview |
| Production `ui-smoky-beta` | **200** | **Pre-P16-O** — 3-button / 加车 hero (P16-Q snapshot) |

**Andy browser E2E on Preview:** Not run — blocked by Vercel SSO (unchanged from P16-Q).

---

## Parity table

| Environment | P16-O customer entry | Match local? |
|-------------|---------------------|--------------|
| Local `d05e94d` | ✅ | — |
| Preview latest | ✅ **bundle** | **🟡** — SSO + env drift risk |
| Preview old | ❌ | ❌ |
| Production | ❌ | ❌ |

---

## Phase 4 verdict

| Question | Answer |
|----------|--------|
| Does P16-O exist in Preview? | **Yes** — latest deploy `ui-iwnyo9ufa` (bundle proof) |
| Does P16-O exist in Production? | **No** |
| Can customer use P16-O on a URL today? | **No** on Production; **Only after SSO** on Preview |
| Is P16-O parity achieved? | **❌** — Production promotion pending; SSO blocks cold Preview |

---

*End of P16-R Phase 4 — P16-O Parity Check*
