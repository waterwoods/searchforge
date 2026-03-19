# Baseline Audit and 10–20 Point Breakdown

**Sprint:** Workbench Handoff Readiness  
**Date:** 2026-03-17

---

## 1. Baseline Audit

### 1.1 What the Broker Can Already See

| Element | Status | Notes |
|---------|--------|-------|
| Case focus | **Strong** | Tag from inferred or structured |
| Your next move | **Strong** | broker_next_step bold |
| Collected chips | **Strong** | Green chips when structured |
| Still needed chips | **Strong** | Orange chips when structured |
| Lifecycle status | **Acceptable** | Handed off / Office follow-up tag |
| Full conversation | **Acceptable** | source_text in card below |
| Human confirmation | **Strong** | Badge when applicable |
| Urgency | **Strong** | Same-day action tag |

### 1.2 What Is Still Hidden or Weak

| Element | Status | Notes |
|---------|--------|-------|
| **Recent customer messages** | **Too thin** | Only source_text blob; broker must parse |
| **Correction/context hint** | **Weak** | follow_up_type in backend but not surfaced |
| **Message count** | **Hidden** | In conversation_summary only |
| **case_messages** | **Hidden** | API returns it; UI not consuming |

### 1.3 What Still Feels Too Debug-Like

- Full conversation shown as raw [客户]/[系统] blob — no structured message list
- No "Recent customer said" section — broker re-reads entire conversation
- Correction/context hints buried in conversation_summary text

### 1.4 What Still Requires Too Much Re-reading

- Broker must parse source_text to find "what did customer say last?"
- Multi-turn cases: no easy way to see turn 1 vs turn 2 vs turn 3

### 1.5 Classification Summary

| Category | Items |
|----------|-------|
| **Strong** | Case focus, next move, collected/still_needed chips, human confirmation, urgency |
| **Acceptable** | Lifecycle, full conversation |
| **Weak** | Correction badge, context hint |
| **Too thin** | Recent customer messages |
| **Commercially important** | Recent messages, next action, correction |

### 1.6 Biggest Current Handoff Weakness

**Broker cannot quickly see what the customer most recently said.** Only source_text blob; no structured "last 2–3 customer messages" above the fold.

### 1.7 Biggest Source of Broker Rework

Re-reading full conversation to understand "what did they say?" and "what did they correct?"

### 1.8 Biggest Source of "Still a Demo" Feeling

- Raw source_text feels like debug output
- No "Recent customer messages" section
- Correction/context not surfaced as badges

---

## 2. 10–20 Point Breakdown

| # | Item | Decision |
|---|------|-----------|
| 1 | **Workbench views in scope** | Case detail card (opened case); queue cards unchanged |
| 2 | **Office users see first** | Case focus, lifecycle, recent customer messages, next move |
| 3 | **Recent customer messages** | Show last 2–3 from case_messages (role=customer) |
| 4 | **How many recent** | 2–3 messages |
| 5 | **Collected fields** | Green chips; already present; keep above fold |
| 6 | **Still needed** | Orange chips; already present; keep above fold |
| 7 | **Lifecycle status** | Tag: Handed off / Office follow-up |
| 8 | **Next office action** | "Your next move" bold; add correction badge when follow_up_type |
| 9 | **Corrections/clarifications** | Badge when follow_up_type in (correction, already_sent) |
| 10 | **Case summary vs raw** | Summary above; raw below fold |
| 11 | **Above the fold** | Case focus, lifecycle, recent messages, next move, collected/still_needed |
| 12 | **Collapsed/secondary** | Full conversation, client prep, draft |
| 13 | **Source of truth** | case_messages; source_text derived |
| 14 | **Frontend contract** | Add case_messages, follow_up_type to SavedCase |
| 15 | **Backend contract** | Already returns case_messages, follow_up_type |
| 16 | **Guardrails/tests** | guardrail_inbox_triage, unified_intake_smoke_check, npm build |
| 17 | **Intentionally deferred** | Field values in chips; queue-level enhancements |
| 18 | **Reduces broker follow-up** | Recent messages + correction badge |
| 19 | **Trial-ready enough** | When broker can understand case in &lt;5 sec |
| 20 | **Next action** | Clear "Your next move" + optional correction badge |

---

*End of baseline audit*
