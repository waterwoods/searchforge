# P16-Y Phase 5 — Missing Information Library (Top 20)

**Date:** 2026-06-01  
**Sprint:** P16-Y Case Intelligence Hardening  
**Purpose:** Canonical gaps the office must detect before acting — mapped to `still_needed_fields` / summary hints

---

## Library

| # | Pattern | Example customer signal | System field / hint | Office action |
|---|---------|-------------------------|---------------------|---------------|
| 1 | **Missing policy number** | “我的保单…” without # | `policy_number` (collected when present) | Look up in AMS before calling carrier |
| 2 | **Missing deadline** | “7 days”, “by 3/15”, “deadline Friday” | `deadline_mentioned` + summary “Deadline: …” | Calendar same-day / countdown |
| 3 | **Missing VIN** | Add-car quote without 17-char VIN | `vin` (add-car lane) | Cannot bind — ask before quote |
| 4 | **Missing notice image/text** | “发来一张截图 看不懂” | `notice_image` | Ask for full notice photo or forward |
| 5 | **Missing driver info** | Add driver — name/license absent | `driver` / add-car still_needed | UW needs driver MVR |
| 6 | **Missing payment proof** | Cancellation / payment failed, no receipt | `payment_proof_or_screenshot` | Verify with carrier before telling client “ok” |
| 7 | **Missing verify-carrier step** | “我已经付了 / 上周发过了” | `verify_carrier_received` | Check carrier portal / email |
| 8 | **Missing declaration page** | Escrow / UW requests dec page | `declaration_page` in still_needed | Generate from carrier or client copy |
| 9 | **Missing garaging proof** | UW / escrow garaging request | `garaging_proof` | Client utility bill or policy dec |
| 10 | **Missing driver license copy** | UW DL request | `driver_license` | Front/back photo |
| 11 | **Missing sale date** | Remove vehicle — no date | `sale_date` (remove-car) | Backdate removal correctly |
| 12 | **Missing new address** | “搬家了” without zip | `zip` / address in summary | Rate change — must confirm garaging |
| 13 | **Missing effective date** | Address change — when moved | (summary hint) | Endorsement effective date |
| 14 | **Missing questionnaire / UW form** | “questionnaire incomplete” | `underwriting_followup` category | Send client checklist with deadline |
| 15 | **Missing accident details** | “刚出事故” — no photos | claim still_needed | Photos, other driver info |
| 16 | **Missing other-driver insurance** | Rear-ended, no adjuster info | claim intake prep | Start claim with evidence list |
| 17 | **Missing signature location** | “我签了呀怎么还要签” | missing_signature lane | Which page/field unsigned |
| 18 | **Missing lienholder info** | Add-car with loan | `lienholder` | COI / loss payee |
| 19 | **Missing delivery date** | Add-car quote — no delivery | `delivery` | Bind timing |
| 20 | **Missing contact name/phone** | Anonymous paste | contact gap (existing) | Callback before carrier call |

---

## Detection status (post P16-Y)

| Pattern | Before | After |
|---------|--------|-------|
| Policy number | ❌ | ✅ `_extract_policy_number_hint` |
| Deadline | ⚠️ prose only | ✅ summary + `deadline_mentioned` |
| Notice image | ❌ | ✅ `notice_image` still_needed |
| Address change intent | ❌ | ✅ `_is_address_change_request` |
| UW vs signature | ❌ | ✅ UW classifier priority |
| Driver add vs DL chase | ❌ | ✅ add-driver before missing-doc |
| VIN / driver / delivery | ✅ add-car lane | ✅ unchanged |

---

## Office glance checklist (human)

When reviewing a case, office should see at least one of:

1. **What happened** — summary intent line  
2. **What's collected** — `collected_fields` or summary “Collected: …”  
3. **What's still needed** — `still_needed_fields` or summary “Still needed: …”  
4. **When** — deadline hint if any  
5. **Who** — policy # or contact if extractable  

---

*End of P16-Y Phase 5 — Missing Info Library*
