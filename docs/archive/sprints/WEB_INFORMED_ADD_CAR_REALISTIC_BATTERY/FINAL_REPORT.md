# Web-Informed Add-Car Realistic Chinese Customer Battery Report

## 1. Sprint theme

- **Evaluated:** The **rule-based** Add-Car / quote-collection path inside **Unified Intake** (`triage_conversation`, `LLM_GENERATION_ENABLED=false`) against **10 web-informed, Chinese-forward California customer scenarios** (multi-turn, price-first, materials questions, late ZIP/driver, corrections, mixed language).
- **Why now:** Chen Kui–style unified entry needs **broker-credible** realism beyond synthetic slot tests—without claiming ethnographic research. This sprint tightens **wording realism**, surfaces **trust risks**, and separates **rule fixes** from **human confirmation** vs **narrow LLM assist**.

## 2. Document set created

| Path | Description |
|------|-------------|
| `docs/sprints/WEB_INFORMED_ADD_CAR_REALISTIC_BATTERY/BLUEPRINT.md` | Sprint blueprint |
| `docs/sprints/WEB_INFORMED_ADD_CAR_REALISTIC_BATTERY/SOURCE_GROUNDED_SCENARIO_DESIGN_SPEC.md` | Source patterns + category map |
| `docs/sprints/WEB_INFORMED_ADD_CAR_REALISTIC_BATTERY/scenario_battery.json` | 10 scenarios (IDs, turns, rationale) |
| `docs/sprints/WEB_INFORMED_ADD_CAR_REALISTIC_BATTERY/battery_run_results.json` | Last rule-path JSON run |
| `docs/sprints/WEB_INFORMED_ADD_CAR_REALISTIC_BATTERY/EVALUATION_CRITERIA.md` | Scoring dimensions |
| `docs/sprints/WEB_INFORMED_ADD_CAR_REALISTIC_BATTERY/COVERAGE_GAP_WEAK_SPOT_SPEC.md` | Weak spots tied to symptoms |
| `docs/sprints/WEB_INFORMED_ADD_CAR_REALISTIC_BATTERY/RULE_BASED_VS_HUMAN_LLM_ESCALATION_SPEC.md` | Fix-now / human / LLM table |
| `docs/sprints/WEB_INFORMED_ADD_CAR_REALISTIC_BATTERY/EXECUTION_OUTLINE.md` | How to re-run |
| `docs/sprints/WEB_INFORMED_ADD_CAR_REALISTIC_BATTERY/FOUNDER_INSPECTION_NOTES.md` | Fast read for demos |
| `docs/sprints/WEB_INFORMED_ADD_CAR_REALISTIC_BATTERY/FINAL_REPORT.md` | This report |
| `scripts/run_web_informed_add_car_realistic_battery.py` | Runner |

## 3. Source-grounded scenario design

- **Patterns used:** (A) Office-style **add-car / quote** data (YMM, ZIP/garaging, delivery, drivers, VIN/materials); (B) **CA price sensitivity** phrasing (ZIP, “大概多少钱”); (C) **Chat realism**—fragments, price-first, screenshot offers, late facts, corrections, mixed 中英车名.
- **How they informed design:** Each **WIRC-*** maps to one primary realism axis (see `SOURCE_GROUNDED_SCENARIO_DESIGN_SPEC.md`).
- **Caveat:** These are **web-informed realistic scenarios**, not statistically definitive customer research.

## 4. Scenario battery overview

| ID | Focus |
|----|--------|
| WIRC-001 | Clean single-message add-car |
| WIRC-002 | Price-first + language anxiety; facts in turn 2 |
| WIRC-003 | Partial then ZIP/delivery/driver |
| WIRC-004 | No hard registration + “can I send VIN screenshot?” |
| WIRC-005 | ZIP in second bubble |
| WIRC-006 | Driver in second bubble |
| WIRC-007 | Vehicle correction |
| WIRC-008 | Uncertain delivery window |
| WIRC-009 | Mixed Chinese/English vehicle naming |
| WIRC-010 | ZIP “expensive?” + WeChat screenshots; then Model Y |

**Why useful:** Covers the **office-shaped** happy path and the **messy** openings brokers actually see on WeChat, in one short battery.

