# Add-Car Quote 80% Completion Report

**Sprint:** Add-Car Quote 80% Completion Sprint  
**Date:** 2026-03-16  
**Scope:** SearchForge → Chen Kui Insurance Unified Entry

---

## 1. Sprint Theme

- **What was chosen:** Upgrade the Add-Car Quote flow from a short 2–3 turn demo-grade flow to a more realistic, business-usable ~80%-complete standard flow.
- **Why now:** The founder identified that the current flow is too short, too demo-like, and not strong enough to hand over to Chen Kui and assistants for real use. Making it configurable too early would expose an immature flow. The correct sequence is: first make Add-Car Quote itself much stronger, then make that mature flow configurable.

---

## 2. Document Set Created

| Doc | Path |
|-----|------|
| Product Blueprint | `docs/sprints/add_car_quote_80_completion/01_PRODUCT_BLUEPRINT.md` |
| Add-Car Flow Design Spec | `docs/sprints/add_car_quote_80_completion/02_ADD_CAR_FLOW_DESIGN_SPEC.md` |
| Conversation / Slot Collection Spec | `docs/sprints/add_car_quote_80_completion/03_CONVERSATION_SLOT_COLLECTION_SPEC.md` |
| Execution Outline | `docs/sprints/add_car_quote_80_completion/04_EXECUTION_OUTLINE.md` |
| Acceptance / SLA Criteria | `docs/sprints/add_car_quote_80_completion/05_ACCEPTANCE_SLA_CRITERIA.md` |
| Founder Demo / Inspection Notes | `docs/sprints/add_car_quote_80_completion/06_FOUNDER_DEMO_INSPECTION_NOTES.md` |

---

## 3. Baseline Audit

### Current Add-Car Quote Flow (Before Sprint)

| Aspect | Before |
|--------|--------|
| **First-turn** | Template lists 6 items; code overrides with progressive ask (year+zip, etc.) |
| **Typical turns** | 2–3 before handoff |
| **Fields collected** | year, model, zip, delivery, driver, VIN |
| **Handoff threshold** | (year+model or VIN) + (zip OR delivery OR driver) |
| **Handoff point** | Often after 2 turns when zip provided |
| **Classification** | **Too short** — zip alone enough for handoff; office often needs delivery/driver for quote |

### Biggest Current Weakness

**Zip alone was enough for handoff.** A real office would want delivery date or primary driver before running a quote. The flow handed off too early when the user gave only vehicle + zip.

### Why the Old Flow Was Too Demo-Like

- 2 turns typical: "加一台X5" → "90210" → hand off
- No delivery/driver requirement
- Case summary thin; broker would chase delivery/driver anyway
- Flow felt like a quick demo, not real intake

---

## 4. Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **What to collect** | vehicle + zip + (delivery or driver) | Office needs location + timing/driver for quote |
| **Order** | vehicle → zip → delivery/driver | Cannot quote without vehicle; zip affects rate; delivery/driver affects timing |
| **First response** | Ask 1–2 next things; acknowledge what user said | Already implemented in code; template override |
| **Handoff point** | When vehicle + zip + (delivery or driver) | Meaningful; broker can act |
| **80% completion** | Stricter handoff; richer extraction (insurance_status, additional_drivers); 4–5 turns when partial | Not enterprise; not configurable; good enough for pilot |

---

## 5. Iteration Loop 1

### What Changed

- **Handoff threshold:** Require zip **and** (delivery or driver). Zip alone no longer enough.
- **Extraction:** Added `insurance_status` (add_to_existing, new_customer) and `additional_drivers` (additional_drivers, only_me) to `_extract_add_car_fields`.
- **Structured fields:** `collected_fields` / `still_needed_fields` now include insurance_status and additional_drivers when detected.
- **Scenarios:** Updated MT11, MT13, MT19, MT30, MT35, R4, first-turn continuity test.

### What Became More Realistic

- Flow continues to ask for delivery when user gives only vehicle+zip
- 4–5 turns typical for partial-info entry
- Case summary reflects delivery/driver when collected
- Broker receives cases with enough info to quote

