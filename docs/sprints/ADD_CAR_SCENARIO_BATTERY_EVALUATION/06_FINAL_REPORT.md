# Add-Car Scenario Battery Evaluation Report

**Sprint:** ADD_CAR_SCENARIO_BATTERY_EVALUATION  
**Engine:** `triage_conversation` → `services/fiqa_api/inbox_triage/triage.py`  
**Run artifact:** `run_results_rule_path.json` (rule path, `LLM_GENERATION_ENABLED=false`)

---

## 1. Sprint theme

- **Evaluated:** Add-Car (加车 / new vehicle quote) behavior across **17 realistic, mostly messy** multi-turn customer threads aimed at **Chinese-speaking California** auto insurance customers.
- **Why now:** Add-Car is the **flagship** Unified Entry scenario; broker confidence depends on **non-happy-path** robustness before serious broker review (Chen Kui).

---

## 2. Document set created

| # | Document |
|---|----------|
| 1 | `00_BLUEPRINT.md` — Add-Car Scenario Battery Blueprint |
| 2 | `01_SCENARIO_DESIGN_SPEC.md` — Scenario Design Spec |
| 3 | `scenario_battery.json` — Scenario Battery (17 scenarios) |
| 4 | `02_EVALUATION_CRITERIA_SPEC.md` — Evaluation Criteria Spec |
| 5 | `03_FIX_PRIORITY_SPEC.md` — Fix-Now / Fix-Next / Acceptable / Defer Spec |
| 6 | `04_EXECUTION_OUTLINE.md` — Execution Outline |
| 7 | `05_FOUNDER_INSPECTION_NOTES.md` — Founder Inspection Notes |
| 8 | `06_FINAL_REPORT.md` — This Final Report |
| + | `run_results_rule_path.json` — Frozen machine output for this run |
| + | `scripts/run_add_car_scenario_battery.py` — Dedicated runner |

---

## 3. Scenario battery overview

- **Count:** 17 scenarios (`ACB-C01..C03`, `ACB-M01..M07`, `ACB-E01..E07`).
- **Types:** 3 clean, 7 moderately messy, 7 edge/risky (correction, materials sent, price anxiety, garaging side-question, two-car, topic jump, hesitation, dense bubble, late ZIP/driver/contact).
- **Why useful:** Exercises **slot extraction**, **handoff timing**, **correction-aware** replies, **materials-sent** branch, and **category stability** under realistic filler—without relying on a single “golden” demo thread.

---

## 4. Evaluation criteria

- **Strong:** Correct Add-Car playbook, right next asks, natural draft, actionable broker step; low embarrassment risk.
- **Acceptable:** Correct outcome with **forgivable friction** (wording echo, minor redundancy, first-turn narrowing).
- **Weak:** Stuck asks, clear extraction miss, or **bad first impression** on an easy message—even if later turns recover.
- **Trust-breaking:** Wrong category, **false “already sent”**, or client reply that sounds **broken / generic** in a way that undermines office trust.

---

## 5. Scenario-by-scenario results

> **Observed behavior** is summarized from `run_results_rule_path.json` (rule path).

### ACB-C01 — 标准两回合：先问价再给全量信息

- **Message sequence:** (1) 2024 凯美瑞 + 问价 → (2) zip 90210 + 提车 + 老公开  
- **Observed:** Turn 1 collects year/model, asks **ZIP** and sets price-expectation line; turn 2 **handoff**, `quote_ready`, broker step references **2024 丰田**.  
- **Judgment:** Playbook correct; draft professional.  
- **Classification:** **Strong**

### ACB-C02 — 英文单泡：信息一次给齐

- **Message sequence:** (1) Full English add-car with CR-V, partial VIN phrase, zip, Friday pickup, only I drive  
- **Observed:** Immediate **handoff**; EN handoff draft; broker asks to confirm main driver / contact despite “only I drive” (structured `still_needed_fields` still lists `primary_driver`).  
- **Judgment:** Add-Car path correct; small **structured-label noise** vs plain English.  
- **Classification:** **Acceptable**

### ACB-C03 — 中英混排车型名

- **Message sequence:** (1) Model Y + 报价 → (2) **邮编95131** + 明天拿车 + 一个人开  
- **Observed:** Turn 2 **still asks for 邮编**; `quote_ready_status` stays **need_more**; no handoff.  
- **Judgment:** **ZIP extraction failed** for `邮编95131` (regex word-boundary issue before digits).  
- **Classification:** **Weak**

### ACB-M01 — 极简开场，信息散落在第二泡

