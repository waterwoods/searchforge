# Reality Validation Checklist

**Version:** V1 (P16-S)  
**Date:** 2026-06-01  
**Status:** Mandatory before every sprint GO verdict  
**Companion:** `POST_SPRINT_HEALTH_CHECK.md` § Reality, P16-Q simulation pattern

---

## Rule

**Localhost PASS is necessary but not sufficient.**

Every future sprint must answer all nine questions below with **Yes** on the **deployed Preview URL** (cold access, no Vercel login) — or document explicit N/A with defer reason.

One **No** on a non-deferred item → sprint **FAIL** for trial-facing work.

---

## Checklist

### Can Andy use it?

| # | Question | Yes | No | N/A | Evidence |
|---|----------|-----|-----|-----|----------|
| 1 | Open Preview URL in incognito without Vercel SSO? | ☐ | ☐ | ☐ | curl -sI |
| 2 | Complete paste → triage → draft → copy in 15 min? | ☐ | ☐ | ☐ | E2E log |
| 3 | Certify deployed UI matches local intent? | ☐ | ☐ | ☐ | Bundle grep |

**Fail example (P16-R):** Q1 = No (401 SSO); Q2 blocked; Q3 partial (bundle yes, access no).

---

### Can Role C use it?

| # | Question | Yes | No | N/A | Evidence |
|---|----------|-----|-----|-----|----------|
| 4 | Land on broker workbench (not 客户报送 default)? | ☐ | ☐ | ☐ | Screenshot |
| 5 | Understand product purpose in 10 seconds? | ☐ | ☐ | ☐ | 10-sec test |
| 6 | No engineer chrome (PG, Simulation, API URL)? | ☐ | ☐ | ☐ | Screenshot |

**Fail example (Production):** Q4 = No — wrong default tab, Add-Car header.

---

### Can Customer use it?

| # | Question | Yes | No | N/A | Evidence |
|---|----------|-----|-----|-----|----------|
| 7 | Single message box visible in 5 seconds? | ☐ | ☐ | ☐ | 5-sec test |
| 8 | Submit without category-first overload? | ☐ | ☐ | ☐ | P16-O strings |
| 9 | Customer path reachable on trial URL? | ☐ | ☐ | ☐ | URL test |

**N/A when:** Sprint is broker-only (P16-I product_only hides customer tab — document Cap 4 tradeoff).

**Fail example (pre-P16-R):** Q7 = No — 3 buttons + ①②③ before type.

---

### Can Assistant use it?

| # | Question | Yes | No | N/A | Evidence |
|---|----------|-----|-----|-----|----------|
| 10 | Process queue item without founder help? | ☐ | ☐ | ☐ | Simulation |
| 11 | Find append / follow-up without scroll hunt? | ☐ | ☐ | ☐ | UX audit |
| 12 | Copy draft and send manually in < 2 min? | ☐ | ☐ | ☐ | Timed test |

---

### Can Broker use it?

| # | Question | Yes | No | N/A | Evidence |
|---|----------|-----|-----|-----|----------|
| 13 | Day 0: paste real WeChat thread → useful draft? | ☐ | ☐ | ☐ | Sample paste |
| 14 | Day 0: complete first value in < 5 min unsupervised? | ☐ | ☐ | ☐ | Timed test |
| 15 | Day 3: draft language matches office (Chinese)? | ☐ | ☐ | ☐ | Draft inspect |
| 16 | Day 7: would return without founder screen-share? | ☐ | ☐ | ☐ | Journey sim |

**Fail example (P16-Q):** Q14 = No — SSO blocks Day 0; Q15 = No — English drafts.

---

### Can someone pay for it?

| # | Question | Yes | No | N/A | Evidence |
|---|----------|-----|-----|-----|----------|
| 17 | Pricing documented ($49/$99)? | ☐ | ☐ | ☐ | One-pager |
| 18 | Invoice sendable with real payment IDs? | ☐ | ☐ | ☐ | Invoice template |
| 19 | ≥1 observation log "worked" line with time saved? | ☐ | ☐ | ☐ | Log v3 |
| 20 | $49 ask defensible without damaging relationship? | ☐ | ☐ | ☐ | P16-Q verdict |

**Current state (P16-R):** Q17 = Yes · Q18 = No · Q19 = No · Q20 = No

---

### Can it be demonstrated?

| # | Question | Yes | No | N/A | Evidence |
|---|----------|-----|-----|-----|----------|
| 21 | Live demo on Preview to third party (not screen-share localhost)? | ☐ | ☐ | ☐ | Demo date |
| 22 | Demo survives without Andy clicking for broker? | ☐ | ☐ | ☐ | Hand-off test |
| 23 | Artifacts exist (log, screenshot, curl transcript)? | ☐ | ☐ | ☐ | File links |

---

### Can it survive Preview?

| # | Question | Yes | No | N/A | Evidence |
|---|----------|-----|-----|-----|----------|
| 24 | Cold curl returns 200 HTML? | ☐ | ☐ | ☐ | curl |
| 25 | CORS allows Preview origin? | ☐ | ☐ | ☐ | OPTIONS |
| 26 | Feature flags correct in Preview bundle? | ☐ | ☐ | ☐ | Bundle grep |
| 27 | Score ≥ Local − 10 on Preview? | ☐ | ☐ | ☐ | Scorecard |

---

### Can it survive Production?

| # | Question | Yes | No | N/A | Evidence |
|---|----------|-----|-----|-----|----------|
| 28 | Production promoted or explicitly deferred? | ☐ | ☐ | ☐ | Deploy log |
| 29 | Production UI correct for broker trial? | ☐ | ☐ | ☐ | Screenshot |
| 30 | Production ≤ 7 days behind Preview? | ☐ | ☐ | ☐ | Bundle date |

**Current state (P16-R):** Q28 = Deferred · Q29 = No · Q30 = No (41 days)

---

## Summary scorecard

| Dimension | Questions | Yes | No | N/A | Pass? |
|-----------|-----------|-----|-----|-----|-------|
| Andy | 1–3 | | | | ☐ |
| Role C | 4–6 | | | | ☐ |
| Customer | 7–9 | | | | ☐ |
| Assistant | 10–12 | | | | ☐ |
| Broker | 13–16 | | | | ☐ |
| Payment | 17–20 | | | | ☐ |
| Demonstration | 21–23 | | | | ☐ |
| Preview survival | 24–27 | | | | ☐ |
| Production survival | 28–30 | | | | ☐ |

**Pass threshold:** Zero **No** on Preview survival (24–27) and Broker Day 0 (13–14) for trial-facing sprints.

---

## Output

| | |
|---|---|
| **Overall** | ☐ **Pass** ☐ **Fail** |
| Sprint ID | |
| Preview URL | |
| Production URL | |
| Reality score (/100) | |
| Delta vs paper sprint score | |
| Reviewer | |
| Date | |

---

## P16-R baseline (reference)

| Dimension | Pass? | Blocker |
|-----------|-------|---------|
| Andy | Fail | SSO |
| Role C | Partial | SSO + chrome on Prod |
| Customer | Partial | Tab hidden product_only |
| Assistant | Unknown | SSO |
| Broker | Fail | SSO + English drafts |
| Payment | Fail | Empty IDs, no log |
| Demonstration | Fail | No cold Preview |
| Preview survival | Fail | 401 |
| Production survival | Fail | 41-day stale |

**Reality score P16-R:** ~68 weighted (bundle ~74, cold ~12)

---

*End of Reality Validation Checklist V1 — mandatory before GO verdict*
