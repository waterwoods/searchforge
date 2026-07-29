# Founder Product Codex v1.0

**Product:** California Auto Insurance Broker Assistant / Unified Intake / Insurance Task Platform  
**Audience:** Future Founder · Investors · Engineers · Customers · Employees · Interviewers  
**Status:** Living founder reference — not a sprint report, not a changelog  
**Date:** 2026-07-24  
**Governing North Star:** `docs/product/p20_product_north_star.md`  
**Runtime truth:** `docs/CURRENT_PRODUCT_SHAPE.md`  
**Decision law:** `docs/product/decision_log.md`

---

> This Codex extracts **why** we built the product this way.  
> It turns months of loops into a reusable methodology.  
> Read it to build the next product without starting from zero.

---

## 1. Executive Summary

### What is this product?

An **Insurance Task Platform** for California auto insurance broker offices — especially offices serving Chinese-speaking customers.

It has two faces:

| Face | Who | What they get |
|------|-----|----------------|
| **Customer** | Policyholder after an accident | A WeChat Mini Program that asks for one clear next step at a time |
| **Broker** | 陈总 / office staff | A Workbench where messy intake becomes one structured, sourced case |

We are not building a carrier system, a full CRM, a chatbot demo, or an agency OS.

We are building:

> A server-driven task system that turns fragmented customer input into a durable service record the broker can understand in about ten seconds — while the customer never feels lost.

### What problem does it solve?

Insurance offices live in WeChat chaos:

- Urgent cancellations buried under “hi” messages  
- Customers re-sending photos the office already has  
- Brokers rewriting the same reply from scratch  
- Accident customers who do not know what to do next  

The product solves **cognitive load under stress** on both sides:

- Customer: one active matter, one next action, trust that nothing was lost  
- Broker: structured case, evidence, timeline, draft — then human control before anything leaves the office  

### Why does it exist?

Because the market already has chat, forms, and portals — and they still fail at the moment that matters:

> After an accident, or under policy pressure, people need calm progress — not more options.

This product exists to own that moment for the broker’s customers, then hand a clean case to the office.

中文意图：我们不是在做“更多功能的保险软件”，而是在做“事故后不慌、办公室不乱”的任务系统。

---

## 2. Founder Story

### Why did this project begin?

It began as SearchForge — retrieval, demos, platform experiments.  
It became a product when the founder chose a **paid pilot wedge** over lab completeness:

1. Find a real broker with real daily pain  
2. Ship the smallest system that reduces that pain  
3. Prove value with use and payment — not architecture slides  

The early promise was simple: paste a messy message → get a structured case → keep follow-up continuity.

Over time the product matured from “inbox triage for the broker” into “customer-first claim intake + broker workbench,” still governed by the same commercial discipline: **pilot before platform**.

### Why insurance?

Insurance is a **workflow + trust** business:

- High stakes, high emotion, low tolerance for “where did my photo go?”  
- Brokers already sit between carrier complexity and customer confusion  
- Chinese-speaking California auto brokers have a clear channel (WeChat) and a clear pain (message chaos)  

Insurance also teaches the durable product lesson:

> Complexity belongs inside the system. Calm belongs to the user.

That lesson transfers to healthcare intake, legal matter opening, mortgage document chase — any domain where a stressed human must complete steps for a professional who must decide.

### Why WeChat Mini Program?

Because that is where the customer already is.

For this market:

- The broker relationship lives in WeChat  
- Login walls kill completion  
- A Mini Program can feel like a calm task app without pretending to be a consumer brand portal  

H5 prototypes taught structure. Mini Program became the production customer surface because **channel fidelity beats framework preference**.

WeChat is not the moat.  
**Continuity + trust + broker control** is the moat. WeChat is the distribution door.

### Why Chen (陈奎 / 陈总) as the first Pilot?

Chen is not a “logo customer.” Chen is a **reality teacher**.

| Why Chen | What it forced |
|----------|----------------|
| Real office traffic | Cancellation urgency, missing docs, add-car, claim — not toy scenarios |
| Chinese + English mix | Language must be broker-native, not engineer-native |
| WeChat-first workflow | Product must respect copy-paste, resume, and human send |
| Trust-sensitive buyer | Engineer chrome, localhost demos, and vague promises fail Day 1 |
| Single-office pilot | Forced focus: one broker done well beats ten imagined tenants |

Pilot rule learned with Chen:

> Stop adding features before one broker completes a real week with logged evidence.

