# P16 North Star Sync — June 2026

**Date:** 2026-06-22  
**Type:** Strategic sync — no implementation  
**Audience:** Andy · Chen Kui · Wu Xiaojie · founders · product  
**Context:** Add-Car pilot largely validated. Broker demo within 48 hours. Reassess north star before building more features.  
**Sources:** `P16_STRATEGIC_RETROSPECTIVE_MONTH1.md` · `P16_POLICY_REVIEW_QUOTE_READINESS_STRATEGY.md` · `P16_BUSINESS_REALITY_CHECK_V1.md` · `P16_REQUEST_FRAMEWORK.md` · `CURRENT_PRODUCT_SHAPE.md` · `P16_BROKER_PAIN_RESEARCH.md` · `P16_CHEN_KUI_DEMO_SCRIPT.md`

---

## 1. Executive Summary

P16 spent Month 1 proving a pattern: **messy customer documents → structured Trusted Packet → broker acts in under 60 seconds.** Add-Car validated that pattern end-to-end — OCR, PDF extraction, VIN validation, readiness states, Copy Packet, Postgres persistence, Cloud Run + Vercel, real broker (Chen Kui), real office operator (Wu Xiaojie).

The strategic question is no longer *whether document-first intake works.* It is *which broker pain the north star should name.*

**Verdict:** **Accept** the statement *"Add-Car validated the engine. Quote Readiness is the bigger north star"* — with one precision:

| Layer | What it is |
|-------|------------|
| **Engine (proven)** | Document upload → extraction → source attribution → READY / NEED_INFO / BROKER_REVIEW → Trusted Packet → Copy Packet |
| **Wedge (shipping)** | Add-Car lane — earns first $49, proves trust, daily office use on car purchases |
| **North star (commercial ceiling)** | **Quote Readiness** — policy documents → Policy Snapshot Packet → broker can shop, retain, or explain — without P16 ever quoting |

**48-hour demo recommendation:** Lead with **Policy Review Intake** (Candidate A) on a real declaration page. Layer **3–5 evidence-backed Opportunity Signals** (Candidate B lite) on top. Keep Add-Car as proven backup. Do **not** build carrier APIs, premium estimates, priority queues, or scoring models before the demo.

**One sentence for Chen Kui:**

> 客户发来保单，60 秒内变成可以比价的完整资料包；如果有违章或材料不全，系统会告诉吴小姐先打电话还是先比价，缺材料的微信跟进也写好了。

---

## 2. Recommended North Star

### Official north star (proposed update)

> **Turn whatever a Chinese insurance customer sends about their current policy — declaration page, renewal notice, insurance card, premium screenshot — into a Quote-Ready Policy Snapshot in under 60 seconds.**
>
> **If anything is missing for shopping or switching carriers, the Chinese follow-up is already written.**
>
> **If the case is ready, the broker sees savings opportunity signals and the next action — not a fake quote.**

### Shorthand

**Quote Readiness Engine** — *document in, broker-ready policy snapshot + opportunity signals out.*

### Product architecture (unchanged principle)

```
Customer Request (lane: add_car | policy_review | …)
→ Readiness
→ Broker Ready Packet
```

> New request type = new schema, not new product. (`P16_REQUEST_FRAMEWORK.md`)

### What the north star is and is not

| Is | Is not |
|----|--------|
| Information assembly for renewal, retention, carrier switch | A quoting or rating product |
| Quote **readiness** — can the broker shop now? | Premium **prediction** |
| Savings **opportunity signals** — prioritization hints | Savings **guarantees** |
| Broker next action + Chinese follow-up draft | Autonomous carrier submission |
| Add-Car as lane 1 inside one product | A separate add-car-only company |

### Chen Kui's three negations (still true, expanded scope)

From the Add-Car demo script — these remain the broker-facing value contract:

1. **No WeChat hunting** — documents uploaded once, case persisted
2. **No repeat calls** — missing items detected; Chinese follow-up drafted
3. **No re-keying** — Copy Packet into carrier portal / AMS

Quote Readiness applies all three to the **highest-frequency, highest-WTP office moment**: renewal and premium complaints.

---

## 3. Add-Car vs Quote Readiness

### Question 1 — Validate or reject?

**ACCEPT** — with framing, not replacement.

### Why accept

**1. Add-Car validated the engine, not the ceiling.**

Month 1 proved:

- Document-first beats conversation-first for structured insurance transactions
- Source attribution is non-negotiable and buildable
- Three readiness states map to real office judgment
- Postgres + phone-key cases work for Chinese broker workflow
- Deployment path (Vercel + Cloud Run) is production-viable

Add-Car was the **correct wedge** because it was frequent enough to pilot, document-dense, and liability-sensitive (wrong VIN = E&O). It de-risked the hardest technical bet.

**2. Quote Readiness names the bigger pain.**

From `P16_BUSINESS_REALITY_CHECK_V1.md` and broker pain research:

| Pain | Add-Car rank | Quote Readiness rank |
|------|--------------|----------------------|
| Renewal + quote shopping | Not solved | **#1 — every policy, every year** |
| Carrier switch re-intake | Not solved | **#3 — 45–90 min/case** |
| Incomplete documents | Partially solved | **#2 — inherited** |
| WeChat document hunting | Solved for add-car | **Inherited for all lanes** |
| Add car | **Core wedge** | Lane 1 |

The example *"My premium jumped from $600 to $1200"* is not an add-car problem. It is a **policy assembly + broker judgment** problem. Steps 1–4 of Chen Kui's workflow (ask for dec page, ask for renewal notice, read policy manually, extract vehicles/drivers/coverage) are exactly what Quote Readiness automates. Steps 5–7 (decide if re-shopping is worthwhile, enter carrier portals, explain outcome) stay with the broker — P16 ends at step 4 with signals for step 5.

**3. Commercial math favors Quote Readiness.**

| Dimension | Add-Car only | Quote Readiness |
|-----------|--------------|-----------------|
| Frequency | Spiky (car purchases) | **Continuous (every policy, every year)** |
| Revenue tie | New business transaction | **Retention + rewrite commission** |
| WTP signal | $49/mo entry | **$99–$199/mo** (research consensus) |
| Competitive threat | Dealer pressure | **Geico / AAA / Progressive direct** |
| Stack reuse | — | **~70%** — same engine, new schema |

**4. Chen Kui's retention story is Quote Readiness, not Add-Car.**

Add-Car saves Wu Xiaojie 8–12 minutes on a car purchase. Quote Readiness saves **20–45 minutes on every renewal and carrier switch** — and prevents the customer from calling Geico first. That is the pitch that converts a pilot into a $99 upgrade and a referral to another broker.

### Why this is not a rejection of Add-Car

Rejecting Add-Car would be wrong. Add-Car:

- Earns first revenue ($49)
- Proves extraction trust on real dealer documents
- Trains Wu Xiaojie on the upload-link habit
- Feeds the same case store and phone-key identity model
- Remains a daily lane (3–5 cases/month for an active agency)

**Add-Car is the on-ramp. Quote Readiness is the destination.**

### Nuance — what Add-Car validated vs what Quote Readiness must still prove

| Validated on Add-Car | Not yet proven for Quote Readiness |
|----------------------|-----------------------------------|
| Single-vehicle VIN extraction | Multi-vehicle dec page extraction |
| Purchase agreement PDF | Carrier-formatted declaration pages (Mercury vs Geico vs Progressive) |
| 8-field flat schema | 25–35 field policy schema (drivers[], coverage limits) |
| Add-car readiness rules | Quote-ready critical field set |
| Copy Packet for one vehicle | Copy Packet for full household |

The north star shifts **before** dec-page extraction is production-hardened — but the 48-hour demo must be honest about extraction risk. Demo on **native PDF dec pages** Chen Kui provides; never demo on insurance-card-only as happy path.

---

## 4. Opportunity Signals Analysis

### Question 2 — Candidate A vs Candidate B

| Candidate | What it is |
|-----------|------------|
| **A — Policy Review Intake** | Upload dec page / renewal notice / insurance card / policy PDF → Policy Snapshot + READY / NEED_INFO / BROKER_REVIEW + Copy Packet |
| **B — Savings Opportunity Signals** | Heuristic signals on extracted data: `PREMIUM_APPEARS_HIGH`, `VIOLATION_PRESENT`, `REQUOTE_RECOMMENDED`, `DO_NOT_OVERPROMISE`, `HIGH_PRIORITY_LEAD`, `FOLLOW_UP_REQUIRED` |

### Four-way comparison