## 5. Scenario-by-scenario results

*Run:* `battery_run_results.json`, `triage_path: rule`, `LLM_GENERATION_ENABLED=false`.

### WIRC-001 — 一次性说清楚

- **Messages:** 1× (2024 本田雅阁, 95131, 下周三提车, 自己开, 报价).
- **Pattern:** Clean direct request.
- **Observed:** `customer_question`, `quote_ready`, `handoff_ready: true`; slots: year, make_model, zip, delivery, driver; name/phone still needed. Client draft: office will quote. Broker line: **“2024 本田”** (Accord not spelled out).
- **Classification:** **Acceptable**
- **Judgment:** Playbook and extraction solid; broker summary **truncates model**.
- **Escalation:** **rule-based good enough**; **better with human confirmation** on name/phone (expected).

### WIRC-002 — 先问大概多少钱 + 英文不好

- **Messages:** (1) 大概多少钱 / 英文不好 / 告诉我还差什么; (2) 2024 斯巴鲁 Outback, 95928, 下周四, 一个人开.
- **Pattern:** Price-first + second-turn completion.
- **Observed:** Turn 1 collects nothing except add-to-existing signal; good ZH reply setting price boundary + asks YMM. Turn 2 `quote_ready`, handoff; broker line **“Run quote for 2024”** (drops Outback label).
- **Classification:** **Acceptable**
- **Judgment:** Stays in flow; excellent turn 1; broker-facing string **thin on model**.
- **Escalation:** **rule-based good enough** (copy/summary polish optional).

### WIRC-003 — 先车型后补邮编提车驾驶人

- **Messages:** (1) 2024 Toyota Camry; (2) 90210, 这周五提车, 自己开.
- **Pattern:** Partial then fragment.
- **Observed:** Turn 1 asks ZIP; turn 2 merges to `quote_ready`, handoff; full Camry in broker line on turn 2 path.
- **Classification:** **Strong**
- **Judgment:** Canonical multi-turn merge behavior.
- **Escalation:** **rule-based good enough**.

### WIRC-004 — registration + 先发 VIN 截图行吗

- **Messages:** 1× (刚买车无正式 registration, 问截图, 2023 Lexus RX, 92618, 下周三, 自己开).
- **Pattern:** Materials / VIN question layered on add-car.
- **Observed:** `follow_up_type: already_sent`; `customer_says_sent_materials` set; **`vin`** marked collected though no VIN string supplied; client draft: **“您说材料发过了…”** (false: customer only asked if they *may* send). `insurance_status_new_customer` vs “加进保单” narrative.
- **Classification:** **Trust-breaking**
- **Judgment:** Customer-facing reply **misstates the conversation**; flags overfire on send intent.
- **Escalation:** **Rule coverage gap** (intent); **human confirmation** on materials; **candidate for future LLM assist** for *ask vs assert* if rules stay brittle.

### WIRC-005 — ZIP 第二泡

- **Messages:** (1) Civic + 明天提车 + 老公开; (2) 94103.
- **Pattern:** Late ZIP.
- **Observed:** Turn 1 correctly needs ZIP; turn 2 `quote_ready`, handoff; spouse driver flagged (`additional_drivers_yes`).
- **Classification:** **Strong**
- **Judgment:** Exactly what brokers need for split messages.
- **Escalation:** **rule-based good enough**.

### WIRC-006 — 驾驶人第二泡

- **Messages:** (1) Model Y + zip95131 + 下周六提车; (2) 主要驾驶人是我.
- **Pattern:** Late driver.
- **Observed:** Turn 1: `handoff_ready: true`, `quote_ready_status: quote_ready`, but **`primary_driver` still in `still_needed_fields`**; broker step says confirm driver. Turn 2 fixes driver; consistent handoff.
- **Classification:** **Weak**
- **Judgment:** **Premature “ready”** vs explicit still-needed driver undermines desk UX.
- **Escalation:** **Rule coverage gap** (gating); **human confirmation** until aligned.

### WIRC-007 — 说错了换车

