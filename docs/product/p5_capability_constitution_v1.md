# SearchForge Workflow Platform — Capability Constitution v1.0

**Status:** Governing product constitution — **not implementation**  
**Date:** 2026-07-25  
**Horizon:** Intended useful for ≥5 years  
**Audience:** Founder · Product · Engineers · AI assistants  

**Does not replace:**  
`docs/FOUNDER_PRODUCT_CODEX_V1.md` (why) ·  
`docs/product/p20_product_north_star.md` (journey law) ·  
`docs/product/decision_log.md` (why we chose) ·  
`docs/product/p5_capability_review.md` (what exists / contracts inventory)

**Answers a different question:**

> What is each Capability allowed to own?

---

## Preamble

The Workflow Platform optimizes the **customer journey**, not feature count.

Capabilities exist so Workflow can stay calm while systems behind them change: CRM, AMS, AI, storage, channels.

```text
Workflow Platform     owns journeys, policy, surface routing, human gates
        ↓
Capability Layer      owns one business ability each, behind a stable contract
        ↓
Adapters              own vendor protocols and raw external systems
        ↓
SearchForge Lab       owns experiments that are not journey-critical
```

**Design philosophy (permanent):**

| Rule | Meaning |
|------|---------|
| One responsibility | Each Capability answers exactly one business question |
| One clear boundary | Owns / Never Owns are explicit |
| One contract | Workflow depends on behavior, not internals |
| One owner | Server / Broker / Customer / Workflow — named |
| Capability may evolve | Adapters, media types, enrichment may grow |
| Responsibility must not | The business question does not drift |

---

# Part I — Architecture Laws

These laws outrank convenience, sprint pressure, and vendor preference.

### L-01 — Workflow owns journeys

Workflow decides *when* the customer or broker moves, *which* surface they see, and *which* Capability to call. Capabilities do not redesign the journey.

### L-02 — Capabilities own business abilities

A Capability performs one ability (lookup, bind evidence, close case, …) and returns a complete, consumable result. It does not own Home → Task → Waiting sequencing.

### L-03 — Adapters own external systems

AMS, CRM, carrier, object storage, WeChat push, OCR vendors, AI models live behind Adapters inside a Capability. Workflow never imports them.

### L-04 — Lab stays out of the spine

RAG, Graph, Agent Studio, Retriever, tuner, and `platform_full` demos are SearchForge Lab unless promoted through this Constitution (see Part IV).

### L-05 — Lookup is READ ONLY

Customer Lookup never creates, merges, updates, or deletes Customer, Policy, Vehicle, or CRM records. Lookup is not Source of Truth.

### L-06 — Prefill is suggestion

Prefill classifies and suggests. After customer confirm/submit, the **claim case** is Source of Truth. Prefill never write-backs to CRM.

### L-07 — Customer-confirmed data wins

Silent overwrite of customer-confirmed facts is forbidden. Corrections of completed required slots go through Broker Request More or explicit customer edit paths Workflow allows.

### L-08 — Workflow never talks directly to CRM

No Mini Program page, Workbench screen, or Workflow kernel may call AMS/CRM SDKs or vendor payloads directly.

### L-09 — Workflow never depends on AI for authority

AI may draft, extract, summarize, or classify **inside** a Capability Adapter. AI must not advance authoritative workflow state, Close a case, fork Active Case, submit Request More, or auto-send to carriers.

### L-10 — Workflow survives every adapter replacement

Replacing Mock→AMS, storage vendor, channel login, or AI model must not require rewriting the customer journey if Capability contracts hold.

### L-11 — Capability must degrade gracefully

If a Capability is unavailable, it returns a **complete degraded result** (or a safe no-op with explicit outcome). It must not throw the journey into a dead end or a single opaque “网络不稳定” for every failure class.

### L-12 — One Active Case remains sacred

A customer has at most one Active Case. Create resolves→resumes. Split/merge is Broker/office only. No Capability may create a second Active Case.

### L-13 — Complexity stays inside

