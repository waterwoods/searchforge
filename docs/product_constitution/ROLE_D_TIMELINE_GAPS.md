# P16-Z7 Phase 4 — Timeline Validation

**Date:** 2026-06-02  
**Assets reviewed:** `case_messages`, `case_activity`, thread render (`formatCaseMessagesForThread`), `BrokerWorkbenchTab.tsx`  
**Sources:** P16-Z5/Z6 visibility audits, codebase inspection, Role D battery

---

## What exists today (backend + UI)

| Asset | Stored | API | Broker UI (post-Z6) | Gap severity |
|-------|--------|-----|---------------------|--------------|
| `case_messages[]` | ✅ Sequenced roles | ✅ GET case | ✅ **对话记录** last 5 | Medium — not full thread |
| `case_activity[]` | ✅ Typed audit | ✅ GET case | ⚠️ Collapsed 操作记录 | High — append invisible |
| `source_text` | ✅ Rebuilt | ✅ | ⚠️ 80-char preview only | Medium |
| `conversation_summary` | ✅ | ✅ | ✅ Glance | Low if merge correct |
| `waiting_on` / `next_contact_by` | ✅ PATCH | ✅ | ⚠️ Follow-up editor | High — not auto-inferred |
| Day labels (Day 1/2/3) | ❌ | ❌ | ❌ | **High** — no calendar semantics |
| Attachment/OCR in thread | ✅ `v6_ocr_signals` | ✅ | ❌ | High for claims |
| Turn delta (correction banner) | ✅ engine | — | ❌ broker (add-car rail only) | High |
| Broker vs customer label | ✅ | ✅ | ✅ 客户/系统 | Low |
| System bubbles | ✅ in store | ✅ | ❌ not rendered | Medium |

---

## Thread render review

**Helper:** `formatCaseMessagesForThread` in `intakePure.ts`

| Behavior | Status | Gap |
|----------|--------|-----|
| Uses `case_messages` when present | ✅ | — |
| Falls back to `source_text` `[客户]` parse | ✅ | — |
| Max 5 messages | ✅ by design | **Older Day 1 facts drop** on 6+ turn cases |
| Newest last ordering | ✅ | — |
| No date/day stamp per bubble | ❌ | Broker cannot see **which day** client wrote |
| No “append” vs “initial paste” marker | ❌ | Activity log has it; thread does not |

**Z6 shipped** append CTA copy: 「追加客户补充」— timeline **storage** works; **temporal story** still weak.

---

## case_activity review

| activity_type (examples) | Written on | Visible to broker? |
|--------------------------|------------|-------------------|
| `follow_up_added` | PATCH waiting_on | ⚠️ Banner hint only |
| `message_appended` | append API | ❌ Default collapsed |
| `status_changed` | lifecycle | ❌ Collapsed |
| `note_added` | broker note | ✅ Separate card |

**Gap:** After Day 2 append, broker must expand **操作记录** to see *that* something changed — glance does not show turn delta.

---

## Information still missing for 3-day memory

### Must-have (blocks Chen Kui 3-day case)

| # | Missing | Why it matters |
|---|---------|----------------|
| 1 | **Per-message timestamp in thread UI** | “Day 3 ping” vs “Day 1 crisis” looks identical |
| 2 | **Turn delta block on broker workbench** | Exists on add-car customer rail only |
| 3 | **waiting_on auto-suggestion** | “carrier还没回复” should set `waiting_on: carrier` |
| 4 | **Collected field merge on all append paths** | Role D D03/D10 lose zip, payment facts |
| 5 | **Lane-stable summary on remove-car / payment** | D07/D10 timeline tells wrong story |

### Should-have (pilot polish)

| # | Missing |
|---|---------|
| 6 | Full thread (>5) expander |
| 7 | System/OCR bubbles in 对话记录 |
| 8 | Activity default-open after append |
| 9 | Queue row: “waiting 2 days on carrier” |
| 10 | Photo reference without reopening WeChat images |

### Nice-to-have (post-pilot)

| # | Missing |
|---|---------|
| 11 | Calendar integration from `next_contact_by` |
| 12 | Customer-facing day progress on 查看办理进度 |
| 13 | learning_signals surfaced as “correction memory” |

---

## Timeline vs North Star pipeline

```
Customer Message → Understanding → Case → Timeline → Next Action → Follow-up → Outcome
                                      ↑
                              **Weakest link @ Day 3**
```

**Engine:** Timeline data **exists** in `case_messages` + `case_activity`.  
**Product:** Timeline **story** (time, responsibility, delta) still incomplete in broker glance.

---

## Phase 4 verdict

| Question | Answer |
|----------|--------|
| Is `case_messages` sufficient for memory? | **Yes** for storage |
| Is thread render sufficient? | **Partial** — fixes ~60% re-read pain, not lane/field gaps |
| Is `case_activity` sufficient? | **Yes** for audit; **no** for daily broker workflow |
| Biggest timeline gap? | **No day/time + no turn delta + waiting_on manual** |
