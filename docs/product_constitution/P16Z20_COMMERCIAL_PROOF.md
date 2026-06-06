# P16-Z20 Phase 4 — Commercial Proof

**Date:** 2026-06-03  
**Sprint:** P16-Z20 Add-Car Commercial Simulation  
**North Star:** Customer Message → Draft Case → Broker Confirm → Get Paid  
**Success metric:** Broker minutes saved per case

---

## Measurement model

Same conservative model as P16-Z19, calibrated to 20 Add-Car-only scenarios:

| Phase | Without Customer Builder | With Customer Builder |
|-------|--------------------------|------------------------|
| Read messages | 1.5–3.5 min (scales with turns) | Paste turns ~20–35 sec |
| Organize / extract | 1.5–2.5 min mental + notes | AI draft ~instant (rules path) |
| Follow-up questions | 0–2.5 min if slots missing | Checklist visible; 0–15 sec |
| Decide next step | 0.5 min | Read `broker_next_step` ~10 sec |
| **WeChat re-read penalty** | — | +1.2 min if case unusable |

---

## Best / Average / Worst tables

### Best cases (top 5 by net broker value)

| ID | Scenario | Manual | With Builder | **Minutes Saved** | Quality | Need WeChat? |
|----|----------|--------|--------------|-------------------|---------|--------------|
| AC03 | VIN missing Honda | 8.1 | 1.0 | **7.1** | 81 | No |
| AC17 | VIN later Tacoma | 8.0 | 1.0 | **7.0** | 81 | No |
| AC04 | Driver ambiguous | 7.8 | 1.0 | **6.8** | 81 | No |
| AC11 | 极简中文 | 7.5 | 1.0 | **6.5*** | 73 | **Yes** |
| AC01 | Complete Tesla | 7.1 | 0.7 | **6.4** | 89 | No |

\*AC11 gross 6.5 min — **net ~1.5 min** after WeChat reopen penalty.

**Best honest net saved (no WeChat reopen):** AC03 at **7.1 min** — organizer value even when VIN still needed.

**Best end-to-end quote-ready:** AC05, AC07, AC09 at **4.7–5.6 min** saved with confidence 100.

---

### Average cases (median cluster — quality 81–89)

| ID | Scenario | Manual | With Builder | **Minutes Saved** | Quality |
|----|----------|--------|--------------|-------------------|---------|
| AC06 | Spouse Lexus | 6.8 | 1.0 | 5.8 | 82 |
| AC08 | Urgent Tesla | 6.6 | 1.0 | 5.6 | 87 |
| AC16 | Materials sent | 7.1 | 1.0 | 6.1 | 82 |
| AC13 | VIN late resolve | 7.1 | 1.0 | 6.1 | 89 |
| AC18 | New customer | 6.7 | 0.7 | 6.0 | 87 |

**Median minutes saved:** **6.0 min**  
**Median case quality:** **82**

---

### Worst cases (bottom 5)

| ID | Scenario | Manual | With Builder | **Gross Saved** | **Net Saved** | Quality | Blocker |
|----|----------|--------|--------------|-----------------|---------------|---------|---------|
| AC20 | Mixed remove+add | 6.1 | 2.1 | 4.0 | **~0** | 35 | Wrong lane |
| AC15 | Teen+spouse | 6.9 | 0.7 | 6.2 | 6.2 | 65 | Weak model line |
| AC12 | Minimal EN | 7.5 | 1.0 | 6.5 | **~1.5** | 73 | No extraction |
| AC11 | Minimal CN | 7.5 | 1.0 | 6.5 | **~1.5** | 73 | No extraction |
| AC19 | Same-day Tesla | 6.7 | 0.7 | 6.0 | 6.0 | 86 | Year slot miss |

---

## Portfolio summary

| Tier | Count | Avg Quality | Avg Minutes Saved (gross) | Avg Net Saved |
|------|-------|-------------|---------------------------|---------------|
| **Best** (Q ≥ 89) | 7 | 90.0 | 6.2 | 6.2 |
| **Average** (Q 81–88) | 9 | 84.1 | 6.1 | 6.1 |
| **Worst** (Q < 81) | 4 | 61.5 | 5.8 | **2.8** |
| **All 20** | 20 | **81.6** | **6.0** | **5.4** |

---

## Time breakdown by activity

| Activity | Without CB (avg) | With CB (avg) | **Saved** |
|----------|------------------|---------------|-----------|
| Reading messages | 2.3 min | 0.4 min | 1.9 min |
| Asking follow-ups | 1.1 min | 0.2 min | 0.9 min |
| Organizing information | 1.8 min | 0.1 min | 1.7 min |
| Reviewing draft case | — | 0.5 min | (included above) |
| WeChat re-read (3 cases) | 1.2 min each | 0 | 1.2 min avoided on 17/20 |
| **Total intake** | **~6.6 min** | **~0.6–1.2 min** | **~5.4 min net** |

---

## ROI sketch (Chen Kui office)

| Assumption | Value |
|------------|-------|
| Add-Car cases per day | 8–12 |
| Minutes saved per case (net) | 5.4 |
| Broker hourly value | $50–75 |
| **Daily savings** | **43–65 min** |
| **Monthly savings (20 days)** | **14–22 hours** |
| **Labor value / month** | **$700–1,650** |

Software at $200–400/mo → **2–8× ROI** on Add-Car intake alone.

---

## What Customer Builder does NOT save

- Carrier quoting / binding (8–15 min — downstream)
- Payment collection
- Physical document verification
- Mixed-intent case boundary resolution (AC20)

---

## Verdict (Phase 4)

Add-Car Customer Builder saves **~5.4 minutes net per case** across 20 realistic scenarios (conservative; excludes downstream quoting).

**Headline for sales:** *"5–6 minutes back on every Add-Car — more when VIN is missing because the checklist is already built."*

Commercial proof is **strong on 17/20 cases**, **weak on 3/20** (minimal openers + mixed-intent boundary).
