# P16 Technical Architecture Summary

**Date:** 2026-06-21  
**Audience:** Andy, Cursor agents, future technical collaborators  
**Authority:** `P16_DECISION_FREEZE_V1.md` · `CURRENT_PRODUCT_SHAPE.md` · runtime code in `ui/` and `services/fiqa_api/`  
**Related:** `P16_STRATEGIC_RETROSPECTIVE_MONTH1.md` (product pivot context)

---

## 1. Executive Summary

P16 is a **document-first add-car intake system** for California auto insurance brokerages. The current architecture turns uploaded customer evidence (PDF, JPG, PNG, HEIC) into a **Trusted Packet** — structured fields with source attribution that the broker office can copy into carrier portals.

**Stack at a glance:**

| Layer | Technology |
|-------|------------|
| Frontend | React 18 · TypeScript · Ant Design 5 · Vite · Vercel |
| Backend | Python · FastAPI · Cloud Run |
| Database | Postgres (`service_records`) |
| AI extraction | Vision LLM (Gemini / OpenAI) + PyMuPDF PDF text-layer VIN |
| Primary route | `POST /api/intake/add-car/extract` |

**Why this architecture is stronger than Month 1's chat-first version:**

- Input matches real customer behavior (dealer paperwork, not typed chat)
- Every field traces to a source file (liability + broker trust)
- Extraction produces copy-ready structured data, not conversation summaries
- Cases persist in Postgres with `service_lane = add_car` and a durable `case_id`
- Readiness states (READY / NEED_INFO / BROKER_REVIEW) are derived from document evidence, not slot-filling guesses

The legacy conversation path (`POST /api/inbox/triage`) still exists for broker paste and multi-turn collecting. It is **not** the primary P16 product surface anymore.

---

## 2. Frontend Architecture

### React + TypeScript

- **Location:** `ui/src/`
- **Framework:** React 18 (`react`, `react-dom`)
- **Language:** TypeScript 5.x
- **Routing:** `react-router-dom` — P16 customer surface at **`/add-car`**
- **Primary page:** `ui/src/pages/AddCarPage.tsx`

### Ant Design

- **Library:** Ant Design 5 (`antd` + `@ant-design/icons`)
- Used for wizard steps, forms, upload dragger, cards, tags, alerts, copy buttons
- No shadcn/ui migration (frozen per Decision Freeze)

### Vite

- **Bundler/dev server:** Vite 7 (`ui/vite.config.ts`)
- Local dev: port **5173**, proxies API calls to backend on **8001**
- Production build enforces `VITE_API_BASE_URL` pointing to HTTPS Cloud Run (no localhost on Vercel)

### Vercel

- Frontend deploys to **Vercel** (Preview + Production)
- **Stable QA URL:** `https://ui-smoky-beta.vercel.app`
- Build-time API target: `VITE_API_BASE_URL` → Cloud Run backend
- Customer entry: `https://ui-smoky-beta.vercel.app/add-car`

### TurboTax-style guided intake

`AddCarPage.tsx` implements a **step-by-step wizard** (P16 Customer Flow Blueprint):

| Step | Screen | Purpose |
|------|--------|---------|
| 0 | Intent | Add vehicle vs replace vehicle |
| 1 | Basic Info | Name · Phone · Garaging ZIP |
| 2 | Upload | PDF / JPG / PNG / HEIC (max 10 files) |
| 3 | Reading | Extraction progress animation |
| 4 | Sent to Broker | Customer-facing completion |
| 5 | Trusted Packet | Broker-facing packet + Copy All |

**Client state:** React `useState` + Ant Design Form. **Zod** available for schema validation. **Zustand** in stack for lightweight shared state elsewhere in the app.

**Readiness UI:** Frontend computes `ready | needs_info | broker_review` from packet fields, VIN validation, warnings, and `document_guidance` (ADR-001 aligned).

### Legacy conversation UI (still present)

- `ui/src/features/intake/components/CustomerEntryTab.tsx` — broker/customer paste + multi-turn chat collecting
- Lives under Unified Intake workbench (`/workbench/unified-intake`)
- Maintained for broker paste path; **not** the Month 1 document-first primary surface

---

## 3. Backend Architecture

### Python + FastAPI

- **Location:** `services/fiqa_api/`
- **App entry:** `services/fiqa_api/app_main.py`
- **API style:** REST, JSON responses, multipart file upload for extraction

### API routes (P16-relevant)

