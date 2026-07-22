# P20 Product Decision Log

**Status:** Permanent record of why product law exists  
**Authority:** Product Constitution v1 (`docs/product/p20_product_constitution_v1.md`)  
**Date:** 2026-07-17  

This is **not** a changelog.  
It does **not** list commits, tickets, or UI tweaks.

It explains **why** an important product decision exists, so future features, engineers, designers, AI assistants, and Founder reviews do not re-argue settled law.

---

## Relationship to other governance docs

| Document | Answers |
|----------|---------|
| Product Constitution | What is always true |
| UX Writing Guide | How we say it |
| Founder Review Checklist | Whether this change may merge |
| **Decision Log** | Why we chose this law or pattern |

If a Founder Review blocks a change, and the block creates or clarifies lasting law, add a Decision Log entry.

---

## Entry template

Copy for every new decision:

```text
### D-XXX — Short title

| Field | Content |
|-------|---------|
| **Decision** | One sentence: what we decided |
| **Context** | What problem or prototype loop forced the choice |
| **Alternatives Considered** | 2–4 real options we rejected |
| **Why This Decision** | Why the chosen option wins for the customer journey |
| **Constitution Principle** | Which frozen principle this supports (or “n/a — operational”) |
| **Date** | YYYY-MM-DD |
| **Status** | Active / Superseded by D-YYY / Amended |
```

**Rules**

1. One decision per entry.  
2. Write for a future reader who was not in the room.  
3. Prefer Constitution principle names over feature names.  
4. Supersede; do not delete history.  
5. Skip routine copy edits unless they change product law.

---

## Active decisions (seed from Prototype Loops 3.x–4.2)

### D-001 — One Active Case

| Field | Content |
|-------|---------|
| **Decision** | A customer has at most one Active Case in progress. Customer create must resolve→resume that case; never fork a second Active Case. Explicit「开始新的报案」with an Active Case shows policy (continue / contact broker) — customer cannot open a second Active Case. Split/merge is Broker/office only. |
| **Context** | Loop 3.x (esp. 3.8–3.9). Case pickers and “which matter am I in?” destroyed trust after an accident. Continuity is the product. P0 Identity Foundation made this server-enforced via durable `wx_*` identity. |
| **Alternatives Considered** | (1) Multi-case home list like a claims portal; (2) Silent second case on return; (3) Always ask “new or existing?” before any continue; (4) Client-only resume-token guard (rejected — not Constitutional). |
| **Why This Decision** | Under stress, one clear matter restores motion. Server identity binding survives storage clear / new device. |
| **Constitution Principle** | One Active Case |
| **Date** | 2026-07-17 (updated 2026-07-22) |
| **Status** | Active |
| **SSOT** | `docs/product/p0_one_active_case_identity_foundation.md` |

---

### D-002 — Append-first, Split-later

| Field | Content |
|-------|---------|
| **Decision** | Ordinary new facts, photos, and supplements attach to the current Active Case first; split/merge/archive is decided later by broker/office — never by forcing the customer to manage case boundaries. |
| **Context** | Loop 3.x. Customers cannot safely classify every photo or message as same vs new accident while stressed. |
| **Alternatives Considered** | (1) Prompt “同一事故还是新事故?” on every upload; (2) Discard ambiguous media; (3) Make the customer pick a lane before retention. |
| **Why This Decision** | Retention beats premature classification. Brokers can split with context; customers should not run intake taxonomy. |
| **Constitution Principle** | Append-first, Split-later |
| **Date** | 2026-07-17 |
| **Status** | Active |

---

### D-003 — Today First

| Field | Content |
|-------|---------|
| **Decision** | Surface exactly one Today’s Focus; later items and waiting are not a second agenda for today. |
| **Context** | Loop 3.x (esp. 3.8–3.9). Missing-item lists and equal-weight checklists caused choice overload. |
| **Alternatives Considered** | (1) Full missing checklist as the main UI; (2) VIN-centered default stack; (3) Status chip and Waiting competing with Focus while customer still owes work. |
| **Why This Decision** | One “今天建议” restores motion. Later and Waiting reassure or wait — they must not restate today’s work as optional parallel work. |
| **Constitution Principle** | Today First |
| **Date** | 2026-07-17 |
| **Status** | Active |

---

### D-004 — Why (Loop 4.0)

