# P16 OCR Accuracy Report V1

**Date:** 2026-06-18  
**Sprint:** P16 Evidence Phase  
**Provider:** dry_run  
**Corpus:** `test_data/p16_real_docs/` — 25 documents  
**Source of truth:** `docs/p16/P16_DECISION_FREEZE_V1.md`


> ⚠️ **DRY RUN MODE** — No real API calls were made. All extraction values are empty.
> All accuracy metrics show 0% because the extractor returned no data.
> **To get real evidence:** run with `--provider gemini` (requires GEMINI_API_KEY).

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Corpus size | 25 documents |
| Document types | purchase_agreement, window_sticker, registration, wechat, vin_photo, dealer_worksheet |
| VIN Accuracy (overall) | **0%** |
| YMM Accuracy (Year) | **0%** |
| Packet Completeness | **0%** (0/25 docs packet-ready) |
| Pilot Readiness | **NO DATA** |

---

## Section 1: Corpus Built

22 documents generated across 6 document types.

| Type | Count | Format | Ground Truth |
|------|-------|--------|--------------|
| Purchase Agreements | 7 | PDF + JPG | VIN, YMM, Name, ZIP, Lienholder |
| Window Stickers | 5 | PDF + JPG + PNG | VIN, YMM only |
| Registrations | 3 | PDF + JPG | VIN, YMM, Name, ZIP |
| WeChat Screenshots | 3 | JPG + PNG | Varies (VIN/ZIP/partial) |
| VIN Photos | 2 | JPG | VIN only |
| Dealer Worksheets | 2 | PDF | VIN, YMM, Name, ZIP, Lienholder |
| **Total** | **22** | | |

OCR difficulty: 9 easy / 10 medium / 3 hard.

Ground truth source: `test_data/p16_real_docs/ground_truth.json`  
Full inventory: `docs/p16/P16_CORPUS_INVENTORY.md`  
Full ground truth: `docs/p16/P16_GROUND_TRUTH.md`

---

## Section 2: Documents Collected

All documents were generated with embedded realistic California auto insurance intake data.
VINs follow NHTSA/ISO 3779 17-character format.
Customer names are Chinese-American — consistent with Chen Kui's pilot customer base.

Document types match the real intake scenario:

- **Purchase agreements** — primary source for VIN + YMM + lienholder
- **Window stickers** — VIN + YMM, no customer data (expected and correct)
- **Registrations** — VIN + YMM + owner name
- **WeChat screenshots** — partial data, conversational format
- **VIN photos** — VIN only, high failure rate expected
- **Dealer worksheets** — structured, highest completeness expected

---

## Section 3: Accuracy Metrics

### 3A. Overall Field Accuracy

| Field | Pass | Fail | Skip | Accuracy |
|-------|------|------|------|----------|
| VIN | 0 | 23 | 2 | **0%** |
| Year | 0 | 22 | 3 | **0%** |
| Make/Model | 0 | 22 | 3 | **0%** |
| Customer Name | 0 | 15 | 10 | **0%** |
| Garaging ZIP | 0 | 15 | 10 | **0%** |
| Packet Ready | 0 | 25 | — | **0%** |

### 3B. Accuracy By Document Type

| Doc Type | n | VIN | Year | Make/Model | Name | ZIP | Packet Ready |
|----------|---|-----|------|------------|------|-----|--------------|
| purchase_agreement | 7 | 0% | 0% | 0% | 0% | 0% | 0/7 (0%) |
| window_sticker | 6 | 0% | 0% | 0% | N/A | N/A | 0/6 (0%) |
| registration | 3 | 0% | 0% | 0% | 0% | 0% | 0/3 (0%) |
| wechat_screenshot | 4 | 0% | 0% | 0% | 0% | 0% | 0/4 (0%) |
| vin_photo | 3 | 0% | 0% | 0% | N/A | N/A | 0/3 (0%) |
| dealer_worksheet | 2 | 0% | 0% | 0% | 0% | 0% | 0/2 (0%) |
| **OVERALL** | **25** | **0%** | **0%** | **0%** | **0%** | **0%** | **0/25 (0%)** |

### 3C. Per-Document Detail

