# P5 Capability Review — Workflow Platform Capability Contracts

**Status:** Architecture review — **not implementation**  
**Date:** 2026-07-25  
**Audience:** Founder · Product · Engineers (onboarding)  
**Governing SSOT:** `docs/product/p20_product_north_star.md`  
**Codex:** `docs/FOUNDER_PRODUCT_CODEX_V1.md`  
**Decision law:** `docs/product/decision_log.md`  
**Runtime truth:** `docs/CURRENT_PRODUCT_SHAPE.md`  
**Prior capability packages:**  
`docs/product/p4_capability_01_customer_lookup.md` ·  
`docs/product/p4_capability_02_claim_prefill.md` ·  
`docs/product/p4_capability_03_smart_claim_start.md`

---

> **One sentence:** Workflow owns the customer journey; Capabilities own one business responsibility each; Adapters own external systems. Workflow must never know how Lookup, AMS, or AI work inside.

---

## 0. Product posture (read first)

| Truth | Source |
|-------|--------|
| Product is an **Insurance Task Platform** (customer Mini Program + broker Workbench), not a carrier OS or full CRM | Codex §1 |
| Workflow is already stable enough to extract **reusable capability contracts** | Founder goal for P5 |
| **Capability before Integration** — contract + mock + flag, then adapter swap | Codex §5; D-016/P4 |
| Paid pilot = product-only surface; SearchForge lab stays out | `CURRENT_PRODUCT_SHAPE.md` |
| AI assists; workflow + humans decide | Codex §6 / §9 |

**Target architecture (5-year clean):**

```text
Workflow Platform          ← journey, One Active Case, surface routing, gates
        ↓
Capability Layer           ← contracts: Lookup, Prefill, Start, Evidence, …
        ↓
Adapters                   ← Mock / AMS / CRM / Carrier / AI / Directory
```

**Anti-pattern (forbidden):**

```text
Workflow → Direct CRM → Direct AI → Direct Graph
```

---

# 1. Capability Catalog

Capabilities are numbered for catalog clarity. **P4 Cap 01–03 keep their names.** Other IDs are review catalog IDs (not a demand to renumber code).

| ID | Capability | One question it answers | Maturity today |
|----|------------|-------------------------|----------------|
| **C01** | **Customer Lookup** | Who is this customer? | Mock harness + contract (flag OFF in pilot) |
| **C02** | **Customer Prefill** *(Claim Prefill)* | What do we already know vs still need? | Mock classifier + contract |
| **C03** | **Smart Claim Start** | How should Start Claim be presented? | Mock planner + optional Mini Program wire (flag OFF) |
| **C04** | **Identity** | Is there a durable person link for One Active Case? | Production (P29B / D-016) |
| **C05** | **Case Resume** | What Active Case should this person continue? | Production (Active Case index) |
| **C06** | **Evidence Upload** | How is evidence durably bound to the case? | Production (unified upload path) |
| **C07** | **Request More** | What exceptional items does the broker still need? | Production (Slice1 / broker_requested) |
| **C08** | **Waiting State** | When the customer owes nothing, what do they see? | Production Commit 1 (D-014 Case Status) |
| **C09** | **Case Timeline** | What happened, in order, for trust and support? | Production (append events; not yet a clean facade) |
| **C10** | **Case Lifecycle Close** | How does a case become terminal History? | Production (D-017 Close → History) |
| **C11** | **Broker Case Brief** | What does the broker need in ~10 seconds? | Production (workbench projection; not yet a clean facade) |
| **C12** | **Notification** | How do we nudge customer or broker without owning journey? | Future — record only |
| **C13** | **Default Intake Plan** | What must a new claim collect without broker gate? | Production (D-009; workflow-adjacent) |

### Catalog inclusion rule

A reusable capability must:

1. Answer **exactly one** business question.  
2. Expose a **stable behavioral contract** Workflow can call.  
3. Survive **adapter replacement** (mock → AMS, rule → AI assist) without rewriting journey.  
4. Keep **customer-visible vs broker-only** boundaries explicit.  
5. Degrade to a **complete, non-dead-end** result on failure.

### Explicit non-capabilities (stay Lab or stay Workflow)