- **Message sequence:** (1) 你好我想加车 → (2) 2020 civic + 94566 + 周五提车 + 老婆开  
- **Observed:** Turn 1 asks year/model; turn 2 handoff. Turn 1 draft **echoes** full customer phrase.  
- **Judgment:** Functionally fine; opener unnatural.  
- **Classification:** **Acceptable**

### ACB-M02 — 邮编最后一回合才给

- **Message sequence:** (1) 2023 宝马X3 + 提车 + 我开 + 加保报价 → (2) zip 92620  
- **Observed:** Turn 1 asks ZIP; turn 2 handoff with concrete BMW X3.  
- **Classification:** **Strong**

### ACB-M03 — 驾驶人最后一回合才说

- **Message sequence:** (1) Lexus RX + zip + 明天拿车 → (2) 主要驾驶人是我老公  
- **Observed:** Turn 1 handoff with **delivery** only (allowed by rules); turn 2 refines driver; still handoff.  
- **Judgment:** Matches stricter “delivery OR driver” policy; broker steps consistent.  
- **Classification:** **Strong**

### ACB-M04 — 姓名电话晚到第三泡

- **Message sequence:** (1) full vehicle + zip + 下周末提车 + **我自己开** → (2) **对了材料要不要发你** → (3) 我是陈晨 + 电话  
- **Observed:** Turn 2 `follow_up_type` **already_sent**, draft “材料发过了”; turn 3 `issue_category` → **`missing_document`**; `still_needed_fields` ends with **primary_driver** even though turn 1 said 我自己开.  
- **Judgment:** **False materials-sent** + **category drift**; driver phrase **我自己开** missed by driver markers (not substring `我开`).  
- **Classification:** **Trust-breaking**

### ACB-M05 — 一泡超长口语堆叠

- **Message sequence:** (1) Single long bubble with Mazda CX-5, zip, dealer pickup, spouse + self drive, 加车问价  
- **Observed:** Single-turn **handoff**, `quote_ready`.  
- **Classification:** **Strong**

### ACB-M06 — 先模糊问价再补全

- **Message sequence:** (1) 能先报价吗想加车 → (2) Subaru + zip + pick up next week + 就我开  
- **Observed:** Turn 1 echo-heavy but on-playbook; turn 2 handoff.  
- **Classification:** **Acceptable**

### ACB-M07 — 犹豫+改口+啰嗦

- **Message sequence:** (1) 不确定先问问可能买新车 → (2) F-150 + zip + 下个月提车 + 一个人开  
- **Observed:** Turn 1 asks year/model; turn 2 handoff; flags `insurance_status_new_customer` (debatably OK).  
- **Classification:** **Acceptable**

### ACB-E01 — 车型纠正：本田→特斯拉

- **Message sequence:** (1) Accord complete → (2) 不对，Model 3  
- **Observed:** Correction turn; draft leads with **2023 Tesla Model 3**; broker step updated.  
- **Classification:** **Strong**

### ACB-E02 — 车型纠正：X5→X3

- **Message sequence:** (1) X5 complete → (2) 不是X5，是X3  
- **Observed:** Same correction-aware behavior as E01.  
- **Classification:** **Strong**

### ACB-E03 — 材料已发微信

- **Message sequence:** (1) Camry complete → (2) 报价资料截图发你微信了  
- **Observed:** `follow_up_type` **already_sent**; broker **verify WeChat + quote**; warmer client line.  
- **Classification:** **Strong**

### ACB-E04 — 加价焦虑+加车同事务

- **Message sequence:** (1) Civic + zip + 下周拿车 + 老婆开 + **能便宜吗大概多少钱**  
- **Observed:** Stays **`customer_question`**, immediate handoff (slots complete).  
- **Judgment:** Correctly avoids pure **premium_review** derailment.  
- **Classification:** **Strong**

### ACB-E05 — 边问 garaging proof 边给车信息

- **Message sequence:** (1) Single bubble: garaging question + full Pilot + zip + 明天提车 + 我开  
- **Observed:** Handoff with **garaging explanation** + long tail that **re-asks** fields largely already present.  
- **Judgment:** Trust OK; **verbosity / redundancy**.  
- **Classification:** **Acceptable**

### ACB-E06 — 两辆车混淆

- **Message sequence:** (1) Tesla + Camry 一起报价 → (2) 只要新 Model Y 细节  
- **Observed:** Turn 1 narrows to Tesla only; turn 2 handoff on **2024 Model Y**.  
- **Judgment:** Acceptable recovery; turn 1 could acknowledge **two vehicles** more explicitly.  
- **Classification:** **Acceptable**

### ACB-E07 — 话题跳跃后再回到加车

