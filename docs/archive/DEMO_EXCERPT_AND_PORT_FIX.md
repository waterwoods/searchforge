# Demo Excerpt and Port Fix Report

**Date:** 2026-02-21  
**Scope:** Part A (Backend snippet), Part B (Frontend proxy-only), Part C (Acceptance)

---

## Summary

1. **Backend:** Added `snippet` field to every source in `/api/query` response. Snippet is always non-empty (first 320 chars of text, or `title — domain` fallback).
2. **Frontend:** Demo page now uses relative paths only (`/api/query`, `/healthz`). Vite proxy handles port routing; no hardcoded 8000/8001 in UI.
3. **Config:** `API_BASE_URL` defaults to `""` when `VITE_API_BASE_URL` is unset, so relative paths hit the proxy in dev.

---

## Part A — Backend Changes

### Files Modified

| File | Change |
|------|--------|
| `services/fiqa_api/routes/query.py` | Added `_build_snippet()`, `_domain_from_url()`. Each source now includes `snippet`, `url`, `domain`. |
| `services/fiqa_api/services/search_core.py` | Increased text truncation from 200 to 400 chars to support 320-char snippets. |

### Snippet Logic

- **Prefer:** `text_zh` if present, else `text`
- **If text exists:** First 320 characters (newlines stripped, whitespace collapsed)
- **If no text:** `f"{title} — {domain}"`
- **Backward compatible:** `text` and `text_zh` remain unchanged

### Response Schema (per source)

```json
{
  "doc_id": "...",
  "title": "...",
  "text": "...",
  "source_url": "...",
  "url": "...",
  "domain": "...",
  "snippet": "...",
  "score": 0.0
}
```

---

## Part B — Frontend Changes

### Files Modified

| File | Change |
|------|--------|
| `ui/src/api/config.ts` | Removed `DEFAULT_BASE_URL = "http://127.0.0.1:8001"`. Default is now `""` when `VITE_API_BASE_URL` unset. |
| `ui/src/pages/DemoPage.tsx` | All API calls use `/api/query` and `/healthz` (relative). Excerpt uses `snippet` first, then text fallbacks. Removed `API_BASE_URL` import. |

### Vite Proxy (unchanged, verified)

```js
// ui/vite.config.ts
'/api': { target: 'http://127.0.0.1:8001', ... },
'/healthz': { target: 'http://127.0.0.1:8001', ... },
```

### Excerpt Display Order

1. `source.snippet` (from backend)
2. `source.text_zh`
3. `source.translations?.zh?.text`
4. `source.text`
5. `"No excerpt."` (fallback only if all above empty)

---

## Part C — Acceptance Steps

### 1. Start Backend

```bash
cd /home/andy/searchforge
set -a; source .env.cloudrun; set +a
TRANSLATION_ENABLED=1 TRANSLATION_PROVIDER=argos python3 -m uvicorn services.fiqa_api.app_main:app --host 0.0.0.0 --port 8001
```

### 2. Start UI

```bash
cd ui && npm run dev
```

### 3. Open Demo

- URL: http://localhost:5173/demo

### 4. Verification Checklist

- [ ] Status bar shows **Connected** and **Latency**
- [ ] Click a scenario question (e.g. 新车投保/最低要求 → 我刚买了新车...)
- [ ] Citations show GOV/INSURER badge
- [ ] "Show excerpt" reveals a non-empty snippet for at least 3 citations
- [ ] No console red errors

### 5. Console Notes (Expected)

- No CORS errors (requests go to same origin via proxy)
- No 404s for `/api/query` or `/healthz`
- Response `sources[].snippet` present for each item

---

## Evidence

- **Build:** `npm run build` succeeds (exit 0)
- **Backend:** `snippet` added in both proxy path (`_item_to_source`) and main search path
- **Frontend:** No hardcoded URLs in DemoPage; config.ts uses `""` default

---

## Follow-up

- Other pages (JobHunter, Mortgage, etc.) use `API_BASE_URL`; when empty they use relative paths and thus proxy. For production, set `VITE_API_BASE_URL` to the Cloud Run URL.