| Route | File | Purpose |
|-------|------|---------|
| `POST /api/intake/add-car/extract` | `routes/add_car.py` | **Primary P16 endpoint** — upload docs, extract packet, persist case |
| `GET /api/inbox/customer/active-case` | `routes/inbox_triage.py` | Phone lookup — return active add-car case |
| `POST /api/inbox/customer/start-add-car` | `routes/inbox_triage.py` | Create draft add-car case (conversation path) |
| `POST /api/inbox/triage` | `routes/inbox_triage.py` | Legacy conversation triage (broker paste) |
| `GET /healthz`, `GET /readyz` | `health/ready.py` | Liveness / readiness probes |

Router registration in `app_main.py`:

```text
app.include_router(inbox_triage_router)   # /api/inbox/*
app.include_router(add_car_router)        # /api/intake/add-car/*
```

Paid pilot runs with `UNIFIED_INTAKE_PRODUCT_ONLY=1` — platform/lab routers hidden.

### Cloud Run

- **Production backend:** Google Cloud Run
- **Current QA API:** `https://fiqa-api-1013093472160.us-west1.run.app`
- **Deploy entry:** `bash scripts/deploy_paid_pilot.sh`
- **Local dev:** `bash scripts/run_demo_local.sh` → port **8001**

### Add Vehicle extraction endpoint

**`POST /api/intake/add-car/extract`** (`routes/add_car.py`)

**Request** (multipart/form-data):

| Field | Required | Notes |
|-------|----------|-------|
| `files` | Optional (≥1 for real extraction) | PDF, JPG, JPEG, PNG, HEIC — max 10 |
| `customer_name` | Yes | |
| `phone` | Yes | US phone |
| `garaging_zip` | Yes | Collected before upload (fraud exposure control) |
| `request_type` | No | `add_vehicle` (default) or `replace_vehicle` |

**Response:**

```json
{
  "packet": { "vin": { "value": "...", "source_file": "...", "confidence": 0.9 }, ... },
  "warnings": ["..."],
  "sources": [{ "file": "...", "fields": "..." }],
  "copy_text": "...",
  "mock_mode": false,
  "model_used": "gpt-4o",
  "case_id": "case_2443b8598545",
  "document_guidance": "..."
}
```

**Flow inside the handler:**

1. Validate form fields and file types
2. Write uploads to a temp directory
3. Run vision extraction per file (`ocr_kill_test/extractor.py`)
4. Merge fields across files (`ocr_kill_test/packet_builder.py`)
5. Apply PDF text-layer VIN preference when applicable
6. Run NHTSA VIN checksum validation
7. Assess document relevance → `document_guidance` for NEED_INFO
8. Build `copy_text` for clipboard
9. Persist case via `save_case()` → return `case_id`

**Mock mode:** Local dev only when no API key. Production/QA returns 422 if extraction unavailable — never fakes OCR in prod.

---

## 4. AI / OCR Pipeline

**Modules:** `services/fiqa_api/ocr_kill_test/`

```
extractor.py      → per-file vision extraction (OpenAI / Gemini)
packet_builder.py → merge multi-file results, conflicts, readiness
schema.py         → field contract (VIN, YMM, ZIP, etc.)
normalizers.py    → field normalization rules
```

### PDF upload

- Accepted: `.pdf`
- **Two-path extraction:**
  1. **PDF text layer** (PyMuPDF / `fitz`) — preferred for native-text dealer PDFs
  2. **Vision OCR** — fallback for scanned/image-only PDFs

### Image / HEIC upload

- Accepted: `.jpg`, `.jpeg`, `.png`, `.heic`
- HEIC converted to JPEG via **pillow-heif** before sending to vision API
- iPhone camera-roll photos are a first-class upload type

### Vision model extraction

- **Providers:** OpenAI (`gpt-4o`) or Google Gemini (`gemini-2.0-flash` / Flash 2.5 family)
- **Selection:** `P16_OCR_PROVIDER` env or `get_extractor("auto")` — prefers Gemini when key present, falls back to OpenAI
- **Prompt:** Structured JSON schema — 8 core fields, document type, conflict detection, insurance-card rules
- **Rule:** Never invent values; empty string when field not visible

### PyMuPDF PDF text-layer VIN extraction

`try_pdf_text_layer_vin()` in `extractor.py`:

- Opens PDF with PyMuPDF (`import fitz`)
- Reads embedded text layer (not rendered image)
- Regex-scans for structurally valid 17-char VIN (`A-HJ-NPR-Z0-9`, no I/O/Q)
- Returns empty string if no text layer or no valid VIN

### PDF text first, Vision fallback

