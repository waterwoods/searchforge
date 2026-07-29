# P5 Master Execution Plan

**Status:** Founder execution roadmap — **not implementation**  
**Date:** 2026-07-25  
**Horizon:** Remaining P5 → Pilot Ready (several months of disciplined loops)  
**Audience:** Founder · Product · Engineers · Insurance Ops  

**Inputs (challenged, not worshipped):**  
`docs/FOUNDER_PRODUCT_CODEX_V1.md` ·  
`docs/product/p5_capability_constitution_v1.md` ·  
`docs/product/p5_capability_review.md` ·  
`docs/product/p5_sprint1_c01_reference_implementation.md` ·  
`docs/product/p4_capability_01_customer_lookup.md` ·  
`docs/product/p4_capability_02_claim_prefill.md` ·  
`docs/product/p4_capability_03_smart_claim_start.md` ·  
`docs/product/decision_log.md` ·  
`docs/CURRENT_PRODUCT_SHAPE.md` ·  
`docs/product/p20_product_north_star.md`

**Architecture already proven (Gate 1):**  
Workflow → Capability C01 → Mock Adapter → `LookupResult` (flag OFF in pilot)

---

> **One sentence:** Finish the customer Trust Start path (C02→C03) under the C01 template, harden the already-shipping spine for Chen’s office, clean Broker Brief/Timeline only where it saves broker time — then pilot. Do not rebuild production capabilities as theater sprints. Do not touch AMS until a real week of use demands it.

中文意图：先让客户觉得“比打电话省事”，再让陈总觉得“回不去旧方式”，最后才接真 CRM。

---

# 0. Executive Verdict

| Question | Answer |
|----------|--------|
| Would the Founder execute this plan? | **Yes — after the rewrites below.** |
| Biggest rewrite vs prior catalog reading | Treat C04–C08, C10, C13 as **already Pilot Spine**, not equal “build next” sprints. |
| First customer “easier than calling” | End of **Sprint 3** (C03 + presentation GO), not C02 alone. |
| First broker time saved (new vs today) | End of **Sprint 5** (Brief + Lookup overlay). Spine already saves time today. |
| Genuinely pilot-ready | End of **Sprint 7** / **Gate 4**. |
| Live AMS / CRM | **After** Gate 4 evidence — never as the next coding dopamine hit. |

### Guiding compression

**Type Less · Think Less · Trust More**

| Layer | Owns |
|-------|------|
| Workflow | Journey, gates, surface routing |
| Capability | One business ability + complete degrade |
| Adapter | Vendor / mock datasource |

Customers should feel they are talking to **陈总’s office**, not software.

---

# 1. Current State (truthful)

### Done

| Asset | Status |
|-------|--------|
| Founder Product Codex | Why / methodology locked |
| Workflow V2 entry for C01 | Proven in code |
| Capability Review + Constitution | Owns / Never Owns locked |
| C01 Reference Implementation | Template for all future Caps |
| C01 Founder Challenge | Presentation P0s recorded (chips, blank escape) |
| Spine production | C04 Identity, C05 Resume, C06 Evidence, C07 Request More, C08 Waiting, C10 Close, C13 Default Plan |

### Not done (despite catalog maturity language)

| Asset | Reality |
|-------|---------|
| C02 Prefill | Contract + mock harness; not Workflow V2 consumer; not customer-done |
| C03 Smart Claim Start | Mock planner; **presentation polish + Mini Program wire** incomplete |
| Customer-facing Lookup/Prefill/Start | Flags OFF; Founder Preview GO not earned |
| C09 Timeline | Production events exist; **clean facade** not done |
| C11 Broker Brief | Workbench projection exists; **clean facade + Lookup overlay** not done |
| C12 Notification | Future seat only — correctly deferred |
| Live AMS adapter | Explicitly deferred |

### Founder Preview findings that change the roadmap (from C01)

1. Unambiguous HIGH match must feel like **chips → story**, not a confirm quiz → **C03 owns this** (P0 before flag ON).  
2. Ambiguous path needs secondary **空白报案** → **C03/UI owns this** (Workflow already allows).  
3. Do **not** merge C01+C02 into a God Capability.  
4. Keep Lookup flag OFF until customer-facing GO.  
5. Further typing removal is **C02**, not C01 overload.

---

# 2. Challenges to Prior Decisions (explicit)

| Prior assumption | Challenge | Resolution in this plan |
|------------------|-----------|-------------------------|
| Implement C01…C13 as equal capability sprints | Most of C04–C13 already ship; re-implementing wastes months | **Spine Stabilize** (docs + thin facade when touched), not rebuild |
| C02 is a standalone customer release | Prefill without Start presentation = invisible engineering | Ship C02 as capability package; **customer milestone is C02+C03** |
| AMS behind C01 is P1 soon | Capability Review correctly says adapter after evidence; Codex says pilot before platform | Move AMS to **post–Gate 4** |
| Formalize every capability facade before pilot | Facade purity ≠ Chen cannot go back | Only facade-clean **C09 + C11** before pilot; leave others until touch |
| Notification helps pilot completion | Journey SoR is in-app Action/Waiting | **Delete C12 from P5 critical path** |
| “Pilot polish” can wait until after all Caps | Smoothness is the product | Insert **Trust Harden** sprint before broker facade work |

