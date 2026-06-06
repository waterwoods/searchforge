# P16-Z3 Hidden Capability Report

**Date:** 2026-06-01  
**Sprint:** P16-Z3 Case Intelligence Maturity Model Sprint  
**Definition:** Capabilities **already built** but **not visible or discoverable** in the trial product surface.  
**Ranking axes:** ROI (revenue/time impact) × Difficulty to expose (effort to wire, not rebuild).

---

## Executive summary

The repository contains **15+ production-grade capabilities hidden behind env flags, product_only gating, collapsed UI, or missing CTAs**. The highest-ROI hidden items require **zero new backend architecture** — only wiring, copy, and founder ops.

**Top 3 hidden capabilities by ROI ÷ effort:**

1. **Post-copy append bridge** — ROI ★★★★★ / Effort S
2. **Append API + triage_for_append** — ROI ★★★★★ / Effort S (UX only)
3. **Chinese broker_next_step templates** — ROI ★★★★★ / Effort S–M (config + tune)

---

## Hidden capability matrix

| # | Capability | Maturity | Location | Hidden because | ROI | Expose difficulty |
|---|------------|----------|----------|----------------|-----|-------------------|
| 1 | **Append re-triage pipeline** | L5 | `triage_for_append()`, append route | UI only after queue reopen | ★★★★★ | **S** — CTA + copy |
| 2 | **Post-copy continuation** | L5 | Missing UI element | Never designed | ★★★★★ | **S** — 0.5 day UX |
| 3 | **v4/v5 risk scores** | L7 | `case_draft_engine.py` | No renderer | ★★★☆☆ | **S** — badge in glance |
| 4 | **client_prep card** | L4 | BrokerWorkbenchTab | `!productOnlyUi` gate | ★★★★☆ | **S** — ungate or inline |
| 5 | **CustomerEntryTab multi-turn** | L5 | `CustomerEntryTab.tsx` | Tab unmounted trial | ★★★☆☆ | **M** — week 3 route |
| 6 | **MyRequestsTab (我的办理)** | L8/L4 | `MyRequestsTab.tsx` | Tab hidden | ★★★☆☆ | **M** — separate URL |
| 7 | **OCR attachment pipeline** | L6 | `v6_attachment_sidecar.py` | Collapsed upload UI | ★★★☆☆ | **M** — promote + keys |
| 8 | **Inline image triage API** | L6 | routes + inboxTriage.ts | No UI caller | ★★☆☆☆ | **M** — paste image support |
| 9 | **assist_layer suggestions** | L7 | `assist_layer.py` | `ENABLE_ASSIST_LAYER=0` | ★★☆☆☆ | **S** — env toggle + display |
| 10 | **Follow-up editor** | L8 | BrokerWorkbenchTab L2349+ | `!productOnlyUi` | ★★☆☆☆ | **S** — ungate waiting_on |
| 11 | **Full case draft card** | L3 | API `case_draft` field | No UI component trial | ★★☆☆☆ | **M** — glance expansion |
| 12 | **Activity timeline** | L8 | `case_activity` backend | Hidden | ★★☆☆☆ | **M** — timeline component |
| 13 | **ScenarioReplayTab** | L5 (lab) | simulation tab | Unmounted | ★★☆☆☆ | **S** — lab route only |
| 14 | **conversion_layer** | L4 | `conversion_layer.py` | Customer tab hidden | ★★★☆☆ | **M** — with Cap 4 |
| 15 | **truth_field_guardrails debug** | L7 | `truth_field_guardrails.py` | DEBUG env | ★☆☆☆☆ | **S** — founder debug |
| 16 | **Role C simulation** | Lab | `role_c_simulation_service.py` | Sim tab hidden | ★☆☆☆☆ | **S** — lab only |
| 17 | **learning_signals JSONL** | L9 | `learning_signals.py` | No HTTP | ★☆☆☆☆ | **L** — feedback loop |
| 18 | **workbench_enrichment tags** | L8 | `workbench_enrichment.py` | Dev UI only | ★☆☆☆☆ | **S** — optional expose |
| 19 | **add_car_llm_slot_candidates** | L2 | env-gated | `ADD_CAR_LLM_SLOT_EXTRACTION` | ★★☆☆☆ | **M** — verify + enable |
| 20 | **Case boundary copy pools** | L5 | `append_case_boundary_copy.py` | Backend-only output | ★★★☆☆ | **S** — already in replies |

---

## ROI-ranked top 10 hidden capabilities

### 1. Post-copy append bridge (L5)

| | |
|---|---|
| **What exists** | Full append backend; missing CTA after copy |
| **Why hidden** | UX never designed for Turn 2 |
| **ROI** | Fixes continuity 41→70+; answers "why reopen webpage?" |
| **Difficulty** | **S** — copy + button, 0.5 day |
| **Action** | Add「客户回复了？追加到此案件」after copy |

### 2. Append API + triage_for_append (L5)

