# P16-Z6 Phase 1 — Memory Visibility Audit

**Date:** 2026-06-02  
**Sprint:** P16-Z6 Case Memory Activation  
**Sources:** `case_store.py`, `service_record_repository.py`, `triage.py`, `BrokerWorkbenchTab.tsx`, `intakePure.ts`, P16-Z3/Z4/Z5 archaeology

---

## Investigation summary

| Asset | Storage | API | Broker UI (pre-Z6) | Broker UI (post-Z6) |
|-------|---------|-----|-------------------|---------------------|
| `case_messages[]` | ✅ Sequenced roles | ✅ GET case | ❌ Collapsed `source_text` only | ✅ **对话记录** card (last 5) |
| `case_activity[]` | ✅ Typed audit | ✅ | ⚠️ Inside 整理明细 collapse | ⚠️ Unchanged (still collapsed) |
| `conversation_summary` | ✅ Per triage | ✅ | ⚠️ Partial chips below fold | ✅ Visible via glance + summary |
| `latest_update` | ✅ Notes vs activity | — | ⚠️ Queue only when no due tag | ✅ Queue `最近：` line |
| `tracking_summary` | ✅ `getCaseTrackingSummary()` | — | ✅ Queue partial | ✅ Unchanged |
| `getRecentCustomerMessages()` | ✅ Helper | — | ❌ Imported, unused | ✅ Used in `buildOfficeWorkbenchGlance` + thread |
| `getLatestUpdateForDisplay()` | ✅ Helper | — | ⚠️ Reopened banner only | ✅ Queue subtitle |
| `source_text` | ✅ Rebuilt from messages | ✅ | ⚠️ 80-char preview | ✅ Thread card preferred |
| `collected_fields` / `still_needed_fields` | ✅ | ✅ | ✅ Chips in collapse | ✅ Unchanged |
| `follow_up_type: correction` | ✅ Engine | ✅ | ⚠️ Badge in 整理明细 | ✅ Unchanged |
| `append_follow_up_message()` | ✅ API | ✅ | ❌ `caseView === 'reopened'` only | ✅ **`case_id` present** |
| `learning_signals.jsonl` | ✅ Append-only | — | ❌ No surface | ❌ Deferred |
| Postgres `record_messages` | ✅ Mirror | ✅ | ❌ Tag only | ❌ Deferred |

---

## What memory existed but was hidden?

1. Full `case_messages` thread — stored, never hero-rendered  
2. `getRecentCustomerMessages` — dead import in workbench  
3. Append UI — gated on reopen, not first persist  
4. Post-copy path — no continuation hint → spell-checker exit  
5. Prior-turn facts in `conversation_summary` — Y44/Y45 dropped on correction (engine)  
6. `bill_sent_claimed` — premium thread field missing (Y45)  
7. Activity audit — default-collapsed in product_only  
8. System bubbles in `case_messages` — never shown  
9. Turn delta (`buildAddCarRailTurnModel`) — customer add-car only  
10. `formal_submitted_at` vs `updated_at` — no glance comparison line  

---

## TOP 20 hidden memory assets

| # | Asset | Why hidden | Revival (Z6) |
|---|-------|------------|--------------|
| 1 | `case_messages[]` full thread | UI never mapped array to timeline | **Shipped** — `formatCaseMessagesForThread` |
| 2 | `getRecentCustomerMessages()` | Import unused in workbench | Wired via glance (existing) + thread |
| 3 | `getLatestUpdateForDisplay()` | Only on reopened banner | Queue `最近：` (existing) |
| 4 | `getCaseTrackingSummary()` | Partial queue use | Unchanged — already wired |
| 5 | `append_follow_up_message()` | UX gated on reopen | **Shipped** — `case_id` gate |
| 6 | `conversation_summary` merge | Y44/Y45 engine gap | **Shipped** — prior-turn prepend |
| 7 | `bill_sent_claimed` | Not in renewal extract | **Shipped** — `_extract_renewal_fields` |
| 8 | `_thread_is_premium_review_lane()` | Did not exist | **Shipped** — blocks add-car misroute |
| 9 | `follow_up_type: correction` | Below fold | Pre-existing badge |
| 10 | `case_activity[]` | Collapsed 操作记录 | Deferred (scope) |
| 11 | `buildAddCarRailTurnModel()` | Customer rail only | Deferred (scope) |
| 12 | `secondary_issue_note` | Below fold | Deferred |
| 13 | System messages in thread | Not rendered | **Shipped** — included in thread card |
| 14 | `learning_signals.jsonl` | No product loop | Deferred |
| 15 | `formal_submitted_at` line | Not in glance | Deferred |
| 16 | `v6_ocr_signals` | Hidden | Deferred |
| 17 | `case_attachments` timeline link | Separate card | Deferred |
| 18 | Postgres `state_history` | PG tag only | Deferred |
| 19 | `session_store` | Dev path | Deferred |
| 20 | Default-open activity after append | Layout default | Deferred |

---

## Core question (Phase 1)

**Can a broker understand the case without reopening WeChat?**

**Before Z6:** No for Turn 2+ — thread and prior intent not visible; corrections dropped summary context.  
**After Z6 (partial):** Turn 1 + persisted cases improve — thread card + engine merge; activity delta and add-car rail still deferred.
