# P16-G Phase 4 — Role-C Revalidation (Round 2)

**Date:** 2026-05-31  
**Persona:** Role C — confused real user; no founder guidance  
**Preview:** https://ui-fvxlrxp4u-andys-projects-1f411b73.vercel.app/workbench/unified-intake  
**Constraint:** CORS fixed; browser automation still blocked at Vercel SSO  
**Method:** Post-CORS API evidence + bundle/source + P16-F.5 UI shell characterization

---

## Round 1 vs Round 2

| Metric | P16-F.5 (CORS broken) | P16-G (CORS fixed) | Delta |
|--------|----------------------|-------------------|-------|
| Overall Role C | **40 / 100** | **58 / 100** | **+18** |
| First 30 seconds | 65 | **68** | +3 |
| First 5 minutes | 28 | **55** | +27 |
| First 15 minutes | 38 | **58** | +20 |

Threshold for unsupervised trial readiness: **≥70** — **NOT MET** (was 40, now 58).

---

## First 30 seconds

**Journey:** Open link → Vercel login (if unauthenticated) → land on workbench.

| Observation | Impact |
|-------------|--------|
| SSO wall before product | Still friction — "is this a dev site?" |
| After login: 办公室工作台 selected | Good — no tab hunt |
| Wayfinding + paste visible | Good — finds entry in <10s |
| Header/tagline still Add-Car flavored | Mild confusion vs cancellation wedge |
| 客户报送 tab still visible | Wrong-path risk |
| Queue loads (post-CORS) | **Positive** — cases appear instead of Network Error |

| Dimension | Score /5 |
|-----------|----------|
| Clarity | 3.5 |
| Trust | 3.5 |
| Speed to orient | 4.0 |
| Would continue | 3.5 |

**First 30 seconds: 68 / 100** (+3 vs round 1)

---

## First 5 minutes

**Journey:** Queue visible → paste cancellation → 开始整理 → expect draft.

| Observation | Impact |
|-------------|--------|
| Queue loads with cases | **Fixed** — no instant "broken" signal |
| Paste + triage API path works | **Fixed** — cancellation category + draft returned |
| ~30s loading copy sets expectation | Good if API latency acceptable |
| Practice scenario buttons work (API) | Same CORS path — should succeed |
| 加载演示队列 should work | API POSTs allowed |
| No pricing / trial terms on screen | Payment path still invisible |
| Add-Car header vs cancellation wedge | Still confusing |
| Vercel login required first visit | Friction for cold open |

| Dimension | Score /5 |
|-----------|----------|
| Clarity | 3.0 |
| Trust | 3.0 |
| Speed | 3.0 |
| Would continue | 3.0 |
| Would pay | 2.0 |

**First 5 minutes: 55 / 100** (+27 vs round 1)

*Note: 55 assumes authenticated session. Unauthenticated user still fails at SSO (+0).*

---

## First 15 minutes

**Journey:** Try demo queue → paste second scenario → copy draft → consider sharing.

| Observation | Impact |
|-------------|--------|
| Core loop completable (API) | **Major improvement** |
| 客户报送 tab → Add-Car portal | Still reinforces wrong mental model |
| Draft quality on cancellation | Actionable English — trust + |
| No founder to explain product | Still alone — but product works |
| Cannot verify WeChat copy flow in automation | Uncertainty |
| Would tell colleague "try it" | **Maybe** — was "don't bother" |

| Dimension | Score /5 |
|-----------|----------|
| Clarity | 3.0 |
| Trust | 3.0 |
| Would continue | 3.0 |
| Would pay | 2.5 |
| Would recommend | 2.5 |

**First 15 minutes: 58 / 100** (+20 vs round 1)

---

## Qualitative answers (Round 2)

| Question | Answer |
|----------|--------|
| **What confuses me?** | Login wall; Add-Car labels on cancellation product; two tabs; no price |
| **What delights me?** | Paste works; draft appears; queue has real structure; broker tab already selected |
| **Would I continue?** | **Maybe** — if I got past login and completed one paste |
| **Would I quit?** | **Less likely** — was within 5 min; now might stay 15 min |
| **Would I pay?** | **No** — no demonstrated ROI, no terms, no price |
| **Would I recommend?** | **Unlikely** — would say "founder sent me a login link" not "buy this" |

---

## Verdict

CORS fix recovered **~18 points** on Role-C composite. The product is no longer instantly "broken." It is still **not unsupervised-trial-ready** (58 < 70) due to SSO friction, residual Add-Car copy, visible 客户报送 tab, and no commercial path.

---

*End of P16-G Phase 4*