### What Became More Useful for Business

- Fewer broker follow-ups for delivery/driver
- Collected/Still needed chips more accurate
- Handoff at a meaningful point

### What Did Not Improve

- No explicit "additional drivers?" ask yet (extraction only)
- No coverage_preference ask
- First-turn template still lists 6 items in config (code overrides)

### Whether Loop 1 Was Worth It

**Yes.** The stricter handoff is the highest-value change. Flow depth increased; handoff is more meaningful.

---

## 6. Iteration Loop 2

**Skipped.** Loop 1 achieved the main goal. Loop 2 targets (first-turn template polish, additional_drivers ask) were deferred:

- First-turn logic already asks 1–2 things via code override
- Additional_drivers ask would add a turn; current flow depth is sufficient for 80%
- Guardrail and multi-turn sims pass; no regression

---

## 7. Optional Loop 3

**Not used.** No clearly valuable, low-risk refinement remained. Stopping is correct: flow is stronger; tests pass; further changes risk regression without proportional gain.

---

## 8. Validation Summary

| Test | Result |
|------|--------|
| `run_inbox_triage_scenarios.py` | 53/53 passed |
| `run_multi_turn_simulations.py` | 38/38 strong |
| `audit_state_field_accuracy.py` | 6/7 passed (M1 pre-existing) |
| `verify_speed_routing.py` | OK |
| `guardrail_inbox_triage.sh` | PASS |
| `test_first_turn_continuity.py` | PASS (updated full-info case with zip) |

**Limitations:** M1 (missing_document clarification) still fails; not Add-Car related. R4 and LC-AC3 had expected handoff updated; LC-AC3 remains FRICTION (handoff at 2, expected 3) — driver correction edge case.

---

## 9. Release / Deployment Judgment

| Area | Status |
|------|--------|
| **Backend changes** | Yes — `triage.py` (handoff, extraction, structured fields) |
| **Backend redeploy** | **Needed** if backend is deployed (Cloud Run) |
| **Frontend changes** | Config only — `configs/simulation_assistant_scenarios.json`, `configs/customer_entry_multi_turn_simulations.json` |
| **Frontend redeploy** | Not required for logic; configs may be bundled |
| **Founder can inspect** | Yes — run demo, Simulation Assistant, Broker Workbench |

---

## 10. Founder Showcase (REQUIRED)

### Example 1: Basic New Car Quote

- **User says:** 想加一台2021 Tesla Model Y 报价
- **System now asks next:** 先把地址邮编发我，我就能帮你算报价。
- **What has been collected:** year, make_model
- **What is still needed:** zip, delivery_date (or primary_driver)
- **Why this is better than before:** Same first ask; but when user gives "90210" only, system now asks for delivery instead of handing off. Flow continues to a meaningful handoff.

### Example 2: User Already Has Insurance (Add-to-Existing)

- **User says:** 想加车，2024 Tesla Model Y
- **System now asks next:** 先把地址邮编发我，我就能帮你算报价。
- **What has been collected:** year, make_model, insurance_status_add_to_existing (inferred from 想加车)
- **What is still needed:** zip, delivery_date
- **Why this is better than before:** Extraction detects add-to-existing; structured fields include it when present. Handoff still requires zip+delivery.

### Example 3: User Needs to Add Another Driver

- **User says:** 2025 Honda CR-V, 92705, 下周提车，还有我老婆也会开
- **System now asks next:** Hand off (full info)
- **What has been collected:** year, make_model, zip, delivery_date, additional_drivers_yes
- **What is still needed:** primary_driver (broker can confirm)
- **Why this is better than before:** additional_drivers detected; case summary richer for broker.

### Example 4: User Wants Better Coverage

- **User says:** 我买了台宝马X5，想问下保费多少钱
- **System now asks next:** 先把年份和地址邮编发我，我就能帮你算报价。
- **What has been collected:** make_model
- **What is still needed:** year, zip, delivery_date
- **Why this is better than before:** Same first ask. When user gives year+zip, system now asks delivery; does not hand off with zip only.

