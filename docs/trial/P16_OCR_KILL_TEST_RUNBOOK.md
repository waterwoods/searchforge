# P16 OCR Kill Test — Runbook

**Purpose:** Operational runbook for running and interpreting the P16 OCR Kill Test.  
**Owner:** Founder / Andy  
**Status:** Kill Test — not a production feature  
**Related sprint:** P16 Add-Car Packet Builder feasibility

---

## What this test does

Takes real insurance/car purchase documents → AI vision extraction → 8 core add-car fields → evaluates packet readiness.

It answers: *Is upload-first extraction strong enough to justify building Add-Car Packet Builder?*

---

## Quick Start (5 minutes)

### Step 1 — Add test documents

```bash
# Create case subfolders
mkdir -p test_assets/p16_ocr_kill_test/case_001
mkdir -p test_assets/p16_ocr_kill_test/case_002

# Add documents to each case folder
cp dealer_paperwork.pdf test_assets/p16_ocr_kill_test/case_001/
cp vin_photo.jpg test_assets/p16_ocr_kill_test/case_001/
cp purchase_contract.pdf test_assets/p16_ocr_kill_test/case_002/
```

### Step 2 — Set API key

```bash
export OPENAI_API_KEY=sk-...
```

### Step 3 — Run

```bash
python scripts/run_p16_ocr_kill_test.py --input-dir test_assets/p16_ocr_kill_test --provider auto
```

### Step 4 — Read results

```
artifacts/p16_ocr_kill_test/results.json   # full extraction data
artifacts/p16_ocr_kill_test/results.csv    # spreadsheet-friendly
docs/trial/P16_OCR_KILL_TEST_REPORT.md     # GO / CONDITIONAL GO / NO GO verdict
```

---

## File / Folder Layout

```
test_assets/p16_ocr_kill_test/
  README.md                  ← instructions for adding files
  case_001/                  ← one customer's documents
    dealer_paperwork.pdf
    vin_photo.jpg
  case_002/
    purchase_contract.pdf
  ...

scripts/
  run_p16_ocr_kill_test.py   ← main runner

services/fiqa_api/ocr_kill_test/
  __init__.py
  schema.py                  ← field definitions and data classes
  normalizers.py             ← VIN/phone/date/zip normalization
  extractor.py               ← OpenAI / Gemini / dry_run adapters
  packet_builder.py          ← merge + readiness + draft generation
  reporter.py                ← JSON / CSV / Markdown report

artifacts/p16_ocr_kill_test/
  results.json               ← full results (auto-created)
  results.csv                ← field extraction table (auto-created)

docs/trial/
  P16_OCR_KILL_TEST_RUNBOOK.md       ← this file
  P16_OCR_KILL_TEST_REPORT.md        ← auto-generated after run
  P16_OCR_KILL_TEST_CERTIFICATION.md ← final GO/NO GO decision
```

---

## CLI Reference

```bash
python scripts/run_p16_ocr_kill_test.py \
  --input-dir  test_assets/p16_ocr_kill_test \   # where your files are
  --provider   auto \                             # openai | gemini | dry_run | auto
  --output-dir artifacts/p16_ocr_kill_test \      # where JSON/CSV go
  --report-path docs/trial/P16_OCR_KILL_TEST_REPORT.md \
  --verbose                                       # print per-file detail
```

### Provider options

| Provider | Env required | Notes |
|----------|-------------|-------|
| `auto` | — | Picks best available |
| `openai` | `OPENAI_API_KEY` | GPT-4o vision. Best quality. ~$0.005/image |
| `gemini` | `GEMINI_API_KEY` or `GOOGLE_API_KEY` | Gemini Flash. Cheaper. ~$0.0005/image |
| `dry_run` | — | No API calls. Tests pipeline only. |

---

## 8 Core Fields

| Field | Normalization | Notes |
|-------|-------------|-------|
| `customer_name` | None | Full legal name |
| `phone` | 10-digit US | Strip formatting |
| `vin` | Uppercase 17-char | Must be A-Z/0-9, no I/O/Q |
| `year` | 4-digit | 1950–2035 range |
| `make_model` | None | Combined field for MVP |
| `garaging_zip` | 5-digit | Leading 5 of ZIP+4 |
| `primary_driver` | None | May differ from buyer |
| `delivery_or_effective_date` | YYYY-MM-DD | ISO format |

---

## Packet Readiness Rules

A packet is `packet_ready = true` only when:

1. All 7 required fields present: `customer_name`, `phone`, `vin`, `year`, `make_model`, `garaging_zip`, `delivery_or_effective_date`
2. No conflicting VIN, year, or make/model values
3. No second vehicle detected

`primary_driver` is surfaced as advisory — missing value does not block readiness.

---

## Pass/Fail Decision Rules

| Verdict | Criteria |
|---------|---------|
| **GO** | ≥7/10 cases packet-ready, VIN extraction ≥90%, no invented fields |
| **CONDITIONAL GO** | 5–6/10 cases packet-ready, VIN usable but inconsistent |
| **NO GO** | <5/10 cases packet-ready, frequent hallucination, or undetectable conflicts |

If fewer than 10 cases are tested, verdict is marked **PROVISIONAL**.

---

## Interpreting Results

### `needs_confirmation: true`

The model is uncertain about this value. Wu Xiaojie should verify before sending to carrier.

### `conflicts`

Two different values were found for the same field across documents. **Do not choose silently.** Ask the customer.

### `unrelated_documents`

The model flagged one or more files as unrelated to auto insurance. Remove them from the packet.

### `second_vehicle_detected: true`

Two vehicles are present in the packet. Split into two separate cases before quoting.

---

## Cost Estimates

| Provider | Per image | 10 cases × 3 files | Notes |
|----------|-----------|-------------------|-------|
| OpenAI GPT-4o | ~$0.005 | ~$0.15 | High quality |
| Gemini Flash | ~$0.0005 | ~$0.015 | Volume pricing |
| dry_run | $0.00 | $0.00 | Pipeline test |

---

## Privacy / Security

- **Do NOT commit real customer documents to git.**
- Redact PII from any committed samples.
- Test documents live only in `test_assets/p16_ocr_kill_test/` — not in `services/` or `docs/`.
- Images are sent to OpenAI/Gemini API. Use only documents the customer consented to share.

---

## Troubleshooting

### "No documents found"

```bash
# Check the folder
ls -la test_assets/p16_ocr_kill_test/
# Files must be in case_XXX subfolders or directly in root
```

### "Could not render PDF to images"

The PDF conversion requires `pymupdf` or `pdf2image`:
```bash
pip install pymupdf      # recommended
# or
pip install pdf2image    # needs poppler-utils (apt install poppler-utils)
```

### "Failed to initialize provider openai"

```bash
echo $OPENAI_API_KEY    # should be sk-...
# If empty: export OPENAI_API_KEY=sk-your-key-here
```

### Dry-run shows all fields empty

This is expected — dry_run does not call any API. It validates the pipeline flow only.

---

## After the test

1. Read `docs/trial/P16_OCR_KILL_TEST_REPORT.md` for the automated verdict
2. Read `docs/trial/P16_OCR_KILL_TEST_CERTIFICATION.md` for the GO/NO GO decision and rationale
3. If GO or CONDITIONAL GO: proceed to sprint planning for Add-Car Packet Builder MVP
4. If NO GO: document failure modes and pivot (manual form, structured upload, etc.)

---

*Kill test — not a production deployment. See `AGENTS.md` scope guardrail.*
