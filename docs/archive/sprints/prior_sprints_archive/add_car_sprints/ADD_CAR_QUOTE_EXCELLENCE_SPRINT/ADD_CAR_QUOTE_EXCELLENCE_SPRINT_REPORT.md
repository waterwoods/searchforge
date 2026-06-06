# Add-Car Quote Excellence Sprint Report

## 1. Sprint theme

- **What was chosen:** Add-car / quote intake flow excellence — make it the strongest, cleanest, most trial-worthy scenario.
- **Why now:** Add-car is one of the broker's most valuable workflows. Before real broker trial with Chen Kui, this scenario must be demo-ready and handoff-ready.

---

## 2. Document set created

| Doc | Path |
|-----|------|
| 1. Add-Car Quote Excellence Blueprint | `01_ADD_CAR_QUOTE_EXCELLENCE_BLUEPRINT.md` |
| 2. Add-Car Field Collection Spec | `02_ADD_CAR_FIELD_COLLECTION_SPEC.md` |
| 3. Add-Car Handoff / Quote-Readiness Spec | `03_ADD_CAR_HANDOFF_QUOTE_READINESS_SPEC.md` |
| 4. Add-Car Broker UX Spec | `04_ADD_CAR_BROKER_UX_SPEC.md` |
| 5. Execution Outline | `05_EXECUTION_OUTLINE.md` |
| 6. Acceptance / Add-Car Criteria | `06_ACCEPTANCE_ADD_CAR_CRITERIA.md` |
| 7. Founder Inspection Notes | `07_FOUNDER_INSPECTION_NOTES.md` |

---

## 3. Baseline audit

### Strongest current parts

- Handoff threshold: vehicle + zip + (delivery or driver) — clear and correct
- Ask order: vehicle → zip → delivery/driver in `_get_next_ask_for_add_car`
- HT8 fix: add-car + garaging question in same turn → answer + hand off
- First-turn handoff when full info provided
- broker_next_step: "Run quote for collected vehicle details..."
- collected/still_needed structured fields

### Biggest weakness

- broker_next_step and conversation_summary did not show concrete vehicle (e.g. "2024 Tesla Model Y") when extractable
- add_car_rules.json missing `ask_driver_only` (code used hardcoded fallback)
- Coverage-adjust side question ("顺便 coverage 可以调吗") not explicitly handled — would ask for driver instead of answering and handing off

### Biggest broker rework source

- Under-filled handoff (mitigated by current threshold)
- Generic broker_next_step without concrete vehicle

### Biggest customer-friction point

- Side questions (garaging, coverage) answered late or ignored

---

## 4. 10–20 point breakdown

| # | Point | Status |
|---|-------|--------|
| 1 | Minimum required fields: year+model (or VIN), zip, delivery or driver | ✓ |
| 2 | Useful optional: insurance_status, additional_drivers | ✓ |
| 3 | Best ask-next order: vehicle → zip → delivery/driver | ✓ |
| 4 | Quote-ready threshold: vehicle + zip + (delivery or driver) | ✓ |
| 5 | Under-filled threshold: never hand off with only year or only zip | ✓ |
| 6 | Same-goal corrections: stay in same case; extraction uses merged text | ✓ |
| 7 | Late detail handling: "对了 是我老婆开" captured in T3 | ✓ |
| 8 | Garaging / doc clarification: answer first, hand off (HT8) | ✓ |
| 9 | Mixed-intent coverage: "顺便 coverage 可以调吗" — answer + hand off | ✓ |
| 10 | Broker summary: concrete vehicle when extractable | ✓ |
| 11 | broker_next_step: "Run quote for {vehicle_concrete}..." | ✓ |
| 12 | Deferred: real premium calculation, carrier integration | ✓ |
| 13 | Most reduces broker rework: concrete vehicle + clear next step | ✓ |
| 14 | Most improves customer experience: answer side questions before handoff | ✓ |
| 15 | Most improves trial/demo value: HT11, HT12, coverage handling | ✓ |
| 16 | Simulations: handoff_timing 12/12 (HT11, HT12 added) | ✓ |
| 17 | Manual founder tests: 4–6 cases in 07_FOUNDER_INSPECTION_NOTES | ✓ |
| 18 | Future V2: X3 correction in broker_next_step (HT12 shows "Bmw" not "BMW X3") | Deferred |