### Example 5: User Asks Short/Fragmented Question

- **User says:** 新车保险多少
- **System now asks next:** 先把年份和车型发我，我就能帮你算。
- **What has been collected:** (none)
- **What is still needed:** year, make_model, zip, delivery_date
- **Why this is better than before:** Same. Flow then continues: vehicle → zip → delivery. 4 turns typical before handoff.

---

## 11. Final Judgment

| Question | Answer |
|----------|--------|
| **Is Add-Car Quote now much stronger than the old 2–3 turn flow?** | **Yes.** Handoff requires zip + (delivery or driver); flow continues when only zip given. |
| **Does it now feel closer to real business intake?** | **Yes.** 4–5 turns when partial; handoff at a meaningful point. |
| **Is it close enough to 80% completion?** | **Yes.** Vehicle+zip+delivery/driver; extraction for insurance_status and additional_drivers. |
| **What still remains weak?** | No explicit "additional drivers?" or coverage_preference ask; optional for later. |
| **Is this now a good enough default flow before making it configurable?** | **Yes.** |
| **What is the single best next move after this sprint?** | Deploy backend; have founder inspect Add-Car in Simulation Assistant and Broker Workbench. Then consider configurability. |

---

## 12. Iteration Log (REQUIRED)

### Loop 1

- **What changed:** Stricter handoff (zip + delivery/driver); extraction for insurance_status, additional_drivers; scenario updates.
- **What got better:** Flow depth; handoff timing; case usefulness.
- **What did not improve:** No additional_drivers/coverage ask; first-turn config unchanged.
- **Whether the loop was worth it:** Yes.
- **Recommended next step:** Deploy; founder inspection.

### Loop 2

- **Not run.** Loop 1 sufficient.

### Loop 3

- **Not run.** No clear low-risk refinement.

---

## 13. 中文宏观总结

**为什么现在先做 Add-Car Quote 80% completion：**  
创始人发现加车报价流程太短（2–3 轮）、太像演示，不足以支撑真实业务。先做强默认流程，再做可配置，顺序正确。

**我们用了什么主要方法和技术：**  
- 提高交办门槛：必须 zip + (delivery 或 driver)，不能只有 zip 就交办  
- 扩展字段提取：insurance_status、additional_drivers  
- 更新多轮场景和 Simulation Assistant 场景的预期轮数  

**这样做的好处是什么：**  
- 流程更接近真实办公室收单  
- 交办时信息更完整，经纪人少追一轮  
- Collected/Still needed 更准确  

**现在已经实现了什么：**  
- 更严格的交办逻辑  
- 4–5 轮典型流程（部分信息时）  
- insurance_status、additional_drivers 的检测与结构化输出  
- 全部 guardrail 和 multi-turn 测试通过  

**还差什么：**  
- 未显式问「还有别人开吗？」  
- 未问 coverage 偏好  
- 可留作后续迭代  

**有没有重大问题：**  
无。M1（missing_document）为既有问题，与 Add-Car 无关。  

**下一步最该做什么：**  
部署后端；创始人用 Simulation Assistant 和 Broker Workbench 验收 Add-Car 流程；再考虑可配置化。

---

## 14. COPY/PASTE FOUNDER BLOCK

```
Add-Car Quote 80% Completion Sprint — Founder Summary

Biggest improvement: Handoff now requires zip + (delivery or driver). 
Flow no longer stops after "90210" — it asks for delivery, then hands off. 
4–5 turns typical when user gives partial info.

Biggest remaining weakness: No explicit "additional drivers?" or coverage ask. 
Optional for later.

Flow now feels near 80% complete: vehicle + zip + delivery/driver; 
richer extraction; meaningful handoff.

Redeploy needed: Backend yes (triage.py). Frontend config-only.

What Andy should inspect next:
1. Simulation Assistant → R4 (Add-car + garaging), SIM3 (Add-car Chinese)
2. Broker Workbench → Add-car case → verify Collected: year, model, zip, delivery
3. Manual: "想加一台X5" → "90210" → system should ask delivery, not hand off
```

---

*End of report*
