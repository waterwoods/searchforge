# P16-Z2 Phase 3 — Multi-Turn Intelligence Research

**Date:** 2026-06-01  
**Sprint:** P16-Z2 Case Intelligence Strategic Reverse Engineering  
**Question:** How do world-class systems merge Message 1…4 → One record?

---

## The problem

```
Message 1: "我想加一台2024 Tesla"
Message 2: "车牌还没拿到"
Message 3: "对了是Model Y"
Message 4: "发你驾照照片了"
        ↓
   ONE case record with:
   - vehicle: 2024 Tesla Model Y
   - plate: pending
   - still_needed: [driver_license_image] → collected after msg 4
   - message_count: 4
```

Single-turn triage is solved (~85/100). Multi-turn is the **#1 Case Intelligence gap** (P16-Y Y44/Y45 fail; continuity 41/100 deployed).

---

## How best-in-class systems handle multi-turn

### 1. Merge context

| System | Strategy | Mechanism |
|--------|----------|-----------|
| **Zendesk** | Ticket comments append; AI summarizes thread on agent open | Side Conversations for internal; Copilot reads full thread |
| **Intercom** | Conversation parts[] immutable; ticket_parts on convert | Fin maintains session context; convert preserves history |
| **Salesforce** | Case Feed + EmailMessage objects; Wrap-Up summarizes | Einstein reads all Case comments for classification |
| **Stripe** | Dispute evidence hash merges manual + auto | `prefer_smart_disputes` combines sources |
| **Linear** | Issue comments + AgentSession plan updates | Agent interprets new comments, updates issue fields |
| **HubSpot** | Ticket thread + CRM timeline | Breeze reads full thread for reply suggestion |

**Industry consensus (2025–2026):**

> **Structured state > raw transcript.** Don't re-send 20 messages to the LLM. Maintain a rolling entity ledger + compressed summary + recent verbatim buffer (6–10 turns).

**Three-layer memory model:**

| Layer | Contents | Size cap |
|-------|----------|----------|
| **Hot** | Last 6–10 turns verbatim | ~2K tokens |
| **Warm** | Rolling summary (200 words) | Updated each turn |
| **Cold** | Entity ledger: people, IDs, dates, vehicles, policy # | Structured JSON |

