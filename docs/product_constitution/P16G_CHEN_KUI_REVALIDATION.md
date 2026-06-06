# P16-G Phase 5 — Chen Kui Revalidation (Round 2)

**Date:** 2026-05-31  
**Persona:** Chen Kui (陈魁) — broker owner, California auto office  
**Preview:** Post-CORS Sprint A Preview + Cloud Run API evidence

---

## Round 1 vs Round 2

| Metric | P16-F.5 | P16-G | Delta |
|--------|---------|-------|-------|
| **Overall Chen Kui** | **32 / 100** | **54 / 100** | **+22** |
| First impression (UI shell) | 68 | **72** | +4 |
| First successful workflow | 5 | **75** | +70 |
| Day 1 utility | 15 | **48** | +33 |
| Day 7 payment intent | 10 | **22** | +12 |

---

## Would I use this tomorrow?

**MAYBE — supervised only.**

Reason: CORS is fixed. I can paste a cancellation notice and get a draft (API-proven; Andy must confirm on phone). UI still has Add-Car header and 客户报送 tab, but 办公室工作台 default and paste copy match how I work. I would not roll out office-wide until Andy walks me through one real WeChat paste on my device.

---

## Would my assistant use it?

**MAYBE — with training.**

Queue loads. Filters (全部/需今天处理/24小时内) and `broker_next_step` on cards fit 50+ messages/day **if** broker mandates use. Still need 15-min training on follow-up paste (更新客户新消息 buried). Vercel login is a problem for assistant onboarding.

---

## Would I pay $49?

**NO** — no 7-day trial completed, no minutes-saved log, no invoice in hand. Product works now; payment case not made.

---

## Would I pay $99?

**NO** — same blockers; no office-wide ROI proof.

---

## What blocks payment? (updated rank)

| Rank | Blocker | Severity | vs P16-F.5 |
|------|---------|----------|------------|
| 1 | No 7-day trial with observation log | **Critical** | unchanged |
| 2 | No $49/$99 on broker one-pager | **Critical** | unchanged |
| 3 | No pilot terms / invoice template | High | unchanged |
| 4 | Vercel login before product | High | unchanged |
| 5 | Production URL still pre-Sprint A | High | unchanged |
| 6 | Add-Car copy on cancellation wedge | Medium | unchanged |
| 7 | 客户报送 tab visible | Medium | unchanged |
| 8 | Andy supervised Day 0 not scheduled | Medium | unchanged |
| ~~9~~ | ~~Preview CORS~~ | ~~Critical~~ | **RESOLVED** |
| 10 | Draft quality on edge cases | Low until trial | unchanged |

---

## What creates trust? (updated)

| Signal | Present? |
|--------|----------|
| 办公室工作台 default | ✅ |
| 「不自动对外发送」trust tag | ✅ |
| 原样粘贴微信 | ✅ |
| Cancellation-first intro | ✅ |
| Engineer chrome hidden | ✅ |
| Demo queue → cancellation case | ✅ API path (browser pending Andy) |
| Real message → draft in <60s | ✅ API path |
| Pricing visible | ❌ |
| Founder kickoff + supervised Day 0 | Not scheduled |

---

## Verdict

Sprint A UI + working API **directionally correct** for my office. Preview is **broker-trial-candidate** after Andy completes supervised 5-minute cancellation paste — not before. Do not send unsupervised URL to assistant until Andy signs off browser E2E.

**Payment probability from Chen Kui lens: ~20%** (up from ~5% when Preview appeared broken).

---

*End of P16-G Phase 5*
