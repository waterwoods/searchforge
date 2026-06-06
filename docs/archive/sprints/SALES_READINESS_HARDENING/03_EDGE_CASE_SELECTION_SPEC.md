# Edge Case Selection Spec

**Sprint:** Sales Readiness Hardening Sprint  
**Created:** 2026-03-17

---

## 1. Selection Principle

**Do NOT fix all edge cases.** Choose the 2–3 most commercially important.

---

## 2. Selected Edge Cases (This Sprint)

### Edge Case 1: Billing Clarification Follow-Up ("我发你了" / "微信发你了")

| Aspect | Detail |
|--------|--------|
| **Why it matters commercially** | High-frequency; payment/cancellation risk; customer says "I already sent it" → broker must verify receipt, not re-ask blindly |
| **How it breaks trust today** | If system keeps asking for notice/screenshot after customer says "我发你了", feels robotic and wastes broker time |
| **Why worth fixing now** | TOP_COMMERCIAL_DEEPENING added MT40; need to verify and harden. Billing + already_sent = same-day action path. |
| **Good behavior** | T2 "通知我发你了，你看下" → already_sent handoff; broker_next_step: "Verify receipt of notice/screenshot; confirm with client if needed." |

**Status:** MT40 exists in configs; verify triage routes correctly and handoff is warm.

---

### Edge Case 2: Talk to Agent Inserted Mid-Flow

| Aspect | Detail |
|--------|--------|
| **Why it matters commercially** | Customer may try to reach human mid-conversation (e.g. after 2 turns of add-car, says "算了，我想直接跟人说") |
| **How it breaks trust today** | Only button works; free-text "联系人工" not detected → system continues triage, customer feels ignored |
| **Why worth fixing now** | Trust-critical; low implementation cost (add markers + early check in triage) |
| **Good behavior** | Any turn: "联系人工" / "联系陈奎" / "我要找人工" → immediate handoff; prior context preserved in handoff |

**Status:** Not implemented. Add markers + triage check.

---

### Edge Case 3: Late Correction After Near-Handoff

| Aspect | Detail |
|--------|--------|
| **Why it matters commercially** | Customer corrects ("不是，是另一辆" / "说错了，我老婆开") right before handoff; broker must see correction |
| **How it breaks trust today** | Correction may not surface clearly in workbench; broker acts on wrong info |
| **Why worth fixing now** | Workbench already has correction badge; ensure follow_up_type=correction survives append and handoff |
| **Good behavior** | Correction badge visible; conversation_summary or context hint includes "Customer corrected: …" |

**Status:** Partially implemented (correction badge). Verify append-message and handoff preserve it.

---

## 3. Explicitly Deferred (This Sprint)

| Edge Case | Reason |
|-----------|--------|
| Mixed-intent with human escalation (e.g. "加车报价，但我想跟人说") | Lower frequency; can defer to next sprint |
| already_sent + clarification mixed path | Handled by reply strategy (answer first); verify only |
| Renewal/premium partial info correction | Lower priority; add-car correction higher |

---

## 4. Verification Plan

- Run `run_inbox_triage_scenarios.py`, `run_multi_turn_simulations.py`
- Run billing "我发你了" scenario (MT40 or equivalent)
- Run free-text "联系人工" in triage
- Run append-message with correction; verify badge

---

*End of Edge Case Selection Spec*
