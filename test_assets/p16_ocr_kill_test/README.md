# P16 OCR Kill Test — Test Assets

**Purpose:** Real-world documents for testing AI extraction → 8 core add-car fields.

---

## How to add test files

Place files into numbered subfolders. Each subfolder = one test case.

```
test_assets/p16_ocr_kill_test/
  case_001/   ← one "customer packet" (1 or more files)
  case_002/
  case_003/
  ...
```

If you drop files directly in the root folder (no subfolders), all root files become `case_001`.

---

## Supported file types

| Type | Extension |
|------|-----------|
| Photos | .jpg, .jpeg, .png |
| Documents | .pdf |

---

## Ideal test documents (10 real-world examples)

| Case | Document | Notes |
|------|----------|-------|
| case_001 | Dealer paperwork | Bill of sale or window sticker |
| case_002 | Purchase contract | Shows buyer name, VIN, delivery date |
| case_003 | VIN photo | Close-up of dashboard or door frame VIN |
| case_004 | Vehicle registration | DMV registration card |
| case_005 | Insurance card | Current policy card |
| case_006 | Dealer email screenshot | Forwarded email with vehicle details |
| case_007 | Mixed multi-page PDF | Multiple document types merged |
| case_008 | Blurry photo | Low-quality image (stress test) |
| case_009 | Unrelated document | Non-automotive document (should be flagged) |
| case_010 | Second vehicle document | Two cars in one packet (should be flagged) |

---

## Status: NO FILES YET

No real documents are currently in this folder.

When you run the test with no files, the runner will:
- Report 0 cases processed
- Print clear instructions
- Exit gracefully with code 0

**To run the test (dry-run mode):**
```bash
python scripts/run_p16_ocr_kill_test.py --input-dir test_assets/p16_ocr_kill_test --provider dry_run
```

**To run with real AI extraction:**
```bash
# Set your API key first:
export OPENAI_API_KEY=sk-...
python scripts/run_p16_ocr_kill_test.py --input-dir test_assets/p16_ocr_kill_test --provider auto
```

---

## Privacy note

Do NOT commit real customer documents to git.
Redact or use anonymized samples only.

Add to `.gitignore` if needed:
```
test_assets/p16_ocr_kill_test/**/*.pdf
test_assets/p16_ocr_kill_test/**/*.jpg
test_assets/p16_ocr_kill_test/**/*.jpeg
test_assets/p16_ocr_kill_test/**/*.png
```
