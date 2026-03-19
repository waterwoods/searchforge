# 15-Minute Broker Demo Script

California Auto Insurance Broker Assistant — Demo for 陈魁.

## Intro (1 min)

**Say:** "This is a California auto insurance assistant for brokers. It helps you answer common client questions quickly, using official sources — DMV, California Department of Insurance, and insurer sites. You can copy the answer and links directly to WeChat. Questions in Chinese or English both work."

**Do:** Open http://localhost:5173/demo. Point to the header: 加州汽车保险经纪助手. Point to the value prop: 帮经纪快速回答客户问题，附官方 / 权威来源链接，可直接发微信.

---

## Question 1 — New Car / Minimum Coverage (3 min)

**Click or type:** 我刚买了辆新车（加州），最低需要买哪些保险？大概怎么配比较合理？

**Say:** "A typical client question. The system returns a concise answer plus official links you can send to the client."

**Do:** Show the 建议结论 panel, 下一步怎么做, and 复制给客户 button. Click 复制给客户 and paste into a note to show the WeChat-ready format.

---

## Question 2 — Registration Suspended (3 min)

**Click or type:** 我的车注册被暂停了（可能是保险问题），我该怎么恢复？需要交多少钱/提交什么材料？

**Say:** "Another common scenario. The assistant pulls from DMV and insurance sources. You get steps and links to share."

**Do:** Expand a citation, show the domain badge (GOV vs INSURER).

---

## Question 3 — License / Compliance Check (3 min)

**Click or type:** 客户问我：怎么查保险公司/经纪人是不是合规？加州官方在哪里能查到？

**Say:** "Compliance questions. The system points to insurance.ca.gov for license lookup. Brokers can quickly verify and share with clients."

**Do:** Show the insurance.ca.gov citation.

---

## Question 4 — Savings / Discounts (2 min)

**Click or type:** 客户想省钱：哪些因素会影响保费？有哪些常见折扣/优惠？

**Say:** "Clients often ask about saving money. The assistant surfaces factors and common discounts from official and insurer sources."

---

## Question 5 — Claims Process (2 min)

**Click or type:** 出险后理赔流程是怎样的？

**Say:** "Claims process. The assistant gives steps and links so you can guide clients quickly."

---

## Fallback transition (if Live fails)

**Say:** "Let me switch to our offline demo mode. We keep pre-saved answers for the most common questions so the demo can run even when the live system is unavailable."

**Do:** Refresh the page. Wait for the orange banner. Click the 5 recommended questions in order. Continue the script from Q1.

---

## Wrap-Up (1 min)

**Say:** "The system is designed to reduce your lookup time and give you authoritative answers you can share with clients. We're iterating based on broker feedback."

**Ask:** "What would make this most useful for your day-to-day work? Any questions or scenarios we should add?"

---

## Timing Summary

| Section | Time |
|---------|------|
| Intro | 1 min |
| Q1 New car | 3 min |
| Q2 Registration suspended | 3 min |
| Q3 License/compliance | 3 min |
| Q4 Savings (Live only) | 2 min |
| Q5 Claims (Live only) | 2 min |
| Wrap-up | 1 min |
| **Total** | **15 min** |
