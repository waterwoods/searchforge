# Live Workflow Depth Activation Verification Report

**Date:** 2026-03-07  
**Goal:** Verify whether 客户可准备, 经纪人可进一步询问, 经纪人下一步 are active in the live running backend.

---

## 1. Runtime path used

- **Endpoint:** `POST http://127.0.0.1:8001/api/query`
- **Backend:** SearchForge Main API (fiqa_api)
- **Port:** 8001

---

## 2. Exact commands run

```bash
# Health check
curl -sf http://127.0.0.1:8001/healthz
# → 200 OK

# Live query (Q1)
curl -s -X POST http://127.0.0.1:8001/api/query \
  -H "Content-Type: application/json" \
  -d '{"question":"我刚买了辆新车（加州），最低需要买哪些保险？大概怎么配比较合理？","mode":"demo","translation_mode":"auto","top_k":5,"generate_answer":true}'

# Retry loop (5 attempts, 5s apart)
for i in 1 2 3 4 5; do
  curl -s -X POST http://127.0.0.1:8001/api/query \
    -H "Content-Type: application/json" \
    -d '{"question":"我刚买了辆新车（加州），最低需要买哪些保险？","mode":"demo","top_k":5,"generate_answer":true}'
  sleep 5
done
```

---

## 3. Live output for Q1/Q2/Q5/Q3

**Result:** No live output obtained.

Every request returned:

```json
{"detail":{"ok":false,"error":"embedding_warming"}}
```

HTTP status: **503**.

---

## 4. Confirmed / partial / failed

| Path | Status | Evidence |
|------|--------|----------|
| **Live API** (`POST /api/query`) | **FAILED** | All requests return 503 `embedding_warming`; no answer body |
| **Offline pack** (`demo_fallback.json`) | **CONFIRMED** | All 5 items contain 客户可准备, 经纪人可进一步询问, 经纪人下一步 |
| **Unit test** (`_apply_broker_demo_answer_fixes`) | **CONFIRMED** | Appends all 3 blocks when answer lacks them |

---

## 5. Exact blocker

**Blocker:** `embedding_warming`

- **Cause:** `EMBED_READY` is `False` in `services/fiqa_api/clients.py`
- **Effect:** `services/fiqa_api/routes/query.py` (lines 730–736) raises 503 before any search or answer logic
- **Chain:** Embedding warmup never completes (e.g. Qdrant unreachable or model load failure) → `EMBED_READY` stays false → every `/api/query` returns 503
- **Readiness:** `GET /ready` returns `{"detail":{"ok":false,"phase":"starting"}}`

---

## 6. What was verified

**Offline pack (demo_fallback.json):**

```
Q1 我刚买了辆新车...  客户可准备: True, 经纪人可进一步询问: True, 经纪人下一步: True  OK
Q2 我的车注册被暂停了...  客户可准备: True, 经纪人可进一步询问: True, 经纪人下一步: True  OK
Q3 客户问我：怎么查...  客户可准备: True, 经纪人可进一步询问: True, 经纪人下一步: True  OK
Q4 客户想省钱...  客户可准备: True, 经纪人可进一步询问: True, 经纪人下一步: True  OK
Q5 出险后理赔流程...  客户可准备: True, 经纪人可进一步询问: True, 经纪人下一步: True  OK
```

When the backend returns 503, the Demo UI uses this offline pack. In that mode, all three workflow blocks are present.

---

## 7. Conclusion

**Live activation could not be verified** because the backend never serves successful `/api/query` responses; all requests fail with 503 `embedding_warming`.

**To verify live activation:** Fix embedding warmup (e.g. Qdrant reachable, embedding model loaded), then run:

```bash
python3 scripts/broker_regression_all5.py --port 8001 --report /tmp/live_verify.md
```

When the backend is ready, the query route will run `_apply_broker_demo_answer_fixes`, which appends 客户可准备, 经纪人可进一步询问, and 经纪人下一步 to broker answers.
