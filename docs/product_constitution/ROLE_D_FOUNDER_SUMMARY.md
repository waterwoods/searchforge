# P16-Z7 Phase 10 — Founder Summary

**Date:** 2026-06-02  
**Sprint:** P16-Z7 Reality Memory Validation  
**Artifacts:** `ROLE_D_*.md` · `configs/role_d_*.json` · `.role_d_results/role_d_battery.json`  
**Constraint honored:** No new features · No P17 · No CRM · No UI redesign

---

## TOP 20 DISCOVERIES

1. **Append path works mechanically** — 10/10 journeys accumulate `N customer message(s)` in summary.
2. **Avg memory score 60.7/75** on 3-day simulation — below P16-Y single-shot 88.9 because end-state is stricter.
3. **Avg reread 68.9/100** — 6/10 journeys broker-readable without WeChat; 4/10 forced reopen.
4. **D08 (premium renewal) is the gold path** — reread 90; Z6 Y45 prior-turn + `bill_sent_claimed` validated.
5. **D09 (cancel→address correction) proves Z6 merge** — `Prior turn: 保单要cancel了` in summary.
6. **D10 (Chinese installment) is the worst path** — stays `unclear` all 3 days; payment facts never collected.
7. **D07 (remove vehicle) lane-flips to add-car** — trust-breaking on Day 3; broker would reopen WeChat immediately.
8. **Category match only 5/10** — multi-day drift and `Boundary: new_issue` mislabels Day 3 turns.
9. **Claims keyword retention 36%** — Turn 1 FNOL OK; corrections and dollars fail.
10. **`waiting_on` is 100% manual** — 0/9 carrier-wait phrases auto-set responsibility.
11. **`case_messages` storage is production-grade** — memory loss is distillation/UI, not persistence.
12. **Z6 对话记录 fixes perceived memory** — not measured in engine run; ~+8 reread pts when deployed.
13. **Non–add-car collected merge still deferred** — D03 zip, D10 $200 prove P16-Z6 item #7 still blocks.
14. **Generic broker step sticks across days** — D01 same English step on all 3 turns.
15. **Chinese payment/lapse under-classified** — D01 `customer_question` vs `cancellation_warning`.
16. **English payment thread breaks on Day 3** — D02 pivots to underwriting_followup; loses #88291 narrative.
17. **Claim collected fields stronger than claim summary** — D05 photos in fields; plate not in headline.
18. **Zendesk parity on UW; behind on payment/claims** — benchmark Phase 7.
19. **~27 min/broker/week savings** at pilot volume — ROI positive on pass band only.
20. **3-day unsupervised memory is not commercial-ready** — needs fixes 1–5 in ROI doc + deploy + observation log.

---

## TOP 10 MEMORY FAILURES

1. Chinese installment/lapse → `unclear` (D10)
2. Remove-car → add-car lane (D07)
3. Total loss correction context dropped (CL02 — 0% retention)
4. Payment confirmation # lost on Day 3 (D02)
5. Cancel wedge misclassified (D01)
6. Zip 94588 not in collected (D03)
7. $420 payment not in summary (D01)
8. Injury/MRI thread → unclear (CL06)
9. Claim misclassified as missing_document (CL03)
10. `waiting_on: carrier` never inferred (all Day 3 carrier pings)

---

## TOP 10 CASES THAT PASSED

| Rank | ID | Why passed |
|------|-----|------------|
| 1 | **D08** | Reread 90; premium + prior turn + bill_sent |
| 2 | **D06** | Memory 67; end-state collected driver + Civic |
| 3 | **D07** | Reread 70 — *only* if broker ignores wrong lane (fragile pass) |
| 4 | **D05** | Claim fields accumulate; adjuster ask readable |
| 5 | **D09** | Correction prepend; address lane |
| 6 | **D04** | UW deadline + policy # stable |
| 7 | **CL07** | 50% retention; UM question in latest |
| 8 | **CL01** | FNOL + police_report collected T3 |
| 9 | **CL05** | Correction flag on payment pivot |
| 10 | **CL09** | Claim correction chain partial |

*Pass = reread ≥70 and/or memory ≥60 without mandatory WeChat on engine rubric.*

---

## TOP 10 CASES THAT FAILED

| Rank | ID | Why failed |
|------|-----|------------|
| 1 | **D10** | unclear ×3; no payment fields |
| 2 | **D02** | Day 3 UW pivot; needs WeChat |
| 3 | **D01** | Wrong category; $420 missing |
| 4 | **D03** | 94588 not structured; needs WeChat |
| 5 | **CL02** | 0% keyword retention |
| 6 | **CL06** | Injury thread unclear |
| 7 | **D07** | Lane flip (qualitative fail despite reread 70) |
| 8 | **CL03** | Wrong lane missing_document |
| 9 | **CL10** | $18k only in latest |
| 10 | **CL04** | Hail/adjuster weak retention |