| Field | Content |
|-------|---------|
| **Decision** | Under Today’s Focus, show one short human “为什么？” that explains why this step matters now — not jargon, not a second recommendation. |
| **Context** | Loop 4.0. Customers completed faster when they understood the reason, without becoming case managers. |
| **Alternatives Considered** | (1) No reason line (Focus + CTA only); (2) Long paragraph restating all missing tasks; (3) System language (“需要完成资料完整度 / OCR”). |
| **Why This Decision** | A single human reason lowers hesitation and supports calm progress without adding a second agenda. |
| **Constitution Principle** | Why |
| **Date** | 2026-07-17 |
| **Status** | Active |

---

### D-005 — After (Loop 4.1)

| Field | Content |
|-------|---------|
| **Decision** | Under Today’s Focus, show one visible “完成后会发生什么？” — exactly one next human consequence, not a process map. |
| **Context** | Loop 4.1. Without a clear next outcome, customers repeated “did it count?” taps and anxiety stayed high after the step. |
| **Alternatives Considered** | (1) No after-line; (2) Multi-step process map (“多级审核、拆分、保险公司流程”); (3) Dual outcomes (“审核或继续补资料”). |
| **Why This Decision** | One concrete next human result (e.g. 陈总开始审核) reduces anxiety and makes the step feel finished. |
| **Constitution Principle** | After |
| **Date** | 2026-07-17 |
| **Status** | Active |

---

### D-006 — One Truth (Loop 4.2)

| Field | Content |
|-------|---------|
| **Decision** | For any moment in the journey, Home, Case Details, Focus, primary CTA, Why, After, and Waiting must answer the same questions the same way — never competing stories. |
| **Context** | Loop 4.2. Mismatched CTA vs Focus, or Waiting vs “今天建议,” made customers doubt whether the product knew what they should do. |
| **Alternatives Considered** | (1) Different shorthand on Home vs Case Details; (2) Generic CTA (“继续案件”) while Focus names a specific upload; (3) Loud Waiting while customer still owes Today. |
| **Why This Decision** | Trust is consistency. One story across surfaces is more important than local clever labels. |
| **Constitution Principle** | One Truth |
| **Date** | 2026-07-17 |
| **Status** | Active |

### D-007 — Golden Production QA is the only production acceptance flow

| Field | Content |
|-------|---------|
| **Decision** | Before every release, Founder demo, and customer pilot, acceptance runs through one permanent Golden Production QA flow: one QA token, one Camry production Case, full customer journey, full broker journey, then GO/NO-GO. Prototypes and mock workbenches are never substitutes. |
| **Context** | P24E/P24E.2 showed Founders mixing Start Claim, prototype Camry seeds, and production token entry — producing false confidence or false failures. Multiple “QA paths” destroyed the release question. |
| **Alternatives Considered** | (1) Keep separate capability scripts as equal acceptance paths; (2) Accept prototype Golden Flow as release evidence; (3) Allow ad-hoc new Cases each demo. |
| **Why This Decision** | One Token → One Case → One Truth is the only way a non-engineer Founder can answer “is this release production-ready?” without Cursor. Capability scripts remain diagnostics; Golden QA is the gate. |
| **Constitution Principle** | One Truth; Capability Done Means User Done (North Star) |
| **Date** | 2026-07-17 |
| **Status** | Active |
| **SSOT** | `docs/product/p24f_golden_production_qa_flow.md` |

### D-008 — Home with active case opens Task Home

| Field | Content |
|-------|---------|
| **Decision** | Capsule / operational Home: active case/token → Task Home (via Entry); no active case → Start Claim. Explicit「开始新报案」clears resume and opens Start Claim. `pages[0]` stays Start Claim for packaging. |
| **Context** | P26A Founder QA: Home with Camry resume cleared the token and stranded customers on「开始报案」, so Task Home was not the operational home. |
| **Alternatives Considered** | (1) Change `pages[0]` to Task Home/Entry (breaks Build Gate / empty-launch packaging); (2) Always Home → Start Claim (fails One Active Case); (3) Multi-case picker (out of Constitution). |
| **Why This Decision** | Keeps packaging gates stable while making Home resume the active case. Start New Claim remains the only intentional new-case reset. |
| **Constitution Principle** | One Active Case; North Star §J |
| **Date** | 2026-07-18 |
| **Status** | Active |
| **SSOT** | `docs/product/p20_product_north_star.md` §J; `miniapp/utils/startClaimEntry.ts` |

### D-009 — Default intake must not require Broker Request More

