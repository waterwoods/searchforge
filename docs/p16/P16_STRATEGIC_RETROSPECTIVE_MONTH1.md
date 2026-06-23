# P16 Strategic Retrospective — Month 1

**Date:** 2026-06-21  
**Scope:** P16 Add-Car Intake — conversation-first → document-first pivot  
**Audience:** Founders, product, broker pilot stakeholders  
**Tone:** Brutally honest. Strategic, not code-focused.

---

## Month 1 Timeline

| Period | What happened | Dominant mental model |
|--------|---------------|----------------------|
| **Early June (Z2.5)** | North star: *"Transform messy customer communication into an office-executable case — in one paste, under one minute."* Roadmap prioritized multi-turn continuity, append path, broker paste workflow. | **Broker paste → structured case** |
| **Jun 6** | Pre-pilot stress test: **33/33 conversation scenarios PASS**. Append integrity PASS. Chen Kui founder review: 81/100. Verdict: proceed to pilot. | **Conversation simulation = readiness** |
| **Jun 7** | Customer First Constitution shipped. Phone as return key. Progress = missing fields. One active case per phone. Customer entry still routes through conversational collecting. | **Customer chat + constitution rules** |
| **Jun 7–16** | Case memory fixes, phone lookup, customer tab, visibility surfaces. Engineering effort on conversation persistence, triage continuity, status truth. | **Make the chat loop durable** |
| **Jun 17** | **Decision Freeze V1.** Product reframed: *Customer Docs → Trusted Packet → Broker.* Upload-first flow spec. OCR accuracy corpus built. Trust Layer sprint begins. | **Document-first pivot declared** |
| **Jun 18–19** | 72-hour pilot build. Trusted Packet UI. HEIC validation. OCR kill tests on 22-doc corpus. CK dry-run prep. | **Extraction + packet = product** |
| **Jun 20** | Request Framework frozen. READY / NEED_INFO / BROKER_REVIEW ADR. 7-screen customer blueprint. 4-day build plan. | **Readiness engine, not chatbot** |
| **Jun 21** | Real-world document validation on QA deployment. State machine: **4/5 PASS**. Happy path (READY): **FAIL** — VIN extraction unreliable on purchase agreement PDFs. | **Documents are right input; extraction is the bottleneck** |

**The pivot was real, not cosmetic.** By mid-month the team was still measuring success by conversation simulation scores. By month-end the product definition, demo script, and broker value prop all assumed uploaded documents as the primary input.

---

## Original Hypothesis

At the start of Month 1, the team believed:

1. **Add-car intake is a conversation problem.** Customers arrive with fragmented messages; the product's job is to ask the right questions and collect missing fields over multiple turns.

2. **The broker workflow is paste-first.** Chen Kui copies WeChat threads into the system; AI triages, classifies urgency, and assembles Collected / Still Needed. The customer-facing surface can mirror this pattern.

3. **Multi-turn continuity is the moat.** Append path, case memory, return-later behavior — if VIN doesn't disappear when the customer sends their name two days later, the product wins.

4. **Simulation gates predict pilot success.** 33/33 realistic SoCal Chinese customer scenarios, 6.2 min/case simulated savings, append battery PASS — these were treated as strong evidence the product was ready for Chen Kui.

5. **Customer self-serve is a parallel front door to broker paste.** Same engine underneath: text in → structured case out. Customer First means the customer can also type instead of waiting for the broker to paste.

6. **The office's job is to understand a case, not re-read documents.** True — but the team interpreted "case" as a conversation summary, not an evidence packet.

7. **LLM strength = understanding messy language.** Bilingual WeChat, partial sentences, "我买了一辆宝马" — the triage engine was built for this.

---

## What We Learned

### What turned out to be right

- **The wedge is add-car.** Broker pain research confirmed it: frequent, document-heavy, time-wasteful, liability-sensitive (wrong VIN = E&O risk).
- **The buyer is the brokerage, not the customer.** Wu Xiaojie saves time; Chen Kui signs the check when minutes saved are proven.
- **Phone as return key works.** No login. Customers understand it. Constitution rules 1–7 remain valid product law.
- **Progress = missing fields.** Customers and brokers think in "what's still needed," not completion percentages.
- **Three readiness states are enough.** READY / NEED_INFO / BROKER_REVIEW maps to how offices actually work. Brokers don't need twelve statuses.
- **Failure-mode gating is trustworthy.** Wrong documents, partial uploads, VIN conflicts route correctly without silent READY. The state machine earned trust even when extraction didn't.
- **Garaging ZIP upfront eliminates a real fraud exposure.** Forcing ZIP before upload was correct and should not be revisited.