Tokens, OpenIDs, person_link keys, match_status, aggregate versions, capability enum names, and vendor refs are not normal customer UI.

### L-14 — Read-after-write or it did not happen

Accepted customer submissions must become visible in the authoritative broker projection for the same case (and request item when applicable).

### L-15 — Broker keeps the human decision boundary

Nothing auto-sends to carriers. Capabilities may prepare; humans decide.

### L-16 — Append-first; split later

Ordinary facts and evidence attach to the current Active Case. Premature “new accident?” taxonomy is not a customer Capability duty.

### L-17 — Default intake must not require Request More

First-time claim tasks come from Default Intake Plan. Request More is exceptional follow-up only.

### L-18 — Waiting is a designed state

When the customer owes no work, they see Case Status / Waiting meaning — not an empty Task Home pretending to be productive.

### L-19 — Capability Done means User Done

A Capability is not done when code merges. It is done when the affected user journey works under Founder/manual evidence.

### L-20 — One Golden acceptance story

Production readiness is judged by the Golden Production QA journey, not by prototype substitutes or lab demos.

### L-21 — Server is final authority

Clients are guests. Constitutional state (Active Case, Close, Waiting vs Action Needed) is server-owned.

### L-22 — Never request what the customer cannot complete

No Unsupported Choices. Capabilities that collect from customers must only ask for completable work.

---

# Part II — Capability Laws (C01–C13)

Catalog IDs follow `docs/product/p5_capability_review.md`.  
**Responsibility text here is constitutional.** Package docs may refine scenarios; they may not invert Owns / Never Owns.

---

## C01 — Customer Lookup

| Field | Law |
|-------|-----|
| **Identity** | C01 Customer Lookup |
| **Purpose** | Answer who this person is in office/policy context, without becoming CRM SoR. |
| **One Sentence Mission** | **C01 answers “Who is this customer?” — read only.** |
| **Owns** | Match/read of identity→customer/policy/vehicle hints; match status; confidence; complete `LookupResult`; adapter boundary to directory/AMS/CRM. |
| **Never Owns** | Case create/update; CRM writes; journey routing; Prefill classification; Start Claim UX; Active Case binding SoR; notifications; evidence; Close. |
| **Inputs** | Durable identity handle (and session). QA scenario keys only in non-prod harnesses. |
| **Outputs** | Always-complete `LookupResult` (match, confidence, summaries, hints, next_action, reasons, source). |
| **Workflow Contract** | Workflow calls Lookup and branches on stable result fields — never on vendor payload shapes. |
| **Failure Principles** | Unavailable / not found → blank-claim-capable result. Ambiguous → no auto-merge. Stale policy / multi-vehicle → explicit confirm signals. Journey continues. |
| **Evolution Rules** | ✓ New directory/AMS adapters; richer fields; better disambiguation signals. ✗ Writes to CRM; creating cases; owning Start Claim screens; exposing OpenID to customers. |

---

## C02 — Customer Prefill (Claim Prefill)

| Field | Law |
|-------|-----|
| **Identity** | C02 Customer Prefill |
| **Purpose** | Classify what is already known vs still needed so customers are not re-asked known facts. |
| **One Sentence Mission** | **C02 decides what we already know — it never invents truth.** |
| **Owns** | Field classification (`AUTO` / customer confirm / broker-owned / unknown); suggested values derived from Lookup; confirm flags. |
| **Never Owns** | Lookup matching; case writes; CRM write-back; Must Have expansion beyond Business Contract; journey screens; notifications. |
| **Inputs** | `LookupResult` (+ Business Contract field list). |
| **Outputs** | Complete `PrefillResult`. |
| **Workflow Contract** | Workflow asks Prefill what to ask; Workflow does not re-encode field taxonomy. |
| **Failure Principles** | Weak/ambiguous lookup → zero AUTO. Unknown fields stay unknown (no invention). Journey can still collect accident facts. |
| **Evolution Rules** | ✓ Promote UNKNOWN→AUTO when adapters provide safe data; add fields with Business Contract change. ✗ Treat Prefill as SoR; write CRM; force VIN/docs as Start Claim blockers without Founder law change. |