No Constitution Owns/Never Owns is overturned. Sequencing and “what is a sprint” are corrected.

---

# 3. Master Execution Roadmap

```text
Gate 1  Reference Architecture          ✓ DONE (C01 template)
            │
            ▼
Sprint 2    C02 Prefill (capability + Workflow consumer)
            │
            ▼
Sprint 3    C03 Smart Claim Start + Mini Program presentation
            │   (includes C01 Preview P0s: chips, blank escape)
            ▼
Gate 2  Customer Trust                  ← flag ON in QA after Founder Preview GO
            │
            ▼
Sprint 4    Trust Harden (copy, degrade paths, Golden QA, Build Gate)
            │
            ▼
Sprint 5    C11 Broker Brief facade + Lookup overlay
            │
            ▼
Sprint 6    C09 Timeline facade (Brief/support hygiene)
            │
            ▼
Sprint 7    Pilot Ready pack (spine stabilize, ops, Chen week prep)
            │
            ▼
Gate 3  Broker Efficiency               ← Brief usable in ≤10s with known customer
Gate 4  Pilot Ready                     ← Chen office real week
            │
            ▼
Sprint 8+   AMS/CRM adapter behind C01 only (evidence-driven)
            │
            ▼
Gate 5  Production Ready                ← paid / “cannot go back”
            │
            ▼
Later       C12 Notification · Knowledge Assist · multi-broker
```

### Recommended order of implementation (short list)

1. C02 Prefill (serial)  
2. C03 + presentation wire (serial; customer GO)  
3. Trust Harden (serial)  
4. C11 Brief facade (serial preferred; can overlap docs with C09)  
5. C09 Timeline facade  
6. Pilot Ready pack  
7. **Stop.** Pilot.  
8. AMS adapter (only if pilot friction names directory truth)  

---

# 4. Capability Plans (remaining → Pilot Ready)

For each remaining Capability: Mission · Business value · Dependencies · Risks · Why now · Why NOT now · Definition of Done · Founder Preview checklist · GO / NO GO.

---

## C02 — Customer Prefill

### Mission

Classify every Start Claim field as AUTO / customer confirm / broker-owned / unknown from `LookupResult` only — so Workflow never re-encodes field taxonomy and customers are never re-asked known facts.

### Business value

**Type Less.** Matched customers stop typing name/vehicle/policy. Trust rises before the accident story. Without C02, C03 cannot honestly hide fields.

### Dependencies

| Depends on | Status |
|------------|--------|
| C01 `LookupResult` contract | Done |
| Business Contract field list | Done |
| C01 package layout (contract/facade/adapter) | Done — copy it |

Does **not** depend on: Mini Program redesign, AMS, Timeline, Notification.

### Risks

| Risk | Severity |
|------|----------|
| Inventing values for UNKNOWN (email/VIN) | High — trust killer |
| Expanding Must Haves “while classifying” | High — journey regression |
| Workflow re-implements taxonomy | Medium — architecture drift |
| Shipping C02 with no C03 consumer | Medium — invisible value |

### Why now?

C01 template is proven. Prefill is the only legal place to remove typing. Blocks Customer Trust gate.

### Why NOT now?

Do not start if Founder has not acknowledged C01 checkbox (READ ONLY + template). Do not couple AMS. Do not wire customer flag ON from C02 alone.

### Definition of Done

- [ ] `contract` / `facade` / mock path mirrors C01 layout  
- [ ] Workflow V2 calls Prefill; does not import adapters  
- [ ] Complete `PrefillResult` for S1–S6 matrix (zero AUTO on weak/ambiguous)  
- [ ] AST boundary tests + Founder-readable simulate script  
- [ ] No Mini Program visual redesign claimed as Cap Done  
- [ ] Founder acknowledgment to start C03 (separate authorize)

### Founder Preview checklist

- [ ] Matched path: name/vehicle appear as known — not retyped  
- [ ] Multi-vehicle: vehicle is ASK (choose), not silent AUTO  
- [ ] Stale policy: policy/carrier confirm, not silent AUTO  
- [ ] Not found / unavailable: zero dangerous AUTO  
- [ ] No enum names (`AUTO_PREFILL`) on any customer surface  
- [ ] Engineer can explain “suggestion, case is SoR” in one sentence

### GO / NO GO

| GO | NO GO |
|----|-------|
| Classification matches P4 table; degrade complete; Workflow thin | Any CRM write; Must Have expansion; Workflow parses Lookup internals; flag ON for customers |

---

## C03 — Smart Claim Start

### Mission

Plan how Start Claim should feel — modes, chips, confirm gates, question visibility, CTAs — so effort stays on “今天发生了什么？” and known context feels trusted. Does not become the case.

### Business value

**Think Less · Trust More.** This is the first sprint where a stressed stranger can say the product feels like the office helping, not a form punishing them.

### Dependencies

