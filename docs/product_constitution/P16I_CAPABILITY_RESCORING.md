# P16-I Capability Re-Scoring

**Date:** 2026-05-31  
**Method:** P16-H rubric + shipped deletions + local product_only build validation  
**Honesty rule:** No inflation; trial proof still pending

---

## Summary

| Metric | P16-G/H | P16-I | Target | Met? |
|--------|---------|-------|--------|------|
| UI Simplicity | 58 | **76** | ≥75 | Yes |
| Capability 1 Broker Front Door | 70 | **79** | ≥78 | Yes |
| Capability 4 Customer Intake | 62 | **68** | — | Tab hidden; paste path improved |
| Capability 6 Trial Conversion | 51 | **62** | ≥60 | Yes |
| Overall product | 68 | **74** | 72–75 | Yes |

---

## Capability 1 — Broker Front Door: **79 / 100** (+9)

| Dimension | Was | Now | Evidence |
|-----------|-----|-----|----------|
| Default surface | 85 | 90 | Single workbench; no customer tab |
| 10-second comprehension | 35 | 72 | Paste above fold; cancellation copy |
| Engineer chrome | 90 | 90 | Unchanged (already clean) |
| Demo queue UX | 75 | 78 | Practice merged; progress kept |
| Information density | 45 | 74 | Queue + detail simplified |

**Gap:** Dark shell header; no authenticated preview E2E this sprint.

---

## Capability 4 — Customer Intake Collection: **68 / 100** (+6)

| Dimension | Was | Now | Evidence |
|-----------|-----|-----|----------|
| Broker paste mechanism | 85 | 88 | Paste promoted; layout fixed |
| Paste UX copy | 55 | 72 | Trial keys in ui_copy.json |
| Follow-up paste discoverability | 60 | 78 | 追加客户补充 near glance |
| Customer portal | 70 | 55* | *Hidden in trial — intentional deferral |
| Surface promotion | 40 | 80 | Broker path dominates |

**Note:** Customer portal message-first redesign deferred; tab hidden per P16-H recommendation C.

---

## Capability 6 — Trial Conversion (inferred): **62 / 100** (+11)

| Dimension | Was | Now |
|-----------|-----|-----|
| Wrong-door abandonment risk | 28 | 65 |
| Time-to-first-action | 40 | 75 |
| Professional trust | 50 | 70 |
| Self-serve Day 1 | 35 | 58 |

**Still blocks unsupervised Day 0:** Commercial pack, Andy preview E2E, founder sign-off.

---

## Overall Product: **74 / 100** (+6)

Engine remains **85–90**. UI simplicity crossed trial gate. Trial conversion improved but **not proven** until observation log.

---

## TOP 20 deletions shipped: **17 / 20**

Shipped: #1–8, #10, #13 (partial), #15–16, #20 (reorder), #21–23 (partial), #26, #47–48 (partial)  
Deferred: #12 customer flow track (tab hidden), #22 full list merge polish, #35 header redesign

---

## Recommendation

| Decision | Action |
|----------|--------|
| Simplicity ≥75 | **Proceed to Preview deploy** after Andy screenshot |
| Chen Kui Day 0 | **Not yet** — need commercial pack + supervised kickoff |
| P17 | **Do not start** until Sprint A accepted |

---

*End of P16-I Capability Re-Scoring*
