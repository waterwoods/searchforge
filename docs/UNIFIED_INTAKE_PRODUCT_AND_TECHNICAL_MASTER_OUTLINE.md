# Unified Intake — Product & Technical Master Outline

## 0. How to Use This Document

This document is the macro blueprint for Unified Intake direction-lock in the current phase. It defines:

- what product we are actually building
- what our current strongest wedge is
- how the product should evolve
- how the technical architecture should evolve
- what we are and are not trying to become

This is **not** an implementation spec.

This is the top-level source of truth for:

- product direction
- business framing
- architecture direction
- state-driven flow migration
- client-pack replication strategy
- technical evolution path

Future sprint docs, specs, implementation plans, and agent prompts should align with this document.

---

## 1. Document Purpose

This document defines the **product essence, stage goals, core skeleton, technical baseline, migration direction, and commercial boundary** of the project.

Its purpose is to ensure:

- we always know what we are building
- we do not accidentally turn this product into a chatbot, CRM, or full insurance platform
- future sprints continue to use **document-driven development**
- agents and engineers keep iterating around the same core direction

---

## 2. One-Sentence Product Definition

We are not building:

- a fully autonomous insurance AI
- a full CRM
- a full agency OS
- a carrier-side execution platform

We are building:

**An Add-Car-first intake and handoff assistant for broker teams that uses state-driven flow to turn messy, fragmented customer input into a formal service record the office can receive, continue, and process.**

The first commercial / monetizable wedge and highest-priority flagship path today is:

**Add-Car / add vehicle quote intake**

---

## 2A. Identity, Session, and Service Record (Stage 1 Model)

This section names the **lightweight industrial backbone** for Add-Car: who is speaking, what conversation this is, and what durable object the office receives. It is **conceptual and product-operational**, not a full account platform or CRM.

### What we are not building in Stage 1

Stage 1 does **not** require—and should not pretend to be—a full **identity/account platform**, **CRM**, **customer 360**, **agency workflow engine**, or **multi-tenant enterprise profile system**. Those may appear in later phases; they are out of scope for the current wedge.

Stage 1 only needs enough **identity**, **session**, and **service-record** discipline to make Add-Car intake **trustworthy**, **trackable**, and **chargeable**, with a **handoff-ready** artifact for the office.

### Identity (who is speaking)

**Identity** answers: *who is this person in business terms, and how sure are we?*

| Stage | Meaning (macro) |
|-------|-----------------|
| **Anonymous / unknown** | Browser or channel presence only; no stable person key yet. |
| **Known lead (light)** | Enough to treat the person as the same lead across turns—e.g. **conversation/session linkage**, optional **phone or name** when collected or broker-pasted, **broker-side reference** when supplied. |
| **Identified for handoff** | Minimum contact/identity signals the broker needs to **trust follow-up** (product rules define fields; often name + phone for Add-Car-style trials)—still **not** a full verified account. |

**Certainty:** the system should distinguish **claimed** vs **confirmed** vs **office-visible** where product rules require it; overclaiming is a truth-layer failure (see §4.8–4.9).

**Stage 1 philosophy:** prefer **light keys** (session continuity, case id, phone/name, broker ref) over login-heavy identity. Defer heavy authentication unless the master roadmap explicitly promotes it.

**Optional lightweight identity/binding (future-facing):** In later Stage 1/Stage 2 optimization, an **optional lightweight identity/binding layer** (e.g. WeChat scan/binding for North American Chinese users, email-link binding, or similar) may be added to improve repeat-user continuity and reduce friction. This layer should remain **optional and per-client/per-market**, must not replace anonymous start or the formal-submit boundary, and must not promote the product into a full account/CRM platform.

### Session / conversation (this intake attempt)

**Session** is the **temporary conversational container** for one intake attempt: messages, turns, and in-progress structured state **before** or **until** the case is promoted per product rules.

- **Purpose:** carry the dialogue, capture fragments, and bind **latest intent** to **current structured truth** (see §4.9).
- **Same intake:** later messages belong to the same session when the product ties them to the same **session/thread id** (and thus the same in-flight case lane)—not when the user merely opens the app again without linkage (that may start a **new** session; policy is product-defined).
- **One identity, many sessions:** a customer may have multiple sessions over time; each is a separate intake attempt unless explicitly merged by broker or product rules.
- **Session vs service record:** the **thread** is for process and audit; the **service record** is the broker-facing durable case object. Chat is input; the record is the spine (see §8).

