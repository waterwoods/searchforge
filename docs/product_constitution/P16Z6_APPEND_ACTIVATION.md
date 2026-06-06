# P16-Z6 Phase 4 — Append Journey Activation

**Date:** 2026-06-02  
**Journey:** Paste → Copy → Append

---

## Why users left (pre-Z6)

| Step | Drop-off reason |
|------|-----------------|
| Paste | Turn 1 feels complete — broker copies draft |
| Copy | No instruction to return; WeChat is still “source of truth” |
| *(missing)* | Append hidden unless queue reopen (`caseView === 'reopened'`) |
| Exit | Turn 2 pasted as **new case** → duplicate records, lost memory |

---

## Post-copy continuation design (shipped)

After **复制客户草稿** or **复制摘要**:

- Show closable `Alert`: “已复制 — 客户若再发消息 → 请用「追加客户补充」…”
- Hint clears on append success or case switch

Append card visibility:

- **Before:** `caseView === 'reopened' && case_id`  
- **After:** `case_id` (includes first persist in same session when id assigned)

---

## TOP 10 continuity improvements

| # | Improvement | Status |
|---|-------------|--------|
| 1 | Post-copy append hint Alert | **Shipped** |
| 2 | Append visible when `case_id` exists | **Shipped** |
| 3 | Thread visible so broker trusts append | **Shipped** |
| 4 | Engine prior-turn merge on append | **Shipped** (Y44/Y45) |
| 5 | Append simulations in guardrail (5/5) | Pre-existing ✅ |
| 6 | Collapse top paste when case open | Deferred |
| 7 | One-click `waiting_on: client` after copy | Deferred |
| 8 | Default-open activity after append | Deferred |
| 9 | 本轮更新 turn-delta on broker surface | Deferred |
| 10 | Append in `trial_launch_check.sh` | Deferred |

---

## Target loop (North Star)

```
Paste → Case → Timeline → Next Action → Copy → Append → Timeline → Next Action
```

Z6 closes the **Copy → Append** gap in software; founder still must validate on deployed URL with Chen Kui.
