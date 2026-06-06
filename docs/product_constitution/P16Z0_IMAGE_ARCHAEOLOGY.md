# P16-Z0 Image Intelligence Archaeology

**Date:** 2026-06-01  
**Sprint:** P16-Z0 — Phase 5  
**Search terms:** OCR, vision, image, notice_image, screenshot, pdf, document extraction  
**Evidence:** `image_input_pipeline.py`, `ocr_case_fusion.py`, `v6_attachment_sidecar.py`, `BrokerWorkbenchTab.tsx`, P16-L/X/Y docs

---

## Executive answer: Can the current system process images?

| Mode | Can process? | Notes |
|------|--------------|-------|
| **Text mentioning screenshot** | Yes | `screenshot_sent`, classification markers — no pixels required |
| **`notice_image` as missing field** | Yes | Detects when customer should send notice but didn't |
| **Inline image on triage API** | Yes (API) | **No product UI caller** — simulation only |
| **Attachment upload (image)** | Yes | Broker workbench → OCR sidecar when credentials exist |
| **Attachment upload (PDF)** | **No text** | Accepted; `engine: "pdf_skipped"` |
| **Primary OCR intake (upload-first)** | **Frozen** | P16-L feature freeze; broker one-pager out-of-scope |
| **Deployed trial paste** | **Text-only** | P16-X: broker paste path has no image upload in main flow |

**Verdict:** Engine can process images when bytes are provided and Vision is configured. **Trial wedge is text paste**; image path is secondary, hidden, or stubbed.

---

## Code that exists

### Pipeline

| Module | Role |
|--------|------|
| `image_input_pipeline.py` | Google Vision REST/SDK; stub fallback |
| `parse_ocr_text_to_fields.py` | OCR text → structured fields |
| `ocr_case_fusion.py` | Merge OCR into triage |
| `v6_attachment_sidecar.py` | `extract_ocr_from_inline_base64()` |
| `triage.py` | `[OCR]` parsing, `v6_ocr_signals`, `IMAGE_FIRST` weak path, `_message_needs_notice_image()` |

### Routes & store

| Endpoint / function | Behavior |
|---------------------|----------|
| `POST /api/inbox/triage` + inline image | OCR via sidecar |
| `POST /cases/{id}/attachments` | Save + `run_v6_ocr_for_saved_attachment()` |
| `add_attachment_to_case()` | `case_store.py` |

### UI

| Surface | Wired? |
|---------|--------|
| `BrokerWorkbenchTab.tsx` ~2048–2108 | `uploadCaseAttachment()` — image/* + .pdf |
| `inboxTriage.ts` `triageMessage(..., inlineImage?)` | API param exists |
| `ScenarioReplayTab.tsx` | Inline OCR in **simulation only** |

### Env flags

- `GOOGLE_API_KEY` / `GOOGLE_CLOUD_API_KEY`
- `V6_OCR_FORCE_STUB=1`, `V6_OCR_STUB_TEXT`
- `V6_AUTO_INPUT_VARIANT` (A/B/C via client pack)

### Lab / simulation

- `scripts/run_v6_auto_input_simulation.py` — Monte Carlo text vs OCR
- P16-Y battery case Y38 — notice image gap

---

## Gaps that remain

| Gap | Severity | Owner |
|-----|----------|-------|
| No `triageMessage(inlineImage)` from product UI | P1 | UI revival |
| PDF text extraction stubbed | P1 | Needs external converter or defer |
| OCR without credentials → empty non-blocking | P2 | Ops (keys) |
| Screenshot with no OCR blob — weak fusion | P1 | P16-Y #4 |
| Primary upload-first intake frozen | Policy | Constitution / P16-L |
| Deployed broker paste text-only | P1 | Trial UX choice |
| RAG `.pdf` discovery | N/A | `discover_auto_insurance_sources.py` — corpus not intake |

---

## notice_image vs OCR vs screenshot

| Concept | Layer |
|---------|-------|
| `notice_image` | **Missing field** — customer should provide notice |
| OCR fusion | **When blob exists** — enriches collected fields |
| `screenshot_sent` | **Claim field** — customer says they sent screenshot |
| IMAGE_FIRST weak path | **Clarification** when image present but OCR empty |

Do not conflate these when reviving features.

---

## Status matrix

| Capability | Impl | Doc | Deploy trial | Hidden | Abandoned |
|------------|------|-----|--------------|--------|-----------|
| Vision OCR engine | Yes | Sparse | If key + upload | Stub default | — |
| Inline triage OCR | Yes | — | No | Sim only | — |
| Attachment OCR | Yes | — | Yes (workbench) | — | — |
| PDF extract | Stub | P16-L | Accepts, skips | — | — |
| notice_image rules | Yes | P16-Y | Yes (text) | — | — |
| Upload-first OCR product | — | P16-L freeze | — | — | **Frozen v1** |

---

## Revival vs rebuild

| Action | Rationale |
|--------|-----------|
| **Revive:** wire existing `inlineImage` on paste card | API done |
| **Revive:** ensure Vision keys on pilot deploy | Ops |
| **Do not rebuild:** new OCR microservice | Duplicates pipeline |
| **Defer:** PDF until wedge proves text paste | Scope |
| **Do not rebuild:** primary OCR intake | Constitution lock |

---

## Evidence index

| Artifact | Path |
|----------|------|
| Feature freeze | `P16L_FEATURE_FREEZE_REPORT.md` (referenced) |
| Conversation audit (OCR ❌ paste) | `P16X_CONVERSATION_AUDIT.md` |
| P16-Y gap #4 | `P16Y_FINAL_VERDICT.md` |
| Pipeline | `services/fiqa_api/inbox_triage/image_input_pipeline.py` |

---

*End of P16-Z0 Image Archaeology*
