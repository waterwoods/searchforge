# Reference Pattern Analysis Spec

**Sprint:** Mature Skeleton / Commercial Intake Backbone Sprint  
**Purpose:** Analyze the most useful mature product pattern families; define what to borrow and what not to copy.

---

## 1. Stripe-Like Patterns

### What Stripe Is Best For

| Pattern | Use for Chen Kui |
|---------|------------------|
| **Page clarity** | Clean hierarchy; one primary action per section; no clutter |
| **Visual productization** | Card-based containment; clear section boundaries; professional feel |
| **Form/card hierarchy** | Primary vs secondary vs tertiary; deliberate spacing |
| **Trust signals** | Security, compliance, "we handle this" framing above the fold |
| **Progressive disclosure** | Show what's needed; hide complexity until needed |

### What NOT to Copy from Stripe

- **Payment/billing flows** — We are not a payment product
- **Developer dashboard density** — Stripe has many tabs, APIs, logs; we are simpler
- **Enterprise configurability** — Stripe Dashboard is heavy; we are lightweight
- **API-first productization** — Our product is broker-facing, not developer-facing

### Borrow Map (Stripe)

| Borrow | Adapt | Skip |
|--------|-------|------|
| Page hierarchy (hero → primary → secondary) | Card containment for intake (not Stripe's exact styling) | Dashboard density |
| Trust/hero above fold | "Office will follow up" instead of "secure payment" | Payment flows |
| One primary action per block | Quick-start buttons as service entry points | API docs, webhooks |

---

## 2. Amazon / Amazon-Style Service Platform

### What Amazon-Style Is Best For

| Pattern | Use for Chen Kui |
|---------|------------------|
| **Service entry structure** | "Track package" / "Return item" / "Contact support" — clear entry points by need |
| **Operational flows** | Self-service path → escalation path; "what do you need?" first |
| **Customer support pathing** | Route by issue type; reduce "tell me your problem" vagueness |
| **Order/case context** | Show what's known; ask for what's missing; structured next step |

### What NOT to Copy from Amazon

- **Scale** — Amazon handles millions of SKUs, returns, logistics; we handle ~7 scenario types
- **Automated resolution** — Amazon auto-refunds, auto-ships; we never auto-send
- **Complex routing** — Amazon routes to many departments; we hand off to one broker office
- **Marketplace dynamics** — Reviews, ratings, seller/buyer; not our model

### Borrow Map (Amazon)

| Borrow | Adapt | Skip |
|--------|-------|------|
| Service entry by need (add car, missing doc, payment) | Our 7 scenarios as entry points | Scale, automation |
| "What do you need?" → route → collect | detect → ask → enough? → hand off | Multi-department routing |
| Order/case context display | Case card: collected, still needed, next step | Marketplace, reviews |

---

## 3. Intercom / Shopify Inbox-Like

### What Intercom/Shopify Inbox Is Best For

| Pattern | Use for Chen Kui |
|---------|------------------|
| **Messaging entry** | Inbox as primary surface; conversation as unit of work |
| **Quick actions** | Canned replies, suggested responses, one-click actions |
| **Handoff friendliness** | Assign to human; context passes; "customer said X" visible |
| **Customer-service interaction framing** | "We're here to help"; conversation-first; reply draft ready |

### What NOT to Copy from Intercom/Shopify Inbox

- **Real-time chat** — We are paste-based; no live WebSocket chat
- **Team assignment** — We have one broker office; no multi-agent routing
- **Conversation threading** — We have case + conversation; simpler model
- **Marketing automation** — Outbound campaigns; we are inbound-only
- **Chatbot-first** — We are intake-first; AI collects, human confirms

### Borrow Map (Intercom/Shopify Inbox)

| Borrow | Adapt | Skip |
|--------|-------|------|
| Handoff context (what customer said, what's needed) | broker_next_step, collected, still_needed | Real-time chat |
| Quick actions / suggested replies | Quick-start buttons, client_reply_draft | Marketing automation |
| "Assign to human" clarity | Hand off to broker; no auto-send | Team assignment |
| Conversation as unit | Case = one conversation; reopen context | Threading, campaigns |

---

## 4. Zendesk-Like Support/Ticket Structure

### What Zendesk Is Best For

| Pattern | Use for Chen Kui |
|---------|------------------|
| **Structured support/ticket thinking** | Ticket = issue + context + status + next action |
| **Priority/urgency** | P1/P2/P3; same-day vs routine |
| **Status workflow** | New → Open → Pending → Solved |
| **Agent view** | What agent sees; what to do next; history |

### What NOT to Copy from Zendesk

- **Full ticketing system** — We are lightweight; no SLA, no macros, no macros library
- **Multi-channel inbox** — Email, chat, social; we are paste-based
- **Knowledge base as product** — Zendesk Guide is central; we have RAG but it's supporting
| **Enterprise workflows** | Triggers, automations, custom fields; we are config-light |

### Borrow Map (Zendesk)

| Borrow | Adapt | Skip |
|--------|-------|------|
| Ticket structure (issue + context + status) | Case = focus + collected + still_needed + next_step | Full ticketing |
| Priority/urgency | critical, high, medium, low | SLA, macros |
| Status workflow | new, reviewing, waiting_client, done | Triggers, automations |
| Agent next action | broker_next_step | Multi-channel, KB |

---

## 5. First Borrow Map Summary

| Reference | Best For | Do NOT Copy |
|-----------|---------|-------------|
| **Stripe** | Page hierarchy, trust/hero, card containment, visual productization | Payment flows, dashboard density, API-first |
| **Amazon-style** | Service entry by need, operational flows, customer support pathing | Scale, automation, multi-department routing |
| **Intercom/Shopify Inbox** | Handoff context, quick actions, conversation-first framing | Real-time chat, team assignment, marketing |
| **Zendesk** | Ticket structure, priority/urgency, status workflow, agent next action | Full ticketing, multi-channel, SLA, macros |

---

## 6. Synthesis Direction

We synthesize **page structure** from Stripe (hierarchy, trust), **flow structure** from Amazon + our detect→ask→enough?→handoff, **state structure** from Zendesk (status, urgency) + our field progress (quote_ready, almost_ready), and **handoff structure** from Intercom (context, draft) + our broker_next_step/collected/still_needed.

**No single product is the template.** We borrow the strongest parts per function.

---

*End of Reference Pattern Analysis Spec*
