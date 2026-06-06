# Product Readiness Scorecard — 12 Macro Goals

**Assessment date:** 2026-03-25  
**Method:** Repo inspection + referenced sprint reports + key file spot-checks (not a full QA pass of production URLs).

---

## Summary table

| # | Goal | State | ~Complete | Next priority? |
|---|------|-------|-----------|----------------|
| 1 | Narrow positioning | Mostly there | 78% | Later (maintain; reinforce in UI/script) |
| 2 | Formal service-entry portal | Partial | 52% | **Yes** |
| 3 | Handoff-ready case result | Mostly there | 72% | **Yes** (polish + edge honesty) |
| 4 | Add-Car flagship strong | Mostly there | 82% | Later (fix known semantic edge) |
| 5 | Human-handoff boundaries clear | Mostly there | 76% | Later |
| 6 | Hot-plug / client-pack | Partial | 62% | **Yes** (targeted isolation debt) |
| 7 | Persistence planned appropriately | Mostly there | 68% | Later |
| 8 | Pilot feedback readiness | Mostly there | 74% | **Yes** (launch/evidence loop) |
| 9 | Validation / regression discipline | Mostly there | 88% | No |
| 10 | Same-industry migration credible | Partial | 64% | Later |
| 11 | Sales / monetization framing | Mostly there | 72% | Later |
| 12 | Simplicity preserved | Partial | 58% | **Yes** (guard scope in UX) |

---

## Done / partial / missing map (coarse)

| Bucket | Goals |
|--------|--------|
| **Strong (mostly ≥70%)** | 1, 3, 4, 5, 7, 8, 9, 11 |
| **Partial (≈50–65%)** | 2, 6, 10, 12 |

**Nothing is literally “missing” at macro level** — the product exists — but **2, 6, 10, 12** are the main **honest partials** that affect sellability and replication storytelling.

---

## Per-goal detail

### 1. Narrow product positioning

| Field | Content |
|-------|---------|
| **State** | Mostly there |
| **~Complete** | 78% |
| **Evidence** | `NARROW_POSITIONING_AND_OPERATOR_VALUE_SPRINT/FINAL_REPORT.md`; `docs/STANDARD_SCENARIO_PACKAGE.md` one-sentence offer; engine is structured for “paste → case → draft,” not CRM. |
| **Biggest gap** | **Pitch/UI drift:** workbench + simulation surfaces can still feel “bigger than the sentence we sell” unless first-screen and demo script are disciplined. |
| **Next priority?** | Later — docs are strong; reinforcement is ongoing. |

### 2. Frontend: formal service-entry portal

| Field | Content |
|-------|---------|
| **State** | Partial |
| **~Complete** | 52% |
| **Evidence** | `UnifiedIntakePage.tsx` implements full Customer Entry + Broker Workbench + rich examples; `clientConfig.ts` supports substantial `ui_copy`. |
| **Biggest gap** | **Density / dual audience:** same page carries founder/demo affordances and full office tooling; “formal customer portal” is not yet the *dominant* first impression without careful demo path. |
| **Next priority?** | **Yes** — high ROI for broker credibility in first 60 seconds. |

### 3. Handoff-ready case result

| Field | Content |
|-------|---------|
| **State** | Mostly there |
| **~Complete** | 72% |
| **Evidence** | `triage.py` `REQUIRED_FIELDS`, `WORKFLOW_STATE_KEYS`; workbench concepts in `STANDARD_SCENARIO_PACKAGE.md`; `case_store` persists workflow-related state. |
| **Biggest gap** | **Semantic polish:** pre-broker acceptance noted `quote_ready` vs `still_needed_fields` inconsistency on one flagship dense message — undermines “trust the card” if it surfaces live. |
| **Next priority?** | **Yes** — fix or explicitly frame; affects broker trust. |

### 4. Add-Car flagship path

| Field | Content |
|-------|---------|
| **State** | Mostly there |
| **~Complete** | 82% |
| **Evidence** | Insurance markers include `add_vehicle`; `config_loader` + industry/client configs; add-car transaction strings in `clientConfig.ts`; `PRE_BROKER` report: strong path, one strict check failed. |
| **Biggest gap** | **One acceptance edge case** (quote_ready + delivery_date still needed) + any remaining branch-specific wording not client-owned. |
| **Next priority?** | Later — after small fix or narrative hedge. |

### 5. Human-handoff boundaries

