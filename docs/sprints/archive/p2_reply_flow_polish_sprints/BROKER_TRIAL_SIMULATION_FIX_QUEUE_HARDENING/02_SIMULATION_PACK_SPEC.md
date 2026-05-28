# Simulation Pack Spec — Broker-Style Realistic Flows

**Sprint:** Broker Trial Simulation + Fix Queue Hardening Sprint  
**Created:** 2026-03-19

---

## 1. Required Flow Coverage

| # | Flow | Business goal | Why it matters | Likely failure mode | Good behavior |
|---|------|---------------|----------------|--------------------|----------------|
| 1 | **Cancellation warning** | Urgency; same-day action | Highest trial value; first demo case | Generic reply; wrong routing | Route to cancellation_warning; urgency; broker_next_step concrete |
| 2 | **Missing document / already sent** | Operational follow-up | "Client says already sent" — real office pain | Ignores "already sent"; re-asks | Verify receipt; broker_next_step: verify whether resubmitted items received |
| 3 | **Add-car quote** | Revenue; multi-turn | High-frequency; Collected chips | First reply too generic; wrong handoff timing | Ask year/zip/delivery; handoff at turn 2–3 |
| 4 | **Premium review / renewal increase** | Retention | Repetitive office work | Generic; no retention framing | Ask policy/bill; retention-style follow-up |
| 5 | **Talk to agent** | Customer wants human | Trust-breaking if wrong | Routes to wrong intent; generic reply | Route to customer_requested_human; handoff-ready immediately |
| 6 | **Mixed-intent case** | Real-world messiness | Customer combines 2+ intents | Picks wrong primary; loses second | Route to primary; acknowledge second; or ask to clarify |
| 7 | **Correction-heavy case** | Turn 2/3 correction | "Not X, it's Y" — common | Ignores correction; repeats wrong | Use correction; update category/collected |
| 8 | **Vague/short customer case** | Real messages are short | "帮我" / "在吗" | Too generic; forces handoff too early | Ask one clarifying question; don't hand off turn 1 |
| 9 | **Already sent / already paid** | Document/payment confusion | Client says sent; system re-asks | Re-asks for what was sent | Verify receipt; broker_next_step: verify |
| 10 | **Broker reopen/append** | Case continuation | Broker adds follow-up to existing case | Loses context; wrong collected/still_needed | Append uses case context; client_id preserved |

---

## 2. Realistic Broker/Customer Behavior (Non-Negotiable)

Simulations MUST include:
- Short / vague customer messages
- Mixed Chinese/English
- Emotionally urgent phrases (急、今天、马上)
- Correction in turn 2 or 3
- Already sent / already paid
- Talk to agent mid-flow
- Mixed intent
- Broker reopening case and appending follow-up
- Switching between client contexts if useful

---

## 3. Existing Simulation Packs (Baseline)

| Pack | Script | Coverage |
|------|--------|----------|
| Inbox triage | `run_inbox_triage_scenarios.py` | 64 single-turn scenarios |
| Multi-turn | `run_multi_turn_simulations.py` | 41 multi-turn (MT1–MT41) |
| Adversarial | `run_adversarial_simulation.py` | 27 adversarial |
| Complex adversarial | `run_complex_adversarial_simulation.py` | 23 mixed-intent/long |
| Simulation Assistant | `run_simulation_assistant_scenarios.py` | 27 (SIM1–SIM5, R1–R8, FAQ) |
| Follow-up append | `run_follow_up_append_simulations.py` | 5 append flows |

---

## 4. Gap Analysis

| Gap | Current | Needed |
|-----|---------|--------|
| Vague/short | Some in adversarial | Explicit "帮我" / "在吗" / "?" |
| Correction-heavy | FA5 (corrected notice) | More: wrong vehicle, wrong doc type |
| Already-sent prominence | FA4 | More flows; verify_receipt visibility |
| Talk-to-agent mid-flow | Single-turn in inbox | Multi-turn: add-car → "联系人工" |
| Broker reopen/append | FA1–FA5 | Client-aware continuity; reopen context |
| Mixed-intent | Complex adversarial | Explicit broker-style mixed (add-car + premium) |

---

*End of Simulation Pack Spec*
