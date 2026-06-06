# P16-Z2 Phase 8 — Capability Map

**Date:** 2026-06-01  
**Sprint:** P16-Z2 Case Intelligence Strategic Reverse Engineering  
**Builds on:** P16Z0_CAPABILITY_MAP_V2.md + competitive research  
**Question:** Which capabilities matter most for paid pilot in 2–3 weeks?

---

## North Star filter

Every capability scored against:

> **Chaos → Understanding → Case → Next Action → Outcome**

| Score | Meaning |
|-------|---------|
| **Critical** | Pilot fails without it |
| **High** | Broker pays / continues using |
| **Medium** | Nice; week 3+ |
| **Low** | Ignore for pilot |
| **Harmful** | Distraction; actively defer |

---

## Cap 1 — Broker Front Door

**Job:** Chen Kui opens URL between WeChat pings → paste → draft → copy → done in 2 minutes.

| Sub-capability | Status | Competitive benchmark | Pilot priority |
|----------------|--------|----------------------|----------------|
| Cold URL access (no SSO) | **Broken** (FP-004) | Table stakes | **Critical** |
| Paste → triage → draft | Current (~45 deploy) | Salesforce Case Classification | **Critical** |
| Copy-to-WeChat button | Current | Intercom saved reply | **Critical** |
| Chinese-only glance | Partial (EN mix) | HubSpot localization | **High** |
| Post-copy continuation CTA | Missing | Intercom handoff | **Critical** |
| Urgent-today queue filter | Missing | Zendesk views | **High** |
| Demo noise demotion | Partial | Linear minimal | **Medium** |
| Mobile usable | Unknown | Intercom messenger | **Medium** |
| Chen Kui ui_copy deploy parity | Partial | Config-driven | **High** |

**Cap 1 pilot score target:** 45 → **75** (deployed)

**What matters most:** Access + paste loop + Chinese trust + append discoverability.

---

## Cap 2 — Case Intelligence (Triage Engine)

**Job:** Transform messy paste into understanding — category, urgency, summary, fields.

| Sub-capability | Status | Competitive benchmark | Pilot priority |
|----------------|--------|----------------------|----------------|
| Classification (category + urgency) | **Strong** (~85) | Einstein Case Classification | Maintain |
| collected_fields extraction | Strong | Salesforce auto-fill | Maintain |
| still_needed_fields detection | Strong | Stripe recommended_evidence | Maintain |
| conversation_summary | Good post-P16-Y | Wrap-Up | **High** (merge) |
| Deadline extraction | Partial | Zendesk SLA | **High** |
| Correction handling | Weak (Y44) | Field history supersede | **High** |
| Multi-turn summary merge | **Broken** (P16-Y P0) | Context engineering | **Critical** |
| Risk scores v4/v5 | Backend only | Einstein confidence | **Medium** |
| OCR fusion | API only | Stripe evidence merge | **Medium** (week 2) |
| LLM path | Unverified | Fin | **Low** |

**Cap 2 pilot score target:** 85 → **88** (battery gate)

**What matters most:** Multi-turn merge + category-specific next-action templates. Engine is built — tune, don't rebuild.

---

## Cap 3 — Structured Case Record

**Job:** Office can act without re-reading raw WeChat paste.

| Sub-capability | Status | Competitive benchmark | Pilot priority |
|----------------|--------|----------------------|----------------|
| Case persist (Postgres) | Current | Salesforce Case | **Critical** |
| Queue + reopen | Current | Zendesk views | **Critical** |
| case_messages thread | Backend ✅ UI partial | Intercom parts | **High** |
| broker_next_step | Weak wording | Salesforce NBA | **Critical** |
| client_prep | Good | Intercom macro | **High** |
| Glance「还缺什么」| Current | still_needed UX | **High** |
| Full case draft card | Hidden | Wrap-Up card | **Low** |
| Attachment on case | Backend ✅ | Salesforce Files | **Medium** |
| Duplicate-case prevention | UX bug | Zendesk merge | **High** |

**Cap 3 pilot score target:** 72 → **80**

**What matters most:** Office Actionability wording + thread visibility on reopen.

---

## Cap 4 — Customer Intake Collection

**Job:** Customer sends request without confusion; office receives structured handoff.

| Sub-capability | Status | Competitive benchmark | Pilot priority |
|----------------|--------|----------------------|----------------|
| CustomerEntryTab multi-turn | **Hidden** on trial | Intercom messenger | **Medium** (week 3) |
| Message-first landing | **Broken** (3 buttons) | Intercom Fin | **High** when exposed |
| 我的办理 status | Hidden | HubSpot portal | **Medium** |
| Formal handoff moment | Over-built | Intercom convert | **High** (simplify) |
| Customer upload | Text only | Portal upload | **Low** (week 3+) |
| Add-car structured flow | Complex | Typed ticket | **Medium** |
| Separate customer URL | Not deployed | HubSpot portal | **Medium** |

**Cap 4 pilot score target:** 55 → **65** (broker-first; customer week 3)

**What matters most for 2-week pilot:** **Broker paste path first.** Customer tab is Cap 4 revival, not Cap 1 blocker. Chen Kui simulation: broker paste is Day 0; customer self-serve is Day 7+.

---