### Service record (what the office actually uses)

**Service record** is the **durable business object** for an Add-Car (or configured) case: structured fields, lifecycle state, identifiers visible in portal/workbench, and **what the broker can rely on** for next steps.

- **Not** “the chat log” as the product of record—though the thread may attach as **evidence** or **audit trail**.
- **Office trust** means: fields and states are consistent with **structured truth** (§4.8); customer-visible copy does not outrun that truth.

### Formal submit / handoff boundary

**Formal submit** (or equivalent product gate) is the boundary where **pre-submit conversational state** becomes **office-visible, persisted service-record truth** under the rules you ship—e.g. dual-write paths, `formal_submitted_at`, workbench visibility.

- **Before formal submit:** intake may be rich and conversational; some fields may be draft or customer-claimed; the office may **not** yet treat the case as received on the durable record.
- **After formal submit:** the service record is the **authoritative broker-facing artifact** for “what was submitted”; further edits are **updates** to that record, not “unsent chat.”
- **Chargeability and pilot narrative** should align with this boundary: what you bill for should map to **clarity and durability of the service record + handoff**, not to raw message count alone.

### Relationship summary

1. **Identity** → *who* (with explicit uncertainty levels).
2. **Session** → *this intake conversation* (ephemeral process container).
3. **Service record** → *the durable case* the office uses (spine of the product).
4. **Formal submit** → *promotion* from session-shaped intake to **office-visible service-record truth** when rules say so.

### Simulation and Role C

**Simulation / scenario replay** (§4.6) exercises the **same** state and service-record world as live intake; it is **supportive instrumentation** for demos and regression—not a separate product identity model.

---

## 3. Current Product Positioning

The most correct product positioning today is:

**Add-Car front-door intake + state-driven information cleanup + handoff-ready service-record tool for brokers**

Its core value is not "generic unified platform" and not "automatically finishing insurance work." Its real value is:

- quickly receiving messy customer input
- turning it into a structured service record
- making missing items explicit
- making next steps explicit
- making office handoff explicit
- helping offices ask fewer follow-up questions, miss fewer details, and receive cases faster
- helping brokers and customers move faster into quote/processing with clearer case readiness

### One-line sales framing

**Turn scattered customer messages into office-ready service records so the office can receive and process cases faster.**

### 3.0 Commercial value anchors (paid wedge — top 3)

For **commercial clarity**, treat these three outcomes as the **first-class** Stage 1 story. Other capabilities are supporting discipline, proof surfaces, or later convenience—not alternate centers of gravity.

1. **正式提交后可追踪** — After **formal submit**, the case is **real work**: shared durable record identity, dependable office-visible status/history, and continuation on the service record—not “unsent chat” or ambiguous drafts.
2. **办公室一眼摘要** — Conversation becomes **office-readable work input**: record + state answer *what this is / what’s missing / what’s next* without the broker reconstructing the whole thread manually.
3. **防漏项检查** — Missing key items stay **explicit** (`still_needed` / gap surfacing) through collection and handoff, cutting back-and-forth and rework.

**Secondary (not the paid-wedge center):** Image/attachment upload and extraction can reduce typing for some customers and already fits the “same record” story when present—but **do not** sell Stage 1 primarily on OCR/vision. Treat photo workflows as **near-term convenience** unless a named pilot blocks without them; prioritize the three anchors and structured-truth discipline first.

### 3.1 Immediate product focus (next cycles)

In the near term (including short planning horizons such as the next day or two), **the priority is not indiscriminate feature expansion.** The active north star is **Add-Car efficiency loop optimization**: make the flagship path feel like a **smooth, trustworthy, low-friction business loop** that reduces front-stage waste.

**Objectives for this focus**

- **Faster customer start** — obvious entry, clear task, same-record identity early.
- **Faster, clearer collection** — explicit gaps, explicit next action, minimal repeated asking.
- **Faster, safer office takeover** — credible handoff, clear ownership, quote-prep readiness understandable at a glance.

**Design priority order (unchanged)**

