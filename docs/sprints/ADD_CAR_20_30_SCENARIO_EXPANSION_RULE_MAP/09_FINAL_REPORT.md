# Add-Car 20–30 Scenario Expansion + Rule-Map Report

**Sprint:** `ADD_CAR_20_30_SCENARIO_EXPANSION_RULE_MAP`  
**Execution:** Rule path (`LLM_GENERATION_ENABLED=false` via runner)  
**Run artifacts:** `/tmp/acexp_only.json` (30), `/tmp/acexp_plus.json` (69 with ACB + ADZM)

---

## 1. Sprint theme

- **What was evaluated:** Add-Car unified intake on the **rule-based / fast-path** (`triage_conversation` → `_rule_based_triage`), using a **new 30-scenario** battery plus regression packs (ACB 17, ADZM 22).
- **Why now:** Add-Car is the flagship path; prior sprints hardened corrections, materials vs ask-to-send, ZIP, and driver micro-phrases. This sprint **widens realistic surface area** and **maps where the rule brain lives** for founder and broker conversations.

---

## 2. Document set created

| # | Path |
|---|------|
| Blueprint | `01_SCENARIO_EXPANSION_BLUEPRINT.md` |
| Design spec (20–30) | `02_SCENARIO_DESIGN_SPEC_20_30.md` |
| Battery file + spec | `scenario_battery.json`, `03_EXPANDED_SCENARIO_BATTERY_SPEC.md` |
| Evaluation criteria | `04_EVALUATION_CRITERIA.md` |
| Coverage gap spec | `05_COVERAGE_GAP_WEAK_SPOT_SPEC.md` |
| Rule-map spec | `06_RULE_MAP_SUMMARY_SPEC.md` |
| Execution outline | `07_EXECUTION_OUTLINE.md` |
| Founder notes | `08_FOUNDER_INSPECTION_NOTES.md` |
| Final report | `09_FINAL_REPORT.md` (this file) |
| Runner | `scripts/run_add_car_expansion_rule_map_battery.py` |

---

## 3. Expanded scenario battery overview

- **Count:** **30** scenarios (`ACEXP-001` … `ACEXP-030`).
- **Categories:** A clean (5), B partial (5), C correction (5), D materials (8), E price/side (5), F driver phrasings (distributed across scenarios; see design spec), G dense/messy (2).
- **Messiness tags:** 5 `clean`, 17 `messy`, 8 `edge`.
- **Why useful:** Covers **progressive disclosure**, **corrections**, **materials intent**, **price anxiety**, **office-style side questions**, and **jumpy threads** typical of Chinese WeChat behavior in CA auto insurance.

---

## 4. Evaluation criteria

Definitions from `04_EVALUATION_CRITERIA.md`:

- **Strong** — Correct playbook, extraction/state aligned, customer + broker outputs clearly useful; no misleading claims.
- **Acceptable** — Minor gaps (e.g. redundant confirm) without wrong product path or harmful wording.
- **Weak** — Partial success: generic broker line, messy combined reply, or missing model token in lexicon; human still salvageable.
- **Trust-breaking** — Wrong vehicle after correction, false materials handling, or category drift that misroutes the broker.

---

## 5. Scenario-by-scenario results (ACEXP)

Abbreviations: **HO** = final `handoff_ready`, **CAT** = final `issue_category`, **QRS** = `quote_ready_status`, **FUT** = `follow_up_type`.