`_apply_pdf_text_vin_preference()`:

```text
For each PDF file:
  1. try_pdf_text_layer_vin(path)
  2. If valid 17-char VIN found → override Vision OCR VIN
  3. Else → keep Vision result (or empty)
```

**Why this matters:** Vision OCR on purchase-agreement PDFs was systematically truncating VINs (16 chars, first-char drop). PDF text layer fixes this on native-text dealer contracts. Deployed Jun 21 (`fiqa-api-00102-fbp`); regression test: **4/4 PDF VIN exact match**.

### Post-extraction validation

- **NHTSA VIN checksum** in `routes/add_car.py` (`validate_vin()`)
- **Multi-file conflict detection** — conflicting VINs → BROKER_REVIEW
- **Document relevance gate** — no vehicle fields extracted → NEED_INFO + bilingual `document_guidance`
- **Insurance card rules** — do not treat agent address as garaging ZIP

---

## 5. Data Persistence

### Postgres

- **Authority:** `SERVICE_RECORD_DATABASE_URL` (or `DATABASE_URL`)
- **Table:** `service_records` (via `db/service_record_repository.py`)
- **Paid pilot flags:** `UNIFIED_INTAKE_DB_PRIMARY_READS=1`, `UNIFIED_INTAKE_DB_PRIMARY_WRITES=1`
- JSON case files are legacy/dev-only; forbidden in prod

### `save_case()`

- **Location:** `services/fiqa_api/inbox_triage/case_store.py`
- Called from `_persist_add_car_case()` after successful extraction
- Writes durable case record with triage result shape:

```text
collected_fields / still_needed_fields
customer_phone / customer_name
primary_vehicle_summary
vehicle_key (VIN)
lifecycle_status
case_messages (starter message)
```

Non-blocking on failure — extraction response still returns even if persist fails (logged).

### Case ID

- Format: `case_{12-char-hex}` (e.g. `case_2443b8598545`)
- Generated in `save_case()` via `uuid4().hex[:12]`
- Returned in extraction response → customer/broker can reference case

### `service_lane = add_car`

- Constant: `SERVICE_LANE_ADD_CAR = "add_car"` (`intake_service_lanes.py`)
- Passed to `save_case(service_lane=SERVICE_LANE_ADD_CAR)`
- Used by workbench queue filtering, phone lookup, and office routing
- Distinguishes add-car cases from general inbox triage cases

### Phone return key (conversation path integration)

- `GET /api/inbox/customer/active-case?phone=...` finds active add-car draft by normalized phone
- Same Postgres backing; document-first and conversation paths share case store

### File storage note

Decision Freeze targets **GCS** for uploaded evidence. **Current V0 implementation** processes files in a **request-scoped temp directory** — files are not yet persisted to object storage after extraction. Packet fields and source filenames are stored; raw file bytes are not retained post-request.

---

## 6. Core Product Model

### Document-first intake

```text
Customer uploads evidence
  → System extracts structured fields
  → Readiness evaluated
  → Trusted Packet delivered
  → Case persisted in Postgres
```

Customer does not type VIN. Customer does not chat through a slot-filling bot on the primary `/add-car` path.

### READY / NEED_INFO / BROKER_REVIEW

Frozen in ADR-001 (`docs/p16/adr/ADR_001_REQUEST_READINESS.md`):

| State | Meaning | Trigger |
|-------|---------|---------|
| **READY** | Broker can act now | VIN + YMM + ZIP present, no blocking conflicts |
| **NEED_INFO** | Customer must provide more | Critical field missing, or wrong/unrelated documents |
| **BROKER_REVIEW** | Human judgment required | VIN conflict, checksum warning, ambiguous extraction |

Derived on backend (warnings, missing fields) and mirrored on frontend (`computeReadinessStatus()` in `AddCarPage.tsx`).

### Trusted Packet

Structured broker-facing output:

- VIN · Year · Make/Model · Garaging ZIP · Customer · Phone
- Per-field **source attribution** (`source_file: pa_007_hyundai_elantra.pdf`)
- Warnings section (VIN issues, conflicts, trade-in flags)
- Missing optional fields (lienholder, delivery date)
- Primary driver default with confirmation notice

### Auto Follow-Up

When readiness = NEED_INFO, the API returns **`document_guidance`** — bilingual text telling the customer what to upload next. Frontend renders this as a copy-ready WeChat message on the Sent / Packet screens.

Example pattern: *"We couldn't find vehicle information. Please upload purchase agreement, registration, or VIN photo."*

