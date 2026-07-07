# P19G-3.1 — WeCom P0 Copy / Button / Progress Card Polish Evidence

**Date:** 2026-07-08  
**Branch:** `sprint/p16-trust-layer`  
**Type:** Copy/constants polish — local tests + build + deploy + phone smoke prep  
**Verdict:** **LOCAL PASS** · **DEPLOY PASS** · **QA gate PASS** · **Phone smoke PENDING**

---

## Goal

Implement P19G-3 P0 copy polish for Add Vehicle WeCom/H5 flow: shorter Chinese-first copy, unified button labels, clearer step framing (第 1 步 / 第 2 步), Progress Card status clarity, and H5 success page alignment — without routing, schema, or Cloud config changes.

---

## Source doc

`docs/p19g3_wecom_copy_button_progress_card_polish_backlog.md` (commit `ca6bc42`)

---

## Changed files

| File | Change |
|------|--------|
| `services/fiqa_api/wecom/reply.py` | Start Card, S1, S2, Phase 2 prompts, Progress Card, recovery copy |
| `services/fiqa_api/wecom/add_vehicle_progress.py` | Phase 1 missing photo labels (中文) |
| `services/fiqa_api/inbox_triage/h5_task_upload.py` | H5 slot labels (登记证 / 可跳过) |
| `ui/src/pages/H5SingleSlotUploadPage.tsx` | H5 success page copy; removed duplicate headline +「稍后继续」 |
| `tests/test_*.py` (10 files) | Updated copy expectations |

---

## Old copy problems

| Area | Before | Problem |
|------|--------|---------|
| Start Card | `加车资料收集` + `registration` + `开始上传照片` | 中英混杂；按钮与 demo 脚本不一致 |
| S1 | `第 1 阶段完成` + 照片 checklist + 分隔线 | 易被理解成全部完成；偏系统模板 |
| S2 | `第 2 阶段完成` + `第 3 步` | 同样误导；冗长 |
| Phase 2 | `第 2 步进行中` + 无固定例子 | partial 时略机械 |
| Progress Card | `第 X 步：` 逐步编号 | 略机械；broker review 重复保单句 |
| H5 success | 双「第 1 阶段完成」+ Workbench + 双按钮 | 重复；暴露后台词 |
| Recovery | `我还没有识别到…` | 偏技术感 |

---

## New copy summary

- 短句中文，一次一事
- 「步」代替「阶段」
- 四问必答：已收到 / 还差 / 下一步 / 是否等陈总
- 不暗示保单已自动修改
- 不说 OCR / workflow / Workbench

---

## Start Card

```text
【加车资料收集】

请先上传 3 类资料：
1. VIN 照片
2. 行驶证 / 登记证
3. 保险卡（没有可跳过）

点下面按钮开始上传。
```

**Button:** `开始上传资料`

---

## S1 (Stage Complete)

```text
【第 1 步完成 ✅】

照片资料已收到。

下一步请在微信里回复：
提车日期、停放 ZIP、联系电话。

例如：
7月10号提车，ZIP 92705，电话 2031234567
```

---

## Phase 2 prompt

**Empty:**

```text
【加车资料 · 第 2 步】

还差 3 个文字信息：

1. 提车日期
2. 停放 ZIP
3. 联系电话

可以直接这样回复：
7月10号提车，ZIP 92705，电话 2031234567
```

**Partial:** 已收到 ✓ / 还差 ○ + `请继续在微信里回复。`（单字段电话时：`请直接回复电话号码即可。`）

**Recovery:**

```text
我还需要一点信息才能继续。

还差：
○ 提车日期
○ 停放 ZIP
○ 联系电话

请直接这样回复：
7月10号提车，ZIP 92705，电话 2031234567
```

---

## S2 (Stage Complete)

```text
【第 2 步完成 ✅】

文字信息已收到。

目前资料已基本收齐。
下一步：陈总人工确认。

系统不会自动修改您的保单。
```

---

## Progress Card

**Phase 1 incomplete:**

