# Real Customer Pack Mainline Sprint Report

**Sprint:** Real Customer Pack Mainline  
**Date:** 2026-03-13  
**Status:** Complete

---

## 1. Realism blueprint summary

### Why it felt demo-like

- **Broker-forwarded voice:** "客户问：...", "客户说..." — broker dictation, not raw customer
- **Too clean / complete:** Full sentences, ideal field order; real users say "宝马x5，多少钱" or "我新车，下周拿，保险大概？"
- **Not enough messiness:** 15 scenarios orderly; adversarial pack (27 messy) not in Simulation Assistant
- **Mixed intent missing:** Single-intent per scenario; real: "加车，顺便 garaging proof 是什么？"
- **Few corrections / emotion:** No "都发过了怎么还要", "还不行吗"

### What real customer style means

- Short fragments, mixed Chinese/English, incomplete info, late corrections
- "Already sent" confusion, emotional/impatient wording
- Screenshot/notice references without full context
- Mixed intent in one message, common shorthand ("发你了", "弄好了发你")

### What the first realism pack contains

- Cancellation/payment confusion + correction
- Missing doc frustrated ("都发过了怎么还要")
- Add-car ultra-short ("宝马x5，多少钱")
- Add-car + garaging (mixed intent)
- Claim panic ("刚撞了，对方跑了")
- Renewal short ("续保涨了好多 有办法吗")
- Payment + dec page (mixed intent)
- Doc vague ("上次那个材料我又发了")

---

## 2. Current scenario realism audit

### Strongest current scenarios

- **SIM2:** UW follow-up, "他又发了一次", "garaging proof 是什么意思" — good clarification
- **SIM10:** "就是上次那个材料，我又发了" — vague, realistic
- **SIM14:** "发你了" — minimal, realistic
- **customer_entry_multi_turn:** MT22, MT29, MT33, MT34 — messier wording, but not in Simulation Assistant

### Weakest current scenarios

- **SIM1, SIM3, SIM5, SIM6:** "客户问：...", "客户说..." — broker-forwarded
- **SIM3:** "我买了台宝马X5，想问下保费多少钱" — too complete; real: "宝马x5，多少钱"

### Biggest realism gaps

| Gap | Before | After |
|-----|--------|-------|
| Messy fragments in main pack | None | R1–R8 |
| Mixed intent in Simulation Assistant | None | R4, R7 |
| Frustrated "already sent" | SIM10 only | R2, R8 |
| Ultra-short add-car | None | R3 |
| Panic claim wording | SIM5 tidy | R5 |

---

## 3. Real Customer Pack design

### Scenarios chosen

| ID | Title | Flow | Source |
|----|-------|------|--------|
| R1 | Notice + cancel confusion (real) | notice_cancellation | Adversarial N1 |
| R2 | Doc frustrated — 都发过了怎么还要 | missing_document | Adversarial D1+D2 |
| R3 | Add-car ultra-short (real) | add_car | Adversarial A1 |
| R4 | Add-car + garaging (mixed intent) | add_car | Mixed-intent MI-AC1 |
| R5 | Claim panic — 刚撞了对方跑了 | claim | Adversarial C1 |
| R6 | Renewal short — 续保涨了好多 | renewal_premium | Adversarial R3 |
| R7 | Payment + dec page (mixed intent) | notice_cancellation | Mixed-intent MI-N2 |
| R8 | Doc vague — 上次那个材料我又发了 | missing_document | Adversarial D2 |

### Organization

- **Section:** `real_customer` — new group in Simulation Assistant
- **Label:** "Real customer style (messy, short, mixed)"
- **Placement:** After Recommended trial, before Multi-turn proof
- **All 2-turn:** Handoff at turn 2; compact, high-value

---

## 4. Implementation changes made

### Files changed

| File | Change |
|------|--------|
| `configs/simulation_assistant_scenarios.json` | Added 8 scenarios R1–R8, `real_customer_order` |
| `ui/src/config/simulation_assistant_scenarios.json` | Same |
| `ui/src/components/simulation/SimulationAssistant.tsx` | Added `real_customer` section type, `groupScenarios` group, intro text |
| `scripts/guardrail_inbox_triage.sh` | Echo text: "15 trial + 8 real-customer" |
| `docs/REAL_CUSTOMER_PACK_BLUEPRINT.md` | New — realism blueprint |

### What was added

- 8 multi-turn scenarios with realistic customer voice
- Direct customer phrasing (no "客户问/客户说")
- Fragments, mixed language, frustrated tone where appropriate
- Mixed-intent examples (R4, R7)

### What was not changed

- Recommended trial scenarios (SIM1–SIM6) — kept for trial clarity
- Edge cases, multi-turn proof — unchanged
- No new product features, no CRM/auth/analytics

---

## 5. Test / evaluation results

### Script results

| Check | Result |
|-------|--------|
| `run_simulation_assistant_scenarios.py` | 23/23 PASS (15 + 8) |
| `run_inbox_triage_scenarios.py` | 49/49 passed |
| `run_multi_turn_simulations.py` | 38/38 strong |
| `audit_state_field_accuracy.py` | 7/7 passed |
| `guardrail_inbox_triage.sh` | PASS |
| `unified_intake_smoke_check.sh` | PASS |
| `cd ui && npm run build` | ✓ built |

### Qualitative realism observations