中文意图：陈总不是销售案例，是产品老师。先把一个办公室做对，再谈平台。

---

## 3. North Star

**One sentence that should never change:**

> We optimize the customer journey, not the feature count. Build the simplest system that reliably solves the user’s problem. Smoothness first; complexity only when proven necessary.

中文：

> 我们优化的是用户旅程，不是功能数量。先做最简单、能稳定解决问题的系统。先保证丝滑；只有真实需求证明必要时，才增加复杂度。

Everything else — constitutions, gates, loops, architecture — exists to protect this sentence.

---

## 4. Customer Philosophy

### One Active Case

A customer has at most one Active Case in progress.

**Why:** After an accident, “which matter am I in?” destroys trust. Continuity is the product. Case pickers feel like power; they feel like abandonment under stress.

Server identity (durable person link) enforces this — client tokens alone are not Constitution.

### Customer should never feel lost

Every screen must answer:

1. Where am I?  
2. What do I do next?  
3. Did what I just did count?  

**Why:** Lostness is the silent churn. Customers do not file bug reports; they message 陈总 in panic, or stop.

### One clear next action

One Task. One Status. One Next Action. One primary CTA.

**Why:** Choice overload turns customers into case managers. Task products win because motion is singular.

### Today First + Why + After

- **Today First:** exactly one “today’s focus”  
- **Why:** one human reason this step matters now  
- **After:** one concrete next consequence (e.g. 陈总开始审核)  

**Why:** Checklists create anxiety. A reason and an outcome create calm progress.

### Customer first

The customer can start without becoming an account holder. Formal handoff still requires enough contact truth for the office to act.

**Why:** Brokers already know people by phone and WeChat. The product should not invent a consumer login religion before the first useful submit.

### Trust before efficiency

Read-after-write. No silent overwrite of customer-confirmed facts. No auto-send to carriers. Broker decides.

**Why:** Speed without trust is a demo. Trust without speed is a portal nobody finishes. We take trust first, then compress steps.

### Waiting is a real state

When the customer owes no work, they see Case Status (“陈总正在审核”), not a dead Task Home that says “先不用操作” with no meaning.

**Why:** Empty productivity screens feel broken. Waiting with a named human feels alive.

中文意图：客户记住的是“我有没有慌”，不是 API。

---

## 5. Workflow Philosophy

### Append First, Split Later

Ordinary facts, photos, and supplements attach to the current Active Case. Split/merge/archive is broker/office work later.

**Created because:** Asking “same accident or new?” on every upload forces taxonomy onto a stressed human.  
**Solved:** Retention without premature classification. Brokers can split with context; customers should not run intake ontology.

### Capability before Integration

Build Lookup → Prefill → Smart Claim Start as **capabilities with contracts and mocks** before live AMS/CRM wiring.

**Created because:** Integration projects absorb months and teach little about UX truth.  
**Solved:** Product shape can be proven with mock scenarios; real CRM becomes a adapter swap, not a rewrite.

### Pilot before Platform

Single broker, manual payment, product-only surface, Postgres truth — before multi-tenant OS dreams.

**Created because:** Platform work feels like progress while no customer is done.  
**Solved:** Commercial learning loop: demo → trial → fix-now → payment or kill reasons.

### Small loops (Production Loop)

One narrow user-facing objective → minimum change → tests → Founder/Broker/Customer evaluation → fix P0/P1 → deploy QA → Founder QA → stop.

Rules: at most three automated loops; never auto-start the next capability; three failed loops with unresolved P0 = **BLOCKED**.

**Created because:** Multi-objective sprints hide failure and inflate scope.  
**Solved:** Controllable progress with an explicit stop condition.

### Founder Reality Walk

Founder walks the real Golden path on real devices/hosts — one token, one Camry case, full customer + broker journey — before calling anything production-ready.

**Created because:** Prototype confidence is a liar. Environment mismatch (QA write / Production read) creates false GO.  
**Solved:** One acceptance story that a non-engineer founder can run without Cursor.

### Release Gates

Hard gates over soft opinions: Read-after-write, One Task/State/Next Action, Form Gate, Entry/Navigation Gate, Mini Program Build Gate, Golden Production QA, Capability Done Means User Done.

**Created because:** Scorecards without blockers ship pretty failures.  
**Solved:** Reliability and smoothness become merge law, not taste.

### Document-driven development

Direction locks in constitutions and decision logs before code thrash.

**Created because:** Agent-assisted coding without product law re-litigates settled decisions every week.  
**Solved:** Future engineers and AI assistants inherit why, not only what.

