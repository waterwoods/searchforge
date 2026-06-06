# P16-U Phase 8 — Remaining Open Issues

**Date:** 2026-06-01  
**Source:** Runner FAILs + parity audit + reality revalidation + inherited P16-R/Q gaps

---

## Open issues (ranked)

### P0 — Trial-killing

| # | Issue | FP | Evidence | Time to close | Risk if open |
|---|-------|-----|----------|---------------|--------------|
| 1 | **Preview SSO / cold 401** | FP-004 | Runner 2× FAIL; curl `_vercel_sso_nonce` | **5 min** (Andy dashboard) | Chen Kui Day 0 impossible |
| 2 | **Production stale bundle** | FP-013, FP-001 | `index-ctrXdUgj.js`; no P16-O markers | **15 min** after #1 | Wrong UI on only cold-access URL |
| 3 | **No shareable broker URL** | FP-014 | Preview 401 + Production wrong | Compound of #1+#2 | Trial cannot start |
| 4 | **Reality gap (paper vs deployed)** | FP-008 | 80% runner vs ~12 broker cold | Closes with #1–#2 | False sprint confidence |
| 5 | **Production wrong default tab** | FP-016 | Stale prod = customer portal first | Fixed by #2 promote | "Is this for quotes?" |

---

### P1 — Trust / evidence

| # | Issue | FP | Evidence | Time to close | Risk if open |
|---|-------|-----|----------|---------------|--------------|
| 6 | **Andy 15-min Preview E2E log** | FP-010, FP-015 | Never published on deployed URL | **15 min** after #1 | No proof of paste loop |
| 7 | **Vercel dashboard env persistence** | FP-003 | Preview scope flags not in dashboard | **10 min** | Redeploy without `-b` regresses |
| 8 | **Local API keys in `.env.cloudrun`** | FP-011 | 2 validate errors remain | **10 min** infra | Next deploy validation noise |
| 9 | **Commercial pack incomplete** | FP-009 | Invoice IDs empty (P16-K) | **30 min** Andy | Day 7 payment blocked |
| 10 | **Customer public path** | FP-012 | product_only hides customer tab | **M** eng | Cap 4 regression |

---

### P2 — Polish (defer post-trial)

| # | Issue | FP | Evidence | Time to close | Risk |
|---|-------|-----|----------|---------------|------|
| 11 | Engineer chrome on full-dev surfaces | FP-017 | Production stale UI | Fixed by prod promote | Trust |
| 12 | UI complexity / 5-second test | FP-007 | P16-N scores | Sprint work | Usage friction |
| 13 | Draft quality on thin input | FP-018 | Triage returns "need more context" | Prompt tuning | Day 3 friction |

---

## Closed or reduced this sprint

| Issue | Status | How |
|-------|--------|-----|
| CORS missing Preview origin | ✅ Closed P16-R | Runner PASS |
| P16-O not on Preview bundle | ✅ Closed P16-R | Runner PASS |
| Local env posture drift | 🟡 Partial P16-U | `.env.cloudrun` sync |
| "No automated health check" | ✅ Closed P16-T/U | Runner operational |

---

## Effort to trial-ready (critical path)

```
FP-004 SSO off          (~5 min)
    → Andy E2E log      (~15 min)
    → Prod promote      (~15 min)
    → Founder GO        (~5 min)
─────────────────────────────────
Minimum founder time:   ~40 min
```

**Agent-automatable remainder:** CORS on next deploy hash (if script run), documentation, runner re-check.

---

## Risk summary

| Risk | Likelihood | Impact |
|------|------------|--------|
| Send Preview URL before SSO check | High (historical) | Trial death |
| Promote Production before Preview E2E | Medium | Wrong prod + false confidence |
| Start P17 before distribution fixed | Medium | FP-008 recurrence |
| Skip observation log during trial | High | FP-009 / FP-015 |

---

*End of P16-U Phase 8 — Remaining Open Issues*
