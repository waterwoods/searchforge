# Core Reply Template Expansion Sprint Report

**Sprint:** Core Reply Template Expansion Sprint  
**Date:** 2026-03-09  
**Mission:** Expand the config-driven reply template layer by extracting the next highest-value reply templates (english_notice_confusion, premium_review, remove_vehicle) out of hardcoded logic, while keeping the Chen Kui insurance mainline stable.

---

## 1. Stages completed

| Stage | Status | Notes |
|-------|--------|-------|
| Stage 1 — Choose the next safe template expansion slice | Completed | Selected english_notice_confusion, premium_review, remove_vehicle |
| Stage 2 — Expand the template config structure | Completed | Extended reply_templates.json with 3 new templates |
| Stage 3 — Extract the chosen templates into config | Completed | triage.py uses config lookup with fallback |
| Stage 4 — Clarify industry vs client override boundaries | Completed | CONFIG_EXTRACTION_GUIDE.md updated |
| Stage 5 — Validate product stability | Completed | All validation scripts passed |
| Stage 6 — Audit + cleanup judgment | Completed | Accept verdict |

---

## 2. Chosen expansion slice

**Selected:**
1. **english_notice_confusion** — Client confused by English notice; wants explanation
2. **premium_review** — Premium too high / renewal review request
3. **remove_vehicle** — Remove sold vehicle from policy

**Why high-value:**
- **english_notice_confusion:** Common when Chinese-speaking clients receive English carrier notices. Strongly affects perceived usefulness; different brokers may want different reassurance tone.
- **premium_review:** High-frequency scenario; tone (softer vs firmer) varies by broker.
- **remove_vehicle:** Same pattern as add_car; clearly swappable, low risk.

**Why safe:** Simple zh/en structure, no interpolation, clear intent detection already exists. All three follow the same lookup pattern as add_car.

---

## 3. Config structure changes

| Path | Change |
|------|--------|
| `configs/industries/insurance/reply_templates.json` | Added english_notice_confusion, premium_review, remove_vehicle (zh/en each) |
| `configs/clients/chen_kui/reply_overrides.json` | Unchanged (overrides empty; uses industry defaults) |
| `services/fiqa_api/inbox_triage/triage.py` | _build_client_reply_draft uses config lookup for the 3 templates with fallback |
| `docs/CONFIG_EXTRACTION_GUIDE.md` | Updated extracted list, remaining hardcoded, per-template placement |

---

## 4. Extracted template behavior

**Moved out of hardcoded logic:**
- english_notice_confusion: zh, en
- premium_review: zh, en
- remove_vehicle: zh, en

**Duplicated logic removed:** The exact hardcoded return strings were replaced with config lookup. Fallback strings retained in code (e.g. `t.get("zh") or "..."`) so behavior is stable if config is missing.

**Still hardcoded:** cancellation_warning, missing_signature, underwriting_followup, renewal_reminder, dmv (low_risk_dmv_status, sr22_help), unclear, informational, policy_delay_pending, generic customer_question fallback.

**Boundary now clearer:** Industry defaults for these three live in reply_templates.json; client can override via reply_overrides.json.

---

## 5. Common / industry / client split

| Layer | What | Example |
|-------|------|---------|
| **Common** | (placeholder) | — |
| **Industry** | Base wording for insurance scenarios | english_notice_confusion, premium_review, remove_vehicle in reply_templates.json |
| **Client** | Optional phrasing overrides | reply_overrides.json (empty = use industry) |

**Per-template placement:**
- **english_notice_confusion:** Industry — common when Chinese-speaking clients get English notices; any broker may tweak tone.
- **premium_review:** Industry — premium-too-high concern; client may want softer/stronger reassurance.
- **remove_vehicle:** Industry — same pattern as add_car; client may vary phrasing.

---

## 6. Validation summary

| Check | Result |
|-------|--------|
| `npm run build` (ui/) | Pass |
| `run_inbox_triage_scenarios.py` | 40/40 passed |
| `run_chen_kui_proxy_calibration.py` | 14/14 passed |
| `run_multi_turn_simulations.py` | 14 strong |
| `run_expression_robustness.py` | (in guardrail) |
| `test_inbox_triage_api.py` | All passed |
| `guardrail_inbox_triage.sh` | PASS |
| `unified_intake_smoke_check.sh` | PASS |

**Spot-checks verified:**
- english_notice_confusion: Config template used when customer_question + english notice confusion
- premium_review: Config template used (CK7, MT4 pass)
- remove_vehicle: Config template used (CK9, MT3 pass)

---

## 7. Business / platform value

- **Reduces future confusion:** Contributors can see which reply behavior is config-driven vs hardcoded.
- **Supports reuse:** New insurance broker can edit reply_templates.json and optionally reply_overrides.json without code change.
- **Helps packaging:** One more step toward client-specific packaging; 6 reply templates now swappable (add_car, payment_lapse_expiration, missing_document, english_notice_confusion, premium_review, remove_vehicle).

---

## 8. Remaining blocker(s)

1. No runtime client/industry selection
2. Other reply templates still hardcoded (cancellation_warning, dmv, unclear, etc.)
3. broker_next_step, client_prep still in code

---

## 9. Recommended next step

Extract **cancellation_warning** next — high demo value, urgent tone, client-sensitive.

---

## 10. 中文或中英混合宏观总结

**这次抽出来的：** english_notice_confusion（英文通知看不懂）、premium_review（保费太高想降）、remove_vehicle（删车/卖车从保单拿掉）三个 reply template，中英各一份。

**english_notice_confusion / premium_review 现在更可替换了：** 是的。这两个场景的回复 wording 已从 triage.py 移到 config，可通过 reply_templates.json 修改，client 可通过 reply_overrides.json 覆盖。

**删掉的旧逻辑 / 保留的 fallback：** 没有删掉逻辑，只把硬编码的 return 字符串换成 config 查找；查找不到时仍用原字符串作为 fallback，保证 config 缺失时行为不变。

**有没有困难或限制：** 无。抽取范围窄，结构简单，验证全部通过。

**这次抽取有真实价值：** 有。6 个高频场景的回复现已可配置，未来换 client 或换 wording 不用改代码。

---

## 11. Practical template config cheat sheet

| What | Where |
|------|-------|
| **Insurance reply templates** | `configs/industries/insurance/reply_templates.json` |
| **Chen Kui overrides** | `configs/clients/chen_kui/reply_overrides.json` |
| **Config loader** | `services/fiqa_api/inbox_triage/config_loader.py` → `get_reply_templates()` |
| **Still in code** | cancellation_warning, missing_signature, underwriting, renewal, dmv, unclear, informational, policy_delay_pending, generic customer_question fallback |
| **May move later** | cancellation_warning, dmv (low_risk + sr22), unclear |

**Extracted keys (6):** add_car, payment_lapse_expiration, missing_document, english_notice_confusion, premium_review, remove_vehicle

---

## 12. Future reuse summary

**Now more swappable:**
- english_notice_confusion, premium_review, remove_vehicle reply wording
- All 6 reply templates editable via config
- Client override path available

**Still not swappable:**
- cancellation_warning, missing_signature, underwriting, renewal, dmv, unclear, informational, policy_delay_pending
- broker_next_step, client_prep
- Handoff thresholds, classification rules

**Next extraction slice:** cancellation_warning (high demo value, urgent tone).

---

*End of report*
