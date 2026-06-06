# P16-Z4 Phase 5 — Claims Case Simulation

**Date:** 2026-06-02  
**Sprint:** P16-Z4 Case Continuity Sprint  
**Method:** 10 realistic multi-turn claims conversations evaluated against engine behavior (`claim_intake` lane, append, summary, next action)  
**Runtime assumption:** Rules-based triage (production fallback path per P16-Y)

---

## Evaluation rubric (per conversation)

| Dimension | Question |
|-----------|----------|
| **Case quality** | Correct category, urgency, collected/still on each turn? |
| **Timeline quality** | Thread + summary reflect all turns? |
| **Next action quality** | `broker_next_step` + draft actionable per turn? |

---

## 10 claims conversations

### C1 — Rear-end, Turn 1 FNOL

| Turn | Message (summary) |
|------|-------------------|
| 1 | 「刚在高速被追尾了，对方跑了，我现在该怎么办？」 |

**Expected:** `claim_intake`, high urgency, still_needed: photos, plate, other driver info.

| Dimension | Score | Notes |
|-----------|-------|-------|
| Case | ✅ Strong | Hit-and-run template path exists |
| Timeline | N/A | Single turn |
| Next action | ✅ Strong | Evidence collection broker step |

---

### C2 — C1 + Turn 2 photo

| Turn | Message |
|------|---------|
| 2 | 「照片发你了，车牌是 8XYZ123」 |

**Expected:** collected_fields grow; still_needed shrink; summary mentions plate.

| Dimension | Score | Notes |
|-----------|-------|-------|
| Case | ⚠️ Partial | Fields may update; summary merge thin |
| Timeline | ⚠️ Partial | `case_messages` ok; summary may not show plate |
| Next action | ✅ OK | Shift to carrier report step |

---

### C3 — C2 + Turn 3 insurance letter

| Turn | Message |
|------|---------|
| 3 | 「保险公司来信说要补充陈述，我附上扫描件」 |

**Expected:** missing_document or claim follow-up; attachment path if broker uploads.

| Dimension | Score | Notes |
|-----------|-------|-------|
| Case | ⚠️ Partial | May classify as missing_document vs claim |
| Timeline | ⚠️ | Attachment API exists; customer inline image weak |
| Next action | ⚠️ | May generic if mixed-intent |

---

### C4 — C3 + Turn 4 customer anxiety

| Turn | Message |
|------|---------|
| 4 | 「怎么还没理赔进度？我很着急」 |

**Expected:** timeline_question / claim follow-up; waiting_on client→carrier.

| Dimension | Score | Notes |
|-----------|-------|-------|
| Case | ⚠️ | May hit unclear vs claim |
| Timeline | ❌ Weak | No carrier-waiting UX |
| Next action | ⚠️ | Generic “check with carrier” |

---

### C5 — Side swipe, bilingual

| Turn | Message |
|------|---------|
| 1 | 「Got in a fender bender in parking lot, other driver gave insurance card」 |

**Expected:** claim_intake, collected: other driver info partial.

| Dimension | Score | Notes |
|-----------|-------|-------|
| Case | ✅ | EN markers work |
| Timeline | N/A | |
| Next action | ⚠️ EN broker_next_step on product_only |

---

### C6 — C5 + photos + “by accident” idiom trap

| Turn | Message |
|------|---------|
| 2 | 「I sent photos. I parked there by accident last week.」 |

**Expected:** Must NOT misclassify as FNOL; append same case.

| Dimension | Score | Notes |
|-----------|-------|-------|
| Case | ⚠️ | “by accident” exclusion exists — monitor |
| Timeline | ⚠️ | Append boundary |
| Next action | ⚠️ | |

---

### C7 — Hit and run Chinese

| Turn | Message |
|------|---------|
| 1 | 「对方肇事逃逸，我只拍到了车尾，没有人受伤」 |

**Expected:** claim_intake_hit_and_run template.

| Dimension | Score | Notes |
|-----------|-------|-------|
| Case | ✅ | |
| Next action | ✅ | Chinese template if configured |

---

### C8 — C7 + Turn 2 police report

| Turn | Message |
|------|---------|
| 2 | 「报警记录在这，案号 2026-12345」 |

**Expected:** collected police_report; broker step: file with carrier.

| Dimension | Score | Notes |
|-----------|-------|-------|
| Case | ⚠️ | No dedicated police_report field |
| Timeline | ⚠️ | Summary may omit case number |
| Next action | ✅ | Prose step ok |

---

### C9 — Mixed claim + payment (priority)

| Turn | Message |
|------|---------|
| 1 | 「出险了要理赔，另外这个月的保费账单我也看不懂」 |

**Expected:** claim wins per mixed-intent rule.

| Dimension | Score | Notes |
|-----------|-------|-------|
| Case | ✅ | Code: claim + payment → claim |
| Next action | ⚠️ | Payment gap ignored until Turn 2 |

---

### C10 — C9 + Turn 2 payment only

| Turn | Message |
|------|---------|
| 2 | 「账单我付过了，截图发你」 |

**Expected:** payment lane on append OR boundary if “new issue”.

| Dimension | Score | Notes |
|-----------|-------|-------|
| Case | ⚠️ | Topic shift — borderline append |
| Timeline | ⚠️ | `case_boundary` may flag |
| Next action | ⚠️ | requires_new_case risk |

---

## Aggregate scores (simulated)

| Dimension | Avg | Verdict |
|-----------|-----|---------|
| Case quality (Turn 1) | **82/100** | claim_intake lane solid |
| Case quality (Turn 2+) | **62/100** | merge + mixed-intent |
| Timeline quality | **55/100** | messages yes, summary/UX no |
| Next action quality | **74/100** | templates strong; waiting weak |

---

## TOP 10 claims failures

| # | Failure | Turns affected |
|---|---------|----------------|
| 1 | **No claims-specific collected_fields** (photos, plate, police #) | C2, C8 |
| 2 | **Summary doesn't accumulate evidence across turns** | C2, C4, C8 |
| 3 | **Carrier-waiting not in `waiting_on` workflow** | C4 |
| 4 | **Mixed claim + payment loses payment on Turn 1** | C9 |
| 5 | **Topic shift claim→payment triggers boundary noise** | C10 |
| 6 | **Customer can't inline attach scan on Turn 3** | C3 |
| 7 | **EN broker_next_step on bilingual office** | C5 |
| 8 | **“Progress check” may classify unclear** | C4 |
| 9 | **No claim closure / outcome field** | All |
| 10 | **Broker never sees thread — re-reads WeChat** | All multi-turn |

---

## Claims wedge recommendation (7-day scope)

1. Config tune `claim_intake` + `claim_intake_hit_and_run` Chinese templates  
2. Append summary merge for photo/plate tokens (rule extract, not new service)  
3. Post-copy waiting_on prompt default 等保司/等客户 by sub-intent  
4. Optional: `still_needed_fields` add `accident_photos`, `other_driver_info` in missing-info library  

---

*End of P16-Z4 Phase 5*