---

## 5. Iteration loop 1

**What was fixed:** add_car_rules.json — added `ask_driver_only` (zh/en).

**Why:** Code used `ask_driver_only` in `_get_next_ask_for_add_car` but config lacked it; used hardcoded fallback.

**What became better:** Config-driven; consistent with Rules Center pattern.

**What did not improve:** Ask-next behavior (already correct).

**Worth it:** Yes — config completeness.

---

## 6. Iteration loop 2

**What was fixed:** broker_next_step and conversation_summary with concrete vehicle; coverage-adjust side-question handling.

**Why:** Broker wants "Run quote for 2024 Tesla Model Y" not just "Run quote for collected vehicle details." Coverage question in same turn was causing driver ask instead of handoff.

**Changes:**
- `_extract_add_car_vehicle_concrete()` — extract year + model (e.g. "2024 Tesla Model Y")
- broker_next_step: when vehicle extractable, use it
- conversation_summary: collected_hint includes concrete vehicle
- Coverage question: when "coverage 可以调" in same turn, answer briefly + hand off
- `_get_next_ask_for_add_car`: skip driver ask when coverage_question in last message

**What improved vs loop 1:** Broker gets concrete vehicle; coverage side question no longer blocks handoff.

**What still remained weak:** HT12 correction "不是X5 是X3" — broker_next_step shows "2024 Bmw" not "2024 BMW X3" (extraction prefers first occurrence).

**Worth it:** Yes — major broker UX improvement.

---

## 7. Iteration loop 3

**What was hardened:** Add-car excellence simulations (HT11, HT12); coverage-question skip in ask-next.

**Why:** HT11 (add-car + coverage question) and HT12 (correction 不是X5 是X3) needed explicit coverage and correction handling.

**Changes:**
- `configs/handoff_timing_simulations.json`: added HT11, HT12
- `_get_next_ask_for_add_car`: coverage_question → return None (hand off)
- Handoff reply: when add-car + coverage question, prepend coverage answer

**What improved vs loop 2:** HT11 passes; HT12 passes (handoff timing); coverage question answered.

**What still remained weak:** HT12 broker_next_step shows "2024 Bmw" not "2024 BMW X3" — correction-preference extraction deferred.

**Worth it:** Yes — 12/12 handoff timing simulations pass.

---

## 8. Validation summary

| Check | Result |
|-------|--------|
| guardrail_inbox_triage.sh | PASS |
| run_inbox_triage_scenarios.py | 64/64 passed |
| run_multi_turn_simulations.py | 41/41 Strong |
| run_handoff_timing_simulations.py | 12/12 passed |

**Limitations:** HT12 broker_next_step shows "Bmw" not "BMW X3" after correction; X3-preference extraction deferred to V2.

---

## 9. Deployment / release judgment

| Component | Status |
|-----------|--------|
| Backend | Changed — triage.py, add_car_rules.json |
| Frontend | No changes |
| Redeploy needed | Backend yes (Cloud Run); frontend no |

**Founder can inspect:** Yes — run guardrail; test add-car flows on Vercel.

---

## 10. Founder manual test list