| Criterion | Candidate A — Policy Review Intake | Candidate B — Opportunity Signals |
|-----------|-----------------------------------|-----------------------------------|
| **Broker value** | **Highest.** Eliminates 20–45 min of manual dec-page assembly — the office's biggest time sink. Wu Xiaojie copies packet into carrier portals. Direct ROI. | **Medium alone, high on top of A.** Signals help Chen Kui decide *shop vs explain vs call first* — but useless without extracted policy data. |
| **Demo impact** | **Highest.** "One PDF → full household in 60 seconds" is visceral. Chen Kui recognizes her daily pain immediately. | **High as a 30-second panel** — violation → `DO_NOT_OVERPROMISE` → "call customer before promising savings" is the retention insight. Weak if shown without A. |
| **Long-term product value** | **Platform layer.** Every future lane (carrier switch, renewal, add driver) needs policy snapshot extraction. A is infrastructure. | **Differentiation + pricing tier.** Signals justify $99–$149 vs $49. They encode broker judgment, not generic OCR. |
| **Build risk** | **High** — dec page format variance, multi-vehicle, coverage limits, E&O on wrong limits | **Low** — 10–15 heuristic rules on extracted fields; no carrier API; no ML |

### Which creates more broker value?

**Candidate A**, by a wide margin.

The biggest office cost is **information assembly**, not quoting. Chen Kui's own workflow lists assembly (steps 1–4) before judgment (step 5). Wu Xiaojie does not need AI to tell her premiums are high — she needs the **VINs, drivers, limits, and premium already on her clipboard** before she opens Mercury.

Signals without a Policy Snapshot are an empty dashboard.

### Which creates more demo impact?

**A + thin B** beats either alone.

- **Minute 1–4:** A — dec page upload → Policy Snapshot → Copy All. Chen Kui says: *"不用重新录入."*
- **Minute 4–5:** B lite — 2–3 signals with document citations. Chen Kui says: *"它知道要先打电话，不是乱报低价."*
- **Minute 5–6:** NEED_INFO beat — insurance card only → Chinese follow-up. Chen Kui says: *"缺材料时消息都写好了."*

B alone in a demo feels like a chatbot opinion. A alone feels like a better OCR tool. **A + B lite** feels like a broker copilot.

### Which creates more long-term product value?

**Both — in sequence.**

```
Stage 1 (A): Policy Snapshot Intake     →  $49–$99 wedge, platform reuse
Stage 2 (B): Opportunity Signals        →  $99–$149 tier, retention pricing
Stage 3:    Multi-lane routing          →  $149–$299 Intake Copilot
```

A is the **platform**. B is the **judgment layer** that competitors cannot copy with off-the-shelf OCR.

### Which should be built first?

**Build A first. Add B as a thin rule layer on demo day 2.**

| Priority | Build | Time | Demo role |
|----------|-------|------|-----------|
| P0 | Policy Review schema + dec page extraction + Policy Snapshot Packet | Day 1 | Primary demo beat |
| P0 | Copy Packet template for multi-vehicle household | Day 1 | Money moment |
| P1 | 3–5 signals only: `VIOLATION_PRESENT`, `DO_NOT_OVERPROMISE`, `FOLLOW_UP_REQUIRED`, `REQUOTE_RECOMMENDED`, `INSUFFICIENT_EVIDENCE` | Day 2 AM | Differentiation panel |
| P1 | `broker_next_action` one-liner | Day 2 AM | Chen Kui judgment aid |
| P2 | Chinese follow-up for policy-review NEED_INFO | Day 2 PM | Second demo beat |
| **Do not build** | `PREMIUM_APPEARS_HIGH` without benchmark data | — | Implies market knowledge P16 does not have |
| **Do not build** | `HIGH_PRIORITY_LEAD`, priority queue, opportunity scoring | — | CRM features; zero demo value in 48h |

### Signal design guardrails (non-negotiable)

Every signal must:

1. Cite **document evidence** (`source_file`, field quote) or **explicit missing-field logic**
2. Use **broker-facing language** — "may," "broker to verify," "visible on renewal notice"
3. Never imply competitor rates or guaranteed savings
4. Never invent violations, accidents, or SR-22 flags not visible on uploaded documents

Safe v0 signal set:

