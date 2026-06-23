# P16 Policy Review / Quote Readiness — North Star Strategy

**Date:** 2026-06-22  
**Type:** Strategic review — no implementation  
**Audience:** Andy · Chen Kui · Wu Xiaojie · future cofounder · potential investor  
**Authority:** Builds on `P16_DECISION_FREEZE_V1.md`, `P16_TECHNICAL_ARCHITECTURE_SUMMARY.md`, `P16_REQUEST_FRAMEWORK.md`, `P16_BROKER_PAIN_RESEARCH.md`, `P16_INSURANCE_OFFICE_PAIN_EXPANSION_REVIEW.md`, ADR-001/003  
**Status:** Recommendation for review — not a decision freeze

---

## 1. Executive Summary

P16 Add-Car Readiness Engine is **validated and deployable**. It proves the core pattern:

> Messy customer documents → structured Trusted Packet → broker can act in under 60 seconds.

The strategic insight from Chen Kui’s office is correct: **Add-Car is the wedge, not the ceiling.**

The bigger commercial pain is not “add a vehicle.” It is:

- “Why is my premium so expensive?”
- “Can you find me a cheaper policy?”
- “Should I switch from Geico / AAA / Progressive?”
- “Did my current carrier overcharge me?”

These questions share one structural job: **assemble the current policy from fragmented evidence, decide whether the broker has enough to shop or re-quote, and tell the broker what to do next** — without P16 ever touching carrier systems.

**Recommendation:** Evolve the north star from **Add-Car Readiness** to **Quote Readiness** — a broker-facing engine that turns declaration pages, renewal notices, insurance cards, and premium screenshots into a **Policy Snapshot Packet** plus **Savings Opportunity Signals**. Add-Car remains one lane inside the same product, not a separate product.

**What changes:** New extraction schema, new readiness rules, new broker-facing analysis layer.  
**What does not change:** No carrier APIs, no quote engine, no premium promises, same three readiness states, same Trusted Packet + Copy Packet model.

**Why now:** Add-Car de-risked the hardest technical bet (vision extraction + source attribution + Postgres cases). Declaration-page extraction is the **highest-WTP, highest-frequency revenue moment** in the office (renewal + carrier switch + quote shopping). The Request Framework already anticipated this as V2 request type N2.

**2-day demo path:** Chen Kui uploads a real declaration page → system returns Policy Snapshot + “QUOTE_READY / NEED_INFO / BROKER_REVIEW” + broker next action + Chinese customer follow-up draft + 2–3 savings *signals* (not prices).

---

## 2. New North Star

### Candidate (recommended)

> **Turn whatever a Chinese insurance customer sends about their current policy — declaration page, renewal notice, insurance card, premium screenshot — into a Quote-Ready Policy Snapshot in under 60 seconds.**
>
> **If anything is missing for shopping or switching carriers, the Chinese follow-up is already written.**
>
> **If the case is ready, the broker sees savings opportunity signals and the next action — not a fake quote.**

### Shorthand

**Quote Readiness Engine** — *document in, broker-ready policy snapshot + opportunity signals out.*

### What this north star explicitly is

| Is | Is not |
|----|--------|
| Policy data intake from real customer documents | A quoting or rating product |
| Quote **readiness** (can the broker shop now?) | Premium **prediction** |
| Savings **opportunity signals** (why premium may be high, who to prioritize) | Savings **guarantees** |
| Broker next action + customer follow-up draft | Autonomous carrier submission |
| Retention + win-back enablement for Chen Kui’s office | A CRM, AMS, or agency OS |

### Why this beats “Add-Car only” as north star