| Item | Classification | Why |
|------|----------------|-----|
| RAG / Qdrant query | **SearchForge Lab** | Optional knowledge wedge; not claim spine |
| Knowledge Graph / Graph Lab | **Lab** | R&D; not journey contract |
| Agent Studio / multi-agent | **Lab** | Experiment surface |
| Retriever / tuner | **Lab** | Platform heritage |
| Constitution / Today First projection | **Workflow Platform** | Journey law + view model, not an external adapter concern |
| Triage “paste → draft” | **Broker assist capability (later)** or Lab-assisted | Valuable; must not drive customer claim authority |

---

# 2. Capability Contracts

Behavior only. No implementation. No API schema redesign.

---

## C01 — Customer Lookup

| Field | Contract |
|-------|----------|
| **Purpose** | Answer “Who is this customer?” so the journey can trust known context without inventing a CRM SoR. |
| **Owner** | **Server capability** (read-only facade). Customer never owns matching. Broker may *see* confidence; customer never sees match machinery. |
| **Inputs** | Durable identity handle (`person_link_key` / session). Optional scenario keys in mock/QA only. |
| **Outputs** | Complete `LookupResult`: match status, confidence, customer/policy/vehicles summaries, active-case hint, prefill seeds, `next_action`, reason codes, source. |
| **Customer Visible** | Human consequences only (later via Prefill/Start): “we know you,” vehicle chooser, stale-policy confirm. Never OpenID, person_link, match_status, refs. |
| **Broker Only** | `lookup_confidence`, broker_customer_ref, full reason codes, ambiguous-match internals, AMS diagnostics. |
| **Workflow Contract** | `lookup(identity) → LookupResult` (always complete). Workflow branches on `next_action` / match status — never on CRM vendor fields. |
| **Failure Modes** | `NOT_FOUND` / unmatched → blank claim path. `AMBIGUOUS_MATCH` → contact broker; no auto-merge. `STALE_POLICY` → confirm gate. `LOOKUP_UNAVAILABLE` / CRM down → graceful blank degrade (HTTP-success semantics for journey). Multiple vehicles → confirm, not silent pick. |
| **Dependencies (future adapters)** | Mock Directory (now) · AMS · CRM · Carrier directory · Broker office directory. **Never** writes Customer/Policy/Vehicle. |
| **Independence** | Cap 02/03 consume `LookupResult` only. Replacing Mock→AMS must not change Workflow or Cap 02/03 contracts. |

**Locked law (P4):** Lookup is READ ONLY. Lookup is not Source of Truth. Claim case remains SoR after create.

---

## C02 — Customer Prefill (Claim Prefill)

| Field | Contract |
|-------|----------|
| **Purpose** | Never ask the customer for facts we already know; classify every Start Claim field as AUTO / customer confirm / broker-owned / unknown. |
| **Owner** | **Server capability** (classification). Presentation may be customer-facing; classification labels are not. |
| **Inputs** | `LookupResult` only (plus Business Contract field list). |
| **Outputs** | Complete `PrefillResult`: per-field class (`AUTO_PREFILL` \| `CUSTOMER_REQUIRED` \| `BROKER_REQUIRED` \| `UNKNOWN`), suggested values, confirm flags (vehicle / stale policy). |
| **Customer Visible** | Effects only: fewer fields, chips, confirm gates. Never enum names or “AUTO_PREFILL.” |
| **Broker Only** | Gaps marked `BROKER_REQUIRED`; confidence inherited from Lookup for workbench. |
| **Workflow Contract** | `prefill(LookupResult) → PrefillResult`. Workflow does not re-implement field taxonomy. |
| **Failure Modes** | Weak/ambiguous lookup → zero AUTO. Missing email/VIN → `UNKNOWN` (do not invent). Stale/multi-vehicle → confirm classes, not silent AUTO. |
| **Dependencies** | Cap 01 contract. Future richer AMS fields promote UNKNOWN→AUTO without contract rewrite. |
| **Independence** | Does not call CRM. Does not write cases. Swappable when Lookup shape holds. |

**Locked law:** Prefill is suggestion; claim case is SoR. No CRM write-back.

---

## C03 — Smart Claim Start