| Signal | Trigger (heuristic) | Broker action |
|--------|---------------------|---------------|
| `VIOLATION_PRESENT` | Violation text visible on dec page or renewal notice | Explain surcharge before shopping |
| `DO_NOT_OVERPROMISE` | Violation + recent accident flag OR SR-22 visible | Call customer first; set expectations |
| `REQUOTE_RECOMMENDED` | Full dec page extracted + renewal within 45 days | Open carrier portals — packet complete |
| `FOLLOW_UP_REQUIRED` | Missing DL#, second vehicle VIN, or garaging ZIP | Send Chinese follow-up before quoting |
| `INSUFFICIENT_EVIDENCE` | Insurance card only; no dec page | NEED_INFO — cannot assess |

Drop `PREMIUM_APPEARS_HIGH` from v0 — without market benchmarks it is either wrong or unprovable. Chen Kui will challenge it.

---

## 5. Broker Value Ranking

### Question 3 — What would actually impress Chen Kui?

Not engineers. Not investors. **Chen Kui** — agency owner, retention-focused, judges software by whether Wu Xiaojie stops re-reading WeChat and whether customers stay.

### Ranked list

| Rank | Item | Why Chen Kui cares |
|------|------|-------------------|
| **1** | **Policy Review lane (Quote Readiness)** | Names her #1 pain: renewal season, premium complaints, carrier switch. *"客户问为什么涨了，吴小姐要先花半小时整理资料"* — if that becomes 60 seconds, she pays $99 without negotiating. This is the retention weapon against Geico. |
| **2** | **Auto Chinese follow-up** | Wu Xiaojie's most repetitive daily task — 30–40 identical WeChat messages per month. Chen Kui does not write them; she feels the office throughput. Completes the north star promise that is **still not fully true** per Business Reality Check. Highest daily stickiness per engineering hour. |
| **3** | **Savings Opportunity Signals (evidence-backed, 3–5 only)** | Chen Kui is a **judgment broker**, not a data entry clerk. Signals that say *"violation visible — call before promising savings"* protect her reputation and E&O exposure. She does not need fake savings numbers; she needs **prioritization** when 15 renewals land in the same week. |
| **4** | **Better packet formatting (Copy All for policy snapshot)** | The money moment from Add-Car — VIN on clipboard, paste into portal — extended to **full household**: 2 vehicles, 3 drivers, limits, premium, term. If Copy All pastes cleanly into EZLynx / Mercury portal fields, Wu Xiaojie adopts it tomorrow. |
| **5** | **Priority queue** | Useful at 50+ open cases. Chen Kui's office today: one broker, one operator, ~10 pilot cases. She will not notice a queue in 48 hours. Build before broker #3, not before demo. |
| **6** | **Opportunity scoring** | Abstract. Chen Kui thinks in cases and relationships, not scores. A numeric score without explanation erodes trust. Signals with evidence > scores. |
| **7** | **Better OCR** | Invisible to Chen Kui. She does not care how the VIN was read. She cares that it is **correct and sourced**. Investing demo time in OCR accuracy messages is engineer vanity. Fix extraction silently; show outcomes. |

### What Chen Kui will say yes to

From demo script psychology and business reality check:

1. **Time collapse** — 30–45 min assembly → 60 sec (Policy Review)
2. **Retention weapon** — respond to "Geico quoted me" before customer switches
3. **Liability safety** — source on every field; BROKER_REVIEW on conflicts; no auto-bind; no fake quotes
4. **Chinese follow-up** — Wu Xiaojie's drafting eliminated

### What Chen Kui will say no to

- Fake Progressive quote
- "You can save $400"
- Customer-facing quote display
- Another chatbot
- Features that require her to change AMS workflow

### Other ideas worth naming (not for 48h)

| Idea | Verdict | Timing |
|------|---------|--------|
| Broker-initiated renewal link ("your renewal is in 30 days — upload dec page") | High value; requires broker-first flow not in current model | After policy_review lane ships |
| Year-over-year premium delta (two dec pages) | Powerful for "why did it go up" | After single dec page works |
| Renewal season batch queue | Operational; not demo | Month 3 |
| WeChat bot | Permanently frozen — paste-link works | Never v1 |

---

## 6. Demo Recommendation

### 48-hour broker demo — recommended script

**Title:** Policy Review in 60 Seconds — from Declaration Page to Quote-Ready Packet  
**Duration:** 6–7 minutes  
**Fallback:** Add-Car happy path (proven) if dec page extraction fails on rehearsal

### Beat-by-beat

