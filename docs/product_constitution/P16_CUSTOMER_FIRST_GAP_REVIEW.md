# P16 Customer First Gap Review

**Sprint:** P16-CUSTOMER-FIRST-CONSTITUTION-P0  
**Date:** 2026-06-07  
**Scope:** Audit docs and code assumptions vs Customer First constitution  
**Action:** Document only — no code changes in this sprint

**Constitution reference:** `P16_CUSTOMER_FIRST_CONSTITUTION.md`

**Rules audited:**

- Customer Never Logs In
- Phone Is The Return Key
- One Customer = One Active Case
- Phone Required For Formal Submit

---

## Summary

| Category | Count | Severity |
|----------|-------|----------|
| Aligned | 12 | — |
| Conflicting | 9 | 4 P0 · 5 P1 |
| Unclear | 6 | Needs spec in Phase 1–3 impl |
| Future implementation requirements | 11 | Phased per roadmap |

**Overall:** Constitution is directionally correct but **not yet enforced** in runtime. Largest gaps: phone-as-return-key, phone gate on formal submit, and master-outline “many records per person” vs one active case.

---

## Aligned Items

| # | Area | Evidence | Rule(s) |
|---|------|----------|---------|
| A1 | Anonymous customer start | `UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` §3.2 — “Anonymous start — no login required” | Customer Never Logs In |
| A2 | No customer password / SSO product | Paid pilot uses API keys for broker perimeter, not customer auth (`CURRENT_PRODUCT_SHAPE.md`) | Customer Never Logs In |
| A3 | Missing-field progress model | `still_needed_fields`, `collected_fields` in triage + workbench glance | Progress = Missing Fields |
| A4 | Office missing checklist | Z11 office value surface — `still_needed`, waiting pill (`P16Z18_CAPACITY_MODEL.md` Cap 6) | Progress = Missing Fields |
| A5 | Broker workbench confirmation | Broker confirms draft before office execution; no auto-send to carriers (`OPERATOR_SURFACE.md`) | Broker Confirms Identity |
| A6 | Broker-controlled terminal states | Workbench lifecycle actions; no customer “close case” button in product_only UI | Only Broker Closes Or Reopens |
| A7 | Add-car flagship path | Product definition and Chen Kui pilot scoped to add-car (`P16_CHEN_KUI_PILOT_PLAN.md`, master outline §2) | Customer First mission |
| A8 | Active case choice gate (partial) | `CustomerEntryTab.tsx` — continue vs new add-car prompt (`517f728` active case choice gate) | One Active Case (UX seed) |
| A9 | My Requests progress panel | Customer sees submitted cases with progress fields (`MyRequestsTab.tsx`, Cap 1 evidence) | Progress = Missing Fields |
| A10 | WeChat binding optional | `light_identity.show_optional_binding` — skippable; copy says不影响正式提交 | Customer Never Logs In |
| A11 | Constitution anti-goals | `ROADMAP_FROM_CONSTITUTION.md` — CRM, OAuth, WeChat sync locked out | Scope guard |
| A12 | Broker paste still valid | Broker workbench paste path unchanged; customer path additive | Dual entry, broker control |

---

## Conflicting Items

| # | Area | Conflict | Constitution rule | Severity |
|---|------|----------|-------------------|----------|
| C1 | **Return path = session_id, not phone** | `CustomerEntryTab.tsx` restores via `getSessionId()` + `GET /api/inbox/session/{id}`; `clearSessionId()` on formal submit | Phone Is The Return Key | **P0** |
| C2 | **Phone not required for formal submit** | `case_draft_engine.py` — “VIN/name/phone do not block case_usable”; formal submit can reach `handoff_pending` without phone | Phone Required For Formal Submit | **P0** |
| C3 | **Contact-only defer path** | `contactOnlyFormal` in `CustomerEntryTab.tsx` — when only name/phone missing, primary action is chat not formal queue; can delay phone | Phone Required For Formal Submit | **P0** |
| C4 | **Master outline: many records per person** | `UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` §3.2 — “One person may have multiple service records” / append-by-matter | One Customer = One Active Case | **P0** (doc) |
| C5 | **90-day roadmap rejected customer-first** | `P16Z25_90_DAY_ROADMAP.md` — “Customer-first before broker retention proven” under explicit rejects | Customer First direction | **P1** (doc) |
| C6 | **WeChat OAuth code present** | `CustomerEntryTab.tsx` — WeChat binding modal, OAuth redirect, simulate complete | Customer Never Logs In (optional OK; prominence conflicts) | **P1** |
| C7 | **Post-submit customer rehydrate broken** | `P16Z18_CAPACITY_MODEL.md` Cap 1 — post-submit refresh empty; My Requests → Customer Entry missing `case_id` | Phone Is The Return Key + Progress | **P1** |
| C8 | **Person-link extension points** | Master outline §3.2 — `person_link_source`: wechat_bind, phone_hash | Phone Return Key not wired to lookup API | **P1** |
| C9 | **Duplicate-case UX** | `P16Z25_30_DAY_ROADMAP.md` M15 “Duplicate-case UX fix” — implies duplicates occur | One Active Case | **P1** |