---

## C03 — Smart Claim Start

| Field | Law |
|-------|-----|
| **Identity** | C03 Smart Claim Start |
| **Purpose** | Present Start Claim so known context feels trusted and effort stays on today’s accident. |
| **One Sentence Mission** | **C03 plans how Start Claim should feel — it does not become the case.** |
| **Owns** | Start plan: mode, chips, confirm gates, question visibility, CTA intent for Start Claim entry. |
| **Never Owns** | Lookup/Prefill logic; Active Case binding; post-submit Task Home; Request More; CRM; carrier FNOL submit. |
| **Inputs** | `LookupResult` + `PrefillResult`. |
| **Outputs** | `SmartClaimStartPlan` (complete for every degrade mode). |
| **Workflow Contract** | Workflow/Mini Program renders the plan; enforces One Active Case and Form Gate; stamps case on submit as SoR. |
| **Failure Principles** | Plan missing/unavailable → blank accident form (today’s safe path). Active case → Continue mode, never second create. No dead-end modes. |
| **Evolution Rules** | ✓ New confirm screens; better chip language; optional assist hints. ✗ Bypass One Active Case; expand Must Haves illegally; call CRM; auto-submit claims. |

---

## C04 — Identity

| Field | Law |
|-------|-----|
| **Identity** | C04 Identity |
| **Purpose** | Smallest durable person link so continuity survives device/storage change — without a Customer Account product. |
| **One Sentence Mission** | **C04 mints continuity — not a customer profile.** |
| **Owns** | Channel proof → opaque person link; session establishment; never persisting/displaying raw OpenID as product data. |
| **Never Owns** | CRM match; policy list; claim history UI; profile center; Lookup; case facts (name/phone on case remain case-owned). |
| **Inputs** | Channel login proof. |
| **Outputs** | Opaque identity handle usable by Resume and Lookup. |
| **Workflow Contract** | Workflow requires Production durable identity for create; never implements vendor login crypto itself. |
| **Failure Principles** | Login failure → retry / contact broker. No silent anon Production create. |
| **Evolution Rules** | ✓ New channel adapters (same opaque-handle contract). ✗ Building Account/Profile/History products inside Identity; exposing OpenID; performing AMS match here. |

---

## C05 — Case Resume

| Field | Law |
|-------|-----|
| **Identity** | C05 Case Resume |
| **Purpose** | Resolve the single Active Case for an identity. |
| **One Sentence Mission** | **C05 remembers the one open matter.** |
| **Owns** | Active Case index bind/resolve/clear; resume availability signal for Workflow. |
| **Never Owns** | Case content facts; Lookup hints as binding SoR; multi-case picker; Close policy (Close *uses* Resume to clear); notifications. |
| **Inputs** | Identity handle and/or validated resume token. |
| **Outputs** | Active case ref or none. |
| **Workflow Contract** | Continue vs Start Claim uses Resume. Create must resolve→resume, never fork. |
| **Failure Principles** | None → Start Claim. Invalid token → re-enter/contact. After Close, binding cleared so one new Active Case may exist later. |
| **Evolution Rules** | ✓ Stronger token validation; multi-channel bind. ✗ Multi-case customer picker; client-only Active Case myth; second Active Case. |

---

## C06 — Evidence Upload

| Field | Law |
|-------|-----|
| **Identity** | C06 Evidence Upload |
| **Purpose** | Durably accept and bind evidence to the case so nothing is silently lost. |
| **One Sentence Mission** | **C06 protects every customer evidence.** |
| **Owns** | Accept media/docs; durable storage via Adapter; bind to case/slot/item; idempotent receipt; customer-safe progress outcomes. |
| **Never Owns** | Deciding *which* slot is Today’s Focus; Closing cases; Lookup; changing journey topology; auto-advancing broker review solely because OCR “looks done.” |
| **Inputs** | Authorized case context, slot/item intent, payload, idempotency keys. |
| **Outputs** | Evidence receipt + projection-visible binding. |
| **Workflow Contract** | Workflow chooses when to collect; C06 guarantees durability and bind semantics. |
| **Failure Principles** | Distinguish transport / validation / server. Partial upload stays unbound until valid. Journey remains retryable. Never forks a new case. |
| **Evolution Rules** | ✓ Video, PDF, OCR/AI extraction adapters (suggest only). ✗ Using OCR to Close or skip Broker gate; dropping accepted bytes; creating cases from upload. |