- **Messages:** (1) 2024 RAV4…; (2) 其实是 2025 凯美瑞混动 Camry hybrid.
- **Pattern:** Correction.
- **Observed:** Turn 2 `follow_up_type: correction`; client draft acknowledges 2025; handoff maintained. Broker lines use **“2024 丰田”** / **“2025”** without full trim.
- **Classification:** **Acceptable**
- **Judgment:** Correction path works; summaries **under-specify** vehicle.
- **Escalation:** **better with human confirmation** on corrected trim.

### WIRC-008 — 提车时间不确定

- **Messages:** 1× (2021 Nissan Altima, 94608, 不确定下周/下下周, 一个人开, 走加车流程).
- **Pattern:** Uncertain delivery.
- **Observed:** `need_more`, no handoff; draft **asks again for ZIP and model** though **both appear in the same message**. `collected_fields` includes `year` but `still_needed_fields` lists **`year` again** plus `make_model`—internally inconsistent. Root symptom: **`make_model` not detected** (e.g. **Altima** gap).
- **Classification:** **Weak**
- **Judgment:** Fails “read the obvious English model” and **repeats asks** incorrectly.
- **Escalation:** **Rule coverage gap** (lexicon); **human confirmation** as backstop.

### WIRC-009 — 中英混排车名

- **Messages:** 1× (2024 Toyota 凯美瑞 Camry LE, zip 95131, next week pick up, 自己开).
- **Pattern:** Mixed zh/en naming.
- **Observed:** `quote_ready`, handoff; summary shows **Toyota Camry**; slots coherent.
- **Classification:** **Strong**
- **Judgment:** Good bilingual tolerance.
- **Escalation:** **rule-based good enough**.

### WIRC-010 — 邮编贵不贵 + WeChat 再 Model Y

- **Messages:** (1) 91367 会不会贵、WeChat 截图; (2) 2024 Model Y, 明天提车, 老婆开.
- **Pattern:** Side concern before vehicle.
- **Observed:** Turn 1: **`unclear`**, notice-style **“内容不够完整”** reply—**wrong template** for shopping small talk. Turn 2: merges ZIP from turn 1, resolves **Tesla Model Y**, `quote_ready`, handoff; `additional_drivers_yes`.
- **Classification:** **Weak** (session-level: first impression wrong; second turn saves).
- **Judgment:** Real customers **do** open like turn 1; current rules **mishandle** that opening.
- **Escalation:** **Rule coverage gap** (routing/template); optional **LLM routing** only if rule explosion continues.

### Summary counts

| Bucket | Count | IDs |
|--------|------|-----|
| Strong | 3 | WIRC-003, 005, 009 |
| Acceptable | 3 | WIRC-001, 002, 007 |
| Weak | 3 | WIRC-006, 008, 010 |
| Trust-breaking | 1 | WIRC-004 |

## 6. Overall pattern analysis