| | |
|---|---|
| **What exists** | `POST append-message`, boundary enforcement, re-triage |
| **Why hidden** | Append card only on `caseView === 'reopened'` |
| **ROI** | Multi-turn retention = payment retention |
| **Difficulty** | **S** — promote append box; link from post-copy CTA |
| **Action** | Wire existing `appendCaseMessage()` prominently |

### 3. Chinese broker_next_step templates (L4)

| | |
|---|---|
| **What exists** | Template system in `ui_copy.json`; generic fallbacks still fire |
| **Why hidden** | Copy not tuned/deployed for Chen Kui lanes |
| **ROI** | Office Actionability is rubric-perfect but Chen Kui wants specificity |
| **Difficulty** | **S–M** — config + blocklist, 1 day |
| **Action** | Cancel/payment/add-car templates; generic blocklist |

### 4. client_prep in broker glance (L4)

| | |
|---|---|
| **What exists** | Generated every triage; card gated off trial |
| **Why hidden** | `!productOnlyUi` |
| **ROI** | Broker sees what customer should send — reduces back-and-forth |
| **Difficulty** | **S** — ungate or one-line in glance |
| **Action** | Show「客户可准备」in productOnlyUi |

### 5. P16-Y append summary merge (L3/L5)

| | |
|---|---|
| **What exists** | Partial summary builder; merge logic not complete |
| **Why hidden** | Engine gap, not UX — but effect is hidden intelligence |
| **ROI** | Y44 correction case; multi-turn trust |
| **Difficulty** | **M** — 1–2 days engine tune (NOT new service) |
| **Action** | Inject prior `[客户]` bubbles into summary |

### 6. v4 risk as「需核实」badge (L7)

| | |
|---|---|
| **What exists** | Score computed; typed in TS |
| **Why hidden** | Never rendered |
| **ROI** | Broker knows when not to auto-trust extraction |
| **Difficulty** | **S** — conditional badge, 0.5 day |
| **Action** | Show when v4_error_risk_score > threshold |

### 7. OCR attachment upload (L6)

| | |
|---|---|
| **What exists** | Full sidecar pipeline; collapsed UI |
| **Why hidden** | Buried in「整理明细」; no Vision keys on pilot |
| **ROI** | Screenshot cancel notices — second wedge |
| **Difficulty** | **M** — promote UI + ops keys, 1 day |
| **Action** | Week 2 wire; tag fields [OCR] in glance |

### 8. waiting_on pill + follow-up editor (L8)

| | |
|---|---|
| **What exists** | Fields on case; editor in dev UI |
| **Why hidden** | product_only hides editor |
| **ROI** | Office knows who waits — reduces mental load |
| **Difficulty** | **S** — pill in glance; optional editor |
| **Action** | Show waiting_on after copy action |

### 9. CustomerEntryTab (L5/L4)

| | |
|---|---|
| **What exists** | Full multi-turn customer intake |
| **Why hidden** | Tab unmounted on trial URL |
| **ROI** | Cap 4 — week 3 if broker requests |
| **Difficulty** | **M** — separate route, 1–2 days |
| **Action** | Defer to week 3 unless Chen Kui asks |

### 10. ScenarioReplayTab (Lab)

| | |
|---|---|
| **What exists** | Multi-turn replay for rehearsal |
| **Why hidden** | Simulation tab unmounted |
| **ROI** | Founder/Andy rehearsal — not Chen Kui revenue |
| **Difficulty** | **S** — lab route |
| **Action** | Keep for founder; not trial surface |

---

## Difficulty legend

| Code | Meaning | Typical effort |
|------|---------|----------------|
| **S** | Wire, ungate, copy, env toggle | <0.5 day |
| **M** | UI component + config + test | 0.5–2 days |
| **L** | New product loop or integration | 3+ days — defer |

---

## What is NOT hidden (already visible)

Do not mistake these for hidden — they are deployed:

- Paste box + 开始整理
- Queue with case cards
- broker_next_step preview on cards
- Copy-to-WeChat / copy draft
- collected_fields / still_needed in glance
- case_lifecycle tags (partial)
- Case status tags (partial)

---

## Anti-revival list (hidden but low ROI)

| Capability | Why not expose now |
|------------|-------------------|
| `audit_export.py` | Stub; no compliance claim |
| `learning_signals.py` | No feedback UI |
| `add_car_llm_slot_candidates` | Rules sufficient at 88.6 |
| Inline image API | Attachment path simpler |
| SimulationAssistant | Orphaned — delete, don't expose |
| Full activity timeline | Week 3+ polish |

---

## 2×2 matrix: ROI vs difficulty

```
High ROI
    │
    │  [Post-copy CTA]  [Append promote]     [Summary merge]
    │  [CN templates]   [client_prep]        [OCR wire]
    │
    │  [Risk badge]     [waiting_on pill]
    │
    │  [ScenarioReplay] [audit_export]     [Customer tab]
    │
Low ROI ──────────────────────────────────────────────→
         Easy (S)                              Hard (L)
                              Difficulty
```

**Quadrant to execute:** Upper-left — high ROI, easy expose.

---

*End of P16-Z3 Hidden Capability Report*
