# 3 Live Chains Implementation Sprint Report

**Sprint:** 3 Live Chains Implementation  
**Date:** 2026-03-09  
**Scope:** BMW X5 / new car quote, payment failed / cancellation risk, English notice confusion / DMV-SR22

---

## 1. Scope completed

| Stage | Status | Notes |
|-------|--------|-------|
| Stage 1 — Lock baseline | ✅ | Guardrails pass; docs locked |
| Stage 2 — BMW X5 chain | ✅ | Fixed English-language reply; chain solid |
| Stage 3 — Payment failed / cancellation risk | ✅ | Chain validated; no changes needed |
| Stage 4 — English notice / DMV-SR22 | ✅ | Chain validated; no changes needed |
| Stage 5 — Optional handoff polish | ✅ | Added "Collected:" display in broker case card (UI-only) |
| Stage 6 — Demo readiness | ✅ | Demo doc updated; all validation passes |

---

## 2. Changes made

### Backend (`services/fiqa_api/inbox_triage/triage.py`)

1. **Language detection fix for multi-turn conversations**
   - **Problem:** Merged conversation text includes `[客户]` and `[系统]` labels. Those labels contain Chinese characters, so `_detect_client_language()` incorrectly returned `zh` for English-only customer messages.
   - **Fix:** Added `_get_customer_content_for_language()` to extract only customer message content (excluding labels) for language detection. Updated `_detect_client_language()` to use this when `[客户]` is present.
   - **Impact:** English add-car (e.g. "I bought a new BMW X5, how much is insurance?") now receives English first reply and English handoff message instead of Chinese.

2. **Handoff reply language**
   - Replaced `language = "zh" if _contains_chinese(merged_text) else "en"` with `language = _detect_client_language(merged_text)` for handoff reply selection.
   - Ensures handoff message matches customer language (English or Chinese).

### Frontend (`ui/src/pages/UnifiedIntakePage.tsx`)

3. **Broker case card "Collected:" display**
   - When `conversation_summary` contains "Collected:", display that line below "Your next move" in the case card.
   - UI-only; uses existing backend data. No new API fields.

### Docs

4. **`docs/UNIFIED_INTAKE_DEMO_READINESS.md`**
   - Added "Today's 3 focus chains" subsection listing BMW X5, payment failed, and English notice/DMV-SR22 with walkthrough hints.

---

## 3. Chain-by-chain results

### Chain 1: BMW X5 / new car quote

| Metric | Before | After |
|--------|--------|-------|
| English customer reply language | Chinese (bug) | English |
| Handoff message language | Chinese | English |
| Partial info (year only) → ask zip | ✅ | ✅ |
| Handoff after zip provided | ✅ | ✅ |
| Broker sees "Collected:" | Backend only | UI displays it |

**Result:** Strong. English path fixed; Chinese path unchanged and solid.

### Chain 2: Payment failed / cancellation risk

| Metric | Status |
|--------|--------|
| Risk recognition | ✅ payment_lapse_expiration |
| Urgency wording | ✅ "今天尽快处理，避免停保" |
| Proof/notice ask | ✅ "请把最新通知或付款截图发我" |
| Handoff after "我发了截图" | ✅ Turn 2 |
| Broker next step | ✅ "Confirm whether the payment actually failed, check whether the carrier still shows the balance due..." |

**Result:** Strong. No changes needed.

### Chain 3: English notice confusion / DMV-SR22

| Metric | Status |
|--------|--------|
| DMV/SR-22 specific reply | ✅ "把 DMV 信件发我，我先帮你确认是不是要 SR-22 filing proof..." |
| Generic notice confusion | ✅ "把完整通知或更清楚的照片发我..." |
| Handoff after notice sent | ✅ Turn 2 |
| Broker next step | ✅ "Confirm whether DMV wants SR-22 filing proof, check any deadline, and tell the client exactly what to bring..." |

**Result:** Strong. No changes needed.

---

## 4. Validation summary

| Check | Result |
|-------|--------|
| `npm run build` (ui/) | ✅ PASS |
| `run_inbox_triage_scenarios.py` (32 scenarios) | ✅ 32/32 |
| `run_chen_kui_proxy_calibration.py` (14 cases) | ✅ 14/14 |
| `run_multi_turn_simulations.py` (14 sims) | ✅ 14/14 Strong |
| `test_inbox_triage_api.py` | ✅ All API tests passed |
| `guardrail_inbox_triage.sh` | ✅ PASS |
| `unified_intake_smoke_check.sh` | ✅ PASS |

---

## 5. Business/demo impact

- **Sellability:** English-speaking customers (e.g. "I bought a new BMW X5") now get English replies end-to-end. Reduces confusion and improves perceived professionalism.
- **Broker clarity:** "Collected:" line visible on add-car cases helps broker see at a glance what was gathered.
- **3 chains:** All three focus chains work end-to-end with correct intent detection, next-ask logic, and handoff timing.

---

## 6. Remaining issues

- **None blocking.** All 3 chains are demo-ready.
- **Optional future:** MT7 (DMV notice confusion) first reply could add "英文通知有些术语看不懂很正常" for explicit English-notice reassurance when `_is_english_notice_confusion` is true but `_is_sr22_help_request` is false. Low priority; current reply is acceptable.

---

## 7. Recommended next step

1. **Demo:** Run the 3 focus chains in UI for founder demo. Use `docs/UNIFIED_INTAKE_DEMO_READINESS.md` §4.
2. **No further code changes** for these 3 chains unless new edge cases appear.
3. **Defer:** OCR, inbox sync, auth, progressive_answers struct, workbench redesign.

