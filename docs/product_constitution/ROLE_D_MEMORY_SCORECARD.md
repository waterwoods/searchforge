# P16-Z7 Phase 2 — Role D Memory Scorecard

**Date:** 2026-06-02  
**Engine:** `triage_conversation` + `triage_for_append` (rules path, `LLM_GENERATION_ENABLED=0`)  
**Raw results:** `docs/product_constitution/.role_d_results/role_d_battery.json`

---

## Aggregate scores

| Metric | Value | Max | Notes |
|--------|-------|-----|-------|
| **Avg memory score** | **60.7** | 75 | summary + fields + next action |
| **Avg reread score** | **68.9** | 100 | broker-understandable without WeChat |
| **Category match** | **5 / 10** | — | `issue_category` vs expected |
| **Needs WeChat** | **4 / 10** | — | reread &lt; 45% keyword coverage |

### Dimension breakdown (avg / 25)

| Dimension | Avg | Interpretation |
|-----------|-----|----------------|
| Summary quality | 22.2 | Message count + Prior turn prepend (Z6) working |
| Field retention | 18.9 | Structured fields lag merged thread facts |
| Next action quality | 19.6 | Turn 1 often OK; generic/clarify on Chinese payment |

---

## Per-journey scorecard

| ID | Category | Memory /75 | Reread /100 | Cat OK | Needs WeChat | Top note |
|----|----------|------------|-------------|--------|--------------|----------|
| D01 | cancellation | 60 | 65 | ❌ | ✅ | `customer_question` not `cancellation_warning`; $420 not in summary |
| D02 | payment | 59 | 60 | ❌ | ✅ | Day 3 pivots to UW; loses `already_paid` / #88291 |
| D03 | missing_doc | 52 | 60 | ❌ | ✅ | 94588 in summary lane but not `collected_fields` |
| D04 | underwriting | 59 | 70 | ✅ | ❌ | Deadline + policy # retained |
| D05 | claim | 60 | 70 | ❌ | ❌ | Collected claim fields strong; plate not in summary headline |
| D06 | add_driver | 67 | 74 | ✅ | ❌ | Turn 3 add-car lane; teen/permit weak Day 1–2 |
| D07 | remove_vehicle | 67 | 70 | ✅ | ❌ | **Lane flip:** remove → add-car quote by Day 3 |
| D08 | coverage_review | **70** | **90** | ✅ | ❌ | **Best** — Prior turn + premium collected (Z6 Y45) |
| D09 | cancellation | 60 | 70 | ✅ | ❌ | Prior cancel in summary; 94566 weak in collected |
| D10 | payment | 53 | 60 | ❌ | ✅ | **Worst** — stays `unclear`; installment/$200 dropped |

---

## Summary quality

| Signal | Pass rate | Evidence |
|--------|-----------|----------|
| Multi-turn message count in summary | **10/10** | `N customer message(s)` on final turn |
| Prior turn prepend (correction/premium) | **3/10** | D08, D09, partial D02 |
| Headline matches primary lane | **6/10** | D07/D10/D02 lane drift |
| Deadline surfaced when present | **4/10** | D01, D04 strong; D03/D10 weak |

**Verdict:** Summary **continuity mechanics work**; **lane-specific headlines** still wrong on remove-car, Chinese payment, and late-turn boundary detection.

---

## Field retention

| Journey | Key facts in thread | In `collected_fields` / `still_needed` | Gap |
|---------|---------------------|----------------------------------------|-----|
| D01 | $420, cancel 7-day | `deadline_mentioned` only | Payment amount, cancel category |
| D02 | #88291, paid 3/12 | `policy_number` (mislabeled lapse) | Confirmation #, verify_carrier |
| D03 | 94588, proof sent | `[]` | Zip, garaging_proof |
| D05 | 8ABC123, photos | accident, hit_and_run, photos | Plate not in summary |
| D08 | renewal, bill sent | premium_*, bill_sent_claimed | ✅ Z6 fix validated |
| D10 | $200, 3 installments | `[]` | Full payment thread lost |

**Verdict:** Field retention **~50% of journey-critical facts** — append merges text but **non–add-car collected merge still deferred** (P16-Z6 #7).

---

## Next action quality

| Pattern | Count | Example |
|---------|-------|---------|
| Actionable claim/UW step | 4 | D04, D05 broker steps |
| Generic notice reader | 1 | D01 same step all 3 days |
| "Ask for missing part" (`unclear`) | 2 | D06 T1–2, D10 all turns |
| Wrong lane (add-car on remove) | 2 | D07 T2–3, D06 T3 boundary |

**Verdict:** Next action **does not always refresh** on append when category stays stale or `unclear`.

---

## Comparison to P16-Y baseline

| Metric | P16-Y (50 cases) | Role D (10 journeys, 3-day) |
|--------|------------------|-------------------------------|
| Avg total | **88.9** / 100 | **60.7** / 75 (~81% normalized) |
| Multi-turn focus | Y41–Y45 | All 10 |
| Append path | Some cases | **100% append sim** |

Role D scores lower because it measures **end-of-journey** state after lane drift and **stricter field retention** across 3 days — closer to Chen Kui’s real reopen test than single-shot Y cases.

---

## Phase 2 verdict

**Memory battery: CONDITIONAL PASS**

- **Pass band:** D04, D05, D06, D07, D08, D09 (reread ≥ 70, no forced WeChat)  
- **Fail band:** D01, D02, D03, D10 (+ D02 borderline)  
- **Blockers for 3-day memory:** Chinese payment/lapse classification, remove-car vs add-car lane, non–add-car collected persistence
