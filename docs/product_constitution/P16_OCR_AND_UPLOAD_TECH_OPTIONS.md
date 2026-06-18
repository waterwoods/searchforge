# P16 OCR, Upload, and Tech Stack Options

**Date:** 2026-06-17  
**Sprint:** P16 Add-Car Packet Builder — Product Definition Sprint  
**Scope:** Upload architecture, OCR/Vision options, frontend component libraries, storage options

---

## 1. Frontend Component Libraries

### shadcn/ui

**Verdict: Use as primary UI library**

- Composable, unstyled-first component primitives built on Radix UI
- Tailwind-native: no extra CSS framework
- Easy to copy-paste individual components into the codebase
- No peer dependency hell
- Components: Input, Form, Button, Badge, Progress, RadioGroup, Checkbox — all needed for P16
- Used by most modern SaaS starters (Vercel templates, T3 Stack)

**Use for:** All form fields, buttons, status badges, confirmation UI, packet display

---

### Tailwind CSS

**Verdict: Use for all layout and styling**

- Already likely in the project (check existing UI code)
- Zero runtime overhead
- Responsive layout trivial: `flex`, `grid`, `sm:`, `md:` breakpoints
- Mobile-first compatible
- No design system conflict with shadcn/ui

**Use for:** Layout, spacing, responsive breakpoints, color overrides

---

### Radix UI

**Verdict: Use via shadcn/ui (indirect)**

- shadcn/ui already wraps Radix primitives
- Do not install Radix directly alongside shadcn/ui — redundant
- Get Dialog, Popover, RadioGroup, Tooltip from shadcn/ui wrappers

---

### Ant Design

**Verdict: Skip for MVP**

- Heavy bundle (~1MB)
- Opinionated Chinese-style design (not bad, but conflicts with SaaS-modern target)
- Hard to customize without CSS overrides
- Over-engineered for a 5-screen upload flow

---

### UploadThing

**Verdict: Consider as backend-for-frontend, not required for MVP**

- SaaS upload service (tRPC-based, Next.js-native)
- Handles presigned URLs, storage, and file routing
- Adds a vendor dependency
- Overkill if using Supabase Storage or GCS directly

---

### React Dropzone

**Verdict: Use for file upload UI**

- 1.3MB installed, minimal
- Handles drag-and-drop, file input, MIME type filtering, max files
- Headless — no UI opinions; plug your own styles
- Used by Expensify, Notion, and dozens of SaaS apps
- 3-year maintenance record; actively maintained

```tsx
// Minimal implementation sketch (not production code)
import { useDropzone } from 'react-dropzone';

const { getRootProps, getInputProps, acceptedFiles } = useDropzone({
  accept: { 'image/*': [], 'application/pdf': [] },
  maxFiles: 5,
  maxSize: 10 * 1024 * 1024, // 10MB
});
```

**Use for:** All file upload UI on Screen 2

---

### FilePond

**Verdict: Skip**

- Beautiful but heavy (jQuery-like plugin pattern)
- Requires FilePond server adapter
- Overbuilds the upload step — we need simple drop zone, not full upload manager

---

### Uppy

**Verdict: Consider for v2 (not MVP)**

- Full-featured file upload library with webcam, Google Drive, Dropbox integrations
- 100KB+ bundle
- Best for complex multi-source upload scenarios
- Overkill for MVP upload screen

---

## 2. OCR / Vision Options

### MVP Goal

> Fastest path to working VIN + year/make/model + garaging ZIP extraction from dealer PDFs and VIN photos.

---

### OpenAI GPT-4o Vision

**Verdict: MVP primary choice**

| Dimension | Score |
|-----------|-------|
| MVP path (speed to working) | ★★★★★ |
| Accuracy on car insurance docs | ★★★★☆ |
| PDF handling | Via convert to images (1 extra step) |
| Image handling | Native JPEG, PNG, WEBP, HEIC |
| Cost | ~$0.003/image (GPT-4o input) |
| Implementation time | 1 day |
| Risk | Rate limits at high volume |

**Why MVP:**
- Already integrated in the codebase (OpenAI client exists)
- Structured JSON extraction via function calling / response_format
- Handles VIN photos, dealer PDFs (after PDF→image convert), insurance cards
- Prompt engineering is fast to iterate

**Implementation approach:**
```
PDF → pdf2image (Python: poppler) → images → GPT-4o Vision
JPG/PNG → GPT-4o Vision directly
```

**Sample prompt (reference only):**
```
You are extracting insurance-relevant fields from a car document image.
Extract the following fields if present: VIN, year, make, model, 
garaging_zip, delivery_date, current_insurer, policy_number, lienholder.
Return JSON. For each field, provide: value, confidence (0-1), 
source_region description.
If a field is not found, set value to null and confidence to 0.
```

---

### Gemini Vision (1.5 Pro / 2.0 Flash)

**Verdict: MVP alternative**

| Dimension | Score |
|-----------|-------|
| MVP path | ★★★★★ |
| Accuracy on car insurance docs | ★★★★☆ |
| PDF handling | Native PDF support (no convert needed) |
| Image handling | Native |
| Cost | ~$0.0025/image (Flash); $0.007/image (Pro) |
| Implementation time | 1 day |
| Risk | Google API stability, response format variability |

**Why consider:**
- Native PDF ingestion (no poppler required) → simpler pipeline
- 2.0 Flash is cheaper than GPT-4o for high volume
- Strong structured extraction via system instructions

**Why not primary:**
- Less battle-tested in this codebase
- Slightly less predictable JSON output formatting

---

