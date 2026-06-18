# P16 Add-Car Packet Builder — 14-Day Build Plan

**Date:** 2026-06-17  
**Sprint:** P16 Add-Car Packet Builder — Product Definition Sprint  
**Build start:** Day 1 after this document is reviewed and approved  
**Authority:** Implement against `P16_ADD_CAR_PACKET_BUILDER_MASTER_SPEC.md` and `P16_ADD_CAR_PACKET_FIELD_CONTRACT.md`

---

## One-Line Goal

> In 14 days, build a working Upload-first Add-Car Packet Builder that passes the 10-case kill test and gets a GO from Chen Kui and Wu Xiaojie.

---

## What This Plan Does NOT Include

Do not build any of the following during this 14-day plan:

- CRM integration
- WeChat bot
- Stripe / payment flow
- Renewal, claim, remove-car flows
- Multi-tenant auth
- Cross-device customer identity
- Second office onboarding
- Voice agent
- Push notifications or email
- GraphRAG
- Full workflow engine
- Temporal / Camunda state machine
- Anything not on the explicit task list below

---

## WEEK 1 — Build Foundation (Days 1–7)

### Day 1–2: Master Spec Lock + Upload UI Scaffold

**Owner:** Product + Frontend

**Tasks:**
1. Review and sign off on `P16_ADD_CAR_PACKET_BUILDER_MASTER_SPEC.md` (this sprint output)
2. Lock field contract: `P16_ADD_CAR_PACKET_FIELD_CONTRACT.md`
3. Create Screen 1 (phone + name entry) — shadcn/ui Input, Form, Button
4. Create Screen 2 (upload zone) — React Dropzone integration
5. File type filtering: accept PDF, JPG, PNG, HEIC, WEBP only
6. File size enforcement: max 10 MB per file, max 5 files
7. Per-file upload status: uploading → ready → error
8. "What can I upload?" collapsible guide (Chinese + English)

**Deliverable:** Screens 1 + 2 working in local dev, no backend needed yet.

---

### Day 3: File Storage Wiring

**Owner:** Backend + Frontend

