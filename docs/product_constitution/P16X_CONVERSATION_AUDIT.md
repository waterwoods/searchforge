# P16-X Phase 5 — Conversation Continuity Audit

**Date:** 2026-06-01  
**Question:** Can the user naturally continue? Can the system ask for missing info? What breaks?  
**Method:** Deployed Preview E2E + append/reopen code path review  
**URL:** https://ui-waterwoods-andys-projects-1f411b73.vercel.app/workbench/unified-intake

---

## Executive summary

**The product completes one conversational turn well. Multi-turn continuity fails at the UI layer** even though the backend supports append, session IDs, and boundary detection.

| Question | Answer |
|----------|--------|
| Can user naturally continue? | **No** — after copy, default exit is WeChat |
| Can system ask for missing info? | **Partially** — one-shot「还缺什么」in glance; no interactive back-and-forth |
| What breaks? | Follow-up entry, case identity across sessions, close loop |

**Continuity score:** **41 / 100**

---

## Turn 1 → Turn 2 (broker path)

### Expected office-assistant behavior

```
Client message → draft → send → client reply → update same case → new draft
```

### Deployed behavior

```
Client message → draft → copy → [user leaves]
                                    ↓
              optional: new paste in top box → NEW triage (risk duplicate case)
                                    ↓
              OR: queue → reopen → append box → updated draft ✅ (undiscoverable)
```

**Break point:** No UI bridges Turn 1 exit (WeChat) to Turn 2 entry (append).

---

## Turn 1 → Turn 2 (customer path)

**Not testable on Preview** — customer tab hidden (`product_only`).  
From P16-N journey map + local code: customer can「提交补充」mid-flow, but **post-handoff** offers append collapse + dual CTAs — overload without clear「reply here when office asks.」

**Customer continuity on deployed URL:** **N/A (0 weight for trial URL)**

---

## Can the system ask for missing information?

| Mechanism | Present? | Natural? |
|-----------|----------|----------|
| Glance「还缺什么（首要）」| ✅ | One-shot; no input field tied to gap |
| `client_prep` in draft | ✅ | Embedded in reply text |
| Interactive「请补充 ZIP」prompt | ❌ | No chat turn from system after submit |
| Customer 提交补充 loop | ⚠️ Hidden tab | Not on Preview |
| OCR / image ask | ❌ Broker paste text-only on Preview | |
| Boundary hint on wrong append | ✅ Backend | Collapsed under tags |

**Verdict:** System **declares** gaps in the first result. It does **not** **conduct** a conversation to fill them. Feels like a **report generator**, not a **dialogue partner**.

---

## Continuity break catalog

| # | Break | Who hits it | Severity |
|---|-------|-------------|----------|
| 1 | No post-copy「when customer replies…」| Broker, assistant | **P0** |
| 2 | Append only on `caseView === reopened` | Everyone | **P0** |
| 3 | Top paste after triage ambiguous (new vs same) | Assistant | **P0** |
| 4 | No「waiting on client」prominent state | Broker | P1 |
| 5 | English broker action breaks reading flow | Chen Kui | P1 |
| 6 | No notification / reminder to return | Broker | P1 |
| 7 | Session ID invisible — cannot resume on new device | Broker | P2 |
| 8 | Customer portal absent on trial URL | End customer | P2 (deferred) |
| 9 | Activity thread collapsed | Assistant | P2 |
| 10 | Duplicate demo queue rows erode trust in「same case」| Cold user | P2 |

---

## Natural continuation test (live)

| Test | Result |
|------|--------|
| Paste cancellation → get draft | ✅ |
| Copy draft without reopen | ✅ |
| Paste client follow-up in top box immediately | ⚠️ Creates new triage path (not tested to DB, but UI allows) |
| Find append without training | ❌ Not visible on fresh case |
| Reopen from queue → append | ✅ UI present |
| Mark case waiting on client | ⚠️ Possible via kebab only |

---

## What "natural" would look like (evaluation only — not a feature proposal)

Reference pattern: after Turn 1, user sees **one sentence** tying case ID, sent state, and **exactly where to paste the reply**. Current product shows **three collapses and a second paste box with conflicting copy**.

---

*End of P16-X Phase 5 — Conversation Continuity Audit*
