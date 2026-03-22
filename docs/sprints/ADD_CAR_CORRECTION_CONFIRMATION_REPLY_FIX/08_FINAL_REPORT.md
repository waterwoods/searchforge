# Add-Car Correction Confirmation Reply Fix — Final Report

## 1. Sprint theme

- **Fixed:** Add-car **customer-facing** replies after **vehicle correction** so they **explicitly confirm the effective vehicle** (office-style Chinese), fix **merged-vs-last-bubble** bugs that dropped or thinned acknowledgements, extend **correction phrasing** (不对 / 搞错了 / comma 不是…是), and align **next-step Chinese copy** (“继续帮您报价”) without changing handoff/slot rules.
- **Why now:** Trust and broker confidence depend on the client **feeling understood**; internal slot correctness alone is not enough.

## 2. Baseline audit

- **Biggest weakness:** Client draft could be **thin or empty** when `last_customer_msg` was actually **full merged text** (length gate), or when **comma/colloquial** corrections skipped the correction branch.
- **Root cause:** `_build_client_reply_draft` treated merged `text` inconsistently (`f"[客户] {text}"` duplication / wrong bubble); `_get_add_car_acknowledgement` applied **`len(msg) > 120`** to that merged string; narrow **不是[^，]…是** regex; year-only branch before rich **concrete**.
- **Functions / areas:** `_build_client_reply_draft`, `_get_add_car_acknowledgement`, `_is_add_car_vehicle_correction_signal`, `_get_next_ask_for_add_car`, `_extract_add_car_vehicle_concrete` (unchanged logic, but now fed reliable context).

## 3. What changed

| File | What |
|------|------|
| `services/fiqa_api/inbox_triage/triage.py` | `_merged_and_last_customer_for_add_car_draft`; add-car draft uses merged slots; `_get_add_car_acknowledgement` last-bubble defense; richer non-correction `concrete` ack; expanded correction detection; zh spacing in `_get_next_ask_for_add_car`; updated zh fallbacks. |
| `configs/industries/insurance/add_car_rules.json` | ask_zip / ask_vehicle zh wording → **继续帮您报价**. |
| `configs/customer_entry_multi_turn_simulations.json` | **ACE17**, **ACE18**. |

## 4. Validation summary

| Command | Result |
|---------|--------|
| `bash scripts/guardrail_inbox_triage.sh` | **PASS** |
| `PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py` | **69 strong, 0 weak** |
| `PYTHONPATH=. python3 scripts/run_add_car_edge_case_simulations.py` | **18 strong, 0 weak** |

No regressions observed in guardrail packs.

## 5. Before vs After

| Before (example failure mode) | After (target) |
|-------------------------------|----------------|
| *(empty ack on long merged text)* or **好的，2024的。** + zip ask | **好的，我按 2024 Tesla 这台车继续。**先把邮编发我，我就能继续帮您报价。 |
| `不是X5，是X3` missed as correction | Same lead pattern with **2024 BMW X3** when year in thread |
| `不对，是 2024 Tesla` → generic **好的，2024 Tesla。** | **好的，我按 2024 Tesla 这台车继续。** … |

## 6. Biggest improvement

- **Customer:** Feels the assistant **locked onto the right car** after a correction.
- **Broker:** Less “botty” thread; fewer anxious clarifications back from the client.

## 7. Biggest remaining weakness

- If the customer **only** corrects with **year** or vague wording (**是2024款的**) with **no make in the bubble**, the system may still only confirm **年份** — that needs either **follow-up ask** or **human** clarification; not solved as a hard NLP problem here.

## 8. Deployment judgment

- **Backend redeploy:** **Yes** — `triage.py` and server-read rules JSON changed.
- **Frontend redeploy:** **No** — sprint scoped to backend/copy.

## 9. Founder test cases (copy-paste)

**A. Honda → Tesla**

1. `我想加车 2021 Honda`  
2. `不是这个，是 2024 Tesla`  

**B. 口语纠正**

1. `我想加车 2021 Honda`  
2. `不对，是 2024 Tesla`  

**C. Comma X5 → X3**

1. `加车 2024 BMW X5`  
2. `不是X5，是X3`  

## 10. 中文宏观总结

- **在什么地方修的：** 主要在 `services/fiqa_api/inbox_triage/triage.py` 里生成加车客户回复、纠错识别和下一句追问的逻辑；另外在 `configs/industries/insurance/add_car_rules.json` 调整了中文追问话术。
- **为什么以前会回复得不够好：** 有时把**整段合并对话**当成“最后一句”处理，触发长度限制导致**干脆不确认**；或者 **不是X5，是X3**、**不对/搞错了** 这类说法没走进“纠错确认车”的分支，只能退化成**偏薄**的应答。
- **现在改成什么样了：** 会优先抓住**最后一句话**做纠错判断；确认时用 **「好的，我按 {有效车辆} 这台车继续。」**，并接上**更自然的下一步收集**（邮编等），中文追问统一带**继续帮您报价**的语气。
- **这一类情况是不是基本解决了：** **常见改车说法**（不是这个/不是…是/不对/搞错了/英文 not that one 等）+ 能解析出车型时，**明显改善**；只有**年份或信息不完整**的纠正，仍可能需要再多问一句，这是**剩余边界**。

---

## 三问（中文，简答）

1. **这个修复主要是在什么文件、什么函数附近做的？**  
   主要在 **`services/fiqa_api/inbox_triage/triage.py`** 的 **`_build_client_reply_draft`**、**`_get_add_car_acknowledgement`**、**`_is_add_car_vehicle_correction_signal`**、**`_get_next_ask_for_add_car`**；配置在 **`configs/industries/insurance/add_car_rules.json`**。

2. **修完以后，这一类“改车”情况是不是明显更好了？**  
   **是**，只要客户在纠正句里能说出**可识别的车**（品牌/车型/英文车名等），客户侧回复会**明确确认**并按新车继续收集信息。

3. **还需不需要 backend redeploy？**  
   **需要。** 改了 API 侧 triage 逻辑与规则文案，**必须重新部署后端**后 Vercel/线上才会一致。