| Minute | Action | Chen Kui takeaway |
|--------|--------|-------------------|
| 0–1 | Pain hook: renewal season — *"客户保费涨了来问，吴小姐要先整理半小时资料？"* | Names #1 pain |
| 1–2 | Customer uploads **one declaration page PDF** (+ optional renewal notice) | Same upload UX as add-car — no new learning |
| 2–3 | Extraction runs (15–30 sec) | Trust pattern she already saw on add-car |
| 3–4 | **Policy Snapshot Packet**: vehicles, drivers, premium, carrier, limits — each field sourced | *"不用重新录入"* |
| 4–5 | **Opportunity panel**: violation visible → `VIOLATION_PRESENT` + `DO_NOT_OVERPROMISE` + broker next action: *"先打电话解释，再比价"* | *"不会乱报价，但告诉我该做什么"* |
| 5–6 | **Copy All** → paste into carrier portal / EZLynx | Same money moment as add-car |
| 6–7 | **Second beat**: insurance-card-only upload → NEED_INFO + Chinese follow-up ready to paste | *"缺材料时消息都写好了"* |

### Prepare two cases

1. **Happy path:** Full dec page, 2 vehicles, 1 violation visible → READY + violation signals
2. **Gap path:** Insurance card only → NEED_INFO + Chinese *"请上传保单声明页"*

### Demo day checklist

| Item | Status assumption |
|------|-------------------|
| Add-Car lane working on production | ✅ Backup demo |
| Real dec page from Chen Kui office (redacted) | ⚠️ Must obtain before demo |
| Chinese follow-up for policy-review NEED_INFO | ⚠️ Build Day 2 or use add-car follow-up pattern |
| Remove `model_used` / prototype noise from packet header | Polish item |
| Do NOT demo premium savings numbers | Hard rule |

### What to say when Chen Kui asks "what about add-car?"

> 加车已经能用了，这是同一个引擎的第二条线。加车是交易，保单整理是每天都有的事。两个都是你的产品，不是两个产品。

### Success gate

Chen Kui watches one real dec page become a copy-ready packet with violation signal and says:

**"这个比加车更常用"**

---

## 7. Required Document Updates

### Question 4 — Document review findings

#### Outdated assumptions

| Document | Outdated assumption | Why outdated |
|----------|---------------------|--------------|
| `P16_BUSINESS_REALITY_CHECK_V1.md` (Jun 19) | North star stable at add-car; no scope expansion before first $49 | Add-Car now largely validated; first $49 path executing; N2 (dec page) timing has arrived |
| `P16_BUSINESS_REALITY_CHECK_V1.md` | "P16 today: Does not help" on renewal + carrier switch | Engine exists; only schema + prompts differ |
| `P16_REQUEST_FRAMEWORK.md` §5 | Renewal / Quote Shopping = V2, do not build now | Should become **Lane 2 (policy_review)** once 10-case add-car gate met or demo-forced |
| `P16_STRATEGIC_RETROSPECTIVE_MONTH1.md` Month 2 P2 | "Do NOT do renewal / carrier switch in Month 2" | Superseded by pilot validation + 48h demo need — with narrow scope (policy_review v0 only) |
| `CURRENT_PRODUCT_SHAPE.md` | Product = "Unified Intake + Workbench" with no lane model | Runtime truth lacks Quote Readiness / policy_review lane |
| `FOUNDER_ONE_PATH.md` §3 Demo | Demo flow ends at add-car scenarios | Needs policy review demo path |
| `UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` | "Active north star is Add-Car efficiency loop" | Macro outline lags P16 strategic evolution |
| `P16_CHEN_KUI_DEMO_SCRIPT.md` | Add-car only demo | Needs policy review companion script |

#### New assumptions (not yet in official docs)

| Assumption | Evidence |
|------------|----------|
| Add-Car pilot is largely validated (OCR, PDF, VIN, readiness, packet, deploy, real users) | User context + Month 1 retrospective |
| Biggest broker pain is policy assembly for renewal / retention / carrier switch | Broker pain research #1; Chen Kui office pattern |
| Quote Readiness is the commercial ceiling north star | `P16_POLICY_REVIEW_QUOTE_READINESS_STRATEGY.md` |
| Opportunity Signals are a Stage 2 overlay, not a fourth readiness state | Policy review strategy §7 |
| Two-stage model: (1) Policy Snapshot Intake, (2) Signals + broker next action | Policy review strategy §3 |
| `policy_review` is a service lane alongside `add_car` | Technical architecture pattern |
| Broker-initiated renewal intake will be needed for highest-WTP scenarios | Business Reality Check weakness #4 |

