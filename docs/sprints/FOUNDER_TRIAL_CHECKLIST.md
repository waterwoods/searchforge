# Founder Trial Checklist — Backend Redeploy Verification

**Purpose:** Test the hardened scenarios on the live frontend after backend redeploy.

**Backend URL:** https://fiqa-api-g7zatxrycq-uw.a.run.app  
**Frontend URL:** _(Vercel / localhost:5173)_

---

## Scenario A — Billing clarification

**Input:** `账单什么意思`

**Expected:**
- Category: customer_question (NOT payment_lapse_expiration)
- Reply: Asks to send full bill/notice, offers to explain key points and next step
- Reply contains: 发我, 帮你看 (or equivalent)

**Pass / Fail:** _____

---

## Scenario B — Billing clarification variant

**Input:** `这个账单我看不懂`

**Expected:**
- Same as Scenario A
- Clarification flow, NOT payment urgency flow

**Pass / Fail:** _____

---

## Scenario C — Remove vehicle shorthand

**Input:** `减车，卖掉了`

**Expected:**
- Remove vehicle / policy change handling
- Asks for sell date, vehicle info, transfer status
- NOT unclear / NOT generic fallback

**Pass / Fail:** _____

---

## Scenario D — Claim first notice shorthand

**Input:** `报事故，刚撞了`

**Expected:**
- Claim intake / first notice guidance
- Asks for photos, other driver info, what happened
- NOT generic fallback

**Pass / Fail:** _____

---

## Scenario E — Renewal increase

**Input:** `续保涨了好多，帮我看看`

**Expected:**
- Renewal / premium review style handling
- Should NOT misroute to payment failure
- Asks for policy, bill, renewal notice

**Pass / Fail:** _____

---

## Summary

- Total passed: _____ / 5
- Biggest issue (if any): _____________________
- Ready for founder demo: Yes / No