1. **Amazon-style flow** — clear step, progression, completion condition, next action.  
2. **Zendesk-style state** — lifecycle and status scannable across customer surface and workbench.  
3. **Intercom-style handoff** — received, not abandoned; office next step clear.  
4. **Stripe-style page** — clarity in service of the loop; pixel polish is not the primary lever in this phase.

**Replication and architecture**

Long-term delivery should remain **hot-swappable**: a stable common base (flow, state, handoff, record summary, workbench, simulation) plus **client / industry / scenario / copy / field-schema packs** — not a one-off insurance-only hardcode of everything.

This long-term direction does **not** change the immediate commercial boundary: **sell and harden Add-Car intake + handoff first** before broader platform ambitions.

### 3.2 Frontend Simplification + Light Identity Entry + Case Opening Discipline

This subsection defines one compact policy for three tightly linked topics in Stage 1:

- frontend simplification
- lightweight identity entry
- service-record opening and merge discipline

These are one product logic, not three separate systems.

**Unified product question set (default UI)**

The default front-stage should answer only:

- **你是谁** (identity confidence at current stage)
- **你在办什么** (current service matter / lane)
- **现在到哪一步** (lifecycle + missing items)
- **下一步做什么** (clear next owner/action)

Anything that does not directly support these questions should be hidden, folded, deferred, or moved to a secondary path.

**Lightweight identity entry (3-layer model)**

Stage 1 keeps identity lightweight and progressive:

1. **Anonymous start** — no login required; intake can begin immediately.
2. **Optional light binding** — optional continuity handle when useful (market/client dependent), without turning this into mandatory auth.
3. **Formal-submit business identity completion** — minimum operator-useful identity/contact fields are completed at submit boundary per Add-Car rules.

For North American Chinese users, **WeChat binding is a strong optional candidate**, but it is not the only valid path and must not replace anonymous start. Phone/email-style fallback remains valid in the same model.

**Case opening and merge policy (record by matter, not person)**

Stage 1 should not assume one person equals one record.

- One person may have multiple service records.
- One service record corresponds to one relatively coherent service matter/service unit.
- Repeated submissions should append only when **same matter evidence is strong at the same time**:
  - identity linkage is sufficient for operational continuity
  - same service type/lane
  - same vehicle (or explicitly same add-car unit)
  - close timing
  - high content continuity
- A new record should be opened when **matter separation evidence is strong**, including:
  - different vehicle / different service type
  - clear topic pivot ("another issue") even in same thread
  - lifecycle/handling stage implying a separate office work item
- When append triage detects `case_boundary=new_issue`, Stage 1 product truth is:
  - current record continuity may be acknowledged in copy
  - but execution should not silently treat this as "safe same-matter append"
  - the next implementation sprint must enforce one explicit action path (block append, force fork, or hard-confirm then append with audit tag)
  - default recommendation: **hard-confirm split to a new case** for Add-Car-first safety.

**Dual state semantics (`case_status` vs `lifecycle_status`)**

- `lifecycle_status` is the **process-state spine** for intake/handoff semantics (customer progress, office handoff stage, state-strip parity across portal/workbench).
- `case_status` is the **operator work-management label** (queue/workbench handling status such as reviewing/waiting/done/closed).
- Primary UI/ops decision axis for product behavior is `lifecycle_status`; `case_status` is secondary and should not redefine process truth.
- Acceptable overlap: both may appear in workbench detail for operator scanning.
- Not acceptable: using `case_status` to infer submit/handoff lifecycle truth, or using `lifecycle_status` as a replacement for operator queue labels.

**Lightweight person-link extension point (future-safe, non-auth)**

- Stage 1 should add only a minimal optional extension point, not a full identity platform:
  - optional `person_link_key` (stable, client-scoped, nullable)
  - optional `person_link_source` (e.g. `wechat_bind`, `phone_hash`, `broker_ref`)
  - optional `person_link_confidence` (`low` | `medium` | `high`)
- This extension point is for repeat-user continuity and cross-case linkage hints only.
- It must not become login/auth gating, customer-360, or mandatory pre-submit identity.

**Boundary and alignment rules**

- Keep **Identity -> Session -> Service record** as backbone (§2A).
- Keep **formal submit** as the promotion boundary to office-visible durable record truth.
- Keep Add-Car-first wedge and JSON-first runtime truth unchanged in Stage 1.
- Keep office workbench lightweight (record/state/action), not a CRM-style customer graph.