| Filename | Type | Difficulty | VIN | Year | YMM | Name | ZIP | Ready |
|----------|------|-----------|-----|------|-----|------|-----|-------|
| dw_001_finance_worksheet.pdf | dealer_worksheet | easy | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| dw_002_buyers_order.pdf | dealer_worksheet | medium | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| heic_001_vin_plate.heic | vin_photo | easy | ❌ | ❌ | ❌ | — | — | ❌ |
| heic_002_window_sticker.heic | window_sticker | easy | ❌ | ❌ | ❌ | — | — | ❌ |
| heic_003_wechat_vin.heic | wechat_screenshot | easy | ❌ | ❌ | ❌ | — | — | ❌ |
| pa_001_toyota_camry.pdf | purchase_agreement | easy | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| pa_002_honda_civic.pdf | purchase_agreement | easy | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| pa_003_bmw_x5.pdf | purchase_agreement | medium | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| pa_004_tesla_model3.jpg | purchase_agreement | medium | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| pa_005_lexus_rx350.pdf | purchase_agreement | hard | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| pa_006_nissan_altima.jpg | purchase_agreement | easy | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| pa_007_hyundai_elantra.pdf | purchase_agreement | medium | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| reg_001_ca_dmv.jpg | registration | easy | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| reg_002_ca_dmv.pdf | registration | medium | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| reg_003_ca_temp.jpg | registration | hard | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| vin_001_dashboard.jpg | vin_photo | medium | ❌ | — | — | — | — | ❌ |
| vin_002_door_jamb.jpg | vin_photo | hard | ❌ | — | — | — | — | ❌ |
| wechat_001_vin_message.jpg | wechat_screenshot | medium | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| wechat_002_delivery_date.png | wechat_screenshot | medium | — | ❌ | ❌ | ❌ | ❌ | ❌ |
| wechat_003_zip_confirmation.jpg | wechat_screenshot | easy | — | — | — | ❌ | ❌ | ❌ |
| ws_001_toyota_rav4.pdf | window_sticker | easy | ❌ | ❌ | ❌ | — | — | ❌ |
| ws_002_ford_f150.jpg | window_sticker | easy | ❌ | ❌ | ❌ | — | — | ❌ |
| ws_003_honda_crv.jpg | window_sticker | medium | ❌ | ❌ | ❌ | — | — | ❌ |
| ws_004_chevy_equinox.png | window_sticker | easy | ❌ | ❌ | ❌ | — | — | ❌ |
| ws_005_bmw_330i.pdf | window_sticker | medium | ❌ | ❌ | ❌ | — | — | ❌ |

---

## Section 4: Top Failure Modes

| Failure Mode | Occurrences |
|-------------|-------------|
| Missing/wrong vin | 23 |
| Missing/wrong year | 22 |
| Missing/wrong make_model | 22 |
| Missing/wrong name | 15 |
| Missing/wrong zip | 15 |

### Top Missing Fields (per extraction pipeline)

| Field | Missing in N docs |
|-------|--------------------|
| customer_name | 25 |
| phone | 25 |
| vin | 25 |
| year | 25 |
| make_model | 25 |
| garaging_zip | 25 |
| primary_driver | 25 |
| delivery_or_effective_date | 25 |

### Trade-in Issues

**dw_002_buyers_order.pdf** contains a trade-in section. If a second vehicle VIN is present, the extraction pipeline should flag `second_vehicle_detected = true`. Evaluation checks this case specifically.

---

## Section 5: Pilot Recommendation

### NO DATA

Dry-run mode — no real extraction performed. Run with --provider gemini.

### Conditions (if CONDITIONAL GO)

1. **VIN conflicts must be reviewed by broker** — source attribution shows which file VIN came from
2. **WeChat-only submissions are insufficient** — customer must upload at least one structured document
3. **VIN photo submissions need secondary document** — camera shots alone have high failure rate
4. **Garaging ZIP must come from intake form** — window stickers never contain ZIP (by design)

### Evidence Basis

This recommendation is based on extraction evidence from 25 corpus documents.
It is not an opinion. The thresholds are:

- VIN Accuracy ≥ 90% → GO
- VIN Accuracy ≥ 75% → CONDITIONAL GO  
- VIN Accuracy < 75% → NO GO

---

## Section 6: Exact Next Action

1. **Fix extraction before pilot.** Top failure modes above must be addressed. Re-run eval after fixes.
2. **Check GEMINI_API_KEY is set.** If running dry_run, re-run with real provider.
3. **Re-run accuracy eval after fixes:** `python3 scripts/run_p16_accuracy_eval.py --provider gemini`

---

*Report generated by `scripts/run_p16_accuracy_eval.py` on 2026-06-18T05:51:38.*  
*Corpus: `test_data/p16_real_docs/` | Ground truth: `docs/p16/P16_GROUND_TRUTH.md`*  
*Artifacts: `artifacts/p16_accuracy_eval/`*