Not yet a separate generated follow-up endpoint — guidance is produced inline by `_assess_document_relevance()` in `add_car.py`.

### Copy Packet

- Backend builds `copy_text` — plain-text block formatted for AMS/carrier portal paste
- Frontend **Copy All** button (`CopyOutlined`) copies `copy_text` to clipboard
- This is the **money moment**: VIN in clipboard → paste into Mercury/Progressive without re-typing

---

## 7. Deployment Model

### Vercel frontend

| Environment | URL | Notes |
|-------------|-----|-------|
| Stable QA | `https://ui-smoky-beta.vercel.app` | Primary P16 validation surface |
| Customer path | `/add-car` | Shareable intake link |
| Env var | `VITE_API_BASE_URL` | Must be HTTPS Cloud Run URL |

### Cloud Run backend

| Environment | URL | Notes |
|-------------|-----|-------|
| QA / paid pilot | `https://fiqa-api-1013093472160.us-west1.run.app` | Current stable revision |
| Health | `/health/live`, `/readyz` | Deploy gate |
| Product mode | `UNIFIED_INTAKE_PRODUCT_ONLY=1` | Hides lab routers |

### Stable QA URL

Used for real-world validation (`P16_REAL_WORLD_VALIDATION_REPORT.md`, `P16_DEPLOY_VALIDATION_REPORT.md`). Backend and frontend are independently deployable; backend-only fixes (e.g. PDF VIN) do not require frontend redeploy when API contract is unchanged.

### CORS

- Configured in `app_main.py` via `CORSMiddleware`
- Production: `ALLOWED_ORIGINS` or `CORS_ORIGINS` env — includes Vercel preview/production origins
- Validated: `ui-smoky-beta.vercel.app` → Cloud Run returns `access-control-allow-origin` ✅
- Local dev: `ALLOW_ALL_CORS=1` or Vite proxy (no cross-origin)

### Local development

```bash
bash scripts/run_demo_local.sh          # API on :8001
cd ui && npm run dev                    # UI on :5173, proxies to :8001
```

---

## 8. What Improved From Month 1

| Area | Chat-first (early June) | Document-first (late June) |
|------|-------------------------|----------------------------|
| **Primary input** | Pasted WeChat text, customer typing | Uploaded PDF / JPG / PNG / HEIC |
| **Core engine** | `triage.py` conversation slot-filling | `ocr_kill_test/` vision + PDF text extraction |
| **Customer UI** | `CustomerEntryTab` message turns | `AddCarPage` TurboTax wizard at `/add-car` |
| **Output** | Collected / Still Needed from chat | Trusted Packet with source attribution |
| **Validation gate** | 33/33 conversation simulation | 22-doc OCR corpus + 5-set real-world validation |
| **Broker action** | Read triage summary | Copy Packet → paste into carrier portal |
| **Case persistence** | Conversation turns often HTTP-only | `save_case()` on every extraction → Postgres `case_id` |
| **Readiness** | Handoff gates in triage policy | READY / NEED_INFO / BROKER_REVIEW from document evidence |
| **VIN accuracy** | Parsed from chat (unreliable) | PDF text layer + vision + NHTSA checksum |
| **UI polish** | Workbench-centric, prototype tags | Stage-gate headers, bilingual guidance, broker packet hierarchy |

**Net effect:** P16 went from a **demo tool that understood chat** to a **persisted case product that reads documents**.

---

## 9. Current Remaining Gaps

| Gap | Status | Notes |
|-----|--------|-------|
| **Real broker cases** | Open | CK-001–CK-010 pilot not yet logged; simulation ≠ production proof |
| **READY on all dealer PDFs** | Partial | PDF text-layer fix works on checksum-valid docs; synthetic demo PDFs may still fail |
| **Broker workbench for packet cases** | Later | Unified Intake workbench exists; document-first packet view integration is not the primary office surface yet |
| **Timeline UI** | Deferred | ADR-002 — post 10-case gate |
| **GCS file retention** | Deferred | Files processed in temp dir; evidence not stored post-request |
| **Auto Follow-Up as standalone feature** | Partial | `document_guidance` inline; full bilingual WeChat template generator (N1) not shipped |
| **SMS** | Later | Phone is return key; no SMS verification or notifications |
| **Gemini as production default** | Partial | Decision Freeze targets Gemini Flash 2.5; QA validation ran on `gpt-4o` when Gemini quota exhausted |
| **Carrier API / quoting** | Out of scope | ADR-003 — P16 ends at Trusted Packet |

