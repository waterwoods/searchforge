# Answer Alignment Audit Sprint — Blueprint

**Sprint:** Answer Alignment Audit + Optimization Direction  
**Created:** 2026-03-15  
**Scope:** Chen Kui Insurance Unified Entry — Customer Entry / Broker Workbench

---

## 1. Why Answer Alignment Matters Now

The founder’s concern: **“The answer is not good enough. It does not really answer the question being asked.”**

- Chen Kui trial success depends on the system feeling **helpful**, not bureaucratic.
- If responses feel 答非所问 (答非所问 = answering something other than what was asked), trust erodes.
- First paid pilot requires the broker to confidently copy replies to clients.
- Answer alignment is a **product differentiator** — brokers already have generic templates; the system must add value by directly addressing the real ask.

---

## 2. Why “Answer the Real Ask” Is Commercially Important

| Stakeholder | Impact of misalignment |
|-------------|------------------------|
| **Chen Kui (broker)** | Won’t trust the draft; will rewrite or ignore. |
| **End client** | Feels unheard; may escalate or churn. |
| **Pilot conversion** | “Doesn’t really help” → no paid trial. |
| **Word of mouth** | “AI doesn’t get it” spreads quickly. |

---

## 3. What Good Enough Looks Like

| Scenario | Good enough |
|----------|-------------|
| **Direct question** (“payment failed 怎么办”) | Brief direct answer first (what to do), then ask for notice/screenshot. |
| **Mixed ask** (“payment failed 怎么办，dec page 我上周发过了”) | Address both: payment urgency + “我们会核对 dec page”。 |
| **Clarification** (“garaging proof 是什么意思”) | Explain first, then ask for document. |
| **Price ask** (“宝马x5，多少钱”) | Acknowledge vehicle, ask year+zip, then quote path — not “请提供更多信息”。 |
| **Urgency** (“最要紧做什么”) | Answer urgency directly, then hand off. |

---

## 4. In Scope / Out of Scope

| In scope | Out of scope |
|----------|--------------|
| Intent classification accuracy | Model swap or fine-tuning |
| Reply strategy (answer first vs collect first) | Full UI redesign |
| Routing (fast vs LLM path) | New features |
| Reply wording / templates | Multi-tenant, auth |
| Over-handoff / under-answer | Other verticals |
| Scenario realism in simulations | |

---

## 5. Success Criteria for This Sprint

- Identify **primary root cause** of answer misalignment.
- Propose **single highest-value optimization direction**.
- Recommend **best small next step** (implementable in 1–2 days).
- Clearly state **what to postpone**.

---

*End of blueprint*
