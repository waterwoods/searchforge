# P16-N Phase 8 — Professional SaaS Comparison (Customer Entry)

**Date:** 2026-06-01  
**Compare:** Unified Intake Customer Entry vs Stripe onboarding · Calendly scheduling · Typeform · HubSpot forms  
**Score each dimension:** 0–100

---

## Summary Scorecard

| Dimension | Customer Entry (current) | Stripe | Calendly | Typeform | HubSpot | Target (P16-N) |
|-----------|-------------------------|--------|----------|----------|---------|----------------|
| **Clarity** | **42** | 92 | 90 | 88 | 55 | 80 |
| **Trust** | **68** | 95 | 82 | 75 | 70 | 85 |
| **Density** | **35** | 88 | 90 | 85 | 40 | 80 |
| **Cognitive load** | **38** | 90 | 88 | 86 | 45 | 78 |
| **Professionalism** | **55** | 95 | 88 | 80 | 65 | 82 |
| **Weighted average** | **48** | 92 | 88 | 83 | 55 | **81** |

**P16-M baseline:** Customer empty ~50 · Post-handoff ~83  
**P16-N target:** Overall customer entry **≥75** (match broker trial credibility)

---

## Clarity (Current: 42)

| Product | Pattern | Customer Entry gap |
|---------|---------|-------------------|
| **Stripe** | "Create account" → email → done | We say 加车报价·客户统一报送 — internal GTM language |
| **Calendly** | "Select a time" — one job | We offer 6 intents before input |
| **Typeform** | Question text IS the page | We have 4 instruction layers before question |
| **HubSpot** | Form fields labeled simply | Our placeholders say "don't use this for add-car" |

**Fix:** Message-first headline; remove category grid; plain Chinese problem statement

---

## Trust (Current: 68)

| Product | Trust signals | Customer Entry |
|---------|---------------|----------------|
| **Stripe** | PCI, lock icons, status page | ✅ 不自动发送 repeated — good substance |
| **Calendly** | Brand polish, calendar preview | ✅ Chen Kui avatar in chrome |
| **Typeform** | Privacy link, minimal data | ⚠️ WeChat binding strip feels surveillance |
| **HubSpot** | Logo wall, GDPR | N/A |

**Strengths:** Manual-send boundary is clear in copy  
**Weaknesses:** Trust repeated 3× but not designed (no checkmark success); UTC footnote erodes trust ("system jargon"); 上传材料 without upload control breaks promise

**Fix:** One trust line + green confirmation check; remove engineer footnotes

---

## Density (Current: 35)

| Product | Words above fold (empty) | Customer Entry |
|---------|-------------------------|----------------|
| **Stripe** | ~25 | ~120 (tagline + ①②③ + labels) |
| **Calendly** | ~30 | ~120 |
| **Typeform** | ~15 | ~120 |
| **HubSpot** | ~80+ | Mid-flow ≈ HubSpot (field chips, tags) |

**Worst screens:** Empty landing · Add-car progress card with full record rail · Post-handoff result card

**Fix:** 40% element reduction (Phase 4); hero textarea only above fold

---

## Cognitive Load (Current: 38)

| Load source | Severity | SaaS comparison |
|-------------|----------|-----------------|
| Category decision before message | **Critical** | No benchmark product does this |
| Dual handoff path (chat phone vs button) | **High** | Stripe: one checkout button |
| Record rail 6 sections | **High** | Typeform: one question |
| Post-handoff 5 sections + 2 CTAs | **Medium** | Calendly: "You're scheduled" + add to calendar |
| Tab bar with broker tools | **Medium** | Stripe: customer portal separate from admin |

**Decision count empty state:** 4+ (which button? structured? text? other?)  
**Stripe empty state decisions:** 1

---

## Professionalism (Current: 55)

| Signal | Current | Professional bar |
|--------|---------|------------------|
| Visual rhythm | Nested grey cards | Flat white + one accent |
| Success state | Green card ✅ | Good — best moment |
| Loading state | Chat bubble spin ✅ | Acceptable |
| Empty state | Button grid ❌ | Feels like internal tool |
| Copy tone | Pilot/engineer mixed | Warm, plain, confident |
| Mobile | Textarea below fold ❌ | Typeform mobile-first |

**Closest match:** Post-handoff confirmation (Calendly-level)  
**Farthest match:** Empty landing (HubSpot form builder demo)

---

## Screen-by-Screen vs Benchmarks

### Empty Landing

| | Unified Intake | Typeform | Verdict |
|---|---------------|----------|---------|
| First impression | Insurance ops portal | Friendly form | ❌ |
| Time to first action | 10–15s | 2s | ❌ |
| Looks like paid product | Partial | Yes | ⚠️ |

### Mid-Flow

| | Unified Intake | Typeform | Verdict |
|---|---------------|----------|---------|
| One question focus | Partial (next_best_question) | Yes | ⚠️ |
| Progress indicator | Step track + card | Dots | ⚠️ |
| Feels conversational | Yes (bubbles) | Yes | ✅ |

### Confirmation

| | Unified Intake | Stripe receipt | Verdict |
|---|---------------|----------------|---------|
| Clear done state | Yes | Yes | ✅ |
| What happens next | Yes but buried | Prominent | ⚠️ |
| Reference number | Yes (monospace) | Subtle footer | ⚠️ |

### Status (My Requests)

| | Unified Intake | Stripe dashboard | Verdict |
|---|---------------|------------------|---------|
| List clarity | Good | Good | ✅ |
| Next action | Good CTA | Good | ✅ |
| Field dump | Too much | Summary only | ⚠️ |

---

## Gap Analysis — Path to 75+

| Dimension | Current | Gap to 75 | Top lever |
|-----------|---------|-----------|-----------|
| Clarity | 42 | −33 | Message-first landing |
| Trust | 68 | −7 | One trust line + success check |
| Density | 35 | −40 | Delete category grid |
| Cognitive load | 38 | −37 | One primary per screen |
| Professionalism | 55 | −20 | Separate customer URL; mobile hero input |

**Highest ROI:** Clarity + density + cognitive load are the **same fix** — empty state rewrite

---

## Competitive Position Statement

> Customer Entry **mid-flow and post-handoff** are within striking distance of Calendly/Typeform.  
> **Landing empty state** is the sole reason aggregate score stays ~50.  
> No new capabilities required — only reorder, hide, and rewrite copy.

---

*End of P16-N Phase 8 — Professional SaaS Comparison*