### What turned out to be wrong

- **Customers do not want to chat with an insurance intake bot.** They want to photograph their dealer paperwork and be done. Add-car is a document transaction wearing a conversation costume.
- **Broker paste simulates the problem; it doesn't solve it.** Chen Kui still pastes. Wu Xiaojie still hunts documents in WeChat. The conversation path optimized the broker's triage view, not the office's data assembly.
- **33/33 simulation PASS was a false positive.** Synthetic conversation scenarios proved the triage engine could parse text. They did not prove the product could extract a 17-character VIN from a real purchase agreement PDF.
- **"Collected / Still Needed" from chat is not broker-trusted.** Brokers need source attribution: *VIN from purchase_agreement.pdf*. Chat-derived fields have no provenance and no liability shield.
- **The highest office pain is document hunting, not message parsing.** Wu Xiaojie's 5–10 minutes per case is spent finding the VIN photo in a 40-message thread, not reading the thread's semantic content.
- **WeChat screenshots are documents, not dialogue.** Customers send photos of contracts, VIN plates, and insurance cards. The "conversation" is a transport layer for images.
- **Multi-turn append is necessary but not sufficient.** Continuity matters when a customer returns with another document. It does not replace the need for structured extraction from uploads.

---

## The Conversation Trap

### Why the team spent significant effort on conversation flow

**1. Inherited architecture.** P16 grew out of Unified Intake MVP, whose v1 input model was *"broker provides pasted message text."* The entire `triage.py` engine — thousands of lines of scenario handling, append logic, bilingual parsing — was conversation-native. Sunk cost is real even when unacknowledged.

**2. Simulation success felt like product-market fit.** 33/33 PASS. Append integrity PASS. Founder review scores in the low 80s. Chen Kui said he'd pay $49 *if real cases match simulation*. The team optimized the thing it could measure.

**3. ChatGPT-shaped product thinking.** The team's instinct — and the market's — is that AI products talk. Building a conversational intake felt modern, demoable, and aligned with LLM capabilities. Upload + OCR felt like 2015 InsurTech.

**4. Broker-as-user bias.** Chen Kui's daily workflow is WeChat. The product met him where he was (paste box) instead of meeting Wu Xiaojie where the pain was (document assembly). The broker is the buyer; the office operator is the daily user. We optimized for the buyer's input habit, not the user's output need.

**5. Customer First was misread as Customer Chat.** The constitution correctly defined phone, missing fields, and status visibility. Implementation defaulted to a conversational collecting UI because that was the only intake surface that existed.

**6. Conversation is easier to demo than extraction.** Typing "我买了2024宝马X5" in a simulation produces instant Collected/Still Needed. Uploading a PDF and waiting 60 seconds for extraction — which might return a 16-character VIN — is a harder demo and a harder engineering problem.

### The trap, stated plainly

> **We optimized the interface we knew how to build (chat) instead of the interface the business requires (documents).**

The conversation flow was not wasted — it produced case memory, phone lookup, readiness states, and broker handoff patterns. But it consumed the majority of Month 1 engineering attention while the actual value moment — *VIN appears in clipboard, broker pastes into carrier portal* — remained unproven on real documents until June 21.

---

## The Document-First Discovery

### How the pivot happened

The pivot was not a single meeting. It was a stack of evidence:

| Evidence | What it showed |
|----------|----------------|
| **Broker pain research (Jun 19)** | Pain #4: WeChat document hunting — 5–10 min/case re-reading threads. Pain #7: wrong/missing documents on 1 in 4 add-car cases. The office doesn't need better chat parsing; it needs documents assembled once. |
| **Business reality check** | *"The Chinese insurance brokerage workflow inherited the format of casual conversation… every business transaction must be reassembled manually from an unstructured social chat format."* The problem is format mismatch, not conversation quality. |
| **Decision Freeze (Jun 17)** | Explicit reframe: `Customer Docs → Trusted Packet → Broker`. Upload-first customer flow. Gemini extraction. Source attribution per field. |
| **OCR accuracy corpus (22 docs)** | VIN 80%, YMM 95% on synthetic docs. Imperfect but directionally right. Purchase agreement PDFs are the hard case. |
| **Real-world validation (Jun 21)** | NEED_INFO, wrong-doc, VIN-conflict routing: **PASS**. READY on clean dealer docs: **FAIL**. Documents are the right input; extraction accuracy is the blocker — not the conversation model. |
| **Chen Kui demo script** | The money moment is Copy Packet → paste into AMS. Not "watch the AI understand my WeChat message." |

### Why documents are a better source of truth than chat for Add Vehicle

**1. The fields already exist in documents.** A purchase agreement contains VIN, year, make, model, buyer name, and often ZIP. A WeChat message contains *"我买了新车"* and maybe a blurry photo. Extraction from evidence beats inference from language.

**2. Source attribution is a liability requirement.** Brokers need to know *where* a VIN came from. Chat-derived VINs have no file, no page, no audit trail. Document-derived VINs do.

**3. Customers already have the documents.** They just received them from the dealer. The friction is not "I don't know what to say" — it's "I don't know what to send." Upload-first with a missing-items list solves the actual customer pain (#1 in broker research).

**4. The office's job is data entry, not interpretation.** Wu Xiaojie copies VIN into Mercury/Progressive/Infinity portals. She doesn't need a conversation summary. She needs a packet.

**5. Validation proved routing, not chatting.** Set B (partial WeChat screenshots → NEED_INFO): PASS. Set D (conflicting VINs across two purchase agreements → BROKER_REVIEW): PASS. The system correctly handles document evidence. It does not need to *talk* to the customer to make these judgments.

**6. Chat cannot reliably produce a 17-character VIN.** Customers rarely type VINs correctly in messages. They photograph the door jamb. The document path matches customer behavior; the chat path fights it.

---

## Product Evolution

```
Week 1–2                          Week 3                           Week 4
─────────────────────────────────────────────────────────────────────────────
Broker pastes WeChat text    →    Customer types in chat UI    →    Customer uploads docs
AI triages + collects             Phone lookup + case memory        OCR extracts fields
Collected / Still Needed          Append path + status visibility   Trusted Packet + Copy All
33/33 simulation PASS             Constitution rules enforced       READY/NEED_INFO/BROKER_REVIEW
```

**North star shift:**

| Before | After |
|--------|-------|
| *Chaos → structured case → next action* | *Customer Docs → Trusted Packet → Broker* |
| One paste, under one minute | Upload + minimal identity, under 3 minutes |
| Conversation is the product | Readiness is the product |
| Broker is primary user | Customer uploads; office consumes packet |
| Simulation = gate | Real documents = gate |

**What shipped in the new model:**

- 7-screen customer flow (Intent → Basic Info → Upload → Reading → Readiness → Fix Missing → Sent to Broker)
- Trusted Packet with source attribution and Copy All
- Request Framework: new request type = new schema, not new product
- Auto Follow-Up message for NEED_INFO cases (bilingual, ready to paste into WeChat)
- ADR-frozen scope: no timeline UI, no carrier API, no CRM in V1

**What did not ship (and should not have been attempted in Month 1):**

- Customer confirmation screen (TurboTax-style review)
- Timeline UI
- WeChat bot integration
- Multi-request-type expansion (renewal, carrier switch)
- Production READY on real dealer PDFs (blocked by VIN extraction)

---

## Engineering Evolution

| Area | Conversation era (Weeks 1–2) | Document era (Weeks 3–4) |
|------|------------------------------|--------------------------|
| **Primary backend surface** | `triage.py` — conversation parsing, slot filling, append | `add_car.py` + OCR kill test — vision extraction, packet builder |
| **Primary frontend** | Unified Intake customer tab — message input, turn history | `AddCarPage.tsx` — upload wizard, extraction progress, packet review |
| **Success metric** | Scenario pass rate (33/33) | Field accuracy on corpus (VIN 80%, YMM 95%) + real-world validation sets |
| **Test strategy** | Synthetic conversation scripts, append batteries | 22-doc OCR corpus, 5-set real-world validation matrix |
| **State model** | lifecycle_status + collected/still_needed slots | READY / NEED_INFO / BROKER_REVIEW readiness engine |
| **Biggest bug class** | Case memory not persisting conversation turns | VIN truncation on PDF text layer (16 chars, first-char drop) |

