# Client Pack Foundation Sprint Report

**Sprint:** Client Pack Foundation Sprint  
**Date:** 2026-03-09  
**Mission:** Create the first practical "client pack foundation" with common base → industry pack → client pack layering.

---

## 1. Stages Completed

| Stage | Status | Notes |
|-------|--------|-------|
| **Stage 1** — Define package model | **Completed** | Created `docs/CLIENT_PACK_FOUNDATION.md` |
| **Stage 2** — Improve config structure | **Completed** | Updated config READMEs, added package layer table to `configs/README.md` |
| **Stage 3** — Define and implement load/override order | **Completed** | Documented in config_loader, CLIENT_PACK_FOUNDATION.md |
| **Stage 4** — Extract one more high-value slice | **Completed** | Extracted `cancellation_warning` to industry reply_templates.json |
| **Stage 5** — Validate product stability | **Completed** | All validations passed |
| **Stage 6** — Audit + report | **Completed** | This report |

**Skipped:** None.

---

## 2. Package Model Definition

### Common Platform Base

- **Intake skeleton:** detect → ask → enough? → hand off (implemented in triage.py)
- **Shared workflow conventions:** docs/MATURE_INTAKE_SKELETON.md, CUSTOMER_ENTRY_REPLY_STRATEGY.md
- **Shared persistence:** case_store.py, data/unified_intake_cases.json
- **Shared test framework:** run_inbox_triage_scenarios.py, run_multi_turn_simulations.py, etc.
- **Common config:** Placeholder; no files yet. Workflow defaults remain in code.

### Insurance Industry Pack

- **Markers:** configs/industries/insurance/markers.json (intent detection)
- **Reply templates:** configs/industries/insurance/reply_templates.json — now includes cancellation_warning, add_car, payment_lapse_expiration, missing_document, english_notice_confusion, premium_review, remove_vehicle
- **Document items:** In markers.json (dec page, garaging proof, SR-22, etc.)

### Chen Kui Client Pack

- **Handoff phrases:** configs/clients/chen_kui/handoff_phrases.json (add_car / other, zh / en)
- **Reply overrides:** configs/clients/chen_kui/reply_overrides.json (optional merge into industry templates)
- **Proxy calibration:** configs/chen_kui_proxy_calibration_cases.json

---

## 3. Config / Loader Changes

| File | Change |
|------|--------|
| `docs/CLIENT_PACK_FOUNDATION.md` | **Created** — Practical package model, load order, what is hardcoded |
| `configs/README.md` | **Updated** — Added package layers table, link to CLIENT_PACK_FOUNDATION |
| `configs/common/README.md` | **Updated** — Clarified what belongs in common |
| `configs/industries/insurance/README.md` | **Updated** — Load order, full template list including cancellation_warning |
| `configs/clients/chen_kui/README.md` | **Updated** — Load order, merge behavior |
| `configs/industries/insurance/reply_templates.json` | **Updated** — Added cancellation_warning (zh/en) |
| `services/fiqa_api/inbox_triage/config_loader.py` | **Updated** — Module docstring and get_reply_templates docstring with load order |
| `services/fiqa_api/inbox_triage/triage.py` | **Updated** — cancellation_warning now uses config with fallback |
| `docs/CONFIG_EXTRACTION_GUIDE.md` | **Updated** — cancellation_warning in extracted list, removed from hardcoded |
| `docs/PROJECT_DOC_SYSTEM_MAP.md` | **Updated** — Added CLIENT_PACK_FOUNDATION to primary docs |
| `docs/runbooks/UNIFIED_INTAKE_MVP_RUNBOOK.md` | **Updated** — Config layer section references CLIENT_PACK_FOUNDATION |

---

## 4. Implemented Package Layering

| Area | Behavior |
|------|----------|
| **Reply templates** | Industry base → client overrides (shallow merge). cancellation_warning, add_car, payment_lapse_expiration, missing_document, english_notice_confusion, premium_review, remove_vehicle all config-driven. |
| **Handoff phrases** | Client-only. Chen Kui pack is source; fallback in code if missing. |
| **Markers** | Industry-only. No client override. |
| **Still hardcoded** | broker_next_step, client_prep, VALID_CATEGORIES, handoff thresholds, classification logic, missing_signature/underwriting/renewal/unclear/informational reply strings |

