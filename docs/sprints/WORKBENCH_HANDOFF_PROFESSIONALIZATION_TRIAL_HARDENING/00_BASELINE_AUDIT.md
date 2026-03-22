# Baseline Audit — Workbench Handoff Professionalization

**Sprint:** Workbench Handoff Professionalization + Trial Hardening  
**Date:** 2026-03-20

---

## 1. Strongest Current Parts

| Element | Status | Notes |
|---------|--------|-------|
| Case focus | **Strong** | Tag from inferred or structured |
| Your next move (broker_next_step) | **Strong** | Bold, labeled "您的下一步" |
| Collected / Still needed chips | **Strong** | Green/orange chips |
| Human confirmation | **Strong** | Badge when applicable |
| Urgency | **Strong** | Same-day action tag |
| Correction / already_sent in detail | **Strong** | Badges in case detail view |
| Quote-ready in detail | **Strong** | Tag when add-car |
| Contact block in detail | **Strong** | Name/phone or "needed" |
| Attachment block in detail | **Strong** | PaperClip + upload |
| Recent customer messages | **Strong** | Last 2–3 in case detail |

---

## 2. Biggest Workbench/Handoff Weakness

**Queue cards lack key signals for scan-at-a-glance.** Broker must open a case to see:
- quote_ready_status (only in detail)
- correction / already_sent (only in detail)
- Contact missing (only in detail)

Queue cards show: case focus, attention, readiness label, attachment count, urgency — but **not** correction/already_sent or quote-ready status explicitly.

---

## 3. Biggest Broker Blind-Spot Risk

**Correction and already_sent are invisible on queue cards.** Broker may open a "Missing document" case thinking it needs a request, when the customer said "I already sent it" — leading to duplicate requests and frustration.

---

## 4. Biggest Office-Usability Gap

**broker_next_step can still be vague** in some scenarios:
- "Review and act on {category}" fallback
- Some add-car cases may not mention contact when name/phone missing
- Missing_document + already_sent: sometimes generic

---

## 5. Biggest Commercial-Feel Gap

**Queue cards feel functional but not fully professional.** Missing:
- Quote-ready tag on add-car cards (relies on readiness label which is derived)
- Correction/already_sent badge on cards
- Clear "what to do" preview without opening

---

## 6. Classification Summary

| Category | Items |
|----------|-------|
| **Strong** | Case focus, next move, collected/still_needed, human confirmation, urgency, correction/already_sent in detail, quote-ready in detail, contact, attachment |
| **Acceptable** | Lifecycle, full conversation, queue readiness label |
| **Weak** | Queue card: quote_ready tag, correction/already_sent badge |
| **High-value to improve now** | Queue card signals; broker_next_step specificity for edge cases |

---

*End of baseline audit*
