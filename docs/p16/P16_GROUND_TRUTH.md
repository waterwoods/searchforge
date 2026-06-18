# P16 Ground Truth Table

**Created:** 2026-06-17  
**Sprint:** P16 Evidence Phase  
**Authority:** This is the manually verified expected-value table for the P16 OCR accuracy evaluation.

The values below are exactly what was embedded in each corpus document by `scripts/generate_p16_corpus.py`.  
The evaluation runner compares Gemini Flash 2.5 extraction output against these values.

**Empty string (`""`) = field is genuinely not present in the document. Extraction of `""` for that field is CORRECT.**

---

## Minimum Required Fields for Evaluation

- **VIN** — 17-character vehicle identification number
- **Year** — 4-digit model year
- **Make/Model** — vehicle make and model string
- **Name** — customer/buyer name (where present)
- **ZIP** — garaging ZIP code (where present)
- **Lienholder** — financing institution (where present)

---

## Purchase Agreements

| Filename | VIN | Year | Make/Model | Name | ZIP | Lienholder |
|----------|-----|------|------------|------|-----|------------|
| `pa_001_toyota_camry.pdf` | 4T1BF1FK5CU512345 | 2023 | Toyota Camry | Wei Zhang | 91801 | Toyota Financial Services |
| `pa_002_honda_civic.pdf` | 2HGFC2F69MH123456 | 2021 | Honda Civic | Mei Lin Chen | 91776 | Honda Financial Services |
| `pa_003_bmw_x5.pdf` | 5UXCR6C06L9B12345 | 2020 | BMW X5 | Jianming Liu | 91011 | BMW Financial Services |
| `pa_004_tesla_model3.jpg` | 5YJ3E1EA8MF123456 | 2021 | Tesla Model 3 | Xiaohui Wang | 91030 | *(none — cash purchase)* |
| `pa_005_lexus_rx350.pdf` | 2T2BZMCA8KC123456 | 2019 | Lexus RX 350 | Hongying Zhao | 91801 | Lexus Financial Services |
| `pa_006_nissan_altima.jpg` | 1N4BL4BV2KC123456 | 2019 | Nissan Altima | Fang Xu | 91702 | Nissan Motor Acceptance |
| `pa_007_hyundai_elantra.pdf` | KMHD84LF8KU123456 | 2019 | Hyundai Elantra | Yong Kim | 91754 | Hyundai Motor Finance |

---

## Window Stickers

**Note:** Window stickers do not contain buyer name or garaging ZIP. These are not extraction failures — they are expected empty.

| Filename | VIN | Year | Make/Model | Name | ZIP | Lienholder |
|----------|-----|------|------------|------|-----|------------|
| `ws_001_toyota_rav4.pdf` | 4T3P6RFV5MU123456 | 2021 | Toyota RAV4 | *(not present)* | *(not present)* | *(not present)* |
| `ws_002_ford_f150.jpg` | 1FTFW1ET5MKD12345 | 2021 | Ford F-150 | *(not present)* | *(not present)* | *(not present)* |
| `ws_003_honda_crv.jpg` | 7FARW2H57ME123456 | 2021 | Honda CR-V | *(not present)* | *(not present)* | *(not present)* |
| `ws_004_chevy_equinox.png` | 2GNAXKEV4M6123456 | 2021 | Chevrolet Equinox | *(not present)* | *(not present)* | *(not present)* |
| `ws_005_bmw_330i.pdf` | 3MW5R7J07N8C12345 | 2022 | BMW 330i | *(not present)* | *(not present)* | *(not present)* |

---

## Registrations

| Filename | VIN | Year | Make/Model | Name | ZIP | Lienholder |
|----------|-----|------|------------|------|-----|------------|
| `reg_001_ca_dmv.jpg` | 4T1BF1FK5CU512345 | 2023 | Toyota Camry | Wei Zhang | 91801 | *(not on reg card)* |
| `reg_002_ca_dmv.pdf` | 2HGFC2F69MH123456 | 2021 | Honda Civic | Mei Lin Chen | 91776 | *(not on reg card)* |
| `reg_003_ca_temp.jpg` | 5UXCR6C06L9B12345 | 2020 | BMW X5 | Jianming Liu | 91011 | *(not on reg card)* |