---

## 5. Validation Summary

| Check | Result | Protects |
|-------|--------|----------|
| `cd ui && npm run build` | **PASS** | UI builds |
| `run_inbox_triage_scenarios.py` | **40/40 passed** | Category, urgency, draft shape |
| `run_chen_kui_proxy_calibration.py` | **14/14 passed** | Chen Kui draft style |
| `run_multi_turn_simulations.py` | **14/14 passed** | Handoff flow, multi-turn |
| `guardrail_inbox_triage.sh` | **PASS** | Scenario pack, API test, persistence, multi-turn |
| `unified_intake_smoke_check.sh` | **PASS** | Full guardrail + manual smoke steps |
| `test_inbox_triage_api.py` | **PASS** (server on 8001) | API contract, cancellation_warning scenario |

---

## 6. Business / Platform Value

- **Reduces confusion:** One doc (CLIENT_PACK_FOUNDATION) explains common / industry / client. Config READMEs align to it.
- **Supports future reuse:** New client = new folder + handoff_phrases + optional reply_overrides. New industry = new folder + markers + reply_templates.
- **Helps packaging:** Package boundaries are explicit. Insurance pack and Chen Kui pack are real, not theoretical.

---

## 7. Remaining Blockers

1. **No runtime client/industry switch** — Paths are fixed to `insurance` and `chen_kui`.
2. **Common base has no config files** — Workflow defaults (max_turns, etc.) remain in code.
3. **Several category reply templates still hardcoded** — missing_signature, underwriting, renewal, unclear, informational, policy_delay_pending.

---

## 8. Recommended Next Step

**Add env-based client selection:** Introduce `CLIENT_PACK` (default `chen_kui`) and `INDUSTRY_PACK` (default `insurance`) env vars. config_loader reads them to choose paths. No UI change; enables future multi-client without code change.

---

## 9. 中文或中英混合宏观总结

**这次 common / industry / client 三层是不是更真实了？**  
是的。Industry 和 client 两层已经有真实配置文件和加载顺序；common 层还是占位，但边界写清楚了。

**哪些东西现在更像「客户包」了？**  
Chen Kui 的 handoff_phrases 和 reply_overrides 已经是客户包；新增的 cancellation_warning 在 industry 层，说明 industry 和 client 的边界更清晰。

**哪些东西还只是未来结构？**  
common 层没有配置文件；没有 runtime 的 client/industry 切换；handoff thresholds 还在代码里。

**有没有困难或限制？**  
没有大困难。保持小步迭代，不做过度的抽象。

**这次对以后卖给别的客户有没有真实帮助？**  
有。新客户只需要新建 `configs/clients/<client_id>/`，放 handoff_phrases 和可选的 reply_overrides，结构已经就绪。文档也写清楚了如何添加新客户和新行业。

---

## 10. Practical Package Cheat Sheet

| Layer | What lives there |
|-------|------------------|
| **Common base** | (Future) workflow defaults, shared labels. Today: code only. |
| **Insurance pack** | markers.json, reply_templates.json (cancellation_warning, add_car, payment_lapse, missing_document, english_notice_confusion, premium_review, remove_vehicle) |
| **Chen Kui pack** | handoff_phrases.json, reply_overrides.json |
| **Still hardcoded** | broker_next_step, client_prep, handoff thresholds, VALID_CATEGORIES, missing_signature/underwriting/renewal/unclear/informational reply strings |
| **Probably moves next** | missing_signature, underwriting, renewal to industry reply_templates; env-based client/industry selection |

---

## 11. Future Hot-Swap Summary

| Now more swappable | Still not swappable |
|-------------------|---------------------|
| Reply templates (industry + client override) | Runtime client/industry switch |
| Handoff phrases (client) | Handoff thresholds |
| Intent markers (industry) | broker_next_step, client_prep |
| Document item labels (industry) | Classification logic |

**Next package-building step:** Env vars `CLIENT_PACK` and `INDUSTRY_PACK` so config_loader can load a different client or industry without code change.

---

*End of report*
