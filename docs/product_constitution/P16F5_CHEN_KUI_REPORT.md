# P16-F.5 Phase 5 — Chen Kui Simulation

**Date:** 2026-05-31  
**Persona:** Chen Kui (陈魁) — broker owner, California auto office, Chinese-speaking clients, WeChat-heavy  
**Preview:** Sprint A Preview (CORS-blocked) + backend engine evidence

---

## Profile

Busy owner. Cares only whether this saves time on cancellations, missing docs, and add-car quotes. Payment decision at Day 7. No patience for "dev environment" excuses.

---

## Would I use this tomorrow?

**NO.**

Reason: Opening Preview today shows **Network Error** before any case loads. I cannot paste a real cancellation notice and get a draft to send on WeChat. The UI looks promising for 30 seconds, then fails. I would not trust my assistant to depend on it.

**If CORS fixed:** **MAYBE** — Sprint A default tab, paste copy, and practice scenarios match how I work. Would need one successful real cancellation paste on my phone/desktop.

---

## Would my assistant use it?

**NO** today.

Assistant needs: queue scan → pick urgent → copy draft. Empty/error queue on load kills the workflow. Assistant would stay in WeChat-only mode.

**If CORS fixed:** **LIKELY** — simplified filters (全部/需今天处理/24小时内), `broker_next_step` on cards, and paste-first flow fit 50+ messages/day. Training still needed for「更新客户新消息」buried UX.

---

## Would I pay $49?

**NO** — no proven minutes saved; product appears broken on the URL you sent me.

---

## Would I pay $99?

**NO** — same blockers; no office-wide ROI proof; no invoice/terms in hand.

---

## What blocks payment?

| Rank | Blocker | Severity |
|------|---------|----------|
| 1 | Preview CORS — cannot complete core loop | **Critical** |
| 2 | No 7-day trial with observation log / minutes saved | **Critical** |
| 3 | No $49/$99 on broker one-pager or in-product | High |
| 4 | No pilot terms / invoice template | High |
| 5 | Vercel login before product | Medium |
| 6 | Add-Car copy on cancellation wedge (tab suffix, header) | Medium |
| 7 | 客户报送 tab visible — assistant opens wrong tab | Medium |
| 8 | Production URL still old experience — link confusion | Medium |
| 9 | No WeChat workflow proof (paste OK, but must copy draft manually) | Low (accepted v1) |
| 10 | Draft quality varies on edge cases | Low until trial |

---

## What creates trust?

| Signal | Present on Preview? |
|--------|---------------------|
| 办公室工作台 default — no tab hunt | ✅ |
| 「不自动对外发送」trust tag | ✅ |
| 原样粘贴微信 — matches my workflow | ✅ |
| Cancellation-first intro (collapsed) | ✅ |
| Engineer PG/API chrome hidden | ✅ (runtime) |
| Demo queue → cancellation case | ❌ (CORS) |
| Real message → draft in &lt;60s | ❌ (CORS) |
| Pricing visible | ❌ |
| Founder kickoff + supervised Day 0 | Not yet scheduled |

---

## Chen Kui scorecard

| Horizon | Score /100 | Notes |
|---------|------------|-------|
| First impression (UI shell) | 68 | Good front door if API worked |
| First successful workflow | **5** | Blocked |
| Day 1 utility | **15** | Would revert to WeChat |
| Day 7 payment intent | **10** | No ROI evidence |
| **Overall Chen Kui** | **32 / 100** | vs P16-F **38**, P16-E assumed **72** |

---

## Verdict

Sprint A **UI improvements are directionally correct** for my office, but **Preview is not broker-trial-ready** until CORS is patched and I complete one supervised 5-minute cancellation paste with working API. Do not send this URL to me or my assistant until then.

---

*End of P16-F.5 Phase 5*