---

## Unclear Items

| # | Question | Why unclear | Resolution owner |
|---|----------|-------------|------------------|
| U1 | Phone normalization rules | US 10-digit vs +1 vs WeChat pasted formats | Phase 3 impl spec |
| U2 | “Valid phone” definition | Minimum digits? area code required? | Phase 3 impl spec |
| U3 | Active case definition | Which `lifecycle_status` values count as “active”? | Phase 2 lookup spec |
| U4 | New vehicle while case open | Customer mentions second car mid-intake — fork or block? | Broker confirm + Rule 7 spec |
| U5 | “When will someone contact me?” | No SLA field or broker promise copy standard | Copy pack + broker SOP |
| U6 | Postgres pilot data vs phone lookup | Stale demo cases may share phones | Phase 4 cleanup criteria |

---

## Future Implementation Requirements

Phased per `Customer First Phase Order` (roadmap docs). Not in scope for P0 doc sprint.

| # | Requirement | Phase | Depends on |
|---|-------------|-------|------------|
| F1 | Customer first screen — name + phone entry on open | 1 | Constitution |
| F2 | Phone lookup API — return active case by normalized phone | 2 | F1, Postgres |
| F3 | Formal submit gate — reject/block without valid phone | 3 | F1, engine + UI |
| F4 | Customer return UI — phone prompt replaces session-only restore | 2 | F2 |
| F5 | Enforce one active add-car case per phone (server-side) | 2–3 | F2, lifecycle rules |
| F6 | Deprecate session-only return for multi-day continuity | 2 | F4 |
| F7 | Update master outline §3.2 merge policy for add-car wedge | 0 | This constitution |
| F8 | Broker identity confirmation affordance (claimed vs confirmed) | 5+ | Workbench copy |
| F9 | Customer status copy for contact timing | 1–2 | ui_copy.json |
| F10 | Postgres pilot data cleanup — dedupe phones, close stale actives | 4 | F5 rules frozen |
| F11 | Chen Kui pilot re-run on customer-first URL | 5 | F1–F4 minimum |

**Explicitly out of scope (do not implement from gap list):**

- SMS OTP
- WeChat OAuth required path
- WeChat bot
- OCR
- Multi-case customer picker
- CRM
- Payment integration

---

## Code Touchpoints (for future sprints — do not change in P0)

| File / module | Current behavior | Target behavior |
|---------------|------------------|-----------------|
| `ui/.../CustomerEntryTab.tsx` | session restore; optional WeChat; contact-only formal | Phone-first entry + lookup |
| `ui/.../caseLifecycleDisplay.ts` | `handoff_pending` without phone check | Phone required before formal |
| `services/fiqa_api/inbox_triage/case_draft_engine.py` | phone not in case_usable gate | phone in formal submit gate |
| `services/fiqa_api/inbox_triage/case_store.py` | stores `customer_phone` when extracted | enforce on formal submit |
| `services/fiqa_api/routes/inbox_triage.py` | session APIs | phone lookup endpoint |
| `services/fiqa_api/db/service_record_repository.py` | case queries by id | active case by phone query |
| `configs/*ui_copy*` | light_identity WeChat hints | phone return key copy |

---

## Doc Touchpoints Updated in P0

| Document | Change |
|----------|--------|
| `P16_CUSTOMER_FIRST_CONSTITUTION.md` | Created — new SSOT |
| `P16Z25_NORTH_STAR.md` | Customer First north star added |
| `UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` | Customer First section + add-car active-case note |
| `P16Z18_CAPACITY_MODEL.md` | Customer First interpretation per capacity |
| `P16Z25_90_DAY_ROADMAP.md` | Customer First phase order |
| `P16Z25_30_DAY_ROADMAP.md` | Customer First phase order |
| `ROADMAP_FROM_CONSTITUTION.md` | Customer First phase order |
| `OPERATOR_SURFACE.md` | Pointer to constitution |

---

## Recommended Resolution Order

1. **Constitution frozen** (this sprint) ✅  
2. **Customer first screen** — collect phone early (Phase 1)  
3. **Phone lookup** — server returns single active case (Phase 2)  
4. **Formal submit gate** — phone required (Phase 3)  
5. **Postgres cleanup** — after rules frozen, before Chen Kui re-pilot (Phase 4)  
6. **Chen Kui pilot** — customer-first URL path (Phase 5)

---

*End of P16 Customer First Gap Review*