#### Contradictions

| Doc A | Doc B | Resolution |
|-------|-------|------------|
| Business Reality Check: "Execute add-car; north star stable" | Policy Review Strategy: "Evolve north star to Quote Readiness now" | **North star evolves; execution sequence stays disciplined** — add-car ships as lane 1; policy_review v0 is demo scope, not full production |
| Strategic Retrospective: "Don't expand request types until extraction works on one" | User: "Add-Car largely validated" | Add-car extraction gate **passed for pilot**; dec page is new extraction surface with its own corpus risk |
| Request Framework: V2 later for renewal | Policy Review Strategy: build in 2 days | Promote to Lane 2 in framework; keep V1 safety rules |
| Business Reality Check: N1 follow-up is most urgent gap | Demo plan leads with policy review | **Both** — N1 is 1–2 days and should ship in parallel; it amplifies both lanes |
| Chen Kui Demo Script: follow-up "auto-generated" | Business Reality Check: "N1 not yet built" | Demo script aspirational; runtime truth may lag — reconcile before demo |

#### Missing concepts (not in CURRENT_PRODUCT_SHAPE or REQUEST_FRAMEWORK)

- **Quote Readiness Engine** as product name / north star
- **Policy Snapshot Packet** as output artifact (parallel to Trusted Packet)
- **Opportunity Signals** layer with evidence citation requirement
- **`broker_next_action`** one-liner in packet
- **Service lane model** (`add_car`, `policy_review`) in runtime truth
- **Two-stage intake → analysis** architecture
- **Broker-initiated intake** for renewal season (future)
- **Language guardrails** for signals (no savings promises)

---

### Question 5 — Proposed updates (do not implement yet)

#### 5.1 `CURRENT_PRODUCT_SHAPE.md`

**Add section: Product lanes (paid pilot)**

```markdown
## Product lanes (paid pilot)

| Lane | Customer intent | Output | Status |
|------|-----------------|--------|--------|
| `add_car` | Add a vehicle | Add-Car Trusted Packet | Live |
| `policy_review` | Review policy / premium / renewal | Policy Snapshot Packet + opportunity signals | Demo / v0 |

**North star:** Quote Readiness Engine — messy policy documents → quote-ready snapshot in <60s.
Add-Car is lane 1; Policy Review is lane 2. Same engine, different schema.
```

**Add to "What we ship":**

- Quote Readiness: declaration page, renewal notice, insurance card, policy PDF → Policy Snapshot + READY / NEED_INFO / BROKER_REVIEW
- Opportunity signals: evidence-backed broker guidance only; no carrier API; no premium estimates

#### 5.2 `FOUNDER_ONE_PATH.md`

**§3 Demo — add row:**

| Scenario | Path |
|----------|------|
| Policy review (Quote Readiness) | Upload dec page → Policy Snapshot → signals → Copy All → NEED_INFO Chinese follow-up |

**Add reference:** `docs/p16/P16_CHEN_KUI_DEMO_SCRIPT.md` (add-car) + policy review demo script (to be created after sync approval)

**§15-minute orientation — add:** Skim `docs/p16/P16_NORTH_STAR_SYNC_JUNE2026.md` for lane model

#### 5.3 `P16_REQUEST_FRAMEWORK.md`

**Promote §5 entry to §4.3:**

```markdown
### 4.3 Policy Review / Quote Readiness (Lane 2)

**Use case:** Customer asks about premium, renewal, or wants to shop carriers.
**Required fields:** carrier, policy_term_end, total_premium, vehicles[] (VIN+YMM), named_insured, phone, garaging_zip
**Accepted documents:** declaration page (primary), renewal notice, insurance card, policy PDF
**Readiness:** same ADR-001 three states; different critical field set
**Output:** Policy Snapshot Packet + opportunity_signals[] + broker_next_action
**Status:** v0 demo target — not production-hardened until dec page corpus gate
```

**Update §5 V2 table:** Remove "Renewal / Quote Shopping" (now Lane 2); keep Switch, Add Driver, Address Change, Coverage Change as V2.

**Add §7 note:** Policy Review uses extended `POLICY DETAILS` bucket (premium, term, coverage limits, violations visible).

#### 5.4 `P16_BUSINESS_REALITY_CHECK_V1.md`

**Add amendment header:**