- **Message sequence:** (1) office 几点关门 → (2) 我要加车 → (3) Mazda CX-9 full details  
- **Observed:** Turn 1 **`unclear`** + **“这段内容还不够完整”**; turns 2–3 recover to Add-Car handoff.  
- **Judgment:** Turn 1 is **broker-embarrassing** for a simple ops question.  
- **Classification:** **Weak**

---

## 6. Overall pattern analysis

- **Already strong:** **End-state handoff** when digits + model + zip + (delivery or driver) line up; **correction-aware** vehicle updates (E01/E02); **materials-sent** path when customer truly says sent (E03); **price anxiety + add-car** without premium-review hijack (E04); **dense single-bubble** parsing (M05).
- **Still fragile:** **ZIP formats** (`邮编` glued to digits); **pragmatic questions** misclassified as document/materials already_sent (M04); **operational small talk** before Add-Car (E07 turn 1); **acknowledgement echo** of entire customer message (M01/M06/M07).
- **Repeating pattern:** Extraction and follow-up typing are **more brittle than** the handoff templates—fixes should target **slot/follow_up detection**, not rewriting all copy.

---

## 7. Fix-now / Fix-next / Acceptable / Defer

| Bucket | Items |
|--------|--------|
| **Fix-now** | ZIP detection for `邮编` + common CN formats; **don’t treat “要不要发你” as already_sent**; treat **我自己开 / 我一个人开** as driver present. |
| **Fix-next** | Trim **echo** in add-car acknowledgements; shorten **E05-style** redundant checklist tail; **two-car** first reply could ask “先报哪一台”. |
| **Acceptable** | C02 structured driver flag noise; E06 turn-1 narrowing (recovery OK). |
| **Defer** | LLM-only paraphrase polish; perfect shortest drafts everywhere. |

---

## 8. Final broker-confidence judgment

- **Serious broker review ready?** **Mostly yes for the “happy-adjacent” Add-Car core** (handoff + correction + true materials-sent + price-anxiety mix), but **not** without acknowledging **M04-class** false positives and **C03-class** ZIP misses—those are the kinds of bugs brokers **feel** immediately.
- **Biggest strength:** Once slots are parsed, **handoff copy and broker_next_step** are **coherent and office-realistic**; correction handling is **credibility-building**.
- **Biggest remaining weakness:** **Follow-up / slot edge cases** (邮编, 要不要发你, 我自己开) and **generic unclear** replies to **simple operational** questions when the thread is young.
- **Single best next fix:** **Harden ZIP + driver micro-phrases + materials-sent guard** (narrow triggers for `already_sent`)—small surface area, high trust ROI.

---

## 9. 中文宏观总结

这轮测的是：**加车报价**在“真客户那样说话”时的表现（多轮、补字段、改口、加价担心、材料、边问边报）。用的是当前 `triage.py` 的 **规则路径**（关掉 LLM），结果可复现。

整体来看：**主流程很能打**——信息齐了以后，办公室侧指引清楚，**改车型**也能跟上；**材料已发**在真实“发微信了”场景也合理。

已经比较稳的情况：**信息完整或第二轮补齐**、**长消息一泡里塞很多字段**、**价格敏感话术不跑题**、**明确说材料已发**。

还容易出问题的：**`邮编` 紧跟数字时邮编抽不出来**、把“**要不要发你**”误判成“**已经发了**”、以及“**我自己开**”这种**常见口语**没被当成驾驶人信息；另外**无关第一句**（比如问营业时间）容易被**模板化“内容不完整”**，对经纪人观感不好。

下一步最值得修：**邮编/驾驶人短语/材料已发触发条件**这三类小修，能明显减少“丢脸型”误判。

---

## 10. COPY/PASTE FOUNDER BLOCK

```
Add-Car Scenario Battery (rule path) — Chen Kui Unified Entry
Scenarios tested: 17
Strong: 8 | Acceptable: 6 | Weak: 2 | Trust-breaking: 1

Biggest strength: Handoff + broker_next_step are coherent once slots parse; vehicle correction & true materials-sent paths build broker trust.

Biggest weakness: Slot/follow-up edge cases (邮编+ZIP, “要不要发你” vs sent, “我自己开” driver) + generic “内容不完整” on simple first messages.

Can Andy show Add-Car to Chen Kui more confidently?
Yes for the core demo (complete/correction/materials/price-mix threads), provided you verbally caveat “we’re hardening edge phrases next” — do NOT pretend M04/C03-class issues are already solved.
```

---

## Roll-up counts (for dashboards)

| Classification | IDs |
|----------------|-----|
| Strong (8) | C01, M02, M03, M05, E01, E02, E03, E04 |
| Acceptable (6) | C02, M01, M06, M07, E05, E06 |
| Weak (2) | C03, E07 |
| Trust-breaking (1) | M04 |