---

## 10. One-Page Architecture Diagram

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CUSTOMER (mobile browser)                          │
│                                                                             │
│   https://ui-smoky-beta.vercel.app/add-car                                  │
│                                                                             │
│   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌─────────┐ │
│   │ Intent   │ → │ Basic    │ → │ Upload   │ → │ Reading  │ → │ Sent /  │ │
│   │ Selector │   │ Info     │   │ Docs     │   │ (wait)   │   │ Packet  │ │
│   └──────────┘   └──────────┘   └──────────┘   └──────────┘   └─────────┘ │
│                                         │                                   │
│                    React 18 + TypeScript + Ant Design 5 + Vite              │
└─────────────────────────────────────────┼───────────────────────────────────┘
                                          │ HTTPS (CORS)
                                          │ POST /api/intake/add-car/extract
                                          │ multipart: files + name + phone + zip
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CLOUD RUN — FastAPI (Python)                         │
│                  fiqa-api-*.us-west1.run.app  (:8001 local)               │
│                                                                             │
│   routes/add_car.py                                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ 1. Validate uploads (PDF/JPG/PNG/HEIC, max 10)                      │   │
│   │ 2. Temp file store                                                  │   │
│   │ 3. ocr_kill_test/extractor.py                                       │   │
│   │      ├─ PDF? → PyMuPDF text-layer VIN first                         │   │
│   │      └─ else → Vision LLM (Gemini / OpenAI gpt-4o)                  │   │
│   │ 4. packet_builder.py → merge fields, detect conflicts               │   │
│   │ 5. validate_vin() → NHTSA checksum                                  │   │
│   │ 6. document_guidance → NEED_INFO message                          │   │
│   │ 7. save_case(service_lane="add_car") → Postgres                     │   │
│   │ 8. Return packet + warnings + copy_text + case_id                   │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│   Legacy (still mounted): POST /api/inbox/triage  (conversation path)       │
│                           GET  /api/inbox/customer/active-case  (phone)     │
└─────────────────────────────────────────┼───────────────────────────────────┘
                                          │
                    ┌─────────────────────┴─────────────────────┐
                    ▼                                           ▼
┌──────────────────────────────┐              ┌──────────────────────────────┐
│         POSTGRES            │              │     VISION API (external)     │
│   service_records table     │              │  Gemini Flash 2.5 / gpt-4o   │
│                             │              │  Structured JSON extraction   │
│   case_id: case_abc123      │              └──────────────────────────────┘
│   service_lane: add_car     │
│   customer_phone / name     │
│   collected_fields          │
│   still_needed_fields       │
│   lifecycle_status          │
└──────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BROKER / OFFICE (Wu Xiaojie)                              │
│                                                                             │
│   Trusted Packet on screen                                                  │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ READY FOR BROKER  |  NEED_INFO  |  BROKER_REVIEW                    │   │
│   │                                                                     │   │
│   │ VIN: KMHD84LF8KU123456   (from: pa_007_hyundai_elantra.pdf)        │   │
│   │ Year/Make/Model: 2019 Hyundai Elantra                               │   │
│   │ Garaging ZIP: 91101                                                │   │
│   │                                                                     │   │
│   │ [ Copy All ]  →  paste into AMS / carrier portal                   │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘


DATA FLOW (one line):

  Docs → Extract → Readiness → Packet → Postgres → Copy → Carrier Portal
```

---

## Key File Index

| Concern | Path |
|---------|------|
| Customer wizard UI | `ui/src/pages/AddCarPage.tsx` |
| Extraction endpoint | `services/fiqa_api/routes/add_car.py` |
| Vision + PDF text extraction | `services/fiqa_api/ocr_kill_test/extractor.py` |
| Packet merge + readiness | `services/fiqa_api/ocr_kill_test/packet_builder.py` |
| Case persistence | `services/fiqa_api/inbox_triage/case_store.py` |
| Service lane constant | `services/fiqa_api/inbox_triage/intake_service_lanes.py` |
| Conversation triage (legacy) | `services/fiqa_api/inbox_triage/triage.py` |
| App + CORS + router mount | `services/fiqa_api/app_main.py` |
| Product scope freeze | `docs/p16/P16_DECISION_FREEZE_V1.md` |
| Readiness ADR | `docs/p16/adr/ADR_001_REQUEST_READINESS.md` |
| Month 1 pivot retrospective | `docs/p16/P16_STRATEGIC_RETROSPECTIVE_MONTH1.md` |

---

*End of P16 Technical Architecture Summary*
