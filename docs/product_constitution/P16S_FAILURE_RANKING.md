# P16-S Phase 3 — Failure Ranking

**Date:** 2026-06-01  
**Sprint:** P16-S Failure Pattern Library + Post Sprint Health Check  
**Method:** Probability × Impact ranking; historical hours lost; prevention ROI

**Reference:** `P16S_FAILURE_DISCOVERY.md`, `FAILURE_PATTERN_LIBRARY.md`

---

## Ranking methodology

| Factor | Scale |
|--------|-------|
| **Probability** | 1–5: likelihood of recurrence next sprint without prevention |
| **Impact** | 1–5: trial/commercial/time damage if it occurs |
| **Risk score** | Probability × Impact (max 25) |
| **Hours lost** | Documented or estimated engineering + founder time across P16-A–R |
| **Hours saved** | Estimated if prevention mechanism applied every sprint |

---

## Top 10 failures most likely to occur again

| Rank | FP | Pattern | P | I | Score | Hours lost (hist.) | Hours saved/yr |
|------|-----|---------|---|---|-------|-------------------|----------------|
| **1** | FP-004 | Preview Protection (401 SSO) | 5 | 5 | **25** | ~25 | ~30 |
| **2** | FP-001 | Deployment Parity Failure | 5 | 5 | **25** | ~45 | ~50 |
| **3** | FP-008 | Reality Gap (paper ≠ deployed) | 5 | 4 | **20** | ~35 | ~40 |
| **4** | FP-003 | Feature Flag Drift | 4 | 5 | **20** | ~15 | ~20 |
| **5** | FP-002 | CORS Origin Block | 4 | 5 | **20** | ~30 | ~25 |
| **6** | FP-010 | Founder Assumption | 4 | 4 | **16** | ~20 | ~15 |
| **7** | FP-013 | Preview/Production Divergence | 4 | 4 | **16** | ~20 | ~18 |
| **8** | FP-005 | Not Deployed | 3 | 5 | **15** | ~20 | ~25 |
| **9** | FP-015 | Missing Evidence | 4 | 3 | **12** | ~10 | ~12 |
| **10** | FP-009 | Commercial Gap (empty invoice) | 3 | 4 | **12** | ~8 | ~10 |

---

## Full ranking (Top 20 patterns)

| Rank | FP | Pattern | P×I | Severity | Open? |
|------|-----|---------|-----|----------|-------|
| 1 | FP-004 | Preview Protection | 25 | P0 | Yes |
| 2 | FP-001 | Deployment Parity | 25 | P0 | Partial |
| 3 | FP-008 | Reality Gap | 20 | P0 | Yes |
| 4 | FP-003 | Feature Flag Drift | 20 | P0 | Partial |
| 5 | FP-002 | CORS Origin Block | 20 | P0 | Latent |
| 6 | FP-010 | Founder Assumption | 16 | P0 | Yes |
| 7 | FP-013 | Preview/Production Divergence | 16 | P0 | Yes |
| 8 | FP-005 | Not Deployed | 15 | P0 | Reduced |
| 9 | FP-014 | Broken Trial Flow | 15 | P0 | Yes |
| 10 | FP-016 | Wrong Default Tab | 15 | P0 | Production |
| 11 | FP-015 | Missing Evidence | 12 | P1 | Yes |
| 12 | FP-009 | Commercial Gap | 12 | P1 | Yes |
| 13 | FP-011 | Environment Drift | 12 | P1 | Partial |
| 14 | FP-019 | Git/Vercel Disconnect | 12 | P1 | Process |
| 15 | FP-007 | UI Complexity Creep | 10 | P1 | Partial |
| 16 | FP-006 | Runtime Error (misattributed) | 10 | P1 | Latent |
| 17 | FP-012 | Capability Regression | 9 | P1 | Yes |
| 18 | FP-018 | Draft Language Mismatch | 9 | P2 | Yes |
| 19 | FP-017 | Engineer Chrome | 8 | P2 | Production |
| 20 | FP-020 | Scope Creep During Trial | 8 | P1 | Process |

---

## Historical hours lost (P16-A through P16-R)

