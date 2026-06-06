# P16-L Readiness Report — Validation Readiness Audit

**Date:** 2026-06-01  
**Sprint:** P16-L — Real Market Validation  
**Authority:** `NORTH_STAR_V1.md`, `CAPABILITY_MAP_V1.md`, `CAPABILITY_SCORECARD.md`, P16-I/J/K evidence  
**Constraint:** Feature-frozen. No new capabilities. Evidence only.

---

## Core workflow under test

```
Paste → Triage → Draft → Copy → Follow-up
```

**Constitution loop:** Paste → structured case → draft → you send (`NORTH_STAR_V1.md` §1)

---

## Question

Can a real broker complete Paste → Triage → Draft → Copy → Follow-up **without founder intervention**?

---

## Evidence summary (P16-I → P16-K)

| Layer | Status | Source |
|-------|--------|--------|
| Triage engine | ✅ Trial-ready (85/100); guardrail 13/13 PASS | Cap 2, P16-J walkthrough |
| Case record + draft | ✅ Works locally; draft quality varies | Cap 3, P16-J steps 3–8 |
| Follow-up paste | ✅ **追加客户补充** promoted (P16-I) | P16-J step 9 |
| Broker front door | ✅ 79/100 locally (product_only) | P16-I rescoring |
| Commercial pack | ✅ Pricing, terms, invoice, Day 0/7 scripts | P16-K complete |
| Broker-stable URL | ❌ Preview SSO; Production frozen pre–Sprint A | P16-J P0 #2–3 |
| Real trial proof | ❌ Zero completed 7-day trial | P16-K |
| Andy Preview E2E | ❌ Not logged | P16-J P0 #4 |

---

## Step-by-step workflow audit