**Tasks:**
1. Confirm storage choice: Supabase Storage or GCS (check existing project infra)
2. Create private bucket: `p16-add-car-evidence`
3. Backend endpoint: `POST /api/v1/requests` → create request_id, return presigned upload URL
4. Frontend: upload files to presigned URL (direct to storage, not through backend memory)
5. Storage path convention: `/{request_id}/{uuid}.{original_ext}`
6. Backend: file metadata stored in Postgres (`request_files` table)
7. File type re-validation at backend (don't trust frontend)

**Deliverable:** Files upload successfully from Screen 2 to cloud storage, metadata stored in DB.

---

### Day 4: OCR Prototype

**Owner:** AI + Backend

**Tasks:**
1. Install `pdf2image` + poppler on backend (for PDF → image conversion)
2. Backend endpoint: `POST /api/v1/requests/{request_id}/extract` (async job trigger)
3. First extraction pass: GPT-4o Vision on dealer_contract.pdf test file
4. Define extraction prompt (see `P16_OCR_AND_UPLOAD_TECH_OPTIONS.md` sample)
5. Parse response into `ExtractionResult` JSON schema (see `P16_ADD_CAR_PACKET_FIELD_CONTRACT.md`)
6. Validate: VIN, year, make/model extracted correctly from test file
7. Log extraction result to console; no UI needed yet

**Deliverable:** OCR works on at least one real dealer PDF in local test.

---

### Day 5: Extraction Schema + Pipeline

**Owner:** AI + Backend

**Tasks:**
1. Multi-file extraction: run vision on each file/page, merge results
2. Conflict detection: same field, different values across sources
3. Missing field detection: required fields not found → `missing_required_fields[]`
4. Confidence scoring: per-field confidence threshold at 0.80
5. Second vehicle detection: multiple distinct VIN references → flag
6. Unrelated file detection: no vehicle fields found → flag
7. Store extraction result in Postgres (`extractions` table, linked to `request_id`)
8. Async job: extraction status = `pending` → `complete` / `failed`
9. Polling endpoint: `GET /api/v1/requests/{request_id}/extraction-status`

**Deliverable:** Extraction pipeline working end-to-end, results stored in DB.

---

### Day 6–7: Confirmation Card UI (Screen 4)

**Owner:** Frontend

**Tasks:**
1. Screen 3: Extracting progress (per-file status, auto-advance on completion)
2. Screen 4: Pull extraction result from API; render pre-filled confirmation card
3. Field states:
   - Green (high confidence, pre-confirmed)
   - Yellow (low confidence, "Please confirm")
   - Red (missing required, "Still Needed")
   - Blue optional (pre-filled, no confirmation required)
4. Conflict widget: side-by-side display, radio choice
5. Second vehicle block: soft block with clear message
6. Inline edit: customer can correct any field
7. "Submit My Request" button: disabled until all required fields have values
8. Chinese + English copy on all states

**Deliverable:** Screen 4 fully interactive. Customer can confirm, correct, and submit.

---

## WEEK 2 — Complete + Test (Days 8–14)

### Day 8: Quote-Ready Packet View (Screen 5b — Office)

**Owner:** Frontend + Backend

**Tasks:**
1. Backend: `GET /api/v1/requests/{request_id}/packet` → return formatted packet JSON
2. Packet JSON: customer, vehicle, location, driver, dates, policy context, missing, conflicts, sources
3. Suggested next action: auto-generated based on packet completeness
4. Office view: broker workbench tab → packet panel
5. Status strip at top: COMPLETE / MISSING FIELDS / HAS CONFLICTS (color-coded)
6. Source file list at bottom (download links with presigned URL, 1-hour expiry)
7. Copy-to-clipboard for full packet text

**Deliverable:** Office can see packet in broker workbench. Wu Xiaojie 10-second test ready.

---

### Day 9: Conflict Handling Logic

**Owner:** Backend + AI

**Tasks:**
1. Review conflict detection output from Day 5
2. Validate: same field, different value → always flagged (never silently resolved)
3. Customer conflict resolution stored: `resolution_chosen`, `resolution_source`, `resolution_by_customer`
4. Packet includes conflict summary: "Customer resolved VIN conflict: chose dealer contract value"
5. Low-confidence fields: if customer did not confirm → packet shows as "Customer did not confirm — use with caution"
6. Write unit tests: conflict_same_value_merge, conflict_different_value_flag, low_confidence_flag

**Deliverable:** Conflict logic tested and confirmed correct.

---

### Day 10: Missing Field UI + State Machine Wiring

**Owner:** Frontend + Backend

**Tasks:**
1. Missing field UI: red "Still Needed" pills in Screen 4
2. "What's still needed" summary bar above submit button
3. State machine implementation (code-based, no Temporal):
   - `draft_upload` → `uploaded` → `extracting` → `needs_confirmation` (→ `needs_more_info`) → `submitted_to_office` → `office_working` → `closed`
4. State stored in `requests.status` in Postgres
5. Customer sees: request status on Screen 5a (post-submit)
6. Office sees: request status badge on workbench packet

**Deliverable:** State machine working, customer and office see correct states.

---

### Day 11: Edge States

**Owner:** Frontend + AI

**Tasks:**
1. Unreadable file: OCR fails → file shown with red "Could not read this file. Try re-uploading."
2. Missing VIN: required field prompt on Screen 4 with "Why is VIN important?" tooltip
3. Conflicting VIN: tested from Case 4 kill test
4. Second vehicle: tested from Case 6 kill test
5. Unrelated document: Case 7 kill test — "No vehicle info found in this file"
6. No documents: Case 8 kill test — manual entry path + contact broker option
7. All 5 files unreadable: escalation message + contact broker link

**Deliverable:** All 6 edge states implemented and testable.

---

### Day 12–13: 10-Case Kill Test + QA

**Owner:** All

**Tasks:**
1. Prepare 10 document test sets (real or realistic mocks — see `P16_PACKET_BUILDER_KILL_TEST_PLAN.md`)
2. Run all 10 cases through staging environment
3. Record: extraction accuracy, missing field detection, conflict detection, packet readability, time to packet
4. Fix top 3–5 extraction failures
5. Fix any UI issues in confirmation card or packet view
6. QA: test on iPhone Safari + Chrome mobile
7. QA: test with Chinese phone number formats

**Deliverable:** Kill test results recorded. Pass threshold: ≥ 7/10 usable packets.

---

### Day 14: Chen Kui + Wu Xiaojie Review + GO/NO-GO

**Owner:** Founder + Broker + Office

**Tasks:**
1. Deploy to staging URL (or show locally on demo laptop)
2. Chen Kui walkthrough: customer flow (Screen 1 → 5a), 15 minutes max
3. Wu Xiaojie review: office packet (Screen 5b), 10-second test on 3 packets
4. Record: time saved estimate, friction points, missing fields in test cases
5. Record kill test summary: usable packets, accuracy, time
6. Decision: GO / CONDITIONAL GO / NO GO

**Deliverable:**
- Kill test results document
- Chen Kui go/no-go verbal
- Wu Xiaojie go/no-go verbal
- If GO: schedule first real customer test

---

## Key Milestones

| Day | Milestone |
|-----|-----------|
| 2 | Screens 1+2 live locally |
| 3 | File storage wired + tested |
| 5 | OCR extraction pipeline end-to-end |
| 7 | Customer confirmation card (Screen 4) fully interactive |
| 8 | Office packet view (Screen 5b) live |
| 11 | All edge states handled |
| 13 | Kill test complete |
| 14 | GO/NO-GO decision |

---

## What Already Exists (Reuse, Don't Rebuild)

| Asset | Location | Use in P16 |
|-------|---------|------------|
| OpenAI client | `services/` or `app/` | Import for GPT-4o Vision calls |
| Case storage / case_id pattern | `case_store.py` | Reuse for request_id + status |
| `still_needed` field pattern | `triage.py` | Reuse for missing field detection |
| Postgres connection | Existing DB URL | Add new tables for requests + extractions |
| Broker workbench UI | `BrokerWorkbenchTab` | Add packet panel as new tab/section |
| My Requests list | `MyRequestsTab` | Reuse for customer request list |
| Cloud Run deployment | `deploy_paid_pilot.sh` | Same deployment target |
| Vercel frontend | Existing Vercel project | Add new route `/add-car` |

---

## New Code Required

| Component | Approx scope |
|-----------|-------------|
| Upload UI (Screens 1–2) | ~200 lines React |
| Extraction progress (Screen 3) | ~50 lines React |
| Confirmation card (Screen 4) | ~400 lines React |
| Packet view (Screen 5b) | ~200 lines React |
| File upload backend endpoint | ~100 lines Python |
| Extraction pipeline | ~200 lines Python |
| Conflict detection logic | ~100 lines Python |
| State machine | ~80 lines Python |
| DB schema additions | 3–4 new tables/columns |
| GPT-4o Vision prompt | 1 prompt file |
| pdf2image integration | ~30 lines Python |

**Estimated total:** ~1,500 lines across frontend + backend. Well within 14-day scope.

---

## Risk Register

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| OCR accuracy on blurry photos | Medium | Show confidence warning; don't pre-confirm |
| PDF conversion issues (poppler) | Low | Test with 5 real dealer PDFs on Day 4 |
| GPT-4o rate limits at demo time | Low | Add retry with exponential backoff |
| Second vehicle detection false positive | Medium | Tune prompt; add threshold |
| Customer confused by conflict widget | Medium | A/B test: side-by-side vs sequential |
| Wu Xiaojie finds packet hard to read | Low | Run 10-second test on Day 13, fix before Day 14 |
| Garaging ZIP not in any document | High | Always prompt manually if not found |

---

## Success Definition

At Day 14:

1. Customer uploads docs → gets Quote-Ready Packet in < 90 seconds
2. Wu Xiaojie reads packet → knows quote-readiness in 10 seconds
3. ≥ 7/10 kill test cases pass
4. Chen Kui would show this to a customer today
5. No required field is ever silently missing or silently guessed

---

*End of P16 Next 14-Day Build Plan*