**SearchForge today:**
- Backend: `conversation_turns` → `triage_conversation()` merges labeled thread ✅
- Gap: **append summary merge** — prior `[客户]` bubbles not injected into summary (P16-Y P0 #1)
- Gap: **UI continuity** — broker doesn't know to reopen case for msg 2–4

---

### 2. Track state

| System | State model | Key fields |
|--------|-------------|------------|
| **Zendesk** | Ticket status + custom fields | New → Open → Pending → Solved |
| **Intercom** | Conversation state + ticket_state | open, snoozed, resolved |
| **Salesforce** | Case Status + Milestones | New, Working, Escalated, Closed |
| **Linear** | Issue status + AgentSession | pending, active, awaitingInput, complete |
| **HubSpot** | Ticket pipeline stage | New, Waiting, Closed |

**SearchForge today:**
- `lifecycle_status`, `waiting_on`, `formal_submission_complete` ✅
- `case_messages[]` on append ✅
- `session_store` for in-progress customer flow ✅
- Gap: **`waiting_on` not prominent** in broker glance
- Gap: No **"等客户回复"** state after copy-to-WeChat

**Steal from Linear AgentSession:**

```
pending     → customer started, collecting info
active      → office working the case  
awaitingInput → waiting on customer document/reply
complete    → handed off / resolved
```

Map to existing `waiting_on` values — no new backend needed.

---

### 3. Handle corrections

| Pattern | Example | Best practice |
|---------|---------|---------------|
| **Supersede** | "不是Model 3，是Model Y" | New value replaces old in entity ledger |
| **Explicit correction flag** | Customer says "刚才说错了" | Mark prior field as superseded, not duplicate |
| **Last-write-wins** | Conflicting dates | Most recent message wins with audit trail |
| **Human confirm** | High-stakes (policy #) | Suggest correction; broker confirms |

**Salesforce approach:** Case history tracks field changes; Einstein re-classifies on update.

**SearchForge gap (P16-Y Y44):** Correction in message 3 not always reflected in `collected_fields` or summary.

**Fix class:** Engine — inject prior turns into summary builder; on correction keywords, supersede not append.

**Minimum viable correction handling (2-week scope):**

1. Detect correction markers: "不对", "更正", "刚才", "其实是", "不是…是…"
2. Re-extract affected entity from latest message
3. Update `collected_fields` with `_corrected_at` metadata (optional)
4. Regenerate `conversation_summary` from entity ledger, not last message only

---

### 4. Handle conflicting information

| Conflict type | Resolution strategy |
|---------------|---------------------|
| Same field, two values | Last-write-wins + flag in summary ("客户更正：…") |
| Contradictory intent | Escalate to broker; set `still_needed: [confirm_intent]` |
| Partial overlap | Merge non-conflicting fields; flag conflict in glance |
| Cross-message policy # mismatch | Surface both; broker verifies |

**Stripe pattern:** `recommended_evidence` lists what's missing; conflicts don't block — human merges at submit.

**Zendesk pattern:** Internal note flagging conflict; agent resolves before close.

**SearchForge recommendation:**

```
if conflict_detected(field):
    collected_fields[field] = latest_value
    still_needed_fields.append(f"verify_{field}")
    conversation_summary += f"⚠️ 客户曾提供不同{field}，请核实"
```

No ML required — rules on known insurance fields (VIN, policy #, plate, dates).

---

### 5. Handle missing information

| Stage | System behavior |
|-------|-----------------|
| **Detect** | Compare required fields for category vs collected |
| **Declare** | `still_needed_fields` visible to office AND customer |
| **Collect** | Ask specific question (not "provide more details") |
| **Track** | Remove from still_needed when provided in append |
| **Escalate** | After N asks without answer → broker manual follow-up |

**Intercom Fin:** Asks one question at a time; doesn't dump field list.

**Salesforce:** Required fields on Case type block close until filled.

**SearchForge today:**
- Detection: **strong** (P16-Y Missing Info 20 patterns) ✅
- Declaration: broker glance「还缺什么」✅
- Collection: customer 提交补充 exists but **tab hidden on trial**
- Track on append: **partial** — append works but merge weak

**Insurance-specific missing info priorities:**

| Category | Must-have fields | Nice-to-have |
|----------|------------------|--------------|
| Add car | VIN or year/make/model, driver, garaging | Plate, lienholder |
| Remove car | Vehicle identifier, effective date | Reason |
| Cancellation | Deadline, carrier, policy # | Payment status |
| Claim | Date, location, description | Photos, police report |
| Payment | Amount, due date, carrier | Screenshot |

---

## Multi-turn architecture (target for pilot)

```
┌─────────────────────────────────────────────────────────────┐
│                     CASE RECORD (Postgres)                   │
│  collected_fields{}  still_needed[]  conversation_summary  │
│  case_messages[]     waiting_on      lifecycle_status       │
└─────────────────────────────────────────────────────────────┘
         ↑ merge                    ↑ append
         │                          │
┌────────┴────────┐        ┌────────┴────────┐
│ triage_conversation│        │ triage_for_append │
│ (greenfield)       │        │ (follow-up)       │
└────────┬────────┘        └────────┬────────┘
         ↑                          ↑
    Message 1                   Message 2–N
    (paste / chat)              (append API)
```

**Critical path (already built, needs wiring):**

1. Broker paste msg 1 → case created
2. Customer replies in WeChat → broker pastes into **same case append box**
3. `triage_for_append()` re-runs → updates fields + summary
4. Broker sees updated glance → new copy-to-client if needed

**What's missing is NOT architecture — it's discoverability + summary merge quality.**

---

## Anti-patterns observed in enterprise systems

| Anti-pattern | Why bad for Chen Kui |
|--------------|---------------------|
| Full transcript re-triage each turn | Slow (~30s); expensive; loses structure |
| New ticket per message | Duplicate cases (already a UX bug on top paste) |
| Category re-selection on append | Customer already explained; insulting |
| Generic "please provide more info" | Office Actionability fails rubric |
| Unlimited conversation history in prompt | Context rot; hallucination |

---

## Multi-turn scorecard (benchmark targets)

| Capability | Zendesk | Intercom | SearchForge now | Pilot target |
|------------|---------|----------|-----------------|--------------|
| Thread preserved | ✅ | ✅ | ✅ backend | ✅ |
| Summary merges turns | ✅ Copilot | ✅ Fin | ⚠️ partial | ✅ P16-Y P0 |
| Correction honored | ✅ | ✅ | ❌ Y44 | ✅ |
| Missing info tracked across turns | ✅ | ✅ | ⚠️ | ✅ |
| Broker knows to append | ✅ UI | ✅ UI | ❌ 38/100 | ✅ copy/UX |
| Customer self-serve append | ✅ portal | ✅ messenger | ❌ hidden tab | ⚠️ week 3+ |

---

## 2-week multi-turn MVP (no new services)

| # | Action | Effort | Impact |
|---|--------|--------|--------|
| 1 | P16-Y P0 append summary merge | M | Fixes Y44 |
| 2 | Post-copy CTA: "客户回复了？点这里追加" | S | Fixes discoverability |
| 3 | Promote append box in reopened case glance | S | P16-M #28 |
| 4 | Correction keyword rules in triage | S | Fixes common Y44 |
| 5 | `waiting_on: customer` default after copy | S | State clarity |

**Do NOT build:** New conversation microservice, LLM-only memory, unlimited history window.

---

*End of P16-Z2 Phase 3 — Multi-Turn Intelligence Research*
