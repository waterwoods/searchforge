# P4 Capability 03 — Smart Claim Start

**Status:** Design + mock planner implemented — awaiting Founder QA  
**Date:** 2026-07-24  
**Naming:** Capability (not Slice)  
**Governing SSOT:** `docs/product/p20_product_north_star.md`  
**Business Contract:** `docs/product/p20_business_contract.md`  
**Depends on:** Cap 01 `LookupResult` + Cap 02 `PrefillResult` (both APPROVED)  
**Identity prerequisite (reuse):** P29B / D-016 — `person_link_key` (unchanged)

---

## Founder Decisions (LOCKED)

1. **Customer primarily answers: “What happened today?”**
2. **Never ask twice. Never surprise. Never expose technical IDs.**
3. **One active claim** — resume beats create.
4. **One Capability, One Responsibility** — answers only: **“How do we present Start Claim so known context feels trusted and effort stays minimal?”**
5. **No CRM / no identity redesign / no DB redesign.** Consumes Cap 01 + Cap 02 only.
6. **Prefill is suggestion; claim case remains Source of Truth.**

---

## One objective / Out of scope

**ONE OBJECTIVE**

Given `LookupResult` + `PrefillResult`, produce a customer-ready **Smart Claim Start** plan (mode, known chips, confirm gates, question visibility, screens, CTAs) so an existing customer finishes Start Claim with roughly **five inputs instead of eighteen**, and a first-time viewer understands the page in under **30 seconds**.

**OUT OF SCOPE**

- Production AMS / CRM / EZLynx / Epic integration  
- Identity redesign / Customer table / DB redesign  
- Live Mini Program page rewrite in this loop (wiring = Implementation Plan next loop)  
- Expanding Start Claim Must Haves beyond Business Contract  
- Photos/docs/VIN as Start Claim blockers  

---

# Phase 0 — Capability Research

## What mature products do

| Product | Start Claim pattern | Known context | Still asked | Lesson for us |
|---------|---------------------|---------------|-------------|----------------|
| **GEICO** | App FNOL in ~5 min; logged-in path; photo estimate tools | Policy + vehicle from account | Loss facts, photos, sometimes other party | Logged-in = trusted identity; speed over form length |
| **Progressive** | App / web / guest; Claims center | Policy when logged in; guest collects basics | Loss facts; guest pays identity tax | Guest path must not crash; logged-in path should feel different |
| **Lemonade** | AI Jim; confirm car + phone; video story; pledge | Policy vehicles; contact | What happened (video), injury, other party later | Confirm vehicle when multi; story is the product; evidence staged |
| **Guidewire (FNOL patterns)** | Structured FNOL; policy/vehicle selection first | Policy graph | Loss event, parties, exposures | Confirm gates before narrative; never silent wrong vehicle |
| **Ping An / CPIC / WeChat MP** | 一键报案; 保单关联; 出险信息补全 | Bound policy after login | 出险时间/地点/经过; materials later | Mini Program: restore identity → show policy → ask loss → upload later |
| **Tencent Insurance / WeChat** | Lightweight MP; progressive disclosure | Session + bound account | Minimal loss facts first | Shell before network; no jargon; contact broker escape |
| **Spark Driver / gig patterns** | Fast incident report under stress | Known driver/vehicle when possible | What/when/where + photos | Stress UX: few taps, big CTAs, optional photos |

## Best practices

1. **Identity first, story second** — show “we know you” before asking for narrative.  
2. **Confirm only ambiguity** — multi-vehicle / stale policy / active case.  
3. **Stage evidence** — photos and documents after core FNOL (or Request More).  
4. **One primary CTA** — Continue / Confirm / Submit; contact broker is secondary.  
5. **Graceful guest/degrade** — blank accident form beats error walls.  
6. **Human language** — never policy_ref, VIN full, OpenID, match_status.

## Anti-patterns

| Anti-pattern | Why it fails |
|--------------|--------------|
| 18-field first screen | Stress + abandonment; feels like underwriting, not help |
| Silent wrong vehicle / policy | Trust destroyed; claim pollution |
| Chatbot that is a form in disguise | Same load, worse latency (GEICO FNOL lesson) |
| Blocking on photos/VIN/docs | Violates Business Contract; kills completion |
| Duplicate claim create | Two active cases; broker chaos |
| Exposing technical IDs | Confuses customer; privacy risk |
| “网络不稳定” for every failure | Hides real recovery path |

