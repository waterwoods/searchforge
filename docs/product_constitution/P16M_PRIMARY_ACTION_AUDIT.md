# P16-M Phase 5 — One Primary Action Audit

**Date:** 2026-06-01  
**Rule:** Every page has exactly one primary action. Secondary = supported. Everything else = tertiary/hidden.  
**Flag:** ⚠️ = more than one primary action detected

---

## Page: Broker Workbench — Empty Queue (`product_only`)

| Tier | Action | Control | Notes |
|------|--------|---------|-------|
| **Primary** | Paste + analyze | 开始整理 | ✅ Correct |
| Secondary | Load demo data | 加载演示队列 | ⚠️ Visually competes — same card weight as paste |
| Secondary | Practice scenario | 取消/付款风险 etc. | Tertiary should be link |
| Tertiary | Clear input | 清空 | OK |
| Tertiary | Refresh queue | 刷新列表 | OK |

**Flag:** ⚠️ **Two primaries** — 开始整理 vs 加载演示队列 on first visit (demo card above queue, near paste column)

**Fix (UI only):** Demo → text link under empty textarea only.

---

## Page: Broker Workbench — Case Open (`product_only`)

| Tier | Action | Control | Notes |
|------|--------|---------|-------|
| **Primary** | Copy draft to send | 复制客户草稿 | ✅ Correct |
| Secondary | Append customer message | 追加客户补充 | OK when reopened |
| Secondary | Change status | 状态 dropdown | OK |
| Secondary | New paste (new case) | 开始整理 on paste card | ⚠️ Competes when paste visible + case open |
| Tertiary | Expand detail | 整理明细 collapse | OK |

**Flag:** ⚠️ **Two primaries** when paste card visible alongside open case — 复制客户草稿 vs 开始整理

**Fix:** When case open, collapse paste to "整理新消息" link.

---

## Page: Broker Workbench — Full Dev

| Tier | Action | Control | Notes |
|------|--------|---------|-------|
| **Primary** (intended) | 开始整理 | paste | — |
| **Primary** (competing) | 加载演示队列 | primary button in collapse | ⚠️ |
| **Primary** (competing) | 打开本条服务记录 | on every queue card | ⚠️ N buttons = N primaries |
| Secondary | Filter queue | Segmented | — |
| Secondary | Patch test/archive | 管理 | — |

**Flag:** ⚠️⚠️ **Multiple primaries** — classic admin dashboard failure

---

## Page: Customer Intake — Empty

| Tier | Action | Control | Notes |
|------|--------|---------|-------|
| **Primary** (intended) | Start add-car | 办理加车报价 | — |
| **Primary** (competing) | Talk to human | 联系人工 | ⚠️ Equal visual weight |
| **Primary** (competing) | Structured submit | 用以上内容发起加车报送 | ⚠️ Inside collapse but large |
| Secondary | Other intents | 其他事项 | OK |
| Secondary | Free-text submit | Send in input area | Hidden until turns > 0 |

**Flag:** ⚠️⚠️ **Three primaries** — violates one-action rule badly

**Fix:** One hero button 开始办理; others secondary outline or menu.

---

## Page: Customer Intake — Mid-Flow (collecting)

| Tier | Action | Control | Notes |
|------|--------|---------|-------|
| **Primary** | Submit next message | 提交补充 / 正式提交办公室 | ✅ Lane-dependent |
| Secondary | Change intent | × on tag | OK |
| Secondary | New conversation | 提交新问题 | OK post-handoff |

**Flag:** ✅ Single primary per lane state

---

## Page: Customer Intake — Post-Handoff Result

| Tier | Action | Control | Notes |
|------|--------|---------|-------|
| **Primary** | Wait / read outcome | (read-only) | Implicit |
| Secondary | Append same case | 追加到本条记录 | OK |
| Secondary | New issue | 提交新问题 | OK |
| Secondary | Track requests | 我的办理 | OK |

**Flag:** ⚠️ **Zero explicit primary** — customer may not know if they should wait, append, or leave

**Fix:** One line CTA: 「请等待办公室联系；有补充请点下方追加」

---

## Page: Case Detail (Broker) — Glance + Draft

| Tier | Action | Control | Notes |
|------|--------|---------|-------|
| **Primary** | Copy draft | 复制客户草稿 | ✅ |
| Secondary | Review detail | Expand 整理明细 | OK |
| Secondary | Read source | Expand 原文 | OK |

**Flag:** ✅ Pass when paste card demoted

---

## Page: Global Chrome

| Tier | Action | Control | Notes |
|------|--------|---------|-------|
| **Primary** | (delegates to tab content) | — | — |
| Secondary | Switch tab (dev) | Tab bar | ⚠️ Competes in full UI |
| Tertiary | 显示产品说明 | link | OK |

**Flag:** ⚠️ In full UI, **tab switch is competing primary** with page action

---

## Summary

| Page | Primary (canonical) | Violations | Severity |
|------|-------------------|------------|----------|
| Broker empty trial | 开始整理 | Demo card | Medium |
| Broker case open | 复制客户草稿 | Paste still primary | Medium |
| Broker full dev | 开始整理 | Queue buttons, demo, filters | High |
| Customer empty | 办理加车报价 | 联系人工 + structured CTA | **High** |
| Customer mid-flow | Submit | None | OK |
| Customer post-handoff | (implicit wait) | No explicit CTA | Medium |
| Global full UI | — | Tab bar | High |

**Pages with clean single primary:** 2 / 7  
**Trial broker path after minor fixes:** 4 / 4 achievable without feature work

---

*End of P16-M Primary Action Audit*
