# Step 3 API Translation Fix Report

## Root Cause Analysis

The API translation fields (`translation_applied`, `detected_lang`, `question_used`) were returning `null` in the API response due to:

1. **Variable Scope Issue**: Translation variables were initialized in the main `try` block, but error handlers in `except` blocks were using `locals()` checks that failed when variables were `None` rather than non-existent.

2. **Error Response Path**: When a collection is not found (e.g., `DATASET_MISSING` error), the error handler constructs a response but the translation variables might not be accessible or might be `None`.

3. **Backend Code Reload**: The backend might not be using the latest code despite restarts, possibly due to Python bytecode caching or `--reload` flag issues.

## Changes Made

### 1. Environment Variable Loading (`app_main.py`)
- Moved `load_dotenv()` to the very top of the file (before any imports)
- Added explicit log line: `print("[env] loaded .env.cloudrun, TRANSLATION_ENABLED=", os.getenv("TRANSLATION_ENABLED"))`

### 2. Translation Module (`services/fiqa_api/utils/translation.py`)
- Refactored `is_translation_available()` to read environment variables at runtime (not at import time)
- Added `translation_debug_state()` function for debugging
- Fixed `argostranslate` API usage (`get_translation_from_codes` instead of non-existent APIs)

### 3. Query Route (`services/fiqa_api/routes/query.py`)
- **Variable Initialization**: Initialize all translation variables at the very beginning of `_execute_query` (lines 312-320):
  ```python
  question_original = cleaned_question
  question_used = cleaned_question
  translation_applied = False
  detected_lang = "unknown"  # Initialize with default, not None
  translation_error = None
  ```
- **Language Detection**: Always detect language, even if translation is not enabled
- **Translation Logic**: Improved `translation_mode` handling to correctly parse request parameters
- **Payload Construction**: Ensure all translation fields are never `None`:
  ```python
  q_orig = question_original if question_original is not None else cleaned_question
  q_used_val = question_used if question_used is not None else q_orig
  trans_applied_val = bool(translation_applied) if translation_applied is not None else False
  det_lang_val = str(detected_lang) if detected_lang is not None and detected_lang != "" else "unknown"
  ```
- **Error Handler**: Updated error response construction to include translation fields with explicit defaults

### 4. Debug Endpoint
- Added `GET /api/debug/translation` endpoint to check translation system state
- Returns `translation_debug_state()` plus `detect_lang` tests

## Current Status

### Backend
- ✅ Code changes implemented
- ✅ Environment variable loading fixed
- ✅ Translation module refactored
- ✅ Query route updated with translation fields
- ⚠️  Backend needs full restart to pick up changes

### API Response
- ❌ Translation fields still returning `null` in error responses
- ⚠️  Issue: Variables might not be accessible in error handler scope
- ⚠️  Issue: Backend might not be using latest code

## Next Steps

1. **Force Backend Restart**:
   ```bash
   pkill -9 -f uvicorn
   lsof -ti :8000 | xargs kill -9
   set -a; source .env.cloudrun; set +a
   export TRANSLATION_ENABLED=1
   export TRANSLATION_PROVIDER=argos
   python3 -m uvicorn services.fiqa_api.app_main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Clear Python Cache**:
   ```bash
   find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
   find . -name "*.pyc" -delete
   ```

3. **Test with Valid Collection**:
   - Use `collection: "auto_insurance_v2_clean"` (not `"auto_insurance"`)
   - This will avoid the `DATASET_MISSING` error and test the main success path

4. **Verify Translation State**:
   ```bash
   curl -s http://localhost:8000/api/debug/translation | jq
   ```

## Acceptance Criteria

- [ ] `/api/debug/translation` returns `enabled_env=1`, `argos_import_ok=true`, `argos_has_zh_en=true`
- [ ] `/api/query` for Chinese + `translation_mode=auto` returns:
  - `detected_lang="zh"`
  - `translation_applied=true`
  - `question_used` is English (translated)
  - At least one source has `text_zh` or `translations.zh.text` (if `TRANSLATE_SOURCES_TO_ZH=1`)
- [ ] Smoke test `scripts/smoke_test_api_translation.sh` PASSES

## Known Issues

1. **Debug Endpoint 404**: `/api/debug/translation` returns 404, suggesting router mounting issue
2. **Error Response Fields**: Translation fields are `null` in error responses (e.g., `DATASET_MISSING`)
3. **Backend Reload**: `--reload` flag might not be picking up all code changes

## Files Modified

- `services/fiqa_api/app_main.py`: Environment variable loading
- `services/fiqa_api/utils/translation.py`: Runtime environment variable reading, debug state
- `services/fiqa_api/routes/query.py`: Translation variable initialization, payload construction, error handling
- `scripts/smoke_test_api_translation.sh`: Smoke test script (already exists)

## How to Run

1. **Start Backend**:
   ```bash
   ./scripts/dev_local.sh
   # OR
   set -a; source .env.cloudrun; set +a
   export TRANSLATION_ENABLED=1
   export TRANSLATION_PROVIDER=argos
   python3 -m uvicorn services.fiqa_api.app_main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Run Smoke Test**:
   ```bash
   ./scripts/smoke_test_api_translation.sh
   ```

3. **Manual Test**:
   ```bash
   curl -s -X POST http://localhost:8000/api/query \
     -H "Content-Type: application/json" \
     -d '{"question":"加州最低汽车保险要求是什么？","top_k":5,"translation_mode":"auto","collection":"auto_insurance_v2_clean"}' | jq
   ```