---

## C07 — Request More

| Field | Law |
|-------|-----|
| **Identity** | C07 Request More |
| **Purpose** | Broker-owned exceptional follow-up: one ordered open request group, one active customer item. |
| **One Sentence Mission** | **C07 lets the broker ask for what’s still missing — exceptionally.** |
| **Owns** | Request group lifecycle (create/amend/withdraw); active item selection; satisfy/reject rules; version-conflict outcomes. |
| **Never Owns** | Default first-time intake plan; Lookup/Prefill; Closing; notifications delivery; inventing unsupported asks. |
| **Inputs** | Broker command; customer submission for active item. |
| **Outputs** | Projections with one customer next action and one broker next action. |
| **Workflow Contract** | Workflow surfaces Today’s Focus from projection; does not invent a second request system. |
| **Failure Principles** | Conflict → reload current projection. Inactive item → reject. Closed case → reject. Product still usable via reload/contact. |
| **Evolution Rules** | ✓ New item types the customer can complete; better amend rules. ✗ Making default intake depend on Request More; AI submitting broker commands; multi-open-groups chaos without Founder law. |

---

## C08 — Waiting State

| Field | Law |
|-------|-----|
| **Identity** | C08 Waiting State |
| **Purpose** | When customer owes no work, express a living waiting meaning (Case Status), not a dead task page. |
| **One Sentence Mission** | **C08 makes waiting feel alive — not empty.** |
| **Owns** | Determination of Waiting vs Action Needed vs Closed *mode signal* from case projection facts; Case Status meaning (status, after-line intent). |
| **Never Owns** | Full journey map; Notification delivery; Timeline history store; inventing Today’s Focus work; Broker Close. |
| **Inputs** | Case projection facts (owes work? open Request More? waiting_broker? closed?). |
| **Outputs** | Surface mode + customer-safe waiting meaning. |
| **Workflow Contract** | Workflow routes Continue into Task Home or Case Status from this mode signal; keeps Service Home as entrance. |
| **Failure Principles** | If work is owed, must not report Waiting (One Truth). Never strand on blank. Degrade to contact broker + Home, not infinite spinner. |
| **Evolution Rules** | ✓ Voluntary append while waiting; richer status copy. ✗ Push/SLA clocks we cannot honor; replacing Workflow routing; multi-case status dashboards. |

---

## C09 — Case Timeline

| Field | Law |
|-------|-----|
| **Identity** | C09 Case Timeline |
| **Purpose** | Append-only history of what happened — distinct from current-state projection. |
| **One Sentence Mission** | **C09 remembers how we got here.** |
| **Owns** | Append and ordered list of typed case events; retention/redaction rules inside the capability. |
| **Never Owns** | Current Today’s Focus; Waiting mode; Brief composition policy (Brief *consumes* timeline); mutating case status by rewriting history. |
| **Inputs** | Case id + typed event. |
| **Outputs** | Ordered history for broker/support (customer sees human receipts, not raw dumps by default). |
| **Workflow Contract** | Workflow/other capabilities emit meaningful events; Timeline stores/orders; never silently drops accepted user work. |
| **Failure Principles** | Append failure must surface as system failure for that write path — not pretend success. Read paths degrade to partial history with honesty. |
| **Evolution Rules** | ✓ Richer event types; export adapters. ✗ Using timeline rewrite to “fix” state; customer-facing engineer event names; analytics owning journey. |

---

## C10 — Case Lifecycle Close

