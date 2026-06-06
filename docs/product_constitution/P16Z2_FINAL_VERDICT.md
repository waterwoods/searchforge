# P16-Z2 Phase 10 — Final Verdict

**Date:** 2026-06-01  
**Sprint:** P16-Z2 Case Intelligence Strategic Reverse Engineering  
**Constraint honored:** Zero code written. Zero P17. Zero new features planned as greenfield builds.

---

## Sprint success criteria

| Criterion | Met? |
|-----------|------|
| Andy understands why customers pay (benchmark companies) | ✅ |
| Andy understands why offices pay (Chen Kui) | ✅ |
| What best systems actually do (mapped) | ✅ |
| What to steal (Top 100) | ✅ |
| What to reject (Top 50) | ✅ |
| Next 30 days clear | ✅ |
| Confusion eliminated | ✅ |
| Code produced | ❌ None (correct) |

---

## 1. What is the product's true North Star?

> **Transform messy customer communication into an office-executable case with a clear next action — in one paste, under one minute.**

Not:
- A chatbot
- A CRM
- A document scanner
- A SearchForge lab
- An "AI platform"

The pipeline:

```
Chaos (WeChat paste, screenshot, voice memo text)
    ↓
Understanding (category, urgency, summary)
    ↓
Case (collected_fields, still_needed_fields, thread)
    ↓
Next Action (broker_next_step, client_prep, waiting_on)
    ↓
Outcome (office acted, customer informed, deadline met)
```

Every company studied (Zendesk, Intercom, Salesforce, Stripe, Linear, HubSpot) implements this pipeline. None skip the "structured record" step. The 2026 shift (Zendesk verified resolution, Linear context-first agents, HubSpot credit-per-resolution) confirms: **outcomes on structured cases**, not activity on messages.

---

## 2. Why would Chen Kui pay?

**He won't pay for software. He'll pay for time back.**

| Pain today | What we sell |
|------------|--------------|
| 50 unread WeChat messages | One paste → ready-to-send reply |
| Re-read paste to find deadline | Deadline in glance + countdown |
| Re-type client message | Copy-to-WeChat button |
| Lose context when client replies | Append to same case |
| Mixed English in tool | Chinese office workflow |
| "Why open a webpage?" | Must beat「直接回微信」on first case |

**Payment trigger:** After supervised Day 0, Chen Kui sends **one draft to a real client without Andy on the phone** — and the client responds positively.

**Price anchor:** If tool saves 15 min/day × 20 days = 5 hours/month. At $50–100/month manual invoice, ROI is obvious for a busy broker.

**Objection to overcome:** "I use it once and go back to WeChat." → Fix append discoverability + waiting_on state.

---

## 3. Why would a customer use it?

**Customers don't want software. They want the office to handle their thing.**

| Customer need | How product serves it (when exposed) |
|---------------|--------------------------------------|
| "帮我加车" without forms | Message-first intake |
| Know what's still needed | Plain Chinese gap list |
| Know it was received | Handoff confirmation |
| Check status without calling | 我的办理 tab |
| Send follow-up info | 提交补充 on same case |

**Pilot reality:** Customers interact through **Chen Kui's WeChat**, not our URL, in weeks 1–2. Customer-facing tab is **week 3** unless broker requests earlier.

**Customer value proposition (via broker):** "发我这个链接，我帮您整理" — broker stays the trusted interface.

---

## 4. What is the highest-ROI capability?

**Ranked by impact ÷ effort for 2–3 week pilot:**

| Rank | Capability | ROI | Status |
|------|------------|-----|--------|
| 1 | **Paste → structured case → copy-to-WeChat** | ★★★★★ | Built; deploy + tune |
| 2 | **Append merge + discoverability** | ★★★★★ | Backend done; UX + P16-Y P0 |
| 3 | **Chinese-specific broker_next_step** | ★★★★★ | Templates; not architecture |
| 4 | **Trial URL access (FP-004)** | ★★★★★ | 5-minute founder fix |
| 5 | **Cancel notice excellence** | ★★★★☆ | Wedge scenario |
| 6 | **Observation log → payment evidence** | ★★★★☆ | Process |
| 7 | **OCR on broker upload** | ★★★☆☆ | Week 2; wire existing |
| 8 | **Customer tab** | ★★★☆☆ | Week 3; hidden asset |

**Single highest-ROI item:** **Post-copy append bridge** — zero backend, fixes continuity 41→70+, unlocks multi-turn office workflow, answers "why reopen the webpage?"

---

## 5. What should become the product's soul?

**One sentence the product should feel like:**

> "Paste 微信 → 案件就绪 → 复制发出 → 客户回复 → 追加 → 再复制"

**Three soul elements:**

1. **Speed** — Under 45 seconds paste to copy on urgent cancel. Beat WeChat manual drafting.

2. **Completeness** — `还缺什么` and `办公室下一步` in Chinese, specific, never generic. Office never re-reads paste.

3. **Continuity** — Same case grows with each message. Linear's "context is source of truth" applied to insurance WeChat.

**Not the soul:** Category buttons, engineer field labels, UTC timestamps, demo queue noise, English mixed in Chinese office, platform/lab tabs.

---

## 6. What should NOT be built?

See `P16Z2_TOP50_DO_NOT_COPY.md`. Summary:

| Never | Defer |
|-------|-------|
| P17 platform | Customer tab (week 3) |
| Stripe billing | OCR upload (week 2) |
| Multi-tenant auth | PDF extraction |
| Full CRM | WeChat API |
| Voice/IVR | Mobile optimization |
| New microservices | LLM generation path |
| OCR-first primary intake | Full P16-M UI sprint |
| Enterprise routing/SLA admin | Activity timeline UI |

**P16-Z0 verdict still stands:** You already built the engine. The trial fails on **URL access and discoverability**, not missing backend.

---

## 7. What should be built next?

**Not "built" — revived, wired, tuned, deployed.**

### Immediate (this week)

1. FP-004 off
2. P16-Y P0 append summary merge
3. Chinese broker_next_step templates + blocklist
4. Post-copy append CTA
5. EN/ZH fix in glance

### Next (week 2)

6. Supervised Chen Kui Day 0
7. Observation log discipline
8. OCR wire on broker upload
9. Urgent/deadline visibility

### Then (week 3)

10. Customer tab if broker wants
11. Payment + testimonial
12. Observation-log-driven fixes only

**Next sprint name suggestion:** **P16-Z3 — Case Continuity & Trial Close** (not P17, not UI overhaul)

---

## 8. If we only had 3 weeks, what would we ship?

### The 3-week product (minimum lovable for paid pilot)

```
┌─────────────────────────────────────────────────────────┐
│  BROKER WORKBENCH (single tab, Chinese, no SSO)         │
│                                                         │
│  [ Paste WeChat message here ]                          │
│  [ 开始整理 ]                                            │
│                                                         │
│  ┌─ Case Glance ─────────────────────────────────────┐  │
│  │ 取消通知 · 紧急 · 还有3天                           │  │
│  │ 已收集: _carrier, _policy, _deadline               │  │
│  │ 还缺: 付款截图                                      │  │
│  │ 办公室下一步: 今天联系 Mercury 确认 UW 状态          │  │
│  │ [ 复制给客户 ]  [ 客户回复了？追加 ]                  │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  Queue: today's urgent cases                            │
└─────────────────────────────────────────────────────────┘
```

### Explicitly NOT in 3-week ship

- Customer self-serve tab (unless week 3 request)
- PDF processing
- Multi-broker
- Billing integration
- New pages or design system
- Platform/lab features

### 3-week ship checklist

| # | Ship item | Type |
|---|-----------|------|
| 1 | Working trial URL | Ops |
| 2 | Cancel + payment + add-car paste excellence | Engine tune |
| 3 | Append with merged summary | Engine |
| 4 | Copy-to-WeChat + append CTA | UX |
| 5 | Chinese throughout | Copy |
| 6 | guardrail PASS | QA |
| 7 | 10 real cases in observation log | Process |
| 8 | Invoice paid | Commercial |
| 9 | Testimonial | Commercial |

---

## Competitive intelligence — one-line takeaways

| Company | Steal | Skip |
|---------|-------|------|
| **Zendesk** | Outcome focus; verified resolution mindset | 20B corpus; voice AI; seat pricing |
| **Intercom** | Conversation-first; convert to typed record | Messenger widget; PLG |
| **Salesforce** | Auto-fill fields; NBA on record; wrap-up | CRM; Flow Builder; Einstein platform |
| **Stripe** | Evidence packet assembly; merge auto+manual | Payments |
| **Linear** | Context → record; inbound automations | Git/PR workflow |
| **HubSpot** | Portal status view; KB deflection loop | Marketing bundle; IVR |

---

## Answer to the mission question

> **"What is the shortest path to creating a valuable Case Intelligence product that a real office would pay for within the next 2–3 weeks?"**

**Shortest path:**

1. **Fix access** (FP-004) — 5 minutes
2. **Tune existing triage** for cancel wedge + Chinese next actions — 2 days
3. **Wire append UX** (no new backend) — 1 day
4. **Implement P16-Y P0 summary merge** — 1–2 days
5. **Supervised Day 0 with Chen Kui** — 2 hours founder time
6. **Observation log → invoice → testimonial** — process, not code

**Total new architecture required: zero.**

The valuable Case Intelligence product **already exists in the repository**. It is hidden behind SSO, undiscoverable append UX, English mixed into Chinese glance, and generic broker_next_step wording.

This sprint's job was to prove that — by looking at what the best companies do and mapping it to what we already have.

---

## Document index (P16-Z2 deliverables)

| Phase | Document |
|-------|----------|
| 1 | `P16Z2_COMPANY_TEARDOWN.md` |
| 2 | `P16Z2_CASE_INTELLIGENCE_COMPARISON.md` |
| 3 | `P16Z2_MULTITURN_RESEARCH.md` |
| 4 | `P16Z2_DOCUMENT_INTELLIGENCE.md` |
| 5 | `P16Z2_NEXT_ACTION_ENGINE.md` |
| 6 | `P16Z2_TOP100_IDEAS.md` |
| 7 | `P16Z2_TOP50_DO_NOT_COPY.md` |
| 8 | `P16Z2_CAPABILITY_MAP.md` |
| 9 | `P16Z2_30_DAY_ROADMAP.md` |
| 10 | `P16Z2_FINAL_VERDICT.md` (this file) |

**Prior archaeology (still authoritative for "what exists"):** P16-Z0 series in same directory.

---

## One-line founder read

> **The world's best systems all do the same thing: chaos → structured case → next action. You already built it. Stop building. Fix the URL, fix the Chinese next-action wording, teach append, run Day 0 with Chen Kui, get paid.**

---

*End of P16-Z2 — Case Intelligence Strategic Reverse Engineering Sprint*