- **R1:** "这个英文 notice 是不是要停了 我没看懂" → sounds like real client, not textbook
- **R2:** "都发过了怎么还要 declaration page" → frustrated, realistic
- **R3:** "宝马x5，多少钱" → ultra-short, no verb
- **R4:** "我想加一辆车，然后这个 garaging proof 又是什么？" → mixed intent, natural
- **R5:** "刚撞了，对方跑了，我现在先干嘛" → panic, hit-and-run
- **R6:** "续保涨了好多 有办法吗" → short, no bill
- **R7:** "payment failed 怎么办，另外dec page我上周发过了" → two things at once
- **R8:** "上次说那个材料我又发了 还不行吗" → vague prior convo, frustrated

All scenarios remain understandable. Realism improved without making the product confusing.

---

## 6. Refinement loop

**Needed?** No. First pass was strong; all 8 scenarios pass; wording is realistic.

**Skipped refinements:**

- Rewriting recommended trial to remove "客户问/客户说" — out of scope; trial clarity preserved
- Adding 3-turn real scenarios — 2-turn sufficient for compact pack
- Further messiness — risk of unreadable chaos; current level is appropriate

---

## 7. Final evaluation

### Biggest realism gain

**Messy, short, mixed-language customer voice is now visible in Simulation Assistant.** Chen Kui and small-client prospects can run R1–R8 and think: "Yes, these are the kinds of messages we really get."

### Biggest remaining weakness

**Recommended trial (SIM1–SIM6) still uses broker-forwarded framing** ("客户问：...", "客户说..."). That is intentional for trial clarity. A future low-cost improvement: rewrite top 3 trial turns to direct customer voice while keeping the same flow structure.

### Founder-level verdict

**Good first realism pack.** The Simulation Assistant now feels more like real customers. The pack is compact (8 scenarios), maintainable, and high-value for demo and regression. A small-client prospect is more likely to recognize their workflow.

---

## 8. Redeploy readiness

| Component | Redeploy? |
|-----------|-----------|
| Frontend | **Yes** — SimulationAssistant shows new "Real customer style" section |
| Backend | No — no API changes |
| Configs | No — configs are bundled with frontend build |

**Action:** Redeploy frontend (Vercel) to expose Real Customer Pack in production.

---

## 9. 中文宏观总结

### 现在为什么更像真实客户了

- 新增 8 个「真实客户风格」场景，用碎片句、混用中英、情绪化语气
- 不再用「客户问：…」「客户说…」，而是客户原话
- 包含「都发过了怎么还要」「上次那个材料我又发了」「刚撞了对方跑了」等真实表达

### 哪几类场景最像现实

1. **付款/通知混淆** — R1「这个英文 notice 是不是要停了 我没看懂」
2. **缺材料 + 已发过** — R2, R8「都发过了怎么还要」「上次那个材料我又发了」
3. **加车超短** — R3「宝马x5，多少钱」
4. **混合意图** — R4, R7「加车 + garaging proof」「payment failed + dec page」

### 这个 pack 会不会更能打动陈奎和潜在小客户

会。小客户看到 R1–R8 会更容易认同：「这就是我们客户会发的消息。」Demo 价值提升。

### 还剩下最大的 realism 缺点是什么

推荐试用场景（SIM1–SIM6）仍用经纪人口吻转述。为保持试用清晰度暂未改。下一步可考虑把前 3 个试用场景改成直接客户原话。

### 下一步最该做什么

1. 部署前端，让 Real Customer Pack 上线
2. 陈奎试用时优先跑 R1, R2, R3，观察反馈
3. 若反馈好，再考虑把 SIM1–SIM3 改成直接客户原话

---

## 10. COPY/PASTE REAL CUSTOMER PACK BLOCK

```
Real Customer Pack — Simulation Assistant
=========================================

What it means
  Messy, short, mixed-language customer scenarios — like real small-client traffic.
  No "客户问/客户说" broker dictation. Direct customer voice.

Strongest realistic scenario types
  • Notice + cancel confusion (R1): "这个英文 notice 是不是要停了 我没看懂"
  • Doc frustrated (R2, R8): "都发过了怎么还要", "上次那个材料我又发了"
  • Add-car ultra-short (R3): "宝马x5，多少钱"
  • Mixed intent (R4, R7): add-car + garaging, payment + dec page
  • Claim panic (R5): "刚撞了，对方跑了，我现在先干嘛"
  • Renewal short (R6): "续保涨了好多 有办法吗"

Biggest demo-value gain
  Chen Kui and small-client prospects can run R1–R8 and think:
  "Yes, these are the kinds of customer messages we really get."

Biggest remaining realism weakness
  Recommended trial (SIM1–SIM6) still uses broker-forwarded framing.
  Intentional for trial clarity. Future: rewrite top 3 to direct customer voice.

Redeploy needed?
  Frontend only (Vercel). Backend unchanged.

What to do next
  1. Deploy frontend
  2. Chen Kui trial: run R1, R2, R3 first
  3. If feedback good: consider rewriting SIM1–SIM3 to direct customer voice
```

---

*See also: `docs/REAL_CUSTOMER_PACK_BLUEPRINT.md`, `docs/SIMULATION_ASSISTANT_SPEED_REALISM_AUDIT_REPORT.md`, `docs/CHEN_KUI_TRIAL_PACK.md`*
