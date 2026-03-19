# Reply Template Extraction Sprint Report

**Sprint:** Reply Template Extraction Sprint  
**Date:** 2026-03-09  
**Mission:** Extract a first meaningful slice of customer-facing reply templates out of hardcoded logic into config, while keeping Chen Kui insurance mainline stable.

---

## 1. Stages completed

| Stage | Status | Notes |
|-------|--------|-------|
| Stage 1 — Choose first template extraction slice | Completed | Selected add_car, payment_lapse_expiration, missing_document |
| Stage 2 — Create template config structure | Completed | reply_templates.json (industry), reply_overrides.json (client) |
| Stage 3 — Extract chosen templates into config | Completed | Config created; triage loads with fallback |
| Stage 4 — Define common/industry/client boundaries | Completed | CONFIG_EXTRACTION_GUIDE.md updated |
| Stage 5 — Validate product stability | Completed | npm build, proxy calibration, multi-turn, expression robustness passed |
| Stage 6 — Audit + cleanup judgment | Completed | Accept verdict |

---

## 2. Chosen template extraction slice

**Selected:**
1. **add_car** — First-turn reply when customer asks for new-car quote (BMW X5 demo scenario)
2. **payment_lapse_expiration** — Urgent reply when payment failed / cancellation risk
3. **missing_document** — Reply when carrier/UW requested item (declaration page, garaging proof, etc.)

**Why:** High demo value, high business value, clearly client/industry-specific, stable, low risk.

---

## 3. Config structure changes

| Path | Purpose |
|------|---------|
| configs/industries/insurance/reply_templates.json | Industry reply templates (add_car, payment_lapse_expiration, missing_document) |
| configs/clients/chen_kui/reply_overrides.json | Optional client overrides |
| config_loader.py | Added get_reply_templates() |
| triage.py | _build_client_reply_draft uses config when present |
| CONFIG_EXTRACTION_GUIDE.md | Updated |

---

## 4. Extracted template behavior

**Moved out:** add_car, payment_lapse_expiration, missing_document (zh/en, with/without item).

**Still hardcoded:** cancellation_warning, missing_signature, underwriting, renewal, dmv, premium_review, remove_vehicle, english_notice_confusion, unclear, informational.

**Duplicated logic removed:** None. Fallback preserved.

---

## 5. Common / industry / client split

- **Industry:** reply_templates.json — base wording for insurance scenarios
- **Client:** reply_overrides.json — optional overrides
- **Common:** placeholder

---

## 6. Validation summary

- npm run build: Pass
- run_chen_kui_proxy_calibration.py: 14/14 passed
- run_multi_turn_simulations.py: 14 strong
- run_expression_robustness.py: 36 strong

---

## 7. Business / platform value

Reply behavior is now partly swappable. New broker can edit config without code change.

---

## 8. Remaining blocker(s)

1. No runtime client/industry selection
2. Other reply templates still hardcoded
3. broker_next_step, client_prep still in code

---

## 9. Recommended next step

Extract english_notice_confusion and premium_review next.

---

## 10. 中文或中英混合宏观总结

**抽出来了：** 加车、付款风险、缺材料的首轮回复（中英）。

**industry/client 更清楚了：** industry=模板，client=可选覆盖。

**没删旧逻辑，保留 fallback。**

**有真实价值：** 高频场景 wording 可配置。

---

## 11. Practical template config cheat sheet

| Config | Where |
|--------|-------|
| Insurance reply templates | configs/industries/insurance/reply_templates.json |
| Chen Kui overrides | configs/clients/chen_kui/reply_overrides.json |
| Still in code | Other category replies in triage.py |

---

## 12. Future reuse summary

add_car, payment_lapse_expiration, missing_document replies: Hot-swappable via config.  
Other replies: Still in code. Next: english_notice_confusion, premium_review.