---

## 4. Core Product Skeleton (Five-Layer Model)

All future product decisions should be evaluated through these five layers.

Two complementary product layers—**simulation / scenario replay** and **flow explanation**—are defined in §4.6 and §4.7. They do not replace Stripe / Amazon / Zendesk / Intercom / Client Pack; they make demo, regression, and legible progress first-class without turning the product into free-form chat or a disconnected toy surface.

### 4.1 Stripe governs Page

Goal:

- page is clean and restrained
- visual hierarchy is strong
- first action is obvious
- it does not feel like a demo or noisy dashboard

### 4.2 Amazon-style governs Flow

Goal:

- the user knows what task they are doing
- the user knows what step they are in
- the user knows who does the next step
- the user knows whether this is the same record or a new issue
- the flow is driven by state, not by chatting

### Amazon-style Task Flow Skeleton (Add-Car v1)

This is the **macro** three-step task skeleton for the Add-Car flagship wedge in **Stage 1** product hardening. It guides what the flow should *feel* like; it does not prescribe a full workflow engine or replace incremental state migration.

**Three-step main flow**

1. **开始报送** — intake has started and input is anchored to a **service record** (same-record identity is established).
2. **补齐关键信息** — required information and evidence are completed until Stage 1 handoff criteria are met; gaps and next actions stay explicit.
3. **办公室接手处理** — the **office** continues the case on that record (handoff is real, not cosmetic).

**Completion condition for each step (when the step advances)**

- **Step 1 → Step 2:** when the system has a defined service record for the Add-Car case and submission is underway (the case is no longer “floating” outside record identity).
- **Step 2 → Step 3:** when Stage 1 rules say minimum required information for office handoff is satisfied—**还缺什么** is resolved or explicitly waived per product rules, and the case is **ready for office** in shared state terms.

**Primary owner of each step**

- Step 1 (**开始报送**): **customer** (system guides and captures).
- Step 2 (**补齐关键信息**): **system** owns surfacing state, gaps, and **下一步**; **customer** supplies what is still needed.
- Step 3 (**办公室接手处理**): **office**.

**Main interface priority**

The product surface should visually prioritize:

- **当前状态**
- **还缺什么**
- **下一步**
- **服务记录编号**

The **thread** remains useful as audit trail and supplemental input, not the primary layer users navigate to understand the task—aligned with **record-first**, **state-driven** migration (see §8).

### 4.3 Zendesk governs State

Goal:

- every service record has a clear state
- state is scannable, trackable, and handoff-friendly
- customer side, result card, and office workbench share the same state world as much as possible
- waiting-on / missing-items / ready-to-process should be obvious

### 4.4 Intercom governs Handoff

Goal:

- the user feels the case has been received
- office next step is clear
- the customer does not need to repeat already-submitted information
- same-case vs new-case boundary is clear
- handoff feels natural rather than robotic

### 4.5 Client Pack governs Replication

Goal:

- common product skeleton stays stable
- customer differences are expressed through configuration
- second and third client become much faster to launch
- long-term structure becomes: common skeleton + industry pack + client pack

### 4.6 Simulation / Scenario Replay Layer

**Why this layer exists**

- **Broker demo:** repeatable, credible walkthroughs without improvising in unconstrained chat.
- **Self-testing:** builders and operators can verify behavior against known, named paths.
- **Repeatable regression:** scenarios are assets that guard behavior as rules and models change.

**Product role**

- **Not** a toy demo disconnected from real intake semantics.
- **Not** free-form chat as the primary mode.
- A **scenario asset layer:** intentional, named, replayable paths that use the same service-record and state world as live intake.
- A **validation and demo surface for the Add-Car-first wedge**, not the main product being sold by itself.

**Recommended 1.0 structure (product skeleton)**

- A **third tab** or equivalent **dedicated front-stage entry** (alongside primary customer/office surfaces—not buried in settings).
- **Named scenario cards** so demos and tests point at explicit assets, not ad hoc typing.
- **A/B fixed-script roles** for deterministic multi-turn replay.
- A **C controlled-LLM variation role** where bounded ambiguity is the point of the scenario.
- **Multi-turn replay** end-to-end, not one-shot tricks.
- **Synchronized structured display:** current state, missing items, next action, and service record identity stay visible alongside replay; the **thread is secondary** (audit / process trail, not the spine for understanding the task).

