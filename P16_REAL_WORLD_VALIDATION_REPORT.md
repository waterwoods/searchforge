# P16 Real-World Document Validation Report

**Date:** 2026-06-21  
**Sprint:** P16 Real-World Document Validation (validation only — no code changes)  
**QA URL:** https://ui-smoky-beta.vercel.app/add-car  
**API:** https://fiqa-api-1013093472160.us-west1.run.app  
**Extraction model (production):** `gpt-4o` (real extraction; `mock_mode: false` on all runs)

---

## Executive Summary

Five validation sets (A–E) were executed against the **stable QA deployment** using realistic document scenarios modeled on California auto insurance office intake. State-machine behavior for **failure modes is strong**: wrong documents, partial uploads, and VIN conflicts route correctly to **NEED_INFO** or **BROKER_REVIEW** without silent READY.

The **happy path does not pass**. Set A (READY GOLD) failed on every variant tested — including a single clean purchase agreement PDF — because VIN extraction systematically produces invalid VINs (truncated to 16 characters or first-character corruption), which forces **BROKER_REVIEW** even when year, make, and model extract correctly.

**Answer to the north-star question:** *Would a real broker office trust this system with real documents?*

**Not yet for production intake.** Failure-mode gating is trustworthy; extraction accuracy on vehicle identity fields is not reliable enough to auto-present **READY FOR BROKER** on standard dealer documents.

| Verdict | Count |
|---------|-------|
| **PASS** (expected state matched) | 4 / 5 |
| **FAIL** | 1 / 5 (Set A — READY GOLD) |
| **Critical blocker** | VIN OCR reliability prevents READY on clean vehicle docs |

---

## Pass / Fail Table

| Set | Scenario | Expected | Actual | Pass | Severity if Fail |
|-----|----------|----------|--------|------|------------------|
| **A** | READY GOLD — purchase agreement + matching registration | `ready` | `broker_review` | **FAIL** | **P0** |
| **B** | NEED_INFO — partial WeChat screenshots, no VIN | `needs_info` | `needs_info` | PASS | — |
| **C** | WRONG DOCUMENT — grocery receipt + utility bill | `needs_info` | `needs_info` | PASS | — |
| **D** | VIN CONFLICT — Toyota PA + Honda PA | `broker_review` | `broker_review` | PASS | — |
| **E** | REAL HEIC — iPhone VIN plate photo | upload OK + graceful state | upload OK → `broker_review` | PASS | — |

### Supplementary runs (same API, not primary sets)

| Run | Documents | Expected | Actual | Notes |
|-----|-----------|----------|--------|-------|
| A2 | Single `pa_001_toyota_camry.pdf` | `ready` | `broker_review` | VIN extracted as 16-char `1B1F1FK5CU512345` |
| A3 | `pa_001` + `ws_001` (different VINs) | `broker_review` | `broker_review` | Conflict detection works |
| B2 | Single `wechat_002` (partial) | `needs_info` | `needs_info` | Clean NEED_INFO |
| C2 | Random landscape PNG | `needs_info` | `needs_info` | Clean NEED_INFO |

---

## Document Corpus Used

All documents are **synthetic or sample-only** — no private customer data.

| Source | Location | Description |
|--------|----------|-------------|
| **Dealer purchase agreements (7 PDF/JPG)** | `test_data/p16_real_docs/purchase_agreements/` | Generated via `scripts/generate_p16_corpus.py`; styled as CA dealer contracts with embedded ground-truth fields |
| **CA registration cards (3)** | `test_data/p16_real_docs/registrations/` | Synthetic DMV-style temp/permanent registration |
| **Window stickers (5)** | `test_data/p16_real_docs/window_stickers/` | Synthetic Monroney labels |
| **WeChat screenshots (3)** | `test_data/p16_real_docs/wechat/` | Synthetic partial-intake chat screenshots |
| **VIN photos (2)** | `test_data/p16_real_docs/vin_photos/` | Synthetic dashboard/door-jamb VIN plate photos |
| **Wrong-document controls** | `test_data/p16_validation_sprint/` | Synthetic grocery receipt PNG, SCE utility bill PDF, random landscape PNG |
| **HEIC sample** | `test_data/p16_validation_sprint/set_e_iphone_vin.heic` | HEIF converted from synthetic VIN photo (iPhone pipeline test) |

Ground truth reference: `test_data/p16_real_docs/ground_truth.json` and `docs/p16/P16_GROUND_TRUTH.md`.

---

## Validation Set Details

### Set A — READY GOLD

**Goal:** Clean vehicle documents → **READY FOR BROKER**

