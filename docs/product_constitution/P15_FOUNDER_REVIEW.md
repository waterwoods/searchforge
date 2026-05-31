# P15 Founder Review

**Version:** P15  
**Date:** 2026-05-31  
**Audience:** Andy (founder)  
**Inputs:** Ratified V1 Constitution, P10/P11/P14-B audits, P15 Implementation Scoreboard, Gap Matrix, Top 50 ROI Fixes

---

## 1. What Are the Top 10 Blockers to Getting Chen Kui to Pay?

Ranked by payment impact (P11 TOP_20 + constitution proof layers):

| # | Blocker | Capability | Why it blocks $49–99 |
|---|---------|------------|----------------------|
| 1 | **Wrong first screen** — lands on 客户报送, never sees cancellation triage | 1 Front Door | Never reaches value → won't pay |
| 2 | **Engineer UI chrome** — PG/API/debug tags | 1 Front Door | "Beta / not for me" → trust broken |
| 3 | **No proven time savings on real cases** | 6 Trial Conversion | Paying for hope, not proof |
| 4 | **Production not validated** — cases may not persist | 7 Founder Control, 3 Case Record | Trust killer if refresh loses work |
| 5 | **Pricing not on one-pager** | 6 Trial Conversion | "How much?" unanswered at Day 7 |
| 6 | **No pilot terms or invoice** | 6 Trial Conversion | Can't expense; data/cancel unclear |
| 7 | **Day 1 fails without founder** (28/100 unsupervised) | 1 Front Door, 6 Trial Conversion | Needs 30-min kickoff every time → not scalable |
| 8 | **Simulation/playbook broken on prod UI** | 1 Front Door, 7 Founder Control | Training path fails; looks unfinished |
| 9 | **Draft quality inconsistent on real messages** | 3 Case Record | Faster to type in WeChat → no ROI |
| 10 | **Add-Car vs cancellation story split** | 1 Front Door, 4 Intake | Pays for triage; UI sells wrong wedge |

**Honorable mention (11–12):** Manual paste feels like extra work without triage win (#5 P11); ChatGPT "good enough" for drafts alone (#20 P11).

---

## 2. Which Blockers Disappear If Sprint A Ships?

Sprint A = Capability 1 Front Door bundle (trust + tab + first value + playbook parity).

| Blocker | After Sprint A? | Notes |
|---------|-----------------|-------|
| 1 Wrong first screen | **Yes** | Default broker tab + wayfinding |
| 2 Engineer UI chrome | **Yes** | product_only purge |
| 7 Day 1 fails without founder | **Mostly** | 28 → ~70 unsupervised; kickoff still helps |
| 8 Simulation/playbook broken | **Yes** | Inline 3 scenarios + doc sync |
| 10 Add-Car vs cancellation split | **Partially** | Intro collapse + cancellation auto-open; full GTM copy in Sprint B |
| 3 No time savings proof | **No** | Requires 7-day trial execution |
| 4 Production not validated | **No** | Sprint A parallel track O2–O3 (Founder Control) |
| 5 Pricing not on one-pager | **No** | Sprint B commercial |
| 6 No terms/invoice | **No** | Sprint B commercial |
| 9 Draft quality on real messages | **No** | Fix-now from trial log only |

**Summary:** Sprint A removes **4 blockers fully**, **2 partially**, leaves **4** to Sprint B + trial week.

---

## 3. Which Blockers Still Remain After Sprint A?

| # | Remaining blocker | Next sprint / action |
|---|-------------------|----------------------|
| 1 | No proven time savings | Week 2 supervised trial + observation log |
| 2 | Production not validated | Day 4 deploy + `/readyz` (parallel to Sprint A) |
| 3 | Pricing / terms / invoice | Sprint B Days 5–6 |
| 4 | Draft quality on real messages | Fix-now max 3 items from trial log |
| 5 | Manual paste skepticism | Win on cancellation minutes; measure in log |
| 6 | ChatGPT alternative | Sell case structure + queue in kickoff |
| 7 | Assistant adoption | 15-min training script (Sprint B) |
| 8 | Founder support bottleneck | L1 doc + 24h SLA in terms |
| 9 | No testimonial | Day 7 capture |
| 10 | Data retention fear | Pilot terms clause |

---

## 4. What Score Changes After Sprint A?

Assumes Sprint A complete **and** parallel deploy gate (O2–O3) passes. Commercial pack (Sprint B partial) not yet included.

| Capability | Before | After Sprint A | After Sprint A + Deploy | After Full Week 1 (+ Commercial) |
|------------|--------|----------------|---------------------------|----------------------------------|
| **1 Broker Front Door** | 35 | **72** | 72 | 75 |
| **2 Urgent Message Triage** | 85 | 87 | 87 | 88 |
| **3 Structured Case Record** | 72 | 72 | **78** | 78 |
| **4 Customer Intake Collection** | 62 | **74** | 74 | 76 |
| **5 Case Lifecycle Management** | 55 | **62** | 62 | 65 |
| **6 Trial Conversion** | 45 | 48 | 52 | **65** |
| **7 Founder / Operator Control** | 68 | 72 | **82** | 85 |
| **Overall (weighted)** | **60** | **68** | **72** | **76** |

### Score change narrative

- **Front Door 35 → 72:** Tab default, chrome hide, wayfinding, demo queue UX, inline practice — contract §6 largely met.  
- **Intake 62 → 74:** Paste copy + loading + correct surface promotion.  
- **Lifecycle 55 → 62:** Filter simplification only; follow-up prominence deferred to Sprint C.  
- **Founder Control 68 → 82:** Deploy + UX gate (if parallel track completes).  
- **Trial Conversion 45 → 65 (Week 1 full):** Pricing, terms, invoice unlock Day 7 conversation — not payment proof yet.  
- **Overall 60 → 72 (Sprint A + deploy)** or **76 (full Week 1)** — approaches 80 target; **80 requires trial evidence** (≥1 "worked" line + behavioral criteria).

---

## Constitution Chain Closure Check

| Link | P15 status |
|------|------------|
| North Star | ✅ Ratified (`NORTH_STAR_V1.md`) |
| Capability | ✅ 7 capabilities locked |
| Contract | ✅ 7 contracts with acceptance criteria |
| Backlog | ✅ `IMPLEMENTATION_BACKLOG.md` |
| Sprint | ✅ `SPRINT_A_FRONT_DOOR.md` defined |
| Code | ⏳ **Next step** — execute Sprint A tasks against files listed |

**Verdict:** Documentation chain is **closed**. First code commit under constitution = Sprint A Day 1 (default tab + chrome hide).

---

## Founder Decision Checklist

- [ ] Approve Sprint A scope (Capability 1 only — no creep)  
- [ ] Confirm parallel deploy Day 4 non-negotiable  
- [ ] Confirm $49/$99 + terms before Chen Kui URL  
- [ ] Schedule Day 8 kickoff only after Day 7 dry-run PASS  
- [ ] Commit to no new features during trial Days 9–14  

---

*End of P15 Founder Review*