```text
【加车资料进度】

▶️ 第 1 步：上传照片

还差：
○ …

请点下面按钮继续上传。
```

**Missing text:**

```text
✅ 照片资料已收到
▶️ 还差文字信息
…
请直接在微信里回复。
```

**Broker review:**

```text
✅ 照片资料已收到
✅ 文字信息已收到
▶️ 陈总人工确认中

目前不需要您补资料。
确认后会通过微信或电话跟进。
```

---

## H5 final page

```text
第 1 步完成 ✅

照片资料已收到。
请回到微信，继续补充：
提车日期、停放 ZIP、联系电话。
```

**Button:** `返回微信`（移除「稍后继续」）

---

## Button labels

| Scene | Label |
|-------|-------|
| Start Card | 开始上传资料 |
| Progress resume | 继续上传照片 |
| H5 success | 返回微信 |
| Secondary (unchanged) | 联系经纪人 |
| Restart intro | 好的，我们为您开始一辆新车的资料收集。 |

---

## Tests / build results

| Command | Result |
|---------|--------|
| `pytest tests/test_p19e2_add_vehicle_progress_card.py -q` | 26 passed |
| `pytest tests/test_p19e1_*.py tests/test_wecom_*.py -q` | 111 passed |
| `pytest tests/test_h5_task_token.py tests/test_h5_single_slot_upload.py tests/test_h5_add_vehicle_photo_flow.py -q` | 32 passed |
| `cd ui && npm run build` | PASS |

---

## QA gate result

```bash
bash scripts/check_chen_kui_demo_environment.sh --cloud-api
```

**PASS** — QA UI + Cloud Run API + Cloud SQL aligned (post-deploy revision `fiqa-api-00165-qfk`).

---

## Deploy (2026-07-07)

### Pushed commits

| Commit | Message |
|--------|---------|
| `7a51ace` | feat: polish Add Vehicle WeCom copy |

Pushed: `git push origin sprint/p16-trust-layer` (`ca6bc42..7a51ace`)

### Backend deploy

| Field | Value |
|-------|-------|
| Script | `bash scripts/deploy_paid_pilot.sh` |
| Project | `optimal-disk-472305-e2` |
| Service | `fiqa-api` |
| Region | `us-west1` |
| **Revision (prior)** | `fiqa-api-00164-8c9` |
| **Revision (this deploy)** | **`fiqa-api-00165-qfk`** |
| URL | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| **GIT_SHA** | **`7a51ace1e`** |
| Deploy time (UTC) | 2026-07-07 ~22:28 UTC |
| `/health/live` | 200 |
| `/readyz` | 200 (`intake_core_readiness: true`) |
| DB secret | `fiqa-service-record-database-url-cloudsql-private` — unchanged |
| Cloud SQL | `caseiq` @ `10.73.0.3` private VPC — unchanged |
| `WECOM_SLICE_SEND_REPLY` | `1` — unchanged |
| `H5_TASK_TOKEN_SECRET` | configured — unchanged |
| WeCom callback / VPC / NAT / min instances | unchanged |
| Neon | Not QA truth |

### Frontend deploy

| Field | Value |
|-------|-------|
| Command | `vercel deploy --prod --yes` (ui/) |
| Production deployment | `https://ui-m120jt8xs-andys-projects-1f411b73.vercel.app` |
| **Stable alias** | **`https://ui-smoky-beta.vercel.app`** |
| `/workbench/document-intake` | HTTP 200 |
| `/task/upload/:taskToken` | HTTP 200 (SPA route) |
| Build | PASS (~39s on Vercel) |
| Bundle check | Contains `第 1 步完成`, `照片资料已收到`, `返回微信` |

### Post-deploy QA gate

```bash
bash scripts/check_chen_kui_demo_environment.sh --cloud-api
# Result: PASS — revision fiqa-api-00165-qfk, Cloud SQL aligned
```

### Log check (post-deploy)

Revision `fiqa-api-00165-qfk` startup + runtime logs reviewed (~100 lines):

