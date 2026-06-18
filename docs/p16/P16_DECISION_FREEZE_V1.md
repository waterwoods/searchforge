# P16 Decision Freeze V1

**Date:** 2026-06-17  
**Sprint:** P16 Decision Freeze  
**Authority:** This document is the **single source of truth** for P16 product scope, architecture, and sprint boundaries.  
**Supersedes for scope/architecture:** Prior P16 roadmaps, tech-option memos, and build plans unless explicitly referenced here.  
**Runtime deployment truth still wins in:** `docs/CURRENT_PRODUCT_SHAPE.md`

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

*End of P16 Decision Freeze V1*
