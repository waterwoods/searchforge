# Five Core Flows Deep Multi-Turn + Structured Case Report Sprint Report

**Sprint:** Five Core Flows Deep Multi-Turn + Structured Case Report  
**Date:** 2026-03-12  
**Budget:** 30–50 minutes focused work  
**Status:** Complete

---

## 1. Stages completed

| Stage | Status | Notes |
|-------|--------|------|
| Stage 1 — Define 3–4 turn target | ✅ | `docs/DEEP_MULTI_TURN_TARGET.md` |
| Stage 2 — Expand deep multi-turn scenarios | ✅ | MT30–MT38 added (9 new; 38 total) |
| Stage 3 — Deep multi-turn bug harvest | ✅ | 38/38 strong; no later-turn bugs |
| Stage 4 — Review structured report visibility | ✅ | Classified strong (per STRUCTURED_OUTPUT_VISIBILITY) |
| Stage 5 — Define minimum useful structured case report | ✅ | Aligned with BROKER_HANDOFF_CLARITY_GUIDE |
| Stage 6 — Prioritize fixes | ✅ | Human confirmation badge chosen |
| Stage 7 — Improvement loop 1 | ✅ | Human confirmation recommended badge |
| Stage 8 — Optional improvement loop 2 | ⏭️ | Skipped — loop 1 sufficient |
| Stage 9 — AI collected vs human must confirm view | ✅ | Badge + compact note in action card |
| Stage 10 — Chen Kui trial pack prep | ✅ | 5 walkthroughs below |
| Stage 11 — Validation | ✅ | npm build, guardrail PASS, 38/38 multi-turn |
| Stage 12 — Redeploy readiness | ✅ | Frontend-only redeploy |
| Stage 13 — Audit | ✅ | Accept |

---

## 2. 3–4 turn target

**Defined in `docs/DEEP_MULTI_TURN_TARGET.md`:**

| Turn | System should | Avoid |
|------|---------------|-------|
| Turn 1 | Acknowledge; ask 1–2 next things | Generic "provide more context" |
| Turn 2 | Use new info; acknowledge; hand off if enough | Ignore what customer said |
| Turn 3 | Preserve context; acknowledge; ask one more OR hand off | Flow switch; wrong follow-up |
| Turn 4 | Same; hand off when enough; reflect all in structured output | Context loss |

**Context preservation:** `conversation_summary` and `collected_fields` / `still_needed_fields` reflect full conversation. "Already sent" → "好的，收到了". Correction → "好的，明白了".

**Flow stability:** No flow switching; progressive ask; hand off when thresholds met.

---

## 3. Scenario expansion

**Added 9 deeper scenarios (MT30–MT38):**

| ID | Flow | Name | Turns | Expected handoff |
|----|------|------|-------|------------------|
| MT30 | add_car_quote | Add car 4-turn | 4 | 3 |
| MT31 | missing_document | Missing doc 3-turn | 3 | 2 |
| MT32 | payment_failed_cancellation_risk | Notice 3-turn | 3 | 2 |
| MT33 | claim_intake | Claim 3-turn | 3 | 2 |
| MT34 | premium_review | Renewal 3-turn | 3 | 2 |
| MT35 | add_car_quote | Add car 3-turn | 3 | 2 |
| MT36 | missing_document | Missing doc 4-turn | 4 | 2 |
| MT37 | payment_failed_cancellation_risk | Payment 4-turn | 4 | 2 |
| MT38 | claim_intake | Claim 4-turn | 4 | 2 |

**Total:** 38 multi-turn simulations; all 5 core flows covered with 3–4 turn variants.

---

## 4. Bug harvest findings

**All 38 multi-turn simulations:** Strong. No context loss, flow pollution, wrong follow-up, or weak handoff.

**Notable behaviors:**
- MT30 (Add car 4-turn): Turn 2 asks zip; turn 3 handoff when zip provided; turn 4 adds delivery (handoff already at 3).
- MT31 (Missing doc 3-turn): Turn 2 handoff when dec page sent; turn 3 garaging sent — final structured output reflects both.
- MT32 (Notice 3-turn): Correction at T2, sent at T3; other_corrected then other_received.
- MT33–MT38: All hand off correctly; structured output reflects full conversation.

**Other packs:**
- Inbox triage: 49/49 passed
- Simulation Assistant: 15/15 Normal
- Guardrail: PASS

**Conclusion:** No high-value 3–4 turn bugs to fix. System preserves context and produces correct structured output across deeper conversations.

---

## 5. Structured report visibility review

**Classification:** Strong (per STRUCTURED_OUTPUT_VISIBILITY sprint).

**Current visibility:**
- Case focus: Dedicated line at top; inferCaseFocusFromStructuredFields when structured data present
- Your next move: Prominent, operational
- Collected / Still needed: Green/orange chips for 4 flows
- Last update: "Where this case stands"
- Queue cards: Case focus tag first; readiness badges

**Gap addressed this sprint:** No explicit "AI collected vs human must confirm" — added Human confirmation recommended badge.

---

## 6. Improvements made

| Change | File | Purpose |
|--------|------|---------|
| Deep multi-turn target | `docs/DEEP_MULTI_TURN_TARGET.md` | Clear 3–4 turn behavior spec |
| 9 new 3–4 turn scenarios | `configs/customer_entry_multi_turn_simulations.json` | MT30–MT38 |
| Human confirmation badge | `UnifiedIntakePage.tsx` | `needsHumanConfirmation()` + badge when payment risk, customer_says_sent, VIN/driver |
| Demo readiness update | `docs/UNIFIED_INTAKE_DEMO_READINESS.md` | 38 variants; Human confirmation badge |

