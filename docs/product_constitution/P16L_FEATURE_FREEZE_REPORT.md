# P16-L Feature Freeze Report

**Date:** 2026-06-01  
**Sprint:** P16-L — Real Market Validation  
**Authority:** `NORTH_STAR_V1.md` §6, `ROADMAP_FROM_CONSTITUTION.md` "Not on Roadmap", P16 constitution 90-day lock  
**Rule:** Unified Intake V1 is feature-frozen until trial produces payment evidence or explicit kill.

---

## Freeze declaration

**Stop building. Stop adding features. Stop adding architecture. Stop adding platform capabilities.**

Allowed work during P16-L:
- Deploy Preview with existing Sprint A bundle (no UI changes)
- Run supervised trial with observation log v3
- Fill commercial details (invoice IDs)
- Fix-now **only after Day 7** from logged friction (max 3 items)

Not allowed:
- P17 or any new capability
- Constitution changes
- Repo cleanup sprints
- Prompt/schema changes mid-trial

---

## Features that are tempting (and why they feel urgent)

| Temptation | Why it feels urgent | Real blocker it doesn't fix |
|------------|---------------------|------------------------------|
| **WeChat sync** | Eliminates paste fatigue | Unknown if paste is the kill reason; 90-day anti-goal |
| **OCR / screenshot upload** | Brokers send images not text | Constitution v1 = paste text only; untested hypothesis |
| **Stripe checkout** | "Professional" payment | Manual invoice is v1; no proof layer filled yet |
| **Better drafts (prompt tune)** | 大改 on real threads | Might help; confounds trial evidence if shipped mid-week |
| **Hide demo card** | Day 0 confusion | P16-J P1 #7; polish not proof |
| **White header / branding** | Looks unfinished | Trust polish; Chen Kui knows Andy — not payment blocker |
| **Mobile layout** | Assistant on phone | No assistant trial mandate yet |
| **English → Chinese draft** | Mixed-language paste | Log friction first; might be edit habit not bug |
| **Queue filter simplification** | P16-I partial | Lifecycle cap 55; trial can proceed |
| **chen_kui ui_copy.json load** | Label trust | Sprint 5 item; defer until trial log says so |
| **Production promote** | Stable URL | **Deploy existing bundle — not a feature**; required for trial |
| **Relax Preview SSO** | URL access | Infra/config — not product feature |
| **Simulation tab restore** | Training | Replaced by inline practice; constitution aligned |
| **Add-car portal redesign** | Master outline GTM | Cancellation-first wedge locked |
| **RAG /demo integration** | Existing codebase | Anti-drift test #4: workbench URL only |
| **Multi-tenant auth** | Second broker | Blocked until first testimonial |
| **CRM / carrier APIs** | Broker asks on Day 7 Q4 | Expected defer; log only |
| **New AI agents** | Platform fantasy | Capability 7 is founder ops, not new agents |
| **Capability 8** | Feels like progress | Constitution: exactly 7 capabilities |
| **Event bus / workflow engine** | Engineering elegance | Platform anti-goal |
| **$199 tier** | Upsell dream | Features don't exist; North Star says unlikely no |

---

## Features that should NOT be built (locked)

From `NORTH_STAR_V1.md` §6 — 90-day lock:

1. Stripe / billing portal / self-serve signup  
2. WeChat or email inbox sync  
3. Multi-tenant / SSO / per-broker isolation (product feature — Preview SSO config is ops)  
4. Full CRM or carrier API integration  
5. In-product OCR / screenshot upload as primary path  
6. Platform SKU / workflow engine / event bus  
7. $199 enterprise tier  
8. Repo-wide cleanup / lab isolation sprints during active broker trial  
9. **New feature work before one broker completes 7-day trial with logged evidence**  
10. Auto-send of client replies  

---

## Features that would distract from validation

| Distraction | How it hurts P16-L |
|-------------|-------------------|
| P17 product sprint | Delays trial; confounds evidence |
| UI polish sprint | Andy builds instead of observing |
| Architecture refactor | Same |
| Second broker outreach | No testimonial yet |
| Marketing site | No payment proof |
| New scenarios / categories | Engine expansion not validation |
| Lab mode improvements | Brokers never see lab |
| Guardrail expansion | Engine already PASS; not blocker |
| Documentation sprawl beyond P16-L | This sprint's docs are the last pack until post-Day 7 |
| ChatGPT comparison deck | Sales material without proof |

---

## Fix-now gate (post Day 7 only)

If trial log shows friction, **maximum 3 fixes** from observation log:

| Allowed fix type | Example from P16-J P1 |
|------------------|----------------------|
| Copy / label | Merge wayfinding + trust line |
| Hide / collapse | Demote demo card to link |
| Draft tuning | Top failure category from log case IDs |
| Deploy promote | Production = Sprint A bundle |

| Disallowed even as "fix" | Example |
|--------------------------|---------|
| New capability | WeChat sync because broker asked |
| New tab | Assistant dashboard |
| Billing automation | Stripe because manual felt awkward |

---

## What Andy might feel like building (founder trap watchlist)

| Feeling | Build urge | Correct response |
|---------|------------|------------------|
| "Chen Kui confused on Day 1" | UI sprint | 5-min WeChat help; log friction |
| "Draft was bad once" | Prompt rewrite | Log case; fix after Day 7 if pattern |
| "Preview SSO embarrassed us" | New hosting architecture | Config/deploy only |
| "He asked for OCR" | Upload feature | Log Q4; reset expectations |
| "Trial is slow" | Add features to impress | More real pastes, not code |
| "Assistant can't login" | Auth system | Chen Kui-only trial; $49 not $99 |

---

## Allowed non-feature work (P16-L scope)

| Work | Type |
|------|------|
| Preview redeploy + env persist | Deploy |
| Andy Preview E2E log | Validation |
| Fill invoice payment IDs | Commercial |
| Run Chen Kui Day 0–7 | Trial |
| Link log v3 from TRIAL_ONE_PATH | Docs wiring |
| Store artifacts in results/trial_logs/ | Evidence |

---

## Success definition for feature freeze

**Success = observation log v3 filled with real cases + Day 7 payment decision.**

Not success:
- Shipped 5 improvements during trial week
- Started P17
- "Feels ready" without gates

---

*End of P16-L Feature Freeze Report*