- **Clearly strong:** **Multi-turn slot merge** when the customer states a clear **English model** the lexicon knows (Camry, Civic, Model Y); **late ZIP** flow; **mixed 中英车名** when “Camry” anchors the model.
- **Still weak:** (1) **Prospective materials** misread as **already sent**; (2) **handoff/quote_ready** vs **missing driver**; (3) **model tokens** missing from lexicon (**Altima**); (4) **non–notice shopping openers** getting **notice/clarification** templates.
- **Under-covered in rules:** “**可以吗**/**行不行**” vs “**已经发了**”; **opening messages** with only ZIP/price/channel questions.
- **Realistic behaviors that still stress the system:** Permission-to-send questions bundled with full vehicle facts; **first bubble** general insurance anxiety **without** year/make/model.

## 7. Fix-now / Fix-next / Human-confirmation / LLM-assist

See `RULE_BASED_VS_HUMAN_LLM_ESCALATION_SPEC.md`. Short version:

- **Fix-now (rule):** WIRC-004 send-intent bug; WIRC-006 gating; WIRC-008 **Altima** (and similar) lexicon; WIRC-010 opener template/routing.
- **Human-confirmation:** Any **materials** flag, **new vs existing** policy nuance, **spouse/secondary driver** details, **corrected trim**.
- **LLM-assist (narrow):** Optional **classifier** for *ask vs assert* on sends, or **intent router** for multi-sentence opens—**not** full generative replacement.

## 8. Rule-based / fast-path summary

| Area | Location |
|------|-----------|
| **Conversation entry** | `triage_conversation()` in `services/fiqa_api/inbox_triage/triage.py` — merges turns, sets `triage_path` to `rule` when LLM off, calls `_rule_based_triage`. |
| **Primary rule router** | `_rule_based_triage()` — intent / flow selection, add-car branch, handoff fields. |
| **Add-car slot logic** | `_extract_add_car_fields`, `_text_has_add_car_driver_signal`, `_add_car_enough_for_handoff`, `_add_car_quote_ready_status`, `_add_car_structured_fields`, `_extract_add_car_vehicle_concrete`, `_is_add_car_vehicle_correction_signal`, `_get_next_ask_for_add_car`, `_get_add_car_acknowledgement` in `triage.py`. |
| **Business-editable prompts** | `configs/industries/insurance/add_car_rules.json` (loaded via `get_add_car_rules()` in `services/fiqa_api/inbox_triage/config_loader.py`). |
| **Markers / lexicon** | `configs/industries/insurance/markers.json` and related industry JSON (referenced by triage for intents and document/send signals). |
| **Scenario runners** | This sprint: `scripts/run_web_informed_add_car_realistic_battery.py`; related: `scripts/run_add_car_scenario_battery.py`, `run_add_car_driver_zip_materials_stress_battery.py`, `run_add_car_edge_case_simulations.py`, `scripts/run_inbox_triage_scenarios.py`. |

**High-level flow:** Customer text (+ prior turns) → **merged string** → markers / flows → if **add_car**: extract **boolean slot grid** + **vehicle string** → **quote_ready / need_more** → ZH/EN **next ask** or **handoff** client draft + broker next step + structured collected/still-needed lists.

## 9. Final broker-confidence judgment

- **Serious broker viewing:** **Conditional yes** for **happy-path demos** where the customer **names a known model clearly** and sends **ZIP + delivery + driver** within one or two turns. **Not yet** “hands off” for **materials-permission** wording or **ZIP/price-only** openers without a **precall fix** or **human triage**.
- **Biggest strength:** **Durable add-car merge** and **closure tone** when slots are recognized.
- **Biggest weakness:** **False “already sent”** customer messaging and **wrong first reply** on **shopping-small-talk** opens.
- **Best next step:** **Rule fix** for **WIRC-004**-class send intent + **template** for **WIRC-010**-class openers; **lexicon** pass for common **English models**; align **handoff_ready** with **driver** completeness.

## 10. 中文宏观总结

这 10 个 case 不是“真实统计”，而是把 **官方/经纪常要的加车信息**、**加州保费敏感话术**、以及 **华人客户在微信里常见的碎片表达**（先问价、先发截图行不行、邮编会不会贵、信息分几次补）拼在一起，做成 **可重复跑的规则路径压力测试**。

- **Rule-based 已经够用的地方：** 明确的 **年份+车型+邮编+提车+驾驶人**（可分两泡补全），以及 **中英混写车名**（有英文车型锚点时）整体表现稳定，handoff 与字段合并对经纪工作流友好。
- **更适合人工确认的地方：** 任何 **材料是否已收到**、**新客户/加保** 语义容易混在一起时；**配偶/次要驾驶人** 细节；**客户改口换车** 后的具体 trim。
- **以后可考虑窄 LLM 辅助的地方：** 像 **“我可以先发截图吗”** 这种 **询问** 被当成 **“已经发了”** 的语义区分；以及 **第一句只有邮编/贵不贵/怎么发资料** 的 **意图分流**（用小型分类器即可，不必上大段生成）。
- **现在能不能更放心给 Chen Kui 看：** 可以作为 **“主路径演示 + 明确边界”** 给看：把脚本定成 **客户第二次消息会补车型** 或 **第一句就含 YMM** 的 demo，会很漂亮；若 demo 允许客户 **第一句只问邮编贵不贵、或问能不能发截图**，则需要 **先修规则或标明人工接手** —— 否则仍有 **信任风险**（尤其是 WIRC-004 类 **客诉级** 话术）。