| Field | Contract |
|-------|----------|
| **Purpose** | Present Start Claim so known context feels trusted and customer effort stays on “what happened today?” |
| **Owner** | **Server plan + Customer surface consumer**. Broker may mirror chips; journey UX is customer-owned. |
| **Inputs** | `LookupResult` + `PrefillResult`. |
| **Outputs** | `SmartClaimStartPlan`: mode, screens, chips, confirm gates, question visibility, primary/secondary CTAs. |
| **Customer Visible** | Mode UX: Continue active · chips · vehicle/policy confirm · accident Must Haves · optional photos · contact broker · blank degrade. |
| **Broker Only** | Confidence, technical IDs, match diagnostics (via Brief, not Start Claim page). |
| **Workflow Contract** | `plan_start(LookupResult, PrefillResult) → SmartClaimStartPlan`. Workflow/Mini Program **renders plan**; does not invent matching rules. |
| **Failure Modes** | Active case → Continue (never second create). Ambiguous → contact broker. Lookup down → blank degrade. Validation/transport/server errors distinguished. No dead ends. |
| **Dependencies** | Cap 01 + Cap 02. Identity + One Active Case (Workflow gates). |
| **Independence** | CRM swap at Cap 01 only. AI may later draft story hints behind optional assist — must not own plan authority. |

---

## C04 — Identity

| Field | Contract |
|-------|----------|
| **Purpose** | Provide the smallest durable person link so One Active Case survives storage clear / new device — without a Customer Account product. |
| **Owner** | **Server**. Channel (Mini Program) supplies ephemeral login; server mints opaque link. |
| **Inputs** | Channel login proof (e.g. wx.login code). |
| **Outputs** | Opaque `person_link_key`; session usable for resume; never raw OpenID to clients as product data. |
| **Customer Visible** | Continuity (“继续当前报案”) — not identity chrome, not OpenID. |
| **Broker Only** | That source is WeChat Mini Program; never OpenID in UI. |
| **Workflow Contract** | `establish_session(channel_proof) → identity_handle`. Workflow uses handle; never implements HMAC/OpenID. |
| **Failure Modes** | Login fail → retry / contact broker; Production rejects anon-only create. No silent second identity. |
| **Dependencies** | WeChat (now) · future channel adapters. Not AMS. Not CRM profile. |
| **Independence** | Lookup consumes identity handle; Identity does not perform CRM match. |

**Locked law (D-016 / P29B):** OpenID is technical; not a profile/history system.

---

## C05 — Case Resume

| Field | Contract |
|-------|----------|
| **Purpose** | Resolve the single Active Case for an identity so Workflow can Continue without case pickers. |
| **Owner** | **Server** (Active Case index). |
| **Inputs** | `person_link_key` (and/or validated resume token for task surfaces). |
| **Outputs** | `null` \| `{ case_id, resume_available, …customer-safe summary }`. |
| **Customer Visible** | Continue vs Start Claim on Service Home; never case picker lists. |
| **Broker Only** | Internal case_id in workbench; customer sees human labels. |
| **Workflow Contract** | `resolve_active_case(identity) → ActiveCaseRef \| none`. Create path must resolve→resume, never fork. |
| **Failure Modes** | None → Start Claim. Binding stale/closed → clear and allow one new Active Case (after Close). Token invalid → re-enter / contact. |
| **Dependencies** | Identity; Case store. Not CRM. |
| **Independence** | Lookup may *hint* active_case; Resume index is SoR for binding. |

**Locked law (D-001):** At most one Active Case.

---

## C06 — Evidence Upload

| Field | Contract |
|-------|----------|
| **Purpose** | Durably accept photos/docs bound to the case so nothing is silently lost; satisfy default intake or Request More items. |
| **Owner** | **Server** storage + case binding. Customer captures; Broker reviews. |
| **Inputs** | Authorized case/task context, slot/item intent, binary/media, idempotency keys. |
| **Outputs** | Bound evidence reference + updated projections (customer task + broker detail). |
| **Customer Visible** | Upload progress, success (“已收到”), retry; slot labels in human language. |
| **Broker Only** | Storage keys, internal attachment IDs, OCR/debug (if any). |
| **Workflow Contract** | `upload_evidence(case_auth, slot, payload) → EvidenceReceipt`. Workflow chooses *when*; capability owns durability + binding. |
| **Failure Modes** | Transport vs validation vs server distinguished. Partial upload unbound until valid bind. Never creates second case. Append-first for voluntary extras while waiting. |
| **Dependencies** | Object storage · later OCR/AI assist adapters (suggest, never auto-advance authority). |
| **Independence** | Replace storage vendor without changing journey screens’ meaning. |