| Depends on | Status |
|------------|--------|
| C01 LookupResult | Done |
| C02 PrefillResult | Sprint 2 |
| Identity + Resume (One Active Case) | Production |
| Mini Program Start Claim render | Must ship in this sprint for User Done |

### Risks

| Risk | Severity |
|------|----------|
| Extra full-screen confirm on unambiguous match | High — UX regression (C01 finding) |
| Ambiguous path traps without 空白报案 | High — customer confusion |
| Plan invents matching rules | High — architecture drift |
| Flag ON before Preview GO | High — pilot instability |
| Expanding photos/VIN as Start blockers | High — Constitution break |

### Why now?

Immediately after C02. Customer Trust does not exist until presentation ships. C01 P0 presentation fixes live here.

### Why NOT now?

Do not start before C02 contract is stable. Do not build AMS chooser theater. Do not redesign Service Home / Waiting in the same loop.

### Definition of Done

- [ ] `plan_start(Lookup, Prefill) → SmartClaimStartPlan` complete for all degrade modes  
- [ ] Workflow/Mini Program **renders plan**; no AMS imports  
- [ ] HIGH + single vehicle + fresh policy → chip strip → story (no quiz page)  
- [ ] Ambiguous → primary 联系顾问 + secondary 空白报案  
- [ ] Active case → Continue only (never second create)  
- [ ] Lookup down / not found → Pilot blank form  
- [ ] Form Gate + Build Gate PASS  
- [ ] Founder Reality Walk on physical Preview (S2, S3, S5, S6 minimum)

### Founder Preview checklist

- [ ] Cold open → shell before network (Nav Gate)  
- [ ] “They know me” before story (matched)  
- [ ] Multi-vehicle chooser once, then story  
- [ ] Stale copy: can continue reporting — not “不能报案”  
- [ ] Ambiguous: never trapped  
- [ ] Blank degrade: same Pilot Must Haves, no error wall  
- [ ] Submit → Waiting with named human (陈总)  
- [ ] Home from success still usable entrance  

### GO / NO GO

| GO | NO GO |
|----|-------|
| Founder says: almost no time proving who I am; story is the work | Any dead-end; quiz on unambiguous match; flag ON in pilot without Preview GO; Must Have expansion |

**Customer-facing flags ON in QA only after GO.** Production/pilot remains OFF until Gate 4 decision.

---

## C04 — Identity

### Mission

Mint opaque durable person link for continuity — not a customer profile.

### Business value

One Active Case survives device/storage clear. Without it, Continuity is theater.

### Dependencies

WeChat login proof. Not AMS. Not Lookup.

### Risks

Building Account/Profile/History; exposing OpenID; anon Production create.

### Why now?

**Not a build sprint.** Production (P29B / D-016). Only touch if regression appears in Trust Harden or Pilot.

### Why NOT now?

No profile center. No phone-mandatory login religion. No “identity v2” rewrite for elegance.

### Definition of Done (stabilize)

- [ ] Production rejects anon-only create  
- [ ] Opaque handle only in client product data  
- [ ] Golden QA resume after storage clear still Continues  

### Founder Preview checklist

- [ ] Continue works after kill app / clear storage (as designed)  
- [ ] No OpenID visible  

### GO / NO GO

| GO | NO GO |
|----|-------|
| Continuity holds on Golden path | Any Account product; Identity performs AMS match |

---

## C05 — Case Resume

### Mission

Remember the one open matter.

### Business value

Continue vs Start without case pickers — stress motion.

### Dependencies

C04 Identity. Case store. Close clears binding (C10).

### Risks

Client-only Active Case myth; multi-case picker; Lookup hint overriding Resume SoR.

### Why now?

**Not a build sprint.** Production. Verify in every customer-facing sprint’s Golden path.

### Why NOT now?

Do not add multi-case. Do not rebuild index “as Capability package” unless binding bugs appear.

### Definition of Done (stabilize)

- [ ] Create resolve→resume never forks  
- [ ] After Close, exactly one new Active Case allowed  

### Founder Preview checklist

- [ ] Active → Continue primary on Service Home  
- [ ] Explicit「开始新的报案」shows policy — no wipe  

### GO / NO GO

| GO | NO GO |
|----|-------|
| One Active Case holds under Preview | Second Active Case possible |

---

## C06 — Evidence Upload

### Mission

Protect every customer evidence — durable bind, idempotent receipt.

### Business value

**Trust.** Lost photos are the #1 “we go back to WeChat chat” reason.

### Dependencies

Case auth, storage adapter. Workflow chooses when.

### Risks

OCR auto-advancing broker done; silent drop; forking case on upload; opaque “网络不稳定”.

### Why now?

**Not a build sprint.** Production path exists. Harden only if Trust Harden / Pilot finds upload failure classes.

### Why NOT now?

No video/PDF/OCR productization before pilot evidence. No upload UX redesign “while wiring Start.”

### Definition of Done (stabilize)

- [ ] Transport / validation / server errors distinguished  
- [ ] Read-after-write on broker projection  
- [ ] Never creates second case  

### Founder Preview checklist

- [ ] Photo success receipt (“已收到”)  
- [ ] Retry path clear  
- [ ] Broker sees same evidence  

