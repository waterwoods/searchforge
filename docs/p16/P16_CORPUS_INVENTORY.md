# P16 Corpus Inventory

**Created:** 2026-06-17  
**Sprint:** P16 Evidence Phase  
**Corpus root:** `test_data/p16_real_docs/`  
**Total documents:** 22  
**Source:** Synthetic documents generated with realistic California auto-insurance intake data. Field values are embedded and verified — see `P16_GROUND_TRUTH.md` for expected extraction values.  
**Ground truth JSON:** `test_data/p16_real_docs/ground_truth.json`

---

## Summary by Document Type

| Type | Count | Subfolders |
|------|-------|------------|
| Purchase Agreements | 7 | `purchase_agreements/` |
| Window Stickers | 5 | `window_stickers/` |
| Registrations | 3 | `registrations/` |
| WeChat Screenshots | 3 | `wechat/` |
| VIN Photos | 2 | `vin_photos/` |
| Dealer Worksheets | 2 | `dealer_worksheets/` |
| **Total** | **22** | |

---

## Purchase Agreements (7)

| Filename | Format | Expected Fields | OCR Difficulty | Notes |
|----------|--------|-----------------|----------------|-------|
| `pa_001_toyota_camry.pdf` | PDF | VIN, YMM, Name, ZIP, Lienholder | Easy | Standard dealer PDF, clean text, single page |
| `pa_002_honda_civic.pdf` | PDF | VIN, YMM, Name, ZIP, Lienholder | Easy | Multi-page contract, key fields on page 1 |
| `pa_003_bmw_x5.pdf` | PDF | VIN, YMM, Name, ZIP, Lienholder | Medium | Dense two-column layout, VIN in header box |
| `pa_004_tesla_model3.jpg` | JPG | VIN, YMM, Name, ZIP | Medium | Image scan of Tesla order agreement, no lienholder (cash) |
| `pa_005_lexus_rx350.pdf` | PDF | VIN, YMM, Name, ZIP, Lienholder | Hard | Scanned fax copy, slightly rotated, low contrast simulation |
| `pa_006_nissan_altima.jpg` | JPG | VIN, YMM, Name, ZIP, Lienholder | Easy | Phone photo of dealer printout, straight shot |
| `pa_007_hyundai_elantra.pdf` | PDF | VIN, YMM, Name, ZIP, Lienholder | Medium | Standard contract, clean fields |

---

## Window Stickers (5)

| Filename | Format | Expected Fields | OCR Difficulty | Notes |
|----------|--------|-----------------|----------------|-------|
| `ws_001_toyota_rav4.pdf` | PDF | VIN, YMM | Easy | Standard Monroney label PDF, structured grid |
| `ws_002_ford_f150.jpg` | JPG | VIN, YMM | Easy | Window sticker photo, slight glare simulation on top |
| `ws_003_honda_crv.jpg` | JPG | VIN, YMM | Medium | Through-window distortion simulation |
| `ws_004_chevy_equinox.png` | PNG | VIN, YMM | Easy | Screenshot from dealer inventory system |
| `ws_005_bmw_330i.pdf` | PDF | VIN, YMM | Medium | Dense feature list, VIN at bottom |

**Note:** Window stickers do not contain customer name or garaging ZIP — those come from intake form. Broker knows this.

---

## Registrations (3)

| Filename | Format | Expected Fields | OCR Difficulty | Notes |
|----------|--------|-----------------|----------------|-------|
| `reg_001_ca_dmv.jpg` | JPG | VIN, YMM, Name, ZIP | Easy | California DMV registration card, standard format |
| `reg_002_ca_dmv.pdf` | PDF | VIN, YMM, Name, ZIP | Medium | PDF of CA temp registration, lighter text |
| `reg_003_ca_temp.jpg` | JPG | VIN, YMM, Name, ZIP | Hard | Temporary operating permit, simulated blur |

---

## WeChat Screenshots (3)

| Filename | Format | Expected Fields | OCR Difficulty | Notes |
|----------|--------|-----------------|----------------|-------|
| `wechat_001_vin_message.jpg` | JPG | VIN, partial YMM, Name | Medium | Customer typed VIN in WeChat message thread |
| `wechat_002_delivery_date.png` | PNG | Partial YMM, ZIP | Medium | Delivery date confirmation thread, no VIN visible |
| `wechat_003_zip_confirmation.jpg` | JPG | ZIP only | Easy | Single-purpose message: customer confirms garaging ZIP |

---

## VIN Photos (2)

| Filename | Format | Expected Fields | OCR Difficulty | Notes |
|----------|--------|-----------------|----------------|-------|
| `vin_001_dashboard.jpg` | JPG | VIN | Medium | Dashboard VIN plate through windshield, typical iPhone |
| `vin_002_door_jamb.jpg` | JPG | VIN | Hard | Door jamb sticker, simulated dark lighting |

---

## Dealer Worksheets (2)

| Filename | Format | Expected Fields | OCR Difficulty | Notes |
|----------|--------|-----------------|----------------|-------|
| `dw_001_finance_worksheet.pdf` | PDF | VIN, YMM, Name, ZIP, Lienholder | Easy | Finance dept worksheet, all fields present |
| `dw_002_buyers_order.pdf` | PDF | VIN, YMM, Name, ZIP, Lienholder | Medium | Buyer's order (note: trade-in section present) |

---

## OCR Difficulty Distribution

| Difficulty | Count | % |
|------------|-------|---|
| Easy | 9 | 41% |
| Medium | 10 | 45% |
| Hard | 3 | 14% |

---

## VIN Coverage

All VINs in this corpus are 17-character strings following NHTSA/ISO 3779 format.
No I, O, or Q characters. All VINs are test-only values (not real registered vehicles).

| VIN | Vehicle | Used in |
|-----|---------|---------|
| 4T1BF1FK5CU512345 | 2023 Toyota Camry | pa_001, reg_001, dw_002 |
| 2HGFC2F69MH123456 | 2021 Honda Civic | pa_002, reg_002 |
| 5UXCR6C06L9B12345 | 2020 BMW X5 | pa_003, reg_003 |
| 5YJ3E1EA8MF123456 | 2021 Tesla Model 3 | pa_004, wechat_001 |
| 2T2BZMCA8KC123456 | 2019 Lexus RX 350 | pa_005 |
| 1N4BL4BV2KC123456 | 2019 Nissan Altima | pa_006 |
| KMHD84LF8KU123456 | 2019 Hyundai Elantra | pa_007, dw_001 |
| 4T3P6RFV5MU123456 | 2021 Toyota RAV4 | ws_001 |
| 1FTFW1ET5MKD12345 | 2021 Ford F-150 | ws_002 |
| 7FARW2H57ME123456 | 2021 Honda CR-V | ws_003 |
| 2GNAXKEV4M6123456 | 2021 Chevrolet Equinox | ws_004 |
| 3MW5R7J07N8C12345 | 2022 BMW 330i | ws_005 |
| 4T1BF1FK5CU512345 | 2023 Toyota Camry | vin_001 |
| 5UXCR6C06L9B12345 | 2020 BMW X5 | vin_002 |

---

*Inventory auto-generated by `scripts/generate_p16_corpus.py` on 2026-06-17.*  
*Accuracy evaluation: `scripts/run_p16_accuracy_eval.py`*  
*Ground truth: `docs/p16/P16_GROUND_TRUTH.md`*