**Honest engineering assessment:** The conversation infrastructure (case store, phone lookup, Postgres persistence, status surfaces) was not throwaway work — it became the case backbone for document uploads. But the extraction pipeline received roughly one week of focused effort while conversation triage received three. That ratio was inverted.

---

## What We Would Do Again

1. **Start with broker pain research before building.** The Jun 19 business reality check should have been Week 1, not Week 3. It would have surfaced document hunting as pain #4 immediately.

2. **Write the Customer First Constitution early.** Phone as return key, no login, missing fields as progress — these rules survived the pivot intact. Constitution-first was correct.

3. **Talk to Wu Xiaojie, not just Chen Kui.** The broker buys; the office operator's daily pain defines the product. Wu Xiaojie's job is copy-paste into carrier portals, not read WeChat summaries.

4. **Freeze scope aggressively.** Decision Freeze on Jun 17 killed CRM, carrier API, timeline UI, WeChat bot, and customer accounts. Every item on the "Do Not Build" list that was actually deferred saved the sprint.

5. **Build the readiness state machine.** READY / NEED_INFO / BROKER_REVIEW is simple, broker-understandable, and validated. Three states, not twelve.

6. **Invest in real document corpus early.** The 22-doc OCR kill test and 5-set validation matrix produced more actionable truth than 33 conversation simulations.

7. **Keep the copy-paste broker path alive during transition.** Chen Kui still pastes. Don't force customers onto a new flow until the document path works on their actual dealer paperwork.

---

## What We Would Never Do Again

1. **Treat conversation simulation pass rate as pilot readiness.** 33/33 PASS gave false confidence. The correct gate is: *Can we extract a VIN from a real purchase agreement and produce READY?* That gate failed on Jun 21.

2. **Build customer chat UI before proving document extraction.** The customer-facing chat collecting screen was the wrong first surface for add-car. Customers have documents, not paragraphs.

3. **Spend three weeks on append/continuity before one week on OCR.** Append matters for return visits. Extraction matters for the first visit — which is 80% of cases.

4. **Confuse "broker pastes WeChat" with "product solves WeChat."** Meeting the broker at his paste habit perpetuates the problem. The product should eliminate the need for paste, not digitize it.

5. **Optimize demo smoothness over extraction accuracy.** A clean conversation demo hides the fact that VIN extraction fails on the most common document type (dealer purchase agreement PDF).

6. **Let the triage engine's size create gravity.** A 7,000-line conversation parser exerts pull toward conversation-shaped solutions. New features get routed through it because it exists.

7. **Defer real-document testing until after UI polish.** Screen 4 Trusted Packet hierarchy was polished before Set A (READY GOLD) was run on production. UI polish on a broken extraction path is lipstick on a pig.

---

## Lessons For Future Insurance Products

### 1. Match input shape to transaction shape

Add-car is a **document transaction**: dealer gives paperwork, office enters fields into carrier portal. Renewal is a **document transaction**: dec page contains everything. Teen driver is a **conversation transaction**: emotional, advisory, low document density. Build the input model per workflow, not one model for all.

### 2. Extraction is the product; conversation is the wrapper

For any workflow where the answer lives in a PDF, photo, or scan, the value moment is *structured fields with source attribution in under 60 seconds*. Conversation adds value only for follow-up ("we still need your lienholder name") — not for primary intake.

### 3. Simulate the evidence, not the dialogue

Test with real documents from day one. Synthetic conversation scenarios test the parser. Real documents test the product. Never confuse the two.

### 4. The office operator is the hidden user

Brokers buy software. Office operators (内勤) determine whether it sticks. If Wu Xiaojie doesn't trust the packet, Chen Kui cancels in 30 days. Design for the person who copies VIN into Mercury at 9 AM.

### 5. Source attribution is non-negotiable in insurance

Every extracted field must trace to a file. Brokers have E&O exposure. "The AI said the VIN is X" is not acceptable. "The VIN is X, from purchase_agreement.pdf, page 1" is.

### 6. Readiness beats completion

