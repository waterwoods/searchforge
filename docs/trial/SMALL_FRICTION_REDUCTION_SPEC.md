# Small Friction Reduction Spec

**Sprint:** Trial Launch + Fix-Now Queue Sprint  
**Created:** 2026-03-18  
**Purpose:** Choose 1–2 small, high-value, low-risk improvements that help the trial run more smoothly.

---

## 1. Chosen Improvements (This Sprint)

### Improvement 1: Copy Case Snapshot

**What:** Add a "Copy case snapshot" button that copies a compact text summary of the current case (case focus, next move, collected, still needed, draft preview) to clipboard.

**Why it matters:** During trial, founder or broker may want to quickly share a case for feedback, or paste into observation log. Manual copy-paste of multiple sections is friction.

**Why now:** Low risk; single button; helps evidence capture and broker handoff communication.

**Scope:** One button in case card action block; copies ~200–400 char summary.

---

### Improvement 2: Trial Mode Label (Optional / Lightweight)

**What:** Subtle "Trial" or "试用中" label in workbench header when in trial context — or a small hint in the Customer Entry area: "Paste customer message (WeChat/email) — 粘贴客户消息".

**Why it matters:** Broker may forget they're in trial; a gentle reminder reduces confusion. Also reinforces "paste here" for first-time users.

**Why now:** Very low risk; CSS/text only; improves Day 1 clarity.

**Scope:** One line of text or badge; no logic change.

---

## 2. Justification Summary

| Improvement | Value | Risk | Effort |
|-------------|-------|------|--------|
| Copy case snapshot | High — evidence capture, handoff sharing | Low | Medium |
| Trial hint / paste hint | Medium — Day 1 clarity | Very low | Low |

**Decision:** Implement Copy case snapshot as primary; add paste hint if time permits.

---

## 3. Deferred (Not This Sprint)

| Idea | Why deferred |
|------|--------------|
| Full "Copy trial summary" | More complex; evidence pack is manual for now |
| Recent message grouping change | Layout already correct per spec |
| Correction badge repositioning | Already visible |
| Full admin portal | Out of scope |

---

*End of Small Friction Reduction Spec*