```markdown
**Amended by:** P16_NORTH_STAR_SYNC_JUNE2026.md (2026-06-22)
**Changes:** Add-car pilot gate largely met. N2 (declaration page / policy review) is now GO for demo + $99 upgrade path. North star wording evolves to Quote Readiness; add-car remains $49 wedge.
```

**Update Part 8 verdict:**

- `CURRENT_NORTH_STAR_SCORE`: revise to name Quote Readiness as ceiling, add-car as wedge
- `FASTEST_PATH_TO_$99`: move N2 from "after first $49" to "in parallel with $49 close if demo lands"
- `NO-GO — Any scope expansion before first $49`: narrow to **no carrier API, no quote engine, no CRM** — policy_review v0 is approved scope expansion, not forbidden scope creep

**Update Part 8 answer:**

Chen Kui pays $49 for add-car (Wu Xiaojie never hunts VIN in WeChat).  
Chen Kui pays $99 for Quote Readiness (Wu Xiaojie never re-reads a dec page on renewal).

#### 5.5 `P16_STRATEGIC_RETROSPECTIVE_MONTH1.md`

**Add section: Month 2 North Star Evolution (2026-06-22)**

```markdown
## Month 2 North Star Evolution

Month 1 proved the engine on add-car. Month 2 names the commercial ceiling:

**Quote Readiness Engine** — policy documents → Policy Snapshot → opportunity signals.

Add-Car remains lane 1 (wedge, $49, trust). Policy Review is lane 2 (retention, $99, demo).

**Revised Month 2 P0:**
- Policy Review v0 for Chen Kui demo (dec page → snapshot + thin signals)
- N1 Chinese follow-up (both lanes)
- Add-car production hardening (real cases, time savings tracker)

**Revised Month 2 P2 resist list:** unchanged on carrier API, quote engine, timeline UI, WeChat bot.
```

**Update Recommendations For Month 2 P2 table:** Change "Renewal / carrier switch request types" row to:

> Policy Review v0 only (declaration page lane). No full renewal calendar, no broker queue at scale, no carrier switch automation.

---

## 8. Final Recommendation

### Strategic decisions

| # | Decision | Recommendation |
|---|----------|----------------|
| 1 | Accept "Add-Car validated engine; Quote Readiness is bigger north star"? | **Yes** — evolve north star wording; keep add-car as lane 1 |
| 2 | 48h build priority | **A first** (Policy Review Intake), **B lite second** (3–5 evidence-backed signals) |
| 3 | Demo lead | **Policy Review** on real dec page; add-car as backup |
| 4 | Do not build before demo | Carrier API, premium estimates, priority queue, opportunity scoring, `PREMIUM_APPEARS_HIGH` |
| 5 | Build in parallel if possible | N1 Chinese follow-up (closes north star gap on both lanes) |
| 6 | Official doc updates | Five files per §7 — **propose only until Andy approves** |

### Execution sequence

```
NOW          Add-Car lane — pilot, $49, proven backup demo
48 HOURS     Policy Review v0 — dec page → Policy Snapshot → 3 signals → Copy All
             + NEED_INFO Chinese follow-up beat
WEEK 1–2     Dec page corpus hardening · 10 real cases time savings · first $49 invoice
WEEK 2–3     $99 upgrade pitch: "renewal mornings 45 min → 15 min"
MONTH 2+     Add driver lane · broker-initiated renewal link · minimal open-cases queue
NEVER v1     Carrier quote automation · fake savings · customer quote display
```

### The founder decision

Month 1 optimized what could be measured (conversation simulations). Month 2 must optimize what Chen Kui will pay for (renewal assembly + retention judgment).

**Do not build more add-car features before the demo.** Add-car is validated enough. The demo that unlocks $99 is a declaration page, not a better VIN parser.

**Do not build a quote engine to impress.** Chen Kui's trust collapses the moment P16 shows a fake savings number. Signals with evidence build trust.

**Do build the thing Wu Xiaojie will use every day in renewal season** — and the Chinese follow-up that eliminates her most repetitive WeChat draft.

### One sentence

> Add-Car proved we can read documents. Quote Readiness proves why Chen Kui keeps paying — because every renewal season, the office stops assembling policies by hand and starts deciding which customers to fight for.

---

*Strategy only. No code. No implementation. Andy approval required before document updates or build execution.*  
*Companion: `P16_POLICY_REVIEW_QUOTE_READINESS_STRATEGY.md` (detailed 2-day build plan)*
