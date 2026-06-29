# P16 Decision Freeze V1

**Date:** 2026-06-17  
**Sprint:** P16 Decision Freeze  
**Authority:** This document is the **single source of truth** for P16 product scope, architecture, and sprint boundaries.  
**Supersedes for scope/architecture:** Prior P16 roadmaps, tech-option memos, and build plans unless explicitly referenced here.  
**Runtime deployment truth still wins in:** `docs/CURRENT_PRODUCT_SHAPE.md`

**ADR Index (architecture decisions — added 2026-06-20):**

| ADR | Decision | File |
|-----|----------|------|
| ADR-001 | Request Readiness State Model (READY / NEED_INFO / BROKER_REVIEW) | `docs/p16/adr/ADR_001_REQUEST_READINESS.md` |
| ADR-002 | No Timeline UI in V1 (deferred to post-10-case gate) | `docs/p16/adr/ADR_002_NO_TIMELINE_V1.md` |
| ADR-003 | No Carrier API or Quote Automation in V1 | `docs/p16/adr/ADR_003_NO_CARRIER_API_V1.md` |
| ADR-004 | Enterprise WeCom Channel Integration (Channel Adapter #1) | `docs/p16/adr/ADR_004_ENTERPRISE_WECOM_CHANNEL_INTEGRATION.md` |
| ADR-005 | Active Case Consolidation & Evidence Append Model (implementation gated) | `docs/p16/adr/ADR_005_ACTIVE_CASE_CONSOLIDATION.md` |

**Request Framework formal spec:** `docs/p16/P16_REQUEST_FRAMEWORK.md`  
**Customer Flow Blueprint:** `docs/p16/P16_CUSTOMER_FLOW_BLUEPRINT.md`  
**Current build plan:** `docs/p16/P16_4_DAY_BUILD_PLAN.md`

---

**Prerequisite reviews completed:**

| Review | Outcome captured in |
|--------|---------------------|
| Architecture Bakeoff | §5 Architecture Decision Record |
| Customer Input Reality Review | §2 Product North Star, §3 Included |
| Workflow Failure Review | §4 Not Building, §7 Top Risks |
| Commercial Validation Review | §9 Revenue Milestone |
| Zip2 Simplicity Review | §4 Not Building, §6 Trust Layer Sprint Scope |

---

## 1. Executive Summary

**What P16 is**

P16 is the **Customer First Add-Car Intake System** for California auto insurance brokerages. It turns messy customer documents into a **Trusted Packet** that the broker office can act on immediately — without re-reading WeChat threads, re-assembling screenshots, or chasing missing fields.

**Why it exists**

Broker offices spend **~10 minutes per add-car request** hunting through WeChat for VIN photos, dealer PDFs, garaging ZIP, and delivery dates. Wu Xiaojie (office operator) re-reads the same evidence multiple times. Chen Kui (broker) re-asks customers for items already sent. The product exists to collapse that loop.

**Who pays**

The **brokerage / agency** pays — starting with the **Chen Kui pilot** ($49/month manual invoice after trial). The customer and office benefit; the broker signs the check when time savings are proven.

**What problem it solves**

```
Customer Docs  →  Trusted Packet  →  Broker
```

P16 reduces add-car intake work from **~10 minutes to ~2–3 minutes** by:

1. Letting the customer upload evidence once (PDF, JPG, PNG, HEIC)
2. Extracting structured fields with Gemini Flash 2.5
3. Delivering a broker-trusted packet with copy-ready fields, VIN validation, and source attribution

This is **not** a CRM, policy system, or WeChat replacement. It is a **trust layer** between customer evidence and broker action.

---

## 2. Product North Star

**Frozen flow:**

```
Customer Docs  ↓  Trusted Packet  ↓  Broker
```

**Current goal:**

Reduce add-car intake work from **~10 minutes** to **~2–3 minutes**.

**Success definition:** Office receives a packet they can quote from without opening WeChat. Broker can copy fields into AMS or carrier portals in one action. Every extracted field traces to a source file.

**Timing targets (aligned to north star):**

| Role | Target |
|------|--------|
| Customer | Upload + minimal identity (< 3 min) |
| System | Extract + assemble packet (< 60 sec) |
| Broker / office | Review + copy fields (< 1 min) |

---

## 3. What We Are Building

### Included

| Area | Scope |
|------|-------|
| **Customer intake** | Name, Phone, Garaging ZIP |
| **Upload** | PDF, JPG, PNG, HEIC |
| **Extraction** | Gemini Flash 2.5 vision extraction |
| **Trusted Packet** | Structured add-car packet for broker/office |
| **Copy Fields** | One-click copy of packet fields for AMS/carrier entry |
| **VIN validation** | Format check + mismatch warning |
| **Source attribution** | Every field links to originating upload |
| **Basic packet review** | Broker sees packet, missing items, warnings — not raw chat |
| **Mobile support** | Customer upload flow works on phone browsers |

**Field contract reference:** `docs/product_constitution/P16_ADD_CAR_PACKET_FIELD_CONTRACT.md` (required fields only for V0; optional fields deferred).

**Upload flow reference:** `docs/product_constitution/P16_UPLOAD_FIRST_CUSTOMER_FLOW.md`

---

## 4. What We Are NOT Building

These are explicitly frozen out of P16 V0 and Trust Layer Sprint:

| Area | Rationale |
|------|-----------|
| **CRM** | Not our wedge; broker keeps existing tools |
| **Policy management** | Out of scope per paid pilot goal |
| **Claims** | Different workflow; no pilot demand |
| **Renewals** | Future vertical; not add-car |
| **Document AI** (Google Document AI) | Deferred — Gemini Flash sufficient for V0 |
| **PDF generation** | Broker copies fields; no PDF export |
| **Customer accounts** | No login; phone + link identity only |
| **Authentication system** | API keys for broker perimeter only |
| **Multi-broker platform** | Single pilot; no tenant isolation |
| **WeChat native integration** | Paste/link only; no bot or sync |
| **Complex trade-in workflow** | One vehicle per request; trade-in VIN flagged not automated |
| **Customer confirmation workflow** | No TurboTax-style confirm screen; broker reviews packet |
| **Screenshot crop attribution** | Full-file source only for V0 |

---

## 5. Architecture Decision Record

### Frontend

| Decision | Choice | Notes |
|----------|--------|-------|
| Framework | **React 18** | Existing `ui/` codebase |
| Component library | **Ant Design 5** | Already in `ui/package.json`; do not migrate |
| Validation | **Zod** | Schema validation for intake + packet |
| State | **Zustand** | Lightweight client state |

### Backend

| Decision | Choice | Notes |
|----------|--------|-------|
| API | **FastAPI** | `services/fiqa_api/` |
| Database | **Postgres** | Durable cases; PG-primary for paid pilot |
| Compute | **Cloud Run** | Production backend |
| Object storage | **GCS** | Uploaded evidence files |
| Extraction | **Gemini Flash 2.5** | Vision extraction; replaces OpenAI default for cost |

### Deployment

| Layer | Target |
|-------|--------|
| Frontend | **Vercel** |
| Backend | **Cloud Run** |
| Storage | **GCS** |

**Rejected alternatives (frozen):** shadcn/ui migration, Supabase Storage, Document AI, UploadThing, Temporal/Camunda workflow engine.

**Reference:** `docs/CURRENT_PRODUCT_SHAPE.md` for env flags and pilot requirements.

---

## 6. Trust Layer Sprint Scope

**Only these six capabilities. Nothing else.**

| # | Capability | Definition |
|---|------------|------------|
| 1 | **Upload** | Customer uploads PDF/JPG/PNG/HEIC to GCS via presigned flow |
| 2 | **Extraction** | Gemini Flash 2.5 extracts structured fields from uploads |
| 3 | **Packet** | System assembles Trusted Packet from extracted + intake fields |
| 4 | **Copy Fields** | Broker copies packet fields to clipboard |
| 5 | **VIN Validation** | VIN format check; warn on invalid or conflicting VIN |
| 6 | **Source Attribution** | Each field shows which file it came from |

**Out of Trust Layer Sprint:** Customer confirmation UI, trade-in automation, WeChat, PDF export, status visibility polish, append/chat triage improvements, demo tab work.

---

## 7. Top Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **HEIC** | iPhone photos fail upload or extract | HEIC in allowed MIME list; test iPhone camera roll |
| **Wrong VIN** | Office quotes wrong vehicle | VIN validation + source attribution; broker review |
| **Trade-in VIN** | Two VINs in one upload set | Flag conflict; one vehicle per request |
| **Wrong ZIP** | Garaging misquote | Require garaging ZIP on intake; cross-check extraction |
| **Missing lienholder** | Incomplete finance info | Optional field; flag in packet missing items |
| **Broker trust** | Chen Kui abandons after bad first case | Source attribution + no silent guessing |
| **Pilot adoption** | No ROI proof after 3 cases | Time savings tracker; 10-case gate before invoice |

---

## 8. Acceptance Criteria

**P16 V0 passes if:**

| # | Criterion | Pass condition |
|---|-----------|----------------|
| 1 | Upload works | Customer uploads ≥1 file (PDF or image); file stored in GCS |
| 2 | Extraction works | Gemini returns ≥1 structured field from upload |
| 3 | Packet generated | Trusted Packet visible to broker with required fields |
| 4 | Copy Fields works | Broker copies field block to clipboard |
| 5 | Source file shown | Each extracted field links to source upload |
| 6 | VIN warning shown | Invalid or conflicting VIN displays visible warning |

---

## 9. Revenue Milestone

**First milestone chain:**

```
Chen Kui Pilot  →  10 Real Cases  →  Average ≥4 min saved  →  First $49 payment
```

| Gate | Metric |
|------|--------|
| Pilot start | Chen Kui uses product on real add-car cases |
| Case gate | 10 cases logged (CK-001 … CK-010) |
| ROI gate | Average ≥4 minutes saved per case vs manual |
| Payment gate | First $49 manual invoice (Zelle/Venmo/WeChat) |

**Tracker:** `docs/trial/P16_TIME_SAVINGS_TRACKER.md`  
**Dashboard:** `docs/trial/P16_REAL_PILOT_DASHBOARD.md`

---

## 10. Frozen Decisions

### Frozen For P16

| Decision | Status |
|----------|--------|
| Ant Design 5 | **Frozen** — no UI library migration |
| Gemini Flash 2.5 | **Frozen** — primary extraction provider |
| GCS | **Frozen** — evidence storage |
| Trusted Packet | **Frozen** — product deliverable name |
| Copy Fields | **Frozen** — broker copy-to-clipboard UX |
| Source Attribution | **Frozen** — field → file traceability |
| VIN Validation | **Frozen** — format + conflict warnings |

### Deferred To Later

| Item | Earliest reconsider |
|------|---------------------|
| Document AI | Post–Trust Layer, if Gemini accuracy insufficient |
| PDF generation | Post-payment, if broker requests |
| Trade-in automation | Post–10-case pilot |
| Customer confirmation | Post–Trust Layer; broker review sufficient for V0 |
| WeChat integrations | Post-payment; not pilot scope |
| Advanced workflow engine | Never for paid pilot wedge |

---

## Document Hierarchy (post-freeze)

| Priority | Document | Role |
|----------|----------|------|
| 1 | **This file** | Scope + architecture freeze |
| 2 | `docs/CURRENT_PRODUCT_SHAPE.md` | Runtime + deploy truth |
| 3 | `docs/product_constitution/P16_ADD_CAR_PACKET_FIELD_CONTRACT.md` | Field definitions |
| 4 | `docs/trial/INDEX.md` | Pilot operations |
| 5 | `docs/goals/insurance_paid_pilot_goal.md` | Commercial scope |

---

---

## 11. Pilot Demo Execution Plan

**Status as of 2026-06-18:** PILOT_DECISION = GO

**Remaining P0 items before first Chen Kui case:**

| # | Item | Status |
|---|------|--------|
| 1 | HEIC real iPhone validation (end-to-end with live extraction API) | Open |
| 2 | Screen 4 Trusted Packet above-fold hierarchy | Open |

**Remaining P1 items:**

| # | Item | Status |
|---|------|--------|
| 3 | Garaging ZIP label audit (UI must say "Garaging ZIP") | Open |
| 4 | Copy All format verification (clean paste into AMS/clipboard) | Open |

**Execution documents:**

| Doc | Purpose |
|-----|---------|
| `docs/p16/P16_72_HOUR_BUILD_PLAN.md` | Day-by-day tasks, acceptance criteria, stop criteria |
| `docs/p16/P16_PILOT_GO_LIVE_CHECKLIST.md` | Pre-launch checklist — all boxes must be checked before Go |
| `docs/p16/P16_CHEN_KUI_3_CASE_SOFT_PILOT.md` | Case-by-case pilot instructions for Chen Kui and Wu Xiaojie |

**Revenue chain reminder (§9):** Chen Kui Pilot → 10 Real Cases → Average ≥4 min saved → First $49 payment.

---

---

## 12. Pilot Demo Readiness

**Added:** 2026-06-18 (P16 Polish Sprint audit)  
**Source:** Full 5-screen Add-Car flow audit — `docs/p16/P16_PILOT_UI_REVIEW.md`, `docs/p16/P16_PILOT_DEMO_BLUEPRINT_V2.md`

---

### PILOT_DEMO_SCORE: 6.2 / 10

| Screen | Avg Score |
|--------|-----------|
| Screen 1 — Entry Gate (CustomerFirstEntryScreen) | 7.5 / 10 |
| Screen 2 — Customer Info (InfoStep) | 6.25 / 10 |
| Screen 3 — Upload (UploadStep) | 5.75 / 10 |
| Screen 4 — Extracting (ExtractingStep) | 5.5 / 10 |
| Screen 5 — Trusted Packet (PacketStep) | 5.75 / 10 |
| **Overall** | **6.2 / 10** |

The product is functionally correct. The trust and professionalism gaps are specific and fixable in < 2 hours.

---

### TOP_10_FINDINGS

| # | Finding | Screen | Priority |
|---|---------|--------|----------|
| 1 | `model_used` technical tag visible on Trusted Packet header | 5 | P0 |
| 2 | Mock mode orange banner fires if Gemini key absent — destroys demo trust | 5 | P0 |
| 3 | Source attribution hidden behind "Show details" toggle (Decision Freeze §3 violation) | 5 | P0 |
| 4 | Warnings render AFTER vehicle fields — wrong order per 72-hour build plan | 5 | P0 |
| 5 | Screen 4 loading state is a bare Ant Design spinner — looks like a crash | 4 | P1 |
| 6 | "Customer Information" title is broker-voice on customer-facing Screen 2 | 2 | P1 |
| 7 | InboxOutlined (email icon) on file upload dragger sends wrong signal | 3 | P1 |
| 8 | "Read Documents" CTA is backend-developer language | 3 | P1 |
| 9 | No case ID or timestamp displayed on Trusted Packet | 5 | P1 |
| 10 | Customer name + garaging ZIP not visible above fold on Trusted Packet | 5 | P1 |

---

### TOP_10_UI_FIXES

| # | Fix | File | Est. Time |
|---|-----|------|-----------|
| UI-01 | Remove `model_used` Tag from PacketStep header | `ui/src/pages/AddCarPage.tsx` | 5 min |
| UI-02 | Add `from: [source_file]` inline with VIN and vehicle fields | `ui/src/pages/AddCarPage.tsx` | 20 min |
| UI-03 | Reorder PacketStep: warnings before vehicle fields | `ui/src/pages/AddCarPage.tsx` | 10 min |
| UI-04 | Guard mock mode Alert behind dev-only check | `ui/src/pages/AddCarPage.tsx` | 5 min |
| UI-05 | Add timestamp to Trusted Packet header | `ui/src/pages/AddCarPage.tsx` | 10 min |
| UI-06 | Change "Customer Information" → "Your Information" | `ui/src/pages/AddCarPage.tsx` | 2 min |
| UI-07 | Replace InboxOutlined with CloudUploadOutlined on Dragger | `ui/src/pages/AddCarPage.tsx` | 5 min |
| UI-08 | Change "Read Documents" CTA → "Continue →" | `ui/src/pages/AddCarPage.tsx` | 2 min |
| UI-09 | Add animated loading steps to ExtractingStep | `ui/src/pages/AddCarPage.tsx` | 30 min |
| UI-10 | Add customer name + garaging ZIP to PacketStep above-fold | `ui/src/pages/AddCarPage.tsx` | 15 min |

**Total estimated time for UI-01 through UI-10: ~1 hr 44 min**

---

### TOP_5_TRUST_IMPROVEMENTS

| # | Improvement | Why It Matters for Chen Kui Pilot |
|---|------------|----------------------------------|
| T1 | Source attribution visible by default on VIN | Wu Xiaojie must see "from: purchase_agreement.pdf" without clicking anything — it's the proof the data is real |
| T2 | Warnings before vehicle fields | If a VIN warning exists, broker must see it before they see the VIN value — current order hides the warning below the data |
| T3 | Remove model_used tag | "gemini-1.5-flash" on the Trusted Packet header is confusing to non-technical brokers and makes the product feel like a prototype |
| T4 | Guard mock mode | If Gemini key is not set and the orange "MOCK extraction only" banner fires during the pilot, Chen Kui will not trust any data in the packet |
| T5 | Case ID + timestamp | "Trusted Packet — Jun 18, 2026, 2:51 PM" makes the product feel like a record, not a live prototype — crucial for broker adoption |

---

### TOP_5_BROKER_REACTIONS (predicted)

Based on the current flow state, if Wu Xiaojie sees the product today:

| # | Reaction | Trigger | Impact |
|---|---------|---------|--------|
| B1 | "What is gemini-1.5-flash?" | `model_used` tag on packet header | Confusion; erodes professionalism |
| B2 | "Where does the VIN come from?" | Source file not visible above fold | Broker must scroll or click to verify — friction on key trust step |
| B3 | "It's loading forever — did it crash?" | Bare spinner on Screen 4 for 20–30 seconds | Abandonment risk on first use |
| B4 | "This feels like a demo, not a real product" | No case ID, no timestamp, no brokerage branding | Pilot adoption risk |
| B5 | "Actually this is great — I don't have to read WeChat" | The copy-paste-into-AMS result after clicking Copy All | This is the money moment — make sure it's reached |

---

### GO_OR_NO_GO

**Status as of 2026-06-18: CONDITIONAL GO**

Required before first Chen Kui case:
- [ ] UI-01: Remove `model_used` tag (5 min)
- [ ] UI-02: Source attribution inline on VIN/vehicle (20 min)
- [ ] UI-03: Reorder warnings before vehicle fields (10 min)
- [ ] UI-04: Guard mock mode banner (5 min)

If these four fixes are deployed: **GO**  
If any one is missed: **NO-GO** on professionalism grounds (T1, T3) or trust grounds (T2, T4)

---

### NEXT_48_HOURS_PLAN

**Today (Jun 18) — Hours 1–4:**
1. Apply UI-01 through UI-04 (the 4 P0 trust fixes) — ~40 min combined
2. Apply UI-05 through UI-10 (P1 polish) — ~60 min combined
3. Run full end-to-end flow: info → upload 3 files → extract → packet → copy → paste into Google Docs
4. Confirm: no mock banner, source attribution visible, warnings before fields, clean copy text
5. Verify: HEIC upload from real iPhone (P16_72_HOUR_BUILD_PLAN.md task 1.1)

**Tomorrow (Jun 19) — Hours 5–24:**
1. Run `trial_launch_check.sh` clean
2. Run `demo_quick_validate.sh` clean
3. Dry-run CK-001 case with real documents
4. Send intake URL to Chen Kui with walkthrough doc
5. Log dry-run in `docs/trial/P16_TIME_SAVINGS_TRACKER.md` as CK-DRY-01

**Detailed docs:**
- Build plan: `docs/p16/P16_72_HOUR_BUILD_PLAN.md`
- UI fixes: `docs/p16/P16_PILOT_DEMO_BLUEPRINT_V2.md` Part 7
- Pilot instructions: `docs/p16/P16_CHEN_KUI_3_CASE_SOFT_PILOT.md`

---

---

---

## 13. PILOT_LAUNCH_STATUS

**Added:** 2026-06-18 (P16 Pilot Launch Sprint)  
**Source:** P16 Pilot Launch Sprint execution — Tasks 1–6

---

### LAUNCH_CHECK_STATUS: PASS

`bash scripts/trial_launch_check.sh` — **PASS** as of 2026-06-18.

**Blocker fixed during this sprint:**  
`case_store.py`: `append_follow_up_message` was not transitioning `lifecycle_status` from `handed_off` → `office_followup` when a follow-up was appended to an already-handed-off case. Fixed in commit `971bb86`. All 200+ guardrail tests pass.

---

### QA ENVIRONMENT

| Layer | URL | Status |
|-------|-----|--------|
| **Frontend (Vercel QA)** | `https://ui-gd6bzzx9v-andys-projects-1f411b73.vercel.app/add-car` | ✅ Live |
| **Backend (Cloud Run)** | `https://fiqa-api-1013093472160.us-west1.run.app` | ✅ Live |
| **Extraction endpoint** | `/api/intake/add-car/extract` | ✅ Registered and live |

`/add-car` route: HTTP 200 ✅

---

### CK_DRY_01_RESULT: PASS

**Dry Run:** Andy Li / 2011 BMW X5  
**Date:** 2026-06-18  
**Documents:** insurance_card.png + smog_check_vir.png  
**Backend:** `https://fiqa-api-g7zatxrycq-uw.a.run.app` (post-deploy Cloud Run)  
**Elapsed:** 14 seconds

| Field | Value | Source | Confidence |
|-------|-------|--------|-----------|
| VIN | `5UXZV4C56BL402905` | insurance_card.png | high |
| Year | 2011 | insurance_card.png | high |
| Make | BMW | smog_check_vir.png | high |
| Model | X5 XDRIVE35I | smog_check_vir.png | high |
| Effective Date | 2026-03-23 | insurance_card.png | high |
| Garaging ZIP | 91101 | intake_form | high |
| Customer | Andy Li | intake_form | high |
| Primary Driver | MISSING | — | — |
| Lienholder | MISSING | — | optional |

**Warnings:** Conflicting delivery_or_effective_date values across documents — expected (insurance card date ≠ smog test date). Broker should verify.

**Mock mode:** false (real extraction via GPT-4o)

**Copy Packet output:**
```
ADD-CAR PACKET

Customer:
  Name: Andy Li
  Phone: 6265550000
  Garaging ZIP: 91101

Vehicle:
  VIN: 5UXZV4C56BL402905
  Year: 2011
  Make: BMW
  Model: X5 XDRIVE35I

Driver:
  Primary Driver: MISSING

Dates:
  Effective Date: 2026-03-23

Finance:
  Lienholder: MISSING

Warnings:
  ⚠ Conflicting delivery_or_effective_date values detected across documents — verify manually

Sources:
  intake_form → customer_name, phone, garaging_zip
  insurance_card.png → vin, year, effective_date
  smog_check_vir.png → make, model
```

---

### PILOT_LAUNCH_SCORE

| Check | Status |
|-------|--------|
| `trial_launch_check.sh` PASS | ✅ |
| QA Frontend URL live (`/add-car` = 200) | ✅ |
| QA Backend URL live (`/health/live` = 200) | ✅ |
| `/api/intake/add-car/extract` endpoint registered | ✅ |
| Dry run CK-DRY-01 PASS | ✅ |
| VIN extracted correctly | ✅ |
| Copy Packet clean | ✅ |
| Mock mode banner suppressed in Vercel deploy | ✅ |
| `P16_ANDY_WALKTHROUGH.md` created | ✅ |
| `P16_FIRST_BROKER_TEST_PLAN.md` created | ✅ |

**PILOT_LAUNCH_SCORE: 10/10 checks passed**

---

### GO_OR_NO_GO

**Status as of 2026-06-18 (post-sprint): GO**

All P0 trust fixes from §12 TOP_10_UI_FIXES are now live:
- ✅ UI-01: `model_used` tag not shown on PacketStep (field exists in API response but not rendered in UI)
- ✅ UI-02: Source attribution inline (`from: insurance_card.png`) shown by default next to VIN
- ✅ UI-03: Warnings displayed BEFORE vehicle fields
- ✅ UI-04: Mock mode banner guarded behind `import.meta.env.DEV` — does NOT fire on Vercel production/preview builds

**Remaining P1 (not blocking):**
- UI-05 through UI-10 are nice-to-have polish; packet is functional and trustworthy

**Ready for:** Wu Xiaojie first broker test  
**Test plan:** `docs/p16/P16_FIRST_BROKER_TEST_PLAN.md`

---

### PRIMARY_DRIVER_FIX — 2026-06-19

**Status:** DEPLOYED — revision `fiqa-api-00096-d2v`, GIT_SHA `aec2e0ee3`

**Problem:** Insurance cards and smog reports do not list a primary driver. QA showed red `Missing: Primary Driver` for every real-document case.

**Rule implemented:** If `primary_driver` is absent after extraction but `customer_name` is present:
- `primary_driver.value = customer_name`
- `primary_driver.source_file = "default_from_customer_name"`
- `primary_driver.needs_confirmation = true`
- Soft notice: "Primary driver defaulted to customer name — please confirm / 默认使用客户姓名，请确认"
- NO red missing alert

**UI:** Yellow "Needs confirmation" tag + bilingual soft prompt shown above-fold in Trusted Packet.

**Copy Packet:** `Primary Driver: nanxin li (defaulted from customer name — confirm)`

**Verified live:** All 5 assertions pass against `https://fiqa-api-g7zatxrycq-uw.a.run.app`.

---

### NEXT_ACTION

1. Andy runs `P16_ANDY_WALKTHROUGH.md` personally (all 5 screens, real documents)
2. Use QA URL: `https://ui-smoky-beta.vercel.app/add-car`
3. Send QA URL to Wu Xiaojie with `P16_FIRST_BROKER_TEST_PLAN.md`
4. Log Wu Xiaojie results in `docs/trial/P16_TIME_SAVINGS_TRACKER.md`
5. After Wu Xiaojie confirms GO: send URL to Chen Kui for first real add-car case (CK-001)
6. Gate to invoice: 10 real cases, average ≥4 min saved

---

---

---

## 14. Timeline V1 Direction

**Added:** 2026-06-19 (P16 Timeline + Case State Machine Design Review)  
**Source:** `docs/p16/P16_TIMELINE_STATE_MACHINE_DESIGN.md`  
**Status:** DESIGN APPROVED — pending GO/NO-GO for implementation

---

### Direction

The Add-Car Trusted Packet will gain a lightweight case timeline. This is the smallest useful layer on top of the existing packet flow — not a CRM.

**Hierarchy:**

```
Customer (phone identity)
  └── Case (one per upload session)
        ├── Vehicle (extracted VIN + year + make + model)
        └── Timeline Events (ordered log)
```

**Timeline events written automatically (no human action):**

`CASE_CREATED` → `DOCUMENT_UPLOADED` → `AI_EXTRACTED_PACKET` → `VIN_VALIDATED` → `PRIMARY_DRIVER_DEFAULTED` (if applicable) → `MISSING_ITEM_DETECTED` (if applicable) → `VIN_CONFLICT_FLAGGED` (if applicable) → `PACKET_READY`

**Case states (mapped to existing `lifecycle_status`):**

`NEW` → `DOCS_UPLOADED` → `PACKET_BUILT` → `READY_FOR_QUOTE` (or `MISSING_ITEMS`)

**Key implementation decisions:**

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Timeline storage (V1 MVP) | `case_activity` JSONB in `service_records.extra` | No schema change; reuses existing persistence path |
| Timeline storage (V2, before 10-case gate) | New `p16_timeline_events` Postgres table | Proper relational log, queryable by event type |
| `case_id` from extract endpoint | Wire `save_case()` call in `add_car.py` | Currently missing — packet exists but no case is persisted |
| Conflict rule | Different VIN = new case; never auto-merge | Protects broker from silent wrong-VIN packets |
| Timeline UI | Ant Design `<Timeline>` inside PacketStep `<Collapse>` | Collapsed by default; doesn't clutter primary broker view |

**What this is NOT:**

- Not a full case management system
- Not a CRM
- Not a customer dashboard
- Not a broker workflow engine
- Not a policy or quote system

**Reference:** `docs/p16/P16_TIMELINE_STATE_MACHINE_DESIGN.md` for full design.

---

*End of P16 Decision Freeze V1*
