# High-Value Question Realism + Product Polish Report

**Sprint:** High-Value Question Realism + Product Polish  
**Created:** 2026-03-14  
**Status:** Complete

---

## 1. Sprint Theme

**Theme:** High-value question realism + product polish

**Why now:** The product has a 25-question corpus, 8 selected high-value productized question types, routing (FAST/LLM/human), simulation scenarios, handoff structure, and trust boundaries. The next highest-value move was to make these selected question types more realistic, first-person, emotionally believable, and demo/pilot convincing — then redeploy so the founder can inspect.

---

## 2. Control Docs Created

| Doc | Path |
|-----|------|
| Sprint Blueprint | `docs/sprints/HIGH_VALUE_QUESTION_REALISM_SPRINT_BLUEPRINT.md` |
| Execution Outline | `docs/sprints/HIGH_VALUE_QUESTION_REALISM_EXECUTION_OUTLINE.md` |
| Acceptance / SLA Criteria | `docs/sprints/HIGH_VALUE_QUESTION_REALISM_ACCEPTANCE_SLA.md` |

---

## 3. Polish Targets Selected

| # | Question Type | Route | Why Selected |
|---|---------------|-------|--------------|
| 1 | new_car_quote | LLM | Top frequency, mixed language |
| 2 | cancellation_warning | LLM | Critical urgency |
| 3 | payment_failed | LLM | High urgency, lapse risk |
| 4 | missing_document | LLM | Turn 1; mixed broker shorthand |
| 5 | already_sent_followup | FAST | Turn 2+; rule handoff |
| 6 | notice_confusion | LLM | English notice, client confused |
| 7 | premium_too_high | LLM | Retention; must NOT get renewal_reminder |
| 8 | claim_intake | LLM | First-response guidance |

---

## 4. Iteration Loop 1

**What changed:**
- Removed "客户问：" and "客户说" wrappers from multi-turn simulations (MT5, MT7, MT8, MT10, MT12, MT26, MT32)
- Changed broker-forwarded phrasing to first-person in `customer_entry_multi_turn_simulations.json`, `inbox_triage_scenarios.json`
- Added first-person variants to `auto_insurance_faq_intake_corpus.json` realistic_phrasing
- Updated FAQ handling matrix with first-person examples

**What got more realistic:**
- Payment/notice confusion: "这个英文 notice 说 payment failed，我现在怎么办？" (direct) vs "客户问：…"
- DMV notice: "这张DMV信什么意思？我需要做什么？" vs "客户发来一张DMV的信，问…"
- Missing doc: "要驾照 copy，我上周就发过了" vs "Client says I already sent it last week"
- Premium: "这个月保费太高了，能不能看看怎么降一点" vs "客户说这个月保费…"
- Add-car: "想加一台2021 Tesla Model Y，下周提车，今天能不能先出报价" vs "客户要加一台…"

**What got more useful:**
- FAQ corpus now has more first-person variants for matching
- Inbox triage scenarios reflect real broker-pasted client messages

**What did not improve:**
- Some scenarios (e.g. S2, S3) remain broker-forwarded by design (formal carrier notice text)
- English-only scenarios unchanged

**Whether it was worth it:** Yes. First-person phrasing is now the default for customer voice; validation passed.

---

## 5. Iteration Loop 2

**What changed:**
- SIM8: "Underwriting requested driver's license copy. Client says…" → "要驾照 copy，我上周就发过了"
- FAQ-W1: "客户问 garaging proof 是什么意思" → "garaging proof 是什么意思"
- FAQ-RM1: "客户卖掉旧车了，想把…" → "卖车了，想把…"
- Synced `configs/simulation_assistant_scenarios.json` → `ui/src/config/simulation_assistant_scenarios.json`

**What improved vs Loop 1:**
- Edge-case scenarios (SIM8, FAQ-W1, FAQ-RM1) now first-person
- UI has full 26-scenario pack including FAQ corpus scenarios

**What still remained weak:**
- FAQ-SR1 Turn 1 "Need SR-22 filing proof…" is broker question style (intentional)
- Some mixed broker/client contexts (e.g. "UW follow up - need dec page. 上周发过了") keep broker shorthand

**Whether it was worth it:** Yes. Consistency across all Simulation Assistant scenarios; UI sync ensures founder sees polished set.

---

## 6. Validation Summary

| Check | Result |
|-------|--------|
| run_inbox_triage_scenarios.py | 53/53 passed |
| run_multi_turn_simulations.py | 38/38 passed |
| audit_state_field_accuracy.py | 7/7 passed |
| verify_speed_routing.py | 9/9 OK |
| guardrail_inbox_triage.sh | PASS |
| unified_intake_smoke_check.sh | PASS |
| run_simulation_assistant_scenarios.py | 26/26 Normal |
| npm run build | Success |

**Limitations:** LC-AC3 has 1 acceptable friction (handoff at turn 2 vs expected 3). No regressions.

---

## 7. Frontend Redeploy Result

