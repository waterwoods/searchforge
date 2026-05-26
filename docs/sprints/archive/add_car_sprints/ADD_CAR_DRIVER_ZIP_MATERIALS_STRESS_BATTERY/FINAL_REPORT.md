# Add-Car Driver / ZIP / Materials-QA Stress Battery Report

## 1. Sprint theme

- **Evaluated:** Rule-based Add-Car triage (`triage_conversation`, `LLM_GENERATION_ENABLED=false`) on **19** realistic Chinese (CA-style) messages stressing **ZIP formats**, **driver micro-phrases**, and **materials question vs already-sent** wording.
- **Why now:** Prior sprints hardened ZIP regex, driver markers, and prospective-send guards; this battery checks **phrasing variance** before serious broker viewing (Chen Kui unified entry).

## 2. Document set created

| Doc | Path |
|-----|------|
| Stress battery blueprint | `01_STRESS_BATTERY_BLUEPRINT.md` |
| Scenario design spec | `02_SCENARIO_DESIGN_SPEC.md` |
| Scenario battery spec | `03_SCENARIO_BATTERY_SPEC.md` |
| Evaluation criteria | `04_EVALUATION_CRITERIA.md` |
| Fix priority spec | `05_FIX_PRIORITY_SPEC.md` |
| Execution outline | `06_EXECUTION_OUTLINE.md` |
| Founder inspection notes | `FOUNDER_INSPECTION_NOTES.md` |
| Scenario JSON | `scenario_battery.json` |
| Runner | `scripts/run_add_car_driver_zip_materials_stress_battery.py` |
| This report | `FINAL_REPORT.md` |

**Code tweak during sprint:** `additional_drivers` detection in `triage.py` now includes `主要驾驶人是我老婆` / `主要驾驶人是我老公` so structured fields show `additional_drivers_yes` when the spouse is named that way (fixes misleading “self-driver only” collection on ADZM-D04).

## 3. Scenario battery overview

- **19 scenarios** — 6 ZIP, 5 driver, 4 materials, 4 mixed (incl. 4 multi-turn).
- **Categories covered:** All three pillars plus dense single-bubble and “minimal first message” patterns.
- **Usefulness:** Reusable JSON + runner; fast regression loop; failures separate **logic** vs **reply polish**.

## 4. Evaluation criteria

- **Strong:** Logic correct; broker + customer text usable with at most minor polish.
- **Acceptable:** Logic correct or intentionally incomplete with clear `still_needed_fields`; small broker string loss.
- **Weak:** Classification OK but **reply** ignores a clear customer question, or broker line drops important model context.
- **Trust-breaking:** Wrong extraction/classification that could mislead bind/rating, or customer reply contradicts facts.

## 5. Scenario-by-scenario results

Evaluated against **last customer turn** (and full thread for merges). Run: `LLM_GENERATION_ENABLED=false`, `triage_path=rule` for all turns.

| ID | Messages (abridged) | Focus | Observed (final turn) | Class | Judgment |
|----|---------------------|-------|------------------------|-------|----------|
| ADZM-Z01 | 想加…本田思域，邮编95131…我自己开 | zip | `zip`, `quote_ready`, handoff | **Strong** | ZIP + slots + handoff clean. |
| ADZM-Z02 | …邮编 95131…就我一个人开 | zip | Same pattern | **Strong** | Space after 邮编 OK. |
| ADZM-Z03 | …zip 95131…本人开 | zip | Same | **Strong** | Spaced `zip 95131` OK. |
| ADZM-Z06 | …zip95131…本人开 | zip | Same | **Strong** | Glued `zip`+digits OK. |
| ADZM-Z04 | …95131…我开 | zip | Same | **Strong** | Bare ZIP OK. |
| ADZM-Z05 | T1 想加宝马X3 → T2 我的邮编95131…主要驾驶人是我 | zip | Turn 2 `quote_ready` | **Strong** | Merged ZIP + delivery + driver. |
| ADZM-D01 | …90210…我自己开 | driver | `primary_driver` | **Strong** | |
| ADZM-D02 | …94102…我一个人开 | driver | `additional_drivers_no` | **Acceptable** | Broker line compresses model (“2024” only). |
| ADZM-D03 | …91355…本人开 | driver | Handoff | **Strong** | |
| ADZM-D04 | …主要驾驶人是我老婆 | driver | `primary_driver` + **`additional_drivers_yes`** (post-fix) | **Strong** | Spouse now visible to broker in structured fields. |
| ADZM-D05 | …我儿子开 | driver | `additional_drivers_yes` | **Acceptable** | Broker line “2020” drops 思域. |
| ADZM-M01 | …要不要发你行驶证截图 | materials | `follow_up_type=new_info` | **Weak** | Logic good; draft does not answer 要不要发. |
| ADZM-M02 | …要不要把截图发你 | materials | `new_info` | **Weak** | Same polish gap. |
| ADZM-M03 | …材料发你微信了 | materials | `already_sent`, verify WeChat broker line | **Strong** | |
| ADZM-M04 | …registration 发你微信了 | materials | `already_sent` | **Strong** | |
| ADZM-X01 | Tesla+邮编95131+我自己开… | mixed | `quote_ready`, `still_needed` has `delivery_date` | **Acceptable** | No delivery token; broker asks confirm delivery — coherent. |
| ADZM-X02 | Honda+90210+我老婆开+dec page要不要发你 | mixed | `new_info`, not false already_sent | **Strong** | Materials question + ZIP + spouse OK. |
| ADZM-X03 | T1 想加车 → T2 …截图发你了 | mixed | T2 `already_sent`, verify path | **Acceptable** | T1 draft echoes customer phrase awkwardly; T2 logic good; delivery still missing in text. |
| ADZM-X04 | T1 full slots → T2 要不要先发给你行驶证照片 | mixed | T2 `new_info` | **Weak** | Classification good; second reply generic, ignores offer question. |

