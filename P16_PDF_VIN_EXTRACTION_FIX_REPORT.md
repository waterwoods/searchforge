# P16 PDF VIN Extraction — Root Cause Review → Conditional Fix → Validation

**Date:** 2026-06-21  
**Sprint:** P16 PDF VIN Extraction Fix  
**Decision Gate:** **PASSED** (High confidence + Strategy A recommended)

---

## 1. Root Cause Conclusion

### Investigation Answers

| # | Question | Answer | Evidence |
|---|----------|--------|----------|
| 1 | Does production ignore PDF text layers? | **YES** | `OpenAIExtractor.extract` → `_prepare_file` → `_pdf_to_images` only. No `page.get_text()` call on production path. |
| 2 | Is VIN available in PDF text layer? | **YES** | PyMuPDF `get_text()` on `pa_001` returns `4T1BF1FK5CU512345` on its own line. **5/5** purchase-agreement PDFs match ground truth via text layer. |
| 3 | Is Vision OCR the VIN source today? | **YES** | Rendered PNG sent to `gpt-4o` vision; VIN field populated from model JSON response only. |
| 4 | What caused `4T1BF…` → `1B1F1FK…`? | **Vision OCR glyph misread** | PDF text is correct; rendered image OCR confuses `4T`→`1B` at positions 1–2, yielding 16 chars. YMM are short labeled text — easier for vision. |
| 5 | Confidence level | **HIGH** | Code-path trace + PDF text dump + reproduced production misread + 5/5 text-layer GT match. |

### Secondary Finding (not fixed in this sprint)

Synthetic corpus VINs mostly fail NHTSA checksum validation (e.g. `pa_001` position 9: expected `8`, got `5`). Even with correct text-layer VIN, **READY is still blocked** by existing `validate_vin()` → `broker_review` for 4/5 purchase agreements. Only `pa_007` / `dw_001` have checksum-valid VINs.

---

## 2. Decision Gate

| Condition | Result |
|-----------|--------|
| Confidence is HIGH | ✅ |
| PDF Text First + Vision Fallback recommended | ✅ Strategy A |

**Gate passed → Phase 2 implemented.**

---

## 3. Strategy Comparison (Phase 1)

| Strategy | Effort | Risk | Expected Accuracy Gain |
|----------|--------|------|------------------------|
| **A. PDF Text First + Vision Fallback** | **S** (~40 lines) | **Low** — fallback unchanged for scans/images | **High on native PDFs** (5/5 GT match proven) |
| B. Vision Only + VIN Correction | M | Medium — post-hoc rules fragile | Low–Medium |
| C. Vision Only + Checksum Repair | M | **High** — could invent invalid VINs | Medium (wrong approach) |
| D. Hybrid (text VIN + vision YMM + rules merge) | L | Medium — merge complexity | High but over-scoped |

---

## 4. Implementation (Phase 2)

### Files Changed

| File | Change |
|------|--------|
| `services/fiqa_api/ocr_kill_test/extractor.py` | Added `try_pdf_text_layer_vin`, `_apply_pdf_text_vin_preference`; wired into `OpenAIExtractor` and `GeminiExtractor` |
| `tests/test_pdf_text_vin_extraction.py` | **New** — 6 unit tests |

### Code Paths Changed

```
POST /api/intake/add-car/extract
  → add_car._run_real_extraction()
    → packet_builder.process_case()
      → OpenAIExtractor.extract()          [CHANGED]
          → _prepare_file() → Vision OCR   [unchanged]
          → _apply_pdf_text_vin_preference()  [NEW — overrides vin if PDF text valid]
```

### Behavior

```
PDF Upload
    ↓
Vision extraction runs (all fields, unchanged)
    ↓
try_pdf_text_layer_vin() via PyMuPDF + regex
    ↓
If structurally valid 17-char VIN found
    ↓
Override vin field (confidence 0.99, note if vision differed)
    ↓
Continue normal pipeline (merge, save_case, readiness, UI)
```

### Preserved (unchanged)

- `save_case` / Postgres persistence
- Readiness logic (`validate_vin`, `computeReadinessStatus`)
- UI / Trusted Packet structure
- Image/HEIC path (no PDF text layer → vision only)
- No new APIs, endpoints, or UI

---

## 5. Validation Results (Phase 3)

### Purchase Agreement PDFs

