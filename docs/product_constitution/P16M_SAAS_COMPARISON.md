# P16-M Phase 6 — Professional SaaS Comparison

**Date:** 2026-06-01  
**Products:** Unified Intake vs Stripe · Linear · Notion · Calendly · HubSpot  
**Focus:** Navigation · Density · Empty state · Success state · Onboarding · Trust

---

## Comparison Matrix

| Dimension | Unified Intake (trial) | Stripe | Linear | Notion | Calendly | HubSpot |
|-----------|------------------------|--------|--------|--------|----------|---------|
| **Navigation** | Single page, no sidebar (trial) ✅ | Minimal top nav | Sidebar 5 items max | Sidebar + pages | 3-step wizard | Heavy nav ❌ |
| **Page density** | Medium-high; collapses help | Low | Low-medium | Medium (user-built) | Very low | High ❌ |
| **Empty state** | Text hint + demo card | Illustration + 1 CTA | Command palette hint | Template gallery | Calendar preview | Checklist |
| **Success state** | Glance + draft copy | Receipt + next steps | Issue closed animation | Page created toast | Confirmation + calendar | Deal stage |
| **Onboarding** | Demo queue + wayfinding | Checklist embed | Import issues | Templates | "Create event type" | Academy |
| **Trust** | Manual-send repeated | PCI badges, status page | SSO, audit log | Privacy page | Brand polish | Certifications |

**Unified Intake closest match:** **Calendly** (single job, linear flow) — if broker path only  
**Unified Intake farthest match:** **HubSpot** (full dev broker UI tag density)

---

## Navigation

| Product | Pattern | Unified Intake |
|---------|---------|----------------|
| Stripe | Dashboard sections; one task per screen | Trial: ✅ one screen. Dev: ❌ 4 tabs + sidebar |
| Linear | Inbox → issue | Queue → case ≈ Linear inbox ✅ |
| Notion | User-defined tree | Over-built for broker ❌ |
| Calendly | Event type → book | Paste → triage ≈ ✅ |
| HubSpot | Objects everywhere | Dev queue tags ≈ HubSpot ❌ |

**Gap:** Customer portal still has Notion-like "choose your adventure" before action.

---

## Page Density

| Product | Words above fold | Unified Intake trial broker |
|---------|------------------|----------------------------|
| Stripe | ~30 | ~80 (trust + wayfinding + subtitles) |
| Linear | ~20 | ~60 |
| Calendly | ~25 | ~70 |
| Notion | Variable | N/A |
| HubSpot | ~120+ | Dev broker ≈ HubSpot |

**Gap:** 2–3× copy density vs Stripe/Calendly on empty broker page.

---

## Empty State

| Product | Empty pattern | Unified Intake |
|---------|---------------|----------------|
| Stripe | "Create your first payment link" + button | Paste area ✅ but demo card splits attention |
| Linear | "No issues" + C keyboard hint | Queue hint ✅ |
| Calendly | Visual of booking page | No outcome preview ❌ |
| Notion | Template picker | Customer portal ≈ template overload ❌ |

**Gap:** No static preview of "what good looks like" (draft snippet mock).

---

## Success State

| Product | Success pattern | Unified Intake |
|---------|-----------------|----------------|
| Stripe | Green check + receipt | Glance box (blue gradient, not success green) |
| Linear | Status change + assignee | Status dropdown — subtle |
| Calendly | "You're scheduled" | 受理结果卡 ✅ customer side |
| HubSpot | Deal stage moved | case_status — OK |

**Gap:** Broker success should feel like **completion** (copy draft = done), not another form section.

---

## Onboarding

| Product | Day 0 | Unified Intake |
|---------|-------|----------------|
| Stripe | Interactive checklist | Demo queue ✅ |
| Linear | Import / create team | Practice scenarios ✅ |
| Calendly | Connect calendar | N/A |
| HubSpot | Setup wizard (overwhelming) | Pilot intro alert (full UI) ❌ |

**Gap:** Assistant persona sees two onboarding paths (demo vs paste).

---

## Trust

| Product | Trust signals | Unified Intake |
|---------|---------------|----------------|
| Stripe | Uptime, PCI, support | 不自动发送 ✅ |
| Linear | SOC2 badge | Chen Kui avatar ✅ |
| Calendly | Professional polish | Ant Design default ⚠️ |
| HubSpot | Logo wall | None needed |

**Gap:** Trust is **copy-based** not **design-based** — no calm footer, no status link.

---

## Per-Product "Steal This"

| Product | Steal | Apply to Unified Intake |
|---------|-------|-------------------------|
| **Stripe** | One primary button color; white space | Flatten glance card; one blue |
| **Linear** | List row = title + label max | Queue: urgency + one line |
| **Notion** | Collapsed by default | ✅ already on detail |
| **Calendly** | 3-step progress, one screen | Broker paste → result → copy |
| **HubSpot** | (Avoid) tag walls, filters | Delete dev chrome from trial |

---

## Overall SaaS Maturity Score

| Product benchmark | Unified Intake trial broker | Gap |
|-------------------|----------------------------|-----|
| Stripe (85) | 74 | −11 |
| Linear (82) | 76 | −6 |
| Calendly (88) | 78 | −10 |
| Notion (80) | 65 (customer) | −15 |
| HubSpot (70) | 40 (dev broker) | −30 |

**Interpretation:** Trial broker path is **Calendly-class** on flow, **Stripe-class** on trust copy, **below Linear** on list density, **far below** on customer empty state.

---

*End of P16-M SaaS Comparison*