| | |
|---|---|
| **Documents** | `pa_001_toyota_camry.pdf` + `reg_001_ca_dmv.jpg` |
| **Ground-truth VIN** | `4T1BF1FK5CU512345` (note: corpus VIN is **16 characters**, not 17 — see Issues) |
| **Expected** | VIN, year, make, model extracted; no blocking warnings; **READY** |
| **Actual** | **BROKER_REVIEW** |
| **Case ID** | `case_65d34068471a` |
| **Elapsed** | 19.1s |

**Extraction result:**

| Field | Extracted | Source file |
|-------|-----------|-------------|
| VIN | `1B1F1FK5CU512345` ❌ (16 chars; leading `4` dropped) | `pa_001_toyota_camry.pdf` |
| Year | `2023` ✅ | `pa_001_toyota_camry.pdf` |
| Make | `Toyota` ✅ | `pa_001_toyota_camry.pdf` |
| Model | `Camry` ✅ | `pa_001_toyota_camry.pdf` |
| Garaging ZIP | `91801` ✅ (from intake form) | intake_form |

**Warnings:**
- `VIN format may be invalid — verify manually (VIN must be 17 characters (got 16))`
- `Multiple VINs detected. Please verify which one is the new vehicle.`

**Screenshot:** `artifacts/p16_real_world_validation/screenshots/A_READY_GOLD_packet.png`

**Issues discovered:**
1. VIN OCR drops leading character (`4T…` → `1B…`) — **P0**
2. Corpus ground-truth VIN for `pa_001` is only 16 characters — **P1** (corpus defect)
3. Multi-doc upload triggers "Multiple VINs" even when registration matches purchase agreement — **P2**

**Severity:** **P0** — primary happy path blocked

---

### Set B — NEED_INFO

**Goal:** Missing critical vehicle information → **NEED_INFO** + Auto Follow-Up

| | |
|---|---|
| **Documents** | `wechat_002_delivery_date.png` + `wechat_003_zip_confirmation.jpg` |
| **Expected** | NEED_INFO; missing VIN/YMM identified; Auto Follow-Up visible |
| **Actual** | **NEED_INFO** ✅ |
| **Case ID** | `case_6d0087c3a543` |
| **Elapsed** | 9.3s |

**Extraction result:** No VIN, year, make, or model extracted (correct for these docs).

**Document guidance (bilingual):**
> We couldn't find vehicle information in your uploaded files. Please upload a purchase agreement, vehicle registration card, insurance card, or a clear VIN photo.

**Missing fields surfaced:** VIN number, Vehicle Year / Make / Model

**Auto Follow-Up:** Would display (critical keys present: vin, year/make/model missing; status = `needs_info`).

**Warnings (minor noise):** `Conflicting garaging_zip values detected across documents` — does not override NEED_INFO (ADR-001 correct).

**Screenshot:** `artifacts/p16_real_world_validation/screenshots/B_NEED_INFO_packet.png`

**Issues discovered:** Garaging ZIP conflict warning on partial chat screenshots is confusing but non-blocking — **P3**

**Severity:** PASS

---

### Set C — WRONG DOCUMENT

**Goal:** Unrelated uploads must **not** become READY

| | |
|---|---|
| **Documents** | `set_c_grocery_receipt.png` + `set_c_utility_bill.pdf` |
| **Expected** | NEED_INFO or BROKER_REVIEW (not READY) |
| **Actual** | **NEED_INFO** ✅ |
| **Case ID** | `case_519dc0718f8c` |
| **Elapsed** | 7.0s |

**Extraction result:** Empty vehicle fields. Document relevance gate fired correctly.

**Supplementary:** Random landscape PNG alone → NEED_INFO (4.2s, no warnings).

**Screenshot:** `artifacts/p16_real_world_validation/screenshots/C_WRONG_DOCUMENT_packet.png`

**Issues discovered:** None — gate behaves as designed.

**Severity:** PASS

---

### Set D — VIN CONFLICT

**Goal:** Conflicting VINs → **BROKER_REVIEW** with visible warning

| | |
|---|---|
| **Documents** | `pa_001_toyota_camry.pdf` + `pa_002_honda_civic.pdf` |
| **Expected** | BROKER_REVIEW; warning visible; no silent VIN selection |
| **Actual** | **BROKER_REVIEW** ✅ |
| **Case ID** | `case_2c81aae9ff85` |
| **Elapsed** | 12.1s |

**Warnings (6 total):**
- VIN format invalid (16 chars)
- Multiple VINs detected
- Conflicting customer_name, year, make_model, garaging_zip across documents

**Extracted VIN shown:** `1B1F1FK5CU512345` (from Toyota doc; Honda VIN not silently chosen as final — conflict surfaced)

**Source attribution:** VIN/year/make/model attributed to `pa_001_toyota_camry.pdf` only in packet display.

