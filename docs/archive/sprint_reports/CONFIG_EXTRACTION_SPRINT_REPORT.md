# Config Extraction Sprint Report

**Sprint:** Config Extraction Sprint  
**Date:** 2026-03-09  
**Mission:** Extract first practical slice of client- and scenario-specific behavior into config, without breaking Chen Kui insurance mainline.

---

## 1. Stages completed

| Stage | Status | Notes |
|-------|--------|-------|
| Stage 1 — Choose first safe extraction slice | ✅ Completed | Selected intent markers (industry) + handoff phrases (client) |
| Stage 2 — Create config structure | ✅ Completed | `configs/common/`, `configs/industries/insurance/`, `configs/clients/chen_kui/` |
| Stage 3 — Extract chosen behavior | ✅ Completed | Markers and handoff phrases moved to config; triage loads with fallback |
| Stage 4 — Define common/industry/client boundary | ✅ Completed | `docs/CONFIG_EXTRACTION_GUIDE.md` created |
| Stage 5 — Validate current product behavior | ✅ Completed | All validation scripts passed |
| Stage 6 — Audit + practical judgment | ✅ Completed | Accept verdict |

---

## 2. Chosen extraction slice

**Selected:**
1. **Intent markers** (industry layer) — ADD_VEHICLE_MARKERS, PAYMENT_MARKERS, DMV_HELP_MARKERS, etc. → `configs/industries/insurance/markers.json`
2. **Handoff reply strings** (client layer) — "报价资料已收集，办公室会尽快出价" / "办公室会尽快处理" → `configs/clients/chen_kui/handoff_phrases.json`

**Why:**
- Markers: Clearly industry-specific; tunable without deploy; highest value for future hot-swap
- Handoff phrases: Clearly client-specific; smallest safe slice; immediate config-layer proof

**Why high-value:**
- Markers drive intent detection; different industry = different markers
- Handoff phrases are office tone; different broker = different phrasing

---

## 3. Config structure changes

| Path | Purpose |
|------|---------|
| `configs/common/README.md` | Placeholder for future shared config |
| `configs/industries/insurance/README.md` | Describes insurance industry pack |
| `configs/industries/insurance/markers.json` | Intent markers + document_items |
| `configs/clients/chen_kui/README.md` | Describes Chen Kui client pack |
| `configs/clients/chen_kui/handoff_phrases.json` | Handoff reply strings (add_car/other, zh/en) |
| `services/fiqa_api/inbox_triage/config_loader.py` | Loads markers and handoff phrases; fallback when missing |

---

## 4. Extracted behavior

