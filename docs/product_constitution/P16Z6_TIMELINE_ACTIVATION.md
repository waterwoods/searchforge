# P16-Z6 Phase 2 — Timeline Activation Design

**Date:** 2026-06-02  
**Borrow:** Zendesk event timeline + Intercom conversation history (**workflow only**, not visuals)

---

## Design principles

1. **Chronological customer + system bubbles** — answer “what did they say?”  
2. **Latest office change above fold** — answer “what changed since I last opened this?”  
3. **Append is the continuity action** — paste → copy → **append**, not paste → copy → exit  
4. **No new services** — render existing `case_messages`, `case_activity`, helpers  

---

## Minimal timeline inside broker workflow

```
┌─ 整理结果 (glance + next action + draft) ─────────────┐
│  OfficeWorkbenchOneGlanceSummary                       │
├─ 对话记录 (NEW — last 5 case_messages) ────────────────┤
│  客户 · 续保费太高                                       │
│  客户 · 我发你账单了…                                    │
├─ 追加客户补充 (when case_id) ──────────────────────────┤
│  TextArea + 追加客户补充                                  │
├─ Post-copy hint (after copy) ──────────────────────────┤
│  “客户若再发消息 → 追加客户补充”                          │
└─ 完整对话（备查）collapse — source_text fallback ────────┘
```

Queue row (unchanged pattern, reinforced):

- `最近：{getLatestUpdateForDisplay}` OR follow-up due tag + `getCaseTrackingSummary`

---

## TOP 10 timeline changes (Z6 scope)

| # | Change | Status |
|---|--------|--------|
| 1 | Render `case_messages` as labeled thread in detail | **Shipped** |
| 2 | Show append when `case_id` exists (not only reopened) | **Shipped** |
| 3 | Post-copy continuation Alert → append path | **Shipped** |
| 4 | Queue `getLatestUpdateForDisplay` on every card | Pre-existing — verified |
| 5 | Prior-turn line in `conversation_summary` (engine) | **Shipped** |
| 6 | Premium lane guard — stop add-car summary on renewal thread | **Shipped** |
| 7 | Default-open 操作记录 after append | Deferred |
| 8 | Generalize 本轮更新 turn-delta from add-car rail | Deferred |
| 9 | Link attachments inline in thread | Deferred |
| 10 | Deadline countdown widget | Deferred |

---

## Zendesk / Intercom workflow mapping

| Their workflow | Our activation |
|----------------|----------------|
| Ticket comments chronological | `case_messages` thread card |
| Internal note vs public reply | `role: system` vs `customer` labels |
| “Last updated” on queue | `getLatestUpdateForDisplay` |
| Agent sees what changed | `Prior turn:` in summary + append hint |
| Customer replied → agent continues same ticket | Append on same `case_id` |