| ID | Messages (summary) | Focus | Observed (final turn) | Class | Judgment |
|----|---------------------|-------|-------------------------|-------|----------|
| ACEXP-001 | 单泡 思域+95131+下周+我自己开 | A | HO ✓, CAT customer_question, QRS quote_ready | **Strong** | Full slots; standard handoff copy. |
| ACEXP-002 | 凯美瑞询价 → zip+周五+一个人开 | A | HO ✓, quote_ready | **Strong** | Classic 2-turn. |
| ACEXP-003 | X3 → 94102明天拿车 → 老公 | A | HO ✓, quote_ready | **Strong** | 3-turn merge solid. |
| ACEXP-004 | EN Model Y + zip + picking up + only I drive | A | HO ✓, quote_ready; `still_needed` lists `primary_driver` | **Acceptable** | Playbook correct; driver phrase “only I drive” not in substring markers—broker step compensates (“Confirm main driver”). |
| ACEXP-005 | 我想加车 → CX-5+zip+下周+本人开 | A | HO ✓, quote_ready | **Strong** | 本人开 detected. |
| ACEXP-006 | CR-V → 邮编+周四+老婆开 | B | HO ✓, quote_ready | **Strong** | Partial ordering OK. |
| ACEXP-007 | 邮编先导 → RAV4+明天+老公 | B | HO ✓, quote_ready | **Strong** | ZIP-first OK. |
| ACEXP-008 | 凯美瑞 → zip+周日 → 儿子 | B | HO ✓, quote_ready | **Strong** | Driver-last OK. |
| ACEXP-009 | Model3+zip+女儿开 → 下周五提车 | B | HO ✓, quote_ready | **Strong** | Delivery-second-bubble OK. |
| ACEXP-010 | RX+…+我自己开 → 电话 | B | HO ✓, quote_ready; phone in collected | **Strong** | Contact extraction surfaced. |
| ACEXP-011 | 雅阁 → 说错是Model Y | C | HO ✓, FUT correction; draft names Tesla | **Strong** | Correction path clear. |
| ACEXP-012 | X5 → 不是X5是X3 | C | HO ✓, FUT correction | **Strong** | Trim correction clear. |
| ACEXP-013 | 塞纳95131 → 等等2024塞纳+95110 | C | HO ✓; broker “2024 丰田” | **Weak** | Handoff OK; **concrete vehicle degrades** (塞纳→泛化). |
| ACEXP-014 | Pilot → Passport纠正+截图发微信 | C/D | HO ✓, FUT already_sent | **Strong** | Layered correction + materials. |
| ACEXP-015 | Civic EN → i meant Camry | C | HO ✓, FUT correction; EN draft | **Strong** | Code-switch correction OK. |
| ACEXP-016 | 宝马330i+齐+材料发你微信了 | D | HO ✓, FUT already_sent | **Strong** | Warm “材料发过了” tone. |
| ACEXP-017 | Outback+我已经发你微信了 | D | HO ✓, FUT already_sent | **Strong** | |
| ACEXP-018 | CX-9+截图发你了 | D | HO ✓, FUT already_sent | **Strong** | |
| ACEXP-019 | RAV4齐+行驶证要不要发你 | D | HO ✓, FUT new_info; permission lead | **Strong** | Prospective-send guard holds. |
| ACEXP-020 | 奥德赛+要不要先发给你 | D | HO ✓, FUT new_info | **Strong** | |
| ACEXP-021 | 汉兰达+我先发给你看看行吗 | D | HO ✓, FUT new_info | **Strong** | |
| ACEXP-022 | 思域齐 → dec page要不要先发你 | D | HO ✓, FUT new_info | **Strong** | Quote-ready + ask-send. |
| ACEXP-023 | 凯美瑞齐 → 行驶证发你微信了 | D | HO ✓, FUT already_sent | **Strong** | Second-bubble sent. |
| ACEXP-024 | ModelY齐+能便宜一点吗 | E | HO ✓; broker “Run quote for 2024” | **Weak** | Stays on Add-Car; **broker line loses model** in this dense layout. |
| ACEXP-025 | X1多少钱 → zip+明天+主要驾驶人是我 | E | HO ✓ | **Strong** | Price opener → collect → handoff. |
| ACEXP-026 | RAV4齐+garaging proof是什么 | E | HO ✓; draft explains garaging but **stacks** generic collect phrasing | **Weak** | Clarification + handoff OK; **reply polish** needed. |
| ACEXP-027 | 2022塞纳+95120明天+办公室几点下班 | E | HO ✗, QRS need_more | **Weak** | **塞纳** missing from make/model lexicon → blocks quote-ready path. |
| ACEXP-028 | 先帮我看看多少钱+CR-V+94566+周五+女儿 | E | HO ✓ | **Strong** | Dense price ask OK. |
| ACEXP-029 |  dense BMW X3 + 老婆开 + dec先发你 | G | HO ✓; broker names X3 | **Strong** | High-density stress passes. |
| ACEXP-030 | 含糊 → 凯美瑞纠正 → 齐+就这样 | G | HO ✓; turns 1–2 broker steps generic | **Acceptable** | Final state good; **early-thread broker text** noisy until details appear. |

### Counts (ACEXP-001–030)

