# Insurance Demo Execution Update

**Generated**: 2026-03-06  
**Scope**: California Auto Insurance Broker Assistant — 陈魁 demo readiness  
**Phase**: Execution-focused (validation → broker customization → demo prep)

---

## 1. Current Validation Result

### Result: **FAIL** (transient: embedding warmup + Qdrant)

| Check | Status | Notes |
|-------|--------|------|
| Backend start | ✅ | `run_demo_local.sh` starts backend on 8001 |
| Health check | ✅ | `/healthz` returns 200 |
| Readiness | ❌ | `embedding_model: false`, `qdrant_connected: false` |
| Quick validate | ❌ | All 3 questions return `embedding_warming` |

### Exact scripts run

```bash
# 1. Start backend (background)
TRANSLATION_ENABLED=1 TRANSLATION_PROVIDER=argos python3 -m uvicorn services.fiqa_api.app_main:app --host 0.0.0.0 --port 8001

# 2. Wait for health
curl -sf http://127.0.0.1:8001/healthz  # OK

# 3. Run validation
bash scripts/demo_quick_validate.sh
```

### Exact blockers

1. **embedding_warming**: Embedding model not ready on first requests. Backend returns `ok: false, error: embedding_warming` for `/api/query`.
2. **qdrant_connected: false**: Qdrant connection not established. Likely cause: `.env` or `.env.cloudrun` missing `QDRANT_URL` and `QDRANT_API_KEY` for Qdrant Cloud, or local Qdrant not running.

### Minimal fix to get PASS

1. **Configure Qdrant**: Copy `configs/demo.env.example` to `.env.cloudrun`, set `QDRANT_URL` and `QDRANT_API_KEY` (Qdrant Cloud), or run local Qdrant.
2. **Ensure collection exists**: Run `bash scripts/run_demo_ingest_oneclick.sh` if `auto_insurance_demo_core` is empty.
3. **Wait for warmup**: After backend start, wait 60–90 seconds before running `demo_quick_validate.sh`, or hit `/api/query` once to warm the embedding model.
4. **Re-run validation**: `bash scripts/demo_quick_validate.sh`

### Historical PASS

Last known PASS: `results/demo_quick_validate/2026-02-21_223652/REPORT.md` — all 3 questions passed with gov+insurer diversity.

---

## 2. Broker-Specific Customization

### Exact files edited

| File | Change |
|------|--------|
| `ui/src/pages/DemoPage.tsx` | Header: 陈奎 → **陈魁** (correct spelling) |

### Exact copy changes

- **Before**: `加州汽车保险智能助手（给陈奎 Demo）`
- **After**: `加州汽车保险智能助手（给陈魁 Demo）`

### Recommended 5 sample questions (demo order)

| # | Question (Chinese) | Broker use |
|---|--------------------|------------|
| 1 | 我刚买了辆新车（加州），最低需要买哪些保险？大概怎么配比较合理？ | 快速给客户权威答复 + 贴官方链接 |
| 2 | 我的车注册被暂停了（可能是保险问题），我该怎么恢复？需要交多少钱/提交什么材料？ | 快速给客户权威答复 + 贴官方链接 |
| 3 | 客户问我：怎么查保险公司/经纪人是不是合规？加州官方在哪里能查到？ | 快速给客户权威答复 + 贴官方链接 |
| 4 | 客户想省钱：哪些因素会影响保费？有哪些常见折扣/优惠？ | 介绍省钱技巧与折扣 |
| 5 | 出险后理赔流程是怎样的？ | 安抚客户并说明步骤 |

Questions 1–3 are the validated quick_validate set; 4–5 are from SCENARIOS and suitable for demo but not in quick_validate.

### Smallest UI/copy edits for “this is for 陈魁”

- ✅ Header: 给陈魁 Demo (done)
- No further edits needed for minimal demo-safe customization.

---

## 3. Demo Readiness

### Status: **Not ready** (blocked by validation FAIL)

| Component | Status | Notes |
|-----------|--------|------|
| Collection | Unknown | Needs `QDRANT_URL` + one-click ingest |
| Offline fallback | ✅ Ready | `ui/src/assets/demo_fallback.json` + `DEFAULT_FALLBACK_ITEMS` |
| Public/demo access | ⚠️ Pending | Requires Cloud Run deploy + `.env.cloudrun` |

### Top risks

1. **Backend/Qdrant unreachable** — Env vars missing; cold start.
2. **Collection empty** — One-click ingest not run.
3. **Embedding warmup** — First 1–2 queries may fail; retry after ~60s.