**Main product principle**

Show how **customer language becomes a service record.** State, missing information, next action, and record identity must remain visible; the conversational thread supports the record, not the reverse—consistent with **record-first**, **state-driven** direction (see §8).

### 4.7 Flow Explanation Layer

**Why this layer exists**

- Users and brokers may not understand **what the system just completed** when a case advances or closes a visible step.
- Cases can feel like they **“end suddenly”** if the UI only shows a final panel or a reply without tying it to workflow position.
- The product must explain **progress through the task**, not only present an endpoint.

**What it must explain**

- **What step was completed** and **why** the case is now in the **next** step (or terminal handoff state).
- **What is still missing** when gaps remain.
- **Who owns the next action** (customer, system surfacing and guidance, office).
- **Whether the office has officially taken over**—handoff is explicit and credible (Intercom-like reassurance without vagueness), not implied by copy alone.

**Main product principle**

This is **not** generic chatbot chatter (“Anything else?”) detached from workflow. It should read like **business-process explanation:** calm, specific, and aligned with **Amazon-style task progression** and **Zendesk-like state**—reinforcing where the case sits in the office-ready service record, not substituting small talk for clarity.

### 4.8 Structured Truth Layer vs Reply Generation Layer (Industrial Standard)

Unified Intake must treat **what is true in structured, office-grade terms** as a separate contract from **how we phrase the customer-visible reply**. Weaknesses in recent hardening (handoff copy ahead of persistence, “ready” language while required fields are still missing, smooth replies that imply verification the system has not performed) are symptoms of **truth–reply drift**, not missing features alone.

**Structured truth layer (authoritative)**

- **Extracted / collected fields** and **explicit still-needed keys** (`collected_fields`, `still_needed_fields`, human-confirmation signals).
- **Lifecycle state** and **readiness flags** that drive the workbench and portal (e.g. `collecting`, `handoff_pending`, post–formal-submit office states)—including the distinction between *quote-prep ready for customer submit* and *office-visible persisted record*.
- **Gates:** handoff readiness vs **formal submit** to office (office-visible persistence); rules for when a case may advance a step in the Amazon-style skeleton.
- **Office-visible record truth:** what the office can rely on as received on the service record, not merely what the last message sounded like.
- **Time truth:** immutable first office-visible write vs rolling activity time (`formal_submitted_at` vs `updated_at` and related semantics)—no pretending a proxy timestamp is an exact customer action log.

**Reply generation layer (subordinate)**

- Turns the **current structured truth snapshot** into **natural, customer-appropriate wording**; acknowledges latest customer intent; varies phrasing **without changing facts**.
- Explains next steps **only** within the truth layer’s allowances (e.g. “submit to send the record” vs “office already has the record”).

**Constraint (non-negotiable)**

- The **reply generation layer is subordinate to the structured truth layer**. It may interpret, soften, route empathy, and choose templates—but **must not assert stronger facts than the truth layer supports**.

**Product principle**

Industrial, explainable, trustworthy behavior requires **explicit alignment checks** between API/state/UI copy and customer replies. The **two-layer** contract (structured truth vs reply) remains foundational; production-grade Add-Car behavior also requires an explicit **Intent layer** between them—see **§4.9**. Normative detail: `docs/sprints/TRUTH_LAYER_REPLY_LAYER_INDUSTRIAL_STANDARD_SPRINT/02_TWO_LAYER_STANDARD_SPEC.md` (truth vs reply) and `docs/sprints/TRUTH_INTENT_REPLY_THREE_LAYER_STANDARD_SPRINT/02_THREE_LAYER_STANDARD_SPEC.md` (full three-layer model).

### 4.9 Three-Layer Standard: Truth → Intent → Reply

**Why a third layer**

The two-layer rule (“structured truth outranks reply”) stops **factually wrong** wording but does not, by itself, stop **wrong answers**: long threads can still sound smooth while **ignoring what the latest turn is actually doing**—repeated handoff templates, generic closure, weak latest-turn specificity, and late-turn **intent collapse** (many distinct questions routed into one reply family). Industrial behavior needs a **middle contract**: what this turn is trying to accomplish, bounded and explainable, **before** wording is chosen.

**Layer roles (summary)**