---

## C07 — Request More

| Field | Contract |
|-------|----------|
| **Purpose** | Let the broker open one ordered exceptional request group; customer completes only the active item; return to broker review. |
| **Owner** | **Broker** creates/amends/withdraws; **Customer** satisfies active item; **Server** projections. |
| **Inputs** | Broker command (items, reason, expected version); customer submission for active item. |
| **Outputs** | Open request group state; one customer next action; one broker next action; read-after-write on both faces. |
| **Customer Visible** | Today’s Focus item, Why/After, complete CTA — not request-group machinery. |
| **Broker Only** | Request editor, withdraw/amend, version conflicts, internal item ids. |
| **Workflow Contract** | `request_more(case, items) → projection`; `satisfy_item(case, item, payload) → projection`. Default intake must **not** require this capability (D-009). |
| **Failure Modes** | Version conflict → reload. Item not active → reject. Terminal/closed case → reject. No Unsupported Choices (never ask what customer cannot complete). |
| **Dependencies** | Case aggregate · Evidence · Constitution projection. AI may draft copy only. |
| **Independence** | Not Lookup. Not Prefill. Exception path beside default plan. |

---

## C08 — Waiting State

| Field | Contract |
|-------|----------|
| **Purpose** | When customer owes no work, show a living Case Status (“陈总正在审核”), not a dead Task Home. |
| **Owner** | **Workflow routing + Server constitution stage**; surface is customer. |
| **Inputs** | Case projection: owes work? open Request More? waiting_broker? |
| **Outputs** | Surface mode: Action Needed (Task Home) vs Waiting Broker (Case Status) vs later Closed. |
| **Customer Visible** | Status title, what happens next, secondary voluntary append (when shipped), contact. |
| **Broker Only** | Internal phase enums, aggregate versions. |
| **Workflow Contract** | `surface_for(case_projection) → ActionNeeded \| Waiting \| Closed`. Capabilities do not invent Waiting copy. |
| **Failure Modes** | Misclassified “waiting” while work owed → FAIL (One Truth). Never strand on blank. |
| **Dependencies** | Constitution / default plan / Request More open state. |
| **Independence** | Not Notification. Not Timeline (Timeline answers history; Waiting answers now). |

**Locked law (D-014):** Waiting is a designed state.

---

## C09 — Case Timeline

| Field | Contract |
|-------|----------|
| **Purpose** | Append-only “what happened” for trust, support, and broker 10-second context. |
| **Owner** | **Server**. Broker-readable; customer sees human receipts, not raw timeline dump (unless later product chooses a safe subset). |
| **Inputs** | Case id + typed event (submit, upload, request more, close, …). |
| **Outputs** | Ordered event list / brief-ready history. Distinct from current-state projection. |
| **Customer Visible** | Receipts / “已提交” moments — not engineer event names. |
| **Broker Only** | Full timeline, actor, system reason codes. |
| **Workflow Contract** | `append_event(case, event)`; `list_timeline(case)`. Workflow emits; capability stores/orders. |
| **Failure Modes** | Append fail must not silently drop accepted user work (read-after-write). Cap size / redact rules stay inside. |
| **Dependencies** | Case store. Future analytics adapters consume; do not write journey. |
| **Independence** | Swappable storage representation; event *meanings* stay stable. |

---

## C10 — Case Lifecycle Close

| Field | Contract |
|-------|----------|
| **Purpose** | Terminal History: stop customer mutations, clear Active Case binding, allow exactly one new Active Case later. |
| **Owner** | **Broker** action; **Server** enforcement. |
| **Inputs** | Authorized close command + case. |
| **Outputs** | Terminal fields; bindings cleared; customer mutations → `case_closed_read_only`. |
| **Customer Visible** | Read-only closed meaning (later); no Close control. |
| **Broker Only** | Close Case control; soft-archive ≠ Close. |
| **Workflow Contract** | `close_case(case) → HistoryRef`. Soft archive is queue filter only. |
| **Failure Modes** | Double-close idempotent/safe. Customer retry cannot reopen. |
| **Dependencies** | Case Resume index · Timeline. |
| **Independence** | Not CRM archive sync (future adapter optional). |

**Locked law (D-017).**

---

## C11 — Broker Case Brief

