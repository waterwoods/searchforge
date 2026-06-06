# P16-Z12 Phase 6 — Founder-as-Chen-Kui Walkthrough

**Date:** 2026-06-02  
**Basis:** Deployed API responses (Phase 5) + Preview UI load (SSO off, CORS fail for live triage)

Scoring: 0–100 per case on five questions (20 pts each).

---

## Case 1 — Payment

| Question | Score | Notes |
|----------|-------|-------|
| Understand case in 5 sec? | 5/20 | Reads as generic question, not "扣款失败" |
| What is missing? | 8/20 | No structured missing list |
| Who is waiting on whom? | 0/20 | No waiting-on |
| What to send client? | 10/20 | Vague English next step |
| Reduce WeChat reread? | 5/20 | Would re-read WeChat for 420 / 换卡 / 取消 |

**Case 1 score: 28/100**

---

## Case 2 — Remove vehicle

| Question | Score | Notes |
|----------|-------|-------|
| Understand case in 5 sec? | 12/20 | `remove_car` service hints intent; category says missing doc |
| What is missing? | 10/20 | Not visible without office checklist |
| Who is waiting on whom? | 0/20 | Absent |
| What to send client? | 8/20 | Generic doc-verify copy, not 销售证明 |
| Reduce WeChat reread? | 12/20 | Partial — sold Camry not in title |

**Case 2 score: 42/100**

---

## Case 3 — Claim

| Question | Score | Notes |
|----------|-------|-------|
| Understand case in 5 sec? | 0/20 | Misclassified as add-car |
| What is missing? | 0/20 | Wrong still_needed (VIN/zip for new car) |
| Who is waiting on whom? | 0/20 | Absent |
| What to send client? | 5/20 | Wrong lane guidance |
| Reduce WeChat reread? | 0/20 | Plate 8ABC123 / 8500 / John not in glance |

**Case 3 score: 5/100**

---

## Overall founder score

**(28 + 42 + 5) / 3 ≈ 25/100**

---

## Top 10 confusions

1. Payment reads as **general inquiry**, not billing/lapse.
2. No **office_case_title** on deployed triage JSON.
3. No **suggested_waiting_on** on deployed responses.
4. Claim thread routed to **add_car** — fatal for Chen Kui trust.
5. **8500** and **8ABC123** not in collected_fields on API.
6. **理赔员 John** not surfaced.
7. CORS blocks Preview → API — founder may think UI is broken.
8. English **broker_next_step** on Chinese paste.
9. Remove case labeled **missing_document** not "卖车删车".
10. Preview backend **7+ commits behind** local branch — expectation mismatch after local green batteries.