## Risks → Opportunities

| Risk | Opportunity |
|------|-------------|
| Wrong prefill | Confirm gates + edit-on-request chips |
| Multi-driver household | Default named insured; easy “不是我开的” edit later (future) |
| Lookup down | Blank degrade with accident Must Haves only |
| Over-asking damage | Collapse damage/photos as optional |
| CRM temptation | Keep adapter boundary at LookupResult only |

---

# 1. Capability Overview

```text
Cap 01 Who?          Cap 02 What do we know?       Cap 03 How do we start?
person_link            LookupResult                  LookupResult
     │                      │                        + PrefillResult
     ▼                      ▼                              │
LookupResult  →  PrefillResult  →  SmartClaimStartPlan     ▼
READ match         READ classify      READ present     Customer-ready
                                                      Start Claim UX
```

| | Cap 01 | Cap 02 | Cap 03 |
|--|--------|--------|--------|
| Question | Who is this customer? | What do we already know? | How should Start Claim feel? |
| Output | `LookupResult` | `PrefillResult` | `SmartClaimStartPlan` |
| Writes | None | None | None (planner only this loop) |

**Success feel:** “The system already knows me.”  
**Customer job:** Answer what happened today (plus rare confirms).

---

# 2. UX Flow Diagram

```text
Open Mini Program
        │
        ▼
 Identity restored (person_link — invisible)
        │
        ▼
 Cap 01 Lookup → Cap 02 Prefill → Cap 03 Plan
        │
        ├── CONTINUE_ACTIVE ──► One Active Case gate ──► Continue / Contact broker
        │
        ├── CONTACT_BROKER ──► Contact advisor (no silent start)
        │
        ├── BLANK_DEGRADE ──► Accident facts only ──► Optional photos ──► Review ──► Submit
        │
        └── MATCHED_* ──► Known chips shown
                              │
                              ├── vehicle confirm? ──► 哪辆车出险？
                              ├── policy confirm? ──► 保单可能已过期
                              ▼
                         Customer reviews chips
                              │
                         Edit on request (optional)
                              │
                              ▼
                         Accident facts only
                         (story / time / location / injury)
                              │
                              ▼
                         Photos optional (skip OK)
                              │
                              ▼
                         Review → Submit → Receipt → Home
```

## Decision points

| # | Decision | Options | Rule |
|---|----------|---------|------|
| D1 | Active case? | Continue vs Contact | Never create second claim |
| D2 | Ambiguous match? | Contact broker | No AUTO chips |
| D3 | Lookup unavailable / no mapping? | Blank degrade | Accident Must Haves only |
| D4 | Multi-vehicle? | Confirm vehicle first | No VIN blank form |
| D5 | Stale policy? | Confirm policy first | No silent trust |
| D6 | Chips OK? | Continue vs Edit on request | Never retype known fields from blank |
| D7 | Accident Must Haves complete? | Enable Submit | Same validator for CTA / hint / submit |
| D8 | Photos now? | Add / Skip | Never blocks Start Claim |
| D9 | Submit error? | Retry vs Contact | Distinguish transport vs server vs validation |

---

# 3. Screen-by-screen walkthrough

| Screen | Customer sees | Primary CTA | Notes |
|--------|---------------|-------------|-------|
| **entry_restore** | “正在为您准备” shell | — | Shell before network (North Star §J) |
| **one_active_case** | Existing case message | 继续当前报案 | S1 only |
| **confirm_vehicle** | Vehicle candidates (Camry / CR-V) | 确认车辆 | S2 |
| **confirm_policy** | Carrier + “可能已过期” | 确认后继续 | S4 |
| **known_context** | Chips: 姓名 / 电话尾号 / 车辆 / 保单 | 信息无误，继续 | Hidden on S5/S6 |
| **accident_facts** | 今天发生了什么？ + 4 Must Haves | 下一步 | Damage collapsed optional |
| **photos_optional** | Add photos or skip | 跳过 | After-submit OK too |
| **review_submit** | Known + accident summary | 提交给顾问 | One submit |
| **receipt** | Success | 返回首页 | Continue path thereafter |
| **contact_broker** | Need advisor help | 联系顾问 | Ambiguous |

**30-second comprehension test (matched path):**  
Headline “今天发生了什么？” + subtitle “我们已准备好您的信息” + visible chips + 4 fields + one CTA.

