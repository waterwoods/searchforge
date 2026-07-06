# P18.1 — Chen Kui Business Workflow Simulation

**Date:** 2026-07-04  
**Type:** Business / process simulation — **not** a technical implementation doc  
**Audience:** Chen Kui (broker owner), Wu Xiaojie (office operator), Andy (founder), product/engineering  
**Prerequisite:** WeCom channel is technically connected and stable. Q0.11.1 passed — WeCom → Cloud Run → Cloud SQL → inbox/outbox → WeCom reply works; generic messages do not create or merge into Draft Cases; historical `sync_msg` replay is deduped.

**Purpose:** Simulate how Chen Kui’s office handles customer requests **today** vs how the new **AI WeCom + Case Workspace** workflow should improve that — before writing more features. This document will later drive product, UI, data model, and code.

**Related:** `docs/p18_chen_kui_wecom_ai_case_intake_demo.md` (demo blueprint) · `docs/p16/TRACK_B0_ACTIVE_WORKSPACE_CONTRACT.md` (B0 contract) · `docs/trial/P16_TIME_SAVINGS_MODEL.md` (time baseline)

---

## 1. Executive Summary

### The old world: personal WeChat and personal memory

Chen Kui’s California auto insurance office runs on **personal WeChat**. Customers message Chen Kui or Wu Xiaojie directly — not a system. Information arrives as scattered chat bubbles: VIN in one message, ZIP two hours later, a windshield-sticker photo the next morning, a voice note about the driver. The broker must **remember** who said what, **scroll** back through threads, **call or text again** for missing fields, **manually organize** a quote packet for the carrier, and **reply** in their own words. Office staff cannot easily take over because context lives in one person’s phone and head.

This workflow depends on **Chen Kui’s personal WeChat and personal memory**. It does not scale, does not hand off cleanly, and loses information when the broker is busy, on vacation, or juggling fifty unread threads.

### The new world: structured AI-built Cases

The new workflow turns WeCom messages into **structured AI-built Cases**. Customers message the office’s **WeCom AI service account** — the same conversational habit as WeChat, but routed into a durable intake engine. The system:

- Recognizes the customer by WeCom identity and enriches with phone, name, and ZIP when provided
- Classifies the request (e.g., Add Vehicle, Claim Lite)
- Preserves every original message in a case timeline
- Extracts facts from fragmented replies across hours or days
- Shows the broker **known facts**, **missing fields**, and **conflict warnings**
- Waits for **broker confirmation** before anything is treated as final

**WeCom is only the channel.** The product is an **AI Case Intake Engine** — an **AI Insurance Workspace**. Customers still chat naturally; the office gets a case object with memory, readiness, and a clear next action.

### Why this matters

Insurance intake is rarely one clean form. The core value is handling **fragmented, inconsistent, delayed customer information** — the real hard problem brokers face every day. A polite chatbot that replies to messages solves none of that. Case memory + structured readiness + broker gate turns chaos into something Wu Xiaojie can act on in under thirty seconds.

---

## 2. Old Workflow Simulation: Add Vehicle — Customer Picking Up a Car

### Scenario

**Customer message (typical opener):**

> “I’m picking up a car tomorrow. Can you add it to my insurance?”

Or in Chinese:

> “我明天提车，能帮我加到保险里吗？”

This is one of Chen Kui’s highest-frequency, highest-friction workflows.

---

### Step-by-step: today’s manual process

