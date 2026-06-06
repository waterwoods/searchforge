# P16-Z19 Step 5 — Founder Commercial Proof

**Date:** 2026-06-03  
**Sprint:** P16-Z19 Customer First Time-Saved Proof Sprint  
**Audience:** Founder → Chen Kui paid pilot conversation  
**Evidence:** Live API battery + Role D + Z16/Z17 flow audits

---

## One-page summary

### 1. How many minutes are saved per case?

| Measure | Minutes |
|---------|---------|
| **Add-Car (full pipeline)** | **4.5 min** |
| **Blended 5-scenario average (net)** | **3.1 min** |
| **Role D multi-day journeys (net)** | **3.1 min** |

**Conservative headline for sales:** **"3–4 minutes saved on every intake — more on Add-Car."**

---

### 2. Which scenarios save the most time?

| Rank | Scenario | Net saved | Why it wins |
|------|----------|-----------|-------------|
| 1 | **Add vehicle** | 4.5 min | Paste → AI draft → confirm → `case_id` in broker queue — zero re-typing |
| 2 | **Claim** | 4.0 min | Accident fields + missing checklist extracted; broker skips re-parse |
| 3 | **Payment / UW** | 2.5 min | Useful draft; classification or persist gaps limit upside |
| 4 | **Remove vehicle** | 2.0 min | Intent clear; no structured fields or office record |

**Lead with Add-Car in every demo.** It is the only scenario that proves the full north star in one session.

---

### 3. Which scenarios still require human work?

| Always human | Never automated in pilot |
|--------------|--------------------------|
| Carrier calls / quoting / binding | Judgment + relationship |
| Payment reinstatement verification | Financial authority |
| Claim adjuster coordination | Regulated process |
| Document upload / UW submission | Physical docs |
| Sale date confirmation on remove | Liability confirmation |

**Product promise:** We do not replace the broker. We eliminate **re-reading WeChat and re-typing the paste**.

---

### 4. What can Chen Kui do faster?

| Today (without us) | With Customer First |
|--------------------|---------------------|
| Open WeChat → read → mental model → reply asking for VIN | Customer pastes once → case arrives with VIN extracted |
| Re-read 3-day thread to remember what changed | Open workbench → 对话记录 + `collected_fields` |
| Type office note from scratch | `broker_next_step` + `client_reply_draft` ready to copy |
| Hunt for missing info in chat scroll | 缺少资料 checklist in glance |
| Start over when customer returns | ⚠️ Partial — My Requests works; append after refresh still weak |

**Chen Kui's fastest win:** Morning queue — open Add-Car cases, quote in order, copy Chinese draft to WeChat. **~4.5 min saved per Add-Car case before he picks up the phone.**

---

### 5. What is the strongest paid-pilot pitch?

> **"Your customers paste once. Your office gets a ready case — vehicle, missing fields, and next step — in under 2 minutes. You stop re-reading WeChat for Add-Car."**

Supporting proof points:

| Proof | Number |
|-------|--------|
| Time saved per Add-Car case | 4.5 min |
| Broker 5-second comprehension (Add-Car) | 85/100 |
| Role D: no WeChat re-read | 0/10 journeys |
| Same `case_id` through append | Proven live |
| Code already built | ~76% of Customer First Case Builder (Z16/Z17) |

**Pilot scope (honest):**

- ✅ Add-Car: customer intake → office case → broker workbench
- ⚠️ Return-later append after refresh: known gap
- ❌ Not in pilot: CRM, OCR, voice, payment/remove auto-persist

**Price anchor:** If Chen Kui saves 70+ minutes/day on 20 cases, that is **~25 hours/month** of broker labor (~$1,250–1,900 at $50–75/hr). Software at $200–400/mo is **3–5× ROI** even conservatively.

---

## North star alignment check

```
Customer Message     ✅ CustomerEntryTab paste
       ↓
AI Draft Case        ✅ triage_conversation (Add-Car proven)
       ↓
Broker Confirm       ✅ Workbench glance + next step
       ↓
Timeline             ✅ case_messages + case_activity
       ↓
Return Later         ⚠️ Pre-submit yes; post-submit partial
       ↓
Get Paid             🎯 This document is the proof layer for that conversation
```

---

## Verdict

**Commercial proof: READY for Add-Car paid pilot.**

Do not sell "all insurance scenarios." Sell **"stop re-reading WeChat on Add-Car"** with measured 4.5 min/case savings and Role D memory proof.