| Field | Law |
|-------|-----|
| **Identity** | C10 Case Lifecycle Close |
| **Purpose** | Terminal History: stop customer mutation, clear Active Case binding, allow a future new Active Case. |
| **One Sentence Mission** | **C10 ends the matter — for real.** |
| **Owns** | Close command semantics; terminal stamps; mutation rejection (`case_closed_read_only`); coordination with Resume clear. |
| **Never Owns** | Soft-archive queue filters as if they were Close; customer Close control; CRM archive sync as authority; reopen product (unless future Founder law). |
| **Inputs** | Authorized broker Close + case. |
| **Outputs** | History ref / terminal projection. |
| **Workflow Contract** | After Close, customer cannot mutate; Resume unbound; one new Active Case may be created later by identity. |
| **Failure Principles** | Double-close safe/idempotent. Fail closed (do not partially clear binding without terminal stamp). |
| **Evolution Rules** | ✓ Optional CRM archive adapter after Close. ✗ Customer self-close; treating archive filter as Close; AI auto-close. |

---

## C11 — Broker Case Brief

| Field | Law |
|-------|-----|
| **Identity** | C11 Broker Case Brief |
| **Purpose** | Project the broker’s ~10-second understand artifact. |
| **One Sentence Mission** | **C11 makes the case understandable in ten seconds.** |
| **Owns** | Brief projection composition from case, evidence, timeline, open requests, optional Lookup overlay; broker-only enrichment. |
| **Never Owns** | Customer journey; mutating case by summarizing; auto-send; replacing Request More/Close commands. |
| **Inputs** | Case aggregate + related capability outputs. |
| **Outputs** | `BrokerBrief` (human language first). |
| **Workflow Contract** | Workbench renders Brief; does not permanently scrape raw tables as the product contract. |
| **Failure Principles** | Partial brief with explicit gaps beats fake completeness. |
| **Evolution Rules** | ✓ AI summarize adapter; Lookup confidence overlay. ✗ AI executing broker actions; showing OpenID; customer exposure of brief internals. |

---

## C12 — Notification

| Field | Law |
|-------|-----|
| **Identity** | C12 Notification |
| **Purpose** | Deliver nudges without owning next action or case truth. |
| **One Sentence Mission** | **C12 knocks on the door — it does not open the case.** |
| **Owns** | Delivery attempts for Workflow-issued intents; channel adapters; delivery results. |
| **Never Owns** | Whether the customer’s next action changes; case status authority; Lookup; inventing journey steps when push fails. |
| **Inputs** | Notification intent (audience, template key, case ref). |
| **Outputs** | Delivery result (sent / skipped / failed). |
| **Workflow Contract** | Workflow decides *whether/when* to notify; C12 decides *how* to deliver. |
| **Failure Principles** | Delivery failure must not corrupt case state. In-app Action/Waiting remains SoR. |
| **Evolution Rules** | ✓ SMS/email/WeChat templates; digest batching. ✗ Notification-driven state machines; push required for journey correctness. |

*Status:* Future capability — constitutional seat reserved; build only when pilot evidence demands.

---

## C13 — Default Intake Plan

| Field | Law |
|-------|-----|
| **Identity** | C13 Default Intake Plan |
| **Purpose** | Attach system_default tasks on claim create so first-time customers are never stuck waiting for broker Request More. |
| **One Sentence Mission** | **C13 gives every new claim a starting checklist.** |
| **Owns** | Default plan content/provider for new claims; distinction of `system_default` vs later `broker_requested`. |
| **Never Owns** | Exceptional Request More groups; Lookup; Closing; channel identity; Lab knowledge retrieval. |
| **Inputs** | New case create context (vertical/lane as Workflow provides). |
| **Outputs** | Default plan consumed by Constitution → customer Task Home. |
| **Workflow Contract** | Create claim ⇒ default plan present. Request More may add; must not silently erase the need for defaults. |
| **Failure Principles** | Missing default plan is a **release defect**, not a soft degrade to empty Waiting. |
| **Evolution Rules** | ✓ Vertical-specific default plans; small plan edits with Founder law. ✗ Moving default ownership to broker-only Request More; per-customer CRM plan as silent SoR without contract. |

