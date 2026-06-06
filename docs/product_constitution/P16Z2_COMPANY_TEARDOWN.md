# P16-Z2 Phase 1 — Company Teardown

**Date:** 2026-06-01  
**Sprint:** P16-Z2 Case Intelligence Strategic Reverse Engineering  
**Constraint:** No code. Strategy only.  
**Question:** Why do customers pay? What creates retention and willingness-to-pay?

---

## Executive synthesis

| Company | Core job customers pay for | North Star | Hardest to copy | Irrelevant to Chen Kui |
|---------|---------------------------|------------|-----------------|------------------------|
| **Zendesk** | Resolve customer issues at scale with measurable outcomes | Verified resolution | 20B+ ticket interaction corpus + outcome pricing infrastructure | Voice AI, 60-language omnichannel, enterprise admin |
| **Intercom** | Turn conversations into revenue and support with AI-first messaging | Conversation → outcome before ticket | Fin agent + messenger UX + conversation graph | Product-led growth funnels, in-app tours |
| **Salesforce Service Cloud** | System of record for service + AI-assisted agent productivity | Case closed with SLA compliance | CRM graph + org-specific ML on historical cases | Full CRM, Einstein platform, enterprise routing |
| **Stripe** | Money movement + dispute recovery with zero integration tax | Dispute won / revenue recovered | Payment graph + network-level fraud/dispute intelligence | Payments, billing, Smart Disputes as standalone product |
| **Linear** | Ship software with minimal process friction | Context → execution (not ticket → handoff) | Developer workflow graph + agent-native issue model | GitHub/GitLab PR automation, eng team workflows |
| **HubSpot Service Hub** | SMB service ops tied to CRM + self-serve deflection | Ticket deflected or closed via knowledge | CRM + content + portal unified data model | Marketing Hub bundle, IVR, skill-based routing |

---

## 1. Zendesk

### Why do customers pay?

- **Single pane for every channel** — email, chat, voice, social — with one ticket history
- **Agent productivity** — macros, views, triggers, SLA timers, copilot drafts
- **Leadership visibility** — CSAT, resolution time, backlog, team performance
- **2026 shift:** Outcome-based AI pricing ($1.50–$2.00 per *verified resolution*) — pay when AI actually closes issues

### Core problem solved

**Chaos of inbound customer problems → organized, routed, resolved work queue with accountability.**

### True North Star

**Verified resolution** — not ticket count, not deflection rate. Zendesk Relate 2026 explicitly pivoted from "deflection" to "the customer's problem is actually solved."

### Retention driver

- **Historical ticket data** locked in — switching means losing resolution patterns, macros, and routing rules
- **Resolution Learning Loop** — every interaction improves automated responses
- **Workflow muscle memory** — agents live in Zendesk 8 hours/day

### Willingness-to-pay driver

- **Cost per resolution math** — if AI resolves at $1.50 vs $8 human handle time, CFO approves
- **SLA breach prevention** — missed SLAs = churn; Zendesk prevents that
- **Omnichannel without building it** — cheaper than internal build

### Hardest to copy

- **~20 billion ticket interaction training corpus** (Relate 2026)
- **Resolution verification model** (independent evaluator for billing)
- **Enterprise trust + compliance footprint** (SOC2, HIPAA paths, global data residency)

### Irrelevant to our product

- Voice AI in 60+ languages
- Per-seat enterprise pricing tiers and add-on maze
- Agent Builder no-code platform for non-insurance verticals
- Outcome-based billing infrastructure (we have 1 broker, manual invoice)

---

## 2. Intercom

### Why do customers pay?

- **Messenger-first UX** — customers don't "open a ticket"; they chat where they already are
- **Fin AI agent** — resolves from knowledge base + product data before human needed
- **Product context** — knows who the user is, what plan, what they clicked
- **Conversation → ticket conversion** when structure is needed (`POST /conversations/{id}/convert`)

### Core problem solved

**Anonymous website visitor or in-app user → qualified conversation → structured ticket/opportunity without losing context.**

### True North Star

**Conversation continuity with resolution** — one thread, one customer, context carried across bot and human.

### Retention driver

