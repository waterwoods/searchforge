# P16-X Phase 4 — Lifecycle Audit

**Date:** 2026-06-01  
**Scope:** Deployed Preview (`product_only`) — full path Message → Close  
**Method:** Live browser + `BrokerWorkbenchTab.tsx` behavior verification  
**URL:** https://ui-waterwoods-andys-projects-1f411b73.vercel.app/workbench/unified-intake

---

## Lifecycle map

```
Message → Triage → Draft → Follow-up → Reopen → Close
  │         │        │         │          │        │
 paste    30s API   copy    append?     queue    kebab
 box      wait     draft   (hidden)    click    状态
```

---

## Step-by-step scoring

| Step | User action | System behavior | Clarity | Continuity | Overall |
|------|-------------|-----------------|---------|------------|---------|
| **1. Message** | Paste into textarea; optional demo scenario buttons | Placeholder clear; brand trust line below fold | 72 | — | **70** |
| **2. Triage** | Click「开始整理」| ~30s; case persisted to Postgres; urgency tag applied | 65 | 60 | **62** |
| **3. Draft** | Read glance; click「复制客户草稿」| Chinese draft usually good; EN broker step leaks | 68 | 45 | **58** |
| **4. Follow-up** | Client replies; paste update | **Append UI only on reopened case**; top paste creates new triage risk | 35 | 30 | **32** |
| **5. Reopen** | Find case in「待处理」; click row | Works; scrolls to detail; disables top「开始整理」| 62 | 70 | **66** |
| **6. Close** | Mark done / archive | Status in kebab「状态」; no close ceremony; no「已结案」UX | 40 | 35 | **38** |

### Weighted lifecycle score

| Step | Weight | Score | Weighted |
|------|--------|-------|----------|
| Message | 10% | 70 | 7.0 |
| Triage | 15% | 62 | 9.3 |
| Draft | 25% | 58 | 14.5 |
| Follow-up | 25% | 32 | 8.0 |
| Reopen | 15% | 66 | 9.9 |
| Close | 10% | 38 | 3.8 |
| **Total** | | | **52.5 → 53** |

**Capability 5 baseline was 55–62; deployed reality: ~53**

---

## Step detail

### Message (70)

**Works:** Single paste box; practice scenario chips load text.  
**Friction:** Demo queue competes above paste;「快速体验（可选）」adds decisions.

### Triage (62)

**Works:** Guardrail PASS; cancellation/missing-doc/add-car scenarios complete on Preview (P16-W).  
**Friction:** 30s wait; loading card easy to miss; no progress % for single paste.

### Draft (58)

**Works:** Three-step glance; copy button;「需您修改后再发」sets expectation.  
**Friction:** Result below fold; duplicate copy buttons; English `broker_next_step`; no post-copy continuation.

### Follow-up (32) — **Weakest link**

**Works:** Backend append + boundary rules (guardrail).  
**Broken in UX:**
- Fresh triage: no「追加客户补充」
- Hint says paste next message in top box — **may fork case**
- User must discover queue → reopen → append

### Reopen (66)

**Works:** Queue lists persisted cases; click loads full record; case ID short form shown.  
**Friction:** English queue previews; duplicate demo rows; no urgency filter chips in product_only.

### Close (38) — **Second weakest**

**Works:** Status API exists (`new`, `in_progress`, `waiting_on_client`, etc.).  
**Broken in UX:** Hidden kebab; no「结案」prompt after copy; no archive confirmation; broker never closes → queue rots.

---

## Lifecycle gap diagram

```
     STRONG                          WEAK
  ┌──────────┐                   ┌──────────┐
  │  Message │ ────────────────► │  Triage  │
  └──────────┘                   └────┬─────┘
                                      │
                                      ▼
  ┌──────────┐                   ┌──────────┐
  │  Reopen  │ ◄── discover ──── │  Draft   │ ── copy ──► WeChat (exit)
  └────┬─────┘      queue        └──────────┘
       │
       ▼
  ┌──────────┐                   ┌──────────┐
  │ Follow-up│ ─── buried ─────► │  Close   │
  └──────────┘                   └──────────┘
       ▲                              ▲
       └──────── user rarely ──────────┘
                  returns
```

---

## Acceptance criteria check (Cap 5 contract)

| Criterion | Met? |
|-----------|------|
| Work now queue same-day first | ⚠️ Queue flat list; no Work now/Waiting split in product_only |
| 下一步 on queue cards | ⚠️ Preview text often English |
| 已收集 / 还缺 on detail | ✅ In glance when expanded |
| Reopen + append same record | ✅ API; ⚠️ UX discoverability |
| Move Work now / Waiting | ❌ Not in product_only UI |
| Simplified filters | ❌ Filters hidden in product_only |

**Contract met:** **3 / 7**

---

*End of P16-X Phase 4 — Lifecycle Audit*