### GO / NO GO

| GO | NO GO |
|----|-------|
| Nothing silently lost on Golden path | OCR closes cases; dual upload authorities |

---

## C07 — Request More

### Mission

Broker asks for what’s still missing — exceptionally. One open group, one active customer item.

### Business value

Broker control without making default intake depend on office labor (D-009).

### Dependencies

Case aggregate, Evidence, Constitution projection.

### Risks

Default intake regressing to broker-gated empty Waiting; AI submitting broker commands; Unsupported Choices.

### Why now?

**Not a build sprint.** Production. Validate in Broker Review after Brief work; use in Chen week.

### Why NOT now?

Do not expand item taxonomy for elegance. Do not make Start Claim depend on Request More.

### Definition of Done (stabilize)

- [ ] First-time create still has system_default tasks without Request More  
- [ ] Version conflict → reload, not corruption  

### Founder Preview checklist

- [ ] Broker requests one item → customer Today’s Focus updates  
- [ ] Satisfy → broker sees it (read-after-write)  

### GO / NO GO

| GO | NO GO |
|----|-------|
| Exception path works; default path independent | Empty Waiting on new claim |

---

## C08 — Waiting State

### Mission

Make waiting feel alive — Case Status with named human, not empty Task Home.

### Business value

Post-submit anxiety killer. “陈总正在审核” is the product feeling.

### Dependencies

Constitution projection (owes work? open RM? waiting_broker?).

### Risks

Misclassified Waiting while work owed (One Truth FAIL); push/SLA promises we cannot honor.

### Why now?

**Not a build sprint.** Commit 1 shipped (D-014). Copy polish allowed in Trust Harden. Voluntary append remains deferred unless Pilot demands.

### Why NOT now?

No Notification-driven Waiting. No status dashboard. No soft-freeze productization until evidence.

### Definition of Done (stabilize)

- [ ] Continue → Case Status when no work owed  
- [ ] Task Home only when Action Needed  

### Founder Preview checklist

- [ ] After submit: named waiting meaning  
- [ ] Home still entrance; not stranded on stale result  

### GO / NO GO

| GO | NO GO |
|----|-------|
| Waiting ≠ dead Task Home | Competing stories across Home/Focus/Waiting |

---

## C09 — Case Timeline

### Mission

Remember how we got here — append-only history distinct from current projection.

### Business value

Trust for support + Brief inputs. Prevents “what happened?” archaeology in WeChat.

### Dependencies

Case store; emitters from Workflow/other Caps. Brief consumes Timeline.

### Risks

Using timeline rewrite to “fix” state; customer-facing engineer event names; blocking pilot on perfect facade.

### Why now?

**After Customer Trust + Brief prioritization.** Clean facade before Pilot Ready so support/Brief do not scrape ad hoc forever — but **not before** C02/C03.

### Why NOT now?

Do not rebuild event store. Do not put Timeline on customer Start Claim path. Do not block Gate 2.

### Definition of Done

- [ ] Explicit facade: `append_event` / `list_timeline`  
- [ ] Accepted user work never silently dropped  
- [ ] Brief consumes facade (or transitional adapter with deadline)  
- [ ] Customer still sees human receipts, not raw dumps  

### Founder Preview checklist

- [ ] Broker can see ordered human history for Golden Camry case  
- [ ] Submit/upload/request/close appear as meaningful events  

### GO / NO GO

| GO | NO GO |
|----|-------|
| History trustworthy for one Golden case | Timeline becomes journey SoR; customer dump of enums |

---

## C10 — Case Lifecycle Close

### Mission

End the matter for real — terminal History, clear Active Case binding.

### Business value

Office can finish; customer cannot mutate forever; new claim later is clean.

### Dependencies

Resume clear; Timeline append on close.

### Risks

Soft archive treated as Close; AI auto-close; partial clear without terminal stamp.

### Why now?

**Not a build sprint.** Production (D-017). Verify in Pilot Ready pack.

### Why NOT now?

No History browsing product. No customer self-close. No CRM archive sync as authority.

### Definition of Done (stabilize)

- [ ] Close → customer mutations `case_closed_read_only`  
- [ ] Binding cleared; new Active Case possible  

### Founder Preview checklist

- [ ] Broker Close on QA Workbench  
- [ ] Customer cannot upload after Close  

### GO / NO GO

| GO | NO GO |
|----|-------|
| Terminal truth holds | Archive filter == Close confusion |

---

## C11 — Broker Case Brief

### Mission

Make the case understandable in ~10 seconds.

### Business value

**Broker Efficiency.** This is where Chen’s office feels speed — story, vehicle, evidence, gaps, next action — especially once Lookup overlay shows confidence without customer-visible machinery.

### Dependencies

Case · Evidence · Timeline · Request More · optional Lookup. Workbench render.

### Risks

AI summary executing actions; scraping raw tables forever; showing OpenID; Brief mutating case.

### Why now?

After Customer Trust (Gate 2) and Trust Harden — so Brief improvements overlay real Start Claim quality, not blank forms only.

### Why NOT now?

Do not build Brief AI theater before customers finish Start Claim calmly. Do not block Gate 2.

