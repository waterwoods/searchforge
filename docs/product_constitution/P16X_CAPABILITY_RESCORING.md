# P16-X Phase 8 — Capability Re-Scoring

**Date:** 2026-06-01  
**Method:** Deployed Preview evidence (P16-X Phases 1–7) — no inflation  
**Baseline:** Cap 5 ~55–62 (docs); Cap 6 ~62–68 (P16-I/K inferred)  
**Honesty rule:** Paper scores ≠ deployed behavior

---

## Summary

| Capability | Prior (best doc claim) | **P16-X deployed** | Δ | Target | Met? |
|------------|------------------------|-------------------|---|--------|------|
| **5 — Case Lifecycle** | 62 (P16-H) | **53** | **−9** | 60+ | ❌ |
| **6 — Trial Conversion** | 68 (P16-K) | **51** | **−17** | 60+ w/ evidence | ❌ |

---

## Capability 5 — Case Lifecycle Management: **53 / 100**

### Dimension breakdown

| Dimension | P16-H | P16-X | Evidence |
|-----------|-------|-------|----------|
| Queue existence | 75 | **68** | Queue loads on Preview; demo noise |
| Prioritization | 70 | **52** | Flat list in product_only; no Work now/Waiting |
| Queue UX | 45 | **48** | Simpler than platform_full; EN previews |
| Follow-up workflow | 55 | **32** | Append only on reopen — **regression vs contract intent** |
| Session continuity | 60 | **58** | Postgres persist ✅; UI return path ❌ |
| Close / status hygiene | — | **38** | Kebab-only status |
| Assistant playbook | 40 | **35** | Still no in-product guidance |

### Why −9 from P16-H

P16-H assumed **simpler queue** improved lifecycle. P16-X proves **follow-up discoverability** and **close loop** dominate — queue simplification did not fix continuation.

### Contract acceptance (7 criteria)

**Met: 3 / 7** (see P16X_LIFECYCLE_AUDIT.md)

---

## Capability 6 — Trial Conversion: **51 / 100**

### Dimension breakdown

| Dimension | P16-K | P16-X | Evidence |
|-----------|-------|-------|----------|
| Trial process definition | 75 | **75** | TRIAL_ONE_PATH unchanged |
| Commercial packaging (docs) | 75 | **75** | P16-K artifacts exist |
| Commercial packaging (in UI) | — | **30** | No pricing/terms in product |
| Day 1 unsupervised path | 58 | **42** | Reachable URL ✅; continuation ❌ |
| Time-to-first-value | 75 | **62** | 30s triage + scroll |
| Behavioral proof capture | 25 | **25** | Zero real trials logged |
| Day 7 payment path | 40 | **38** | Still founder-dependent |
| Post-first-submit stickiness | — | **28** | **New dimension — killer gap** |

### Why −17 from P16-K inferred 68

P16-K scored **commercial docs** and **landing simplification**. P16-X scores **what happens after first submit** — where trial value must compound across Days 1–7. Single-turn UX **cannot produce** ≥3 real cases with follow-ups without founder nagging.

### Trial completion forecast (7 days, unsupervised)

| Criterion | Likely? |
|-----------|---------|
| ≥3 real cases pasted | ⚠️ Maybe |
| Draft copied ≥2× with edits | ⚠️ Maybe Day 0–1 only |
| Opened ≥4/7 days | ❌ Unlikely without habit hook |
| Follow-up on same case | ❌ Unlikely without training |
| Day 7 payment | ❌ No |

---

## Cross-capability interaction

```
Cap 6 Trial Conversion
        │
        depends on
        ▼
Cap 5 Lifecycle (follow-up + close)
        │
        blocked by
        ▼
Post-submit continuation UX  ← P16-X finding
```

**Improving Cap 6 without Cap 5 continuation is impossible** — broker cannot prove daily time savings if they use product once per case turn zero.

---

## Overall product score (lifecycle-weighted refresh)

| Capability | Weight | P16-X Score | Weighted |
|------------|--------|-------------|----------|
| 1 Front Door | 25% | 72 | 18.0 |
| 2 Triage | 15% | 85 | 12.8 |
| 3 Case Record | 15% | 72 | 10.8 |
| 4 Intake | 10% | 55* | 5.5 |
| **5 Lifecycle** | 10% | **53** | **5.3** |
| **6 Trial** | 15% | **51** | **7.7** |
| 7 Founder Control | 10% | 70 | 7.0 |
| **Overall** | | | **67.1 → 67** |

*Cap 4 depressed — customer portal N/A on Preview

**Delta vs P16-I overall 74:** **−7** — engine strong; **continuation weak**

---

## Rescoring verdict

| Question | Answer |
|----------|--------|
| Is Cap 5 trial-ready at 60+? | **No — 53** |
| Is Cap 6 trial-ready at 60+? | **No — 51** |
| Primary drag | Post-first-submit single-turn UX |
| Engine blame? | **No** — guardrail PASS, append API works |

---

*End of P16-X Phase 8 — Capability Re-Scoring*