- **No** import/syntax errors
- **No** WeCom reply errors
- **No** H5 task upload errors
- **No** Postgres read facade errors
- Expected optional warnings only: embedding warmup deferred, Qdrant/Redis optional, bm25 optional

---

## Andy WeCom phone smoke checklist

**Backend:** `fiqa-api-00165-qfk` · **GIT_SHA:** `7a51ace` · **Frontend alias:** `ui-smoky-beta`

### Smoke A — Start Card copy

| # | Action | Expected | Result |
|---|--------|----------|--------|
| A1 | Send `重新加车` | Start Card with `【加车资料收集】` + 3-item checklist | **PENDING** |
| A2 | Button label | `开始上传资料` | **PENDING** |
| A3 | No English / long URL in main copy | Clean Chinese-first copy | **PENDING** |

### Smoke B — H5 photo flow + final page

| # | Action | Expected | Result |
|---|--------|----------|--------|
| B1 | Click `开始上传资料` | H5 opens | **PENDING** |
| B2 | Complete or skip photo flow | `第 1 步完成 ✅` | **PENDING** |
| B3 | Final page copy | 照片资料已收到 + 回微信补文字 | **PENDING** |
| B4 | Button | `返回微信` only (no 稍后继续) | **PENDING** |
| B5 | No Workbench / 全部完成 | Clean customer copy | **PENDING** |

### Smoke C — S1 WeCom copy

| # | Action | Expected | Result |
|---|--------|----------|--------|
| C1 | After H5 flow_complete | `【第 1 步完成 ✅】` + example line | **PENDING** |
| C2 | Next action clear | 微信里回复提车日期/ZIP/电话 | **PENDING** |

### Smoke D — Phase 2 text + S2 copy

| # | Action | Expected | Result |
|---|--------|----------|--------|
| D1 | Send `7月10号提车，ZIP 92705，电话 2031234567` | `【第 2 步完成 ✅】` | **PENDING** |
| D2 | Broker handoff copy | 陈总人工确认 + 不会自动修改保单 | **PENDING** |
| D3 | No greeting hijack | Phase 2 extractor wins | **PENDING** |

### Smoke E — Progress Card copy

| # | Action | Expected | Result |
|---|--------|----------|--------|
| E1 | Send `进度` (after S2) | broker review Progress Card | **PENDING** |
| E2 | Short status lines | 照片✅ 文字✅ 陈总确认中 | **PENDING** |

### Smoke F — Phase 1 incomplete progress (optional)

| # | Action | Expected | Result |
|---|--------|----------|--------|
| F1 | New add car, partial photos, send `继续` | `▶️ 第 1 步：上传照片` + `继续上传照片` | **PENDING** |

### Smoke G — Regression

| # | Action | Expected | Result |
|---|--------|----------|--------|
| G1 | Send `我要理赔` | Claim lane (existing behavior) | **PENDING** |
| G2 | Send `你好` / `进度` | Progress Card if active case; menu if none | **PENDING** |

---

## Constraints honored

| Constraint | Status |
|------------|--------|
| No OCR | ✅ |
| No Claim workflow | ✅ |
| No schema migration | ✅ |
| No Cloud config change | ✅ |
| No routing / state machine change | ✅ |
| Copy/constants only | ✅ |
| No H5 token/security change | ✅ |

---

## Known limitations

- Restart still instant (no confirmation card) — P1 per backlog
- Greeting menu unchanged — P1
- Broker Done Card (`DONE_CARD_TEXT`) unchanged — P1
- Legacy Start Card (`Start / 开始`) unchanged — legacy fallback path only
- Legacy Start Card (`Start / 开始`) unchanged — legacy fallback path only

---

## GO / HOLD

| Gate | Verdict |
|------|---------|
| Local tests + build | **GO** |
| Push + deploy | **GO** |
| Post-deploy QA gate | **GO** |
| Logs | **GO** (clean) |
| Andy phone smoke | **PENDING** — operator run on WeChat |

---

*P19G-3.1 deploy complete. Andy phone smoke pending.*