| Field | Contract |
|-------|----------|
| **Purpose** | Project a 10-second understand artifact: story, vehicle, evidence, open requests, next broker action. |
| **Owner** | **Server projection for Broker**. |
| **Inputs** | Case aggregate + timeline + evidence + open requests + optional Lookup overlay. |
| **Outputs** | Brief DTO for Workbench (human language first). |
| **Customer Visible** | Nothing from this capability directly. |
| **Broker Only** | Entire brief; confidence; gaps; draft assists. |
| **Workflow Contract** | `brief(case) → BrokerBrief`. Workflow/Workbench renders; does not scrape raw tables ad hoc forever (cleanup target). |
| **Failure Modes** | Partial data → show known + explicit gaps; never fake completeness. |
| **Dependencies** | Case · Evidence · Timeline · Request More · optional Lookup. AI summarize = adapter behind brief, not authority. |
| **Independence** | CRM fields may enrich brief later without changing customer journey. |

---

## C12 — Notification (future)

| Field | Contract |
|-------|----------|
| **Purpose** | Nudge humans when Workflow state changes (e.g. broker requested more; case waiting too long) — without owning next action. |
| **Owner** | **Server** fan-out; channel adapters (WeChat template, SMS, email). |
| **Inputs** | Notification intent from Workflow (template key, case ref, audience). |
| **Outputs** | Delivery attempt result (sent / skipped / failed). |
| **Customer Visible** | Channel message in human language pointing back into journey. |
| **Broker Only** | Office alerts; never customer-internal IDs. |
| **Workflow Contract** | `notify(intent) → DeliveryResult`. Workflow decides *whether*; capability decides *how*. |
| **Failure Modes** | Delivery fail must not corrupt case state; in-app Waiting/Action remains SoR. |
| **Dependencies** | WeChat · SMS · email providers. |
| **Independence** | Fully optional; journey works without push. |

**Priority: P2.** Do not build before pilot evidence demands it.

---

## C13 — Default Intake Plan (workflow-adjacent)

| Field | Contract |
|-------|----------|
| **Purpose** | New claim immediately exposes system_default tasks so first-time customers are never stuck waiting for broker Request More. |
| **Owner** | **Server / Workflow law** (D-009). Not an external adapter capability. |
| **Inputs** | New case create. |
| **Outputs** | Default plan → Constitution → customer Task Home projection. |
| **Customer Visible** | Today’s Focus tasks. |
| **Broker Only** | That items are `system_default` vs `broker_requested`. |
| **Workflow Contract** | Create claim ⇒ default plan attached. Request More adds; does not replace defaults silently. |
| **Failure Modes** | Missing default plan ⇒ empty Waiting = release FAIL. |
| **Dependencies** | Constitution projection. |
| **Independence** | Vertical-specific plan content; spine pattern reusable. |

*Catalog note:* C13 is **Workflow Platform law packaged as a plan provider**, not an AMS adapter. Keep it out of the CRM layer.

---

# 3. Capability Dependency Map

```text
C04 Identity
    |
    v
C05 Case Resume <---- C10 Close (clears binding)
    |
    +------------------+------------------+
    |                  |                  |
    v                  v                  v
C01 Lookup -----> C02 Prefill -----> C03 Smart Claim Start
    |                                     |
    |         Workflow Journey            |
    |      (create / continue)            |
    |                                     v
    |                          Case Aggregate <---- C13 Default Plan
    |                                 |
    |              +------------------+------------------+
    |              |                  |                  |
    |              v                  v                  v
    |         C06 Evidence       C07 Request More   C09 Timeline
    |              |                  |                  |
    |              +--------+---------+                  |
    |                       v                            |
    |                 C08 Waiting State                  |
    |                       |                            |
    +---------------------->+<---------------------------+
                            |
                            v
                      C11 Broker Brief
                            |
                            v
                      C12 Notification (future, optional)

Adapters (below all of the above):
  Mock Directory · AMS · CRM · Carrier · Object Storage · AI assist · Channel push
```

### Hard dependency rules

| Rule | Meaning |
|------|---------|
| **Workflow → Capability** | Allowed |
| **Capability → Capability** | Only along the arrows above (Lookup→Prefill→Start; Evidence/RequestMore→Waiting inputs) |
| **Capability → Adapter** | Allowed inside capability boundary |
| **Workflow → Adapter** | **Forbidden** |
| **Capability → Workflow internals** | Forbidden (no UI routing inside Lookup) |
| **AI → Authority** | Forbidden (AI may draft inside Brief / triage assist; never Close, never Request More submit, never Active Case fork) |