---

## WeChat Screenshots

| Filename | VIN | Year | Make/Model | Name | ZIP | Lienholder |
|----------|-----|------|------------|------|-----|------------|
| `wechat_001_vin_message.jpg` | 5YJ3E1EA8MF123456 | 2021 | Tesla Model 3 | Xiaohui Wang | 91030 | *(not present)* |
| `wechat_002_delivery_date.png` | *(not present)* | 2019 | Nissan Altima | Fang Xu | 91702 | *(not present)* |
| `wechat_003_zip_confirmation.jpg` | *(not present)* | *(not present)* | *(not present)* | Hongying Zhao | 91801 | *(not present)* |

---

## VIN Photos

**Note:** VIN photos contain only the VIN plate. No name, ZIP, or YMM expected.

| Filename | VIN | Year | Make/Model | Name | ZIP | Lienholder |
|----------|-----|------|------------|------|-----|------------|
| `vin_001_dashboard.jpg` | 4T1BF1FK5CU512345 | *(not present)* | *(not present)* | *(not present)* | *(not present)* | *(not present)* |
| `vin_002_door_jamb.jpg` | 5UXCR6C06L9B12345 | *(not present)* | *(not present)* | *(not present)* | *(not present)* | *(not present)* |

---

## Dealer Worksheets

| Filename | VIN | Year | Make/Model | Name | ZIP | Lienholder |
|----------|-----|------|------------|------|-----|------------|
| `dw_001_finance_worksheet.pdf` | KMHD84LF8KU123456 | 2019 | Hyundai Elantra | Yong Kim | 91754 | Hyundai Motor Finance |
| `dw_002_buyers_order.pdf` | 4T1BF1FK5CU512345 | 2023 | Toyota Camry | Wei Zhang | 91801 | Toyota Financial Services |

---

## Evaluation Rules

### VIN Match Criteria
- **PASS:** Extracted VIN matches ground truth exactly (17 characters, case-insensitive)
- **FAIL:** Wrong VIN, truncated VIN, or VIN with spaces/dashes inserted
- **SKIP:** Field genuinely not present in document (empty ground truth)

### YMM Match Criteria
- **Year PASS:** Extracted year is a 4-digit string equal to ground truth year
- **Make/Model PASS:** Extracted make/model string contains both the make and model (e.g., "Toyota Camry" in "2023 Toyota Camry LE" = PASS)
- **Partial credit:** Year correct but model wrong = 50% YMM score

### Name Match Criteria
- **PASS:** Extracted name contains all words from ground truth name (order-insensitive)
- **PARTIAL:** First name only, or last name only = 50%
- **FAIL:** Wrong name or completely absent when present in document

### ZIP Match Criteria
- **PASS:** Extracted ZIP is 5-digit string equal to ground truth ZIP
- **FAIL:** Wrong ZIP, partial ZIP, or ZIP absent when present in document

### Lienholder Match Criteria
- **PASS:** Extracted lienholder name contains the institution name (e.g., "Toyota Financial" in "Toyota Financial Services" = PASS)
- **SKIP:** Empty ground truth (field not present in document)

---

## Known Document Characteristics Affecting Extraction

| Doc | Known Challenge | Expected Impact |
|-----|-----------------|-----------------|
| `pa_005_lexus_rx350.pdf` | Simulated rotated/faded text | May reduce VIN confidence |
| `reg_003_ca_temp.jpg` | Simulated blur | May fail VIN, YMM |
| `vin_002_door_jamb.jpg` | Dark lighting simulation | May fail VIN |
| `wechat_002_delivery_date.png` | No VIN in document | VIN empty = correct |
| `wechat_003_zip_confirmation.jpg` | Only ZIP message | All fields empty except ZIP = correct |

---

*Ground truth authored 2026-06-17.*  
*Source documents generated by `scripts/generate_p16_corpus.py`.*  
*Accuracy runner: `scripts/run_p16_accuracy_eval.py`*