- **Messenger installed on site/app** — ripping it out breaks customer entry
- **Fin trained on your content** — knowledge investment compounds
- **Operator workflows** — saved replies, assignment, snooze, tags become habit

### Willingness-to-pay driver

- **Deflection of repetitive questions** — Fin handles password resets, pricing FAQs
- **Speed to first response** — sub-minute bot reply vs hours email
- **Revenue attribution** — conversations tied to pipeline (Sales Hub overlap)

### Hardest to copy

- **Fin + Custom Helpdesk API** — pull/push conversation model that works with external systems
- **Ticket type schema system** — typed attributes, list fields, structured conversion from chat
- **Product analytics integration** — user events + support in one graph

### Irrelevant to our product

- In-app product tours and onboarding checklists
- B2B SaaS pricing page chat widgets
- Multi-brand messenger deployments
- Proactive outbound messages / campaigns

---

## 3. Salesforce Service Cloud

### Why do customers pay?

- **Case as system of record** — every interaction, field, owner, SLA on one object
- **Einstein Case Classification** — auto-fill Type, Reason, Priority from historical cases
- **Einstein Case Wrap-Up** — summarize chat, suggest next fields at close
- **Next Best Action** — context-aware recommendation cards on Case record
- **Routing + Flow automation** — case hits queue without human triage

### Core problem solved

**Unstructured inbound → classified, routed, SLA-tracked case with full customer 360.**

### True North Star

**Case closed within SLA with complete audit trail** — compliance and reporting are first-class.

### Retention driver

- **CRM is the business** — Account, Contact, Opportunity, Case all linked
- **Custom objects and flows** — years of org-specific automation
- **Historical ML models trained on org data** — switching loses prediction accuracy

### Willingness-to-pay driver

- **Agent time saved on classification** — mailroom sorter metaphor: case arrives pre-categorized
- **Routing accuracy** — urgent cases reach Tier 2 without manual read
- **Leadership dashboards** — case volume, backlog, agent utilization

### Hardest to copy

- **Customer 360 graph** — every case linked to account history, contracts, assets
- **Per-org ML on closed cases** — 85% accept-rate gate before auto-set
- **Enterprise admin ecosystem** — thousands of AppExchange integrations

### Irrelevant to our product

- Full Sales Cloud + Marketing Cloud bundle
- Interactive Voice Response (IVR) and call center
- Skill-based routing across 50 agents
- Conditional SLAs by customer tier

---

## 4. Stripe

### Why do customers pay?

- **Payments work** — that's the core; support is embedded
- **Smart Disputes** — AI assembles evidence packets from transaction graph + merchant data
- **Zero integration for disputes** — built into existing Stripe Dashboard/API
- **Recommended evidence fields** — system tells you what's missing before submission

### Core problem solved

**Messy dispute notice + scattered evidence → complete, deadline-safe submission packet.**

### True North Star

**Revenue recovered** — dispute won or accepted intelligently; never miss deadline.

### Retention driver

- **Payment data is already there** — no export/import
- **Network intelligence** — Stripe sees patterns across merchants
- **Automatic deadline submission** — set and forget

### Willingness-to-pay driver

- **Success fee on recovered disputes** — only pay when it works
- **Time saved on evidence gathering** — hours → minutes
- **Win rate improvement** — tailored packets by reason code

### Hardest to copy

- **Transaction graph** — charge, customer, IP, receipt, shipping, metadata all linked
- **Issuer reason-code intelligence** — knows what evidence wins by dispute type
- **Scale of dispute outcomes** — feedback loop across network

### Irrelevant to our product

- Payment processing entirely
- Subscription billing
- Connect marketplace splits
- Radar fraud scoring

### What IS relevant (pattern, not product)

Stripe's **evidence packet assembly** is the closest analog to **insurance case assembly from messy inputs**:
- Pull from structured sources automatically
- Flag `requires_evidence` vs `available`
- Merge manual + auto into strongest packet
- Submit before deadline

---

## 5. Linear

### Why do customers pay?

- **Speed** — issue created and updated in seconds, keyboard-first
- **Minimal process** — no Jira admin PhD required
- **Context-native agents (2026)** — Linear Agent creates/updates issues from conversations, Slack, code
- **GitHub/GitLab automation** — PR state drives issue state