| Field | Content |
|-------|---------|
| **Decision** | Customer Start Claim creates an active collecting case, issues a signed resume token, and Constitution exposes `system_default` intake tasks immediately. Broker Request More / Send Request is only for exceptional follow-ups (`broker_requested`). |
| **Context** | P26G: normal intake was gated on Slice1 open requests + QR launch tokens; new claims started in `broker_review` so Today collapsed to「先不用操作」. |
| **Alternatives Considered** | (1) Auto-seed Slice1 request rows on create (keeps broker system as plan owner); (2) Hard-coded Mini Program checklist (breaks Constitution SSOT); (3) Keep QR-only access (fails First-Time / Return-Later gates). |
| **Why This Decision** | Default plan lives server-side (`default_intake_plan` → Constitution → Projection → Task Home). Resume uses validated tokens, not bare local `case_id`. Broker follow-ups add without wiping defaults. |
| **Constitution Principle** | One Truth; One Active Case; North Star §J2 |
| **Date** | 2026-07-18 |
| **Status** | Active |
| **SSOT** | `docs/product/p20_product_north_star.md` §J2; `services/fiqa_api/inbox_triage/default_intake_plan.py` |

### D-010 — Claim Vehicle Identity V1 is claim-scoped Request More

| Field | Content |
|-------|---------|
| **Decision** | V1 vehicle identity is one primary slot owned by `case_id`, entered via Broker Request More (plus in-claim supplement/edit), with optional VIN and completeness via VIN **or** year/make/model when VIN is unavailable; `vin` and `vehicle_information` merge into the same object on the existing claim fact path — no WeCom Add Car reopen, no `intake_entities` dual-write, no Start Claim VIN requirement. |
| **Context** | Post-P36 Add Vehicle discovery. Risk of reopening `SERVICE_LANE_ADD_CAR`, inventing a second vehicle workflow, or dual-writing entity memory while Slice1 already collects VIN. |
| **Alternatives Considered** | (1) Reuse WeCom Add Car lane as claim path; (2) Session/`intake_entities` as authoritative vehicle SoT; (3) Multi-vehicle garage under Service Home; (4) Mandatory VIN at Start Claim. |
| **Why This Decision** | Smallest main-chain extension: broker asks only when needed; one slot prevents duplicate identity; claim facts already power Workbench/customer read-after-write. |
| **Constitution Principle** | One Truth; Smallest Working Solution; No Unsupported Choices; Main-Chain First |
| **Date** | 2026-07-21 |
| **Status** | Active |
| **SSOT** | `docs/product/CLAIM_VEHICLE_IDENTITY_V1.md` |

### D-011 — Claim Vehicle vs Add Car naming

| Field | Content |
|-------|---------|
| **Decision** | **Add Car** (`保单加车`) is Policy Management only; **Claim Vehicle** (`事故车辆`) / **Vehicle Information** (`车辆信息`) are Claim only; **Vehicle Identity** is an internal backend object name and must never appear in customer UI; legacy **Add Vehicle** means Add Car, not claim work. |
| **Context** | Claim Vehicle Identity V1 planning reused “Add Vehicle” while WeCom/docs still say Add Car / Add Vehicle for the policy lane — engineers could not tell Policy vs Claim vs storage. |
| **Alternatives Considered** | (1) Keep “Add Vehicle” as umbrella for both; (2) Rename all code symbols immediately; (3) Customer-facing “Vehicle Identity.” |
| **Why This Decision** | Smallest fix is language law: domains stay separate; code renames wait for an explicit cleanup; UI stays non-technical. |
| **Constitution Principle** | Complexity Stays Inside; One Truth; Smallest Working Solution |
| **Date** | 2026-07-21 |
| **Status** | Active |
| **SSOT** | `docs/product/CLAIM_VEHICLE_VS_ADD_CAR_TERMINOLOGY.md` |


### D-016 — Durable MP identity enforces One Active Case

| Field | Content |
|-------|---------|
| **Decision** | Mini Program customer create uses `wx.login` → `/api/h5/customer/session` → opaque `wx_*` person_link → `mp_customer_active_case` resolve/bind. Production rejects anon-only create (`durable_identity_required`). `force_new` is ignored. Prototype `anon-*` create is isolated to non-Production and still index-bound. |
| **Context** | Audit found Start Claim used `anon-*` so server could not guarantee One Active Case after storage clear / new device. |
| **Alternatives Considered** | (1) Keep client-only token guard; (2) Full Customer Account product; (3) Phone-mandatory login before claim. |
| **Why This Decision** | Smallest durable identity that makes Rule 1 a backend invariant without building an account system. |
| **Constitution Principle** | One Active Case |
| **Date** | 2026-07-22 |
| **Status** | Active |
| **SSOT** | `docs/product/p0_one_active_case_identity_foundation.md` |


### D-017 — Broker Close → History (read-only)

