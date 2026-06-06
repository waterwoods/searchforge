# P16-Q Phase 7 — Failure Analysis

**Date:** 2026-06-01  
**Sprint:** P16-Q Reality Validation  
**Sources:** Phases 1–6, Preview verification, founder journey, role simulations  
**Method:** Map loss / trust break / usage stop; rank by severity

---

## Failure taxonomy

| Type | Definition |
|------|------------|
| **Lost** | User cannot find next action; wrong surface; bounce |
| **Trust break** | User decides product is broken, unsafe, or not real |
| **Usage stop** | User started once but abandons habit |

---

## Cross-simulation failure map

| # | Failure point | Simulations affected | Type | Severity |
|---|---------------|---------------------|------|----------|
| 1 | **Preview URL → Vercel SSO (401)** | Chen Kui, Role C, Assistant, Skeptical, Founder (deploy) | Trust break + stop | **P0 Critical** |
| 2 | **Production URL → customer tab default, Add-Car chrome** | Role C, Skeptical, Chen Kui (wrong link) | Lost + trust break | **P0 Critical** |
| 3 | **P16-O customer UX not deployed** | Founder, Role C, Chen Kui (customer path) | Trust break | **P0 Critical** |
| 4 | **`VITE_UNIFIED_INTAKE_PRODUCT_ONLY` not in Vercel dashboard** | All deploy paths | Usage stop (future redeploy) | **P1 High** |
| 5 | **No Andy authenticated Preview E2E log** | Founder, Chen Kui trial | Trust break (founder) | **P1 High** |
| 6 | **Empty broker queue on first open** | Assistant, Chen Kui, Skeptical | Lost | **P1 High** |
| 7 | **Demo queue vs paste — dual onboarding** | Founder, Chen Kui | Lost | **P2 Medium** |
| 8 | **English draft on Chinese WeChat paste** | Chen Kui, Assistant, Skeptical | Usage stop | **P2 Medium** |
| 9 | **Customer dev chrome: 4 tabs + 场景仿真** | Role C, Founder (customer test) | Lost | **P2 Medium** |
| 10 | **Contact-only handoff: two-step submit** | Founder, Role C (add-car path) | Lost | **P2 Medium** |
| 11 | **Follow-up plan buried below fold** | Assistant | Usage stop | **P2 Medium** |
| 12 | **OpenAI 429 → rules-only triage** | Founder (edge cases) | Trust break | **P2 Medium** |
| 13 | **No pricing on product surface** | Skeptical, Chen Kui | Trust break | **P2 Medium** |
| 14 | **Zero paying brokers / no social proof** | Skeptical, Chen Kui | Trust break | **P2 Medium** |
| 15 | **No mobile validation** | Assistant, Chen Kui | Usage stop | **P3 Low** |
| 16 | **Monospace case IDs / engineer chrome** | Skeptical, Role C | Trust break | **P3 Low** |
| 17 | **Dark app header wrapper** | All UI simulations | Trust break | **P3 Low** |
| 18 | **Production ignores `?tab=broker`** | Founder, Skeptical | Lost | **P3 Low** |
| 19 | **No WeChat integration story** | Skeptical, Chen Kui | Usage stop | **P3 Low** (accepted v1 scope) |
| 20 | **Invoice payment IDs empty** | Chen Kui payment | Usage stop at Day 7 | **P1 High** (commercial) |

---

## Where users get lost (ranked)

| Rank | Moment | User thought |
|------|--------|--------------|
| 1 | Open Preview link | "Link is broken" |
| 2 | Open Production link (broker) | "I'm on the wrong site" |
| 3 | Customer landing (old bundle) | "Which button — add car or type here?" |
| 4 | Empty broker queue | "Nothing works" |
| 5 | Handoff pending contact-only | "Submit once or twice?" |

---

## Where trust breaks (ranked)

| Rank | Moment | Trust damage |
|------|--------|--------------|
| 1 | Vercel login wall | "Not a product — dev infrastructure" |
| 2 | Customer UI for broker | "Founder doesn't understand my job" |
| 3 | 场景仿真 tab visible | "I'm in a test lab" |
| 4 | No peer customers | "Am I the guinea pig?" |
| 5 | Draft language mismatch | "AI doesn't understand my office" |

---

## Where usage stops (ranked)

| Rank | Day | Stop reason |
|------|-----|-------------|
| 1 | Day 0 | Cannot load URL |
| 2 | Day 1 | Faster to stay in WeChat for routine |
| 3 | Day 2 | Forgot URL / no reminder |
| 4 | Day 3 | Draft needed heavy edit every time |
| 5 | Day 7 | No invoice / no proof → won't pay |

---

## Severity summary

| Severity | Count | Must fix before unsupervised trial |
|----------|-------|----------------------------------|
| **P0 Critical** | 3 | All three |
| **P1 High** | 4 | At minimum #1, #3, #5, #20 |
| **P2 Medium** | 7 | Fix #6, #9 for Chen Kui quality |
| **P3 Low** | 6 | Defer |

---

## Key insight

**Engine failures are not the top failure mode.** Guardrail PASS, API PASS, local loop PASS.

**Distribution and deploy failures dominate.** Users never reach the triage engine on the URLs documented for trial.

P16-O improved **local customer code** but **increased deploy drift** — founder confidence may rise locally while **external reality score falls**.

---

*End of P16-Q Phase 7 — Failure Analysis*
