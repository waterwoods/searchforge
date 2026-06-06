# P16-Z18 Top 20 Reusable Assets

**Date:** 2026-06-03  
**Sprint:** P16-Z18 Product Constitution Refresh  
**Method:** ROI ranking from P16-Z16 reuse map · P16-Z9 · P16-Z5/Z6/Z10 · P16-Z17 proof  
**Rule:** Reuse beats rebuild. Rank = (pilot impact × evidence maturity) ÷ (effort + regression risk)

---

## Ranked list

| Rank | Asset | Location | ROI | Why |
|------|-------|----------|-----|-----|
| **1** | **CustomerEntryTab** | `ui/.../CustomerEntryTab.tsx` | ★★★★★ | Primary Customer First surface — ~76% complete, live proof |
| **2** | **save_case()** | `case_store.py` | ★★★★★ | Case creation truth — formal submit → real `case_id` |
| **3** | **triage.py** (48 modules) | `inbox_triage/triage.py` | ★★★★★ | Complete AI draft engine — P16-Y 88.6, no microservice |
| **4** | **appendFollowUpMessage()** | `ui/src/api/inboxTriage.ts` | ★★★★★ | Customer + broker append client — same API |
| **5** | **triage_for_append()** | `triage.py` L3854+ | ★★★★★ | Multi-turn merge intelligence — production-grade |
| **6** | **append_follow_up_message()** | `case_store.py` L1098+ | ★★★★★ | Thread + field merge persistence |
| **7** | **BrokerWorkbenchTab** | `ui/.../BrokerWorkbenchTab.tsx` | ★★★★☆ | Broker confirm layer — 88/100, unchanged |
| **8** | **UserCaseListProgressPanel / MyRequests** | `UserCaseListProgressPanel.tsx` | ★★★★☆ | Post-submit discovery — wire `case_id` back (0.5d unlock) |
| **9** | **case_messages[]** | `case_store.py` | ★★★★☆ | Timeline truth — seq 1–11 proven on live case |
| **10** | **case_activity[]** | `case_store.py` | ★★★★☆ | Audit trail — create + append events |
| **11** | **Role D battery** | `scripts/run_role_d_memory_battery.py` | ★★★★☆ | Multi-day proof gate — reread 82.6, need WeChat 0/10 |
| **12** | **P16-Y battery** | `scripts/run_p16y_case_battery.py` | ★★★★☆ | Single-turn regression — 88.6 avg |
| **13** | **session_store + getInProgressSession** | `session_store.py`, CustomerEntryTab | ★★★★☆ | Pre-submit return — proven 2 turns |
| **14** | **_merge_persisted_collected** | `triage.py` (Z10A) | ★★★★☆ | Generic field merge on append |
| **15** | **buildAddCarRailTurnModel()** | `AddCarRecordSummaryRail.tsx` | ★★★☆☆ | Best turn-delta UI — generalize to broker/customer |
| **16** | **_apply_office_value_surface()** | `triage.py` (Z11) | ★★★☆☆ | 5-second Chen Kui glance — payment/remove/claim |
| **17** | **_suggest_waiting_on()** | `triage.py` (Z10B) | ★★★☆☆ | 9/9 auto-detect — broker confirms PATCH |
| **18** | **caseLifecycleDisplay** | `caseLifecycleDisplay.ts` | ★★★☆☆ | Shared customer/broker labels — fix submitted resume |
| **19** | **guardrail_inbox_triage.sh** | `scripts/operator/` | ★★★☆☆ | Pre-ship gate — must stay green |
| **20** | **trial_launch_check.sh** | `scripts/` | ★★★☆☆ | Pre-trial single entry — deploy + batteries |

---

## Required assets (user mandate — cross-reference)

| Asset | Rank | Notes |
|-------|------|-------|
| CustomerEntryTab | #1 | Case Builder UI |
| MyRequests | #8 | My Requests tab + progress panel |
| appendFollowUpMessage | #4 | Client API |
| save_case | #2 | Persistence |
| triage_for_append | #5 | Append engine |
| BrokerWorkbench | #7 | Broker review |
| Role D | #11 | Validation battery |
| P16-Y | #12 | Single-turn battery |
| case_messages | #9 | Timeline |
| case_activity | #10 | Audit |

---

## Honorable mentions (21–30, reuse don't rebuild)

| Asset | Location | Value |
|-------|----------|-------|
| `triageMessage()` | `inboxTriage.ts` | All customer turns |
| `case_draft_engine.py` | `inbox_triage/` | Draft + risk v4/v5 |
| `getRecentCustomerMessages()` | `intakePure.ts` | Wire in glance (2 hr, Z5) |
| `getLatestUpdateForDisplay()` | `intakePure.ts` | Queue subtitle |
| `_prepend_prior_customer_turn_on_correction` | `triage.py` (Z6) | Y44/Y45 fix |
| Formal submit gate | `routes/inbox_triage.py` L1417+ | Prevents bad cases |
| Append boundary tests | `tests/` + append sims | Regression gate |
| `ScenarioReplayTab` | UI lab | Role D dev — not customer product |
| `service_record_repository.py` | Postgres mirror | Prod persistence |
| `OfficeWorkbenchOneGlanceSummary` | UI (Z11) | Office value layout |

---

## Reuse clusters (action map)

### Cluster A — Close customer loop (P0, ~3 days)

`CustomerEntryTab` + My Requests handoff + `sessionStorage` active `case_id` + `appendFollowUpMessage`

**Unlocks:** Return Later → Append without new code.

### Cluster B — Deploy proof (P0, ops)

`triage.py` (Z11 surface) + `guardrail` + `trial_launch_check` + Cloud Run secrets

**Unlocks:** Chen Kui cold URL.

### Cluster C — Broker path (already shipped, deploy)

`BrokerWorkbenchTab` + Z6 thread + Z10B waiting suggest + post-copy append hint

**Unlocks:** Broker wedge Day 0.

### Cluster D — Validation (ongoing)

P16-Y + Role D + observation log

**Unlocks:** Commercial evidence.

---

## Do not duplicate

| Temptation | Use rank # instead |
|------------|-------------------|
| New Customer Builder app | #1 CustomerEntryTab |
| New case API service | #2 save_case |
| New append microservice | #5, #6 |
| New timeline DB | #9, #10 |
| New validation framework | #11, #12 |

---

## ROI formula used

```
ROI = (pilot_impact × maturity) / (effort_days × regression_risk)
```

**Top 3 by ROI × urgency:**  
1. Wire My Requests → CustomerEntryTab (#1 + #8) — 0.5–1.5d, unlocks entire north star return path  
2. Deploy backend with Z11 markers (#3 + #16) — ops, unlocks Chen Kui test  
3. Persist active case_id (#1 + sessionStorage) — 1d, fixes refresh

---

*End of P16-Z18 Phase 7 — Top 20 Reusable Assets*