| Step | Customer action | Chen / broker action | Where information lives | Risk / problem |
|------|-----------------|----------------------|-------------------------|----------------|
| **1. Initial contact** | Texts Chen Kui or Wu Xiaojie **personally** on WeChat | Sees notification among dozens of other chats; may delay opening | Customer’s WeChat → broker’s personal WeChat | Request buried; no priority queue; no office visibility |
| **2. Broker opens thread** | Waits | Scrolls chat history; reads opener | Broker’s phone only | Context not shared; if Chen is driving, customer waits |
| **3. Ask for basics** | — | Composes reply asking for VIN, delivery date, garaging ZIP, primary driver, phone, current policy | Outbound WeChat bubble | Broker must remember standard checklist from memory |
| **4. Customer replies slowly, out of order** | “It’s a 2024 BMW” → (2 hrs later) “VIN is 1HGBH…” → (next day) “ZIP 91101” | Re-opens thread each time; mentally merges new facts with old | Scattered across multiple inbound bubbles | Easy to miss a bubble; no single “source of truth” |
| **5. Customer sends screenshot or photo** | Sends window sticker or insurance card photo | Opens image; may squint at VIN; may save to camera roll | Photo in WeChat album; maybe forwarded to office WeChat | VIN not searchable; photo may never reach office system |
| **6. Broker remembers context** | May reference “same driver as last time” | Must recall prior policy / household from memory or carrier portal | Broker’s head + separate carrier system | Wrong driver assumed; no audit of what customer actually said |
| **7. Broker manually checks what is missing** | — | Mental checklist: VIN? ZIP? Date? Driver? Phone? Policy number? | Nowhere formalized | Often discovers gaps only when starting carrier entry |
| **8. Broker manually follows up** | Gets another “when will it be done?” ping | Composes second or third WeChat asking for same missing field | More chat bubbles | Customer annoyed (“I already sent that”); broker loses credibility |
| **9. Broker manually updates carrier / policy process** | — | Re-keys extracted facts into carrier portal or emails office packet | Carrier system + informal office note | Typos; duplicate entry; office gets incomplete packet |
| **10. Broker replies to customer** | Receives “OK thanks” or more questions | Writes confirmation or ETA from scratch | Outbound WeChat | Tone inconsistent; no standard “we received everything” moment |
| **11. Office staff cannot easily take over** | Calls office directly if Chen is slow | Wu Xiaojie asks Chen “what do we have on the Li pickup?” | Chen must verbally transfer context | Handoff failure; customer repeats information |

---

### Old workflow summary

```
Customer (personal WeChat)
    → fragmented bubbles over hours/days
    → broker scrolls, remembers, asks again
    → manual carrier entry + informal office note
    → no shared case, no audit trail, no staff handoff
```

**Typical time:** ~10 minutes per add-car case when follow-up is needed (see `docs/trial/P16_TIME_SAVINGS_MODEL.md`).  
**Failure modes:** lost messages, repeated questions, wrong VIN/ZIP, delayed pickup coverage, broker burnout.

---

## 3. New Workflow Simulation: Add Vehicle through AI WeCom

Same customer scenario — picking up a car tomorrow — but the customer messages the **office WeCom AI service account** instead of Chen Kui’s personal WeChat.

---

### Step-by-step: AI Case Workspace process

| Step | Customer action | AI / system action | Broker action | Data saved | Why better than old workflow |
|------|-----------------|--------------------|--------------|-----------|------------------------------|
| **1. Initial contact** | Messages WeCom AI service account: “明天提车，能加到保险吗？” | Receives callback; dedupes `msg_id`; queues inbox event | — (notified later via Workbench) | Raw message + `external_userid` + timestamp | Durable ingress; not lost in personal chat pile |
| **2. Identity anchor** | — | Binds WeCom `external_userid`; attempts match on phone/name/ZIP if present in message | — | Channel identity on case stub | Customer recognizable even before phone given |
| **3. Intent classification** | — | Classifies **Add Vehicle** (high confidence) | — | Intent label on evidence | No broker needed to categorize request |
| **4. Start Card** | Sees guided menu / Start Card in WeChat | Sends Start Card — **no Draft Case yet** | — | Outbox record; no premature case | Generic chat does not create junk cases (Q0.11.1) |
| **5. Customer starts flow** | Taps **开始 / Start** | Creates **Draft Case** bound to `external_userid` | — | `service_record` Draft; `broker_confirmed_at` null | Explicit customer consent to begin structured intake |
| **6. Fragmented replies** | “VIN 1HGBH41JXMN109186” (now); “邮编 91101” (2 hrs later) | Extracts VIN, ZIP; merges into Draft; updates collected / still needed | — | Each message in timeline + merged fields | Facts accumulate automatically; broker not re-reading thread |
| **7. More facts** | “3月15号生效，主驾驶 Li Hua，6265550100” | Extracts date, driver, phone; attaches phone to case; may flag **Known Customer** if match | — | `collected_fields`, `still_needed_fields`, `record_messages` | Single structured view replaces mental merge |
| **8. Photo instead of text** | Sends window sticker photo | Logs image as evidence; may prompt for VIN text (no OCR yet) | — | Evidence event; `photos_pending` flag if applicable | At minimum, photo is on the case — not lost in camera roll |
| **9. Readiness display** | — | Computes quote-ready when required fields present | — | Case status → Ready for Broker | Broker opens Workbench to finished picture, not raw chat |
| **10. Broker Workbench** | — | — | Opens case list; sees Draft badge, WeCom tag, known / missing / conflicts | All prior steps visible in one screen | **No WeChat hunting** — 30-second scan vs 2-minute scroll |
| **11. Broker confirms or handles manually** | — | — | Reviews facts; clicks **Confirm** (Add Vehicle) or **Manual Handle** if edge case | `broker_confirmed_at` set on confirm | Broker is safety gate — nothing “final” without explicit yes |
| **12. Done Card to customer** | Receives bilingual Done Card in WeChat | Sends canned acknowledgment: broker reviewed, office will proceed | — | Outbox + confirm timestamp | Customer gets clear closure; broker does not compose from scratch |
| **13. Future follow-ups** | Returns tomorrow: “对了，提车改到周五了” | Attaches to **same case** when appropriate (same `external_userid`, open or recently confirmed flow) | Sees updated field + change flag | Timeline append; field overwrite with conflict note | Customer does not restart; broker sees **what changed** |

