# P16-Z6 Phase 8 — ROI Validation

**Date:** 2026-06-02  
**Scope:** Memory activation only — no new services

---

## Time savings model (broker office)

| Activity | Before (min) | After Z6 (min) | Savings |
|----------|--------------|----------------|---------|
| Re-read WeChat for last 2 bubbles | 2–4 | 0.3 (glance thread) | **~2 min/case** |
| Re-open WeChat after copy for Turn 2 | 3–5 | 1 (append in place) | **~3 min/case** |
| Decode wrong lane (premium as add-car) | 5–10 | 0 | **~7 min** on renewal threads |
| Re-explain cancel+address correction | 4–6 | 1 | **~4 min** on correction cases |

**Assumption:** 8 multi-turn cases/week/broker → **~15–25 min/week** saved at pilot scale.

---

## Re-reads avoided

| Signal | Estimate |
|--------|----------|
| Thread card replaces WeChat scroll | 2–3 re-reads/case on Turn 2+ |
| Prior-turn in summary | 1 re-read on correction/premium |
| Queue `最近：` | 0.5 re-read on queue scan |

---

## Broker effort reduced

- **Cognitive:** One surface for “what they said” + “what to do”  
- **Operational:** Fewer duplicate cases from re-paste instead of append  
- **Trust:** P16-Y multi_message **21.5 → 21.8**; Y44/Y45 **79 → 86**

---

## TOP 10 highest ROI fixes (this sprint)

| Rank | Fix | Effort | ROI |
|------|-----|--------|-----|
| 1 | Y44/Y45 summary merge | 1 day | ★★★★★ |
| 2 | Render `case_messages` | 0.5 day | ★★★★★ |
| 3 | Append when `case_id` | 2 hr | ★★★★★ |
| 4 | Post-copy hint | 15 min | ★★★★☆ |
| 5 | Premium lane guard | 0.5 day | ★★★★☆ |
| 6 | `bill_sent_claimed` | 1 hr | ★★★★☆ |
| 7 | Queue latest update | 0 (exists) | ★★★☆☆ |
| 8 | Default-open activity | 2 hr deferred | ★★★☆☆ |
| 9 | Turn-delta rail | 0.5 day deferred | ★★★☆☆ |
| 10 | Founder 3× two-turn log | 1 hr process | ★★★★★ (commercial proof) |

---

## Investment vs return

| Input | Output |
|-------|--------|
| ~1 engineer-day (Z6 scope) | +0.3 P16-Y avg; Y44/Y45 pass band; visible thread |
| $0 new infra | Uses existing `case_messages` + triage |
| Deploy + 3 observation cases | Chen Kui GO/NO-GO for paid pilot memory claim |
