# P16-Z0 Capability Map v2

**Date:** 2026-06-01  
**Sprint:** P16-Z0 — Phase 8  
**Supersedes for archaeology purposes:** `CAPABILITY_MAP_V1.md` (adds hidden/broken/unused layer)  
**Authority unchanged:** `contracts/CAPABILITY_*.md`, Constitution V1

---

## Map legend

| Layer | Meaning |
|-------|---------|
| **Current** | Works on deployed trial path or primary operator script |
| **Hidden** | Implemented; gated by `product_only`, env, or lab route |
| **Broken** | Known fail on Preview / trial URL |
| **Unused** | Code exists; no caller or zero imports |
| **High-value** | High ROI if revived (not rebuilt) |

---

## By constitution capability (7 caps)

### Cap 1 — Broker Front Door

| Layer | Items |
|-------|-------|
| **Current** | Broker workbench paste, demo queue load, triage API on Preview (when SSO fixed) |
| **Hidden** | Customer tab, simulation tab, lab routes |
| **Broken** | Cold Preview URL 401 (FP-004); P16-W crash fixed but redeploy-dependent |
| **Unused** | — |
| **High-value** | Post-copy continuation CTA; Chinese-only glance (P16-M #5, P16-X #5) |

**Scores:** ~45 deploy / ~70 local

---

### Cap 2 — Urgent Message Triage

| Layer | Items |
|-------|-------|
| **Current** | Classification, urgency, cancellation/payment lanes, guardrail PASS |
| **Hidden** | Assist layer, debug perf metrics |
| **Broken** | — (engine strong) |
| **Unused** | — |
| **High-value** | Maintain P16-Y battery in CI |

**Scores:** ~85

---

### Cap 3 — Structured Case Record

| Layer | Items |
|-------|-------|
| **Current** | `collected_fields`, `still_needed_fields`, case persist, queue |
| **Hidden** | `case_messages` thread UI, risk scores, full case draft card |
| **Broken** | Duplicate-case risk on top paste (UX) |
| **Unused** | `getRecentCustomerMessages` import |
| **High-value** | Append promoted in glance (P16-M #28) |

**Scores:** ~72

---

### Cap 4 — Customer Intake Collection

| Layer | Items |
|-------|-------|
| **Current** | Full implementation in dev (`CustomerEntryTab`) |
| **Hidden** | **Entire tab on trial URL** |
| **Broken** | Deploy path N/A for trial |
| **Unused** | — |
| **High-value** | Separate customer route (P16-M #23) — **after** Cap 1/5 deploy pass |

**Scores:** ~55 deploy

---

### Cap 5 — Case Lifecycle Management

| Layer | Items |
|-------|-------|
| **Current** | Reopen, append API, lifecycle derivation |
| **Hidden** | Work now/Waiting split, activity timeline, follow-up editor |
| **Broken** | Multi-turn continuity 41/100 deployed; append undiscoverable |
| **Unused** | — |
| **High-value** | Post-copy bridge + append UX (no new backend) |

**Scores:** **53** deploy (P16-X)

---

### Cap 6 — Trial Conversion

| Layer | Items |
|-------|-------|
| **Current** | Trial scripts, commercial docs, checklists |
| **Hidden** | Observation log (not in UI) |
| **Broken** | Invoice IDs empty; 0 observation rows; Day 0 blocked |
| **Unused** | — |
| **High-value** | Fill invoice + log row 1 + Day 0 supervised (founder ops) |

**Scores:** **51** deploy

---

### Cap 7 — Founder / Operator Control

| Layer | Items |
|-------|-------|
| **Current** | `guardrail_inbox_triage.sh`, `trial_readiness_check.sh`, P16-T runner, health scripts |
| **Hidden** | Full lab script corpus (197 shell files) |
| **Broken** | Preview SSO blocks automated cold checks |
| **Unused** | Many lab batteries (see duplication audit) |
| **High-value** | `trial_launch_check.sh` as single pre-trial entry |

**Scores:** ~65

---

## Cross-capability layers

### Hidden capabilities (implement but trial hides)

```
CustomerEntryTab + MyRequestsTab + Simulation tab
Follow-up editor, case notes, activity timeline
Role C replay UI, Scenario Logic Center, Add Car Rules
Assist layer, debug signals, v4/v5 risk in UI
Inline image OCR on triage (API only)
WeChat live binding (stub default)
```

### Broken capabilities (deploy/trial)

```
Preview cold URL (FP-004 SSO)
Multi-turn UX continuity (engine OK)
English broker_next_step on Chinese office (F-005)
Cap 5/6 below trial threshold on deployed URL
PDF OCR (stub — acceptable if documented)
Role C API 503 without OpenAI key
```

### Unused capabilities (code rot)

```
SimulationAssistant.tsx (zero imports)
getRecentCustomerMessages in workbench (unused import)
inlineImage on triageMessage (no product caller)
audit_export.py (scaffold)
```

### High-value capabilities (revive, don't rebuild)

```
triage_for_append + append-message API
P16-Y rules + run_p16y_case_battery.py
case_draft_engine + conversation_summary
Attachment upload OCR path (with keys)
ScenarioReplayTab (lab only)
Commercial pack + Day 0/7 scripts
P16-T health runner
CONSTITUTION_ENFORCEMENT gate
```

---

## Visual: capability visibility on trial URL

```
                    LOCAL (full UI)          PREVIEW (product_only)
Broker paste        ████████████             ████████░░░░
Append API          ████████████             ████░░░░░░░░  (undiscoverable)
Customer intake     ████████████             ░░░░░░░░░░░░  (tab off)
Case intelligence   ████████████             ████████░░░░  (one-shot gaps)
OCR inline          ████░░░░░░░░             ░░░░░░░░░░░░
Role C sim UI       ████████░░░░             ░░░░░░░░░░░░
Commercial docs     ████████████             ████████████  (process not product)
Observation log     ████████████             ░░░░░░░░░░░░  (not in app)
```

---

## Deploy vs local gap (systemic)

| Capability | Local | Deploy | Primary cause |
|------------|-------|--------|---------------|
| Cap 1 | ~70 | ~45 | Tab surface + SSO + English copy |
| Cap 4 | High | N/A tab | product_only |
| Cap 5 | Medium | 53 | Hidden lifecycle UX |
| Cap 6 | Docs | 51 | Evidence not captured |

**Fix class:** Founder SSO + small UI revival sprint — **not** new platform (P17).

---

## Related documents

| Doc | Use |
|-----|-----|
| `P16Z0_CAPABILITY_INVENTORY.md` | Full table |
| `P16Z0_TOP20_REDISCOVERIES.md` | Forgotten assets |
| `P16Z0_FINAL_VERDICT.md` | Prioritized actions |
| `CAPABILITY_MAP_V1.md` | Original contract scores |

---

*End of P16-Z0 Capability Map v2*