---

### New workflow summary

```
Customer (WeCom service account)
    → fragmented messages over time
    → AI preserves identity + full conversation
    → AI builds/updates ONE Draft Case
    → Broker Workbench: identity, summary, known / missing / conflict
    → Broker Confirm → Done Card
    → future messages attach to same case when appropriate
```

**Target time for broker review:** under 2 minutes when case arrives Ready for Broker.  
**Invariant:** No automatic policy change — ever. AI prepares; broker decides.

---

## 4. Fragmented Information Scenarios

This is the **real hard problem**. Customers do not submit forms. They chat. The product must win on **memory, merge, and readiness** — not on clever replies.

---

### Scenario A: VIN now, ZIP two hours later

| | Old workflow | New system should |
|---|--------------|-------------------|
| **What happens** | Broker sees VIN message; may reply “thanks”; forgets to note missing ZIP until end of day | First message merges VIN into Draft; `still_needed` shows ZIP; AI asks only for ZIP next |
| **Struggle** | Mental todo list; easy to close thread prematurely | — |
| **System behavior** | — | Persist both messages in timeline; update `collected_fields` / `still_needed_fields`; suggested next question: garaging ZIP |

---

### Scenario B: Customer changes delivery date

| | Old workflow | New system should |
|---|--------------|-------------------|
| **What happens** | “明天提车” becomes “改到周五” in a later bubble | New date extracted; previous date retained in timeline |
| **Struggle** | Broker may quote wrong effective date; office enters stale date | — |
| **System behavior** | — | **Conflict / change flag**: “Delivery date updated: Fri (was Thu)”; broker sees diff at confirm time |

---

### Scenario C: Customer sends photo instead of text

| | Old workflow | New system should |
|---|--------------|-------------------|
| **What happens** | Broker opens image in WeChat; manually reads VIN | Image logged as evidence on case |
| **Struggle** | Photo never reaches office packet; VIN not searchable | — |
| **System behavior** | — | Store evidence event; reply: “收到照片。如果方便，请再发一下 VIN 文字方便核对。” (no full OCR in v1) |

---

### Scenario D: “Same driver as before”

| | Old workflow | New system should |
|---|--------------|-------------------|
| **What happens** | Broker assumes spouse / prior policy driver from memory | If **Known Customer** + prior case on file → suggest driver from history |
| **Struggle** | Wrong driver on quote; E&O risk | — |
| **System behavior** | — | Show **Possible Match** suggestion with “verify with customer” — never auto-fill without broker visibility; flag as needs confirmation |

---

### Scenario E: Customer mixes in a claim question

| | Old workflow | New system should |
|---|--------------|-------------------|
| **What happens** | “加车，对了昨天还撞了” — broker must juggle two topics in one thread | During open Add Vehicle Draft → set `claim_mentioned_at` flag only |
| **Struggle** | Add-car packet delayed; claim urgency missed; two workflows entangled | — |
| **System behavior** | — | Acknowledge claim mention; **do not branch** (Rule 8: one business flow at a time); banner in Workbench: “Customer also mentioned accident — handle separately after add-car” |

---

### Scenario F: Customer disappears and returns tomorrow