## Cap 5 — Case Lifecycle Management

**Job:** Message 2–4 updates same case; office knows what's waiting.

| Sub-capability | Status | Competitive benchmark | Pilot priority |
|----------------|--------|----------------------|----------------|
| Append API | **Strong** backend | Zendesk comment append | **Critical** (UX) |
| Append discoverability | **Broken** (38/100) | Intercom continuity | **Critical** |
| waiting_on field | Exists, not prominent | Salesforce status | **High** |
| follow-up editor | Hidden | Intercom snooze | **Medium** |
| Activity timeline | Hidden | Case Feed | **Low** |
| Boundary detection (new vs same) | Current | Zendesk merge | Maintain |
| Lifecycle derivation | Current | Status machine | Maintain |
| Multi-turn continuity UX | **41/100** | Intercom | **Critical** |

**Cap 5 pilot score target:** 53 → **70**

**What matters most:** Post-copy append bridge. Zero new backend.

---

## Cap 6 — Trial Conversion

**Job:** Andy → Chen Kui → invoice → testimonial in 2–3 weeks.

| Sub-capability | Status | Competitive benchmark | Pilot priority |
|----------------|--------|----------------------|----------------|
| trial_launch_check.sh | Current | CI gate | **Critical** |
| Commercial docs pack | Current | Sales enablement | Maintain |
| Observation log | **Empty** | Zendesk QA | **Critical** (process) |
| Invoice with payment IDs | **Empty** | Manual billing | **Critical** (founder) |
| Day 0 supervised session | Not started | HubSpot onboarding | **Critical** |
| 15-min demo script | Current | — | Maintain |
| Testimonial capture | Not started | CSAT | **High** (Day 7) |
| Time-saved evidence | None | Outcome pricing | **High** |

**Cap 6 pilot score target:** 51 → **75**

**What matters most:** FP-004 + observation log row 1 + supervised Day 0. Mostly founder ops.

---

## Cap 7 — Founder / Operator Control

**Job:** Andy ships with confidence; no silent regressions.

| Sub-capability | Status | Competitive benchmark | Pilot priority |
|----------------|--------|----------------------|----------------|
| guardrail_inbox_triage.sh | Current | Stripe CI | **Critical** |
| P16-Y battery gate | Current | Rubric QA | **High** |
| P16-T health runner | Current | Datadog | **High** |
| Preview SSO audit | Broken | Security | **Critical** |
| Deploy parity script | Current | — | Maintain |
| Failure pattern library | Current | SRE | Maintain |
| ScenarioReplayTab | Current | Sandbox | **Medium** |
| 197 lab scripts | Noise | — | **Ignore** |

**Cap 7 pilot score target:** 65 → **80**

---

## Capability priority matrix (all caps)

```
                    IMPACT ON PAID PILOT
                    Low         High
              ┌──────────┬──────────┐
         Low  │ Cap 7    │ Cap 4    │
    EFFORT    │ (lab)    │ (customer│
              │          │  tab)    │
              ├──────────┼──────────┤
         High │ Cap 6    │ Cap 1,2  │
              │ (process)│ Cap 3,5  │
              └──────────┴──────────┘
```

---

## Ranked capabilities (what matters most)

| Rank | Capability | Cap | Why |
|------|------------|-----|-----|
| 1 | Paste → case → copy (broker loop) | 1, 2, 3 | Core product soul |
| 2 | Trial URL access | 1, 6, 7 | Blocks everything |
| 3 | Append discoverability + merge | 2, 5 | Multi-turn = real office workflow |
| 4 | broker_next_step Chinese specificity | 2, 3 | Office Actionability unlock |
| 5 | Observation log + Day 0 | 6 | Payment evidence |
| 6 | guardrail + battery CI | 2, 7 | Quality without Andy QA every paste |
| 7 | Cancel notice excellence | 2 | Trial wedge scenario |
| 8 | Urgent queue + deadline display | 1, 5 | 50 unread WeChat context |
| 9 | OCR on broker upload | 2 | Week 2 differentiator |
| 10 | Customer tab exposure | 4 | Week 3; not Day 0 |

---

## Hidden high-value assets (revive, don't rebuild)

From P16-Z0 + this sprint:

| Asset | Cap | Action |
|-------|-----|--------|
| append-message API | 5 | Teach in UI |
| CustomerEntryTab | 4 | Enable week 3 |
| v4/v5 risk scores | 2, 3 | Show in glance |
| OCR sidecar | 2 | Wire upload |
| follow-up editor | 5 | Unhide on trial |
| ScenarioReplayTab | 7 | Rehearsal |
| P16-Y append merge spec | 2 | Implement P0 |

---

## Capabilities that do NOT matter for pilot

| Capability | Cap | Verdict |
|------------|-----|---------|
| P17 platform | — | Never |
| Stripe billing | 6 | Never |
| Multi-tenant auth | — | Never |
| Voice / IVR | — | Never |
| Full CRM | — | Never |
| PDF IDP | 2 | Defer |
| SimulationAssistant.tsx | 7 | Delete |
| ML distillation experiment | 2 | Ignore |
| Audit export scaffold | 7 | Ignore |
| Platform_full lab routers | 7 | Ignore |

---

*End of P16-Z2 Phase 8 — Capability Map*