### Complexity Stays Inside

Tokens, projections, aggregate versions, capability labels, OpenIDs — never normal UI.

**Created because:** Engineer chrome destroys broker trust in the first five minutes.  
**Solved:** Professional calm as a product feature.

---

## 6. Product Architecture

Responsibilities only — not implementation.

```text
Customer
   ↓
WeChat Mini Program          ← calm task surface; one next action
   ↓
Cloud Run API                ← product-only intake + customer task APIs
   ↓
Cloud SQL (Postgres)         ← durable cases, sessions, active-case binding
   ↓
Broker Workbench             ← queue, case brief, request more, close
   ↓
Timeline                     ← append-only history of what happened
   ↓
Evidence                     ← durable photos/docs bound to the case
```

| Layer | Responsibility |
|-------|----------------|
| **Customer** | Provide facts and evidence under stress; never manage office workflow |
| **Mini Program** | Present one task/status/next action; capture; resume; show waiting |
| **Cloud Run** | Enforce product law: identity, One Active Case, validation, projections |
| **Cloud SQL** | Source of durable truth for paid pilot; multi-instance safe |
| **Broker Workbench** | Understand case fast; request more; close to history; never auto-send |
| **Timeline** | Auditable “what happened” — supports trust and support |
| **Evidence** | Durable attachments with case binding — nothing silently lost |

Surrounding product truths:

- **Server is final authority** for workflow state and Active Case  
- **AI assists; workflow + human decide**  
- **Feature flags** keep mock capabilities off production until Founder GO  

---

## 7. Technical Architecture

High-level only.

### Frontend

- **Customer:** WeChat Mini Program (`miniapp/`) — native packaging, Build Gate before Preview QA  
- **Broker:** React/Vite Workbench (`ui/`) — Unified Intake / document-intake surfaces on Vercel  

### Backend

- FastAPI service on **Cloud Run**  
- Product-only mode for pilots (`UNIFIED_INTAKE_PRODUCT_ONLY`) — lab routers stay out of the paid surface  

### State

- Postgres holds cases, sessions, active-case index, timeline, evidence metadata  
- Client holds resume UX helpers; **not** constitutional truth  
- Projection pattern: Constitution / plan → customer Task Home view model → broker detail  

### Feature Flags

- Capability mocks (e.g. customer lookup) default **OFF** in production  
- Flags exist so Pilot polish and Golden QA stay honest while future prefill is developed  

### Timeline

- Append-only historical audit  
- Distinct from current-state projection (state answers “now”; timeline answers “how we got here”)  

### Shared Services

- Intake triage, customer claim/task APIs, support export perimeter, readiness (`/readyz`)  
- Identity: lightweight durable person link for Mini Program — not a full account platform  

### Deployment

| Piece | Where |
|-------|--------|
| API | Cloud Run |
| DB | Cloud SQL Postgres |
| Broker UI | Vercel |
| Customer | WeChat Mini Program → Cloud QA / Production API profiles |

### Why this scales

- **Channel adapters** (Mini Program, Workbench, future WeCom) sit on one case spine  
- **Capability contracts** (Lookup / Prefill / Start plan) let CRM arrive without UX rewrite  
- **Tenant later:** one office proven → configuration and isolation, not a second product  
- **Product-only perimeter** keeps R&D from contaminating pilot reliability  

中文意图：架构的目标不是炫技，是让未来换 CRM、加租户、换行业时，不必推翻客户旅程。

---

## 8. Evolution Timeline

```text
Prototype
   ↓
Capabilities
   ↓
Integration
   ↓
Pilot Polish
   ↓
Founder Reality Walk
   ↓
Pilot
   ↓
Platform
```

| Stage | What changed |
|-------|----------------|
| **Prototype** | SearchForge / H5 / demo queues. Proved “messy message → case” and broker draft value. Learned what not to promise (auto-send, full CRM). |
| **Capabilities** | Customer First Add-Car, then Claim Intake as flagship vertical. Constitutions locked: One Active Case, Append-first, Today First, Why/After, One Truth. Mini Program became customer surface. |
| **Integration** | Server-authoritative resume, default intake plan without broker gate, Request More, evidence, Close → History, Workbench unification. Read-after-write became law. |
| **Pilot Polish** | Language, continuity, CTA clarity, waiting state, contact consistency — smoothness without new features. UX score treated as a product metric. |
| **Founder Reality Walk** | Golden Production QA: one token, one Camry case, customer + broker, real hosts. Prototypes banned as acceptance substitutes. |
| **Pilot** | Chen office path: product-only deploy, Postgres, trial observation, fix-now queue, manual payment. |
| **Platform** | *Future.* Multi-broker, multi-tenant, real AMS/CRM, second industry — only after pilot truth, not before. |