| Layer | Role |
|-------|------|
| **Truth** | Office-grade snapshot: extracted fields, still-needed, lifecycle, gates (handoff vs formal submit), office-visible record, time semantics. **Authoritative for what is allowed to be true.** |
| **Intent** | **Current-turn job**: what the customer is doing *now* (supplement, correct, ask process, ask coverage/quote detail, claim materials sent, ask if office received, etc.), derived from latest text + context + **truth state as a constraint**. **Authoritative for what we should answer.** |
| **Reply** | Natural-language rendering that **answers the resolved intent** and **never exceeds** truth. Phrase, soften, reassure, vary—**no stronger facts**. |

**Constraint chain (non-negotiable)**

1. **Truth constrains Intent** — Intent classification cannot imply outcomes the truth layer forbids (e.g. “office already has the record” is not a valid intent resolution if formal submit / office-visible persistence does not support it).
2. **Intent constrains Reply** — The reply must address the **resolved current-turn intent** within truth; it is not enough for the reply to be merely truth-safe if it answers the wrong question.
3. **Reply cannot outrun Truth** — Same rule as §4.8: no receipt, completeness, verification, or timing claims the structured + persistence layer does not support.

**Relationship to other layers**

- **Flow explanation** (§4.7) and **right-rail record summary** remain **truth-aligned presentation**; they do not replace Intent—they show *where* the case is. Intent decides *what the latest message is asking for* within that state.
- **Simulation / replay** (§4.6) should be able to show **intent resolution** alongside state for regression (future implementation backlog).

**Normative spec**

Forbidden failure modes, acceptance criteria, and an industrial review checklist: `docs/sprints/TRUTH_INTENT_REPLY_THREE_LAYER_STANDARD_SPRINT/02_THREE_LAYER_STANDARD_SPEC.md`.

### 4.10 Contact-gap reminders (name / phone still missing)

When quote-related slots are far enough along but **name or phone** are not yet on the structured record, the product must stay **truth-honest** without letting that gap **hijack** every customer turn. This is a **reply-shaping** policy; structured truth (`still_needed_fields`, workbench/office summary) remains authoritative for what the office is missing.

| Strength | When |
|----------|------|
| **Strong** | **Before formal submit**, when the customer is **finishing intake**, **asking to submit / hand off**, or when **contactability is the real blocker** for the office to proceed. One clear ask in the main body is appropriate. |
| **Light** | When the **current turn is clearly about something else**: timeline, quote/coverage detail, “did the office receive it?”, materials status, or a **small supplement**—answer that first; any contact reminder is a **short secondary line**, not a second main paragraph. |
| **De-emphasize / skip in the reply** | When the **same contact-gap line would repeat across multiple consecutive assistant turns** (noise), or when the **latest intent is not contact collection**—after repetition, prefer **no extra tail** in the customer reply; **office-facing** summary and `still_needed` **continue to show the gap** so operators are not misled. |

**Principle:** Office truth stays complete; customer-facing wording **separates** the main answer from the contact nudge and **does not** paste the same nudge every turn.

---

## 5. Three-Stage Roadmap

### 5.1 Stage 1: Intake and Structuring

This is the current core stage and top priority.

Goals:

- turn messy customer input into a structured service record
- define the minimum required fields
- make missing information explicit
- make current state explicit
- make next step explicit
- make office handoff explicit

This stage does **not** aim to provide:

- real pricing
- direct carrier API execution
- full CRM capability
- fully automated insurance execution

Core value of this stage:

- fewer follow-up questions
- fewer missed details
- faster intake
- turning WeChat/screenshots/fragments into formal service records

### 5.2 Stage 2: Quote Preparation Automation

Goals:

- automatically determine whether the case is quote-ready
- automatically identify missing key items
- automatically classify:
  - ready to process
  - waiting for documents
  - needs manual confirmation
- automatically generate better quote-preparation summaries for office staff

This stage still does **not** mean true pricing. It means:

**Semi-automating quote preparation.**

### 5.3 Stage 3: Real Quote / Internal System Connection

Goals:

- connect to broker internal systems
- connect to comparative raters / quote APIs / carrier systems
- support real pricing flow when business conditions are mature enough

Only at this stage do we seriously consider:

- real price generation
- real underwriting/quote workflow
- deeper automated execution

---

## 6. Current Strongest Wedge: Add-Car