| Label | Count |
|-------|------:|
| Strong | 24 |
| Acceptable | 2 |
| Weak | 4 |
| Trust-breaking | 0 |

### Combined regression (69 scenarios)

- **No final handoff:** **ACEXP-027**, **ADZM-M06**, **ADZM-X05** (3 total). ADZM failures match known stress/edge design; **no new category drift** beyond the 塞纳 gap called out above.

---

## 6. Overall pattern analysis

### Clearly strong now

- **Playbook lock-in:** All 30 ACEXP scenarios remained **`customer_question`** on the final turn—no accidental premium_review/payment routing.
- **Progressive multi-turn merge:** ZIP/vehicle/driver/delivery ordering variants (B) consistently reach **quote_ready** + handoff.
- **Materials intent:** **already_sent** vs **prospective send** separation is reliable on the scripted phrasing (D).
- **Vehicle corrections:** Customer-facing acknowledgements for Honda→Tesla, X5→X3, EN “i meant” (C) are **broker-demo grade**.

### Still weak

- **Broker-facing vehicle concreteness** on some dense/mixed bubbles (**024**, **013**): year or make-family only.
- **Chinese model nicknames / minivan names** (**027** 塞纳): not in `_extract_add_car_fields` model substring list → **collection incomplete**.
- **Clarification + handoff reply composition** (**026**): correct content but **redundant** “再收集” style tail.
- **English driver micro-phrase coverage** (**004**): “only I drive” vs documented “only me”.

### Under-covered (suggested next tests)

- More **non-Lexus/Toyota Chinese nicknames** (e.g. 锐志, 大霸王, 途乐) and **trim tokens** (e.g. **xDrive30i** without BMW in text—here BMW present).
- **Two active vehicles** without a clear “只要一台” disambiguation (030 resolves to one; sharper two-VIN cases not in this battery).

---

## 7. Fix-now / Fix-next / Acceptable / Defer

| Bucket | Item |
|--------|------|
| **Fix-next (highest ROI)** | Extend **model / nickname lexicon** (塞纳 → Sienna path) and/or light **vehicle span** extraction so broker line keeps concrete model. |
| **Fix-next** | Add **“only i drive”** (and variants) to `_ADD_CAR_DRIVER_MARKERS` for parity with “only me”. |
| **Acceptable** | ACEXP-004, ACEXP-030 — monitor; no urgent change for demo if broker reads `still_needed_fields`. |
| **Defer** | Full **two-vehicle disambiguation** engine; **office-hours** side answer quality (027 turn still completes if model fixed). |

---

## 8. Rule-based / fast-path summary

### How a message becomes Add-Car (high level)

1. **`triage_conversation`** merges prior turns + latest bubble (`_build_conversation_text_for_triage`).  
2. With LLM off, **`_rule_based_triage`** runs **`_classify_with_guardrails`** → category templates. Add-car detection uses **`_is_add_vehicle_request`**.  
3. **`_get_next_ask_draft`** (and related add-car helpers) build the **next customer draft** from **`_get_next_ask_for_add_car`**, which pulls configurable prompts via **`get_add_car_rules()`**.  
4. Handoff assembly applies **`_extract_add_car_fields`**, **`_add_car_enough_for_handoff`**, **`_derive_follow_up_type`**, **`_get_prospective_send_materials_lead`**, and broker summary / `broker_next_step` tailoring (materials-sent, correction, coverage side questions, etc.).

### Main files (concrete)

