# P16-Z2 Phase 7 — Top 50 Ideas That Should NOT Be Copied

**Date:** 2026-06-01  
**Sprint:** P16-Z2 Case Intelligence Strategic Reverse Engineering  
**Rule:** If it requires enterprise team, expensive infra, or doesn't move Chaos→Case→Next Action for one broker office — reject.

---

## Category A — Enterprise Complexity (1–10)

| # | Anti-pattern | Source | Why reject |
|---|--------------|--------|------------|
| 1 | Full CRM (Account/Contact/Opportunity) | Salesforce | Chen Kui has AMS; not replacing |
| 2 | Custom object schema designer | Salesforce | 1 developer; rules in code suffice |
| 3 | Flow Builder visual automation | Salesforce | Overkill for 5 categories |
| 4 | Strategy Builder for NBA | Salesforce | Templates in ui_copy.json |
| 5 | Skill-based routing across agents | HubSpot Enterprise | 1–2 person office |
| 6 | Conditional SLAs by customer tier | Salesforce | One service level |
| 7 | Multi-brand messenger deployment | Intercom | Single broker brand |
| 8 | AppExchange integration marketplace | Salesforce | Zero integrations v1 |
| 9 | Sandbox org provisioning | Salesforce | Postgres + product_only |
| 10 | Enterprise admin certification path | All | Andy is founder-operator |

---

## Category B — Admin-Heavy Workflows (11–20)

| # | Anti-pattern | Source | Why reject |
|---|--------------|--------|------------|
| 11 | Ticket type schema admin UI | Intercom | Hardcode 5 insurance types |
| 12 | Trigger/macro admin console | Zendesk | 5 macros in config JSON |
| 13 | Routing rule builder | Zendesk | One queue sufficient |
| 14 | Custom field admin per org | All | Fields in triage.py |
| 15 | Workflow approval chains | Enterprise | Chen Kui decides alone |
| 16 | Role-based permission matrix | Enterprise | No auth in pilot |
| 17 | Audit log export compliance suite | Enterprise | Observation log enough |
| 18 | Knowledge base CMS with approvals | HubSpot | RAG corpus separate |
| 19 | Multi-language KB management | HubSpot | ZH + EN paste sufficient |
| 20 | Ticket form designer | Zendesk | Message-first, not forms |

---

## Category C — Features Requiring Large Teams (21–30)

| # | Anti-pattern | Source | Why reject |
|---|--------------|--------|------------|
| 21 | Foundation model training team | Zendesk | Use API models |
| 22 | 20B ticket corpus | Zendesk | Can't replicate |
| 23 | Per-org ML retraining pipeline | Salesforce Einstein | Rules + battery |
| 24 | Voice AI 60 languages | Zendesk | Text/WeChat wedge |
| 25 | Omnichannel ingestion (social, SMS) | Zendesk | WeChat paste simulates |
| 26 | IVR call center | HubSpot | Out of scope |
| 27 | Live chat widget ecosystem | Intercom | Broker shares URL |
| 28 | In-app product analytics | Intercom | Not SaaS product |
| 29 | Proactive outbound campaigns | HubSpot | Inbound only |
| 30 | Developer API platform | Stripe | Intake API exists |

---

## Category D — Expensive Infrastructure (31–40)

| # | Anti-pattern | Source | Why reject |
|---|--------------|--------|------------|
| 31 | Outcome-based AI billing infrastructure | Zendesk | Manual invoice |
| 32 | Resolution verification AI model | Zendesk | Human verifies |
| 33 | Multi-region data residency | Enterprise | US-only pilot |
| 34 | Dedicated IDP cluster | InsurGrid | Vision API on demand |
| 35 | Real-time websocket fanout | Intercom | Polling OK for pilot |
| 36 | Elasticsearch for ticket search | Zendesk | Postgres + queue |
| 37 | Kafka event bus | Enterprise | Direct API |
| 38 | Multi-tenant isolation layer | SaaS | Single broker |
| 39 | CDN edge for messenger | Intercom | Vercel sufficient |
| 40 | GPU cluster for OCR | IDP vendors | Google Vision API |

---

## Category E — Low ROI for Pilot (41–50)

| # | Anti-pattern | Source | Why reject |
|---|--------------|--------|------------|
| 41 | CSAT survey after every case | Zendesk | Day 7 testimonial |
| 42 | Customer satisfaction AI scoring | All | n=1 broker |
| 43 | Agent performance leaderboard | Zendesk | No team |
| 44 | Gamification badges | HubSpot | Wrong culture |
| 45 | Public status page | Enterprise | WeChat updates |
| 46 | Community forum | All | WeChat is forum |
| 47 | Chatbot builder no-code | Intercom | Triage engine IS bot |
| 48 | A/B test framework in product | Growth | Scripts sufficient |
| 49 | Stripe billing integration | Pilot scope | Zelle manual |
| 50 | P17 platform / SearchForge lab | Internal | Constitution blocked |

---

## Honorable mentions — tempting but wrong timing

| Idea | Why wait |
|------|----------|
| Customer tab on trial URL | After broker paste path proven |
| Primary OCR upload-first intake | Constitution frozen |
| PDF IDP pipeline | Screenshot sufficient |
| WeChat official API integration | Paste wedge works |
| Multi-broker tenancy | After first payment |
| LLM generation for all fields | Rules + snippets suffice |
| Full activity timeline UI | Append CTA first |
| SimulationAssistant.tsx | Delete; use ScenarioReplayTab |

---

## Decision filter (use on every future idea)

```
                    ┌─────────────────────────┐
                    │ Does it help transform  │
                    │ messy comm → office-    │
                    │ executable case faster? │
                    └───────────┬─────────────┘
                          NO    │    YES
                    ┌───────────┴─────────────┐
                    ▼                         ▼
                 REJECT              ┌─────────────────┐
                                    │ Can 1 dev ship   │
                                    │ in ≤1 week?      │
                                    └────────┬─────────┘
                                        NO   │   YES
                                    ┌────────┴────────┐
                                    ▼                 ▼
                              DEFER / NEVER      BUILD / REVIVE
```

---

## What P16-Z0 already said not to rebuild (still valid)

1. Multi-turn microservice — use triage_conversation
2. Case intelligence microservice — use triage.py + case_draft_engine
3. OCR pipeline from scratch — use image_input_pipeline
4. Stripe in-app billing
5. P17 platform
6. Customer portal from scratch — CustomerEntryTab exists
7. New add-car battery — use guardrail + p16y

---

*End of P16-Z2 Phase 7 — Top 50 Do Not Copy*
