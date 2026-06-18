# P16 OCR Kill Test Matrix V2

20 realistic extraction tests to stress-test Gemini Flash 2.5 before the Chen Kui pilot.

| Test ID | Scenario | Input Files | Expected Packet Output | Risk Level | Pass Criteria |
|---|---|---|---|---|---|
| 01 | Clean Native PDF | `purchase_agreement_01.pdf` | Full packet (VIN, YMM, Name, Address, Lienholder) | Low | 100% accurate extraction of all fields. |
| 02 | Blurry VIN Dashboard | `vin_photo_01.jpg` | VIN only | High | Correctly extracts 17-char VIN despite glare. |
| 03 | Mixed Language Chat | `wechat_screenshot_01.jpg` | VIN, Name | High | Ignores Chinese context, extracts English/Alphanumeric VIN and Name. |
| 04 | Trade-in + New Vehicle | `purchase_agreement_09.pdf` | New Vehicle VIN, YMM | High | Correctly identifies New Vehicle vs Trade-in Vehicle. Flags multiple VINs if unsure. |
| 05 | Window Sticker Only | `window_sticker_02.jpg` | VIN, YMM | Medium | Extracts VIN and YMM despite glass reflection. |
| 06 | Missing VIN | `wechat_screenshot_02.png` | YMM, Name (No VIN) | Low | Gracefully returns null for VIN, extracts YMM. |
| 07 | Folded Contract | `purchase_agreement_06.jpg` | VIN, YMM, Name, Address | High | Extracts across the fold without dropping characters. |
| 08 | Handwritten Notes | `purchase_agreement_10.jpg` | VIN, YMM, Name, Address | Medium | Ignores or correctly parses handwritten margin notes. |
| 09 | HEIC iPhone Photo | `purchase_agreement_02.heic` | VIN, YMM, Name, Address | Medium | System successfully converts/processes HEIC and extracts fields. |
| 10 | Multi-page PDF | `purchase_agreement_05.pdf` | Full packet | Low | Finds VIN on page 1, Lienholder on page 3. |
| 11 | Cropped Screenshot | `window_sticker_05.png` | VIN, YMM | Medium | Extracts partial data without hallucinating missing parts. |
| 12 | Ripped Registration | `registration_03.jpg` | VIN, YMM, Name | High | Extracts available fields, returns null for missing ZIP. |
| 13 | Dealer Email Forward | `dealer_email_01.pdf` | VIN, YMM, Name, Lienholder | Low | Parses unstructured email body text correctly. |
| 14 | Door Jamb Sticker | `vin_photo_02.jpg` | VIN, YMM | Medium | Extracts VIN and sometimes Year/Make from barcode label. |
| 15 | Old Insurance Card | `insurance_card_02.jpg` | VIN, YMM, Name | Low | Extracts vehicle info, ignores expired effective dates. |
| 16 | Conflicting Names | `purchase_agreement_04.png` | Co-buyers Names | Medium | Extracts both buyer and co-buyer names. |
| 17 | PO Box Address | `registration_01.jpg` | Name, PO Box ZIP | Low | Extracts PO Box as valid garaging address/ZIP. |
| 18 | Low Contrast Scan | `purchase_agreement_04.png` | VIN, YMM, Name | High | Successfully reads faded text. |
| 19 | Out of State Reg | `registration_04.jpg` | VIN, YMM, Name, Address | Medium | Extracts correctly despite non-CA format. |
| 20 | Multiple Screenshots | `wechat_screenshot_01.jpg`, `wechat_screenshot_03.jpg` | VIN, Name, Address | High | Merges data from two separate images into one packet. |
