# P19G-3.1 — WeCom P0 Copy / Button / Progress Card Polish Evidence

**Date:** 2026-07-08  
**Branch:** `sprint/p16-trust-layer`  
**Type:** Copy/constants polish — local tests + build + QA gate  
**Verdict:** **LOCAL PASS** · **QA gate PASS** · **HOLD deploy + phone smoke**

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

**PASS** — QA UI + Cloud Run API + Cloud SQL aligned (pre-deploy baseline unchanged).

---

## Constraints honored

| Constraint | Status |
|------------|--------|
| No OCR | ✅ |
| No Claim workflow | ✅ |
| No schema migration | ✅ |
| No Cloud config change | ✅ |
| No deploy | ✅ |
| No routing / state machine change | ✅ |
| Copy/constants only | ✅ |

---

## Known limitations

- Restart still instant (no confirmation card) — P1 per backlog
- Greeting menu unchanged — P1
- Broker Done Card (`DONE_CARD_TEXT`) unchanged — P1
- Legacy Start Card (`Start / 开始`) unchanged — legacy fallback path only
- Cloud/QA still serves pre-deploy copy until next deploy

---

## GO / HOLD

| Gate | Verdict |
|------|---------|
| Local tests + build | **GO** |
| Commit | **GO** |
| Deploy | **HOLD** — copy not live until deploy |
| Phone smoke | **HOLD** — run after deploy on WeCom + H5 |

---

*P19G-3.1 local implementation complete. Next: deploy + Andy phone smoke when ready.*
