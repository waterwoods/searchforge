# Handoff Readiness UX Spec

**Sprint:** Workbench Handoff Readiness  
**Purpose:** Define what the office-side interface should make obvious.

---

## 1. What the Office Should See First (Above the Fold)

| Order | Section | Content | Why |
|-------|---------|---------|-----|
| 1 | **Case focus** | Add car quote, Premium review, Missing document, etc. | Triage at a glance |
| 2 | **Lifecycle / status** | Handed off / Office follow-up; Ready for handoff / Collecting | Stage clarity |
| 3 | **Recent customer messages** | Last 2–3 original customer messages, labeled | Broker sees what customer said without parsing |
| 4 | **Your next move** | One operational sentence | Action clarity |
| 5 | **Collected** | Green chips | Avoid re-asking |
| 6 | **Still needed** | Orange chips | Next ask clarity |

---

## 2. What Should Be Visible Without Extra Clicking

- Recent customer messages (2–3 most recent)
- Collected / still needed chips
- Lifecycle status
- Next move
- Correction / context hint when present (e.g. "Customer corrected", "Client says already sent")

---

## 3. What Can Be Collapsed or Secondary

- Full conversation (raw [客户]/[系统] text) — below fold, collapsible
- Client prep
- Draft to review — secondary card
- Broker notes — secondary

---

## 4. Handoff Quality / Correction Visibility

When `follow_up_type` or conversation_summary indicates:
- **Correction** — Show badge: "Customer corrected/clarified"
- **Already sent** — Show badge: "Client says already sent"
- **Human confirmation** — Show badge: "Verify before acting: …"

---

## 5. Queue-Level (Recent Cases List)

Each case card in the queue should show:
- Case focus
- Compact preview of last customer message (or first 80 chars of source_text)
- Collected / still needed hint when add-car or structured
- Lifecycle tag (Handed off / Office follow-up)
- Urgency

---

*End of UX spec*