Key mindset shift across stages:

> From “can we demo it?” → “can a stressed stranger finish without us?” → “can the founder certify production without Cursor?”

---

## 9. Major Decisions

### Why One Active Case?

Stress + continuity. Multi-case portals optimize for power users; accident intake optimizes for motion. Server enforcement survived storage clear and new devices — client-only guards did not.

### Why not CRM first?

CRM is a graveyard of integrations. Brokers buy **time and calm**, not another system of record they must migrate into. We create a trustworthy service record first; CRM becomes a consumer of that record later.

### Why mock before integration?

Mock scenarios force the UX contract (MATCH_FOUND, multi-vehicle confirm, stale policy, unavailable) before AMS politics begin. Capability Done means the **customer journey** is designed and testable — not that EZLynx returned 200.

### Why server as source of truth?

Clients lie, clear storage, race, and go stale. Constitutional rules (One Active Case, Close, Waiting vs Action Needed) only work if the server owns them.

### Why Mini Program first (for customers)?

Channel is reality. The customer will not install our brand app to send VIN photos to 陈总. Meet them where trust already exists.

### Why capability design?

One Capability, One Responsibility. Lookup answers “who is this?” Prefill answers “what can we fill?” Smart Claim Start answers “how do we present Start Claim?” Mixing them creates untestable blobs.

### Why customer journey over feature count?

Feature count is founder vanity. Journey completion is broker revenue and customer trust. The North Star makes this non-negotiable.

### Why Golden Production QA only?

Multiple QA paths produced false confidence. One Token → One Case → One Truth is the only founder-operable release question.

### Why broker never loses control?

Nothing auto-sends. AI drafts; humans approve. That is not a limitation — it is the purchase condition for regulated, reputation-sensitive offices.

### Why “Capability Done Means User Done”?

Merged PRs and green CI do not equal a finished product. Without Founder/manual evidence, we ship theater.

---

## 10. Lessons Learned

### Technical

- Dual write paths and JSON fallbacks create silent authority bugs — **one persistence truth** for pilot  
- Client resume tokens are UX; durable identity is Constitution  
- Environment mismatch (QA vs Production Workbench) wastes more founder time than code bugs  
- Build Gate / packaging failures (`wx://not-found`) are release blockers, not nitpicks  

### Product

- Waiting must be designed as a state, not leftover copy  
- Pause language matters: “先离开，稍后再继续” ≠ “稍后再填” ≠ done  
- Default intake cannot depend on broker Request More, or first-time users land in empty waiting  
- Engineer wording (“自动回读服务器”) breaks trust instantly  

### Founder

- Trial-ready scripts ≠ broker-ready UI  
- Obsess over the first five minutes  
- Stop feature work until one broker week is logged  
- Hide pricing and you stall Day 3; hide promises and you keep trust  

### Customer

- Customers remember feelings, not APIs  
- Under stress, one next action beats ten accurate options  
- “Did it count?” anxiety needs After-lines and receipts, not more status chips  

### Team / AI

- Constitutions + Decision Log prevent AI assistants from re-arguing settled law  
- Small one-objective loops beat epic multi-agent thrash  
- Document-driven development is how a small team stays coherent with high AI throughput  

### What we would do differently

1. Enforce **server Active Case identity** earlier — before client-token mythology  
2. Name **Claim Vehicle vs Add Car** on day one of language law  
3. Make **Golden Production QA** the only acceptance path earlier  
4. Treat **Founder Reality Walk hosts** as part of the product, not tribal knowledge  
5. Separate **lab SearchForge** from **product-only** surface sooner in operator docs  

---

## 11. Future Roadmap

| Horizon | Focus |
|---------|--------|
| **Near-term** | Pilot polish continuity; Founder GO on physical Preview; no new feature theater |
| **Pilot** | Chen real usage; observation log; fix-now top frictions; payment or kill reasons |
| **Real CRM / Lookup** | Replace mock directory with AMS adapter behind Cap 01 contract |
| **Real Prefill** | Cap 02 against live policy/vehicle truth; confirm gates stay human |
| **Automation** | Still broker-controlled; automate gathering and drafting, not sending and deciding |
| **AI** | Extract, classify, summarize, draft — never advance authoritative workflow alone |
| **Multiple Brokers** | Second office only after first testimonial and support posture holds |
| **Multi-tenant** | Tenant config + isolation after single-tenant operational excellence |
| **Second Industry** | Reuse task spine (intake → evidence → professional review) — new vertical constitution |
| **Platform** | Workflow operating model sold as reusable product — not a rewrite of Pilot |

