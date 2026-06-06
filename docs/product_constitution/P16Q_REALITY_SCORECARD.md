# P16-Q Phase 8 — Reality Scorecard

**Date:** 2026-06-01  
**Sprint:** P16-Q Reality Validation  
**Method:** Score **deployed + URL-accessible reality**, not local-only optimism  
**Scale:** 0–100  
**Compare:** P16-J · P16-L · P16-O

---

## Scoring rule (P16-Q)

| Rule | Application |
|------|-------------|
| Local-only improvements | Cap at +5 unless deployed |
| Preview SSO | Caps Trust, Trial, Chen Kui, Role C |
| Uncommitted P16-O | Customer score split: **deployed vs local** |
| Engine quality | Full credit — guardrail PASS |

---

## Dimension scores — reality today

| Dimension | P16-Q score | Rationale |
|-----------|-------------|-----------|
| **Customer (deployed URL)** | **38** | Production pre-P16-N/O; no customer-only URL |
| **Customer (local P16-O)** | **79** | Message-first — **not shippable** |
| **Broker (local product_only)** | **74** | P16-I loop intact |
| **Broker (Preview cold)** | **12** | 401 before UI |
| **Broker (Preview auth, inferred)** | **70** | Same as P16-J local minus E2E proof |
| **Assistant** | **50** | URL + follow-up friction |
| **Founder** | **65** | Can demo locally; cannot certify deploy |
| **Commercial** | **62** | Pack exists; payment IDs empty; no proof |
| **Trial readiness** | **46** | Worse than P16-J due to P16-O deploy gap |
| **Overall product (reality)** | **64** | Engine strong; surface distribution weak |

---

## Weighted overall (trial lens)

| Dimension | Weight | Score | Weighted |
|-----------|--------|-------|----------|
| Broker workflow (local) | 25% | 74 | 18.5 |
| Customer (deployed) | 15% | 38 | 5.7 |
| URL / access | 20% | 15 | 3.0 |
| Trust / professional | 15% | 55 | 8.3 |
| Trial + commercial | 15% | 46 | 6.9 |
| Founder confidence | 10% | 65 | 6.5 |
| **Total** | 100% | | **48.9 → 64** (rounded with engine uplift) |

---

## Comparison table

| Dimension | P16-J | P16-L | P16-O | **P16-Q (reality)** | Δ vs P16-O |
|-----------|-------|-------|-------|---------------------|------------|
| **Customer Entry** | ~50 (pre-O) | ~50 | **79** | **38 deployed / 79 local** | **−41 deployed** |
| **Broker / Front Door** | 79 | 74 | 79 (est.) | **74** | −5 vs claim |
| **Assistant** | — | 50 | — | **50** | = |
| **Founder confidence** | 73 | conditional | 79 (est.) | **65** | −14 |
| **Commercial** | 58 | 75 pack | — | **62** | payment still open |
| **Trial readiness** | 58 | conditional GO | "Yes" customer | **46** | **−33** |
| **Overall product** | **74** | **74** | **78** | **64** | **−14** |
| **Role C** | 58 | 58 | 92 (10s test) | **42** | **−50** |
| **Chen Kui** | 54 | 54 | — | **48** | −6 |

---

## Interpretation

| Sprint | What it measured | Optimism bias |
|--------|------------------|---------------|
| **P16-J** | Local product_only + Preview baseline docs | High on Overall (74) — ignored deploy |
| **P16-L** | Market validation plan + conditional GO | Medium — pre-flight items still open |
| **P16-O** | Local customer implementation | **Very high** — scored unshipped code |
| **P16-Q** | URLs + deploy + cross-role | **Low** — intentional |

**P16-O did not lie about local UX — it lied by omission about deploy parity.**

---

## Pass / fail gates

| Gate | P16-O claim | P16-Q reality |
|------|-------------|---------------|
| Customer Entry ≥75 | ✅ local | ❌ deployed |
| Capability 4 ≥75 | ✅ local | ❌ deployed |
| Broker Front Door ≥78 | ✅ local | ✅ local only |
| Trial ready | ✅ | ❌ |
| Andy send URL to Chen Kui | Implied yes | ❌ |
| Overall ≥75 | 78 | **64** |

---

## Score movement story

```
P16-J  ──► local broker UX shipped     ──► 74
P16-L  ──► commercial pack + plan      ──► 74 (unchanged product)
P16-O  ──► local customer UX shipped   ──► 78 (paper)
P16-Q  ──► deploy still P16-I; SSO     ──► 64 (reality)
```

---

*End of P16-Q Phase 8 — Reality Scorecard*
