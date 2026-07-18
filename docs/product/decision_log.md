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
| **Decision** | A customer has at most one Active Case in progress; reopen continues that case; starting another accident is an explicit secondary choice with confirm. |
| **Context** | Loop 3.x (esp. 3.8–3.9). Case pickers and “which matter am I in?” destroyed trust after an accident. Continuity is the product. |
| **Alternatives Considered** | (1) Multi-case home list like a claims portal; (2) Silent second case on return; (3) Always ask “new or existing?” before any continue. |
| **Why This Decision** | Under stress, one clear matter restores motion. Secondary + confirm keeps a real new accident possible without making case management the default job. |
| **Constitution Principle** | One Active Case |
| **Date** | 2026-07-17 |
| **Status** | Active |

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

---

## Index

| ID | Decision | Principle | Status |
|----|----------|-----------|--------|
| D-001 | One Active Case | One Active Case | Active |
| D-002 | Append-first, Split-later | Append-first, Split-later | Active |
| D-003 | Today First | Today First | Active |
| D-004 | Why (Loop 4.0) | Why | Active |
| D-005 | After (Loop 4.1) | After | Active |
| D-006 | One Truth (Loop 4.2) | One Truth | Active |
| D-007 | Golden Production QA only | One Truth / User Done | Active |
| D-008 | Home → Task Home when active | One Active Case / §J | Active |
| D-009 | Default intake without broker gate | One Truth / §J2 | Active |

---

## Document control

| Version | Date | Change |
|---------|------|--------|
| v1 | 2026-07-17 | Template + seed decisions from Loops 3.x–4.2 |
| v1.1 | 2026-07-17 | D-007 Golden Production QA acceptance standard |
| v1.2 | 2026-07-18 | D-008 Home routing with active case |
| v1.3 | 2026-07-18 | D-009 Default intake without broker Request More |

**Change rule:** New Active entries require Founder acknowledgment. Superseding an entry requires a new ID and an explicit Status update on the old entry.