---

## TOP 10 CLAIMS INSIGHTS

1. Turn 1 FNOL routing is pilot-ready without new engine.
2. Turn 2+ memory is the commercial gap (36% avg retention).
3. Plate corrections need headline + collected persistence.
4. Total loss disputes are the highest-risk trust breakers.
5. Photo-reference turns often OK in `collected_fields`, weak in summary.
6. Police report # can land in collected (CL01) but late.
7. Carrier-delay language does not set `waiting_on: carrier`.
8. Mixed claim/payment uses correction flag — partial win (CL05).
9. Glass→full claim pivot loses glass-only context (CL08).
10. Deploy thread UI before claims commercial claim — perception > engine score.

---

## TOP 10 WAITING_ON INSIGHTS

1. Model is correct — execution is manual only.
2. Day 3 “any update?” messages are wait-checks, not new issues.
3. Carrier/adjuster phrases appear in 5+ journeys — none auto-map.
4. `tracking_summary` works when broker maintains field.
5. Queue `waiting_on: client` filter is underused without SOP.
6. Follow-up editor collapsed — responsibility tagging skipped.
7. Office-wait (quote/refund) not inferred from D06/D08 language.
8. Intercom/Zendesk win on responsibility views without AI.
9. Highest ROI: 0.5-day triage heuristic → suggest `waiting_on`.
10. Assistant can compensate in pilot — broker alone cannot.

---

## TOP 10 HIGHEST ROI FIXES

1. Chinese payment/lapse classification (D10, D01)
2. Remove-car lane guard (D07)
3. Persist collected on all append paths (D03, D10)
4. Deploy Z6 thread + append CTA
5. `waiting_on` heuristic from triage text
6. Claim plate/policy/$ collected merge (CL01–CL10)
7. Day 3 broker_next_step refresh on status pings
8. Per-message timestamp in 对话记录
9. Broker turn-delta block (generalize add-car rail)
10. Founder 3× logged real 3-day observation cases

---

## ONE SENTENCE PRODUCT SOUL

> **Unified Intake is the office’s memory of what the client already said — not a replacement for WeChat, the carrier portal, or the broker’s judgment.**

---

## ONE SENTENCE NORTH STAR

> Turn messy client messages into a time-bound office obligation with a clear next action and a traceable close — in one paste, under one minute.

---

## FINAL VERDICT

### Can Chen Kui manage a 3-day case without reopening WeChat?

**Partially — not universally.**

| Scope | Verdict |
|-------|---------|
| Premium renewal + bill (D08) | **Yes** |
| UW deadline (D04) | **Mostly yes** |
| Correction cancel→address (D09) | **Mostly yes** |
| Claim FNOL + photos (D05) | **Mostly yes** (confirm plate in WeChat) |
| Payment / cancel / installment (D01, D02, D10) | **No** |
| Remove vehicle (D07) | **No** |
| Complex claims (CL02, CL06) | **No** |

**Overall:** **4/10 journeys require WeChat on Day 3** (engine rubric); **6/10 pass** with Z6 UI likely **7–8/10** after deploy.

---

### What exactly blocks him?

| Blocker | Symptom | Fix |
|---------|---------|-----|
| **Payment/lapse Chinese** | `unclear`, no $/installment in case | Classification + collected merge |
| **Remove-car lane** | “New quote” on sold Camry | Lane guard in `triage.py` |
| **Collected not merged on append** | Zip, amounts, confirmation # missing | P16-Z6 deferred item #7 |
| **No `waiting_on` inference** | Day 3 pings feel like new fires | Triage heuristic + SOP |
| **Claims correction memory** | 全损, $18k, injury dropped | Claim-specific summary merge |
| **Append habit + deploy** | Duplicate cases; no thread card | Z6 deploy + one-time training |
| **No observation proof** | Founder can’t claim commercial GO | 3 logged real 3-day cases |

---

## Next action (founder)

1. **Deploy Z6** to preview — re-run `scripts/run_role_d_memory_battery.py` is optional; run **3 real** two–three-turn cases in observation log.  
2. **Engine slice (3 days):** payment Chinese + remove-car + collected merge.  
3. **Re-run Role D battery** — target: avg reread **≥80**, needs_wechat **≤2/10**.  
4. **Do not** market “3 days without WeChat” until then.

---

*Battery: `LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_role_d_memory_battery.py`*