| File | Ground Truth VIN | Before Fix | After Fix | Length | Checksum | Readiness* |
|------|------------------|------------|-----------|--------|----------|------------|
| `pa_001_toyota_camry.pdf` | 4T1BF1FK5CU512345 | 1B1F1FK5CU512345 | **4T1BF1FK5CU512345** | 16→**17** | ✗→✗ | broker_review→broker_review |
| `pa_002_honda_civic.pdf` | 2HGFC2F69MH123456 | 1HGFC2F69MH123456 | **2HGFC2F69MH123456** | 17→17 | ✗→✗ | broker_review→broker_review |
| `pa_003_bmw_x5.pdf` | 5UXCR6C06L9B12345 | JXCR6C06L9B12345 | **5UXCR6C06L9B12345** | 16→**17** | ✗→✗ | broker_review→broker_review |
| `pa_005_lexus_rx350.pdf` | 2T2BZMCA8KC123456 | (not run) | **2T2BZMCA8KC123456** | —→17 | —→✗ | n/a→broker_review |
| `pa_007_hyundai_elantra.pdf` | KMHD84LF8KU123456 | (not run) | **KMHD84LF8KU123456** | —→17 | —→**✓** | n/a→**ready** |

\*Readiness computed with production vision YMM + VIN before/after fix; no other warnings.

### Other PDF corpus (text-layer only — after fix)

| File | GT Match | Checksum |
|------|----------|----------|
| `reg_002_ca_dmv.pdf` | ✅ | ✗ |
| `dw_001_finance_worksheet.pdf` | ✅ | ✓ |
| `dw_002_buyers_order.pdf` | ✅ | ✗ |
| `ws_001_toyota_rav4.pdf` | ✅ | ✗ |
| `ws_005_bmw_330i.pdf` | ✅ | ✗ |

### Summary Metrics

| Metric | Before | After |
|--------|--------|-------|
| PA PDF GT VIN match | 0/3 tested (vision) | **5/5** (text layer) |
| PA PDF 17-char VIN | 1/3 (pa_002 only, wrong char) | **5/5** |
| PA PDF READY path | **0/5** | **1/5** (pa_007 only) |
| Unit tests | — | **12/12 pass** (6 new + 6 regression) |

---

## 6. READY-Path Improvement

| Scenario | Before | After | Notes |
|----------|--------|-------|-------|
| Set A (`pa_001` + reg) | BROKER_REVIEW (16-char VIN) | BROKER_REVIEW (17-char VIN, checksum fail) | **VIN accuracy fixed; READY still blocked by checksum** |
| `pa_007` alone | Not tested | **READY** | Checksum-valid synthetic VIN |
| Image/HEIC uploads | Unchanged | Unchanged | Vision-only path preserved |
| Wrong-doc / NEED_INFO | Unchanged | Unchanged | No PDF text VIN → no override |

**Net:** VIN accuracy on native PDFs is materially improved. READY path opens for checksum-valid PDFs only; corpus checksum defect remains a separate blocker for Set A.

---

## 7. Rollback Plan

1. Revert `services/fiqa_api/ocr_kill_test/extractor.py` (remove `try_pdf_text_layer_vin`, `_apply_pdf_text_vin_preference`, and two return-site calls).
2. Delete `tests/test_pdf_text_vin_extraction.py` (optional).
3. Redeploy Cloud Run API — no DB migration, no UI change, no config change.

Single-file revert; zero data migration risk.

---

## 8. Final Recommendation

### **CONDITIONAL SHIP**

**Ship because:**
- Root cause proven with high confidence
- Minimal, isolated change (one production module)
- 5/5 purchase-agreement VIN accuracy on PDF text layer
- Zero regression on existing tests
- Vision fallback preserved for scanned PDFs and all images

**Conditions before calling Set A "READY":**
1. Deploy this fix to Cloud Run QA
2. Regenerate corpus VINs with valid NHTSA checksums (separate small sprint)
3. Re-run Set A validation post-deploy

**Do not block this fix** on corpus checksum repair — they are independent improvements.

---

## Artifacts

| Artifact | Path |
|----------|------|
| Validation JSON | `artifacts/p16_pdf_vin_rca/validation_results.json` |
| Prior real-world report | `P16_REAL_WORLD_VALIDATION_REPORT.md` |
| Unit tests | `tests/test_pdf_text_vin_extraction.py` |

---

*End of P16 PDF VIN Extraction Fix Report*