## 6. Overall pattern analysis

- **ZIP robustness:** **Solid** on this battery — `邮编` / `邮编 ` / `zip 95131` / `zip95131` / bare `95131` / second-turn “我的邮编…” all populate `zip`.
- **Driver robustness:** **Solid** for listed micro-phrases; **主要驾驶人是我老婆** required the **additional_drivers** extension so broker-facing lists show non–self-driver context (implemented in this sprint).
- **Materials Q vs statement:** **Solid** for classification — `要不要…发` stays `new_info`; completed-send phrases hit `already_sent` with verify-WeChat broker guidance.
- **Clearly strong:** ZIP path, materials **intent** split, already-sent handoff copy, mixed X02.
- **Still weak:** **Customer-facing reply** when the bubble contains both quote-complete info **and** a prospective-send question (M01, M02, X04 turn 2) — playbook should add one acknowledging sentence.

## 7. Fix-now / Fix-next / Acceptable / Defer

| Bucket | Item |
|--------|------|
| **Fix-now** | Done for D04-shaped spouse phrasing (`主要驾驶人是我老婆/老公` → `additional_drivers_yes`). |
| **Fix-next** | Add-car draft: when `_is_prospective_send_offer_message` and quote-ready, append short permission line (WeChat/screenshot) before standard handoff. |
| **Acceptable** | Broker lines that shorten “2024 凯美瑞” → “2024”; X01 missing explicit delivery with explicit `still_needed_fields`. |
| **Defer** | Turn-1 echo of raw customer text (“好的，你好我想加车”); name/phone collection prompts. |

## 8. Final broker-confidence judgment

- **More confident for broker viewing?** **Yes** for **ZIP** and **materials classification**; **yes** for **driver** after spouse phrase structured fix.
- **Biggest strength:** Stable **9xxxx ZIP** extraction and **already_sent** vs **要不要发** distinction with sensible broker verify step.
- **Biggest remaining weakness:** **Reply polish** when customers combine **full quote slots** with **“要不要发你…”** — logic is right, UX sounds slightly deaf.
- **Single best next fix:** **Prospective-send-aware client_reply** on quote-ready Add-Car (one sentence, then existing handoff).

## 9. 中文宏观总结

这轮主要测了三类：**邮编写法**、**驾驶人说法**、**材料是问句还是已发**。整体结果：**邮编和材料意图分类很稳**；“要不要发你”不会被误判成“已经发过了”。**驾驶人**里“主要驾驶人是我老婆”这类说法，已在规则里补上配偶信号，避免经纪人只看字段时误以为全是本人开。仍偏弱的是：**客户在同一句话里既给齐报价信息又问要不要发截图时，系统回复还是统一用“资料好了交办公室”**，听起来像没听见最后一句——属于**回复润色**，不是分类逻辑崩盘。下一步最值得做的是：**在加车且识别到“要不要发…”时，加一句简短答复再交接**。

## 10. COPY/PASTE FOUNDER BLOCK

```
Add-Car stress battery (ADZM): 19 scenarios, rule path, LLM off.
Classifications: Strong 12 | Acceptable 4 | Weak 3 | Trust-breaking 0 (after spouse-phrase structured-field fix).
ZIP: feels solid (邮编 / zip+space / zip 粘连 / 裸95131 / 第二泡邮编).
Driver phrases: feel solid for listed variants; 主要驾驶人是我老婆 now flags additional_drivers_yes.
Materials Q vs sent: distinction feels solid; verify-WeChat broker path fires on 发你微信了.
Biggest remaining weakness: customer reply ignores “要不要发你…” when quote info is already complete (polish, not logic).
Andy can show Add-Car to Chen Kui with higher confidence on ZIP + materials routing; call out that doc-offer questions may need a one-line human-feeling answer in a live demo.
```
