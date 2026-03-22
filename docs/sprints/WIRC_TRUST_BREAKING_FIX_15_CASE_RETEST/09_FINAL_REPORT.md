# WIRC Trust-Breaking Fix + 15 Realistic Case Retest Report

## 1. Sprint theme

- **Fixed:** False “already sent” behavior on **prospective send** phrasing (VIN/截图/发你 + 可以吗/行吗/要不要…), including the **short `unclear` path** that echoed “您是说发过了吗？” on substring **发你**.
- **Why now:** Web-informed realistic traffic showed rule-based Add-Car is strong, but **one trust-breaking class** made the assistant sound **overconfident and false** — unacceptable before serious broker review.

## 2. Root-cause audit

### Biggest root cause

**Imprecise “sent” detection:** `_derive_follow_up_type` treated **bare `截图`/`screenshot`** and substring **`发你`/`发我`** as sufficient for `already_sent`. That is wrong for questions such as “我可以先发你截图吗”.

### Exact files / functions

- **`services/fiqa_api/inbox_triage/triage.py`**: `_derive_follow_up_type`; `_build_client_reply_draft` (`unclear` ≤20 chars); `_build_conversation_summary`; `_extract_cancellation_fields`; `_is_fast_path_candidate`; `triage_conversation` add-car materials / broker_next_step branches; `_is_add_vehicle_request`; `_extract_add_car_fields`; `_add_car_vehicle_concrete_from_scope`; progressive add-car draft branches (zh/en).
- **`configs/industries/insurance/markers.json`**: `vehicle_context` tokens (Nissan, Altima, 凯美瑞, 塞纳, Model Y, etc.).

### Design vs rules vs lexicon vs first-turn

| Question | Answer |
|----------|--------|
| 1) Mainly product-design? | **No.** Intended behavior was already described in code comments (prospective send polish); **marker ordering and breadth** failed. |
| 2) Mainly intent-guard / rule-logic? | **Yes.** Primary fix: **guard + completed-send predicate** replacing loose markers. |
| 3) Mainly lexicon? | **No for the trust break**; **yes for polish** on Nissan Altima / mixed naming. |
| 4) Mainly first-turn tolerance? | **Partially.** Some lines still land in `unclear` without add-car anchors; they must **not** claim “sent” (pass). Narrow routing added for **VIN + permission** and **行驶证/registration + permission**. |
| 5) What should stay rule-based? | Follow-up typing, add-car slot prompts, structured `collected_fields`, handoff phrase selection, scenario/guardrail packs. |
| 6) Human confirmation? | Payment / cancellation disputes, “carrier still chasing me” vs client claims, dense mixed-intent threads, any binding decision. |
| 7) Future LLM assist? | Discourse segmentation, sarcasm/negation, novel attachment descriptions — **not** for simple permission-to-send. |

## 3. What was changed

- **Added** `_message_claims_completed_material_send` and **expanded** `_is_prospective_send_offer_message`.
- **Replaced** naive `sent_markers` block in `_derive_follow_up_type` with the completion predicate.
- **Gated** short `unclear` “sent” replies (zh/en), broker summary “Client says already sent”, payment screenshot hints, cancellation `screenshot_sent`, fast-path short send, add-car broker “verify materials” branches.
- **Routing:** `_is_add_vehicle_request` bridges **VIN + prospective materials** and **行驶证/registration + prospective send**.
- **Slots / copy:** Nissan Altima in field + concrete resolution lists; **driver-only ask** when zip+delivery present but driver missing (zh/en).

## 4. 15 realistic retest scenarios

| ID | Intent |
|----|--------|
| WTR-S01 | VIN + 我可以先发你截图吗 |
| WTR-S02 | 我先发你 VIN 截图行吗 |
| WTR-S03 | 截图要不要先发你 |
| WTR-S04 | 行驶证截图我先发你看看行吗 |
| WTR-S05 | True 材料发你微信了 + quote context |
| WTR-F01 | ZIP 94102 会不会贵 |
| WTR-F02 | registration 未完成 + 订单截图可以吗 |
| WTR-F03 | 你好我想加个车 |
| WTR-F04 | VIN 要不要先给你看一下 → second turn add-car |
| WTR-L01 | Nissan Altima + VIN screenshot permission |
| WTR-L02 | 丰田塞纳 + 保险卡截图要不要先发你 |
| WTR-L03 | Model Y + 截图我先发你可以吗 |
| WTR-M01 | Correction + 驾照截图发微信了 |
| WTR-M02 | Quote-ready + 行驶证截图行吗 |
| WTR-M03 | 先按这台车看一下… Mazda CX-5 |

## 5. Retest results

All **15/15 PASS** (`scripts/run_wirc_trust_breaking_15_retest.py`, rules only).