The current strongest flagship path is:

**Add-Car / add vehicle quote intake**

Why we focus here first:

- high frequency
- relatively standardized
- real office pain point
- easiest to explain ROI
- best wedge for a pilot
- best candidate for a replicable standard template

### Commercial principle

**Fully sharpen one narrow template first, then replicate. Do not broaden too early.**

### Immediate commercial promise

**Help brokers receive Add-Car customers faster, collect messy information better, reduce repeated back-and-forth, and hand off a structured service record faster into quote/processing.**

---

## 7. Definition of “Stage 1 Add-Car Is Truly Strong”

Stage 1 Add-Car is considered genuinely strong when:

- a first-time customer knows how to start
- messy user input can be reliably organized
- text, screenshots, and images can belong to the same service record
- the system can identify what is still missing
- the system can tell when the case is ready for office handoff
- the customer knows the next step
- the office knows the next step
- customer entry, result card, and workbench feel like the same record
- the system does not repeatedly ask for already-submitted information
- users and brokers no longer feel it is a toy demo

---

## 8. Core Flow Migration Direction

We should not continue strengthening a **chat-driven process** as the final form. We should gradually migrate toward a:

**State-driven process**

### 8.1 Current shape

- customer says something
- system replies
- the chat pushes the flow forward
- state is attached after the chat

### 8.2 Target shape

- what is the current state?
- what is the current record?
- what is still missing?
- who owns the next action?
- chat is only an input method
- record and state become the primary layer

### Migration principle

- do not rebuild from scratch
- do not remove chat in one step
- keep chat as the input layer
- gradually make state, record, and task the primary layer

---

## 9. Current Technical Baseline

### 9.1 Frontend

Current main frontend stack:

- React
- TypeScript
- Vite

Current key frontend files:

- `ui/src/pages/UnifiedIntakePage.tsx`
- `ui/src/api/clientConfig.ts`
- `configs/clients/<client_id>/ui_copy.json`

Current strengths:

- fast iteration
- fast UI changes
- well-suited for pilot and demo speed

Current weaknesses:

- `UnifiedIntakePage.tsx` is still large and mixed-responsibility
- flow logic, state display, and workbench view are not fully separated
- the frontend still behaves somewhat like an evolving large page rather than a cleanly layered product surface

### 9.2 Backend

Current main backend stack:

- FastAPI

Current key backend files:

- `services/fiqa_api/routes/inbox_triage.py`
- `services/fiqa_api/inbox_triage/triage.py`

Current strengths:

- fast business-rule iteration
- fast Add-Car improvement loop
- highly suitable for early-stage product hardening

Current weaknesses:

- `triage.py` is becoming too central
- logic, state, reply shaping, and handoff logic are too concentrated
- current form is closer to a strong pilot engine than a long-term production engine

### 9.3 Configuration Layer

Current config assets:

- `configs/industries/insurance/*.json`
- `configs/clients/<client_id>/*.json`

Current strengths:

- industry pack + client pack already exist in early form
- highly valuable for replication

Current weaknesses:

- still in the middle of being externalized from code
- common skeleton vs customer-specific difference still needs a clearer boundary

### 9.4 Data Layer

Current data/storage reality:

- lightweight JSON persistence
- `case_store.py`
- `session_store.py`

Current strengths:

- simple
- fast
- enough for pilot and early proof

Current weaknesses:

- limited concurrency, auditability, recovery, permissions, history, and operator-grade durability
- this is pilot-grade persistence, not production-grade persistence

### 9.5 Deployment Layer

Current deployment reality:

- frontend: Vercel
- backend: Cloud Run
- local: scripts + Vite + FastAPI + Docker/Compose support

Current strengths:

- fast to ship
- fast to demo
- good for rapid trial-and-error

Current weaknesses:

- frontend/backend version drift is possible
- `ui_copy`, environment variables, and backend image version need better consistency discipline

---

## 10. Productionized Technical Evolution Direction

### 10.1 Stage A: Current → Sellable Pilot

Keep:

- React + Vite
- FastAPI
- Vercel + Cloud Run
- config-driven approach
- lightweight persistence

At this stage, the most important thing is **not** changing the tech stack. The most important thing is making the Add-Car flagship path truly strong.

### 10.2 Stage B: After Pilot Stabilizes

