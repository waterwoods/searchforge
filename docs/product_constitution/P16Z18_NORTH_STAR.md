# P16-Z18 North Star Review

**Date:** 2026-06-03  
**Sprint:** P16-Z18 Product Constitution Refresh  
**Sources:** P16-Z3 through P16-Z17 · P16-Z25 · P16-Z9 SSOT · live case `case_98f4ac099d15`

---

## What is the true product?

**Not** a CRM, chatbot, insurance software platform, or SearchForge lab.

**The true product** is a **Customer First intake loop** for a California auto insurance office:

```
Customer sends a messy message
    → AI turns it into a draft case (structured fields, gaps, next step)
    → Broker confirms or corrects
    → Case persists with a case_id and timeline
    → Customer can return later and append to the same case
    → Office acts and closes
```

The broker workbench is the **confirmation layer**, not the product entry point.  
WeChat remains the channel in weeks 1–2; the **customer tab** (`CustomerEntryTab`) is real code at ~76%, not a future build.

Evidence: P16-Z16/Z17 live proof — `CustomerEntryTab` → `save_case` → `case_id` → append → `BrokerWorkbenchTab` on the same record.

---

## OLD NORTH STAR

> **Turn messy client messages into a time-bound office obligation with a clear next action and a traceable close — in one paste, under one minute.**

**Source:** P16-Z2, P16-Z2.5, P16-Z9 (broker-paste framing)

**What it got right:**
- Chaos → case → next action → close
- Not CRM / not chatbot
- Under-one-minute wedge for Turn 1
- Append and timeline as subordinate loops

**What it missed (discovered Z16–Z17):**
- Assumed **broker paste** as primary entry; customer-facing Case Builder already exists
- Underweighted **return later** and **same case_id** as product-defining
- Optimized for broker front door (Cap 1) over Customer First loop
- "One paste" reads as broker-only; customer sends messages across days

**Broker sub-loop (still valid, subordinate):**

> 整理 → 复制发出 → 在等客户 → 客户回复 → 同案追加 → 看得见变了什么 → 再复制

---

## NEW NORTH STAR

> **Turn a customer's messy message into a draft case the office can confirm — same case across days, clear next action, traceable timeline — until the request is closed and the office gets paid.**

**Customer-first pipeline (canonical):**

```
Customer Message → AI Draft Case → Broker Confirm → Timeline → Return Later → Close → Get Paid
```

**Success means:**
1. Customer message becomes a **draft case** (not a chat reply)
2. Broker **confirms** — does not re-type from WeChat
3. **case_id** survives refresh and multi-day append
4. **Timeline** proves what happened (broker sees it today; customer wiring in progress)
5. Customer can **return later** without starting over
6. Office closes the obligation → **first paying broker**

---

## ONE-SENTENCE VERSION

> **Messy customer message → AI draft case → broker confirms → same case tomorrow → get paid.**

---

## 12-YEAR-OLD VERSION

> **You text the insurance office what you need. The computer turns it into a neat request. The broker checks it, fixes anything wrong, and handles it. You can come back later and add more info — it all stays on the same request until it's done.**

---

## North star evolution table

| Era | Sprint | Entry point | North star emphasis |
|-----|--------|-------------|---------------------|
| Z2–Z2.5 | Strategic RE | Broker paste | Office-executable case in one paste |
| Z3–Z10 | Engine + memory | Broker paste + append | Time-bound obligation + multi-turn memory |
| Z9 | SSOT | Broker-first capacities | Same sentence; L5 = Role D gates |
| Z16–Z17 | Customer Builder reality | **Customer tab** | Case Builder exists; finish wiring return-later |
| **Z18** | Constitution refresh | **Customer First** | Draft case → confirm → timeline → return → paid |

---

## What does NOT change

| Item | Why |
|------|-----|
| Not a CRM / chatbot / insurance platform | Every sprint Z3–Z17 reaffirmed |
| Reuse `triage.py`, `case_store.py`, existing UI | Z0, Z3, Z16, Z17 — no greenfield |
| WeChat is channel; product is case memory | Z2 soul, Z4 continuity |
| Turn 1 speed still matters | P16-Y 88.6 avg |
| Payment = manual invoice until Chen Kui pays | Z3, Z9, Z12 |

---

## 90-day success metrics (subordinate to north star)

| Metric | Target | Battery / proof |
|--------|--------|-----------------|
| Customer Builder score | **≥90** (from 76) | Z17 scorecard + 3-day Tesla walkthrough |
| Post-submit return → append | Works without founder narration | Browser E2E after wiring |
| Broker review without WeChat re-read | Role D reread ≥80 | `run_role_d_memory_battery.py` |
| Single-turn intelligence | P16-Y ≥88 | `run_p16y_case_battery.py` |
| Commercial proof | Chen Kui supervised → invoice | Observation log |
| Deployed path | Cold URL works | `trial_launch_check.sh` |

---

## Verdict

**Update the north star.** The product is no longer "broker paste tool first." It is **Customer First Case Builder** with broker confirmation — built, ~76% wired, 3–4 engineer-days from supervised pilot.

Do not revert to broker-only framing in docs or sprints. Broker paste remains a **valid wedge** for Chen Kui Day 0, not the product definition.

---

*End of P16-Z18 Phase 1 — North Star Review*