Rule for every row:

> Do not promote a horizon until the previous horizon produced user-done evidence.

---

## 12. Business Vision

### As SaaS

A paid broker office product:

- Customer Mini Program intake  
- Broker Workbench  
- Durable cases and evidence  
- Manual → then simple billing  

Success metric early: **minutes saved + cases completed + broker retention**, not MAU vanity.

### As a workflow platform

A reusable pattern:

```text
Stressed submitter
  → one active matter
  → structured tasks + evidence
  → professional workbench
  → human decision boundary
```

Insurance Claim Intake is vertical #1. The platform is the **task + trust spine**.

### As a reusable operating model

What transfers beyond this repo:

- North Star + Production Loop  
- Constitutions + Decision Log  
- Capability-before-integration  
- Golden acceptance story  
- Founder Reality Walk  
- Pilot-before-platform commercial sequence  

### Beyond insurance

Same spine, new constitutions:

| Domain | Stressed user | Professional | Matter object |
|--------|---------------|--------------|---------------|
| Healthcare | Patient intake | Clinic staff | Visit / referral packet |
| Legal | Client matter open | Paralegal / attorney | Matter file |
| Real estate | Buyer/seller docs | Agent / TC | Transaction checklist |
| HR | Employee onboarding | People ops | Employee packet |
| Government | Applicant | Caseworker | Benefit case |
| Financial services | Applicant | Advisor / ops | Account opening file |

Expansion rule:

> Keep the feelings. Replace the vocabulary. Do not copy the insurance UI.

---

## 13. Interview Story

**(≈10 minutes for a hiring manager)**

I founded and drove an insurance task product for California brokers serving Chinese-speaking customers. The job was not “build AI.” The job was **make a stressed customer finish the next step, and make a broker understand the case in ten seconds**.

**Leadership.** I locked a North Star — journey over feature count — and enforced it with constitutions, decision logs, and release gates so a small team (and AI coding agents) could not drift into platform fantasy.

**Architecture.** We separated customer Mini Program, Cloud Run product API, Postgres truth, and Broker Workbench. Server owns One Active Case and workflow state. Timeline and evidence are durable. AI assists; humans decide. That boundary is how you stay auditable.

**AI.** We use models where they reduce chaos — triage, extraction, drafts — and forbid them from advancing authoritative state or auto-sending. The moat is conversational recovery + durable case memory + human gate, not chatbot theater.

**Product thinking.** Principles like Append-first/Split-later, Today First, Why/After, and Waiting-as-a-state came from founder walks with real accident flows — not from competitor screenshots.

**Execution.** We run three-loop max production cycles with one objective, Golden Production QA (one token, one case, full journey), and “Capability Done Means User Done.” We ship pilot polish before CRM integration.

**Tradeoffs.** We chose Mini Program over brand app, mock capabilities before AMS, single-broker pilot before multi-tenant, manual payment before Stripe. Each tradeoff optimized for learning speed and trust, not completeness.

That’s the story: **product law + calm UX + durable truth + controlled AI**, proven toward a real broker pilot.

---

## 14. Investor Story

**(≈10 minutes for an investor)**

**Market.** Independent insurance brokers — especially bilingual offices — run high-stakes workflows inside chat. Labor is expensive; mistakes are reputational; carriers are not going to fix the broker’s customer experience.

**Problem.** Message chaos. Re-asking. Lost photos. Slow first response after accidents. Tools exist (CRM, email, portals) but none own the **stressed handoff moment** between customer and broker.

**Solution.** An Insurance Task Platform: Mini Program for customers, Workbench for brokers, durable case spine in the cloud. One active matter. One next action. Structured evidence. Broker control before send.

**Moat.** Not “we have GPT.” Moat is:

1. Channel-native continuity (WeChat reality)  
2. Product constitutions that keep UX calm as features grow  
3. Server-authoritative case truth + timeline/evidence  
4. Capability contracts that absorb CRM without rewriting the journey  
5. Founder operating system (gates, Golden QA, pilot loop) that compounds  