### Core problem solved

**Scattered feedback and context → tracked work item without manual ticket ceremony.**

### True North Star

**Context → execution** — Karri Saarinen: "issue tracking as central organizing layer is dead." Work flows from conversation/code; issues are outputs, not inputs.

### Retention driver

- **Team workflow embedded in Linear** — cycles, projects, triage views
- **Git integration** — PR linkbacks, auto-status
- **Agent adoption** — 75%+ enterprise workspaces use coding agents; 25% of new issues agent-authored

### Willingness-to-pay driver

- **Engineering velocity** — less time in process, more in code
- **Visibility without overhead** — leadership sees progress without standup theater
- **Agent-native workflows** — automations refine inbound issues on arrival

### Hardest to copy

- **Opinionated UX** — years of "remove friction" product culture
- **Agent session model** — `AgentSession` lifecycle, plans, activities API
- **Developer audience trust** — brand = fast, not enterprise bloat

### Irrelevant to our product

- Git branch naming → auto-assign
- Sprint cycles and roadmap views
- PR review state automation
- Engineering-specific issue types

### What IS relevant (pattern)

- **Automations on inbound** — "intelligent triage the moment new context arrives"
- **Context as source of truth** — don't force user to translate to ticket first
- **Agent plans** — session-level checklist that evolves during execution

---

## 6. HubSpot Service Hub

### Why do customers pay?

- **All-in-one SMB stack** — CRM + tickets + knowledge base + portal
- **Customer portal** — authenticated users see ticket status, reply, self-serve KB
- **Breeze Customer Agent** — AI resolves from KB + website + files; credits per resolution
- **Ticket → KB loop** — frequent questions become articles; deflection compounds

### Core problem solved

**Small team drowning in repeat questions → self-serve + organized ticket queue tied to CRM.**

### True North Star

**Ticket deflected or closed** — knowledge gap detection drives content investment.

### Retention driver

- **CRM is shared across sales/marketing/service** — one customer record
- **Knowledge base investment** — articles, SEO, multi-language
- **Portal becomes customer habit** — "check my ticket" instead of calling

### Willingness-to-pay driver

- **67% ticket reduction claim** (marketing) via KB + portal
- **Professional tier unlocks** KB + portal + customer agent
- **Credit-based AI** — pay for resolutions delivered, not seats idle

### Hardest to copy

- **Smart CRM** — unified contact timeline across hubs
- **Content + service integration** — KB articles surface in tickets, portal, agent
- **SMB onboarding simplicity** — setup in hours not months

### Irrelevant to our product

- Marketing Hub email campaigns tied to tickets
- Multi-language KB at enterprise scale
- IVR and call routing
- Salesforce migration tools (they don't integrate)

---

## Cross-company patterns (steal these)

| Pattern | Best exemplar | Chen Kui application |
|---------|---------------|---------------------|
| Paste → structured record in one action | Salesforce Case Classification | WeChat paste → case glance |
| Conversation → typed record | Intercom convert-to-ticket | Customer chat → service record |
| Evidence packet assembly | Stripe Smart Disputes | Notice screenshot → collected_fields |
| Outcome not activity pricing | Zendesk verified resolution | Sell "cases ready to act" not "messages processed" |
| Context-first, ticket-second | Linear Agent | Message-first intake, not category buttons |
| Self-serve status | HubSpot portal | 我的办理 tab (already built, hidden) |
| Next action on record | Salesforce NBA | broker_next_step + waiting_on |

---

## What Chen Kui would never buy from these companies

| Vendor product | Why not |
|----------------|---------|
| Zendesk Suite | $50+/seat/mo; built for 10+ agent call centers |
| Intercom Fin | Needs website messenger + KB corpus |
| Salesforce Service Cloud | $100+/user; 6-month implementation |
| Stripe | Not a service product |
| Linear | Wrong vertical entirely |
| HubSpot Service Hub | CRM-first; Chen Kui lives in WeChat + AMS |

**Implication:** We are not competing with these vendors. We are **extracting patterns** for a **1-office, WeChat-native, insurance-specific Case Intelligence wedge**.

---

*End of P16-Z2 Phase 1 — Company Teardown*
