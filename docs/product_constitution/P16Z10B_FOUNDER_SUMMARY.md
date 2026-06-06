# P16-Z10B — Founder Summary (Phase 10)

**Date:** 2026-06-02  
**Sprint:** Memory Completion — waiting-on inference + claims retention  
**Constraint honored:** No new services · no new DB · `triage.py` + battery only

---

## TOP 20 DISCOVERIES

1. `waiting_on` PATCH stack was production-ready; only inference was missing.  
2. Production enum uses **`broker`** not `office` for back-office wait.  
3. Z10A generic merge was the right spine for claims — Z10B only added literals + lane guard.  
4. Claims battery failed mainly on **`unclear` mis-route**, not missing FNOL templates.  
5. `total loss` / adjuster language must be in `_is_claim_intake_request` — not only FNOL markers.  
6. Literal tokens (`plate_7XYZ999`, `claim_amount_4200`) drive oracle retention, not booleans alone.  
7. VIN digits were mistaken for claim amounts — window guard required.  
8. `suggested_waiting_on` lifts reread when payment confirmation tokens added to blob.  
9. Day-3 “any update” pings route to carrier/UW via category + thread context.  
10. CL06 injury thread hits **100%** with `injury_neck` / `injury_mri` / `rear_end` tokens.  
11. CL03 mis-route fixed by claim lane guard over missing_document.  
12. Claims append must pass `persisted_collected_fields` — same fix as Z10A journeys.  
13. P16-Y **88.6** — no regression from claim/waiting heuristics.  
14. Role D reread **82.6** — crosses 80 bar with payment/cancel literal enrichments.  
15. Need WeChat stays **0/10** on journeys.  
16. Waiting battery **9/9** — exceeds 7/9 target.  
17. `$420` / `#88291` belong in collected as `payment_amount_420` / `payment_confirmation_88291`.  
18. Chinese cancel keywords need explicit tokens for bilingual reread (`cancel_notice_zh`).  
19. Summary claim `Collected:` line is high-ROI for broker scan.  
20. Chen Kui can pilot 3-day claim **with assistant SOP** — not fully unattended.

---

## TOP 10 WAITING_ON IMPROVEMENTS

1. `_suggest_waiting_on()` heuristic in `triage.py`  
2. `suggested_waiting_on` optional triage field  
3. Carrier: adjuster / 保险公司 / carrier delay phrases  
4. Underwriting: UW still reviewing / billing+UW update  
5. Client: 还缺材料 / still_needed alignment  
6. Broker: quote / refund / 便宜方案  
7. Status-ping routing (payment → carrier, UW form → underwriting)  
8. `verify_carrier_received` → carrier suggest  
9. Battery 9-scenario suite in `run_role_d_memory_battery.py`  
10. **0/9 → 9/9** auto-detect on Role D phrases

---

## TOP 10 CLAIMS RETENTION IMPROVEMENTS

1. Extended `_is_claim_intake_request` for claim-status language  
2. `_thread_is_claim_lane` + persisted claim memory  
3. `_augment_claim_collected_from_merged` literal tokens  
4. `_extract_plate_hint` / claim # / amount extractors  
5. `total_loss` / `total_loss_disputed` tokens  
6. Injury + rear-end + 101 location tokens  
7. Claim summary `Collected:` headline  
8. Missing-doc vs claim lane guard  
9. Claims battery append `reply_truth_context`  
10. **36% → 71%** keyword retention

---

## TOP 10 REUSES

1. `_merge_persisted_collected` (Z10A)  
2. `case_store` `waiting_on` model — unchanged  
3. `update_case_follow_up` PATCH — unchanged  
4. `_extract_policy_number_hint`  
5. `_extract_payment_amount_hint` (+ literal suffix)  
6. Claim templates Turn-1  
7. `_prepend_prior_customer_turn_on_correction` (Z6)  
8. `run_role_d_memory_battery.py` framework  
9. `guardrail_inbox_triage.sh`  
10. `run_p16y_case_battery.py`

---

## TOP 10 THINGS NOT BUILT

1. WaitingOnEngine service  
2. Auto-PATCH `waiting_on` on triage  
3. `next_contact_by` auto-suggest from deadline  
4. Post-append “谁在等谁?” UI modal  
5. New claims table / API  
6. OCR / image plate reader  
7. Deadline countdown widget  
8. Expanded follow-up editor UX  
9. Live UI re-validation pass  
10. Stripe / auth / multi-tenant

---

## SCORES

| Metric | Before (Z10A) | After (Z10B) |
|--------|---------------|--------------|
| **ROLE D REREAD** | 75.8 | **82.6** |
| **NEED WECHAT** | 0/10 | **0/10** |
| **CLAIMS RETENTION** | 36% | **71%** |
| **WAITING_ON AUTO** | 0/9 | **9/9** |
| **P16-Y** | 88.9 | **88.6** |
| **MEMORY (0–75)** | 62.3 | 62.3 |
| **L5 READINESS** | Partial | **Pilot-ready w/ SOP** |

---

## FINAL VERDICT

**Can Chen Kui now manage a 3-day case without reconstructing it from WeChat?**

> **For standard journeys (cancel, payment, UW, add-car, remove): Yes** — reread 82.6, need WeChat 0/10.  
> **For 3-day claims: Yes with assistant discipline** — 71% claim memory + `suggested_waiting_on`; broker confirms wait state on case record.  
> **Not yet:** fully unattended complex total-loss disputes or edge cases CL07/CL08 without occasional WeChat peek.

**North star progress:** Messy paste → time-bound obligation with **visible wait party** and **durable claim facts** — in one paste path, rules-only, no new architecture.

---

*Artifacts: `P16Z10B_*.md` · results: `docs/product_constitution/.role_d_results/role_d_battery.json`*