### Fallback plan if live retrieval fails

1. **Offline mode**: Demo works without backend. Click the 3 sample questions → load pre-saved answers from `demo_fallback.json` or `DEFAULT_FALLBACK_ITEMS`.
2. **Steps**: Open Demo URL → see "Offline" badge → click 3 recommended questions → show 建议结论 + 下一步 + 复制给客户.
3. **Refresh offline pack** (when backend is up): `python3 scripts/snapshot_demo_answers.py`

---

## 4. Work Split

| Who | Can do now |
|-----|-------------|
| **Cursor** | Validation scripts, broker UI edits (header 陈魁), execution report, demo flow doc |
| **OpenClaw** | Discovery/ingest (run_demo_ingest_oneclick.sh), fetch-extract-summarize for new sources |
| **Andy** | Configure `.env`/`.env.cloudrun` (QDRANT_URL, QDRANT_API_KEY), run one-click ingest, start demo, verify live retrieval, schedule demo with 陈魁 |
| **Deferred** | Stripe, multi-tenant auth, new verticals, LLM answer generation |

---

## 5. Next 10 Actions (Priority Order)

1. **Configure Qdrant** — Andy: Set `QDRANT_URL` and `QDRANT_API_KEY` in `.env` or `.env.cloudrun`.
2. **Run one-click ingest** — Andy or Cursor: `bash scripts/run_demo_ingest_oneclick.sh` (if collection empty).
3. **Start demo + validate** — Andy: `bash scripts/run_demo_local.sh`, wait 90s, then `bash scripts/demo_quick_validate.sh` in another terminal.
4. **Refresh offline pack** — After validation PASS: `python3 scripts/snapshot_demo_answers.py`.
5. **Demo prepare** — Night before: `bash scripts/demo_prepare_tomorrow.sh`.
6. **Schedule 15-min demo** — Andy: With 陈魁.
7. **Run demo** — Andy: Use recommended 5 questions in order; fallback to Offline if live fails.
8. **Deploy to Cloud Run** (optional) — For public URL: `bash scripts/deploy_rag_demo.sh` with `.env.cloudrun`.
9. **Deploy frontend** (optional) — Vercel/Netlify or share local URL for pilot.
10. **Manual payment** — Zelle/Venmo/WeChat; send invoice.

---

## Appendix: 15-Minute Demo Package

### Recommended demo flow

| Time | Action | On screen |
|------|--------|-----------|
| 0:00 | Intro | "加州汽车保险智能助手，给陈魁 Demo" |
| 0:30 | Q1 (新车最低保险) | Click → show answer + gov/insurer citations |
| 2:30 | Q2 (注册暂停恢复) | Click → show DMV links |
| 4:30 | Q3 (合规查询) | Click → show insurance.ca.gov |
| 6:30 | Q4 (省钱/折扣) | Click or type → show tips |
| 8:30 | Q5 (理赔流程) | Click or type → show steps |
| 10:00 | Copy to client | Click "复制给客户（可直接发微信）" |
| 11:00 | Q&A | Answer questions |

### Exact order of 5 sample questions

1. 我刚买了辆新车（加州），最低需要买哪些保险？大概怎么配比较合理？
2. 我的车注册被暂停了（可能是保险问题），我该怎么恢复？需要交多少钱/提交什么材料？
3. 客户问我：怎么查保险公司/经纪人是不是合规？加州官方在哪里能查到？
4. 客户想省钱：哪些因素会影响保费？有哪些常见折扣/优惠？
5. 出险后理赔流程是怎样的？

### What to avoid during demo

- Do not type ad-hoc questions not in the 5 (risk of poor retrieval).
- Do not switch to non-demo mode.
- Do not show backend logs or terminal.
- Do not demo if backend shows "Disconnected" without switching to Offline and using the 3 sample questions.

### Live-demo risk checklist

- [ ] `.env` or `.env.cloudrun` has QDRANT_URL, QDRANT_API_KEY
- [ ] `auto_insurance_demo_core` has ≥20 points (run one-click ingest if unsure)
- [ ] `demo_quick_validate.sh` PASS before demo day
- [ ] `demo_prepare_tomorrow.sh` run night before
- [ ] Offline fallback tested (stop backend, click 3 questions)
- [ ] Network/VPN stable

### Fallback if live retrieval fails

1. Acknowledge: "Let me switch to offline mode."
2. Ensure status shows "Offline".
3. Click the 3 sample questions only (they load from pre-saved answers).
4. Continue demo with 建议结论 + 下一步 + 复制给客户.