### Independence checklist (must remain true)

| If we replace… | Workflow still works because… |
|----------------|-------------------------------|
| CRM / AMS | Cap 01 adapter swap; Cap 02/03 unchanged |
| Mock Directory | Same `LookupResult` |
| AI model | Only assist adapters behind Brief/triage/OCR |
| Graph / RAG | Never on main claim chain |
| Object storage | Cap 06 adapter |
| Mini Program channel | Identity + Resume contracts stay; channel adapter changes |

---

# 4. Workflow vs Capability Boundaries

## Workflow Platform owns

| Owns | Examples |
|------|----------|
| Customer journey sequencing | Home → Start / Continue → Task → Receipt → Waiting |
| One Active Case policy | Never second Active Case; Continue vs Contact |
| One Task / Today First / Why / After / One Truth | Constitution projection to surfaces |
| Surface routing | Action Needed vs Waiting vs Closed |
| Human decision boundary | No auto-send to carrier |
| Release acceptance | Golden Production QA story |
| When to call capabilities | e.g. call Lookup on Start Claim entry — not *how* Lookup matches |
| Feature flags at journey edge | smartClaimStartEnabled; degrade to blank form |

## Capability Layer owns

| Owns | Examples |
|------|----------|
| One business responsibility | “Who is this?” / “What do we know?” / “Bind this photo” |
| Complete result on every failure mode | Lookup unavailable still returns a full result |
| Customer-visible vs broker-only data split | Confidence never on customer chips |
| Adapter boundary | Mock vs AMS behind Cap 01 |
| Idempotency / durability of its verb | Upload receipt; Request More version conflict |

## Adapters own

| Owns | Must not own |
|------|----------------|
| Vendor protocols (EZLynx, Epic, WeChat, S3) | Journey copy, One Active Case, Form Gate |
| Raw vendor payloads | Customer UI jargon |
| Availability / rate limits | Silent wrong-person merge |

## Boundary anti-patterns (reject in review)

1. Start Claim page calling AMS SDK directly.  
2. Prefill writing CRM.  
3. Lookup creating cases.  
4. Waiting State implemented only as copy on Task Home.  
5. Request More required for default first-time intake.  
6. Graph/RAG required for `/readyz` on paid pilot.  
7. AI advancing `claim_phase` or closing cases.

---

# 5. Lab vs Product Recommendations

| Asset | Classification | Recommendation |
|-------|----------------|----------------|
| **Unified Intake + Mini Program claim journey** | **Workflow Platform** | Keep as product spine |
| **Cap 01–03 contracts + mocks** | **Capability Layer (Product)** | Keep; wire under flags; AMS later |
| **Identity / Resume / Evidence / Request More / Waiting / Close** | **Workflow + Capability (Product)** | Formalize facades over time; already product law |
| **Broker Workbench / Case Brief** | **Product** | Clean C11 facade when touching workbench |
| **Inbox triage paste→draft** | **Broker assist (Product-adjacent)** | Keep product-only; optional AI adapter; do not block claim spine |
| **RAG / `/api/query` / Qdrant demos** | **SearchForge Lab** | Stay behind `PRODUCT_ONLY`; never pilot-critical |
| **Graph Lab / Knowledge Graph** | **Lab** | No Workflow dependency |
| **Agent Studio / multi-agent** | **Lab** | Extract patterns only if a Capability contract needs an AI adapter |
| **Retriever / tuner / embedding warming** | **Lab** | Optional for notice/knowledge wedges |
| **Guardrails (intake scenario batteries)** | **Product quality tooling** | Keep as release hygiene; not a runtime customer capability |
| **platform_full routers** | **Lab surface** | Forbidden on paid pilot URLs |

### Shared-capability candidates (Lab → Product only when proven)

| Candidate | Promote when… | Becomes… |
|-----------|----------------|----------|
| Document/OCR extract | Broker time saved on real cases | Adapter behind Evidence or Brief |
| Notice/knowledge answer | Office uses it weekly in pilot | Separate **Knowledge Assist** capability (broker-only) |
| Graph entity link | Disambiguation pain is real | Adapter behind Lookup (still `LookupResult`) |
| Generic workflow kernel semantics | >1 vertical / multi-broker ops pain | Workflow Platform kernel (still not Temporal-by-default) |

