# Human Front Door + Talk-to-Agent — Product Blueprint

**Sprint:** Human Front Door + Talk-to-Agent Sprint  
**Scope:** Chen Kui Insurance Unified Entry  
**Created:** 2026-03-15

---

## 1. Why the Front Door Matters Commercially

Before a customer cares about durable architecture, they first need to feel:
- **Understood** — the system gets what they're asking
- **Reassured** — it is helping, not interrogating
- **Not trapped** — they can reach a real human when needed
- **Connected to a real office** — their info goes to Chen Kui's team, not into a void

The front door is the first impression. For a small insurance broker serving Chinese-speaking clients, trust is the product. If the entry feels like a dev tool or lab interface, customers will bounce before the strong intake logic ever runs.

**Commercial impact:** A polished front door converts "maybe I'll try this" into "I'll send this to my broker." A prototype-like front door does the opposite.

---

## 2. Why Talk to Agent Matters

Users who want to speak to a human have no dedicated path today. "上传材料 / 联系客服" conflates documents with contact; it routes to missing-document, not "I want to talk to someone."

**Trust gap:** Customers who are confused, urgent, or simply prefer human contact may leave. For a small business, one lost customer who felt trapped is one too many.

**Product audit finding:** "No clear 'talk to agent' path" is the single biggest weakness. Shopify, Stripe, Amazon all surface "Contact support" or "Talk to us" on the first screen.

---

## 3. Why Business-Readable Case Summary Matters

Today the Case Summary shows raw field names: `year`, `make_model`, `zip`. Broker notes should read like: "Year", "Make/Model", "ZIP" — or better, "年份", "车型", "邮编" in customer-facing context.

**Office-facing:** When Chen Kui's team receives a handoff, the summary should feel like broker notes, not developer fields. "Collected: year, make_model" → "已收集：年份、车型、邮编"

**Customer-facing:** During intake, the live summary should reassure: "We have your car info and ZIP; we still need delivery date." Not: "Collected: year make_model zip. Still needed: delivery_date."

---

## 4. What "Good Enough for Paid Pilot Front Door" Means

| Criterion | Definition |
|-----------|------------|
| **More human** | Welcome feels like a real office assistant; copy is warm, not robotic |
| **More reassuring** | User sees "办公室会尽快处理" / "我们会尽快帮您" — clear that a real team will follow up |
| **Clear human handoff** | "联系人工" / "联系陈奎办公室" is visible, obvious, and works |
| **Business-readable summary** | Case Summary uses human labels (Year, Make/Model, ZIP) not raw keys |
| **Trust boundary** | User understands: not auto-send; office will confirm; no false promises |

**Not yet required:** Backend data-model redesign, multi-tenant auth, Stripe integration. This sprint is front-door and handoff UX only.

---

## 5. Out of Scope (Non-Negotiable)

- Backend data-model redesign
- Heavy infrastructure work
- New CRM or multi-tenant features
- Changes to core triage logic beyond Talk-to-Agent routing

---

*See also: UX Design Spec, Execution Outline, Acceptance Criteria, Talk-to-Agent Policy*
