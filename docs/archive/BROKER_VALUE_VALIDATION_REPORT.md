# Broker Value Validation Report

**Phase**: Broker Value Validation  
**Date**: 2026-03-06  
**Goal**: Prove real business value for California auto insurance brokers (e.g., 陈魁)

---

## 1. Offline 5-question readiness

| Item | Status |
|------|--------|
| **All 5 questions supported** | ✅ Yes |
| **demo_fallback.json** | Updated with 5 items (was 3) |
| **snapshot_demo_answers.py** | Docstring fixed (3→5); script already had 5 questions |
| **DEFAULT_FALLBACK_ITEMS** | All 5 in DemoPage.tsx; used when JSON missing or item not found |

### Files touched

| File | Change |
|------|--------|
| `ui/src/assets/demo_fallback.json` | Added Q4 (省钱/折扣) and Q5 (理赔流程); improved Q2 (恢复费约 $14), Q3 (direct license lookup URL) |
| `scripts/snapshot_demo_answers.py` | Docstring: "3 broker questions" → "5 broker questions" |
| `ui/src/pages/DemoPage.tsx` | Error message: "3 个推荐问题" → "5 个推荐问题"; fallback bullets/steps for suspended (add $14), license (add Check a License URL); DEFAULT_FALLBACK Q2/Q3 improved |

### Weak fallback answers (addressed)

| Question | Weakness | Fix |
|----------|----------|-----|
| Q2 注册恢复 | No fee amount | Added "恢复费约 $14" |
| Q3 合规查询 | Generic insurance.ca.gov homepage | Added direct license lookup URL and "Check a License" hint |
| Q4 省钱/折扣 | Generic DMV/insurance links | Kept; snapshot with live backend will get better sources |
| Q5 理赔流程 | Generic links | Kept; structure is broker-appropriate |

**Note**: If snapshot runs with LLM generation off, answers may be empty. DemoPage falls back to `DEFAULT_FALLBACK_ITEMS` when `item.answer` is empty. Current `demo_fallback.json` has broker-appropriate answers for all 5 questions.

**To refresh with live backend**: `python3 scripts/snapshot_demo_answers.py` (backend on 8001). If answers are empty, merge with DEFAULT_FALLBACK_ITEMS or keep current JSON.

---

## 2. Broker value validation set

Five realistic broker scenarios with expected outputs and current usefulness.

### Scenario 1: Customer asks minimum insurance needed

| Field | Value |
|-------|-------|
| **Broker scenario** | New car buyer; needs to know what to buy to register |
| **What broker wants** | Quick answer: CA minimums (15/30/5), plus practical advice for new car |
| **Expected useful output** | 简短结论 + 官方链接 + 下一步（让客户提供信息，给 2–3 套方案） |
| **Current product helps?** | ✅ Yes. Answer has 15/30/5, collision/comprehensive suggestion, broker steps |
| **Falls short** | No direct DMV minimum-requirements URL in fallback; live retrieval may surface it |

### Scenario 2: Registration suspended

| Field | Value |
|-------|-------|
| **Broker scenario** | Customer says "我的车注册被暂停了" |
| **What broker wants** | Steps to restore; fee amount; materials needed |
| **Expected useful output** | 简短结论 + 恢复费 + DMV 在线提交链接 + 步骤 |
| **Current product helps?** | ✅ Yes. Now includes "恢复费约 $14"; DMV suspended-registration URL in sources |
| **Falls short** | Fee may vary; DMV page has full details; broker can copy and share |

### Scenario 3: Compliance / license lookup

| Field | Value |
|-------|-------|
| **Broker scenario** | Customer asks "怎么查你们公司/经纪人是不是合规？" |
| **What broker wants** | Official source to verify license; direct URL |
| **Expected useful output** | insurance.ca.gov Check a License + direct URL + steps |
| **Current product helps?** | ✅ Yes. Direct license lookup URL; "Check a License" hint |
| **Falls short** | Broker must still navigate CDI site; search tips not in answer |

### Scenario 4: Customer wants to save money / reduce premium

