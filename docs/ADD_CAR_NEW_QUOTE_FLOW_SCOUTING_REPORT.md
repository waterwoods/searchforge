# Add Car / New Quote Flow Scouting Report

**Sprint:** Add Car / New Quote Flow Scouting Sprint  
**Date:** 2026-03-10  
**Scope:** SearchForge → Chen Kui Insurance Unified Entry — Add Car / New Quote flow only

---

## 1. What already exists

### Intent detection and markers
- **`configs/industries/insurance/markers.json`:** `add_vehicle` (加车, add car, new car, 报价, how much, bought, etc.) and `vehicle_context` (vin, vehicle, model, tesla, toyota, honda, bmw, etc.)
- **`triage.py`:** `_is_add_vehicle_request()` — requires add_vehicle markers AND (vehicle_context OR "quote" OR "报价")
- **Fallback:** Hardcoded `_FALLBACK_MARKERS` in triage.py mirrors config when file missing

### Reply templates
- **`configs/industries/insurance/reply_templates.json`:** `add_car` zh/en first-turn templates
- **`configs/clients/chen_kui/reply_overrides.json`:** Empty — no client-specific overrides
- **`_build_client_reply_draft()`:** Uses add_car template for customer_question + add_vehicle; mixed-intent add-car + garaging proof confusion gets retrieval augmentation

### Broker handoff
- **`configs/clients/chen_kui/handoff_phrases.json`:** `add_car` zh ("报价资料已收集，办公室会尽快出价，有结果会联系您。") and en ("Quote details received. Our office will review and follow up with you.")
- **`broker_next_step`:** "Collect the new vehicle details, confirm the delivery date and primary driver, then quote or add it the same day if possible."
- **`client_prep`:** "Year, make/model, VIN if available, delivery date, zip or address, lienholder if any, and primary driver details."

### Multi-turn logic
- **`_extract_add_car_fields()`:** Extracts year, zip, model, delivery, driver, vin from customer messages only
- **`_add_car_enough_for_handoff()`:** (year+model or VIN) + (zip or delivery or driver)
- **`_get_next_ask_for_add_car()`:** Asks zip if missing; else delivery+driver; else None (hand off)
- **`_get_next_ask_draft()`:** Only add-car gets "ask one more" beyond turn 2; others hand off
- **First-turn handoff:** When `customer_count + 1 == 1` and `_add_car_enough_for_handoff(fields)` → hand off immediately

### Conversation summary
- **`_build_conversation_summary()`:** Intent hint ("New quote / new vehicle" vs "Add car to existing policy"), "Collected: year, model, zip, delivery, driver", "Still needed: delivery date, main driver" when applicable

### Retrieval
- **Add-car + garaging proof confusion:** `retrieve_document_explanation()` augments reply when add-car + document confusion (garaging proof)
- **No standalone retrieval** for pure add-car quote — retrieval only for notice/document confusion

### Simulations and tests
- **`inbox_triage_scenarios.json`:** R14, R17, R18, D4, ER1, ER2 (add-car single-turn)
- **`customer_entry_multi_turn_simulations.json`:** MT1, MT2, MT11, MT13, MT15, MT16 (add-car multi-turn)
- **`expression_robustness_cases.json`:** AC1–AC10 (add_car_quote intent)
- **`adversarial_real_user_scenarios.json`:** A1–A7 (add_car flow)
- **`mixed_intent_scenarios.json`:** MI-AC1–4 (add-car + garaging, premium, renewal, notice)
- **`long_context_memory_shift_simulations.json`:** LC-AC1–5 (corrections, partial info, driver correction)

### Scripts
- `run_adversarial_simulation.py --flow add_car`
- `run_expression_robustness.py --intent add_car_quote`
- `run_multi_turn_simulations.py`
- `run_complex_adversarial_simulation.py`
- `prepare_unified_intake_founder_demo.py` — seeds "Add-car quote request" case

