# P19M-1 — Mini Program Prototype Foundation Evidence

**Date:** 2026-07-10  
**Branch:** `sprint/p16-trust-layer`  
**Starting commit:** `71ae202` — docs: lock mini program prototype scope and approve gate zero  
**Status:** P19M-1 foundation complete — local prototype GO; production HOLD

---

## 1. Architecture compliance

| Lock | Status |
|------|--------|
| Mini Program sole Customer Task App | ✅ Native pages; no H5 React reuse |
| WeCom entry/notification only | ✅ No WeCom wizard in MP |
| H5 fallback/API reference | ✅ Backend H5 routes called as-is |
| Structured Task First | ✅ Task Home + guided steps |
| Append-first | ✅ Existing backend dedup/timeline |
| No H5 reskin | ✅ New WXML task UI, one CTA per screen |
| Lock 3 scope | ✅ No voice/video/Add Car/auth/schema |

---

## 2. Directory created

`miniapp/` — native WeChat Mini Program (no Taro/uni-app).

---

## 3. Pages implemented

| Page | Purpose | Primary CTA | State |
|------|---------|-------------|-------|
| `entry` | Resolve token, load task | 重试 (error) | ✅ |
| `task-home` | Status, received/missing, next action | Dynamic (story/photos/review) | ✅ |
| `story` | Text accident description | 保存并继续 | ✅ |
| `basics` | Injury, time, location, vehicle | 保存并继续 | ✅ |
| `photos` | 2 photo uploads via evidence pack | 添加照片 / 继续 | ✅ |
| `review` | Final check + submit | 提交给陈总审核 | ✅ |
| `receipt` | Post-submit status | 查看当前状态 | ✅ |
| `error` | Invalid/expired/network | 重试 | ✅ |

---

## 4. API reuse

| Wrapper | Backend |
|---------|---------|
| `CustomerTaskApi.getTask` | `GET /api/h5/tasks/{token}/intake` |
| `saveStory` / `saveBasics` | `PATCH /api/h5/tasks/{token}/fields` |
| `submitTask` | `POST /api/h5/tasks/{token}/submit` |
| `uploadPhoto` | `POST /api/h5/tasks/{uploadToken}/upload` |

**Backend business code changed:** No  
**Schema migration:** No

---

## 5. Adapter boundaries

- **TaskLaunchContext:** launch query, `config.devTaskToken`, resume storage
- **MiniProgramSessionIdentity:** anonymous mock only
- **MediaCaptureAdapter:** `wx.chooseMedia` image only
- **CustomerTaskApi:** channel-neutral facade; H5 paths isolated in `services/taskApi.ts`

---

## 6. Tests

| Suite | Result |
|-------|--------|
| `tests/test_p19m1_mini_program_logic.py` | ✅ PASS |
| `tests/test_h5_claim_intake_form.py` | ✅ PASS |
| `tests/test_p19h3i_claim_task_dashboard_always_return_h5.py` | ✅ PASS |
| `tests/test_p19h3h_append_first_split_later.py` | ✅ PASS |

---

## 7. Run instructions

```bash
# Mint QA token
PYTHONPATH=. python3 scripts/p19m1_mint_prototype_token.py --api-base http://127.0.0.1:8001

# Copy miniapp/config.example.ts → miniapp/config.ts, set devTaskToken

# Open miniapp/ in 微信开发者工具; disable domain check for prototype API
```

---

## 8. Screenshots

Not captured in CI — manual DevTools verification required.

---

## 9. Manual checklist

- [ ] Token opens current Claim
- [ ] Task Home renders dashboard semantics
- [ ] Story saves
- [ ] Photo 1 + 2 upload
- [ ] App reload resumes same task
- [ ] Review shows story/photos
- [ ] Submit once; duplicate safe
- [ ] Receipt renders
- [ ] Workbench reads result
- [ ] Invalid token → error

---

## 10. Known blockers / unknowns

| Item | Status |
|------|--------|
| Official 主体 / 类目 | Gate 1 HOLD |
| Production openid binding | Not implemented |
| WeCom MP card | Adapter mock |
| Domain whitelist in real MP | DevTools `urlCheck: false` |
| CORS | Cloud Run allows; local needs DevTools setting |

---

## 11. GO / HOLD

| Decision | Verdict |
|----------|---------|
| Local developer prototype | **GO** |
| Real WeChat DevTools E2E | **GO** (manual) |
| Production publish | **HOLD** |
| Gate 1 official feasibility | **HOLD** |
| Next implementation phase | **P19M-1A** Developer Tool Integration Fixes |

---

*P19M-1 foundation — no deploy, no publish.*