| Field | Content |
|-------|---------|
| **Decision** | Broker-only `close_case` stamps terminal History fields, clears Active Case bindings, and rejects all customer mutations with `case_closed_read_only`. Soft archive remains a queue filter only (≠ Close). After Close, same identity may create exactly one new Active Case. Workbench exposes minimal Close Case control; QA seed renamed Create Test Case. |
| **Context** | Workbench status/archive was not true Close; resume tokens could still mutate closed/archived cases; Active binding could linger. |
| **Alternatives Considered** | (1) Treat soft archive as Close; (2) Token revocation registry; (3) Full History product UI. |
| **Why This Decision** | Server-authoritative terminal state + binding cleanup is the smallest Constitution-complete Close without Reopen or History browsing. |
| **Constitution Principle** | One Active Case; Server is final authority |
| **Date** | 2026-07-22 |
| **Status** | Active |
| **SSOT** | `docs/product/p0_broker_close_history_lifecycle.md` |

### D-015 — Founder QA Broker Workbench = QA document-intake

| Field | Content |
|-------|---------|
| **Decision** | Canonical Founder QA Broker Workbench is **document-intake** on the **QA Preview** host (`ui-waterwoods-…`), baked to Cloud QA. Production keeps document-intake on `ui-smoky-beta`. Unified Intake stays the overall web portal — not the Founder QA bookmark. Do not redirect document-intake → unified-intake for this alignment. |
| **Context** | ENVIRONMENT MISMATCH: Golden/phone wrote Cloud QA; Founder opened smoky-beta document-intake (Production API) and could not see today’s QA case. |
| **Alternatives Considered** | (1) Make unified-intake the sole primary and redirect document-intake (prior freeze); (2) Keep dual equal bookmarks; (3) Align document-intake host/API only. |
| **Why This Decision** | Smallest fix: one Founder habit (document-intake) + correct QA host. No UI redesign, no customer change, no T6. |
| **Constitution Principle** | One Truth; Complexity Stays Inside; Capability Done Means User Done |
| **Date** | 2026-07-22 |
| **Status** | Active (QA alignment Commit 1) |
| **SSOT** | `ui/src/config/workbenchEnv.ts`; `scripts/camry_golden_qa.py` `WORKBENCH_QA_URL`; `docs/FOUNDER_QA_PLAYBOOK.md`; `docs/runbooks/CLOUD_QA_RESOURCE_NAMES.md` |

---

## Index

| ID | Decision | Principle | Status |
|----|----------|-----------|--------|
| D-001 | One Active Case (server-enforced) | One Active Case | Active |
| D-016 | Durable MP identity → Active Case | One Active Case | Active |
| D-017 | Broker Close → History (read-only) | One Active Case | Active |
| D-002 | Append-first, Split-later | Append-first, Split-later | Active |
| D-003 | Today First | Today First | Active |
| D-004 | Why (Loop 4.0) | Why | Active |
| D-005 | After (Loop 4.1) | After | Active |
| D-006 | One Truth (Loop 4.2) | One Truth | Active |
| D-007 | Golden Production QA only | One Truth / User Done | Active |
| D-008 | Home → Task Home when active | One Active Case / §J | Active |
| D-009 | Default intake without broker gate | One Truth / §J2 | Active |
| D-010 | Claim Vehicle Identity V1 | One Truth / Smallest Working Solution | Active |
| D-011 | Claim Vehicle vs Add Car naming | Complexity Stays Inside / One Truth | Active |
| D-015 | Founder QA Workbench = QA document-intake | One Truth / User Done | Active |

---

## Document control

| Version | Date | Change |
|---------|------|--------|
| v1 | 2026-07-17 | Template + seed decisions from Loops 3.x–4.2 |
| v1.1 | 2026-07-17 | D-007 Golden Production QA acceptance standard |
| v1.2 | 2026-07-18 | D-008 Home routing with active case |
| v1.3 | 2026-07-18 | D-009 Default intake without broker Request More |
| v1.4 | 2026-07-21 | D-010 Claim Vehicle Identity V1 freeze |
| v1.5 | 2026-07-21 | D-011 Claim Vehicle vs Add Car naming freeze |
| v1.6 | 2026-07-22 | D-015 Founder QA Broker Workbench = QA document-intake |
| v1.7 | 2026-07-22 | D-016 Durable MP identity / One Active Case server enforcement |
| v1.8 | 2026-07-22 | D-017 Broker Close → History (read-only) |

**Change rule:** New Active entries require Founder acknowledgment. Superseding an entry requires a new ID and an explicit Status update on the old entry.
