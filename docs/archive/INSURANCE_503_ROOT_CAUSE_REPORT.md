# Insurance 503 Root Cause Report

**Generated**: 2026-03-06  
**Scope**: Backend failure causing `/api/query` → HTTP 503 in insurance demo

---

## 1. Exact backend error

| Field | Value |
|-------|-------|
| **HTTP status** | 503 Service Unavailable |
| **Response body** | `{"detail": {"ok": false, "error": "embedding_warming"}}` |
| **Root cause** | `EMBED_READY` is `False` because embedding warmup never completed |
| **Warmup failure** | Qdrant Cloud returns **404** on `GET /collections` → warmup raises → `EMBED_READY` never set |

### Backend log evidence

```
[CLIENTS] Initializing Qdrant client with URL: https://***.us-east4-0.gcp.cloud.qdrant.io
httpx: HTTP Request: GET https://...cloud.qdrant.io:6333/collections "HTTP/1.1 404 Not Found"
[ERROR] [CLIENTS] Qdrant client created but connection test failed: Unexpected Response: 404 (Not Found)
[ERROR] [WARMUP] Embedding warmup failed: Unexpected Response: 404 (Not Found)
[CLIENTS] Initialization complete: {'embedding_model': False, 'qdrant': False, ...}
```

Chain: **Qdrant 404** → warmup fails → `EMBED_READY` stays `False` → every `/api/query` returns 503.

---

## 2. Where it happens in code

| Location | File | Function/Line | What happens |
|----------|------|---------------|--------------|
| **503 raised** | `services/fiqa_api/routes/query.py` | Lines 586–593 | `if not EMBED_READY:` → `raise HTTPException(status_code=503, detail={"ok": False, "error": "embedding_warming"})` |
| **EMBED_READY never set** | `services/fiqa_api/clients.py` | `_warmup_embedding_background` (lines 700–722) | Warmup calls `get_qdrant_client().get_collections()`; Qdrant returns 404 → exception → warmup exits without setting `EMBED_READY = True` |
| **Qdrant 404** | `services/fiqa_api/clients.py` | `get_qdrant_client` (lines 283–290) | `_qdrant_client.get_collections()` → `UnexpectedResponse: 404 (Not Found)` |

### Exact path

```
POST /api/query
  → routes/query.py (FastAPI route)
  → line 587: if not EMBED_READY:  # True (never set)
  → line 590–593: raise HTTPException(status_code=503, detail={"ok": False, "error": "embedding_warming"})
```

---

## 3. Why frontend shows 503

| Step | What happens |
|------|--------------|
| 1 | Frontend at `localhost:5173/demo` calls `fetch('/api/query', {...})` (via Vite proxy → backend 8001) |
| 2 | Backend receives POST, checks `EMBED_READY`, finds it `False` |
| 3 | Backend raises `HTTPException(status_code=503, ...)` |
| 4 | FastAPI returns HTTP 503 with JSON body |
| 5 | Frontend gets `res.ok === false`, throws `Error(errData.error || 'HTTP 503')` |
| 6 | Console: "Failed to load resource: the server responded with a status of 503" |

`/healthz` returns 200 (backend process is up), but `/api/query` returns 503 because the query path explicitly checks `EMBED_READY` and raises 503 when it is false.

---

## 4. Confirmed cause

| Candidate | Status | Evidence |
|-----------|--------|----------|
| **Qdrant Cloud 404 / paused cluster** | ✅ **Confirmed** | Logs show `GET .../collections` → 404. Warmup depends on Qdrant ping; when it fails, `EMBED_READY` never flips. |
| **embedding_warming not finished** | ✅ **Consequence** | Warmup fails, so `EMBED_READY` stays false; that is exactly what triggers 503. |
| **Startup race / async init** | ❌ Not primary | Warmup runs in background; it fails due to Qdrant 404, not timing. |
| **Translation dependency failure** | ❌ Not involved | Translation is not in the warmup or query readiness path. |
| **Missing collection** | ❌ Not reached | Failure is at `get_collections()` (list collections), before any collection-specific call. |

---

## 5. Smallest fix

**Operational (no code change):** Wake the Qdrant Cloud cluster at [cloud.qdrant.io](https://cloud.qdrant.io). Free-tier clusters can be paused; waking it restores the API. Then restart the demo and re-run validation.

**Code option (if Qdrant must stay down):** Make the warmup vector ping non-blocking so `EMBED_READY` can be set even when Qdrant fails. Queries would then fail later at search time (Qdrant still needed), so this does not fix validation—only changes the error from `embedding_warming` to a search failure.

---

## 6. Fastest demo-safe workaround

**Use Offline mode.** The demo works without live retrieval.

### Option A: Stop backend (cleanest)

1. Stop the backend (Ctrl+C on `run_demo_local.sh` or kill the uvicorn process).
2. Keep the UI running (or restart with `npm run dev` in `ui/`).
3. Open http://localhost:5173/demo.
4. `fetch('/healthz')` fails → `backendConnected = false` → `useOfflineFallback = true`.
5. Click the 3 sample questions → they load from `demo_fallback.json` / `DEFAULT_FALLBACK_ITEMS`.
6. No 503; demo works.

### Option B: After first 503

1. Backend running, user clicks a sample question → 503.
2. Frontend sets `error` → `useOfflineFallback = true` (because `!!error && !response`).
3. Banner shows "Offline Demo (Fallback) — Click the 3 sample questions above to load pre-saved answers."
4. User clicks any of the 3 sample questions again → they load from fallback.
5. Demo works.

---

## 7. Offline mode can be forced cleanly

| Method | How |
|--------|-----|
| **Stop backend** | `backendConnected = false` → `useOfflineFallback = true` from first load. Sample questions use fallback immediately. |
| **After 503** | First query fails; `useOfflineFallback` becomes true; next click on sample questions uses fallback. |

Fallback data: `ui/src/assets/demo_fallback.json` (3 items) or `DEFAULT_FALLBACK_ITEMS` in `DemoPage.tsx` if the file is empty.

---

## 8. Next 5 actions

| # | Action | Owner |
|---|--------|-------|
| 1 | **Demo now**: Stop backend, open http://localhost:5173/demo, click the 3 sample questions | Andy |
| 2 | Wake Qdrant Cloud cluster at cloud.qdrant.io (if paused) | Andy |
| 3 | Restart `bash scripts/run_demo_local.sh`, wait 90s, run `bash scripts/demo_quick_validate.sh` | Andy |
| 4 | If validation PASS: run `python3 scripts/snapshot_demo_answers.py` to refresh offline pack | Andy |
| 5 | Schedule broker demo with 陈魁; use Offline mode if live retrieval still fails | Andy |