| Category | Hours lost | Primary drivers |
|----------|------------|-----------------|
| **Deploy / CORS / Preview** | ~95 | CORS weeks P16-F→G; SSO re-diagnosis every sprint; P16-O deploy drift |
| **Reality re-validation** | ~35 | P16-Q full reality sprint; P16-R parity closure |
| **UI sprints (local-only value)** | ~50 | P16-H, M, N, O work partially unrealized on URLs |
| **Commercial / trial prep** | ~25 | P16-K, L docs; blocked by deploy |
| **Local dev friction** | ~15 | Node 20, CORS localhost, 503 warming (mostly fixed P16-D) |
| **Process / false confidence** | ~30 | Repeated E2E log deferral; wrong GO assumptions |
| **Total estimated** | **~250 hrs** | ~6 weeks of calendar time on deploy/reality alone |

---

## Hours saved if prevented (annual estimate)

Assumes 12 sprints/year with post-sprint health check enforced:

| Prevention mechanism | Hours saved/sprint | Annual |
|---------------------|-------------------|--------|
| Automated cold-URL parity check | 4–8 | 48–96 |
| CORS auto-patch on deploy | 2–4 | 24–48 |
| Vercel env dashboard persistence | 1–2 | 12–24 |
| Mandatory reality scorecard before verdict | 3–5 | 36–60 |
| Andy 15-min E2E log gate | 2–3 | 24–36 |
| **Conservative total** | **12–22** | **144–264** |

**Net:** Preventing top 5 patterns alone recovers **60–80%** of historical deploy/reality waste.

---

## Impact matrix (Probability × Impact)

```
Impact →
    1    2    3    4    5
P 5 [   ][   ][   ][ 8][1,4]     ← FP-008, FP-001, FP-004
r 4 [   ][   ][15][10][3,2,5]    ← FP-015, FP-010, FP-003, FP-002, FP-013
o 3 [   ][18][ 9][ 9][ 5,14]     ← FP-018, FP-012, FP-009, FP-005, FP-014
b 2 [   ][17][ 7][ 6][16]         ← FP-017, FP-007, FP-006
  1 [   ][20][   ][19][   ]      ← FP-020, FP-019
```

**Quadrant priority:** Upper-right (P≥4, I≥4) = immediate automation + mandatory checklist.

---

## Trial progress blockers (ranked by days blocked)

| Rank | Failure | Days blocked | Trial impact |
|------|---------|--------------|--------------|
| 1 | Preview SSO (FP-004) | ~30+ | Cannot send URL; Day 0 dead |
| 2 | Production frozen (FP-013) | ~41 | Wrong link in any old doc |
| 3 | CORS outage (FP-002) | ~14 | Preview unusable even with SSO bypass |
| 4 | P16-O not deployed (FP-005) | ~7 | Customer path wrong on Preview |
| 5 | No E2E log (FP-015) | ~21 | Founder cannot certify |
| 6 | Empty invoice (FP-009) | ~14 | Day 7 payment blocked |
| 7 | Zero trial completed (FP-014) | ∞ | No payment proof |

---

## False confidence incidents (ranked)

| Rank | Failure | Confidence created | Reality |
|------|---------|-------------------|---------|
| 1 | Local PASS → "shippable" (FP-008) | P16-J 74, P16-O 78 | Deployed 52–64 |
| 2 | Guardrail PASS → "trial ready" (FP-008) | Cap 2 = 85 | Broker never reaches engine |
| 3 | P16-O verdict without deploy (FP-005) | Customer UX "done" | Preview lacked strings |
| 4 | CORS fix locally assumed remote (FP-001) | P16-F.5 partial GO | Preview still broken |
| 5 | Commercial docs = payment ready (FP-009) | P16-K closed | IDs still empty |

---

## Recommended prevention priority

| Priority | Action | Patterns addressed | Effort |
|----------|--------|-------------------|--------|
| **P0** | POST_SPRINT_HEALTH_CHECK mandatory | All | Low (process) |
| **P0** | Cold URL curl in CI/script | FP-001, FP-004, FP-013 | Medium |
| **P0** | Disable Preview SSO | FP-004, FP-014 | Low (settings) |
| **P1** | Vercel env persistence + deploy script | FP-003, FP-005, FP-019 | Medium |
| **P1** | CORS post-deploy hook | FP-002, FP-006 | Medium |
| **P2** | Reality scorecard template | FP-008, FP-010, FP-015 | Low |
| **P2** | Constitution Enforcement gate | FP-007, FP-012, FP-020 | Low |

---

*End of P16-S Phase 3 — Failure Ranking*