*Note:* C13 is Workflow-adjacent law packaged as a plan provider. It is not an AMS Capability.

---

# Part III — Cross-Capability Review

### One question each (no duplicates)

| ID | Exactly one question |
|----|----------------------|
| C01 | Who is this customer? |
| C02 | What do we already know vs still need? |
| C03 | How should Start Claim be presented? |
| C04 | What durable person link exists? |
| C05 | Which Active Case continues? |
| C06 | How is evidence bound durably? |
| C07 | What exceptional items does the broker still need? |
| C08 | What surface mode when work is / isn’t owed? |
| C09 | What happened, in order? |
| C10 | How does the case become terminal History? |
| C11 | What does the broker need in ~10 seconds? |
| C12 | How do we deliver a nudge? |
| C13 | What must a new claim collect by default? |

### Ownership seam rules (anti-overlap)

| Seam | Winner | Loser must not |
|------|--------|----------------|
| Active Case binding | **C05** | C01 may hint only |
| Known facts classification | **C02** | C01 does not classify Start Claim fields |
| Start Claim presentation | **C03** | C02 does not own screens |
| Default vs exception collection | **C13** vs **C07** | C07 must not be required for first create |
| Now vs history | **C08** vs **C09** | Timeline ≠ Waiting; Waiting ≠ Timeline |
| Broker understand vs history store | **C11** vs **C09** | Brief consumes Timeline; does not replace it |
| Continuity vs CRM who | **C04** vs **C01** | Identity never AMS-matches |
| Terminal vs queue filter | **C10** | Soft archive ≠ Close |
| Nudge vs truth | **C12** | Notification never owns case mode |

### Hidden dependency ban

Forbidden hidden edges:

- Workflow → vendor SDK  
- C03 → AMS (must go C01)  
- C06 OCR → auto Close / auto broker-done  
- C11 AI summary → auto Request More / Close  
- Lab Graph → Mini Program Start Claim  

Allowed edges are only those in the Capability Review dependency map (Identity→Resume; Lookup→Prefill→Start; Evidence/RequestMore/Timeline→Brief; Close→Resume clear; Workflow orchestrates calls).

---

# Part IV — Capability Evolution Policy

### When to create a new Capability

Create a new Capability **only if all** are true:

1. It answers a **new** business question not covered by C01–C13.  
2. Workflow would otherwise grow vendor or domain logic.  
3. It can expose a **stable contract** with graceful degrade.  
4. It can evolve via Adapters without journey rewrite.  
5. Founder acknowledges a catalog ID and Owns / Never Owns.

Examples that **deserve** a new Capability later: Knowledge Assist (broker-only), Payment/Billing, Carrier Submit (still human-gated).

Examples that **do not**: “better button color,” “new Graph demo,” “one more Workbench column” without a new business question.

### When to extend an existing Capability

Extend when the change:

- Still answers the **same** one-sentence mission  
- Fits Owns / does not invade Never Owns  
- Preserves Workflow Contract behavior (additive fields OK; semantic inversion not OK)  
- Keeps degrade complete  

Examples: C06 + video; C01 + new AMS adapter; C11 + AI summarize adapter.

### How to prevent God Capabilities

A Capability is becoming a God Capability if it:

- Answers more than one business question  
- Owns journey routing **and** a domain verb  
- Writes CRM **and** presents customer UX **and** closes cases  
- Requires Lab Graph to function  

**Remedy:** Split along one-question lines; push vendors into Adapters; return journey logic to Workflow.

### How to prevent business logic leakage into Workflow

Workflow may:

- Call Capability contracts  
- Enforce product laws (One Active Case, Form Gate, Waiting vs Action)  
- Choose *when* to call  

Workflow may not:

- Parse AMS payloads  
- Re-implement Prefill taxonomy  
- Embed OCR thresholds that advance state  
- Special-case vendor errors as journey truth without Capability mapping  