| | Old workflow | New system should |
|---|--------------|-------------------|
| **What happens** | Broker loses thread in unread pile; customer repeats opener | Same `external_userid` → attach to open Draft Case |
| **Struggle** | Duplicate work; customer repeats VIN | — |
| **System behavior** | — | Resume flow: “欢迎回来。我们还需要您的邮编。” AI remembers earlier answers; does not re-ask for VIN |

---

### Scenario G: Inconsistent ZIP / address

| | Old workflow | New system should |
|---|--------------|-------------------|
| **What happens** | “91101” then “其实车在 91030” | Both values in timeline |
| **Struggle** | Broker quotes wrong territory; wrong garaging | — |
| **System behavior** | — | **Conflict warning**: two ZIPs detected; broker must pick or clarify before Confirm |

---

### Scenario H: Broker needs to know what changed

| | Old workflow | New system should |
|---|--------------|-------------------|
| **What happens** | Wu Xiaojie asks Chen “有任何更新吗？” — Chen scrolls again | Workbench shows last customer message + field-level change flags |
| **Struggle** | Office acts on stale packet | — |
| **System behavior** | — | Timeline ordered by time; highlight fields updated since broker last opened case |

---

## 5. Business Value Comparison

| Dimension | Old WeChat manual workflow | New AI Case Workspace |
|-----------|---------------------------|------------------------|
| **Speed** | ~10 min/case with follow-up; broker reads full thread each time | ~2–3 min broker review when case is Ready; AI merges while customer chats |
| **Accuracy** | Typos from manual re-keying; missed bubbles | Structured extraction + conflict flags; broker confirms before action |
| **Missing information** | Discovered late, often at carrier entry | `still_needed_fields` visible continuously; AI asks next gap only |
| **Memory** | Broker’s head + scroll WeChat | Case timeline + collected fields persist across days |
| **Handoff to staff** | Verbal transfer; Wu Xiaojie cannot self-serve | Any broker/staff opens same case in Workbench |
| **Audit trail** | Chat history on personal phone only | `record_messages`, evidence events, confirm timestamp |
| **Customer experience** | “Did you get my VIN?” repeated pings | Natural chat; AI remembers; Done Card closure |
| **Broker workload** | High cognitive load — organize + follow up + enter | Review + confirm; AI did organize and follow-up prompts |
| **Error risk** | Wrong VIN/ZIP/driver; coverage gap on pickup day | Conflict warnings; broker gate; phone required before confirm |
| **Scalability** | Bounded by Chen Kui’s attention | Same pipeline for 10 or 100 WeCom threads; queue + drain |
| **Future revenue opportunity** | Invisible — no renewal/cross-sell signal | Placeholder insight layer: renewal, cross-sell, coverage gap (not automated yet) |

---

## 6. Broker Workbench Design Implications

Chen Kui should open the Workbench and **immediately feel** the new workflow is better than scrolling WeChat. The screen must answer: *Who is this? What do they want? What do we know? What’s missing? What changed? What do I do next?*

### Required surfaces (Add Vehicle + Claim Lite)

| Element | Purpose | Example |
|---------|---------|---------|
| **Customer identity badge** | Anchor trust | **Known Customer** (Li Hua · 626-555-0100) · **New Customer** · **Possible Match** (verify) |
| **Channel tag** | Source clarity | **WeCom** / 微信客服 |
| **Case type** | Business context | Add Vehicle · Claim Lite |
| **Case status** | Actionability | Draft · Needs Info · Ready for Broker · Confirmed |
| **Known facts** | Replaces thread scrolling | VIN, ZIP, delivery date, driver, phone — structured list |
| **Missing fields** | Replaces mental checklist | e.g., “Garaging ZIP”, “Primary driver” |
| **Conflict warnings** | Prevents E&O | Two ZIPs · date changed · VIN format suspect |
| **Latest customer message** | Fresh context | Most recent bubble text + time |
| **Timeline** | Audit + handoff | Original messages in order (read-only) |
| **Suggested next question** | Optional AI assist | “Ask customer for garaging ZIP” — for broker or AI to send |
| **Confirm** | Add Vehicle closure | Sets confirmed; triggers Done Card |
| **Manual Handle** | Claim Lite / edge cases | No auto Done Card; broker takes over |
| **AI Insights placeholder** | Future vision | Disabled “coming soon”: renewal, cross-sell, coverage gap |

