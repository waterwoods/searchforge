# California Auto Insurance Broker Assistant — Product Description

**For 陈魁 and broker demos.**

---

## What It Is

A California auto insurance assistant for brokers. It answers common client questions using official sources — California DMV, California Department of Insurance, and major insurer sites.

---

## What It Helps With

- **Faster answers** — Get concise answers and official links instead of searching multiple sites.
- **Client-ready copy** — One-click copy in a format you can paste into WeChat.
- **Authoritative sources** — Answers are tied to DMV, insurance.ca.gov, and insurer pages.
- **Bilingual** — Ask in Chinese or English; results can be shown in Chinese.

---

## 5 Sample Questions (Broker-Relevant)

1. 我刚买了辆新车（加州），最低需要买哪些保险？大概怎么配比较合理？  
   *New car, minimum coverage, how to configure*

2. 我的车注册被暂停了（可能是保险问题），我该怎么恢复？需要交多少钱/提交什么材料？  
   *Registration suspended, how to restore*

3. 客户问我：怎么查保险公司/经纪人是不是合规？加州官方在哪里能查到？  
   *How to verify insurer/broker license, where to look up*

4. 客户想省钱：哪些因素会影响保费？有哪些常见折扣/优惠？  
   *Factors affecting premiums, common discounts*

5. 出险后理赔流程是怎样的？  
   *Claims process*

---

## Live Mode vs Offline Demo Mode

| | Live Mode | Offline Demo Mode |
|---|-----------|-------------------|
| **When** | Backend and Qdrant are running | Backend or Qdrant unavailable |
| **Questions** | Any question | 3 pre-saved questions only |
| **Answers** | Real-time retrieval | Pre-saved answers |
| **Use case** | Full demo, real usage | Demo fallback when live fails |

**In short:** Live mode = ask anything, get real-time answers. Offline mode = click 3 questions, get pre-saved answers. Both show the same UI and client-ready copy.

---

## Language

- Practical, not technical
- No mention of AI/LLM unless asked
- Focus on: faster answers, official sources, client-ready copy
