# P16-M Phase 3 — Stripe Benchmark

**Date:** 2026-06-01  
**Reviewer lens:** Stripe PM reviewing Unified Intake for commercial readiness  
**Build reference:** `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1` + full dev UI  
**Scale:** 0–100 per dimension

---

## Scoring Rubric

| Score | Meaning |
|-------|---------|
| 90–100 | Stripe-shippable; no explanation needed |
| 75–89 | Professional; minor polish |
| 60–74 | Usable; trust/density gaps |
| 40–59 | Internal tool wearing SaaS costume |
| 0–39 | Demo lab |

---

## Screen 1 — Broker Workbench Empty (`product_only`)

| Dimension | Score | Stripe PM notes |
|-----------|-------|-----------------|
| **Clarity** | 78 | Paste-first story clear; duplicate lines (subtitle + trust + wayfinding + card extra) dilute |
| **Focus** | 72 | Demo card competes with paste on first visit; should be empty-state footnote |
| **Density** | 74 | Acceptable; dark header + white island feels like admin wrapper not product |
| **Trust** | 82 | Manual-send repeated enough; avatar helps; no scary engineer labels in product_only |
| **Professionalism** | 70 | Ant Design defaults visible; no custom typography/spacing system |
| **Overall** | **75** | "I'd ship a beta with copy merge + demo demotion" |

---

## Screen 2 — Broker Workbench + Case Detail (`product_only`)

| Dimension | Score | Stripe PM notes |
|-----------|-------|-----------------|
| **Clarity** | 80 | Glance block is strong; ①②③ numbering feels internal doc not product |
| **Focus** | 76 | Copy draft is right hero; status dropdown + tags still compete |
| **Density** | 68 | Good collapses; reopened append card adds vertical stack |
| **Trust** | 79 | Draft labeled 确认后再发; collapsed raw thread correct |
| **Professionalism** | 73 | Gradient boxes and multi-color borders = dashboard not Stripe calm |
| **Overall** | **75** | "Core loop works; visual system needs one primary color lane" |

---

## Screen 3 — Broker Workbench Full Dev

| Dimension | Score | Stripe PM notes |
|-----------|-------|-----------------|
| **Clarity** | 42 | Tag wall on queue cards = instant "this is ours not yours" |
| **Focus** | 38 | KPI row + filters + paste + queue = four products on one page |
| **Density** | 35 | Worst offender; 12+ tags per row |
| **Trust** | 45 | PG mirror + API URL destroys commercial trust |
| **Professionalism** | 40 | Engineering workbench; not customer-facing |
| **Overall** | **40** | "Would not show to a paying broker" |

---

## Screen 4 — Customer Intake Empty (full UI)

| Dimension | Score | Stripe PM notes |
|-----------|-------|-----------------|
| **Clarity** | 58 | Add-car-first vs "unified" confuses; too many paths before first action |
| **Focus** | 52 | Three button columns + structured form + free text = choice paralysis |
| **Density** | 50 | Hero + step track + path card = scroll before type |
| **Trust** | 65 | Broker branding present; scope paragraph too long |
| **Professionalism** | 62 | Better than broker dev mode; still not Calendly-simple |
| **Overall** | **57** | "Customer would bounce; broker shouldn't lead with this in trial" |

---

## Screen 5 — Customer Intake Active / Result

| Dimension | Score | Stripe PM notes |
|-----------|-------|-----------------|
| **Clarity** | 68 | Result card good; thread + progress + input = three paradigms |
| **Focus** | 64 | Post-handoff should be one card not card + collapsed thread + input |
| **Density** | 60 | Status strips + rails + tags acceptable for insurance domain |
| **Trust** | 70 | Timestamps honest but over-explained |
| **Professionalism** | 65 | Chat bubbles feel consumer; result card feels enterprise — split personality |
| **Overall** | **65** | "Secondary surface OK; not the GTM front door" |

---

## Screen 6 — Global Chrome

| Dimension | Score | Stripe PM notes |
|-----------|-------|-----------------|
| **Clarity** | 74 | Brand card works; app title duplicates in dark header |
| **Focus** | 80 | Single-tab trial mode good |
| **Density** | 72 | Two headers (dark + white) = wasted vertical |
| **Trust** | 85 | Chen Kui identity strong |
| **Professionalism** | 68 | Grey gutter + nested cards = nested admin |
| **Overall** | **76** | "Merge chrome layers" |

---

## Aggregate Stripe Scorecard

| Screen | Overall |
|--------|---------|
| Broker empty (trial) | 75 |
| Broker + case (trial) | 75 |
| Broker full dev | 40 |
| Customer empty | 57 |
| Customer active | 65 |
| Global chrome | 76 |
| **Weighted (trial GTM)** | **74** |
| **Weighted (full codebase)** | **63** |

---

## Stripe PM Verdict (one paragraph)

Unified Intake's **broker trial path** is past "internal dashboard" and into " credible early SaaS" — paste → structured glance → copy draft is the right Stripe-shaped transaction. It fails Stripe bar on **visual system** (too many border colors, alert types, nested cards), **first-visit focus** (demo card placement), and **dev-mode leakage** (tag walls, infra labels). Customer portal is **not Stripe-grade** for cold arrival: too many entry paths before value. Stripe would **not** add features; they'd delete half the labels, merge headers, and make one green primary button story end-to-end.

---

## Stripe "Would Fix First" (evaluation only)

1. One header, one trust line, one primary CTA above fold  
2. Remove all monospace IDs from default view  
3. Replace gradient glance box with flat white + left accent  
4. Demo = text link in empty paste state  
5. Customer: one button "开始" not three columns  

---

*End of P16-M Stripe Benchmark*