### Emotional design goal for Chen Kui

> “I am not hunting WeChat. I am confirming a packet my office can already use.”

Wu Xiaojie should be able to open the same case and prepare the carrier packet **without asking Chen what the customer said**.

---

## 7. Customer Experience Design Implications

The customer should feel the new flow is **still natural like WeChat** — not a portal, not a long form, not a generic chatbot.

| Principle | What customer should feel | What system must avoid |
|-----------|---------------------------|------------------------|
| **Natural conversation** | “I’m just texting the insurance office” | Multi-screen forms; login walls |
| **No long forms** | One question at a time when needed | Dumping a checklist of ten fields |
| **Smart questions only** | AI asks the **next useful** missing field | Asking for VIN twice |
| **Memory** | “They remember what I sent this morning” | Treating return visit as brand-new request |
| **No duplicate asks** | Same fact never requested again unless conflict | Robotic re-prompts after customer already answered |
| **Broker review transparency** | Clear that **broker will review before final changes** | Promising instant policy update |
| **Return later** | Can disappear and continue tomorrow | “Start over” or lost context |
| **Closure** | Done Card = “office has what they need” | Silence after last message |

### Sample customer-facing tone (Add Vehicle)

- After Start: “好的，我们帮您整理加车信息。请先发送车辆 VIN。”
- After partial info: “收到。还需要您的车辆停放邮编（garaging ZIP）。”
- After broker confirm: Done Card — bilingual acknowledgment that broker reviewed and office will proceed.

---

## 8. Demo Story Recommendation

For the **3–4 day Chen Kui demo**, show exactly **two stories**. Together they prove this is **not a simple chatbot**.

### Story A: Add Vehicle — full flow (primary, ~80% of demo time)

**Why:** Shows structured **transaction workflow** — the bread-and-butter Chen Kui case type.

**Script beats:**

1. Customer: “我想加一台车” → **Start Card** (no case yet)
2. Tap Start → **Draft Case** created
3. Fragment across 3–5 messages: VIN → ZIP + date → driver + phone
4. Broker opens Workbench → known / missing → **Confirm**
5. Customer receives **Done Card**

**Proof for Chen Kui:** Generic “hello” does not create a case; fragmented messages accumulate; broker confirms explicitly.

---

### Story B: Claim Lite — intake summary (secondary, ~20% of demo time)

**Why:** Shows **messy real-world information collection** — accidents are urgent, emotional, incomplete.

**Script beats:**

1. Customer: “刚出事故了” → Claim Start / guided ack
2. Over several messages: time, location, injuries yes/no, other party, police report, “照片稍后发”
3. Workbench shows **Claim Intake Summary** — known / missing / urgency
4. Broker clicks **Manual Handle** — no Done Card, no FNOL automation

**Proof for Chen Kui:** Same channel, different case type; AI summarizes chaos; broker decides — system does not dispatch adjusters or file claims.

---

### Why both stories

| Story | Proves |
|-------|--------|
| Add Vehicle | Structured fields, readiness, Confirm + Done Card, Rule 8 discipline |
| Claim Lite | Messy intake, urgency, Manual Handle, no false automation promise |
| Together | **AI Case Intake Engine** — not “WeChat auto-reply bot” |

**Opening line for demo:**

> “客户加车或出事故，吴小姐是不是要在微信里翻聊天记录、打电话补信息，再手动输进系统？”

Wait for yes. Then:

> “这个演示不是聊天机器人。是：**客户照常发微信，AI 帮办公室整理成 Case，您点确认。**”

---

## 9. What Not to Build Yet

Explicitly **out of scope** for P18 / Chen Kui demo. Building these now would dilute the story and violate ADRs.

| Do not build | Reason |
|--------------|--------|
| Full CRM / household model | Demo is case intake, not client management |
| Rating engine | No carrier API (ADR-003) |
| Auto policy change | Broker gate is the product story |
| Full claim FNOL automation | Claim Lite = collect + summarize only |
| Multi-topic workflow engine | One flow at a time; flags not branches (Rule 8) |
| Advanced cross-sell engine | Placeholder only |
| Full OCR pipeline | Images logged as evidence at most |

### Future placeholder (vision only — show disabled in Workbench)

These appear in an **AI Insights** “coming soon” box — **not automated** in v1:

- **Renewal reminder** — policy expiring soon
- **Cross-sell** — umbrella / home gap
- **Coverage gap** — liability limits vs vehicle value
- **Risk flag** — teen driver, high-value vehicle
- **Missing opportunity** — customer asked about coverage type not yet quoted

Reference: `docs/p16/P16_FUTURE_VISION.md` — Loop 2 / Continuous Readiness hypothesis.

---

## 10. Product Principles

Reaffirmed for P18.1 and all downstream work:

| # | Principle | Meaning |
|---|-----------|---------|
| 1 | **WeCom is a channel, not the product** | Swap channel later; case engine stays |
| 2 | **Case is the core object** | Every message serves case readiness |
| 3 | **Customer identity is the anchor** | `external_userid` + phone + name/ZIP enrichment |
| 4 | **Conversation memory is the moat** | Timeline + merge beats one-shot LLM reply |
| 5 | **Broker confirmation is the safety gate** | Nothing final without Confirm / Manual Handle |
| 6 | **One active business flow at a time** | Second topic → flag, not parallel workflow (Rule 8) |
| 7 | **AI prepares, broker decides** | Extract, summarize, prompt — broker confirms |

---

## 11. Output — Next-Step Recommendations

This simulation doc is **planning only**. Recommended implementation order after approval:

### A. UI / Workbench — polish first

| Priority | Piece | Story |
|----------|-------|-------|
| P0 | Draft badge on case list | A |
| P0 | WeCom channel tag (微信客服) | A, B |
| P0 | Known / missing / conflict display (add-car) | A |
| P0 | Claim Intake Summary panel | B |
| P0 | Manual Handle CTA (distinct from Confirm) | B |
| P1 | Identity badge: New / Known / Possible Match | A, B |
| P1 | Claim mentioned banner (`claim_mentioned_at`) | A |
| P1 | Read-only conversation timeline | A, B |
| P2 | AI Insights placeholder (disabled) | Vision |

### B. Backend — required for demo

| Piece | Story | Notes |
|-------|-------|-------|
| B0 flags enabled on pilot revision | A | `WECOM_B0_ACTIVE_WORKSPACE=1` |
| Start Card → Draft on Start click | A | Already built; harden |
| Field merge across turns | A | VIN, ZIP, date, driver, phone |
| Broker Confirm → Done Card | A | Idempotent |
| `claim_mentioned_at` flag mid add-car | A | Rule 8 |
| Claim Lite stub + lane + extractors | B | New |
| Claim Start Card + merge path | B | Mirror Add Vehicle pattern |
| Identity match state in case JSON | A, B | `new` / `known` / `possible_match` |
| `record_messages` dual-write verify | A, B | Timeline source |

### C. Demo script to write

| Artifact | Owner | Content |
|----------|-------|---------|
| `docs/p18_chen_kui_demo_script_5min.md` (or extend P16 script) | Eng + Andy | Bilingual cues; Story A + B beats; “not a chatbot” positioning |
| Internal rehearsal checklist | Ops | Fragmented 5-message add-car; claim 4-message script; manual drain steps |
| Wu Xiaojie role-play sheet | Andy | Handoff moment: open Workbench without asking Chen |

### D. Tests to add

| Test area | Examples |
|-----------|----------|
| Fragmented merge | VIN turn 1 + ZIP turn 2 → single Draft, correct `still_needed` |
| Date change | Conflict flag when delivery date updated |
| Rule 8 | Claim mention during add-car → flag only, no second case |
| Return visit | Same `external_userid` attaches to open Draft |
| Confirm gate | Confirm blocked without phone |
| Claim Lite | Claim messages → claim stub; Manual Handle path; no Done Card |
| Dedup / replay | `sync_msg` replay does not double-merge (Q0.10 layer) |
| Generic message | No Draft without Start click (Q0.11.1 regression) |

---

## Acceptance Criteria (this document)

- [x] Clearly explains old vs new workflow
- [x] Uses Add Vehicle / car pickup as the main example
- [x] Explains why fragmented information is the hard problem
- [x] Maps business value to product capabilities
- [x] Gives design implications for Broker Workbench and customer WeCom experience
- [x] Recommends Add Vehicle + Claim Lite for the 3–4 day demo
- [x] Provides practical next steps
- [x] Planning only — no code, deploy, smoke, networking, or copy changes in this task

---

*End of P18.1 — Chen Kui Business Workflow Simulation*