---

# 4. Question Decision Matrix

| Field | S1 Continue | S2 Multi-vehicle | S3 Matched | S4 Stale | S5/S6 Degrade |
|-------|-------------|------------------|------------|----------|---------------|
| customer_name | HIDDEN | chip EDIT_ON_REQUEST | chip | chip | BROKER_OWNED |
| phone | HIDDEN | chip (尾号) | chip | chip | BROKER_OWNED |
| vehicle | HIDDEN | **VISIBLE_CONFIRM** | chip AUTO | chip AUTO | BROKER_OWNED |
| policy | HIDDEN | chip | chip | **VISIBLE_CONFIRM** | BROKER_OWNED |
| vin / plate | HIDDEN | follows vehicle confirm (not primary ask) | chip plate optional | chip | BROKER_OWNED |
| accident_story | HIDDEN | VISIBLE_REQUIRED | VISIBLE_REQUIRED | VISIBLE_REQUIRED | VISIBLE_REQUIRED |
| accident_time | HIDDEN | VISIBLE_REQUIRED | VISIBLE_REQUIRED | VISIBLE_REQUIRED | VISIBLE_REQUIRED |
| accident_location | HIDDEN | VISIBLE_REQUIRED | VISIBLE_REQUIRED | VISIBLE_REQUIRED | VISIBLE_REQUIRED |
| injury | HIDDEN | VISIBLE_REQUIRED | VISIBLE_REQUIRED | VISIBLE_REQUIRED | VISIBLE_REQUIRED |
| damage | HIDDEN | COLLAPSED_OPTIONAL | COLLAPSED_OPTIONAL | COLLAPSED_OPTIONAL | COLLAPSED_OPTIONAL |
| photos | HIDDEN | COLLAPSED_OPTIONAL | COLLAPSED_OPTIONAL | COLLAPSED_OPTIONAL | COLLAPSED_OPTIONAL |
| documents / police / email | HIDDEN | BROKER_OWNED | BROKER_OWNED | BROKER_OWNED | BROKER_OWNED |

**Visibility legend**

| Visibility | Meaning |
|------------|---------|
| `VISIBLE_REQUIRED` | Blocks submit (Business Contract Must Have) |
| `VISIBLE_CONFIRM` | Must resolve before accident block |
| `COLLAPSED_OPTIONAL` | Expand on demand; never enablement |
| `HIDDEN` | Not on this path |
| `BROKER_OWNED` | Request More / workbench — not Start Claim expansion |

---

# 5. Prefill Presentation Rules

1. **Show confidence in human language** — “我们已了解您” / “我们会先记下事故情况”. Never HIGH/MEDIUM/LOW in customer UI.  
2. **Chips only for safe AUTO (or confirm-needed suggestions)** — name, phone last4, vehicle summary, carrier·status.  
3. **Mask phone** — `尾号 1234`, never full E.164 as hero.  
4. **Never show** `person_link_key`, OpenID, `case_id`, `vehicle_ref`, `POL-MOCK-*`, `match_status`.  
5. **VIN** — last4 only if shown; full VIN = Request More.  
6. **Stale policy** — show with warning chrome + confirm; do not present as quiet truth.  
7. **Multi-vehicle** — no primary vehicle chip value until chosen; show chooser.  
8. **Degrade paths** — zero identity chips; no apology essay; go to accident facts.  
9. **Broker confidence** — Cap 01 `lookup_confidence` stays on Broker Header, not customer chips.

---

# 6. Customer Editing Rules

| Situation | Rule |
|-----------|------|
| AUTO chip correct | No action — never retype |
| AUTO chip wrong | **Edit on request** → inline edit that field only; siblings preserved |
| Vehicle wrong (single) | Edit on request; do not clear name/phone |
| Multi-vehicle | Confirm step required before accident |
| Stale policy | Confirm or contact broker — no silent accept via Submit |
| Driver not named insured | Future: edit driver; default stays named insured (record only now) |
| Want new claim with active case | Blocked — Continue or Contact (One Active Case) |
| Optional damage/photos | Expand/collapse; clearing optional never blocks CTA |

**Never ask twice:** once confirmed or AUTO-accepted, field stays out of primary ask list for the session plan.

---

# 7. Failure Handling