| # | Input | Expected |
|---|-------|----------|
| 1 | 加车 2024 Tesla Model Y → 90210 下周提车 | Handoff T2; summary has year, model, zip, delivery |
| 2 | 加车 2024 X5 → 90210 下周提车 对了 garaging proof 是什么 | Answer garaging; handoff T2 |
| 3 | 加车 2021 Honda → 不是这个 是 2024 Tesla Model Y → 90210 下周提车 | Handoff T3; collected shows 2024 Tesla |
| 4 | 加车 2024 Tesla Model Y → 90210 下周提车 → 对了 是我老婆开 | Ask driver T2; handoff T3 with driver |
| 5 | 加车 2024 Tesla Model Y → 90210 下周提车 顺便问一下 coverage 可以调吗 | Answer coverage; handoff T2 |
| 6 | 加车 2024 X5 90210 下周提车 我开 | Handoff T1; full info |

---

## 11. Final judgment

| Aspect | Result |
|--------|--------|
| **Biggest gain** | Concrete vehicle in broker_next_step + coverage side-question handling |
| **Biggest remaining weakness** | HT12 correction broker_next_step shows "Bmw" not "BMW X3" |
| **Star trial scenario?** | Yes — add-car is demo-ready; handoff timing and ask-next are strong |
| **Best next step** | Deploy backend; founder manual test; add X3 correction preference in V2 |

---

## 12. 中文宏观总结

- **为什么现在做这一轮：** 加车是经纪人最高频、最有价值的场景；在陈奎实盘前必须做到可演示、可交付。
- **主要修了什么：** 1) add_car_rules 补全 ask_driver_only；2) broker_next_step 和 conversation_summary 展示具体车型；3) coverage 侧问同消息时回答并 hand off；4) 新增 HT11、HT12 模拟。
- **最大提升：** 经纪人收到具体车型（如 "2024 Tesla Model Y"）和更清晰的下一步；覆盖侧问不再打断 handoff。
- **还差什么：** HT12 修正 "不是X5 是X3" 后 broker_next_step 仍显示 "Bmw" 而非 "BMW X3"。
- **下一步最该做什么：** 部署后端；创始人手动测试；V2 做 X3 修正优先提取。

---

## 13. COPY/PASTE FOUNDER BLOCK

```
Add-Car Quote Excellence Sprint — Founder Summary

Biggest improvement: Broker now sees concrete vehicle (e.g. "2024 Tesla Model Y") in broker_next_step and conversation_summary. Coverage side question ("顺便 coverage 可以调吗") is answered and handoff proceeds; no more driver ask blocking it.

Biggest remaining weakness: HT12 correction "不是X5 是X3" — broker_next_step shows "2024 Bmw" not "2024 BMW X3". Deferred to V2.

Redeploy needed: Backend yes (triage.py, add_car_rules.json). Frontend no.

Test first on Vercel: (1) 加车 2024 Tesla Model Y → 90210 下周提车 — verify broker_next_step shows "Run quote for 2024 Tesla Model Y". (2) 加车 2024 X5 → 90210 下周提车 对了 garaging proof 是什么 — verify answer + handoff. (3) 加车 2024 Tesla → 90210 下周提车 顺便问一下 coverage 可以调吗 — verify coverage answer + handoff.
```

---

## 14. REQUIRED SHORT OVERVIEW

### 为什么做这件事

加车/报价是经纪人最高频、最有价值的场景。在陈奎实盘前，需要把加车做成可演示、可交付的「明星场景」。

### 主要用了什么方法/技术

- 控制文档：7 份 blueprint + spec + 验收标准
- 三轮迭代：config 补全 → broker 摘要 + coverage 侧问 → 模拟加固
- 新增 `_extract_add_car_vehicle_concrete()` 提取具体车型
- 新增 HT11、HT12 模拟；覆盖 coverage 同消息处理

### 这轮最大的提升

经纪人收到具体车型 + 清晰下一步；覆盖侧问不再打断 handoff；12/12 handoff timing 模拟通过。

### 现在还差什么

HT12 修正「不是X5 是X3」后 broker_next_step 仍显示 "Bmw" 而非 "BMW X3"；X3 优先提取留待 V2。