---

## 7. Trial scenario preparation

See §14 Chen Kui trial walkthroughs below.

---

## 8. Validation summary

| Check | Result |
|-------|--------|
| `npm run build` (ui/) | ✓ |
| `run_inbox_triage_scenarios.py` | 49/49 passed |
| `run_multi_turn_simulations.py` | 38/38 strong |
| `guardrail_inbox_triage.sh` | PASS |

---

## 9. Redeploy readiness

- **Frontend-only redeploy needed:** Yes
- **Backend changes:** None
- **Deploy order:** Frontend (Vercel) only
- **Post-deploy smoke:** Open `/workbench/unified-intake`, Load founder demo queue, verify Case focus, Human confirmation badge on payment/missing-doc cases, queue case focus tags

---

## 10. Recommended next step

1. Redeploy frontend to Vercel
2. Chen Kui runs 3–5 trial walkthroughs (§14)
3. Collect feedback on 3–4 turn quality and Human confirmation visibility
4. Optional: Add more 4-turn edge scenarios if new patterns surface

---

## 11. 中文或中英混合宏观总结

**五条主线这次 3–4 轮更稳了没有？**  
是的。新增 9 个 3–4 轮场景（MT30–MT38），覆盖 5 条主线；38/38 全部 Strong。加车 4 轮（模糊→年份车型→邮编→提车）正确在第三轮 handoff；缺材料 3 轮（dec page 发了→garaging 发了）最终 structured output 正确反映两项都发了。

**结构化结果这次看得更清楚了没有？**  
是的。Case focus、Collected/Still needed 已有；本次新增 "Human confirmation recommended" 徽章，当 AI 从对话推断出客户说已发、或付款风险、或 VIN/驾驶人时，broker 一眼看出需要人工确认。

**AI 收集了什么、人还要确认什么，清楚了没有？**  
清楚了。Human confirmation recommended 出现在：付款/取消风险、customer_says_sent_*、VIN、primary_driver。Broker 知道哪些是 AI 推断、哪些需要人工复核。

**抓出了哪些 bug？**  
没有。38 个多轮场景全部通过，无 context loss、flow pollution、wrong follow-up。

**这次做完为什么更接近真实可用？**  
1）3–4 轮对话更稳，覆盖更自然的多轮场景；2）broker 能明确看到 AI 收集 vs 需要人工确认；3）结构化输出更完整。

---

## 12. Practical multi-turn + structured-result checklist

| Later turns should | Final case report should | Human confirmation should |
|--------------------|--------------------------|---------------------------|
| Preserve context from T1–T2 | Show Case focus at top | Show badge when payment risk |
| Acknowledge before next ask or handoff | Show Your next move | Show badge when customer_says_sent |
| Not flow switch | Show Collected (green chips) | Show badge when VIN/driver |
| Reflect all in structured output | Show Still needed (orange chips) | Compact note: "AI collected; broker verify" |
| Hand off when enough | Show full conversation below | — |

---

## 13. Bug + report visibility summary

| Area | Status |
|------|--------|
| Strongest deep-turn scenarios | MT30 (add-car 4-turn), MT31 (missing doc 3-turn), MT32 (notice 3-turn), MT33–MT38 |
| Suspicious | None |
| Report visibility improvements | Human confirmation recommended badge |
| Remaining issues | None blocking |

---

## 14. Chen Kui trial walkthroughs

### Walkthrough 1: Cancellation risk (urgency)

**What to run:** Load founder demo queue  
**What to say/click:** Click "Load founder demo queue" → cancellation risk case opens first  
**What to watch for:** Case focus "Payment / cancellation risk"; "Human confirmation recommended" badge; "Same-day action"; "Your next move"  
**What this proves:** 紧急 case 能一眼看出；broker 知道今天要处理；AI 推断需人工确认

---

### Walkthrough 2: Missing document (customer says sent)

**What to run:** Reopen "Missing document follow-up" from Recent cases  
**What to say/click:** 点击 Reopen case  
**What to watch for:** "Human confirmation recommended" (customer_says_sent); Collected/Still needed chips; "Resume here"  
**What this proves:** 跟进 continuity；broker 知道客户说已发；需人工核对

---

### Walkthrough 3: Add car 4-turn (multi-turn)

**What to run:** Customer Entry，paste: "新车保险多少" → "2025 Honda CR-V" → "90210" → "下周拿车"  
**What to say/click:** 客户入口输入四句，依次发送  
**What to watch for:** Turn 2 问邮编；Turn 3 handoff 收到 ZIP；Turn 4 补充提车；Case focus "Add car quote"；Collected: Year, Model, ZIP, Delivery  
**What this proves:** 多轮 intake 能收集关键字段；3–4 轮稳定

---

### Walkthrough 4: Claim intake (first response)

**What to run:** Paste "刚出事故了，要收集什么？" → "拍了照片，对方保险也记了，发你微信"  
**What to say/click:** 两轮对话  
**What to watch for:** Case focus "Claim intake"；Collected: Accident reported, Photos, Other driver info；handoff "好的，收到了"  
**What this proves:** 事故 first response 流程正常

---

### Walkthrough 5: Simulation Assistant (QA)

**What to run:** 客户入口 → Simulation Assistant → 选 "Notice / Cancellation" 或 "Add car (Chinese)"  
**What to say/click:** Run simulation → 看 Evaluation: Normal  
**What to watch for:** 两轮后 handoff；无 generic "please provide more context"  
**What this proves:** 系统对 scripted 场景稳定，可用于内部 QA

---

*End of report*
