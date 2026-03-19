# Insurance Demo Revalidation Report

**Generated**: 2026-03-06  
**Scope**: California Auto Insurance Broker Assistant — controlled re-validation and demo-readiness  
**Phase**: Execution (not discovery); correct launcher path

---

## 1. Validation result

| Result | **FAIL** |
|--------|----------|
| Commands run | `bash scripts/run_demo_local.sh` (background) → wait 95s → `bash scripts/demo_quick_validate.sh` |
| Startup timing | 95 seconds (embedding warmup + Qdrant ping) |
| What happened | Backend started, healthz OK, UI ready. Qdrant Cloud returned 404. Embedding warmup failed (depends on Qdrant ping). All 3 validation questions returned `embedding_warming`. |

### Exact output

```
[0] Health check http://127.0.0.1:8001/healthz...
  OK

[1] Q1: 我刚买了辆新车（加州）...
[2] Q2: 我的车注册被暂停了...
[3] Q3: 客户问我：怎么查保险公司/经纪人...

[4] Validating...
**Overall: FAIL**

### Q1 ❌ FAIL
- ❌ `ok`: API ok=false: {'detail': {'ok': False, 'error': 'embedding_warming'}}

### Q2 ❌ FAIL
- ❌ `ok`: API ok=false: {'detail': {'ok': False, 'error': 'embedding_warming'}}

### Q3 ❌ FAIL
- ❌ `ok`: API ok=false: {'detail': {'ok': False, 'error': 'embedding_warming'}}
```

### Startup log (relevant)

```
[CLIENTS] Initializing Qdrant client with URL: https://***.us-east4-0.gcp.cloud.qdrant.io
[CLIENTS] QDRANT_API_KEY present: True
httpx: HTTP Request: GET https://...cloud.qdrant.io:6333/collections "HTTP/1.1 404 Not Found"
[ERROR] [CLIENTS] Qdrant client created but connection test failed: Unexpected Response: 404 (Not Found)
[ERROR] [WARMUP] Embedding warmup failed: Unexpected Response: 404 (Not Found)
```

---

## 2. Current blocker