### Definition of Done

- [ ] `brief(case) → BrokerBrief` facade  
- [ ] Human language first; explicit gaps when partial  
- [ ] Optional Lookup overlay (confidence / known policy) broker-only  
- [ ] Workbench renders Brief contract (stop permanent ad hoc scrape)  
- [ ] Founder 10-second understand test PASS on Golden case  

### Founder Preview checklist

- [ ] Open case → understand story/vehicle/evidence/next action ≤10s  
- [ ] Matched mock customer shows known context without engineer IDs  
- [ ] Gaps honest when data missing  

### GO / NO GO

| GO | NO GO |
|----|-------|
| Chen-speed understand without Cursor | AI auto Request More/Close; customer exposure of brief internals |

---

## C12 — Notification

### Mission

Knock on the door — do not open the case.

### Business value

Optional nudge when office/customer is idle. **Not required for journey correctness.**

### Dependencies

Workflow intent; channel adapters.

### Risks

Notification-driven state machines; push required for correctness; pilot instability from channel setup.

### Why now?

**Not now.** Constitution already reserves the seat.

### Why NOT now?

In-app Action/Waiting is SoR. WeChat template setup burns weeks. No pilot evidence of “nudge would have saved the case.”

### Definition of Done

N/A for P5 critical path. Record-only until Pilot observation log demands it.

### Founder Preview checklist

N/A

### GO / NO GO

| GO (future) | NO GO (P5) |
|-------------|------------|
| Pilot log shows missed follow-ups that push would fix | Any P5 sprint named “build Notification” |

---

## C13 — Default Intake Plan

### Mission

Give every new claim a starting checklist so first-time customers never wait for broker Request More.

### Business value

First-time completion. Empty Waiting after create is a release defect.

### Dependencies

Create claim → Constitution → Task Home.

### Risks

Moving default ownership to broker-only RM; CRM plan as silent SoR.

### Why now?

**Not a build sprint.** Production (D-009). Guard in every release.

### Why NOT now?

No vertical plan explosion. No per-customer CRM plans as SoR.

### Definition of Done (stabilize)

- [ ] Create ⇒ system_default tasks present  
- [ ] Missing default plan = FAIL  

### Founder Preview checklist

- [ ] Brand-new claim shows Today’s Focus without broker action  

### GO / NO GO

| GO | NO GO |
|----|-------|
| First-time path works | Empty Waiting on create |

---

## AMS / CRM Adapter (post-capability, still P5 horizon)

Not a catalog Capability — an **Adapter behind C01**.

### Mission

Replace Mock Directory with real office/AMS truth without rewriting journey.

### Business value

Fewer blank claims for real Chen customers; Brief enrichment. Commercial proof of Capability-before-Integration.

### Dependencies

Stable C01 contract; Pilot evidence that mock mismatch is real pain; credentials/ops.

### Risks

CRM coupling into Workflow; write-back temptation; months of EZLynx politics; pilot freeze.

### Why now?