| Field | Value |
|-------|-------|
| **Broker scenario** | Renewal or new quote; customer asks about discounts |
| **What broker wants** | Factors affecting premium; common discounts; broker action steps |
| **Expected useful output** | 因素 + 折扣列表 + 建议（收集信息、推荐折扣、多家比价） |
| **Current product helps?** | ✅ Yes. Bullets cover factors and discounts; steps are broker-oriented |
| **Falls short** | Generic; no insurer-specific discount URLs; broker still does manual lookup for carrier-specific programs |

### Scenario 5: Customer asks what to do after accident

| Field | Value |
|-------|-------|
| **Broker scenario** | Post-accident; customer panicked |
| **What broker wants** | Clear sequence: safety → report → contact insurer → materials |
| **Expected useful output** | 流程（确保安全 → 报警 → 报案 → 材料） + 建议保留的信息 |
| **Current product helps?** | ✅ Yes. Flow is clear; steps include 安抚客户、指导报案、准备材料 |
| **Falls short** | No "24小时内报案" explicit guidance; no SR-22 mention for high-risk cases |

---

## 3. Real usefulness assessment

| Scenario | Speed | Clarity | Shareability | Time-saving | Weak points |
|----------|-------|---------|--------------|-------------|-------------|
| **1. Minimum insurance** | Fast (1 click) | Clear 15/30/5 | ✅ 可直接转发 | Reduces lookup | No DMV minimum URL in fallback |
| **2. Registration suspended** | Fast | Clear + $14 fee | ✅ | Strong | Fee may vary by case |
| **3. Compliance lookup** | Fast | Clear + direct URL | ✅ | Strong | Broker must still navigate CDI site |
| **4. Savings/discounts** | Fast | Clear factors + discounts | ✅ | Moderate | Generic; carrier-specific programs not covered |
| **5. Claims process** | Fast | Clear flow | ✅ | Strong | No "report within 24h" explicit |

### Honest assessment

- **Strong**: Q1, Q2, Q3 — broker gets usable answer quickly; copy-to-client works; reduces manual lookup.
- **Moderate**: Q4 — useful for conversation starter; broker still does carrier-specific lookup.
- **Strong**: Q5 — flow is clear; broker can share; minor gap on timing guidance.

**Overall**: Product helps in 4/5 scenarios with high value; Q4 is useful but not complete. For day-to-day work, the main gap is **carrier-specific** information (discounts, claims contacts), which is outside current RAG scope.

---

## 4. Smallest value-improving changes

| File | Change | Why it improves broker usefulness |
|------|--------|----------------------------------|
| `ui/src/assets/demo_fallback.json` | Q2: add "恢复费约 $14" | Broker can tell customer fee without looking up |
| `ui/src/assets/demo_fallback.json` | Q3: direct license URL + "Check a License" | Broker goes straight to lookup, not homepage |
| `ui/src/pages/DemoPage.tsx` | fallbackSuspended: add $14 | Same for heuristic extraction when answer is thin |
| `ui/src/pages/DemoPage.tsx` | fallbackLicense: add Check a License URL + steps | Broker knows exact path; fewer clicks |
| `ui/src/pages/DemoPage.tsx` | DEFAULT_FALLBACK_ITEMS Q2, Q3 | Ensures offline path has improved answers |
| `ui/src/pages/DemoPage.tsx` | Error message: 3 → 5 个推荐问题 | Accurate when offline |
| `scripts/snapshot_demo_answers.py` | Docstring 3 → 5 | Accurate documentation |

**No large redesigns.** Only small, practical improvements.

---

## 5. Broker value measurement pack

### 5.1 Broker value test sheet

**Path**: `docs/broker_value_test_sheet.md`

Use during value-validation meeting. Andy runs through 5 scenarios; broker rates each. Includes copy-to-client test.

### 5.2 Feedback form / question list

**Path**: `docs/broker_value_feedback_form.md`

Short feedback questions: saves time? usable answer? would use again? what is missing? top questions not covered? optional pricing sensitivity.

