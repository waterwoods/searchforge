# P16-Z4 Phase 3 — Append UX Review

**Date:** 2026-06-02  
**Sprint:** P16-Z4 Case Continuity Sprint  
**Sources:** P16-X, P16-M, P16-O, `BrokerWorkbenchTab.tsx`, `CustomerEntryTab.tsx`, P16Z0 archaeology

---

## Core question

**Why do users not return after copy?**

The product completes the user's mental job at Turn 1 (draft ready → copy → WeChat). Turn 2 requires **queue literacy**, **reopen**, and **append discoverability** — none of which are taught at the exit moment.

---

## Current append paths

| Path | Who | Trigger | Friction |
|------|-----|---------|----------|
| Broker paste → persist → reopen case → append box | Chen Kui / assistant | Manual queue click | High — 3 steps |
| Broker fresh triage with `case_id` but `caseView !== reopened` | Same | Append may be hidden | **Critical** (P16-X #2) |
| Customer post-handoff 追加到本条记录 | End customer | Collapsed link | Hidden on trial; low discovery |
| Top paste again | Broker | Default hero | **Creates duplicate case** risk |
| `conversation_turns` pre-persist | Dev / customer chat | Before save | Not broker trial path |

---

## P16-X findings (lifecycle)

| Finding | Mechanism |
|---------|-----------|
| Exit point is copy | Primary CTA = job done |
| Paste box stays hero | Says “next message here” not “append to this case” |
| Append gated on reopen | `caseView === 'reopened'` pattern |
| No waiting state | Nothing says 现在在等客户 |
| WeChat is channel of record | Product = sidecar |
| No return trigger | No in-app signal |

**Metaphor:** Spell-checker popup — useful once, dismissed forever.

---

## P16-M findings (UI noise)

| # | Relevant improvement | Impact on append |
|---|---------------------|------------------|
| 11 | Collapse paste when case open | Reduces fork-case |
| 19 | Disable 开始整理 when case open | Prevents duplicate |
| 28 | Promote append in glance when reopened | Direct fix |
| 2 | Demote 快速体验 | Reduces Turn-1 distraction |
| 16 | Empty state 3-step bullets | Could include append step |

---

## P16-O findings (customer post-submit)

| Before | After |
|--------|-------|
| 18–24 UI objects | 8–10 objects |
| Dual primaries | 查看办理进度 + 提交新问题 |
| Append visible | **Collapsed** under 有补充？ |

**Effect:** Customer Turn-2 path exists in code but **feels optional and buried**. Broker path worse — no post-copy bridge at all.

---

## Append backend vs UX matrix

| Dimension | Backend | UX |
|-----------|---------|-----|
| API reliability | ✅ | — |
| Boundary enforcement | ✅ | ⚠️ Error copy only on block |
| Summary refresh on append | ⚠️ Y44 | ❌ User doesn't see thread |
| Discoverability | — | ❌ |
| Habit formation at copy | — | ❌ |

---

## TOP 10 reasons Turn-2 fails

| # | Reason | Evidence | Fix class |
|---|--------|----------|-----------|
| 1 | **Copy = exit** — no second beat taught | P16-X F-001 | Post-copy one-liner |
| 2 | **Append hidden until queue reopen** | P16-X #2, BrokerWorkbench | Show append when `case_id` exists |
| 3 | **Top paste invites new case** | P16-X F-004, P16-M #11 | Collapse paste / disable 开始整理 |
| 4 | **WeChat is the real thread** | P16-X role sim | Position product as “office record” not chat |
| 5 | **No waiting_on set after send** | P16-X F-008 | Prompt 改为等客户 |
| 6 | **Queue not Monday habit** | Chen Kui 47/100 | Chinese 下一步 on row only |
| 7 | **Customer append collapsed** | P16-O | Broker path matters more for pilot |
| 8 | **Summary doesn't show “what changed”** | Y44 | Engine merge + activity default-open |
| 9 | **Requires_new_case feels like failure** | Boundary UX | Clear 开新案 CTA when blocked |
| 10 | **No logged two-turn trial proof** | P16-X GO/NO-GO | Founder ritual + observation log |

---

## Smallest append fix stack (ordered)

```
1. Copy-adjacent continuation sentence     (~15 min)
2. Append card when case_id set            (~2 hr)
3. Collapse top paste when case open       (~0.5 day)
4. conversation_summary merge (Y44)        (1–2 days engine)
```

---

*End of P16-Z4 Phase 3*