| Step | Founder assisted | Founder nearby | Founder absent | Blocker if absent |
|------|------------------|----------------|-----------------|-------------------|
| **1. Open workbench** | ✅ Pass | ⚠️ Partial | ❌ Fail likely | Preview SSO; Production wrong UX |
| **2. Paste raw message** | ✅ Pass | ✅ Pass | ⚠️ Partial | Demo card competes with paste (P16-J #7) |
| **3. Triage output** | ✅ Pass | ✅ Pass | ✅ Pass | Engine works; ~30–60s wait needs expectation copy |
| **4. Review case + draft** | ✅ Pass | ✅ Pass | ⚠️ Partial | Long cases require scroll to draft |
| **5. Copy draft** | ✅ Pass | ✅ Pass | ✅ Pass | Single **复制客户草稿** CTA (P16-I) |
| **6. Follow-up paste** | ✅ Pass | ⚠️ Partial | ⚠️ Partial | Two mental models (reopen vs new paste) |
| **7. Reopen next day** | ✅ Pass | ⚠️ Partial | ❌ Fail likely | URL/login friction; no habit without stable URL |

**Full loop without intervention:** Only achievable today on **local product_only** or **screen-share from founder laptop**. Not on broker-owned URL alone.

---

## Readiness scores

### Founder assisted — **82 / 100** (Ready for supervised Day 0)

| Criterion | Met? | Notes |
|-----------|------|-------|
| Andy can demo full loop locally | ✅ | P16-J walkthrough 10/10 steps (step 10 partial on prod URL) |
| Day 0 script exists | ✅ | `CHEN_KUI_DAY0_SCRIPT.md` |
| Commercial artifacts ready | ✅ | P16-K: one-pager v2, terms, invoices |
| Observation log ready | ✅ | V2; V3 adds evidence fields |
| First value in &lt;5 min achievable | ✅ | Demo queue → cancellation case |
| Broker can paste real message with Andy on call | ✅ | API-proven; P16-G Chen Kui 75/100 first workflow |

**Verdict:** Supervised Day 0 can run **this week** if Andy uses local/screen-share OR fixes Preview URL first.

---

### Founder nearby — **58 / 100** (Not ready for unsupervised Days 1–7)

| Criterion | Met? | Notes |
|-----------|------|-------|
| Broker opens URL alone | ⚠️ | SSO wall on Preview; Production wrong |
| Broker pastes without asking "which tab?" | ✅ | Single surface (P16-I) |
| Broker copies draft without Slack/call | ⚠️ | First-time users may hesitate on draft quality |
| Broker does follow-up paste alone | ⚠️ | P16-J #15: reopen vs new paste unclear |
| Broker returns Day 2 without reminder | ❌ | No push; habit not formed |
| Founder available async (WeChat 24h) | Assumed | Required in PILOT_TERMS |

**Verdict:** Days 1–7 need **async founder availability**, not full supervision — but **stable URL is mandatory** before Day 1 alone.

---

### Founder absent — **32 / 100** (Not ready — do not attempt)

| Criterion | Met? | Notes |
|-----------|------|-------|
| Cold URL → product loads | ❌ | Preview 401 SSO; Production pre–Sprint A |
| 10-second comprehension | ⚠️ 72/100 | P16-J cold test; near gate locally only |
| Self-serve Day 1 (P11 benchmark) | ❌ | Was 28/100 unsupervised; UI improved but URL/commercial gaps remain |
| Payment ask without founder | ❌ | Zero proof layers filled |
| Assistant onboarded without founder | ❌ | Vercel login; no mandate; P16-G assistant 50/100 |

**Verdict:** Unsupervised trial **will fail** at URL load or Day 2 abandonment. Constitution and P16-J explicitly forbid unsupervised URL drop.

---

## Capability scorecard cross-check

| Capability | Score | Workflow step | Trial-ready? |
|------------|-------|---------------|--------------|
| 1 Broker Front Door | 79 | Open + orient | Yes (local); No (deployed URL) |
| 2 Urgent Triage | 85 | Paste → classify | Yes |
| 3 Case Record | 72 | Draft + structure | Yes |
| 4 Intake Collection | 68 | Paste surface | Conditional |
| 5 Case Lifecycle | 55 | Follow-up + queue | Conditional |
| 6 Trial Conversion | 68 | Evidence collection | Docs yes; proof no |
| 7 Founder Control | 68 | Gates + scripts | Partial |

**Overall product:** 74/100 — **demo-ready, not market-validated**.

---

## North Star §9 payment layers (readiness)

| Layer | Ready for trial? |
|-------|------------------|
| Quantitative (minutes saved) | ❌ — must be collected during trial |
| Behavioral (opens, copies) | ❌ — must be collected during trial |
| Infrastructure (prod URL) | ❌ — Preview SSO; Production frozen |
| Commercial (terms, invoice, pricing) | ✅ — P16-K closed |
| Qualitative (Day 7 Q3) | ❌ — must be collected at Day 7 |

**3 of 5 layers open.** Commercial closed. Proof and infrastructure block payment.

---

## Minimum blockers before Chen Kui Day 0 (ranked)

| # | Blocker | Blocks mode | Owner |
|---|---------|-------------|-------|
| 1 | No broker-stable URL | Founder nearby, absent | Eng/Andy |
| 2 | Andy Preview E2E not logged | All modes on deployed URL | Andy |
| 3 | Invoice payment details unfilled | Day 7 payment | Andy |
| 4 | No scheduled Day 0 + Day 7 calls | Trial execution | Andy |
| 5 | Zero real-case proof | Payment ask | Broker + Andy |

**Not blockers for supervised Day 0:** UI simplicity (passed), commercial docs (passed), triage engine (passed).

---

## Readiness verdict

| Mode | Score | Can start trial? |
|------|-------|------------------|
| **Founder assisted** | **82/100** | **Yes** — supervised Day 0 on local or fixed Preview |
| **Founder nearby** | **58/100** | **Conditional** — only after stable URL + Day 0 success |
| **Founder absent** | **32/100** | **No** — refuse unsupervised trial |

**Bottom line:** The **product loop works** when Andy is in the room. **Market validation has not started** because no broker has run the loop on real cases with logged evidence. P16-L exists to run that experiment — not to build more product.

---

*End of P16-L Readiness Report*