### 5.3 Simple judgment criteria

| Criterion | How to judge |
|-----------|--------------|
| **Saves time?** | "Before: how long to answer? After: how long with tool?" |
| **Usable answer?** | "Could you copy and send to client with minimal edit?" |
| **Would use again?** | "Would you use this in real work?" |
| **What is missing?** | Open-ended; note top 2–3 gaps |

### 5.4 Meeting recommendation for 陈魁

**Format**: 30–45 min value-validation session (not sales pitch).

1. **Intro (2 min)**: "We want to see if this actually helps your work. No payment today — just your honest feedback."
2. **Demo (15 min)**: Show 5 recommended questions; click each; show 复制给客户; let broker try copy/paste to WeChat.
3. **Broker tries (10 min)**: Broker asks 2–3 real client questions (or types them); observe if answer is useful.
4. **Feedback (10 min)**: Use `broker_value_feedback_form.md`; ask saves time? usable? would use again? what's missing?
5. **Close (2 min)**: "We'll improve based on your feedback. If it proves useful, we can talk about a pilot."

**Goal**: Prove business value first; no payment discussion until value is confirmed.

---

## 6. Repeatability note

### Reusable parts

| Part | Reusable? | Notes |
|------|-----------|-------|
| **Validation method** | ✅ | Test sheet, feedback form, meeting structure |
| **Answer structure** | ✅ | 简短结论 / 官方依据 / 下一步建议 / 可直接转发 |
| **Copy-to-client format** | ✅ | demoCopy.ts; region-agnostic |
| **Snapshot script pattern** | ✅ | POST questions → save JSON; swap questions per region |
| **Scenario tags** | ✅ | Pattern: newcar, suspended, license, savings, claims — map to local equivalents |

### California-specific parts

| Part | California-specific? | Notes |
|------|----------------------|-------|
| **15/30/5 minimums** | ✅ | CA liability limits |
| **DMV, insurance.ca.gov** | ✅ | CA agencies |
| **$14 reinstatement fee** | ✅ | CA DMV |
| **Check a License URL** | ✅ | insurance.ca.gov path |
| **Question wording (Chinese)** | Partial | Same scenarios, different language/regulation |

### Future template candidates

| Template | Purpose |
|----------|---------|
| `configs/regions/ca_auto_insurance.json` | Questions, fallbacks, scenario tags, URLs |
| `docs/broker_value_test_sheet_TEMPLATE.md` | Replace scenarios per region |
| `docs/broker_value_feedback_form_TEMPLATE.md` | Same questions; translate as needed |

---

## 7. Work split

| Who | Responsibility |
|-----|----------------|
| **Cursor** | Offline pack refresh, validation set, report, measurement pack, small value improvements |
| **OpenClaw** | Run `snapshot_demo_answers.py` when backend live; ingest/refresh if corpus changes |
| **Andy** | Run value-validation meeting with 陈魁; use test sheet + feedback form; decide next steps |

---

## 8. Next 12 actions (ordered by priority)

1. **Run value-validation meeting** — Use test sheet + feedback form with 陈魁
2. **Run snapshot** — `python3 scripts/snapshot_demo_answers.py` when backend on 8001 (refreshes Q1–Q5 with live sources)
3. **Capture feedback** — Document: saves time? usable? would use again? what's missing?
4. **Address top 1–2 gaps** — From feedback; smallest changes only
5. **Re-run validation** — If broker agrees, second session with improvements
6. **Decide pilot** — If value proven, discuss pilot terms (manual payment)
7. **Refresh offline pack** — After any answer/corpus change
8. **Add 1–2 broker questions** — If broker asks new question types
9. **Deploy for pilot** — When broker ready; `deploy_rag_demo.sh` or ngrok
10. **Track usage** — Log questions asked, copy usage (manual at first)
11. **Extract region config** — When expanding to China/Europe; follow FUTURE_EXTRACTION_POINTS.md
12. **Optional: enable LLM** — If retrieval answers insufficient; adds cost

---

*End of report*
