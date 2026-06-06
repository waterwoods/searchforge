# P16-Z16 Phase 6 — Reuse Map

**Date:** 2026-06-03  
**Sprint:** P16-Z16 Customer Builder Reality Validation  
**Top 20 reusable assets for Customer First → Case Builder → Broker Review**

---

| # | Asset | Location | Maturity | Reuse difficulty | Value |
|---|-------|----------|----------|------------------|-------|
| 1 | **Customer Entry tab (case builder UI)** | `ui/src/features/intake/components/CustomerEntryTab.tsx` | High (Add-Car) | Low — rename/reposition | Primary Customer First surface |
| 2 | **`triageMessage()` API client** | `ui/src/api/inboxTriage.ts` | High | Low | All customer turns |
| 3 | **`save_case()` persistence** | `services/fiqa_api/inbox_triage/case_store.py` | High | None — use as-is | Case creation truth |
| 4 | **Formal submit gate** | `routes/inbox_triage.py` L1417–1510 | High | Low — expose clearer CTA copy | Prevents premature cases |
| 5 | **In-progress session store** | `session_store.py`, `session_repository.py` | Medium–High | Low | Pre-submit return same browser |
| 6 | **`getInProgressSession()` restore** | `CustomerEntryTab.tsx` L439–456 | Medium | Low | Refresh recovery pre-submit |
| 7 | **My Requests / progress panel** | `UserCaseListProgressPanel.tsx` | Medium | Low — wire case_id back | Post-submit status |
| 8 | **`listRecentCasesPage()`** | `inboxTriage.ts` L423–438 | High | None | Customer case discovery |
| 9 | **`filterUserVisibleCases()`** | `UserCaseListProgressPanel.tsx` L63–71 | Medium | Medium — add customer scope later | List hygiene |
| 10 | **`appendFollowUpMessage()`** | `inboxTriage.ts` L510–523 | High | Low — surface in My Requests | Same-case continuity |
| 11 | **`triage_for_append()`** | `triage.py` L3854+ | High | None | Append intelligence |
| 12 | **`append_follow_up_message()`** | `case_store.py` L1098+ | High | None | Thread + field merge |
| 13 | **`case_messages[]` timeline** | `case_store.py` | High | Low — show in customer UI | Continuity proof |
| 14 | **`case_activity[]` audit** | `case_store.py` | High | Low — customer "updates" feed | Trust + transparency |
| 15 | **Broker Workbench** | `BrokerWorkbenchTab.tsx` | High | None — already paired | Broker Review leg |
| 16 | **`AddCarRecordSummaryRail`** | `AddCarRecordSummaryRail.tsx` | High | Low | Structured case builder UX |
| 17 | **`caseLifecycleDisplay` helpers** | `caseLifecycleDisplay.ts` | High | None | Shared customer/broker labels |
| 18 | **Append boundary enforcement** | `triage.py`, append route | High | None | Prevents timeline corruption |
| 19 | **Postgres service record mirror** | `service_record_repository.py` | Medium–High | Config-only | Production persistence |
| 20 | **Light identity / WeChat stub** | `CustomerEntryTab.tsx`, wechat routes | Low–Medium | Medium | Future cross-session link |

---

## Reuse clusters

### Cluster A — Customer Builder (keep, repackage)

`CustomerEntryTab` + `triageMessage` + session restore + formal submit + post-handoff append

**Action:** Rename to Customer First / Case Builder in product copy. Do not fork.

### Cluster B — My Progress (keep, wire)

`UserCaseListProgressPanel` + `listRecentCasesPage`

**Action:** Pass selected `case_id` into Customer Entry; enable append from detail panel. ~1–2 days.

### Cluster C — Broker Review (keep as-is)

`BrokerWorkbenchTab` + case APIs

**Action:** No change. Already consumes same cases.

### Cluster D — Engine (keep as-is)

`triage_conversation`, `triage_for_append`, `save_case`, `append_follow_up_message`

**Action:** No change. Mature.

---

## Do not rebuild

| Temptation | Why reuse instead |
|------------|---------------------|
| New case schema | `CASE_CONTRACT_V1` / `SavedCase` already complete |
| New append API | `POST .../append-message` production-tested |
| New session system | Postgres session store exists |
| Separate customer app | `UnifiedIntakePage` tab model sufficient for MVP |

---

## Highest-value reuse wins (Pareto)

1. Wire My Requests → Customer Entry (`case_id` prop) — unlocks return-later  
2. Persist `lastCaseId` to sessionStorage — unlocks post-submit append after refresh  
3. Rename Customer Entry → **Case Builder** in customer-facing copy — positioning  
4. Unhide customer tabs in trial when demoing Customer First — `productOnlyUi` gate awareness