| Failure | Customer experience | Recovery |
|---------|---------------------|----------|
| Lookup unavailable (S6) | Blank Smart Start (accident only) | Submit still works; broker fills identity later |
| No mapping (S5) | Same as S6 | Contact broker secondary |
| Ambiguous match | Contact broker screen | No form that guesses |
| Active case | Continue gate | No second create |
| Stale policy ignored | CTA blocked until confirm | Explicit options |
| Vehicle not chosen (S2) | CTA blocked | Chooser required |
| Validation missing Must Have | Field errors + missing hint | Same validator as CTA |
| Transport error | Retry submit | Distinct copy from server/validation |
| Server reject | Contact broker + retry if retryable | Never one opaque “网络不稳定” |
| Prefill wrong after submit | Broker corrects via workbench | Case is SoR; prefill was suggestion |

**Dead-end ban:** every mode has a primary CTA and at least one recovery path.

---

# 8. Scenario Review (S1–S6)

| Scenario | Mode | Est. inputs | Known shown | Effort verdict |
|----------|------|-------------|-------------|----------------|
| **S1** Existing + active | `CONTINUE_ACTIVE` | **1** (Continue) | via active case, not new form | Minimal — no re-ask |
| **S2** Multi-vehicle | `MATCHED_CONFIRM_VEHICLE` | **5** (1 confirm + 4 Must Haves) | 李娜 + phone; vehicle chooser | Confirm then story |
| **S3** No active | `MATCHED_KNOWN` | **4** | 陈明 + Camry + Mercury | Best “knows me” path |
| **S4** Stale policy | `MATCHED_CONFIRM_POLICY` | **5** | 王强 + Camry + stale confirm | No silent trust |
| **S5** No mapping | `BLANK_DEGRADE` | **4** | none | Graceful; no wall |
| **S6** Unavailable | `BLANK_DEGRADE` | **4** | none | Graceful; no wall |

**vs 18-field baseline:** S3 removes ~14 asks; S2/S4 remove ~13; S5/S6 still only 4 accident Must Haves (identity → broker, not customer tax).

**Simulation**

```bash
P4_CUSTOMER_LOOKUP_MOCK=1 PYTHONPATH=. python3 scripts/simulate_p4_cap03_smart_claim_start.py
PYTHONPATH=. python3 -m pytest tests/test_p4_capability_03_smart_claim_start.py -q
```

**Expected:** `RESULT: PASS` and pytest green.

---

# 9. Implementation Plan

| Phase | Work | Status |
|-------|------|--------|
| A | `SmartClaimStartPlan` contract + engine | **Done (this capability)** |
| B | S1–S6 simulation + pytest | **Done** |
| C | Founder design package (this doc) | **Done** |
| D | Mini Program: fetch lookup→prefill→plan; render chips + confirms | **Next loop** |
| E | Keep `startClaimValidation.ts` Must Haves; bind plan visibilities | **Next loop** |
| F | Stamp AUTO into case facts on create (suggestion copy, not CRM write) | **Later loop** |
| G | AMS/EZLynx/Epic adapter behind Cap 01 facade | **Future Cap — no Cap 03 change** |

**Live wire constraints (when authorized)**

- Feature flag chain: Cap 01 mock/AMS flag → Cap 03 presentation only if plan present  
- Flag off / degrade → today’s accident form (already close to BLANK_DEGRADE)  
- No DB migration  
- No identity change  

---

# 10. Founder QA Package (≤10 minutes)

## Executive Summary

**Smart Claim Start** turns Cap 01 + Cap 02 into a customer-ready plan: known chips, rare confirms, and accident Must Haves only. Existing matched customers answer ~4–5 things, not 18. No CRM. No identity redesign. Planner is mock-complete; live Mini Program wiring is the next controlled loop.

## Architecture

```text
Mini Program / sim
  → Cap 01 lookup_customer(person_link)
  → Cap 02 build_prefill_result(LookupResult)
  → Cap 03 build_smart_claim_start_plan(LookupResult, PrefillResult)
  → SmartClaimStartPlan (mode, chips, questions, screens, CTAs)
  → (next loop) Start Claim UI
```

## Go / No-Go

| | |
|--|--|
| **GO** | Approve modes + question matrix + presentation/edit/failure rules; authorize next loop for Mini Program wire |
| **NO-GO** | Only if Founder requires CRM write-back, VIN/docs as Must Have, or multi-claim create now |