| Field | Content |
|-------|---------|
| **State** | Mostly there |
| **~Complete** | 76% |
| **Evidence** | Append/boundary batteries in `guardrail_inbox_triage.sh` (`run_case_boundary_battery.py`, `run_append_boundary_ab_scenarios.py`); `handoff_phrases.json` pattern; product docs: no auto-send. |
| **Biggest gap** | **LLM / rule brittleness** remains; human review still mandatory — must stay explicit in any pilot contract. |
| **Next priority?** | Later — monitor trial feedback. |

### 6. Hot-plug / client-pack structure

| Field | Content |
|-------|---------|
| **State** | Partial |
| **~Complete** | 62% |
| **Evidence** | `config_loader.py` industry + client merge; `SECOND_BROKER_CLIENT_PACK_DRILL/FINAL_REPORT.md` documents swapped surfaces + remaining leaks; guardrail includes cross-client A/B. |
| **Biggest gap** | **Residual engine-resident strings**, default `chen_kui`, industry markers with broker-specific tokens; silent fallback to Chen handoff file called **dangerous** in drill. |
| **Next priority?** | **Yes** — targeted isolation fixes unlock honest “second broker” story. |

### 7. Database / persistence planning

| Field | Content |
|-------|---------|
| **State** | Mostly there |
| **~Complete** | 68% |
| **Evidence** | `case_store.py`: JSON file, caps, attachments dir, env `UNIFIED_INTAKE_CASES_PATH` — aligned with demo/pilot scope in `insurance_paid_pilot_goal.md` (no multi-tenant). |
| **Biggest gap** | **Honest narrative:** if pilot implies “never loses cases,” JSON single-node limits must be clear; no enterprise HA story. |
| **Next priority?** | Later — document + operational backup unless pilot demands more. |

### 8. Pilot feedback readiness

| Field | Content |
|-------|---------|
| **State** | Mostly there |
| **~Complete** | 74% |
| **Evidence** | Extensive `docs/trial/`; `PRE_BROKER` says **show for feedback** with caveats; `trial_readiness_check.sh` / `trial_launch_check.sh` referenced in `AGENTS.md`. |
| **Biggest gap** | **Production URL alignment** called out as not fully verified in pre-broker report — affects “real pilot” logistics, not only code. |
| **Next priority?** | **Yes** — close the last-mile operational loop. |

### 9. Validation / regression discipline

| Field | Content |
|-------|---------|
| **State** | Mostly there |
| **~Complete** | 88% |
| **Evidence** | `guardrail_inbox_triage.sh`: scenario pack, API optional, continuity, persistence, workflow backbone, multi-turn, adversarial, complex adversarial, case boundary, simulation assistant, broker trial stress, handoff timing, standard package grep, client-aware handoff, identity append, cross-client A/B, append boundary A/B, residual copy A/B, phrase-map A/B. |
| **Biggest gap** | **Guardrail ≠ broker perception** — still need live paste habits and narrative; occasional semantic tests need widening when fixed. |
| **Next priority?** | No — maintain on change. |

### 10. Same-industry migration readiness

| Field | Content |
|-------|---------|
| **State** | Partial |
| **~Complete** | 64% |
| **Evidence** | Second broker pack + drill runner PASS; explicit portability gaps documented. |
| **Biggest gap** | **Voice parity across all branches** and removal of dangerous fallbacks — migration is credible **with engineering time**, not plug-and-play marketing yet. |
| **Next priority?** | Later — unless second broker becomes immediate revenue. |

### 11. Sales / monetization framing

| Field | Content |
|-------|---------|
| **State** | Mostly there |
| **~Complete** | 72% |
| **Evidence** | `insurance_paid_pilot_goal.md` manual payment, single broker; monetization specs in narrow positioning sprint; standard package naming. |
| **Biggest gap** | **Offer packaging in UI** (what they see vs what founder says) still improvable; testimonial capture process is business-side. |
| **Next priority?** | Later — after pilot starts. |

### 12. Product simplicity

| Field | Content |
|-------|---------|
| **State** | Partial |
| **~Complete** | 58% |
| **Evidence** | Large `UnifiedIntakePage.tsx`; many capabilities (simulation, queues, attachments) justified for pilot but increase **cognitive load**. |
| **Biggest gap** | **Scope creep in UX** could contradict “narrow tool” positioning without a guided mode or cleaner customer-only shell. |
| **Next priority?** | **Yes** — tie UI to narrow job (can be same code, clearer modes). |

---

*End of scorecard*
