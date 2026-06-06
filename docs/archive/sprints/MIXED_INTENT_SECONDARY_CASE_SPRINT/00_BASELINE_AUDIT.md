# Baseline Audit — Mixed-Intent Handling

**Sprint:** Mixed-Intent + Secondary Case Strategy  
**Purpose:** Honest audit of current system from mixed-intent perspective.

---

## 1. Current Triage Behavior

| Area | Current State |
|------|---------------|
| **Topic switching** | flow_count >= 2 → routes to LLM (triage.py `_is_turn1_lightweight_candidate`) |
| **Primary selection** | `_classify_with_guardrails` picks one category; claim+payment → claim |
| **Secondary visibility** | None. No secondary_issue_note; summary is single intent_hint |
| **Draft for mixed** | Some hardcoded: payment+document, premium+document, add-car+garaging |

---

## 2. Where Case Logic Becomes Messy

| Risk | Location | Impact |
|------|----------|--------|
| **Single intent_hint** | `_build_conversation_summary` | Secondary goal invisible to broker |
| **Single broker_next_step** | category_templates | No "Also" for secondary |
| **No secondary_issue_note** | case_store, triage | Broker cannot see "customer also asked X" |
| **Draft sometimes misses secondary** | run_complex_adversarial_simulation | MI-AC1, MI-D1: document confusion not always in draft |

---

## 3. Where Summaries May Become Overloaded

| Risk | Current | When |
|------|---------|------|
| **Generic "Latest: ..."** | Summary ends with latest snippet | Long mixed message → snippet truncates |
| **No structure for "also"** | No field | Broker infers from raw text only |
| **Collected/still_needed** | Add-car, missing_doc only | Other categories: no structured collected |

---

## 4. Where Broker Follow-Up Could Become Confusing

| Risk | Why |
|------|-----|
| **Broker does not know there was a second question** | No secondary_issue_note |
| **broker_next_step ignores secondary** | Single action only |
| **Case looks single-goal but customer asked two things** | Summary hides second |

---

## 5. What Already Works Acceptably

| Area | Status |
|------|--------|
| **Mixed routes to LLM** | flow_count >= 2 → LLM path |
| **Claim + payment → claim** | Existing rule |
| **Payment + document already sent** | Draft appends "如果材料说发过了，我这边也帮你核对" |
| **Premium + document already sent** | Same pattern |
| **Add-car + garaging confusion** | Draft adds garaging explanation |
| **Mixed-intent sim** | 14 scenarios; primary usually recognized |
| **correction / clarification** | context_hint "Customer corrected/clarified" |

---

## 6. Classification

| Level | Items |
|-------|-------|
| **Already acceptable** | Mixed→LLM routing; claim+payment; payment+doc; premium+doc; add-car+garaging; correction hint |
| **Weak** | Secondary not in summary; no secondary_issue_note; draft sometimes misses secondary (MI-AC1, MI-D1) |
| **Risky for trial** | Broker cannot see "customer also asked X"; case looks single when it is mixed |
| **High-value to improve now** | Add secondary_issue_note to summary; improve draft for document confusion in add-car |

---

## 7. Biggest Gaps

| Gap | Description |
|-----|-------------|
| **Biggest mixed-intent weakness** | Secondary intent is invisible to broker; no structured "Also asked" |
| **Biggest case-pollution risk** | Low today (we pick one category); risk is broker missing second topic |
| **Biggest broker-confusion risk** | Broker reads case, acts on primary, misses that customer also asked about X |

---

*End of Baseline Audit*