### Docs
- `CUSTOMER_ENTRY_REPLY_STRATEGY.md` — add-car strategy, second-turn rules
- `FIVE_BUSINESS_FLOWS_TARGETS.md` — Flow 1 acceptance criteria
- `UNIFIED_INTAKE_DEMO_READINESS.md` — BMW X5 / new car quote in best 3-case demo
- `ADD_CAR_NEW_QUOTE_VERTICAL_FLOW_SPRINT_REPORT.md` — latest vertical sprint
- `MATURE_INTAKE_SKELETON.md` — shared detect → ask → enough? → hand off

---

## 2. What already feels strong

- **Intent detection:** Add-car is well-covered for standard phrasings (加车, 报价, new car, how much, bought + vehicle). Expression robustness: 10/10 AC variants pass; adversarial: 7/7 add_car scenarios pass.
- **First-turn reply:** Template asks for year, model, VIN, delivery, zip, driver — not generic "provide more context."
- **Multi-turn flow:** Progressive ask (year only → ask zip → zip → hand off) works. Full-info first turn hands off immediately.
- **Handoff message:** "报价资料已收集，办公室会尽快出价" is broker-natural and distinct from generic "办公室会尽快处理."
- **Broker summary:** Intent hint (new quote vs add car), Collected, Still needed in `conversation_summary`.
- **Mixed-intent add-car + garaging:** Handled — garaging explanation + add-car ask.
- **Founder demo:** Add-car is in best 3-case and 5-case flows; BMW X5 / new car quote explicitly documented.

---

## 3. What is incomplete or weak

### Customer-side
- **Ultra-short / vague:** "宝马x5，多少钱" — `vehicle_context` includes "x5" but lowercase "宝马" may not match; "我新车，下周拿，保险大概？" (A2) has no vehicle details — likely unclear or weak.
- **VIN-only first turn:** "VIN xxx, 90210" without quote intent markers is not recognized as add-car (documented in sprint report).
- **Model not in list:** `_extract_add_car_fields` has a fixed model list; new makes/models (e.g. Rivian, Lucid) may miss.
- **"想加车，型号还没定" (A6):** Intent clear, no model — system will ask for fields but handoff threshold requires year+model or VIN.

### Broker-side
- **Collected/Still needed:** Only in `conversation_summary` free text, not structured fields. Broker cannot filter/sort by "has zip" or "missing driver."
- **New quote vs add-car:** Intent hint is in summary text; no dedicated `flow_type` or `intent_subtype` field for downstream use.

### Simulation / test coverage
- **`run_inbox_triage_scenarios.py`:** Covers R14, R17, R18, D4, ER1, ER2 but not explicitly add-car-only; full guardrail runs all scenarios.
- **Adversarial A2, A4, A6, A7:** Vague or minimal-info cases — pass/fail not verified in this scout; A1–A7 all passed in run.
- **Long-context LC-AC3:** "我刚才说错了，是我老婆开那辆" — driver correction; `conversation_summary` does not explicitly carry "corrected: main driver = spouse" — broker infers from `source_text`.
- **Mixed-intent MI-AC2 (add-car + premium):** Primary intent handling — triage may surface add-car; premium ask may be secondary; not validated.

### Demo readiness
- **Add-car is not first in demo order:** Cancellation risk opens first; add-car is case 3 or 4. For a quote-focused pitch, add-car could lead.
- **No add-car-specific demo script:** `CHEN_KUI_FOUNDER_DEMO_SCRIPT` mentions add-car but does not have a dedicated add-car-only walkthrough.

### Realism / business value
- **Lienholder:** In `client_prep` but not in handoff threshold or extraction; rarely asked in first 2 turns (by design).
- **New policy vs renewal add-car:** "不是续保，是新保单" (LC-AC4) — clarification handled; no confusion with premium_review.
- **Carrier quote integration:** Out of scope; broker still does manual quote.

---

## 4. What is duplicated or confusing