### Google Document AI (Form Parser / Specialized Processors)

**Verdict: Enterprise tier — not for MVP**

| Dimension | Score |
|-----------|-------|
| MVP path | ★★★☆☆ |
| Accuracy on structured forms | ★★★★★ |
| PDF handling | Native, best-in-class |
| Image handling | Native |
| Cost | $1.50/1,000 pages (Form Parser) |
| Implementation time | 2–3 days |

**Why enterprise:**
- Best accuracy for structured insurance forms, but slower to set up
- Requires Google Cloud project, processor creation, IAM setup
- No custom field prompting (uses pretrained processors)
- Worth switching to at 500+ requests/month for accuracy gains

---

### Azure Document Intelligence (Form Recognizer)

**Verdict: Enterprise tier alternative**

| Dimension | Score |
|-----------|-------|
| MVP path | ★★★☆☆ |
| Accuracy | ★★★★★ |
| PDF handling | Native |
| Image handling | Native |
| Cost | $1.50/1,000 pages |
| Implementation time | 2–3 days |

**When to use:** If team is already on Azure infrastructure. Comparable to Google Doc AI in capability.

---

### AWS Textract

**Verdict: Skip for MVP**

| Dimension | Score |
|-----------|-------|
| MVP path | ★★☆☆☆ |
| Accuracy | ★★★★☆ |
| Setup complexity | High (IAM roles, region config) |
| Cost | $1.50/1,000 pages |
| Implementation time | 3–4 days |

**Why skip:** No clear advantage over Google Doc AI; more AWS config overhead; hardest to iterate on prompt/schema.

---

### Recommended Stack

**MVP (now):**
- OpenAI GPT-4o Vision
- PDF conversion: `pdf2image` (Python, uses poppler)
- Structured output: OpenAI `response_format = json_schema`

**Future enterprise (at 500+ requests/month):**
- Google Document AI (Form Parser) for PDFs
- GPT-4o Vision fallback for handwritten or unusual images

---

## 3. File Upload Architecture

### Recommended: Supabase Storage

**Verdict: MVP primary choice**

```
Frontend (React)
    ↓ presigned URL request
Backend (FastAPI / Cloud Run)
    ↓ generate presigned PUT URL
    ↓
Supabase Storage Bucket (private)
    ↓
Backend receives upload notification
    ↓
OCR / extraction pipeline
    ↓
Structured JSON → Postgres (existing)
    ↓
Packet generation
```

**Why Supabase Storage:**
- Project likely uses Supabase for Postgres — same account, no new billing
- Private buckets by default (no public raw file URLs)
- Presigned URL support
- 1 GB free tier; ~$0.021/GB after
- SDK available for Python and TypeScript

**Alternative: Google Cloud Storage**
- Use if the project is already on Google Cloud Run
- Same architecture; presigned URL support
- Slightly more GCP IAM config

**Alternative: AWS S3**
- Standard choice but adds AWS dependency if not already in use
- More complex IAM + bucket policy setup

**Skip: Direct backend upload**
- Upload passes through backend memory and disk
- Not scalable; creates memory pressure on Cloud Run
- Forces file size limits at the API layer

---

## 4. Security Notes

| Concern | Rule |
|---------|------|
| File size | Max 10 MB per file, enforced at both frontend and backend |
| Max files | Max 5 files per request, enforced at frontend and backend |
| Allowed types | PDF, JPG, JPEG, PNG, HEIC, WEBP only — reject everything else |
| Public URLs | No public raw file URLs — all access via presigned URLs with expiry |
| URL expiry | Presigned download URLs: 1 hour expiry for office access |
| Deletion | Files deleted after 90 days OR after case closed, whichever first |
| Retention for compliance | Keep extraction JSON for 1 year (not raw files) |
| No PII in filenames | Rename files to UUID on upload; preserve original name in metadata only |
| Virus scanning | Nice-to-have for v2; not required for MVP (trust + size limit sufficient) |
| Request isolation | Each request ID has its own storage path: `/{request_id}/{uuid}.{ext}` |

---

## 5. Extraction Pipeline Architecture

```
[File Upload Complete]
        ↓
[Backend: Retrieve from Storage]
        ↓
[If PDF → convert to images (pdf2image + poppler)]
        ↓
[For each page/image → GPT-4o Vision API call]
        ↓
[Per-page extraction results → merge across pages]
        ↓
[Conflict detection: same field, different values]
        ↓
[Missing field detection: required fields not found]
        ↓
[Second vehicle detection: multiple VINs/year+make combos]
        ↓
[Confidence scoring: per-field confidence threshold]
        ↓
[Extraction JSON → stored in Postgres (extracted_facts table)]
        ↓
[Frontend polls extraction status → Screen 3 progress]
        ↓
[Extraction complete → redirect to Screen 4 confirmation]
```

**Extraction timeout:** 60 seconds max per request. If exceeded, show error and allow retry.

**Retry logic:** On OCR failure, retry once with fallback (lower resolution, single-page). On second failure, flag file as unreadable.

---

## 6. Frontend Tech Summary

| Decision | Choice | Reason |
|----------|--------|--------|
| Component library | shadcn/ui | Modern, composable, Tailwind-native |
| Styling | Tailwind CSS | Responsive, zero runtime |
| File upload | React Dropzone | Lightweight, headless, drop-in |
| Form state | React Hook Form (with Zod) | Validation + type-safety |
| State management | React useState / context | Simple 5-screen flow; no Redux needed |
| API calls | fetch / axios | Keep it simple |

---

*End of P16 OCR and Upload Tech Options*