Brokers don't think "80% complete." They think: *Can I quote this right now?* (READY), *What do I need to ask the customer?* (NEED_INFO), or *Something looks wrong — I need to look.* (BROKER_REVIEW). Design all future workflows around these three judgments.

### 7. Chinese-language follow-up is a feature, not the product

Generating a bilingual WeChat message for missing items (N1) is high-value and low-complexity. It should be a output of the readiness engine, not a separate conversational product.

### 8. Don't expand request types until extraction works on one

The unified framework (Add Vehicle → Switch → Renewal → Replace) is architecturally sound. But Month 1 proved that VIN extraction on one document type isn't reliable yet. Adding renewal dec-page extraction before fixing purchase agreement VIN would multiply failure modes.

---

## Recommendations For Month 2

### P0 — Fix the happy path

| Action | Why |
|--------|-----|
| Fix VIN extraction on purchase agreement PDFs (text-layer preference, checksum validation, 17-char enforcement) | Set A READY GOLD is the gate. Without it, no broker will trust the product on real cases. |
| Run Wu Xiaojie real-case test with actual customer documents (not synthetic corpus) | Synthetic docs proved routing; real docs prove extraction. |
| Complete CK-001 through CK-003 soft pilot on real cases | 3 real cases > 33 simulated conversations. |

### P1 — Ship the outputs that matter

| Action | Why |
|--------|-----|
| Auto Follow-Up message for NEED_INFO (bilingual, copy-ready for WeChat) | Closes the gap between "detects missing items" and "eliminates Wu Xiaojie's most repetitive task." |
| Copy All verified on AMS/carrier portal paste | The money moment. Remove `model_used` tag and other prototype noise from packet header. |
| Time savings tracker: log 10 real cases with before/after minutes | $49/month invoice requires ≥4 min saved per case, measured, not simulated. |

### P2 — Resist scope expansion

| Do NOT do in Month 2 | Why |
|----------------------|-----|
| Renewal / carrier switch request types | Highest WTP, but extraction isn't proven on add-car yet. |
| Timeline UI | ADR-002 deferred until 10-case gate. |
| Customer chat collecting UI | Deprecated path. Maintain for broker paste; do not invest further. |
| WeChat bot / native integration | Paste-link achieves same outcome. |
| Conversation simulation expansion | Redirect testing budget to document corpus growth. |

### P2 — Preserve conversation architecture value

| Keep and extend | Why |
|-----------------|-----|
| Phone lookup + case append for return visits | Customer returns with another document → same case, not new case. |
| Case memory / Postgres persistence | Backbone for document uploads and status. |
| Customer status visibility (submit state, missing fields, contact state) | Constitution Rule umbrella: Customer Must Always Know The Status. |
| Broker workbench handoff | Broker confirms identity, closes/reopens — human judgment stays human. |

### Month 2 success definition

> **10 real add-car cases completed. Average ≥4 minutes saved per case. READY achieved on at least 7 of 10 without broker manually re-entering VIN. Chen Kui receives first $49 invoice.**

If Month 2 ends without real-case time savings evidence, the product has a narrative problem — not an architecture problem.

---

## The Startup Lesson

**We optimized the wrong thing because it was the thing we could measure.**

Conversation simulations produce clean pass/fail scores. Document extraction produces messy partial failures. The team naturally gravitated toward the metric that looked like progress.

This is the general lesson:

> **When your AI product's demo input differs from your customer's real input, you are building a demo — not a product.**

The pivot from conversation-first to document-first was correct. It was also late. Three weeks of conversation optimization could have been one week of conversation infrastructure plus two weeks of extraction validation — if the team had started with Wu Xiaojie's question: *"Show me the VIN from this dealer PDF without me reading it."*

The conversation architecture was not a mistake. Treating it as the product was.

Month 2 is not about choosing between chat and documents. It is about making the document path trustworthy enough that Chen Kui stops pasting WeChat threads — and Wu Xiaojie stops re-reading them.

---

*Sources: P16 Decision Freeze V1 · Customer First Constitution · Broker Pain Research · Business Reality Check V1 · Pre-Pilot Founder Review (33/33) · OCR Accuracy Report V2 · Real-World Validation Report (Jun 21) · Request Framework · Case Memory Root Cause · P16Z25 North Star · Upload-First Customer Flow*
