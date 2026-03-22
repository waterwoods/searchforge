# Add-Car Commercial Flow Hardening Report

## 1. Sprint theme

- **What was chosen:** Add-Car Commercial Flow Hardening — strengthen the full customer-to-broker add-car module as one coherent commercial flow.
- **Why now:** Add-Car is the flagship scenario. It already has quote-ready, identity/contact-lite, attachment-ready-lite, and workbench handoff. But it still felt like parts connected together. Before broader commercialization, the team should harden Add-Car as a full module.

---

## 2. Document set created

| Doc | Path |
|-----|------|
| 1. Blueprint | `01_ADD_CAR_COMMERCIAL_FLOW_HARDENING_BLUEPRINT.md` |
| 2. End-to-End Flow Spec | `02_ADD_CAR_END_TO_END_FLOW_SPEC.md` |
| 3. Readiness / Completeness Spec | `03_ADD_CAR_READINESS_COMPLETENESS_SPEC.md` |
| 4. Broker Workbench Usability Spec | `04_ADD_CAR_BROKER_WORKBENCH_USABILITY_SPEC.md` |
| 5. Weak-Point / Fix Queue Spec | `05_ADD_CAR_WEAK_POINT_FIX_QUEUE_SPEC.md` |
| 6. Execution Outline | `06_EXECUTION_OUTLINE.md` |
| 7. Acceptance / Commercial Hardening Criteria | `07_ACCEPTANCE_COMMERCIAL_HARDENING_CRITERIA.md` |
| 8. Founder Inspection Notes | `08_FOUNDER_INSPECTION_NOTES.md` |
| 0. Baseline Audit | `00_BASELINE_AUDIT.md` |

---

## 3. Baseline audit

### Strongest current parts

- Quote-ready visibility, collected/still-needed, broker handoff, identity, case persistence
- Side-question handling (garaging, coverage) answered before handoff
- Correction handling; handoff timing 13/13; multi-turn 51/51; broker stress 12/12

### Biggest module-coherence weakness

- Add-car + "发你微信了" (materials sent) — broker_next_step was generic; no "Verify materials received"

### Biggest broker-usability gap

- When customer says materials sent in add-car context, broker didn't get tailored next step

### Biggest customer-trust gap

- Driver ask blocked handoff when customer said "registration 发你微信了" — felt like system ignored their message

### Biggest commercial-feel gap

- Add-car + already_sent combinations not coherent; broker rework risk

---

## 4. 10–20 point breakdown