**Test:** If Workflow code names a vendor, it is leaking — move behind a Capability Adapter.

### Lab → Product promotion

Lab work becomes Product only by:

1. Naming the Capability (new or existing)  
2. Writing Owns / Never Owns under this Constitution  
3. Providing degrade behavior  
4. Passing North Star gates + User Done evidence  
5. Remaining off the paid-pilot critical path until Founder GO  

---

# Part V — Capability Dependency Principles

1. **Downward only for vendors:** Capability → Adapter → vendor.  
2. **Sideways only by contract:** Capability A may consume Capability B’s **output contract**, never B’s adapter.  
3. **Workflow is the orchestrator:** Fan-in/fan-out of calls lives in Workflow, not in a mega-Capability.  
4. **Optional capabilities stay optional:** C01–C03 and C12 must degrade; spine (C04–C07, C10, C13) failure is a product incident, not a silent skip of One Active Case.  
5. **Hints are not SoR:** Lookup active_case hint never overrides C05. Prefill never overrides customer-confirmed case facts.  
6. **No cyclic ownership:** If A owns X, B cannot also own X. Seams in Part III resolve ties.  
7. **Replaceability proof:** For every Adapter, name the mock/fallback that keeps Workflow moving.

---

# Part VI — Founder Guidelines (one page)

### If you join SearchForge tomorrow — think this before touching a Capability

**1. Name the layer**

| If you are changing… | Put it in… |
|----------------------|------------|
| Home → Start → Task → Waiting → Close sequencing | **Workflow** |
| One business ability with a stable result | **Capability** |
| EZLynx / S3 / WeChat / model calls | **Adapter** (inside a Capability) |
| RAG / Graph / Agent demos | **SearchForge Lab** |

**2. Ask four questions**

1. What **one business question** does this answer?  
2. What does it **Own** / **Never Own**?  
3. If the vendor is down, how does Workflow **degrade**?  
4. Would a stressed customer or Chen still finish without Cursor?

If you cannot answer, you are not ready to create or modify a Capability.

**3. Prefer extend over invent**

- Same mission → extend existing Capability  
- New mission → new Capability + Founder catalog entry  
- “While we’re here” extras → record as future ideas; do not ship into Owns

**4. Never do these**

- Workflow calling CRM/AI/Graph directly  
- Lookup writing CRM  
- Prefill as Source of Truth  
- Second Active Case  
- AI closing cases or sending to carriers  
- Lab dependency on the Golden customer path  

**5. Definition of done**

Code + tests are necessary. **User Done** (Founder/manual evidence on the real journey) is constitutional.

**6. When unsure**

Read, in order: North Star → this Constitution → Decision Log → Capability Review → package doc for that Cap.  
Do not re-argue settled Owns / Never Owns without a new Decision Log entry.

---

# Part VII — Relationship to other documents

| Document | Role vs this Constitution |
|----------|---------------------------|
| Founder Product Codex | Why the product exists; methodology |
| P20 North Star | Journey optimization + release gates |
| Decision Log | Why a law was chosen |
| P5 Capability Review | Inventory, contracts detail, priorities |
| P20 Interaction / Smooth Task Constitutions | Frontend/state interaction law |
| P4 Cap 01–03 packages | Scenario harnesses under C01–C03 laws |
| CURRENT_PRODUCT_SHAPE | Runtime/deploy truth |

**Conflict rule:** If a sprint doc conflicts with this Constitution on Owns / Never Owns / Architecture Laws, **this Constitution wins** until Founder supersedes with v1.x and a Decision Log entry.

---

# Document control

| Version | Date | Change |
|---------|------|--------|
| v1.0 | 2026-07-25 | Initial Capability Constitution from Codex, Decision Log, North Star, P5 Capability Review |

**Amendment rule:**  
- Clarify wording without changing Owns → patch (v1.x) with Founder note.  
- Change Owns / Never Owns / Architecture Laws → new minor version + Decision Log entry + Founder acknowledgment.  
- Do not delete history; supersede explicitly.