**Only after Gate 4** (or late Gate 4 if mock mismatch is the #1 Chen friction).

### Why NOT now?

Mock already teaches UX. Integration without pilot truth teaches vendor pain, not product.

### Definition of Done

- [ ] New adapter implements `CustomerDirectoryAdapter`  
- [ ] Same `LookupResult`; C02/C03/Workflow unchanged  
- [ ] Degrade to blank on AMS down  
- [ ] Flag strategy explicit; rollback to mock/blank  

### GO / NO GO

| GO | NO GO |
|----|-------|
| Adapter swap demo on Golden path; journey unchanged | Workflow imports AMS SDK; Prefill write-back |

---

# 5. Sprint-by-Sprint Plan

Assume **1–2 week loops**, one objective each, max three automated loops, stop on PASS, never auto-start next Cap (Codex Production Loop).

| Sprint | Name | One objective | Out of scope | Exit |
|--------|------|---------------|--------------|------|
| **1** | C01 Reference | ✓ Done — three-layer template | C02+ | Gate 1 |
| **2** | C02 Prefill | Workflow consumes PrefillResult from LookupResult | MP redesign, AMS, flag ON | Cap Done + authorize C03 |
| **3** | C03 Trust Start | Customer Start Claim feels trusted; chips/story; blank escape | Waiting redesign, Brief AI, AMS | **Gate 2 candidate** |
| **4** | Trust Harden | Golden QA + copy + degrade + Build/Form/Nav gates green on Preview | New Caps, AMS | Customer Trust hardened |
| **5** | C11 Brief | Broker understands Golden case in ≤10s; Lookup overlay | Notification, CRM write | Gate 3 candidate |
| **6** | C09 Timeline | Timeline facade feeds Brief/support | Customer timeline dump product | Hygiene PASS |
| **7** | Pilot Ready Pack | Ops + spine stabilize + Chen week script + payment posture | Multi-tenant, Stripe, Lab | **Gate 4** |
| **8+** | AMS Adapter | Live directory behind C01 | Journey rewrite | Gate 5 candidate |

### Ideal sequence (compressed calendar view)

```text
Month 1:  Sprint 2 → Sprint 3 → Gate 2 → Sprint 4
Month 2:  Sprint 5 → Sprint 6 → Sprint 7 → Gate 4 (Chen week starts)
Month 3:  Pilot observe / fix-now → decide AMS → Gate 5 / pay / kill reasons
```

Durations flex; **order does not**.

---

# 6. Dependency Graph

```text
                    [Gate 1 ✓]
                         │
                         v
                      C01 Lookup
                         │
                         v
                      C02 Prefill ----------(serial)--------→
                         │
                         v
                      C03 Smart Start + MP render
                         │
                         v
                    [Gate 2 Customer Trust]
                         │
                         v
                    Trust Harden (Workflow gates)
                         │
            +------------+------------+
            │                         │
            v                         v
     C11 Broker Brief          C09 Timeline facade
     (Lookup overlay)          (Brief input hygiene)
            │                         │
            +------------+------------+
                         │
                         v
              Pilot Ready Pack (C04–C08,C10,C13 stabilize)
                         │
                         v
              [Gate 3 Broker] + [Gate 4 Pilot Ready]
                         │
                         v
              AMS Adapter (C01 only)
                         │
                         v
              [Gate 5 Production Ready]

Spine (already live — verify, don't rebuild):
  C04 Identity → C05 Resume ← C10 Close
  C13 Default Plan → Case → C06 Evidence / C07 Request More → C08 Waiting

Forbidden edges:
  Workflow → AMS/CRM/AI/Graph
  C03 → AMS (must go C01)
  C02 → case/CRM writes
  C12 → case mode authority
```

### Serial vs parallel

| Must remain serial | Why |
|--------------------|-----|
| C01 → C02 → C03 | Contract chain; presentation consumes both |
| C03 → Gate 2 → Trust Harden | Do not polish a journey that does not exist |
| Trust Harden → Pilot Ready | Do not invite Chen onto shaky Start Claim |
| Gate 4 → AMS | Capability before Integration |

| Can parallelize | Why |
|-----------------|-----|
| C09 docs + C11 spike after Gate 2 | Shared Brief dependency; still prefer Brief first for value |
| Spine regression scripts anytime | Already production |
| Lab work | Forever off critical path |
| Copy variants for stale/ambiguous | Inside Sprint 3/4 only |

| Never parallel with critical path | Why |
|-----------------------------------|-----|
| Notification | Distraction |
| Account/Profile | Constitution ban |
| Multi-tenant / Stripe | Pilot-before-platform |
| Graph/RAG on Start Claim | Lab contamination |

---

# 7. Review Cadence

| Review type | When | Who | Question |
|-------------|------|-----|----------|
| **Founder Review** | End of every Sprint; mandatory Gate 2/3/4/5 | Andy | User Done? Journey calmer? Scope creep? |
| **Founder Reality Walk** | Before any customer-facing flag ON; before Gate 4 | Andy on real phone + QA hosts | Can I certify without Cursor? |
| **Broker Review** | After Sprint 5 (Brief); mid Pilot week; before Gate 5 | 陈总 / office staff | 10-second understand? Request More usable? Would you keep it? |
| **Pilot Review** | Weekly during Chen week (Gate 4→5) | Andy + Chen | Fix-now list; payment or kill reasons |
| **Customer proxy walk** | Sprint 3 + 4 (Founder as stressed customer) | Andy | Easier than calling? |

**Rule:** Broker Review before Pilot Week is Brief-focused. Do not burn Chen’s time on mock harness demos.

---

# 8. Risk Register (ranked)

| Rank | Risk | Why it matters | Mitigation |
|------|------|----------------|------------|
| 1 | **UX regression on Start Claim** (quiz, traps, error walls) | Destroys “easier than calling” | C01 P0s as C03 exit criteria; Preview before flag ON |
| 2 | **Architecture drift** (Workflow→vendor, God Caps) | Rewrites journey later | Copy C01 layout; AST import bans; Constitution wins |
| 3 | **Capability overlap** (C01 classifies, C03 matches, C08 owns history) | Unclear ownership → thrash | Seam table in Constitution; one question each |
| 4 | **Pilot instability from premature flag ON** | Chen sees broken trust path | Flags OFF until Gate 2; pilot ON only at Gate 4 decision |
| 5 | **CRM coupling / AMS too early** | Months lost; little UX learning | AMS post–Gate 4; adapter-only |
| 6 | **Workflow complexity** (too many modes/screens) | Customer confusion | Prefer chip strip; delete loading theater; blank degrade |
| 7 | **AI overreach** | Trust/compliance break | AI assist only inside adapters; never Close/RM/Active Case |
| 8 | **Premature optimization** (facade every Cap, Notification, OCR) | Delays Pilot | Delete from critical path (see §11) |
| 9 | **Spine neglect while building C02/C03** | Upload/Waiting/Close regressions | Golden QA every customer sprint |
| 10 | **Customer confusion on stale/ambiguous** | Panic → WeChat to 陈总 | Copy + secondary CTA in Sprint 3/4 |

---

# 9. Customer Journey Overlay

```text
Open MP → Identity quiet → Lookup quiet → Prefill quiet → Start feel
    → Accident story → Optional evidence → Submit → Waiting (陈总)
    → (maybe Request More) → Broker Brief → Close
```

| Feeling milestone | Sprint | What must be true |
|-------------------|--------|-------------------|
| “They know me” | Sprint 3 | Chips before story |
| **“This is easier than calling the office.”** | **Sprint 3 → Gate 2** | Matched path ~5 inputs; no identity theater; blank escape |
| “It counted; 陈总 has it” | Already spine; re-prove Sprint 4 | Waiting + read-after-write |
| **Broker first saves time (new)** | **Sprint 5** | Brief ≤10s + known-customer overlay |
| Broker already saves some time | Today | Structured case vs WeChat archaeology — protect, don’t rebuild |
| **Genuinely pilot-ready** | **Sprint 7 / Gate 4** | Flags strategy clear; Golden PASS; ops; Chen week script |
| “We cannot go back” | Gate 5 | Real week logged; fix-now drained; payment or explicit keep |

---

# 10. Founder Gates

## Gate 1 — Reference Architecture ✓

**Must be true:** Workflow → Capability → Adapter proven; Lookup READ ONLY; degrade never blocks accident report; template documented.

**Evidence:** `p5_sprint1_c01_reference_implementation.md` + tests/sim PASS.

## Gate 2 — Customer Trust

**Must be true:**

- C02 + C03 User Done on Preview  
- Unambiguous = chips→story  
- Ambiguous = contact + blank escape  
- Not found/unavailable = blank Pilot form  
- Form / Nav / Build / Golden customer path PASS  
- Founder says the north-star line without coaching  

**Flag policy:** QA may ON; pilot/production still OFF until Gate 4 decision.

## Gate 3 — Broker Efficiency

**Must be true:**

- Brief facade: ≤10s understand on Golden case  
- Lookup overlay broker-only (no OpenID)  
- Request More + Close still work  
- Broker Review: “faster than WeChat scroll”  

## Gate 4 — Pilot Ready

**Must be true:**

- Gates 2–3 held on latest revision  
- Spine stabilize checklist PASS (C04–C08, C10, C13)  
- `CURRENT_PRODUCT_SHAPE` paid-pilot posture validated  
- Trial launch / founder pre-trial scripts PASS  
- One Camry Golden Production QA GO  
- Chen week observation log template ready  
- Rollback: flags OFF → blank path still works  
- Explicit **out of scope** for pilot: AMS, Notification, Account, multi-tenant, Lab  

## Gate 5 — Production Ready

**Must be true:**

- Real Chen week evidence (not demo day)  
- Fix-now P0s closed or accepted  
- Payment or written “keep / kill” reasons  
- Support posture (who answers when it breaks)  
- AMS only if evidence-driven and adapter-clean  
- Still: no auto-send; human gate  

---

# 11. Pilot Readiness Plan

### Phase A — Product shape (Sprints 2–4)

1. Finish Trust Start (C02→C03).  
2. Harden copy and degrade.  
3. Keep Lab off paid URLs.  

### Phase B — Office shape (Sprints 5–7)

1. Brief the broker can trust.  
2. Timeline hygiene for support.  
3. Ops: deploy, keys, QA Workbench host alignment (D-015), rollback drills.  

### Phase C — Chen week (Gate 4→5)

| Day | Focus |
|-----|-------|
| 0 | Founder Reality Walk GO; flags decision documented |
| 1–2 | Shadow real intake; log friction |
| 3–5 | Fix-now only (P0/P1); no new Caps |
| End | Pilot Review: keep / pay / kill reasons |

### Explicit pilot non-goals

- Live AMS  
- Notification  
- OCR auto  
- Stripe  
- Second broker  
- Graph/RAG dependency  

---

# 12. Long-Term Thinking (beyond P5)

### Anticipate today (lightweight only)

| Item | Anticipate how | Do not build now |
|------|----------------|------------------|
| AMS adapter swap | Keep C01 protocol pure; no Workflow vendor names | EZLynx project |
| AI draft in Brief | Brief facade accepts assist adapter later | Auto actions |
| Second channel | C04 opaque-handle contract stays | Account platform |
| Knowledge Assist | Lab until weekly office use | Wire into Start Claim |
| Notification | Seat reserved in Constitution | Channel stack |

### Do not anticipate with architecture

- Temporal/Camunda  
- Multi-case customer portal  
- Prefill CRM write-back  
- Carrier auto-submit  
- Multi-vertical kernel abstraction  

**Why not:** Speculative architecture is the enemy of Chen’s “cannot go back.” Contracts already buy optionality.

---

# 13. Challenge the Roadmap

### Could we remove an entire Sprint?

**Yes — remove any “formalize C04/C05/C06/C07/C08/C10/C13 as greenfield Capability packages” sprint.**  
Replace with Pilot Ready Pack verify-only. That saves ~4–6 weeks.

**Maybe merge Sprint 5+6** into one “Broker Understand” sprint if staffing is one engineer — Brief first, Timeline only if Brief scrape is painful.

### Could two capabilities merge?

| Merge idea | Verdict |
|------------|---------|
| C01+C02 God Cap | **No** — Founder Challenge already rejected |
| C02+C03 single Cap | **No** — different questions; **Yes** as one customer milestone |
| C08+C09 | **No** — now vs history |
| C09+C11 | **No** as Caps; **Yes** as one broker sprint optionally |

### Should one capability split?

**C03 presentation vs C03 planner:** Keep one Capability; allow two commits inside Sprint 3 (plan then wire). Do not invent C03a/C03b catalog IDs.

### Are we building something too early?

| Too early | Action |
|-----------|--------|
| AMS | Defer post–Gate 4 |
| C12 Notification | Delete from P5 path |
| OCR/video | Record only |
| Voluntary Waiting append | Defer unless Pilot demands |
| Full facade for every spine Cap | Delete as sprint type |

### What would GEICO / Lemonade / world-class SaaS do differently?

| They would | We adopt | We reject |
|------------|----------|-----------|
| Logged-in path feels different from guest | Matched chips vs blank degrade | Full consumer account |
| Confirm only ambiguity | C03 chip law | 18-field FNOL |
| Stage evidence after core loss facts | Default plan + RM | Photos as Start blockers |
| Instrument funnel drop-off | Pilot observation log | Vanity MAU dashboards |
| Ship thin vertical slice to real users fast | Gate 4 Chen week | Platform-complete AMS first |
| Kill features that don’t move completion | Delete Notification/AMS-early | Catalog completionism |

---

# 14. Deliverables Summary

### 1. Master Execution Roadmap

Gate 1 ✓ → C02 → C03 → Gate 2 → Trust Harden → C11 → C09 → Pilot Pack → Gate 3/4 → AMS → Gate 5.

### 2. Sprint-by-Sprint Plan

See §5. One objective per sprint. Stop rules from Codex Production Loop.

### 3. Dependency Graph

See §6. Serial Trust chain; parallel only Brief/Timeline hygiene; spine verify-only.

### 4. Risk Register

See §8. Top risks: UX regression, architecture drift, premature flags/AMS.

### 5. Founder Gates

See §10. Reference → Customer Trust → Broker Efficiency → Pilot Ready → Production Ready.

### 6. Pilot Readiness Plan

See §11. Product shape → Office shape → Chen week → pay/keep/kill.

### 7. Recommended order

C02 → C03 → Harden → C11 → C09 → Pilot Pack → (stop) → AMS.

### 8. Delete from current roadmap thinking

| Delete | Why |
|--------|-----|
| Greenfield rebuild sprints for C04–C08, C10, C13 | Already production |
| C12 Notification on P5 critical path | Optional; journey works without |
| AMS before Chen week | Integration theater |
| Customer Account / multi-case picker | Constitution ban |
| Lab Graph/RAG on claim spine | Contaminates pilot |
| “Implement all P1 from momentum” | Caps must be authorized separately |
| Expanding Start Claim Must Haves during Prefill | Scope bomb |

### 9. Add to roadmap

| Add | Why |
|-----|-----|
| **Trust Harden sprint** after C03 | Smoothness before broker chrome |
| **C01 Preview P0s as C03 exit criteria** | Chips + blank escape |
| **Flag policy by Gate** | Prevents pilot instability |
| **Broker Review after Brief, not after every Cap** | Respect Chen’s time |
| **Pilot observation → AMS decision gate** | Evidence over ambition |
| **Rollback drill** (flags OFF → blank) | Operational trust |

### 10. Final recommendation

**Execute this plan.**

If I were the Founder, I would:

1. Acknowledge C01 template + Preview P0s.  
2. Authorize **only** Sprint 2 (C02) next — not C02+C03+AMS.  
3. Refuse any sprint that rebuilds shipping spine “for cleanliness.”  
4. Treat **Gate 2** as the emotional product release; Gate 4 as the commercial one.  
5. Keep saying no to Notification, Account, and CRM write-back until a real week of Chen evidence argues otherwise.

**Success looks like:**

> Chen’s office says: we cannot go back to the old way.  
> Customers feel: this is easier than calling.  
> Engineers feel: adapters can change; the journey does not.

---

# 15. Authorization Checklist (Founder)

- [ ] Acknowledge this Master Execution Plan as P5 sequencing SSOT  
- [ ] Acknowledge Gate 1 complete; Gate 2 is next emotional milestone  
- [ ] Acknowledge spine Caps are verify/stabilize, not rebuild  
- [ ] Acknowledge C12 / AMS deleted from near-term critical path  
- [ ] Authorize Sprint 2 (C02) as the **only** next implementation loop  
- [ ] Refuse momentum starts of C03 until C02 Cap Done + separate authorize  

---

## Document control

| Version | Date | Change |
|---------|------|--------|
| v1 | 2026-07-25 | Initial P5 Master Execution Plan from Codex, Constitution, Capability Review, C01 reference, Decision Log, Preview findings |

**Conflict rule:** If a future sprint doc schedules AMS, Notification, or spine rebuild before Gate 2/4 per this plan, **this plan wins** until Founder supersedes with v1.x + Decision Log entry.
