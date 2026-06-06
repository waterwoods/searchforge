# Baseline Audit — Workbench Office Tool Professionalization

**Sprint:** Workbench Office Tool Professionalization  
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
| Queue cards: quote_ready, correction, already_sent, contact needed | **Strong** | Added in WORKBENCH_HANDOFF_PROFESSIONALIZATION |
| Due tag (overdue/due today) | **Strong** | getFollowUpDueTag, getCaseAttentionState |

---

## 2. Biggest Office-Tool Weakness

**Queue cards lack broker_next_step preview.** Broker must open a case to see what to do. The compactPreview shows collected/missing summary but not the actual next step.

**Follow-up (waiting_on, next_contact_by) on queue cards** is shown via getLatestUpdateForDisplay or getCaseTrackingSummary — but it competes with "最近" and may be truncated. Due-state tag exists but follow-up could be more prominent.

---

## 3. Biggest Broker Blind-Spot Risk

**Next-step invisibility on queue.** Broker cannot prioritize by "what to do" without opening each case. Quote-ready, correction, already_sent are now visible (from prior sprint), but the actual broker_next_step is not.

---

## 4. Biggest Follow-Up Visibility Gap

**Follow-up block in case detail is below the fold.** The "当前状态" card with waiting_on, next_contact_by is in a Row below the main "Case 整理" block. Per spec, follow-up should be above the fold as part of the working case sheet.

**Queue cards:** getCaseTrackingSummary shows "Waiting on X · Next contact by Y" but it's in small secondary text. Due tag is present; could be more prominent when overdue/due today.

---

## 5. Biggest Commercial-Feel Gap

**Case detail still feels like a panel rather than a case sheet.** Sections are present but the hierarchy could be clearer. "Case 整理" is one large card; follow-up is in a separate "当前状态" card below. A broker opening a case should immediately see: focus → next step → customer → collected → still needed → materials → follow-up.

---

## 6. Classification Summary

| Category | Items |
|----------|-------|
| **Strong** | Case focus, next move, collected/still_needed, human confirmation, urgency, correction/already_sent, quote-ready, contact, attachment, queue signals (from prior sprint), due tag |
| **Acceptable** | Lifecycle, full conversation, queue readiness label |
| **Weak** | Queue card: broker_next_step preview; case detail: follow-up above fold; case detail: section hierarchy |
| **High-value to improve now** | Queue card next-step preview; case detail follow-up prominence; case detail section hierarchy |

---

*End of baseline audit*
