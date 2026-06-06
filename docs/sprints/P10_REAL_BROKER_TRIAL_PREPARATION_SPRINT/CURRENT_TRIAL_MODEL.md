# Current Trial Model — P10 Truth Snapshot

**Sprint:** P10 Real Broker Trial Preparation  
**Sources:** README, AGENTS, CURRENT_PRODUCT_SHAPE, BROKER_ONE_PAGER, BROKER_DEMO_FLOW, BROKER_TRIAL_PLAYBOOK, FOUNDER_ONE_PATH, DEMO_STORY, TRIAL_ONE_PATH, CUSTOMER_LANGUAGE_GUIDE, OPERATOR_SURFACE (non-archived only)

---

## 1. What exactly is being sold?

**Unified Intake** — a broker-office SaaS that turns messy customer messages (WeChat text, carrier notices, follow-ups pasted by the broker) into **one structured case** with:

- Urgency (e.g., same-day action)
- **Your next move** — one operational sentence
- **Collected** / **Still needed** chips
- An editable **draft reply** the broker copies to WeChat

**Not sold:** inbox sync, OCR/screenshot reading, auto-send, CRM, carrier integration, multi-office billing.

**Commercial frame:** 7-day free trial → optional paid pilot (~$99/month manual invoice acceptable per paid-pilot goal).

**Deployment shape:** Vercel frontend + Cloud Run backend + Postgres for durable cases on paid pilot.

---

## 2. Who is the customer?

**Primary:** California auto insurance brokers serving Chinese-speaking clients.

**Archetype:** Chen Kui (陈魁) — small office or solo broker, high WeChat/message volume, needs faster triage and client-ready replies, not another enterprise CRM.

**User in the office:** Broker or assistant; broker stays in control of every outbound message.

---

## 3. What is the first value moment?

**Documented path:** Broker opens workbench → loads demo queue → opens **cancellation risk** case → sees same-day urgency + **Your next move** + draft in under ~2 minutes.

**Actual UI default:** Page opens on **客户报送 (Customer Entry)** with Add-Car-first pilot intro — not the cancellation triage story. First value moment depends on founder redirecting broker to **办公室工作台** tab.

**True first value (if guided):** One messy paste → structured case with a usable draft and clear next action without re-reading the whole thread.

---

## 4. What is the Day-1 success condition?

Per TRIAL_ONE_PATH / BROKER_TRIAL_PLAYBOOK:

| Signal | Evidence |
|--------|----------|
| Broker opened workbench and bookmarked URL | Self-reported |
| Ran learning path (demo queue + 3 scenarios) | Founder demo queue loaded; ideally Simulation Assistant (hidden in product-only UI) |
| Pasted **one real message** | Case saved; broker saw Case focus, Your next move, Collected/Still needed |
| Broker can describe product in one sentence | To colleague or founder |

**Day-1 fail:** Broker can't tell what the system did with their message; expected WeChat sync or auto-send.

---

## 5. What is the Day-7 success condition?

| Signal | Evidence |
|--------|----------|
| Used 2–3+ real office cases (Day 3+) | Observation log entries |
| Answers **yes or maybe** to "Would this save time?" | With a specific example |
| Names scenario they'd use **Monday morning** | Cancellation, missing doc, or add-car |
| Trusts draft as **starting point** (with edits) | Not auto-trust |
| Pilot interest | Willing to try paid month or asks pricing |

**Day-7 fail:** Stops opening after Day 1; output routinely wrong; can't explain product.

---

## 6. What would make a broker stop using it?

| Stop reason | Why it kills retention |
|-------------|------------------------|
| **Expected WeChat/email sync** | Product requires manual paste — feels like extra step, not less work |
| **Drafts wrong or generic often** | Faster to write from scratch in WeChat |
| **Can't find urgency in the queue** | Same chaos as before — urgent cases still buried |
| **Slow or down during business hours** | 503 / warming / API errors with no fallback |
| **Too confusing on Day 1** | Wrong tab, English jargon ("case", "Unified Intake"), engineer tags (PG 镜像, 路由/指标) |
| **Add-car path promised but cancellation path weak** | UI says Add-Car-first; broker's Monday pain is payment/cancellation |
| **No persistence / lost cases** | JSON-only local demo or refresh loses work |
| **Founder unavailable when stuck** | No self-serve help beyond one-pager |
| **Simulation/training unavailable** | Product-only UI hides Simulation tab; playbook Day-1 steps break |
| **Mis-set expectations from old RAG demo** | `/demo` Q&A wedge vs workbench intake — different product |

---

## Summary table

| Question | Answer |
|----------|--------|
| Sold | Paste → structured case → draft → you send |
| Customer | CA auto broker, Chinese-speaking clients, small office |
| First value | Cancellation urgency + next move + draft (if on workbench tab) |
| Day-1 | Learn + 1 real paste + can explain in one sentence |
| Day-7 | Real use + time savings + trust draft + pilot interest |
| Stop using | Wrong expectations, bad drafts, confusion, downtime, no sync |

---

*End of current trial model*