**Founder checkbox**

- [ ] Approve North Star: customer mainly answers “What happened today?”  
- [ ] Approve Capability Overview (§1) — Cap 03 presents only  
- [ ] Approve UX Flow + decision points (§2)  
- [ ] Approve Screen walkthrough (§3)  
- [ ] Approve Question Decision Matrix (§4)  
- [ ] Approve Prefill Presentation Rules (§5) — no technical IDs  
- [ ] Approve Customer Editing Rules (§6)  
- [ ] Approve Failure Handling (§7) — no dead ends  
- [ ] Confirm Scenario Review S1–S6 + simulation PASS (§8)  
- [ ] Approve Implementation Plan (§9) — wire UI next; no CRM now  

## Recommendation

**GREEN for Smart Claim Start design + mock planner.**  
**YELLOW for live Mini Program chip/confirm wiring** (next loop).  
**RED for CRM / identity / Must Have expansion now.**

## Scorecard (this loop)

| Dimension | Result | Evidence |
|-----------|--------|----------|
| Reliability | PASS | Complete plan every S1–S6 + ambiguous; no dead ends |
| Simplicity | PASS | Matched headline = 今天发生了什么？ |
| Smoothness | PASS | Confirms only when Prefill says needs_confirm |
| Business Value | PASS | S3: 18 → 4 inputs; S1: 1 tap Continue |
| Scope Control | PASS | No CRM/UI rewrite/DB/identity |

---

## Phase 5 — Risk Review (mitigations)

| Risk | Mitigation in Cap 03 |
|------|----------------------|
| Customer confusion | One headline, one CTA, chips above fold |
| Wrong vehicle | S2 confirm required; candidates from Cap 01 |
| Wrong policy | S4 confirm; stale chrome |
| Privacy | No OpenID/person_link/full phone/VIN in chips |
| Incorrect prefill | Edit on request; case SoR after submit |
| Multiple drivers | Default named insured; edit later (future idea) |
| Language | Customer copy ZH; broker may use EN later |
| Accessibility | Large CTA, no color-only confirm state (wire loop) |
| Mobile UX | Step confirms before long textarea; photos skippable |

---

## Phase 6 — Future Compatibility

| Concern | Cap 03 guarantee |
|---------|------------------|
| CRM dependency | **None** — `adapter_boundary = consumes_LookupResult_and_PrefillResult_only` |
| DB redesign | **None** |
| Identity redesign | **None** — still P29B `person_link_key` |
| EZLynx / Epic / custom CRM | Swap Cap 01 adapter only; Cap 02/03 unchanged if contracts hold |
| Richer AMS fields | Cap 02 can promote UNKNOWN→AUTO; Cap 03 auto-shows more chips |
| Lower confidence | Cap 01 confidence → fewer AUTO in Cap 02 → Cap 03 degrades presentation |

---

## Code map

| Path | Role |
|------|------|
| `services/fiqa_api/inbox_triage/smart_claim_start/contract.py` | `SmartClaimStartPlan` |
| `services/fiqa_api/inbox_triage/smart_claim_start/engine.py` | Planner / Smart Question Engine |
| `tests/test_p4_capability_03_smart_claim_start.py` | Tests |
| `scripts/simulate_p4_cap03_smart_claim_start.py` | S1–S6 (+ ambiguous) simulation |
| `docs/product/p4_capability_03_smart_claim_start.md` | This Founder package |

## Future ideas (record only)

- Live Mini Program render of chips + confirm gates from plan  
- “不是我开的” driver switcher  
- Location suggest from device (permissioned)  
- Voice story remains primary input (already in Start Claim)  
- Damage photo hints after injury=yes (still optional)  
- Household disambiguation UI when Cap 01 returns AMBIGUOUS with candidates  

---

## Production Loop worksheet

- **Loop:** 1  
- **One objective:** LookupResult + PrefillResult → customer-ready SmartClaimStartPlan (design + mock)  
- **Explicitly out of scope:** CRM, identity, DB, live Mini Program rewrite  
- **Minimum change:** `smart_claim_start` package + sim + tests + Founder doc  
- **Focused tests:** `tests/test_p4_capability_03_smart_claim_start.py`  
- **Commit authorized:** NO (unless Founder asks)  
- **QA deploy authorized:** NO  
- **Founder/manual QA evidence:** simulation + this package (pending Founder checkboxes)  
