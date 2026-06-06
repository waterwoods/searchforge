# Trial Observation Log V3

**Broker:** _________________  
**Trial start:** _________________  
**Trial end:** _________________  
**Plan at Day 7:** 入门版 $49 / 标准版 $99 (circle one)

**Replaces:** [`TRIAL_OBSERVATION_LOG_V2.md`](./TRIAL_OBSERVATION_LOG_V2.md)  
**Authority:** P16-L — evidence-only improvement; no new complexity

---

## Per-case log (one row per real message)

Copy this block for each case.

```
Date / time:
Scenario:           Cancellation / Missing doc / Add-car / Other: _____
Raw message source: WeChat / Email / Notice / Other

--- Evidence ---
Minutes saved (estimate):     ___ min (vs doing manually)
Draft used?                   Y / N
  If Y, edit level:           小改 / 中改 / 大改 / 没用
Would do manually otherwise?  Y / N / Maybe

--- Outcome ---
Worked?                       Y / N / Partial
Did not work?                 Y / N  — one line: _______________
Confidence level (before):    1–5 (1=没把握, 5=很清楚)
Confidence level (after):     1–5

--- Quotes (verbatim if possible) ---
Broker quote:                 "_________________________________"
Assistant quote (if any):     "_________________________________"

--- Founder (only if founder intervened) ---
Founder assisted?             Y / N — what: _______________
```

**Strong "worked" line rule:** Minutes saved ≥5 **and** Draft used = Y **and** Worked? = Y.

**Partial credit rule:** Worked? = Partial if structure helped but draft unused.

---

## Daily summary

| Day | Cases pasted | Drafts used | Est. min saved | Opened workbench? | Continue tomorrow? | Notes |
|-----|--------------|-------------|----------------|-------------------|--------------------|-------|
| Day 0 | | | | Y (kickoff) | | |
| Day 1 | | | | Y / N | Y / N / Maybe | |
| Day 2 | | | | Y / N | Y / N / Maybe | |
| Day 3 | | | | Y / N | Y / N / Maybe | |
| Day 4 | | | | Y / N | Y / N / Maybe | |
| Day 5 | | | | Y / N | Y / N / Maybe | |
| Day 6 | | | | Y / N | Y / N / Maybe | |
| Day 7 | | | | Y (review) | — | |

**Scenario mix (running):** e.g. 2 cancellation, 1 missing-doc, 1 add-car

---

## Behavioral gates (North Star §9)

| Gate | Target | Actual | Pass? |
|------|--------|--------|-------|
| Real cases pasted | ≥3 | | |
| Draft used (copied with edits) | ≥2 | | |
| Workbench opened | ≥4 of 7 days | | |
| "Worked" line with minutes | ≥1 | | |

---

## Day 7 — Value questions

1. **Which scenario felt most useful?**
   - 

2. **Which part still feels risky?**
   - 

3. **Would this save time? (specific example)**
   - 

4. **What would you want next?** *(log only — not a build commitment)*
   - 

5. **Would you try a paid month? $49 or $99?**
   - 

---

## Summary

| Metric | Value |
|--------|-------|
| Total cases | |
| Total est. minutes saved | |
| Drafts used (count) | |
| Would do manually otherwise (count Y) | |
| Worked Y / Partial / N | / / |
| Most used scenario | |
| Biggest friction | |
| **Would pay $49?** | Y / N / Maybe — why: |
| **Would pay $99?** | Y / N / Maybe — why: |
| **Would use again?** | Y / N |

**Best broker quote (for testimonial):**
> "_______________________________________________"

---

## Friction log (evidence only)

| # | Date | Scenario | Observation | Category | Fix decision |
|---|------|----------|-------------|----------|--------------|
| 1 | | | | Trust / High / Med / Low | Fix now / Next / Defer |
| 2 | | | | | |
| 3 | | | | | |

**Store:** `results/trial_logs/{broker}_{date}.md`

---

## V3 changes from V2 (why)

| V2 field | V3 change |
|----------|-----------|
| Draft copied? | Renamed **Draft used?** — same meaning, clearer for "edited but not sent" |
| Would assistant have done manually? | Renamed **Would do manually otherwise?** — applies to broker too |
| Confidence before/after | Kept; grouped under **Confidence level** |
| Worked / Friction | Split **Worked?** + **Did not work?** — forces explicit negative evidence |
| — | Added **Broker quote** + **Assistant quote** — verbatim proof |
| — | Added **Founder assisted?** — detects over-helping |
| Daily summary | Added **Continue tomorrow?** per day — early abandonment signal |

**Removed:** Nothing. No new sections beyond evidence fields.

---

*End of Trial Observation Log V3*