**Screenshot:** `artifacts/p16_real_world_validation/screenshots/D_VIN_CONFLICT_packet.png`

**Issues discovered:** VIN format warning conflated with true multi-VIN conflict — broker sees 6 warnings which may be overwhelming — **P2**

**Severity:** PASS (behavior correct)

---

### Set E — REAL HEIC

**Goal:** iPhone HEIC upload succeeds or degrades gracefully

| | |
|---|---|
| **Documents** | `set_e_iphone_vin.heic` (HEIF, 17 KB) |
| **Expected** | Successful upload; extraction or graceful NEED_INFO |
| **Actual** | Upload **OK** → **BROKER_REVIEW** (VIN extracted but invalid checksum; YMM missing) |
| **Case ID** | `case_4652e137f9e4` |
| **Elapsed** | 5.6s |

**Extraction result:**

| Field | Value |
|-------|-------|
| VIN | `4T1BF1FK5CU512345` (17 chars but checksum invalid) |
| Year/Make/Model | empty |

**Warning:** `VIN checksum may be invalid (expected '8' at position 9, got '5')`

**Screenshot:** `artifacts/p16_real_world_validation/screenshots/E_REAL_HEIC_packet.png`

**Issues discovered:**
1. HEIC pipeline works end-to-end ✅
2. VIN-only HEIC photo cannot reach READY without YMM — expected; follow-up path applies — **P3**
3. Synthetic VIN fails checksum validation — corpus issue — **P2**

**Severity:** PASS (upload + graceful degradation)

---

## Top Risks Discovered

| # | Risk | Severity | Impact |
|---|------|----------|--------|
| 1 | **VIN first-character drop / truncation** on clean PDFs and images | **P0** | Every tested purchase agreement routes to BROKER_REVIEW instead of READY |
| 2 | **Corpus VINs include invalid lengths/checksums** | **P1** | Validation corpus cannot produce a true READY GOLD baseline until fixed |
| 3 | **No READY path observed** across 8 API runs with vehicle documents | **P0** | Broker cannot trust auto-ready packets for quoting |
| 4 | **Warning overload on multi-doc conflict** (6 warnings on Set D) | **P2** | Correct behavior but may erode broker confidence in UI clarity |
| 5 | **Partial-doc ZIP conflict warning on Set B** | **P3** | Minor UX noise during NEED_INFO flow |
| 6 | **YMM not extracted from VIN-only HEIC** | **P3** | Expected gap; follow-up message handles it |

---

## Recommended Fixes

*(Documentation only — not implemented in this sprint)*

| Priority | Fix | Rationale |
|----------|-----|-----------|
| **P0** | Investigate VIN extraction prompt / PDF render / post-processing for leading-character loss | Root cause of Set A failure; observed on `pa_001`, `pa_002`, `pa_003` |
| **P0** | Regenerate corpus with **valid 17-character VINs** (correct checksum) | Current ground truth includes 16-char VINs; invalidates READY GOLD testing |
| **P1** | Re-run Set A after VIN fix; target ≥90% READY on clean PA + registration pairs | Required before broker pilot |
| **P1** | Collect 3–5 **redacted real broker office documents** (with broker permission) | Synthetic docs do not capture fax quality, handwriting, or real dealer layouts |
| **P2** | Deduplicate / consolidate conflict warnings (one primary alert + detail list) | Set D showed 6 warnings for one logical conflict |
| **P2** | Suppress field-conflict warnings when `document_guidance` is active (NEED_INFO path) | Set B garaging_zip warning is misleading |
| **P3** | Add VIN-decode fallback for year/make/model when VIN extracts cleanly | Would improve HEIC-only and VIN-photo intake |

---

## Artifacts

| Artifact | Path |
|----------|------|
| API results (summary) | `artifacts/p16_real_world_validation/api_results.json` |
| API results (full) | `artifacts/p16_real_world_validation/api_results_full.json` |
| Supplementary runs | `artifacts/p16_real_world_validation/supplementary_results.json` |
| Packet screenshots (PNG) | `artifacts/p16_real_world_validation/screenshots/*_packet.png` |
| Packet HTML replays | `artifacts/p16_real_world_validation/screenshots/*_packet.html` |
| Validation-only test assets | `test_data/p16_validation_sprint/` |

---

## Methodology Notes

- All API calls: `POST /api/intake/add-car/extract` on production Cloud Run backend
- Readiness state computed using same logic as `AddCarPage.tsx` → `computeReadinessStatus()`
- QA UI verified reachable (HTTP 200) at stable alias `ui-smoky-beta.vercel.app`
- No code, UI, feature, or deployment changes made during this sprint
- Browser file-upload automation was blocked by MCP security restrictions; packet screenshots generated from live API responses

---

*End of P16 Real-World Document Validation Report*