1. **Why Add-Car is flagship** — Highest-frequency, highest-value broker scenario
2. **Why it felt stitched** — Quote-ready, contact, attachment, correction were separate; add-car + materials sent not tailored
3. **Believable intake** — Clear first-step guidance; no redundant ask; side questions answered
4. **Believable quote-ready** — vehicle + zip + (delivery or driver); contact optional but visible
5. **Believable broker handoff** — Concrete vehicle; one next step; contact hint when missing
6. **Broker 3–5 second scan** — Quote-ready, contact, attachment, correction above fold
7. **Contact + quote-ready** — Case can be quote_ready with still_needed: name, phone; broker_next_step mentions
8. **Attachment + quote-ready** — Separate signal; optional; "Materials received" when present
9. **Correction + module** — Same case; merged text; correction badge; latest wins
10. **Side-question + module** — Garaging, coverage answered before handoff; no driver ask blocking
11. **Highest-value weak point** — Add-car + "发你微信了" → broker_next_step "Verify materials received"
12. **Reduces broker rework** — Tailored broker_next_step; no re-ask for materials customer said sent
13. **Improves customer trust** — Warmer handoff reply when materials sent; no driver ask after "发你微信了"
14. **Improves product feel** — One coherent flow; combinations handled
15. **Deferred** — OCR, carrier API, full CRM, mandatory attachment
16. **Simulations needed** — BS11, BS12, MT51, HT13
17. **Founder manual test** — 4–6 Vercel flows; add-car + materials sent
18. **V2** — broker_next_step when attachment uploaded (triage doesn't have case_attachments)

---

## 5. Iteration loop 1

**What was fixed:** Add-car + "already sent" (materials) — when customer says "发你微信了" / "registration 发你微信了" in add-car context.

**Why:** Highest-value weak point. Broker got generic "Run quote" when customer said materials sent. Should say "Verify materials received via WeChat; run quote when confirmed."

**Changes:**
- broker_next_step: when add-car + follow_up_type=already_sent, use "Verify materials received via WeChat; run quote for {vehicle} when confirmed."
- collected_fields: add "customer_says_sent_materials"
- Handoff reply: warmer "您说材料发过了，办公室会核对后尽快出价，有结果会联系您。"
- _get_next_ask_for_add_car: when materials_sent in last message, skip driver ask → hand off
- BS11 simulation added

**What now feels more commercial:** Broker knows to verify materials when customer says sent; customer gets reassurance; no driver ask blocking handoff.

**What did not improve:** Attachment upload (case_attachments) — triage doesn't receive it; broker_next_step at display time would need API/UI change.

**Whether it was worth it:** Yes — major coherence improvement.

---

## 6. Iteration loop 2

**What was fixed:** Combination scenarios — MT51 (add-car + materials sent in one turn), HT13 (add-car + materials sent T3).

**Why:** Validate add-car + already_sent across turn structures; regression coverage.

**What improved vs loop 1:** 51/51 multi-turn; 13/13 handoff timing; MT51 and HT13 pass.

**What still remained weak:** broker_next_step when attachment uploaded (not in triage scope).

**Whether it was worth it:** Yes — simulation coverage for combinations.

---

## 7. Iteration loop 3

**What was hardened:** BS12 — Add-car correction + materials sent (3-turn combo).

**Why:** Realistic combination: T1 wrong vehicle, T2 correction, T3 zip+delivery+materials sent.

**What improved vs loop 2:** 12/12 broker trial stress; correction + materials_sent combo validated.

**What still remained weak:** HT12 broker_next_step shows "Bmw" not "BMW X3" after correction (deferred).

**Whether it was worth it:** Yes — trial-ready combination coverage.

---

## 8. Optional loop 4

**Whether used:** No.

**Why stopping is correct:** Loop 1–3 addressed the highest-value weak points. Remaining items (broker_next_step when attachment uploaded, X3 correction preference) require API/UI or extraction changes; acceptable for trial.

---

## 9. Validation summary

| Check | Result |
|-------|--------|
| guardrail_inbox_triage.sh | PASS |
| run_multi_turn_simulations.py | 51/51 Strong |
| run_broker_trial_stress_simulations.py | 12/12 passed |
| run_handoff_timing_simulations.py | 13/13 passed |
| run_complex_adversarial_simulation.py (mixed_intent) | 14/14 Strong |

**Limitations:** broker_next_step when attachment uploaded — triage doesn't have case_attachments. HT12 correction shows "Bmw" not "BMW X3" — deferred.

---

## 10. Deployment / release judgment

| Component | Status |
|-----------|--------|
| Backend | Changed — triage.py |
| Frontend | No changes |
| Redeploy needed | Backend yes (Cloud Run); frontend no |

**Founder can inspect:** Yes — run guardrail; test add-car + materials sent on Vercel.

---

## 11. Founder manual inspection list

| # | Input | Expected |
|---|-------|----------|
| 1 | 加车 2024 Tesla Model Y → 90210 下周提车 | Handoff T2; broker_next_step mentions vehicle |
| 2 | 加车 2024 X5 → 90210 下周提车 对了 garaging proof 是什么 | Answer garaging; handoff T2 |
| 3 | 加车 2024 Tesla Model Y 90210 → 下周提车 registration 发你微信了 | Handoff T2; broker_next_step "Verify materials received" |
| 4 | 加车 2021 Honda → 不是这个 是 2024 Tesla → 90210 下周提车 材料发你微信了 | Handoff T3; collected shows Tesla; broker_next_step verify |
| 5 | 加车 2024 X5 90210 下周提车 我开 | Handoff T1; full info |
| 6 | 加车 2024 Tesla Model Y 90210 下周提车 registration 发你微信了 (one turn) | Handoff T1; broker_next_step verify |

---

## 12. Final judgment

| Aspect | Result |
|--------|--------|
| **Biggest gain** | Add-car + materials sent: broker_next_step "Verify materials received"; warmer handoff reply; materials_sent skips driver ask |
| **Biggest remaining weakness** | broker_next_step when attachment uploaded (triage doesn't have case_attachments); HT12 X3 correction |
| **Flagship-commercial enough?** | Yes — add-car feels more coherent; combinations handled; broker gets actionable next step |
| **Best next step** | Deploy backend; founder manual test; V2: broker_next_step augmentation when attachment added |

---

## 13. 中文宏观总结

- **为什么现在做这一轮：** 加车是旗舰场景，已有报价、联系、附件、工作台，但「发你微信了」组合未处理，经纪人收到通用下一步。
- **主要修了什么：** 1) add-car + 发你微信了 → broker_next_step「Verify materials received」；2) 更暖的 handoff 回复；3) materials_sent 时跳过 driver 追问，直接 hand off；4) BS11、BS12、MT51、HT13 模拟。
- **最大提升是什么：** 客户说材料发过了，经纪人收到「核实材料」的下一步；不再追问驾驶人；整体流程更连贯。
- **还差什么：** 附件上传后 broker_next_step 增强（需 API/UI）；HT12 修正后显示 X3 优先（V2）。
- **下一步最该做什么：** 部署后端；创始人 Vercel 测试；V2 考虑附件上传时 broker_next_step 增强。

---

## 14. COPY/PASTE FOUNDER BLOCK

```
Add-Car Commercial Flow Hardening — Founder Summary

Biggest improvement: When customer says "发你微信了" or "registration 发你微信了" in add-car context, broker now gets "Verify materials received via WeChat; run quote for {vehicle} when confirmed." Warmer handoff reply. No driver ask blocking handoff when customer says materials sent.

Biggest remaining weakness: broker_next_step when attachment uploaded (triage doesn't have case_attachments). HT12 correction shows "Bmw" not "BMW X3" — deferred.

Redeploy needed: Backend yes (triage.py). Frontend no.

Test first on Vercel: (1) 加车 2024 Tesla Model Y 90210 → 下周提车 registration 发你微信了 — verify broker_next_step says "Verify materials received". (2) 加车 2021 Honda → 不是这个 是 2024 Tesla → 90210 下周提车 材料发你微信了 — verify handoff T3, collected shows Tesla, broker_next_step verify.
```

---

## 15. REQUIRED SHORT OVERVIEW

### 为什么做这件事

加车是旗舰场景，已有报价、联系、附件、工作台，但客户说「发你微信了」时经纪人收到通用下一步，流程不够连贯。

### 主要用了什么方法/技术

- 控制文档：9 份 blueprint + spec + 验收标准
- 三轮迭代：add-car + already_sent broker_next_step → 组合模拟 → correction + materials_sent
- materials_sent 跳过 driver 追问；更暖 handoff 回复；collected_fields customer_says_sent_materials

### 这轮最大的提升

客户说材料发过了，经纪人收到「核实材料」的下一步；不再追问驾驶人；BS11、BS12、MT51、HT13 通过。

### 现在还差什么

附件上传后 broker_next_step 增强（需 API/UI）；HT12 修正后 X3 优先显示（V2）。