| ID | Observed (last turn) | Classification | Judgment |
|----|----------------------|----------------|----------|
| WTR-S01 | `customer_question`, prospective lead + zip ask | A fixed | Trust-safe |
| WTR-S02 | Same pattern | A fixed | Trust-safe |
| WTR-S03 | `unclear`, generic completeness ask — **no** false sent | C residual | Acceptable; copy could be smarter |
| WTR-S04 | `customer_question`, permission + year/model ask | A + C | Good |
| WTR-S05 | Handoff + “材料发过了…” | A fixed | True positive preserved |
| WTR-F01 | `unclear` — no false sent | C | OK |
| WTR-F02 | Handoff + permission lead | A | Strong |
| WTR-F03 | `unclear` | C | OK |
| WTR-F04 | Handoff after full add-car turn | A | Strong |
| WTR-L01 | Handoff + permission | B + A | Strong |
| WTR-L02 | Handoff + permission | B | Strong |
| WTR-L03 | Handoff + permission | B | Strong |
| WTR-M01 | Materials-sent handoff | A | True positive |
| WTR-M02 | Handoff + 截图-style permission lead | A | Strong |
| WTR-M03 | Quote-ready handoff | A | Strong |

**Other batteries:** `guardrail_inbox_triage.sh` **13/13**; inbox scenarios **64/64**; WIRC battery **10** scenarios OK; add-car edge **18/18 Strong**; driver/ZIP/materials + scenario batteries completed without errors.

## 6. Overall pattern analysis

- **Clearly stronger:** Prospective vs completed distinction on **截图 / 发你 / VIN permission**; broker summary noise reduced; cancellation screenshot flag less gullible; add-car handoff copy aligns with **actual** send claims.
- **Still weak / borderline:** Ultra-short **screenshot-only** permission without vehicle anchor may stay **`unclear`** (not trust-breaking). ZIP-only premium worry still generic.
- **Class mix:** Core fix = **A (rules)**; Nissan/Model naming = **B**; short non-add-car opens = **C**; binding disputes = **D**; messy discourse = **E** (future).

## 7. Fix-now / Fix-next / Human-confirm / LLM-assist

See **`05_FIX_NOW_FIX_NEXT_HUMAN_CONFIRM_LLM_ASSIST.md`**.

## 8. Rule-based / fast-path summary (founder-readable)

- **Main file:** `services/fiqa_api/inbox_triage/triage.py`.
- **Intent / category:** Marker packs in `configs/industries/insurance/markers.json` + helper predicates (`_is_add_vehicle_request`, payment/claim helpers, …).
- **Follow-up / reply strategy:** `_derive_follow_up_type`, `_is_prospective_send_offer_message`, `_message_claims_completed_material_send`, `_build_client_reply_draft`, `_get_next_ask_for_add_car`, `_get_prospective_send_materials_lead`.
- **Extraction:** `_extract_add_car_fields`, `_extract_add_car_vehicle_concrete`, contact/cancellation/missing-doc helpers.
- **Handoff / broker copy:** `triage_conversation` tail — `handoff_phrases`, `add_car_materials_sent`, `broker_next_step` tailoring.
- **Regression:** `scripts/run_inbox_triage_scenarios.py`, `scripts/guardrail_inbox_triage.sh`, add-car battery scripts, this sprint’s `run_wirc_trust_breaking_15_retest.py`.

**Flow (simplified):** text → classify category → if add-car, extract slots → choose draft (progressive ask or handoff) → attach prospective-send lead when question → set `follow_up_type` / `collected_fields` / broker_next_step.

## 9. Final broker-confidence judgment

- **Safer for serious broker review:** **Yes** for the specific **trust-breaking** class; the system no longer systematically **mislabels permission as completed send**.
- **Biggest strength:** Deterministic guard + completion predicate is **testable** and **repeatable** across summary, cancellation, and add-car paths.
- **Biggest remaining weakness:** **First-turn** generic `unclear` copy for some screenshot questions without policy context — accurate but not glamorous.
- **Best next step:** Optional **one-line `unclear` template** for “screenshot permission only” (Fix-next **A/C**), and broker trial observation on **ZIP worry** turns.

## 10. 中文宏观总结

- **这类 trust-breaking 根因：** 规则把「截图 / 发你」等词**误当成已经发送**的完成态，而不是「可不可以先发」的问句；短句 `unclear` 路径还误用子串 **发你** 触发「您是说发过了吗」。
- **这次主要是设计还是规则还是词表？** 主要是**规则与意图守卫（排序 + 覆盖）**；词表（Nissan Altima 等）是**体验补强**。
- **15 个真实 case：** 在 **LLM 关闭** 条件下 **15/15 通过**；核心信任问题已压住。
- **Rule-based 已够用：** 明确的「先发可以吗」类问句、典型加车上下文、以及「发你微信了」类完成态分流。
- **更适合人工确认：** 付款/争议、公司与客户说法不一致、复杂混意图长文。
- **以后可上 LLM 辅助：** 分段理解、讽刺/否定、全新材料类型描述——但**不必**为了「先发截图行吗」上模型。
- **给 Chen Kui 看：** 在「截图/VIN/发你 + 问句」这条高风险线上，**可以更有信心**；若客户只发一句截图问句且无上下文，仍可能得到偏**保守/不完整**的回复——这是**产品话术层下一步**，不是再会出现的「假已发送」类错误。
