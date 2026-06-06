# P16-Q Phase 6 — Skeptical Broker Simulation

**Date:** 2026-06-01  
**Persona:** Broker who uses **WeChat only** today — no relationship with founder  
**Method:** Try to reject the product; Production + Preview cold paths + WeChat workflow comparison  
**Goal:** Top 20 objections a skeptical broker would raise

---

## Setup

I am a California auto broker. My office runs on WeChat groups, voice notes, and carrier portals. Andy sends me a "productivity tool" link. I have **zero** obligation to be polite.

---

## Top 20 Objections

| # | Objection | Severity | Evidence |
|---|-----------|----------|----------|
| 1 | **"The link asks me to log into Vercel — is this malware?"** | Critical | Preview HTTP 401 + SSO nonce |
| 2 | **"Why am I on a customer page asking me to add a car?"** | Critical | Production default tab + Add-Car chrome |
| 3 | **"I already read messages in WeChat — paste is double work."** | Critical | No WeChat sync; manual copy |
| 4 | **"Who else pays for this? Show me a real broker."** | Critical | Zero paying customers logged |
| 5 | **"What does $49 buy that my assistant can't do?"** | High | No on-screen pricing at product entry |
| 6 | **"The draft is in English — my clients are Chinese."** | High | API/browser path on mixed threads |
| 7 | **"场景仿真 — am I in a test environment?"** | High | Production shows simulation tab |
| 8 | **"Four tabs — which one is real?"** | High | Full dev chrome on Production |
| 9 | **"Does this auto-send to my clients?"** | High | Must read trust copy; not obvious on old bundle |
| 10 | **"Where is my data stored? HIPAA? Insurance regs?"** | High | No legal/compliance footer in product |
| 11 | **"It took 30 seconds — WeChat is instant."** | Medium | Triage latency copy |
| 12 | **"Empty queue — broken?"** | Medium | First open before paste/demo |
| 13 | **"Why Chen Kui's name on my tool?"** | Medium | White-label not available |
| 14 | **"I need phone — this is desktop web."** | Medium | No mobile proof |
| 15 | **"Another login someday?"** | Medium | Vercel today; no product auth story |
| 16 | **"Add-car buttons — I handle cancellations all day."** | Medium | Wrong wedge on Production |
| 17 | **"演示队列 — I'm not training your AI."** | Medium | Demo card visible |
| 18 | **"Case ID looks like a database key."** | Low | Monospace IDs |
| 19 | **"Dark header looks like a developer dashboard."** | Low | App shell vs white island |
| 20 | **"When you shut down, I lose my queue."** | Low | No export story; vendor lock-in fear |

---

## Objection clusters

```
Access (1, 2, 8)     → "Can't even start"
Workflow (3, 6, 11)  → "Slower than WeChat"
Trust (4, 5, 9, 10) → "Not a real product company"
Pilot smell (7, 13, 17, 19) → "Lab, not SaaS"
```

---

## Skeptical broker verdict

**Would sign up:** **NO**  
**Would take a second call:** **Only if** founder screen-shares working paste on **my** message  
**Would pay:** **NO** without peer proof + stable URL

**Overall skeptical broker score: 32 / 100**

---

## What would NOT convince this persona (avoid sales talk)

- Capability scorecards from founder sprints  
- Guardrail PASS logs  
- "P16-O raised customer entry to 79" — **not deployed**  
- Stripe comparisons in docs

**Would convince (reality only):**

- Public broker URL, no login, paste → Chinese draft → copy in &lt;60s on **their** cancellation screenshot  
- One named broker saying "I paid $49"  
- Terms + invoice in the same email as the URL

---

*End of P16-Q Phase 6 — Skeptical Broker Simulation*
