# Add-Car Founder Trial Scenario Pack

Use these in **Customer Entry** and **Workbench** in order during founder inspection. Pass criteria: correct category, sensible `collected_fields` / `still_needed_fields`, `quote_ready_status` when applicable, professional `broker_next_step`, handoff when rules say so.

## 1. Normal add-car

- **T1:** “我想加一台2024 Honda CR-V，邮编91780，下周五提车，主要我开。”
- **Expect:** Add-car intent, fields trend toward quote-ready, clear next step for office.

## 2. Quote-ready, no contact

- **T1:** Full vehicle + zip + delivery + driver in one message; **omit** name/phone.
- **Expect:** Quote-ready or near-ready; contact “待补”; human confirmation may flag if policy ties to identity.

## 3. Add-car + materials sent

- **T1:** Add-car basics. **T2:** “registration 和 dec page 我昨天已经发给你们了。”
- **Expect:** `follow_up_type` / office context reflects “already sent”; broker next step includes verify receipt.

## 4. Add-car + correction

- **T1:** Vehicle A. **T2:** “不对，是2024 Tesla Model 3，不是本田。”
- **Expect:** Correction handling; structured fields updated; no premature wrong handoff.

## 5. Add-car + side question

- **T1:** “加一台宝马X5 90210 下周提车 对了 garaging proof 是什么”
- **Expect:** Mixed intent note or answered side thread; add-car collection continues; broker sees both.

## 6. Progressive info collection

- **T1:** “刚订了新车想加保。” **T2:** 年份+车型. **T3:** 邮编. **T4:** 提车+驾驶人.
- **Expect:** `need_more` → `almost_ready` → `quote_ready` progression; `next_best_question` useful each turn.

## 7. Partial info + hesitation

- **T1:** “想问问新车保险大概多少钱” (no vehicle details). **T2:** “我还没想好车型能不能先报个价”
- **Expect:** Polite boundary; still asks for minimum facts; does not fake quote; office step honest.

## 8. Quick-start + structured hybrid (post-sprint)

- **Action:** Use “加车报价 · 快速填写” with 2–3 fields → submit.
- **Expect:** Same triage as typed paragraph; soft route `add_car`; fewer turns to quote-ready.