| Field | Value |
|-------|-------|
| **Success** | Yes |
| **Production URL** | https://ui-bthw2oxnm-andys-projects-1f411b73.vercel.app |
| **Deployment URL** | https://vercel.com/andys-projects-1f411b73/ui/DbvPUtcBeJWbE5or5Y2mkNnr9Mbx |
| **Alias updated** | Yes — https://ui-smoky-beta.vercel.app |
| **Warnings** | Chunk size > 500 kB (pre-existing) |

---

## 8. Post-Deploy Inspection

**Directly observed:**
- Deployment completed; alias ui-smoky-beta.vercel.app points to new build
- Simulation Assistant config synced (26 scenarios including FAQ-RM1, FAQ-SR1, FAQ-W1)

**Inferred from build/code:**
- Updated scenarios visible in Simulation Assistant at `/workbench/unified-intake`
- First-person wording in SIM1–SIM15, R1–R8, FAQ-RM1, FAQ-W1
- Trust boundary, Collected/Still needed, Human confirmation badges unchanged

**What feels more real:**
- Customer messages read as direct speech ("这个英文 notice 说 payment failed，我现在怎么办？") not broker paraphrase
- Short, messy fragments ("宝马x5，多少钱", "续保涨了好多 有办法吗") preserved

**What still feels weak:**
- Some broker-forwarded contexts (e.g. "UW follow up - need dec page") remain — acceptable for office workflow

---

## 9. Founder Showcase (REQUIRED)

### new_car_quote (Add vehicle, get quote)
- **Customer asks:** 我买了台宝马X5，想问下保费多少钱 / 宝马x5，多少钱 / 想加车，2024 Tesla Model Y
- **System roughly responds:** Acknowledge vehicle; ask for year, model, zip (or delivery/driver). Progressive 1–2 things at a time.
- **Still need to collect:** year, model or VIN, zip or address, delivery date, primary driver
- **Route:** LLM
- **Why it now feels more real:** First-person and shorthand ("宝马x5，多少钱") match how clients text brokers; no "客户问" wrapper.

### cancellation_warning (Policy will cancel)
- **Customer asks:** 这个是不是保单要停了？我昨天收到账单 overdue / Notice: Policy will be cancelled in 7 days. 这个是不是今天一定要处理？
- **System roughly responds:** Immediate urgency; ask for notice, payment proof; today action.
- **Still need to collect:** notice, payment status or screenshot
- **Route:** LLM (Human confirmation)
- **Why it now feels more real:** Direct client worry ("这个是不是保单要停了？") instead of "客户问 这个是不是…"

### payment_failed (Payment issue, lapse risk)
- **Customer asks:** payment failed，现在怎么办 / 这个英文 notice 说 payment failed，我现在怎么办？ / payment failed 是不是要停保？
- **System roughly responds:** State urgency; ask for notice or payment proof; today action.
- **Still need to collect:** notice, payment screenshot, callback number
- **Route:** LLM (Human confirmation)
- **Why it now feels more real:** Client speaks directly ("我现在怎么办？", "是不是要停保？"); urgency clear.

### missing_document (UW requested, client says sent)
- **Customer asks:** 要驾照 copy，我上周就发过了 / UW follow up - need dec page. 上周发过了 / declaration page 我上周就发了，怎么还在追？
- **System roughly responds:** Name the item; ask for resend or confirm we will verify.
- **Still need to collect:** item identified, sent status clear
- **Route:** LLM (Turn 1); Human confirmation when customer_says_sent
- **Why it now feels more real:** First-person "我上周就发过了", frustrated "怎么还在追？" — real office tone.

### already_sent_followup (Confirmation document sent)
- **Customer asks:** 发你了 / 我发了截图 / 上周发过了
- **System roughly responds:** Acknowledge; hand off to broker to verify.
- **Still need to collect:** (none — broker verifies)
- **Route:** FAST
- **Why it now feels more real:** Minimal, natural follow-up; no over-explanation.

### notice_confusion (English notice, need explanation)
- **Customer asks:** 这张DMV信什么意思？我需要做什么？ / 这个英文 notice 什么意思？ / 这个通知是不是今天一定要处理？
- **System roughly responds:** Reassure; ask for full notice or clearer photo; we will explain.
- **Still need to collect:** full notice, clearer photo
- **Route:** LLM (Human interprets)
- **Why it now feels more real:** Direct "什么意思？" "我需要做什么？" — client looking at letter.

### premium_too_high (Premium review, want to lower)
- **Customer asks:** 这个月保费太高了，能不能看看怎么降一点 / 续保涨了好多，有办法吗
- **System roughly responds:** Reassure options exist; ask for policy or bill (one is enough).
- **Still need to collect:** current policy, renewal notice, bill
- **Route:** LLM (must NOT get renewal_reminder)
- **Why it now feels more real:** First-person "太高了", casual "有办法吗" — retention-style.

