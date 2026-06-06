# P16-Z7 Phase 7 — Reality Comparison Benchmark

**Date:** 2026-06-02  
**Compare:** Unified Intake (current) · Zendesk · Intercom · WeChat-as-CRM  
**Question:** Would a broker need to reopen WeChat less often?

---

## Workflow comparison (3-day insurance case)

| Step | WeChat only | Zendesk | Intercom | Unified Intake (Z6+Z7) |
|------|-------------|---------|----------|------------------------|
| Day 1 intake | Read chat | Ticket + tags | Conversation | Paste → case |
| Day 2 client reply | Scroll chat | Comment thread | Continued convo | **Append** (if habit) |
| Day 3 status ping | Scroll again | Ticket history | Inbox | Summary + 对话记录 (5) |
| Responsibility | Mental | Custom fields | Tags/bots | **Manual** waiting_on |
| Chinese insurance lanes | Native | Manual macros | Manual | **Engine lanes** |
| Payment/cancel wedge | Native | Rules + agent | Bot flows | **Strong T1**, weak T3 |
| Attachments | Native | Upload | Upload | Paste text; OCR partial |

---

## WeChat reopen frequency (Role D evidence)

| System | Est. reopen rate Day 3 | Why |
|--------|------------------------|-----|
| WeChat only | **100%** | No structured memory |
| Zendesk (trained agent) | **~40%** | Full thread + fields |
| Intercom | **~45%** | Good thread; weak insurance lanes |
| **Unified Intake** | **~40%** (4/10 forced) | Thread UI helps; engine gaps on payment/remove/claims |

**Unified Intake vs WeChat:** **~60% fewer forced reopens** on best journeys (D08, D09, D05).  
**Not yet vs Zendesk:** Parity on UW (D04); **behind** on payment (D02, D10) and claims corrections.

---

## When Unified Intake wins

| Scenario | vs Zendesk/Intercom |
|----------|---------------------|
| Chinese cancel/payment wedge Turn 1 | Faster than manual ticket typing |
| Premium renewal + bill sent (D08) | Prior-turn merge **better than** generic ticket |
| Correction cancel→address (D09) | Comparable to agent note + tags |
| One paste &lt;1 min North Star | Zendesk slower for intake |

---

## When Unified Intake loses

| Scenario | Gap |
|----------|-----|
| D10 Chinese installment | Zendesk agent sets fields manually — UI wins |
| CL02 total loss correction | Zendesk full thread always visible |
| waiting_on carrier | Zendesk views/filters native |
| Photo evidence | WeChat gallery; Zendesk attachments |
| D07 remove-car lane drift | Zendesk agent corrects category |

---

## Would broker reopen WeChat less often?

| Broker | Answer |
|--------|--------|
| **vs WeChat-only office** | **Yes** — if append habit + Z6 thread deployed (~6/10 cases) |
| **vs Zendesk-trained office** | **Tie to slightly worse** on payment/claims; better on Chinese lane T1 |
| **vs Intercom** | **Slightly better** on insurance-specific triage; worse on responsibility automation |

---

## Strategic position (P16-Z3 maturity)

| Layer | Level | Benchmark note |
|-------|-------|----------------|
| Engine | L4.5 | Matches mid-market ticket intelligence |
| Deployed UX | L3.5–4 | Thread card closes gap to Zendesk **view** |
| 3-day memory | **L4.0** | Role D 68.9 reread — below Zendesk **L4.5** on corrections |

---

## Phase 7 verdict

Unified Intake **already reduces WeChat reopens** for renewal, correction, and claim Turn-1 paths — **not yet** a Zendesk replacement for **3-day payment or complex claims** without manual `waiting_on` and field hygiene.

**Commercial claim safe:** “Fewer WeChat scrolls on repeat clients” — **not** “never open WeChat for 3 days.”