**Moved out of hardcoded logic:**
- 14 marker sets (question_help, strong_cancellation, payment, add_vehicle, etc.)
- document_items (driver's license, declaration page, garaging proof, etc.)
- 4 handoff reply strings (add_car zh/en, other zh/en)

**Still hardcoded:**
- `_build_client_reply_draft` category templates (Chinese/English per category)
- `_get_category_templates` broker_next_step, client_prep
- Handoff thresholds (`_add_car_enough_for_handoff`)
- Classification logic (`_classify_with_guardrails`)
- FORMAL_DRAFT_MARKERS, UNSENDABLE_DRAFT_MARKERS, ROBOTIC_DRAFT_MARKERS

**Boundary now clearer:** Industry = markers. Client = handoff phrasing. Common = (future) shared defaults.

---

## 5. Common / industry / client split

| Layer | What | Where |
|-------|------|-------|
| **Common** | Shared defaults | `configs/common/` (placeholder) |
| **Industry** | Intent markers, document types | `configs/industries/insurance/markers.json` |
| **Client** | Handoff phrasing, office tone | `configs/clients/chen_kui/handoff_phrases.json` |

**Future hot-swap:**
- New insurance client → new `configs/clients/<id>/handoff_phrases.json`
- New industry → new `configs/industries/<id>/markers.json` + code adaptation

---

## 6. Validation summary

| Check | Result |
|-------|--------|
| `npm run build` (ui/) | ✅ Pass |
| `run_inbox_triage_scenarios.py` | ✅ 40/40 passed |
| `run_chen_kui_proxy_calibration.py` | ✅ 14/14 passed |
| `run_multi_turn_simulations.py` | ✅ 14 strong |
| `run_expression_robustness.py` | ✅ 36 strong |
| `test_inbox_triage_api.py` | ✅ All passed |
| `guardrail_inbox_triage.sh` | ✅ PASS |
| `unified_intake_smoke_check.sh` | ✅ PASS |

**Protected:** Category/urgency regression, draft style, handoff flow, API contract, case persistence.

---

## 7. Business / platform value

- **Reduces future confusion:** Clear where markers vs phrasing live
- **Supports reuse:** New client = new handoff_phrases.json; new industry = new markers.json
- **Helps selling/packaging:** "Client pack" and "industry pack" are now real files, not just docs

---

## 8. Remaining blocker(s)

1. No runtime client/industry selection — triage always loads chen_kui + insurance
2. Category templates still in code — next extraction candidate
3. Handoff thresholds still in code — could move to industry config later

---

## 9. Recommended next step

Extract **category reply templates** (`_build_client_reply_draft` strings) to `configs/clients/chen_kui/reply_templates.json` when adding a second client. Do not do it now; wait for clear need.

---

## 10. 中文或中英混合宏观总结

**这次具体把哪一小块从硬编码里抽出来了：**
- 意图检测用的 marker 列表（加车、付款、取消、DMV 等）→ `configs/industries/insurance/markers.json`
- 交案时的回复话术（「报价资料已收集，办公室会尽快出价」等）→ `configs/clients/chen_kui/handoff_phrases.json`

**现在 common / industry / client 这三层更清楚了没有：**
- 更清楚了。industry = 保险专用 markers；client = 陈奎办公室话术；common = 占位，未来放共享默认值。

**以后换陈奎、换别的保险客户、换香肠客户时，哪些地方会更容易替换：**
- 换陈奎或换别的保险经纪：替换 `handoff_phrases.json` 即可
- 换行业（如香肠）：替换 `markers.json`，并适配 triage 逻辑

**有没有困难或限制：**
- 目前没有运行时切换 client/industry 的机制，只能改配置文件路径
- 大量 category 模板还在代码里，下次可抽

**这次抽取到底是不是有真实价值：**
- 有。markers 和 handoff 话术是典型的「换客户/换行业就要改」的内容，现在在 config 里，未来 hot-swap 更现实。

---

## 11. Practical config cheat sheet

| Config | Where |
|--------|-------|
| **Common** | `configs/common/` — placeholder only |
| **Insurance** | `configs/industries/insurance/markers.json` |
| **Chen Kui** | `configs/clients/chen_kui/handoff_phrases.json` |
| **Still in code** | Category templates, handoff thresholds, classification logic |
| **May move later** | Reply templates (`_build_client_reply_draft`), handoff thresholds |

---

## 12. Future reuse summary

| Area | Hot-swappable? |
|------|----------------|
| Intent markers | ✅ Yes — edit `markers.json` |
| Handoff phrases | ✅ Yes — edit `handoff_phrases.json` or add new client dir |
| Document items | ✅ Yes — in `markers.json` |
| Category reply templates | Partial — add_car, payment_lapse_expiration, missing_document in reply_templates.json; others still in code |
| Handoff thresholds | ❌ No — still in code |
| Classification logic | ❌ No — stays in code |

**Next extraction slice:** Category reply templates when adding second client.

---

*End of report*
expiration, missing_document reply templates to `configs/industries/insurance/reply_templates.json`. Client overrides: `configs/clients/chen_kui/reply_overrides.json`. Triage uses config when present, fallback when missing. Validation: proxy calibration, multi-turn, expression robustness passed.

**Cheat sheet:** Insurance templates → `reply_templates.json`. Chen Kui overrides → `reply_overrides.json`. Still in code → other category replies.

---

*End of report*