| Dimension | Add-Car only | Quote Readiness |
|-----------|--------------|-----------------|
| Broker pain rank (#1 in research) | #7–10 frequency wedge | **#1 renewal + quote shopping** |
| Revenue moment | Transactional (new car) | **Annual retention + carrier switch** |
| Customer question answered | “What do I send to add a car?” | **“Why is my rate high? Can you help?”** |
| WTP signal | $49/mo proven entry | **$99–$199/mo** (research consensus) |
| Reuse of built stack | 100% | **~70%** — same engine, new schema |

Add-Car stays valuable as the **on-ramp**: it proves trust, ships today, and feeds the same case store. Quote Readiness is the **expansion story** investors and Chen Kui will pay for.

---

## 3. Two-Stage Model

### Stage 1 — Policy Data Intake

**Customer uploads (any combination):**

| Document | Typical role | Extraction value |
|----------|--------------|------------------|
| **Declaration Page** | Primary — full policy snapshot | Highest: vehicles, drivers, limits, premium, term |
| **Renewal Notice** | Premium delta + renewal date | Carrier, new premium, effective date, sometimes violation flags |
| **Current Policy / dec page PDF** | Same as declaration | Same |
| **Insurance ID Card** | Quick VIN + carrier + dates | Partial — one vehicle only; no limits/drivers |
| **Premium screenshot** | WeChat / carrier app / email | Premium amount, sometimes carrier; rarely full limits |

**AI extracts (with source attribution per field):**

| Bucket | Fields |
|--------|--------|
| **Policy identity** | Carrier, policy number (if visible), named insured, policy term, effective / expiration dates |
| **Premium** | Total premium, term (6-mo / 12-mo), per-vehicle premium if shown |
| **Vehicles** | VIN, year, make, model, garaging ZIP (per vehicle) |
| **Drivers** | Name, DOB, DL# (if visible), relationship |
| **Coverage** | BI/PD limits, UM/UIM, comp/collision deductibles, med pay |
| **Risk signals** | Violations, accidents, SR-22 flags — **only if explicitly visible on document** |
| **Gaps** | Missing drivers, missing VINs, limits not visible, multi-vehicle card-only upload |
| **Provenance** | `source_file`, `source_quote`, confidence, conflict flags |

**Output:** **Policy Snapshot Packet** — structurally parallel to Add-Car Trusted Packet.

### Stage 2 — Opportunity / Savings Readiness Analysis

**Input:** Policy Snapshot Packet + optional broker context (renewal season, target carriers — manual, not API).

**AI produces (broker-facing only):**

| Output | Purpose |
|--------|---------|
| **Quote Readiness state** | Can broker open carrier portals and start quotes now? |
| **Savings Opportunity Signals** | Prioritization hints — not prices |
| **Broker Next Action** | One line: “Run 3-carrier compare” / “Request DL for second driver” / “Explain violation surcharge — do not promise savings” |
| **Customer Follow-Up Draft** | Chinese WeChat-ready message for missing items or “we’re reviewing your policy” |
| **Risk / Missing Info Warnings** | Coverage gaps, incomplete driver list, premium screenshot without limits |

**Safe signal examples (Phase 2):**

- `LIKELY_SWITCH_CANDIDATE` — renewal within 45 days + complete vehicle/driver snapshot
- `SAVINGS_REVIEW_WORTHY` — premium visible + full dec page extracted (broker can shop)
- `HIGH_TOUCH_PRIORITY` — multi-vehicle household + high stated premium
- `CROSS_SELL_OPPORTUNITY` — UM/UIM low or missing vs CA norms (broker judgment)
- `FOLLOW_UP_BEFORE_QUOTE` — missing DL#, garaging ZIP, or second vehicle VIN
- `PREMIUM_DRIVER_VIOLATION` — violation/accident visible on dec page or renewal notice
- `DO_NOT_OVERPROMISE` — SR-22, recent accident, teen driver visible — savings unlikely without coverage change
- `INSUFFICIENT_EVIDENCE` — insurance card only; cannot assess savings opportunity

**Hard rule:** Every signal must cite **document evidence** or **explicit missing-field logic**. No invented violations. No fabricated competitor rates.

---

## 4. Business Pain Analysis

### The Chen Kui post pattern

> “Two vehicles, $1197 / 6 months. One violation. Otherwise it would be $800+.”

This is not a quoting problem. It is a **translation + prioritization** problem:

1. Customer sees a number ($1197) without context.
2. Broker knows *why* (violation surcharge) and *what would change it* (clean record, different carrier, coverage adjustment).
3. Broker must decide: spend 45 minutes shopping, or explain and retain on current carrier.
4. Today Wu Xiaojie spends 20–40 minutes **assembling** the policy before any of that judgment happens.

P16 Stage 1 eliminates assembly. P16 Stage 2 surfaces **which cases deserve shopping effort** and **which need expectation-setting first**.

### Pain ranking (broker office)

| Rank | Pain | Quote Readiness fit |
|------|------|---------------------|
| 1 | Renewal + “why did my premium go up?” | **Primary** — dec page + renewal notice |
| 2 | Incomplete documents on every request | **Inherited** — NEED_INFO + Chinese follow-up |
| 3 | Carrier switch re-intake | **Primary** — same dec page extraction |
| 4 | WeChat document hunting | **Inherited** — one upload link, one case ID |
| 5 | “Can you beat Geico?” quote shopping | **Primary** — quote readiness, not quotes |
| 6 | Add car | **Existing lane** — already built |
| 7 | Teen driver premium shock | **Partial** — violation/driver signals; emotional call stays with broker |

### Customer pain (downstream of broker product)

Customers do not buy software. They benefit when Chen Kui:

- Responds faster at renewal (“you’re not ignoring me”)
- Explains premium in Chinese with structured facts
- Shops proactively instead of waiting for the customer to call Geico

Quote Readiness makes Chen Kui **look faster and more prepared** — the retention weapon against direct carriers.

### Commercial wedge

| Segment | Add-Car | Quote Readiness |
|---------|---------|-----------------|
| Frequency | Spiky (car purchases) | **Continuous (every policy, every year)** |
| Revenue tie | New business | **Retention + rewrite commission** |
| Competitive threat | Dealer pressure | **Geico / AAA / Progressive direct + bilingual gap** |
| Chen Kui quote | “Saves time on加车” | **“Helps me keep customers and win them back from Geico”** |

---

## 5. Reuse from Add-Car

### Can the architecture be extended quickly?

**Yes.** The Request Framework principle holds:

> **New request type = new schema, not new product.**

Estimated reuse: **~70% of stack, ~30% new (schema + prompts + rules + UI labels).**

### High reuse (keep as-is)

| Asset | Location / pattern | Reuse |
|-------|-------------------|-------|
| Document upload UX | `AddCarPage.tsx` wizard (steps 0–5) | Same flow; new intent + copy |
| Multipart extract API | `POST /api/intake/add-car/extract` pattern | Generalize to `/api/intake/{lane}/extract` or `request_type=policy_review` |
| Vision OCR pipeline | `ocr_kill_test/extractor.py` | Same providers (Gemini/OpenAI), new prompt schema |
| PDF text-layer extraction | PyMuPDF VIN path | Extend to policy numbers, premium regex |
| Packet builder | `packet_builder.py` — merge, conflicts | Same merge/conflict logic |
| Field attribution model | `ExtractedField` + `source_file` | Identical pattern |
| Readiness states | ADR-001 READY / NEED_INFO / BROKER_REVIEW | Same three states, different critical fields |
| Copy Packet | `copy_text` clipboard block | New template for policy snapshot |
| Case persistence | `save_case()`, Postgres `service_records` | New `service_lane = policy_review` |
| Case ID + phone key | `case_{hex}`, phone lookup | Same |
| Deployment | Vercel + Cloud Run + `deploy_paid_pilot.sh` | Same |
| Document guidance / follow-up | `_assess_document_relevance()` pattern | New missing-field messages |
| Bilingual customer messaging | Existing triage templates + guidance | Extend for policy docs |
| No carrier API | ADR-003 | Unchanged |

### Partial reuse (adapt)

| Asset | Adaptation |
|-------|------------|
| VIN validation | Per-vehicle loop; NHTSA checksum on each VIN |
| Document type detection | Add: `declaration_page`, `renewal_notice`, `premium_screenshot` |
| `document_guidance` | “Upload declaration page” vs “upload purchase agreement” |
| Frontend readiness compute | New critical-field set |
| OCR kill-test corpus | Add dec pages to `test_data/` (gap today — mostly add-car docs) |
| Service lane routing | Workbench filter by `policy_review` |

### New work required

| Item | Why |
|------|-----|
| **Policy review field schema** | 8 add-car fields → 25–35 policy fields |
| **Multi-vehicle / multi-driver structures** | Arrays, not flat VIN |
| **Coverage limit parsing** | BI 100/300, comp/coll deductibles — format variance by carrier |
| **Extraction prompt v2** | Dec page layout literacy (Mercury vs Geico vs Progressive) |
| **Opportunity signal rules** | Stage 2 — rule layer on top of packet (can start heuristic, not ML) |
| **Dec page test corpus** | Real redacted dec pages — **biggest validation risk** |
| **UI intent screen** | “Review my policy / find savings” vs “Add a vehicle” |
| **Packet copy format** | Carrier-portal paste layout for full household |

### Risky areas

| Risk | Severity | Mitigation |
|------|----------|------------|
| **Dec page OCR accuracy** | High | Start with native PDF dec pages; broker BROKER_REVIEW on conflicts; never auto-quote |
| **Coverage mis-extraction** | High | Flag limits as “needs confirmation”; wrong limits → wrong quotes → E&O |
| **Invented violations** | Critical | Extract only visible violations; empty if not on document |
| **Insurance-card-only uploads** | Medium | NEED_INFO — cannot claim quote-ready |
| **Premium screenshot without context** | Medium | Extract premium; warn “limits unknown — dec page required” |
| **Savings overpromise** | Critical | Signals use “may” / “broker to verify”; `DO_NOT_OVERPROMISE` state |
| **Scope creep to quote engine** | High | ADR-003 holds; demo shows signals not prices |
| **Multi-policy households** | Medium | BROKER_REVIEW when multiple policies detected |

---

## 6. New Field Schema

### Phase 1 essential fields (minimum for demo + pilot)

**Critical for QUOTE_READY (all must be present or derivable):**

| Field | Why essential |
|-------|---------------|
| `carrier` | Every downstream action is carrier-aware |
| `policy_term_end` or `renewal_date` | Prioritization + urgency |
| `total_premium` + `premium_term` | Savings conversation anchor |
| `vehicles[]` — at least one with `vin`, `year`, `make_model` | Cannot quote without vehicles |
| `named_insured` + `customer_phone` | Case identity |
| `garaging_zip` (per vehicle or policy-level) | Rating input |

**Important but not blocking READY (flag ⚠️):**

| Field | Notes |
|-------|-------|
| `drivers[]` — name, DOB | Often on dec page; may need DL# follow-up |
| `coverage` — BI limits, comp/coll deductibles | Needed for apples-to-apples compare |
| `policy_number` | Broker lookup; not always customer-visible |
| `violations[]` / `accidents[]` | Only if printed on document |

**Optional / enrich:**

| Field | Notes |
|-------|-------|
| Per-vehicle premium | When dec page breaks it out |
| UM/UIM limits | Cross-sell signal |
| Lienholders | Less critical for shopping than add-car |
| Prior carrier | Switch context |

### Schema shape (conceptual)

```
PolicySnapshotPacket
├── policy
│   ├── carrier, policy_number, named_insured
│   ├── term_start, term_end, premium_total, premium_term
│   └── source_attribution per field
├── vehicles[] 
│   └── vin, year, make_model, garaging_zip, coverages{}, source...
├── drivers[]
│   └── name, dob, dl_number?, source...
├── risk_signals_visible[]
│   └── type, description, source_file (violation/accident/SR-22)
├── missing_for_quote[]
│   └── field, reason, customer_action
├── warnings[]
│   └── conflicts, low_confidence, multi_policy
└── opportunity_signals[]  (Stage 2)
    └── signal_id, rationale, evidence_refs[]
```

### Document-type → field coverage (expected)

| Document | Carrier | Premium | Vehicles | Drivers | Limits | Violations |
|----------|---------|---------|----------|---------|--------|------------|
| Declaration page | HIGH | HIGH | HIGH | HIGH | HIGH | MEDIUM |
| Renewal notice | HIGH | HIGH | LOW | LOW | LOW | MEDIUM |
| Insurance card | HIGH | LOW | ONE only | LOW | LOW | LOW |
| Premium screenshot | MEDIUM | HIGH | LOW | LOW | LOW | LOW |

**Phase 1 acceptance criterion:** Declaration page PDF → ≥85% of critical fields on 3 real redacted samples (internal bar before Chen Kui demo).

---

## 7. Readiness States

Keep ADR-001 exactly three states. **Do not add** `SAVINGS_FOUND`, `QUOTED`, or `SWITCH_RECOMMENDED`.

### Policy Review lane definitions

| State | Meaning | Broker sees |
|-------|---------|-------------|
| **READY** | Enough to open carrier portals and start quotes | Policy Snapshot + opportunity signals + “Copy All” |
| **NEED_INFO** | Missing critical quote inputs | Missing list + Chinese follow-up draft |
| **BROKER_REVIEW** | Data present but trust issue | Conflicts, partial dec page, card-only upload upgraded to snapshot |

### Critical vs optional (Policy Review)

**Critical (missing any → NEED_INFO):**

- Carrier (or “unknown carrier” with dec page that failed carrier parse)
- At least one vehicle VIN + YMM
- Total premium OR renewal notice with premium
- Policy term end / renewal date
- Garaging ZIP (policy or per-vehicle)
- Named insured + phone

**Optional (missing → ⚠️ on READY packet):**

- Full driver list with DL#
- Complete coverage limits
- Violation history
- Second vehicle if broker knows household is multi-car (BROKER_REVIEW if detected mismatch)

### Stage 2 overlay (not a fourth state)

`opportunity_signals[]` and `broker_next_action` sit **inside** the packet. They do not change READY/NEED_INFO/BROKER_REVIEW.

Example broker_next_action strings:

- READY + `LIKELY_SWITCH_CANDIDATE` → “Shop Mercury, Infinity, Progressive — packet complete”
- READY + `DO_NOT_OVERPROMISE` → “Call customer first — explain violation impact before shopping”
- NEED_INFO → “Send Chinese follow-up: need declaration page + second driver DL”

---

## 8. Demo Recommendation

### Best 1–2 day demo for Chen Kui

**Title:** “Policy Review in 60 Seconds — from Declaration Page to Quote-Ready Packet”

**Duration:** 5–7 minutes live  
**URL:** Same Vercel app — new intent: “Review my policy / 帮我看看保费” (route TBD: `/policy-review` or intent on unified entry)

### Demo script (beat-by-beat)

| Minute | Action | Chen Kui takeaway |
|--------|--------|-------------------|
| 0–1 | Pain hook: “Renewal season — 客户问为什么涨了，吴小姐要先花半小时整理资料？” | Names her #1 pain |
| 1–2 | Customer uploads **one declaration page PDF** + optional renewal notice | Same upload UX as add-car |
| 2–3 | Extraction runs (15–30 sec) | Same trust pattern |
| 3–4 | **Policy Snapshot Packet**: 2 vehicles, premium $1197/6mo, carrier, limits, drivers | “不用重新录入” |
| 4–5 | **Opportunity panel**: violation visible → `PREMIUM_DRIVER_VIOLATION` + `DO_NOT_OVERPROMISE` + broker next action | “AI不会乱报价，但告诉我该先打电话还是先比价” |
| 5–6 | **Copy All** → paste into EZLynx / carrier portal | Same money moment as add-car |
| 6–7 | **Chinese follow-up** (second beat): re-run with insurance-card-only → NEED_INFO + ready-to-paste WeChat | “缺材料时消息都写好了” |

### Demo cases (prepare 2)

1. **Happy path:** Full dec page, 2 vehicles, 1 violation visible → READY + violation signal + “shop after customer conversation”
2. **Gap path:** Insurance card only → NEED_INFO + Chinese “请上传保单声明页”

### What makes Chen Kui say yes

She does **not** need to see a fake Progressive quote. She needs to see:

1. **Time collapse** — 30–45 min assembly → 60 sec  
2. **Retention weapon** — respond to “Geico quoted me” before customer switches  
3. **Liability safety** — source on every field; BROKER_REVIEW on conflicts; no auto-bind  
4. **Chinese follow-up** — Wu Xiaojie’s repetitive WeChat drafting eliminated  

### Minimum viable workflow (pilot)

```
Customer receives link (WeChat)
  → Selects "Policy review / 保费咨询"
  → Name + phone
  → Uploads dec page (or best available docs)
  → System extracts Policy Snapshot
  → Readiness evaluated
  → Broker gets packet in office queue
  → Broker copies into quote tools (manual)
  → Broker calls customer with facts + recommendation (human)
```

No customer login. No quote display. No carrier API. Phone + case ID return key — same as add-car.

---

## 9. Two-Day Sprint Plan

**Goal:** Chen Kui-demoable Policy Review v0 — not production-hardened.

### Day 1 — Stage 1: Policy Snapshot Intake

| Block | Deliverable |
|-------|-------------|
| Morning | Policy review schema doc + extraction prompt v1 (dec page focused) |
| Morning | 3–5 redacted dec pages in test corpus (Chen Kui office or public samples) |
| Afternoon | Backend: `request_type=policy_review` on extract path OR parallel route |
| Afternoon | Packet builder: multi-vehicle, premium, carrier, term |
| EOD | CLI/script demo: PDF in → Policy Snapshot JSON out |

### Day 2 — Stage 2: Signals + Demo polish

| Block | Deliverable |
|-------|-------------|
| Morning | Rule-based `opportunity_signals` + `broker_next_action` (10–15 rules) |
| Morning | `copy_text` template for policy snapshot |
| Afternoon | UI: intent selector or `/policy-review` minimal page (clone add-car wizard) |
| Afternoon | Chinese `document_guidance` for top 3 missing-doc patterns |
| EOD | Run demo script twice; fix one real failure mode |

### Explicitly out of 2-day scope

- Workbench queue UI for policy_review lane
- GCS file retention
- Comparison of two dec pages (year-over-year premium delta)
- Driver license upload lane
- Automated re-upload loop (Business Loop — future)

### Success gate

Chen Kui watches one real dec page become a copy-ready packet with violation signal and says: **“这个比加车更常用”** (“We’d use this more than add-car”).

---

## 10. What NOT to Build

Aligned with ADR-003 and Decision Freeze.

| Do not build | Reason |
|--------------|--------|
| Carrier APIs (Mercury, Geico, Progressive, etc.) | Permission, liability, not the wedge |
| Quote engine / EZLynx integration | Incumbents’ category; P16 ends at packet |
| Premium calculation or “estimated savings $X” | False precision → trust collapse + E&O |
| “We found you a cheaper policy” customer messaging | P16 does not know market rates |
| Side-by-side carrier price comparison UI | Requires live rating |
| AMS write-back | Broker’s system |
| Automated carrier bind / policy change | Legal + trust |
| Customer-facing quote display | Wrong product surface |
| ML churn model | No training data; heuristic signals sufficient for v0 |
| New readiness states | ADR-001 violation |
| Separate product brand for policy review | One engine, multiple lanes |
| Timeline / workflow engine | ADR-002 |

### Language guardrails (customer + broker)

**Say:**

- “Your policy information was sent to your broker.”
- “Your broker will review savings options and contact you.”
- “Based on your documents, a violation may be affecting premium — your broker will explain.”

**Never say:**

- “You can save $400 by switching.”
- “Progressive would charge less.”
- “Your current carrier overcharged you.”

---

## 11. Final Recommendation

### Key questions — answers

| # | Question | Answer |
|---|----------|--------|
| 1 | New north star? | **Quote Readiness Engine** — policy documents → quote-ready snapshot + opportunity signals in 60 seconds |
| 2 | What to call it? | **Externally:** “Quote Readiness” or “Policy Review & Quote Readiness.” **Avoid:** “Insurance Opportunity Engine” (vague). **Avoid:** “Savings Engine” (implies guaranteed savings). **Internal lane:** `policy_review` |
| 3 | Best 1–2 day demo? | Declaration page → Policy Snapshot → violation/switch signals → Copy All → card-only NEED_INFO Chinese follow-up |
| 4 | Minimum viable workflow? | Link → upload dec page → packet + readiness → broker copies to quote tools → human call |
| 5 | Reuse from P16? | ~70%: upload UX, OCR pipeline, packet model, Postgres cases, readiness states, deployment, Copy Packet |
| 6 | Must NOT build yet? | Carrier APIs, quotes, savings dollar amounts, AMS, automated bind |
| 7 | Chen Kui “keep customers / win from Geico”? | Faster renewal response + complete policy snapshot before customer shops alone + Chinese expectation-setting on violations |
| 8 | Essential Phase 1 fields? | Carrier, term, premium, vehicles (VIN/YMM), garaging ZIP, named insured, phone |
| 9 | Safe Phase 2 signals? | Switch candidate, review-worthy, follow-up-before-quote, violation surcharge, do-not-overpromise, cross-sell hint — all evidence-backed |
| 10 | Connect to Add-Car? | **Same product, new lane** per Request Framework. Shared entry: “What do you need?” → add car \| review policy. Shared case store. Add-car remains shippable wedge; policy review becomes flagship north star |

### Naming recommendation

| Name | Verdict |
|------|---------|
| Policy Review Engine | Good for **Stage 1** (intake) — customer-understandable |
| **Quote Readiness Engine** | **Best umbrella** — broker-accurate, ADR-003 safe |
| Savings Readiness Engine | Risky — implies savings outcome |
| Insurance Opportunity Engine | Too abstract for demo |

**Recommended customer-facing:** “帮我看看保费 / Review My Policy”  
**Recommended broker-facing:** “Quote Readiness Packet”

### Strategic sequence

```
NOW (proven)     Add-Car lane — pilot, $49, trust
NEXT (2 days)    Policy Review v0 demo for Chen Kui
THEN (1–2 wks)   Dec page corpus hardening + workbench lane + N1 follow-up messages
LATER            Replace vehicle, add driver — same engine
NEVER v1         Carrier quote automation
```

### Decision ask

Approve evolution of north star from **Add-Car Readiness** to **Quote Readiness**, with Add-Car as lane 1 and Policy Review as lane 2 — **without** new ADR for carrier APIs, **with** schema addition to Request Framework when build starts.

### One sentence for investor / cofounder

> We built document extraction for add-car; the same engine turns declaration pages into quote-ready policy snapshots so Chinese insurance brokers can retain customers at renewal and win them back from direct carriers — without us ever touching carrier APIs or quoting.

---

*Related: `P16_REQUEST_FRAMEWORK.md` §5 (V2 Renewal / Quote Shopping) · `P16_NORTH_STAR_VALIDATION_V1.md` (N2 declaration page) · `adr/ADR_003_NO_CARRIER_API_V1.md` · `P16_BROKER_PAIN_RESEARCH.md`*