- **Markers in two places:** `markers.json` and `_FALLBACK_MARKERS` in triage.py. Config wins when loaded; fallback used when config empty. Not confusing but duplicated.
- **Handoff threshold:** `_add_car_enough_for_handoff` is hardcoded; `CLIENT_PACK_FOUNDATION` and `CONFIG_EXTRACTION_GUIDE` say "could move to config later" — not done.
- **"New quote" vs "Add car to existing policy":** Logic: "加车"/"add car"/"add vehicle" → "Add car to existing policy"; else → "New quote / new vehicle." Distinction is clear in code but not exposed as a structured field.
- **`customer_question` category:** Add-car, remove-car, premium, DMV, claim all map to `customer_question`; differentiation is via intent detection and templates. Fine for triage, but broker-facing labels ("Add car quote") come from `conversation_summary` intent hint, not a dedicated field.

---

## 5. Highest-value gaps

1. **Ultra-short / vague add-car (e.g. A2, A6, A7):** "我新车，下周拿，保险大概？", "想加车，型号还没定", "quote for new car, picking up tomorrow" — risk of unclear or generic fallback. **Fix:** Relax `_is_add_vehicle_request` for clear quote intent + delivery/date even without vehicle details; or add markers for "新车"/"new car" + "保险"/"insurance"/"quote" as sufficient when delivery present.
2. **Structured Collected/Still needed for broker:** Today it's only in `conversation_summary` text. **Fix:** Add `collected_fields` and `still_needed_fields` (or similar) to triage output for add-car so UI/filters can use them.
3. **Adversarial and mixed-intent regression:** Run `run_adversarial_simulation.py --flow add_car` and `run_complex_adversarial_simulation.py` in CI/guardrail; ensure A2, A6, A7 and MI-AC2, MI-AC4 have explicit pass criteria.
4. **Add-car as demo lead (optional):** If founder wants to lead with revenue/quote, add an add-car-first demo path or script variant.
5. **VIN-only first turn:** Low frequency; documented as known limitation. Defer unless real traffic shows it.

---

## 6. Recommended next sprint scope

**Narrow Add Car / New Quote vertical sprint (1–2 days):**

1. **Gap 1 — Ultra-short add-car:** Add or relax markers so "我新车，下周拿，保险大概？" and "quote for new car, picking up tomorrow" get add-car reply (ask for vehicle details) instead of unclear. Validate A2, A6, A7 in adversarial.
2. **Gap 2 — Structured broker output:** Add `collected_fields: list[str]` and `still_needed_fields: list[str]` to triage output for add-car when applicable. Wire to `conversation_summary` or a new field; update UI if needed.
3. **Gap 3 — Regression protection:** Add explicit assertions for adversarial A2, A6, A7 and mixed-intent MI-AC2, MI-AC4 in `run_adversarial_simulation.py` or a dedicated add-car guardrail script.
4. **Out of scope this sprint:** VIN-only, lienholder in threshold, config-based handoff thresholds, new policy vs renewal structured field.

---

## 7. 中文宏观总结

**现在这条主线已经做到哪了：**
- 加车/报价的意图识别、首轮回复、多轮追问（缺邮编问邮编、缺提车/驾驶人再问）、交办语、经纪人摘要（Collected/Still needed）都已实现。
- 全信息首条、分步补全、中英混合、简写（加一台X5、90210）都能跑通。
- 加车+garaging proof 混淆有检索增强；新报价 vs 加车有区分。

**哪些已经不错：**
- 意图识别覆盖好，表达鲁棒性和对抗测试都通过。
- 多轮逻辑清晰：先要邮编，再要提车/驾驶人，够了就交办。
- 交办语「报价资料已收集，办公室会尽快出价」自然、好懂。

**最大缺口是什么：**
- 极简/模糊说法（如「我新车，下周拿，保险大概？」、「quote for new car, picking up tomorrow」）可能被判成 unclear，拿不到加车专用回复。
- 经纪人看到的 Collected/Still needed 只在摘要文本里，没有结构化字段，无法做筛选或排序。
- 对抗和混合意图的回归没有明确纳入 guardrail，部分场景可能漏测。

**今天最应该补哪一刀：**
- 补一刀：极简加车意图 — 放宽或加 marker，让「新车+保险/quote+提车」这类说法也能进 add-car，而不是 unclear。这是投入小、见效快的改进。
- 第二刀：给 add-car 输出 `collected_fields` / `still_needed_fields`，方便经纪人工作台和后续自动化。

---

*End of scouting report*
