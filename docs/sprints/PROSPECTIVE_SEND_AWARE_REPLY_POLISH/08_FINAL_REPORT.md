# Prospective-Send-Aware Reply Polish — Final Report

## 1. Sprint theme

- **Fixed:** Add-Car customer replies now open with a brief, office-style answer when the customer **asks or suggests** sending materials (WeChat / screenshot / generic docs), then continue normal slot collection or handoff.
- **Why now:** Classification was already safe; the weak point was **voice**—replies felt generic or parroted the question.

## 2. Baseline audit

- **Biggest weakness:** No first-sentence acknowledgment of the send-permission question; optional echo of the raw question in `_get_add_car_acknowledgement`.
- **Root cause:** Prospective-send was only used in `_derive_follow_up_type`; reply builders did not branch on it.
- **Functions / areas:** `_is_prospective_send_offer_message`, `_derive_follow_up_type`, `_get_add_car_acknowledgement`, `_get_next_ask_for_add_car`, `_build_client_reply_draft` (add-car), `triage_conversation` (handoff assembly).

## 3. What changed

- **File:** `services/fiqa_api/inbox_triage/triage.py`
- **Additions:** `_get_prospective_send_materials_lead()`; extended `_is_prospective_send_offer_message()` for 我先发给你看看行吗 / 行不行 patterns.
- **Wiring:** Prepend lead in add-car collecting path, turn-1 rule draft path, and quote-ready handoff path; exclude prospective from short-message echo; guard `materials_sent` substring with `not _is_prospective_send_offer_message`.
- **Scenarios:** `docs/sprints/ADD_CAR_DRIVER_ZIP_MATERIALS_STRESS_BATTERY/scenario_battery.json` (+ADZM-M05, M06, X05; 22 total).

## 4. Validation summary

- `bash scripts/guardrail_inbox_triage.sh` — **PASS**
- `PYTHONPATH=. python3 scripts/run_add_car_scenario_battery.py` — **PASS** (17 scenarios)
- `PYTHONPATH=. python3 scripts/run_add_car_driver_zip_materials_stress_battery.py` — **PASS** (22 scenarios)
- `PYTHONPATH=. python3 scripts/run_add_car_edge_case_simulations.py` — **PASS** (18 simulations)
- **Weak cases:** ADZM-M01/M02/X02/X04 and ACB-M04 turn-2 now lead with an explicit 可以… line before handoff/collection.
- **Regressions:** None observed in the above suite; `already_sent` paths (e.g. ADZM-M03/M04, ACB-E03) unchanged in intent.

## 5. Before vs After

- **Before (example):** Quote-ready + 要不要发你行驶证截图 → generic “您说的报价资料已整理好了…” only (question ignored).
- **After:** “可以，截图先发我，我这边一起看。您说的报价资料已整理好了，办公室会尽快出价，有结果会联系您。”

## 6. Biggest improvement

- **Customer:** Feels heard when asking permission to send materials.
- **Broker:** Safer distinction between “asking to send” vs “said they sent”; fewer false “verify materials” mental mismatches when reading the thread.

## 7. Biggest remaining weakness

- Next-slot wording can still repeat a field (e.g. year/model) when the thread already partially filled it—pre-existing collection copy, not introduced by this sprint.

## 8. Deployment judgment

- **Backend redeploy:** **Yes** — `triage.py` changed; production API must pick up the new module.
- **Frontend redeploy:** **No** — UI unchanged.

## 9. Founder test cases (copy-paste)

1. `加车 2024 Toyota Camry，92801，下周提车，我开，要不我发你微信你看下行不行`
2. `2024特斯拉Model 3，95131，明天提车，我自己开，要不要发你行驶证截图`
3. `你好我想加车` → then second message: `我先发给你看看行吗`

## 10. 中文宏观总结

- **改动位置：** 主要在 `triage.py` 里生成加车客户回复的几条路径（首轮规则草稿、第二轮追问、以及可交办公室时的 handoff 文案），新增一个很短的“可以发我”类开场白。
- **以前为什么泛：** 系统只按槽位推进，没有在话术上单独回应“要不要发你”这种礼貌/确认问句；有时还会把短句原样 echo 成“好的，要不要发你。”
- **现在什么样：** 先用一句话说清楚“可以发、怎么发”（微信/截图/材料），再接原来的邮编/提车/交办公室逻辑；真正“已发材料”的句子仍走原来的核对与 handoff。
- **这类问句是否更好：** 是，明显更像真人办公室会先答应一句再继续办事。
