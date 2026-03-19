# State / Field Accuracy Audit + Tighten Sprint Report

**Sprint:** State / Field Accuracy Audit + Tighten  
**Date:** 2026-03-12  
**Budget:** 10–15 minutes  
**Scope:** Chen Kui Insurance Unified Entry — lightweight state layer, field extraction, reply routing

---

## 1. State audit

### Flows by strength

| Flow | Strength | Notes |
|------|----------|-------|
| **Add-car / quote** | Strong | follow_up_type correct (new_info, already_sent); collection_stage; collected_fields (year, make_model, zip, delivery_date) accurate |
| **Claim intake** | Strong | accident_reported, photos, other_driver_info extracted; already_sent when customer says "发你微信" |
| **Renewal / premium** | Strong | premium_concern, policy_bill_sent; already_sent when "发你微信" |
| **Missing document** | Acceptable → Strong (after fixes) | SIM2 "garaging 是什么意思" was mis-classifying customer_says_sent_garaging; fixed with item-specific clarification check |
| **Cancellation / payment risk** | Acceptable → Strong (after fixes) | No structured fields before; added _cancellation_structured_fields; "需要再发什么给你吗" was new_info → fixed to clarification_question |

### Where state signals were inaccurate (before fixes)

1. **follow_up_type:** "需要再发什么给你吗" (do I need to send you anything?) was falling through to `new_info` or matching `already_sent` via "发你" — wrong. Should be `clarification_question`.
2. **collected_fields (missing doc):** "declaration page 发你了，garaging 是什么意思" was adding `customer_says_sent_garaging_proof` because "是什么意思" was treated as global clarification — wrong. Clarification is item-specific.
3. **collected_fields (cancellation):** Cancellation/payment flows had no structured fields — broker saw empty Collected/Still needed.

---

## 2. Field extraction audit

### Accurate

- **Add-car:** year, make_model, zip, delivery_date, primary_driver, vin
- **Claim:** accident_reported, hit_and_run, photos, other_driver_info, police_report, injuries
- **Renewal:** premium_concern, renewal_context, remove_vehicle_interest, policy_bill_sent
- **Missing doc:** requested_*, customer_says_sent_* (after item-specific clarification fix)

### Weak before fixes (now improved)

- **Cancellation:** No structured fields → added notice_present, screenshot_sent, already_paid_claimed, urgency_due_confusion
- **Missing doc:** customer_says_sent_garaging when customer asked "garaging 是什么意思" → fixed with item-specific clarification

### Most risky (still to watch)

- **Renewal policy_bill_sent:** Uses broad "发" — could over-trigger if customer says "要发什么" in renewal context. Mitigated: clarification_markers checked before sent.
- **Claim photos/other_driver:** Partial info ("有照片但对方保险还没拿到") — still_needed correctly includes other_driver_insurance_license.

---

## 3. Root causes

| Problem | Root cause |
|---------|------------|
| "需要再发什么" → wrong type | No clarification marker for "发什么" / "需要再发"; "发你" in sent_markers matched first |
| customer_says_sent_garaging when asking "garaging 是什么意思" | Global "什么意思" check treated whole message as clarification; needed item-specific patterns |
| Cancellation empty structured | No _cancellation_structured_fields; else branch returned [] |

---

## 4. Fixes made

| File | Change |
|------|--------|
| `services/fiqa_api/inbox_triage/triage.py` | Added "发什么", "需要再发", "再发什么" to clarification_markers (before sent_markers) |
| `services/fiqa_api/inbox_triage/triage.py` | Item-specific clarification: is_dec_clarification, is_garaging_clarification, is_dl_clarification — only when question names that item |
| `services/fiqa_api/inbox_triage/triage.py` | Added _extract_cancellation_fields, _cancellation_structured_fields |
| `services/fiqa_api/inbox_triage/triage.py` | Wired cancellation/payment_lapse to _cancellation_structured_fields in triage_conversation |
| `services/fiqa_api/routes/inbox_triage.py` | Wired _cancellation_structured_fields for single-message triage (triage_message path) |
| `scripts/audit_state_field_accuracy.py` | New audit script for state/field accuracy (7 targeted cases) |

---

## 5. Before vs after

| Scenario | Before | After |
|----------|--------|-------|
| MT6 "需要再发什么给你吗" | new_info or already_sent | clarification_question |
| M1 "declaration page 发你了，garaging 是什么意思" | customer_says_sent_garaging (wrong) | customer_says_sent_declaration_page only |
| C1 "我昨天付了，截图发你" | collected=[] | screenshot_sent, already_paid_claimed |
| C2 "需要再发什么给你吗" | new_info | clarification_question |

---

## 6. Validation summary

| Check | Result |
|-------|--------|
| `run_inbox_triage_scenarios.py` | 49/49 passed |
| `run_multi_turn_simulations.py` | 38/38 strong |
| `guardrail_inbox_triage.sh` | PASS |
| `audit_state_field_accuracy.py` | 7/7 passed |
| `unified_intake_smoke_check.sh` | Guardrail PASS (manual UI steps printed) |

---

## 7. Redeploy readiness

- **Backend:** Yes — triage.py, routes/inbox_triage.py
- **Frontend:** No changes
- **Redeploy:** Backend only

---

## 8. 中文总结

**轻量状态机现在到底稳不稳：**  
较稳。follow_up_type 在主要场景下正确；"需要再发什么" 等澄清类问题已归为 clarification_question；"发你了" 仍正确归为 already_sent。

**字段提取哪里最准，哪里还不够准：**  
- 最准：add-car（year/model/zip/delivery）、claim（accident/photos/other_driver）、renewal（premium_concern/policy_bill_sent）  
- 已改进：missing doc 不再把「garaging 是什么意思」误判为已发送；cancellation 新增 notice/screenshot/paid 等字段

**这次修了哪几个最值钱的点：**  
1. 「需要再发什么给你吗」→ clarification（不再误判为已发送）  
2. 「declaration page 发你了，garaging 是什么意思」→ 只标记 dec 已发，不标记 garaging 已发  
3. 取消/付款风险流程增加 structured fields（notice_present, screenshot_sent, already_paid_claimed）

**下一步还最该补什么：**  
1. 在 UI 中展示 follow_up_type（如「澄清问题」「已发送」）  
2. 对 renewal 的 policy_bill_sent 做更细的边界测试  
3. 对 claim 的「部分信息」场景（有照片无对方保险）做更多回归测试