Gradually evolve toward clearer structure.

#### Frontend evolution

Move from a large mixed page toward clearer layers:

- record layer
- state layer
- task layer
- office view layer

#### Backend evolution

Move from “rules + replies” toward:

- record model
- state model
- next-action model
- handoff model

#### Data evolution

Move from lightweight persistence toward:

- formal database-backed persistence
- better auditability
- more stable data structures

### 10.3 Stage C: Multi-Client and Scaled Operations

Gradually add:

- stronger persistence
- identity and permissions
- auditability
- observability
- finer-grained AI cost management
- client pack productization

---

## 11. Database Strategy

### 11.1 Current

Using **Postgres** in the small/early stage is fully reasonable. It is not a “temporary toy” database. It is already a mainstream production database direction.

### 11.2 Mid-stage

Postgres will likely remain the main database. The change is not from Postgres to something exotic; the change is from:

- lightweight usage

to:

- managed production-grade usage
- high availability
- backup and recovery
- stronger auditability
- more reliable operations

### 11.3 Longer-term

The long-term direction is usually not “replace Postgres entirely,” but:

- keep Postgres as the core system-of-record database
- add supporting layers when needed:
  - cache
  - object storage
  - search
  - analytics
- evolve the record model and state model before changing database strategy

### Database principle

**Do not rush to change databases. Get the record model and state model right first.**

---

## 12. AI / Token / Cost-Control Principles

### Principle 1: Use rules where rules are enough

For example:

- Add-Car field extraction
- state progression
- already_sent detection
- common handoff cases

### Principle 2: Use larger models only where ambiguity is real

For example:

- fuzzy phrasing
- very messy input
- complex follow-up
- more natural summarization or explanation

### Principle 3: Do not send every frontend step to an expensive model

Ideal production strategy:

- rules first
- smaller / cheaper model as fallback
- expensive model only when truly needed

### Principle 4: Record and state matter more than “beautiful extra words”

Stability, controllability, and lower cost matter more than sounding fancy.

---

## 13. Final Meaning of Client Pack

Client Pack is not just for changing wording. Long-term it should carry:

- branding and tone
- handoff differences
- rule differences
- UI copy
- pilot strategy differences
- customer-specific workflow details

### Ideal model

**80% common skeleton + 20% customer-specific difference**

That is how replication becomes real.

---

## 14. Commercial Core

We are not selling:

- fully automatic pricing
- a fully automatic insurance AI
- a full agency OS

We are selling:

**Add-Car intake and handoff assistant: front-door intake + information cleanup + structured service-record handoff for broker teams**

The **paid-wedge promise** should stay tied to the **three anchors in §3.0** (trackable after formal submit, office one-glance readability, missing-item surfacing)—not generic chat, CRM breadth, or “AI platform” ambition.

### Short-term success criteria

- Add-Car truly works
- customers are willing to use it
- offices are willing to receive from it
- the second client becomes easier to launch than the first

---

## 15. Current Biggest Risks

- broadening to too many scenarios too early
- trying to integrate real pricing APIs too early
- continuing to polish page chrome before state is truly clear
- failing to turn Client Pack into a true replication engine
- telling a product story that exceeds actual product maturity
- overpromising externally before pilot-grade technical reality is clearly understood

---

## 16. Current Master Strategy

### One-line master strategy

**First turn Add-Car Stage 1 into a state-driven, office-ready, replicable standard template. Then use that template to replicate, expand, and automate.**

---

## 17. What Future Sprints Should Align To

Every future major sprint should answer at least one of these:

1. Does this make Add-Car more office-ready?
2. Does this make the flow more state-driven?
3. Does this strengthen record identity and same-record continuity?
4. Does this make Client Pack more replicable?
5. Does this move the technical base from pilot-grade toward productionized structure?
6. Does this improve real pilot trust instead of just visual polish?
7. Does this strengthen **identity clarity**, **session clarity**, or **service-record trust** for Add-Car (see §2A)?

If not, the sprint should be questioned before implementation.

---

## 18. Closing Principle

The goal is not to become a bigger chatbot. The goal is to become a **narrow, valuable, replicable, productionizing business workflow product**.

The path is:

- sharpen one narrow wedge
- make state stronger than chat
- make record stronger than thread
- make office handoff trustworthy
- make client replication fast
- scale only after the template is real