---

## 8. 中文或中英混合宏观总结

**今天 3 条链路分别修了什么：**

1. **BMW X5 / 新车报价：** 修了英文客户收到中文回复的 bug。现在英文客户（如 "I bought a new BMW X5, how much is insurance?"）全程收到英文回复；中文客户不变。加车 partial 场景（先给年份，再给 zip）逻辑正常，会先问 zip 再 handoff。
2. **付款失败 / 取消风险：** 未改代码。风险识别、紧急措辞、proof 索取、handoff 时机均正常。
3. **英文 notice 困惑 / DMV-SR22：** 未改代码。DMV/SR-22 专用回复、通用 notice 困惑回复、handoff 逻辑均正常。

**哪条链路提升最大：** BMW X5 英文链路。之前英文客户会收到中文回复，体验差；现在全程英文，明显提升。

**还有什么地方没完全顺：** 无阻塞问题。MT7 若想更精细，可在「英文 notice 看不懂」场景加一句「英文通知有些术语看不懂很正常」的安抚语，属可选优化。

**现在最适合怎么展示：** 按 `UNIFIED_INTAKE_DEMO_READINESS.md` §4 的 3 条 focus chain 顺序：先 BMW X5（中英各一次），再 payment failed，再 DMV/SR-22。每条 2 轮对话即可 handoff，broker 端可见清晰 case card。

---

## 9. 如何打开前端 / 后端

### Run commands

```bash
# Start demo (backend + frontend)
bash scripts/run_demo_local.sh

# Pre-demo checklist
bash scripts/demo_pre_checklist.sh

# Validation (no server needed for most)
LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py
LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_chen_kui_proxy_calibration.py
LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py
bash scripts/guardrail_inbox_triage.sh
bash scripts/unified_intake_smoke_check.sh
```

### URLs

| Surface | URL |
|---------|-----|
| **Frontend (Unified Intake)** | http://localhost:5173/workbench/unified-intake |
| **Backend API** | http://localhost:8001 |
| **Health** | http://localhost:8001/healthz |

### Port caveats

- **Default:** Backend 8001, frontend 5173 (Vite).
- **Docker:** Backend 8000 when using `docker compose up rag-api`.
- If frontend runs on a different port (e.g. 5174), use the URL shown in the Vite terminal.

---

## 10. 3 条链路 walkthroughs

### Chain 1: BMW X5 / new car quote (English)

| Turn | Role | Content |
|------|------|---------|
| 1 | Customer | I bought a new BMW X5, how much is insurance? |
| 1 | System | I can start a quote for the new car. Send me the year, make/model, VIN if you have it, delivery date, zip or address, and main driver and I will check it. |
| 2 | Customer | 2024, 90210, picking up next week |
| 2 | System | Quote details received. Our office will review and follow up with you. |

**Handoff:** Yes, after turn 2.  
**Broker receives:** `source_text` (full conversation), `conversation_summary` with "Add-car / new vehicle quote. Collected: year, model, zip, delivery. 2 customer message(s)...", `broker_next_step`: "Collect the new vehicle details, confirm the delivery date and primary driver, then quote or add it the same day if possible."  
**Result:** Strong.

---

### Chain 1b: BMW X5 (Chinese, partial → ask zip → handoff)

| Turn | Role | Content |
|------|------|---------|
| 1 | Customer | 我买了台宝马X5，想问下保费多少钱 |
| 1 | System | 可以先帮你看这台车的报价。把车子的年份、车型、VIN（有的话）、提车日期、地址邮编和主要驾驶人发我，我先帮你算。 |
| 2 | Customer | 2024年的 |
| 2 | System | 把地址邮编发我，我先帮你算。 |
| 3 | Customer | 90210 |
| 3 | System | 报价资料已收集，办公室会尽快出价，有结果会联系您。 |

**Handoff:** Yes, after turn 3.  
**Broker receives:** Full conversation; "Collected: year, model, zip"; broker_next_step for add-car.  
**Result:** Strong.

---

### Chain 2: Payment failed / cancellation risk

| Turn | Role | Content |
|------|------|---------|
| 1 | Customer | 客户问：这个英文 notice 说 payment failed，我现在怎么办？ |
| 1 | System | 这看起来是付款出了问题。请把最新通知或付款截图发我，我先帮你确认；如果还没付，今天尽快处理，避免停保。 |
| 2 | Customer | 我发了截图在微信 |
| 2 | System | 办公室会尽快处理，有结果会联系您。 |

**Handoff:** Yes, after turn 2.  
**Broker receives:** `payment_lapse_expiration`, urgency high, `broker_next_step`: "Confirm whether the payment actually failed, check whether the carrier still shows the balance due, and help the client fix it today."  
**Result:** Strong.

---

### Chain 3: English notice confusion / DMV-SR22

| Turn | Role | Content |
|------|------|---------|
| 1 | Customer | DMV信说要 SR-22 proof 才能 clear suspension，这个要带什么？ |
| 1 | System | 把 DMV 信件发我，我先帮你确认是不是要 SR-22 filing proof（SR-22备案证明），再告诉你要带什么。 |
| 2 | Customer | 通知我发你了，你看下 |
| 2 | System | 办公室会尽快处理，有结果会联系您。 |

**Handoff:** Yes, after turn 2.  
**Broker receives:** `customer_question`, `broker_next_step`: "Confirm whether DMV wants SR-22 filing proof, check any deadline, and tell the client exactly what to bring or what still needs to be filed."  
**Result:** Strong.

---

*End of sprint report*