| File | Role |
|------|------|
| `services/fiqa_api/inbox_triage/triage.py` | **Primary rule brain:** `_is_add_vehicle_request`, `_extract_add_car_fields`, `_text_has_add_car_driver_signal` / `_ADD_CAR_DRIVER_MARKERS`, `_extract_ca_zip_from_message` / `_CA_ZIP_STRICT_RE`, correction helpers (`_is_add_car_vehicle_correction_signal`, `_extract_add_car_vehicle_concrete`), `_get_add_car_acknowledgement`, `_get_next_ask_for_add_car`, `_add_car_structured_fields`, `_derive_follow_up_type`, `_is_prospective_send_offer_message`, `_get_prospective_send_materials_lead`, `_rule_based_triage`, **`triage_conversation`** (orchestration, handoff flags, `quote_ready_status`). |
| `services/fiqa_api/inbox_triage/config_loader.py` | Loads **`get_add_car_rules()`** from JSON; **`_ADD_CAR_RULES_DEFAULTS`** fallback. |
| `configs/industries/insurance/add_car_rules.json` | Editable **next-step prompts**: `ask_vehicle`, `ask_zip`, `ask_delivery_driver`, `ask_driver_only` (zh/en). |
| `services/fiqa_api/routes/inbox_triage.py` | HTTP API **`triage_conversation`**, Rules Center hooks for add-car rules. |
| `services/fiqa_api/inbox_triage/case_store.py` | Case persistence; contact fields from triage (`ADD_CAR_IDENTITY_CONTACT_LITE` notes in code). |
| `scripts/run_add_car_expansion_rule_map_battery.py` | This sprint’s runner (+ optional ACB/ADZM). |
| `scripts/run_add_car_scenario_battery.py`, `scripts/run_add_car_driver_zip_materials_stress_battery.py`, `scripts/run_add_car_edge_case_simulations.py`, `scripts/run_add_car_high_roi_regression.py`, `scripts/guardrail_inbox_triage.sh`, `scripts/test_inbox_triage_api.py` | Regression / guardrail / API smoke. |
| `configs/customer_entry_multi_turn_simulations.json` | Broader **add_car_quote** simulation entries (separate from sprint JSON batteries). |

### Key function entry points (line anchors in `triage.py`)

- `_is_add_vehicle_request` — ca. **436**  
- `_rule_based_triage` — ca. **1060**  
- `_extract_add_car_fields` — ca. **1804**  
- `_add_car_structured_fields` — ca. **2181**  
- `_get_add_car_acknowledgement` — ca. **2463**  
- `_get_next_ask_for_add_car` — ca. **2545**  
- `_get_next_ask_draft` — ca. **2642**  
- **`triage_conversation`** — ca. **2685**

---

## 9. Final broker-confidence judgment

- **Serious broker viewing?** **Yes**, for the **core Add-Car story** (collect → handoff, materials vs ask-to-send, corrections, ZIP/driver progression) on the rule path—**provided** the demo script avoids **rare Chinese nicknames** and **overly dense “cheap + full slots”** lines until broker-line extraction is tightened.
- **Biggest strength:** **Intent stability** + **materials/correction** behavior under realistic Chinese phrasing.
- **Biggest remaining weakness:** **Vehicle concreteness** in broker-facing text and **lexicon gaps** for some Chinese model names.
- **Single best next fix:** **Expand model/nickname coverage + normalize “only I drive”** so `quote_ready` / `broker_next_step` stay aligned with what the customer actually typed.

---

## 10. 中文宏观总结

- **这轮测了多少个场景：** 新增 **30** 个 `ACEXP` 场景；若加上历史电池 **ACB（17）+ ADZM（22）**，一共 **69** 次场景运行（同一套 rule path）。
- **哪些已经很稳：** 多轮补齐（车型/邮编/提车/驾驶人）、**材料已发 vs 问你先发** 的区分、常见纠正（换品牌/换车型）、整体 **不会跑错大类**（保持 Add-Car / `customer_question`）。
- **哪些还弱：** 少数 **经纪人侧车型不够具体**（只写到年份或“丰田”）；**“塞纳”** 这类 **中文昵称/车型词未进关键词表** 时会卡住 handoff；**夹杂科普问题时**（garaging）客户回复有时会 **重复堆叠** “再发资料”话术；英文 **“only I drive”** 这类驾驶人表达覆盖不如 **only me**。
- **rule-based 主脑在哪里：** 主要在 **`services/fiqa_api/inbox_triage/triage.py`**（Add-Car 提取、跟进行为 `follow_up_type`、下一步追问/确认、handoff 组装），可配置文案在 **`configs/industries/insurance/add_car_rules.json`**（由 **`config_loader.get_add_car_rules`** 加载）；入口 API 在 **`services/fiqa_api/routes/inbox_triage.py`**。
- **现在能不能更放心给 Chen Kui 看：** **可以更有信心展示主线 Add-Car**，但建议在演示里 **避开生僻中文车型昵称** 和 **“砍价+超长同泡”** 的极端组合，或把它当作“办公室人工兜底”示例；工程上 **下一轮最值得做的是补齐车型词表/经纪人侧车型摘要**。