**Rule:** Lab inventions enter Product only by **passing a Capability contract**, not by wiring Graph into Mini Program.

---

# 6. Implementation Priority

Priorities are **product architecture order**, not a commit authorization.

### P0 — Spine already shipping; keep contracts sacred

| Item | Why P0 |
|------|--------|
| **C04 Identity** | Constitutional One Active Case |
| **C05 Case Resume** | Continuity |
| **C06 Evidence Upload** | Trust; nothing lost |
| **C07 Request More** | Broker exception path |
| **C08 Waiting State** | No dead-end after submit |
| **C10 Close → History** | Terminal truth |
| **C13 Default Intake Plan** | First-time path without broker gate |
| **Workflow gates** (Form / Nav / Build / Golden QA) | Release law |

*P0 work is stabilize + document boundaries — not new CRM.*

### P1 — Capability Layer that unlocks CRM without rewrite

| Item | Why P1 |
|------|--------|
| **C01 Lookup** live consumer paths (still mock or AMS behind facade) | Who? |
| **C02 Prefill** live Start Claim classification | Ask only new facts |
| **C03 Smart Claim Start** Founder GO + controlled flag ON in QA | Journey feel |
| **C09 Timeline** as explicit capability facade | Clean Brief/support |
| **C11 Broker Case Brief** facade | 10-second understand + Lookup overlay |
| **AMS/CRM adapter behind C01 only** | Integration without journey rewrite |

### P2 — After pilot evidence

| Item | Why P2 |
|------|--------|
| **C12 Notification** | Optional nudge; journey already works |
| Richer Prefill fields (email, full VIN via Request More) | Demand-driven |
| Household disambiguation UI for AMBIGUOUS | Rare; contact broker works |
| Knowledge Assist (from Lab RAG) as broker-only capability | Not claim spine |
| Multi-tenant / second industry spine reuse | Platform horizon |
| AI draft adapters with audit | Assist only |

### Explicitly not scheduled (record only)

- Customer Account / profile center  
- Multi-case picker  
- CRM write-back from Prefill  
- Temporal/Camunda migration  
- Auto-send to carriers  
- Graph-required intake  

---

# 7. Engineer onboarding cheat sheet

After this review, a new engineer should memorize:

| Layer | Owns |
|-------|------|
| **Workflow Platform** | Journey, One Active Case, Today First, surface routing, human gate, Golden acceptance |
| **Each Capability** | One business question + complete degrade + customer/broker visibility split |
| **Adapters** | AMS/CRM/AI/storage/channel protocols |
| **SearchForge Lab** | RAG, Graph, Agent, Retriever, tuner, platform_full demos |
| **Workflow Platform product** | Claim intake spine + Workbench + durable Postgres cases |

**Call pattern:**

```text
Workflow needs “who is this?”
  → calls Customer Lookup capability
  → receives LookupResult
  → does not import EZLynx client

Workflow needs “start claim UX”
  → calls Smart Claim Start with Lookup+Prefill results
  → renders plan
  → does not re-encode match rules
```

---

# 8. Success criteria (P5 exit)

| Criterion | Met? |
|-----------|------|
| Workflow ownership is explicit | Yes — §4 |
| Each reviewed capability has Purpose/Owner/IO/Visibility/Contract/Failures/Deps | Yes — §2 |
| Cap 01–03 remain independently evolvable | Yes — dependency map |
| Additional reusable capabilities named without inventing unproven product | Yes — C04–C13 |
| Lab vs Product classified | Yes — §5 |
| Priority P0/P1/P2 set without authorizing commits | Yes — §6 |
| Target architecture is Capability Layer, not direct CRM/AI/Graph | Yes — §0 / §3 |

**Founder ask (review only):** Acknowledge catalog + boundaries. Authorize later loops separately (wire flags, AMS adapter, facade cleanups) — never “implement all P1 from momentum.”

---

## Document control

| Version | Date | Change |
|---------|------|--------|
| v1 | 2026-07-25 | P5 Capability Review from Codex, Decision Log, P4 Caps, Constitutions, Current Product Shape |

**Change rule:** Contract changes to C01–C03 require Founder acknowledgment and Decision Log entry if they alter product law. Catalog IDs C04–C13 may refine naming when a dedicated capability package is opened.
