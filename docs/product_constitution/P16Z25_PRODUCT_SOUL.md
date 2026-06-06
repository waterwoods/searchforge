# P16-Z2.5 Product Soul

**Date:** 2026-06-01  
**Sprint:** P16-Z2.5 Product Soul Synthesis  
**Sources:** P16-Y, P16-Z0, P16-Z2

---

## The two sentences

**Customers do not pay us for** AI, software, dashboards, category buttons, document scanning, chatbots, CRM features, or a platform.

**Customers pay us for** the office handling their insurance request faster — with clear next steps, nothing lost in WeChat chaos, and a reply they can trust.

---

## What brokers pay for (Chen Kui lens)

Brokers do not pay for software. They pay for **time back**.

| Pain today | What we sell |
|------------|--------------|
| 50 unread WeChat messages | One paste → ready-to-send reply |
| Re-read paste to find deadline | Deadline in glance + countdown |
| Re-type client message | Copy-to-WeChat button |
| Lose context when client replies | Append to same case |
| Mixed English in tool | Chinese office workflow |
| "Why open a webpage?" | Beat「直接回微信」on first case |

---

## What customers pay for (via broker)

Customers do not want software. They want **the office to handle their thing**.

| Customer need | How product serves it |
|---------------|----------------------|
| "帮我加车" without forms | Message-first intake (week 3+) |
| Know what's still needed | Plain Chinese gap list |
| Know it was received | Handoff confirmation |
| Check status without calling | 我的办理 tab |
| Send follow-up info | 提交补充 on same case |

**Pilot weeks 1–2:** Customers interact through Chen Kui's WeChat, not our URL. Broker stays the trusted interface.

---

## The product should feel like

> **Paste 微信 → 案件就绪 → 复制发出 → 客户回复 → 追加 → 再复制**

---

## Three soul elements

### 1. Speed

Under 45 seconds paste to copy on urgent cancel. Beat WeChat manual drafting. If the first case is slower than typing a reply by hand, the broker never returns.

### 2. Completeness

`还缺什么` and `办公室下一步` in Chinese, specific, never generic. Office never re-reads paste. broker_next_step must name the carrier, the document, or the deadline — not "follow up with client."

### 3. Continuity

Same case grows with each message. Linear's "context is source of truth" applied to insurance WeChat. Turn 1 is not the product — the loop is the product.

---

## Not the soul

| Element | Why excluded |
|---------|--------------|
| Category buttons | Workflow-first, not message-first |
| Engineer field labels | Office reads Chinese, not `_policy_number` |
| UTC timestamps | Wrong culture for Chinese office |
| Demo queue noise | Competes with 开始整理 on Day 0 |
| English mixed in Chinese glance | Breaks Chen Kui trust |
| Platform/lab tabs | Internal tooling, not broker product |
| Smarter AI for Turn 1 only | Continuity cues > smarter first draft |
| Full CRM / multi-tenant | Chen Kui has AMS; not replacing |

---

## Competitive soul alignment

Every benchmark company (Zendesk, Intercom, Salesforce, Stripe, Linear, HubSpot) implements:

```
Chaos → Understanding → Case → Next Action → Outcome
```

We built this pipeline. We have not yet **deployed and taught** it.

---

## Soul test (use on every feature idea)

Ask: *Does this help a broker paste WeChat chaos and get a Chinese next action they can copy in under a minute — and come back when the client replies?*

- **Yes** → Revive, wire, or tune.
- **No** → Reject or defer.

---

*End of P16-Z2.5 Product Soul*