**Execution.** We already moved from lab demo → customer claim intake → server identity → pilot polish with explicit GO/NO-GO discipline. We sell progress as **user-done evidence**, not roadmap slides.

**Future expansion.** First: dominate claim intake for offices like Chen’s. Then: real CRM adapters, multi-broker, multi-tenant. Then: replicate the operating model into adjacent professional workflows. Insurance is the wedge; **trustworthy task intake** is the category.

Ask: we are not raising to invent more features. We are raising to **finish pilot truth and replicate the office**.

---

## 15. Reusable Framework

### Universal pattern (any workflow product)

```text
1. Name the stressed user and the professional
2. Define one Active Matter rule
3. Design one Next Action surfaces
4. Append evidence first; classify later
5. Put state authority on the server
6. Give the professional a 10-second brief
7. Keep a human decision boundary
8. Accept only through one Golden journey
9. Pilot one real office before platform
10. Extract constitutions so AI/engineers cannot drift
```

### Reusable layers

| Layer | Reuse |
|-------|--------|
| North Star | Journey > features; smoothness first |
| Customer philosophy | One matter, one action, trust before efficiency |
| Workflow philosophy | Append-first, capability-before-integration, small loops |
| Product spine | Submitter surface → API → durable store → professional workbench → timeline/evidence |
| Capability pattern | Contract + mock + flag + later adapter |
| Acceptance | Golden path; Founder Reality Walk; User Done |
| Commercial sequence | Demo → supervised trial → fix-now → pay/kill → second customer |

### Industry swap checklist

1. What is the Active Matter?  
2. What is Today’s Focus under stress?  
3. What must never be customer-visible complexity?  
4. What may AI suggest vs decide?  
5. What is the professional’s “10-second understand” artifact?  
6. What is the human send/approve boundary?  
7. What is the one Golden acceptance story?  

If you cannot answer these, you are not ready to write code for that industry.

---

## 16. Founder Principles

Principles that should still be true in five years:

1. **Customers remember feelings, not APIs.**  
2. **One next action beats ten options.**  
3. **Trust is part of the product.**  
4. **Pilot teaches more than speculation.**  
5. **Architecture should make future change easier — not impress today.**  
6. **Optimize the journey, not the feature count.**  
7. **Smoothness first; complexity only when proven necessary.**  
8. **Complexity stays inside; calm stays outside.**  
9. **Server is final authority; clients are guests.**  
10. **Append first; split later.**  
11. **Capability before integration.**  
12. **Pilot before platform.**  
13. **AI assists; workflow and humans decide.**  
14. **Capability Done means User Done.**  
15. **One Golden acceptance story — prototypes are not production proof.**  
16. **Waiting is a designed state, not empty UI.**  
17. **Never request what the customer cannot complete.**  
18. **Read-after-write or it didn’t happen.**  
19. **Document the why, or the team will re-litigate forever.**  
20. **Stop when the loop passes — do not invent the next capability out of momentum.**  
21. **Sell control to professionals; sell calm to customers.**  
22. **A second industry reuses the spine, not the screenshots.**

中文总原则：

> 先让一个真实的人，在真实的压力下，走完下一步。  
> 再谈平台、租户、和下一行业。

---

## How to use this Codex

| Reader | Use |
|--------|-----|
| **New engineer** | Read §§1, 3–7, 9 — then `CURRENT_PRODUCT_SHAPE.md` + `AGENTS.md` |
| **Hiring manager** | §13 (+ §3 and §9) |
| **Investor** | §14 (+ §§1, 11–12) |
| **Founder (next product)** | §§3–5, 15–16 — copy the framework, replace the vertical |
| **Employee / customer-facing** | §§1–4, 12 — language of promise and non-promise |

**Related living law (do not duplicate here):**

- North Star: `docs/product/p20_product_north_star.md`  
- Decision Log: `docs/product/decision_log.md`  
- Production Constitution: `docs/design/p20_production_constitution_master_design_2026_07_12.md`  
- Runtime: `docs/CURRENT_PRODUCT_SHAPE.md`  
- Founder ops path: `docs/FOUNDER_ONE_PATH.md`

---

## Document control

| Version | Date | Notes |
|---------|------|-------|
| **v1.0** | 2026-07-24 | First Founder Product Codex — methodology extraction from P16–P20 / Pilot path |

**Change rule:** Amend when product law changes (new North Star clause, superseded Decision Log entries, or a new commercial stage begins). Do not turn this into a sprint diary.

---

*End of Founder Product Codex v1.0*