### claim_intake (Accident, first-step guidance)
- **Customer asks:** 刚出事故了，要收集什么？ / 刚撞了，对方跑了，我现在先干嘛
- **System roughly responds:** Brief empathy; first-step: safety, photos, other driver info. Hit-and-run: emphasize plate, photos.
- **Still need to collect:** accident details, photos, other driver info (if not hit-and-run)
- **Route:** LLM (Human handles claim)
- **Why it now feels more real:** Panic tone "刚撞了，对方跑了，我现在先干嘛" — believable post-accident.

---

## 10. Final Judgment

1. **Did the selected high-value questions become more realistic?** Yes. First-person direct phrasing is now default; "客户问/客户说" wrappers removed where customer would speak directly.

2. **Did the product become more convincing for demo/pilot use?** Yes. Scenarios sound like real client messages; Chen Kui can judge "would my clients say this?"

3. **Which 3 polished question types now feel strongest?** new_car_quote, payment_failed/cancellation_warning, claim_intake.

4. **Which still feel weak or generic?** already_sent_followup (minimal by design); notice_confusion when broker forwards formal notice text.

5. **Did the frontend redeploy succeed?** Yes. Alias ui-smoky-beta.vercel.app updated.

6. **What should the founder inspect next?** Open https://ui-smoky-beta.vercel.app/workbench/unified-intake → Simulation Assistant → run SIM1, SIM2, SIM3, R3, R5, R6. Verify wording feels first-person and real.

7. **Best next move after this sprint:** Run Chen Kui trial with polished scenarios; capture which 3 he finds most useful; iterate on "still need to collect" clarity if he asks.

---

## 11. Iteration Log (REQUIRED)

### Loop 1
- **What changed:** First-person phrasing across multi-turn sims, inbox triage, FAQ corpus, FAQ handling matrix.
- **What got better vs prior:** Customer voice is direct; no broker-wrapper when customer would speak.
- **What did not improve:** Broker-forwarded formal notices (S2, S3) unchanged by design.
- **Whether the loop was worth it:** Yes.
- **Recommended next step after that loop:** Loop 2 — polish edge cases (SIM8, FAQ-W1, FAQ-RM1) and sync UI.

### Loop 2
- **What changed:** SIM8, FAQ-W1, FAQ-RM1 first-person; configs → UI sync.
- **What got better vs Loop 1:** Full scenario set consistent; UI shows 26 scenarios.
- **What did not improve:** FAQ-SR1 broker-question style kept (intentional).
- **Whether the loop was worth it:** Yes.
- **Recommended next step:** No Loop 3; deploy and founder inspection.

---

## 12. 中文宏观总结

**哪几个高价值问题这次被重点打磨了：** 新车报价、取消风险、付款失败、缺材料、已发送跟进、通知困惑、保费太高、事故报案。

**哪些现在更像真实用户会说的话：** "这个英文 notice 说 payment failed，我现在怎么办？"、"宝马x5，多少钱"、"续保涨了好多，有办法吗"、"刚撞了，对方跑了，我现在先干嘛"、"要驾照 copy，我上周就发过了"。

**系统大约会怎么回答：** 根据类型：紧急的催今天处理、要材料的点名要什么、报价的逐步问年份/zip/提车日、事故的给第一步指引（安全、拍照、对方信息）。

**还要补什么信息：** 各类型在 FAQ handling matrix 和 corpus 里有 "Still need to collect"；如报价要 year/model/zip、付款要 notice/截图、缺材料要具体项+是否已发。

**哪些走 FAST，哪些走 LLM，哪些要人工确认：** FAST：already_sent_followup、what_to_send、add_car_field_followup。LLM：new_car_quote、cancellation_warning、payment_failed、missing_document、notice_confusion、premium_too_high、claim_intake。人工确认：cancellation、payment、missing_doc customer_says_sent、add_car VIN/driver。

**发布以后你该去看什么：** 打开 https://ui-smoky-beta.vercel.app/workbench/unified-intake，点 Simulation Assistant，跑 SIM1（取消风险）、SIM2（缺材料）、SIM3（加车报价）、R3（宝马x5多少钱）、R5（刚撞了对方跑了）、R6（续保涨了好多）。看措辞是否像真人发的，不像测试用例。

---

## 13. COPY/PASTE DECISION BLOCK

```
Polished top question groups: new_car_quote, cancellation_warning, payment_failed, missing_document, already_sent_followup, notice_confusion, premium_too_high, claim_intake

Strongest 3 realistic examples:
1. "这个英文 notice 说 payment failed，我现在怎么办？" → urgency, today action
2. "宝马x5，多少钱" → ultra-short add-car, progressive ask
3. "刚撞了，对方跑了，我现在先干嘛" → panic, hit-and-run, first-step guidance

Best FAST candidates: already_sent_followup, what_to_send, add_car_field_followup

Biggest remaining weak area: already_sent minimal by design; some broker-forwarded formal notices unchanged

Redeploy succeeded: Yes. Alias: https://ui-smoky-beta.vercel.app

What to inspect next: Simulation Assistant → SIM1, SIM2, SIM3, R3, R5, R6 — verify first-person, real tone
```

---

*End of report*
