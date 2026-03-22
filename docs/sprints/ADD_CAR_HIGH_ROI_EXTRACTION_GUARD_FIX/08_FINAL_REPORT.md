# Add-Car High-ROI Extraction + Intent Guard Fix Report

## 1. Sprint theme

- **Fixed:** ZIP detection beside Chinese, driver micro-phrases, false `already_sent` on question-like “要不要发你” wording.
- **Why now:** Scenario battery showed “almost right” failures that directly hurt broker trust on high-frequency WeChat patterns.

## 2. Baseline audit

- **ZIP weakness:** `\b9[0-9]{4}\b` missed `邮编95131` (no word boundary before `9`).
- **Driver weakness:** `我自己开` does not contain consecutive `我开`; `儿子开`/`女儿开` under-covered vs `孩子开`.
- **already_sent weakness:** Tuple marker `发你` matched inside `要不要发你`.
- **Root causes:** Brittle regex boundary; incomplete lexicon; keyword-only follow-up typing without intent guard.

## 3. What was changed

- **File:** `services/fiqa_api/inbox_triage/triage.py`
- **ZIP:** `_CA_ZIP_STRICT_RE`, `_text_has_ca_zip_signal`, `_extract_ca_zip_from_message`; `_extract_add_car_fields`, fast path, acknowledgements updated.
- **Driver:** `_ADD_CAR_DRIVER_MARKERS`, `_text_has_add_car_driver_signal`; `has_additional_drivers` includes `儿子开`/`女儿开`.
- **already_sent:** `_is_prospective_send_offer_message` + early `new_info` return before `sent_markers` in `_derive_follow_up_type`.
- **Regression:** `docs/sprints/ADD_CAR_HIGH_ROI_EXTRACTION_GUARD_FIX/regression_scenarios.json`, `scripts/run_add_car_high_roi_regression.py`.

## 4. Validation summary

Executed with `LLM_GENERATION_ENABLED=false` where applicable:

| Command | Result |
|---------|--------|
| `bash scripts/guardrail_inbox_triage.sh` | **PASS** (includes 64 scenario pack, API checks, 69 multi-turn, stress/handoff packs, etc.) |
| `python3 scripts/run_multi_turn_simulations.py` | **PASS** — 69 strong |
| `python3 scripts/run_add_car_edge_case_simulations.py` | **PASS** — 18 strong |
| `python3 scripts/run_add_car_scenario_battery.py` | **PASS** — 17/17 scenarios |
| `python3 scripts/run_add_car_high_roi_regression.py` | **PASS** — 13/13 |
| `python3 scripts/audit_state_field_accuracy.py` | **PASS** — 9/9 |

**Weak scenarios fixed:** `ACB-C03` (and any path depending on `邮编95131`-style ZIP) now reaches quote-ready when delivery + driver are present; `要不要发你`-style wording no longer forces `already_sent`.

**Regressions observed:** None in the above suite.

## 5. Before vs After

| Input | Before (typical) | After |
|-------|------------------|--------|
| `邮编95131` | zip often false | zip true |
| `我自己开` | driver often false | driver true |
| `要不要发你` | `already_sent` | `new_info` |
| `材料发你微信了` | `already_sent` | `already_sent` |

## 6. Biggest improvement

Add-car **slot filling** and **follow-up tone** align with how clients actually type: Chinese glued to digits, ultra-short driver replies, and modal questions about sending.

## 7. Biggest remaining weakness

Prospective-send patterns are **regex-scoped**; rare colloquial offers may still hit `发你` until another targeted phrase is added. ZIP remains **9xxxx-focused** (product scope unchanged).

## 8. Deployment judgment

- **Backend redeploy:** **Yes** — `triage.py` is server-side logic.
- **Frontend redeploy:** **No** — no UI changes in this sprint.

## 9. Founder test cases (copy-paste after deploy)

1. `想加一台2024 Tesla Model Y，先帮我报个价` → then `邮编95131，明天拿车，就我一个人开`
2. `加车 2022 Honda Accord，90210` → then `我自己开`
3. `要不要发你` (after any add-car collect thread) — should **not** open “you already sent” reassurance as primary path
4. `材料发你微信了` — should stay **already_sent** / verify materials tone
5. `zip 95131` as only new detail after add-car opener — zip should register

## 10. 中文宏观总结

以前容易错，主要是因为：邮编贴在汉字后面时，老的“单词边界”规则认不出来；像“我自己开”这种短句并不包含连续的“我开”；而“要不要发你”里刚好带了“发你”两个字，被系统误当成“已经发过了”。这次用 **提取→规范化→校验** 的思路改了邮编识别，用 **可维护词表** 补了常见驾驶人说法，并在判断 **already_sent** 之前加了 **“是不是在问要不要发”** 的意图护栏。修完之后，这几类高频微信说法会明显更稳。仍然没做的是：把所有口语变体一次性穷举（仍靠后续遇到再补小规则），以及把邮编扩到全美所有格式（当前仍以加州常见的 9xxxx 为主）。
