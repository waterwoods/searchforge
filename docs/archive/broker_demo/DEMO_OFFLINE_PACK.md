# Demo Offline Pack

Offline fallback for the broker demo when the backend is down or slow. Pre-saved answers for the 5 sample questions are loaded from `ui/src/assets/demo_fallback.json` so the demo can still run without a live backend.

## How to Generate the Fallback

**Recommended:** Run `bash scripts/demo_quick_validate.sh` with the backend up. On validation PASS, it automatically runs `snapshot_demo_answers.py` and updates `demo_fallback.json`. One command = validate + refresh offline pack.

**Manual refresh:**

1. **Start the backend** (with Qdrant Cloud and translation enabled):
   ```bash
   bash scripts/run_demo_local.sh
   ```
   Or manually:
   ```bash
   set -a; source .env.cloudrun; set +a
   TRANSLATION_ENABLED=1 TRANSLATION_PROVIDER=argos python3 -m uvicorn services.fiqa_api.app_main:app --host 0.0.0.0 --port 8001
   ```

2. **Run the snapshot script**:
   ```bash
   python3 scripts/snapshot_demo_answers.py
   ```

3. The script POSTs the 5 broker questions to `http://127.0.0.1:8001/api/query` and saves the responses to `ui/src/assets/demo_fallback.json`.

4. If the backend is not reachable, the script exits with a clear error message.

## When the Fallback Is Used

- **Backend health check fails**: The UI shows an "Offline Demo (Fallback)" banner.
- **Request errors**: If a query fails (e.g. network error), the fallback banner appears.
- **Behavior**: Clicking any of the 5 sample questions loads answers from `demo_fallback.json` instead of calling the API. Citations (domain badge, URL, snippet) are displayed the same as in normal mode.

## Refresh Offline Pack Button

A "Refresh Offline Pack" button (developer feature) appears in the offline banner. Clicking it shows a modal with instructions:

```
Run: python3 scripts/snapshot_demo_answers.py (backend must be running)
```

The browser does not run commands; the user must run the script manually.

## Acceptance Checklist

- [ ] `ui/src/assets/demo_fallback.json` exists and has 5 items
- [ ] Each item has `question`, `answer`, and `sources` (array of `{ domain, url, snippet }`)
- [ ] When backend is stopped, the "Offline Demo (Fallback)" banner appears
- [ ] Clicking the 5 sample questions in fallback mode loads answers without API calls
- [ ] Citations display correctly (domain badge, clickable URL, snippet)
- [ ] "Refresh Offline Pack" button shows the instructions modal
