# Insurance Live+Offline Demo Recovery Report

**Generated**: 2026-03-06  
**Scope**: California Auto Insurance Broker Assistant — controlled revalidation + offline hardening + dual-path simulation

---

## 1. Live revalidation result

| Result | **FAIL** |
|--------|----------|
| Commands run | `bash scripts/run_demo_local.sh` (background) → wait 95s → `bash scripts/demo_quick_validate.sh` |
| Timing | 95 seconds (embedding warmup + Qdrant ping) |
| Blocker | Qdrant Cloud returns 404 on `GET /collections` → warmup fails → `EMBED_READY` stays false → all queries return 503 `embedding_warming` |

### Exact blocker

- **Stage**: Qdrant connection
- **Cause**: Qdrant Cloud 404 (cluster likely paused)
- **Fix**: Andy must wake Qdrant Cloud cluster at [cloud.qdrant.io](https://cloud.qdrant.io), then re-run validation

---

## 2. Offline fallback verification

| Status | **Verified** |
|--------|--------------|
| Backend stopped | Yes |
| Page loads | Yes |
| Status bar | Shows "Offline", "Backend: Disconnected" |
| 3 sample questions | All load from `demo_fallback.json` / `DEFAULT_FALLBACK_ITEMS` |
| Results | 建议结论, 权威依据, 复制给客户, gov/insurer links all present |

### What works

- 3 sample questions load pre-saved answers instantly
- 建议结论（给客户的版本）, 下一步怎么做, 权威依据, 复制给客户（可直接发微信） all work
- Broker header "加州汽车保险智能助手（给陈魁 Demo）" visible
- Offline banner: "演示模式（离线）— 点击上方 3 个推荐问题加载预存答案，演示可正常进行。"

### What looked awkward (before fixes)

- Error message "embedding_warming" was technical and unhelpful
- Offline banner was mixed English ("Offline Demo (Fallback)")

### Smallest improvements applied

1. **`ui/src/pages/DemoPage.tsx`**: Map `embedding_warming` → friendly message: "服务正在启动，请稍后重试。或直接点击上方 3 个推荐问题使用离线演示。"
2. **`ui/src/pages/DemoPage.tsx`**: Fix error extraction from API `detail.error` (was `errData.error`, now `errData?.detail?.error`)
3. **`ui/src/pages/DemoPage.tsx`**: Offline banner copy → "演示模式（离线）" + "点击上方 3 个推荐问题加载预存答案，演示可正常进行。"

---

## 3. Dual-path demo readiness

### Live success path

| Step | Status | Notes |
|------|--------|-------|
| App starts | ✅ | `run_demo_local.sh` starts backend + UI |
| Sample questions work | ❌ Blocked | Qdrant 404 → 503 |
| Results usable | N/A | Blocked |
| Broker header/copy | ✅ | "加州汽车保险智能助手（给陈魁 Demo）" |

**Live path ready?** No — blocked by Qdrant. Once Qdrant is active, re-run validation once.

### Live failure → Offline fallback path

| Step | Status | Notes |
|------|--------|-------|
| Live unavailable | ✅ | 503 or backend down |
| Offline fallback used | ✅ | `useOfflineFallback` true when error or backend down |
| Demo works | ✅ | 3 sample questions load from fallback |
| No confusion | ✅ | Friendly error message + Offline banner |

**Offline path ready?** Yes.

### Overall broker demo readiness

| Condition | Ready? |
|-----------|--------|
| Demo with Live retrieval | No — Qdrant must be woken |
| Demo with Offline fallback | **Yes** — can demo today |
| Demo with both paths | Almost — fix Qdrant, then both work |

---

## 4. Smallest remaining fixes

| # | Fix | Priority | Owner |
|---|-----|----------|-------|
| 1 | Wake Qdrant Cloud cluster | **P0** | Andy |
| 2 | Re-run `bash scripts/run_demo_local.sh` + `demo_quick_validate.sh` after Qdrant up | P0 | Andy |
| 3 | (Optional) Fix `run_demo_local.sh` to print actual UI port when 5173 is in use | P2 | Cursor |

---

## 5. Automation opportunities

### Cursor (in-repo)

| Task | Script | Status |
|------|--------|--------|
| Pre-demo checklist | `scripts/demo_pre_checklist.sh` | ✅ Created |
| Demo prepare (validate + snapshot) | `scripts/demo_prepare_tomorrow.sh` | ✅ Exists |
| Quick validate | `scripts/demo_quick_validate.sh` | ✅ Exists |
| One-command start | `scripts/run_demo_local.sh` | ✅ Exists |
| Friendly 503 message | `DemoPage.tsx` | ✅ Done |
| Offline banner copy | `DemoPage.tsx` | ✅ Done |

### OpenClaw (repeated runs)

| Task | How |
|------|-----|
| Snapshot offline pack | `python3 scripts/snapshot_demo_answers.py` (backend must be up) |
| One-click ingest | `bash scripts/run_demo_ingest_oneclick.sh` |
| Build demo collection | `python3 scripts/build_demo_core_collection.py --top-n 20` |

### Andy (manual)

| Task | When |
|-----|------|
| Wake Qdrant Cloud cluster | Before demo if Live needed |
| Configure `.env.cloudrun` | One-time (QDRANT_URL, QDRANT_API_KEY) |
| Run `run_demo_local.sh` | Before each demo |
| Run `demo_pre_checklist.sh` | Before each demo (optional) |
| Schedule 15-min demo with 陈魁 | — |
| Use Offline mode if Live fails | During demo |

### Repeatable pre-demo checklist

```bash
# Night before (optional)
bash scripts/demo_prepare_tomorrow.sh

# Day of demo
bash scripts/demo_pre_checklist.sh   # Quick env + offline + validate check
bash scripts/run_demo_local.sh       # Start demo
# Open http://localhost:5173/demo
# If Live fails: stop backend, refresh, click 3 sample questions
```

---

## 6. Recommended next 10 actions

| # | Action | Owner |
|---|--------|-------|
| 1 | **Wake Qdrant Cloud cluster** at cloud.qdrant.io | Andy |
| 2 | Re-run `bash scripts/run_demo_local.sh`, wait 90s, `bash scripts/demo_quick_validate.sh` | Andy |
| 3 | If PASS: run `python3 scripts/snapshot_demo_answers.py` to refresh offline pack | Andy |
| 4 | **Schedule 15-min demo with 陈魁** | Andy |
| 5 | Run `bash scripts/demo_pre_checklist.sh` before demo | Andy |
| 6 | Use recommended 5 questions in order | Andy |
| 7 | If Live fails during demo: say "切换到离线演示", stop backend, refresh, click 3 sample questions | Andy |
| 8 | Capture broker feedback | Andy |
| 9 | (Optional) Add 1–2 broker-specific questions to SCENARIOS | Cursor |
| 10 | (Later) Deploy to Cloud Run for public URL | Andy |

---

## Files changed

| File | Change |
|------|--------|
| `ui/src/pages/DemoPage.tsx` | Friendly `embedding_warming` message; fix `detail.error` extraction; Offline banner copy |
| `scripts/demo_pre_checklist.sh` | New pre-demo checklist script |
| `docs/INSURANCE_LIVE_OFFLINE_DEMO_RECOVERY_REPORT.md` | This report |

---

## Conclusion

**Offline demo is ready today.** You can demo to 陈魁 using Offline mode: stop the backend, open http://localhost:5173/demo, click the 3 sample questions. Live retrieval works once the Qdrant Cloud cluster is active.