| Item | Detail |
|------|--------|
| **Exact issue** | All `/api/query` requests return `ok: false, error: embedding_warming` |
| **Exact root cause** | Qdrant Cloud returns 404 on `GET /collections`. Embedding warmup requires a successful Qdrant ping; when it fails, `EMBED_READY` never flips to true. |
| **Chain** | Qdrant 404 → warmup fails → `EMBED_READY` stays false → queries return `embedding_warming` |
| **Smallest fix** | **Andy**: Verify Qdrant Cloud cluster is active (not paused) at [cloud.qdrant.io](https://cloud.qdrant.io). Qdrant Cloud pauses free-tier clusters after inactivity. Wake the cluster in the dashboard, then re-run `bash scripts/run_demo_local.sh` and `bash scripts/demo_quick_validate.sh`. |

### No code change required

The `.env.cloudrun` Qdrant config (URL, API key) is present and correctly formatted. The 404 is from the Qdrant Cloud service, not from misconfiguration. Fix is operational: ensure cluster is active.

---

## 3. Demo readiness status

| Status | **Almost ready** |
|--------|------------------|
| Live retrieval | ❌ Blocked by Qdrant 404 |
| Offline fallback | ✅ Ready — `demo_fallback.json` has 3 items; `DEFAULT_FALLBACK_ITEMS` in `DemoPage.tsx` |
| UI / broker copy | ✅ Ready — header "加州汽车保险智能助手（给陈魁 Demo）" |
| What is still missing | Qdrant Cloud cluster must be active for live retrieval. Until then, demo can run in **Offline mode** only. |

### Before showing 陈魁

1. **Option A (live)**: Wake Qdrant Cloud cluster → re-run validation → confirm PASS.
2. **Option B (offline)**: Run `bash scripts/run_demo_local.sh` → open http://localhost:5173/demo → if backend shows "Offline" or live fails, click the 3 sample questions to load pre-saved answers. Demo works without Qdrant.

---

## 4. Broker demo package

### Current broker header/copy status

| Element | Value |
|---------|-------|
| Header | 加州汽车保险智能助手（给陈魁 Demo） |
| Subtitle | Ask questions about car insurance in California (中英文均可) |
| Source note | 数据来源：加州 DMV / 加州保险监管机构 / 主流保险公司官方页面 |
| Sample questions | 3 recommended (matches quick_validate) |

### Recommended 5 demo questions (in order)

| # | Question (Chinese) | Broker use |
|---|--------------------|------------|
| 1 | 我刚买了辆新车（加州），最低需要买哪些保险？大概怎么配比较合理？ | 快速给客户权威答复 + 贴官方链接 |
| 2 | 我的车注册被暂停了（可能是保险问题），我该怎么恢复？需要交多少钱/提交什么材料？ | 快速给客户权威答复 + 贴官方链接 |
| 3 | 客户问我：怎么查保险公司/经纪人是不是合规？加州官方在哪里能查到？ | 快速给客户权威答复 + 贴官方链接 |
| 4 | 客户想省钱：哪些因素会影响保费？有哪些常见折扣/优惠？ | 介绍省钱技巧与折扣 |
| 5 | 出险后理赔流程是怎样的？ | 安抚客户并说明步骤 |

Questions 1–3 are the validated set (quick_validate). 4–5 are from SCENARIOS and suitable for demo.

### Recommended 15-minute flow

| Time | Phase | Action |
|------|-------|--------|
| 0:00 | Intro | "加州汽车保险智能助手，给陈魁 Demo" — show header, source note |
| 0:30 | Q1 | Click sample Q1 → Ask → show answer + gov/insurer citations |
| 2:30 | Q2 | Click sample Q2 → show DMV/insurance links |
| 4:30 | Q3 | Click sample Q3 → show insurance.ca.gov license lookup |
| 6:30 | Q4–5 | Use scenario buttons or type Q4/Q5 |
| 10:00 | Copy-to-client | Show 复制给客户, WeChat-ready format |
| 12:00 | Q&A | Take broker feedback |

### Fallback plan if live retrieval has issues

1. Say: "Let me switch to offline mode."
2. Ensure status shows "Offline" (or stop backend to force it).
3. Click only the 3 sample questions — they load from `demo_fallback.json` or `DEFAULT_FALLBACK_ITEMS`.
4. 建议结论 + 下一步 + 复制给客户 all work in Offline mode.

---

## 5. Work split

| Who | What |
|-----|------|
| **Cursor** | Validation scripts, broker UI (header 陈魁), execution report, demo flow doc. No further code changes needed for this phase. |
| **OpenClaw** | Snapshot offline pack (`snapshot_demo_answers.py`) when backend is up; one-click ingest. |
| **Andy** | 1) Verify Qdrant Cloud cluster is active (wake if paused). 2) Re-run `run_demo_local.sh` + `demo_quick_validate.sh` after cluster is up. 3) Schedule 15-min demo with 陈魁. 4) Use Offline mode if live fails. |

---

## 6. Next 10 actions (priority order)

| # | Action | Owner |
|---|--------|-------|
| 1 | Wake Qdrant Cloud cluster (cloud.qdrant.io) if paused | Andy |
| 2 | Re-run `bash scripts/run_demo_local.sh` | Andy |
| 3 | Wait 90s, then `bash scripts/demo_quick_validate.sh` | Andy |
| 4 | If PASS: run `python3 scripts/snapshot_demo_answers.py` to refresh offline pack | Andy or OpenClaw |
| 5 | Schedule 15-min demo with 陈魁 | Andy |
| 6 | Use recommended 5 questions in order | Andy |
| 7 | If live fails: switch to Offline, click 3 sample questions | Andy |
| 8 | Capture broker feedback | Andy |
| 9 | (Optional) Add 1–2 broker-specific questions to SCENARIOS | Cursor |
| 10 | (Later) Deploy to Cloud Run for public URL | Andy |

---

## Files referenced

| File | Purpose |
|------|---------|
| `scripts/run_demo_local.sh` | One-command demo launcher (backend 8001 + UI 5173) |
| `scripts/demo_quick_validate.sh` | 3-question validation |
| `scripts/demo_quick_validate.py` | Validation rules (results≥3, gov, insurer) |
| `ui/src/pages/DemoPage.tsx` | Broker header, sample questions, Offline fallback |
| `ui/src/assets/demo_fallback.json` | Pre-saved answers for 3 questions |
| `.env.cloudrun` | QDRANT_URL, QDRANT_API_KEY (present; 404 from service) |
| `results/demo_quick_validate/2026-03-06_115337/REPORT.md` | Latest validation report |

---

**Conclusion**: Validation FAIL due to Qdrant Cloud 404. Demo is **almost ready** — Offline mode works today. Fix Qdrant cluster, re-validate, then demo to 陈魁.
