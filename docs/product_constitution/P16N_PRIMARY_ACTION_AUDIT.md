# P16-N Phase 3 — Primary Action Audit

**Date:** 2026-06-01  
**Rule:** Every customer page has exactly one primary action. Secondary = supported. Everything else = tertiary or hidden.  
**Flag:** ⚠️ = more than one primary action detected  
**Scope:** Customer surfaces only (`CustomerEntryTab`, `UserCaseListProgressPanel`, customer-visible chrome)

---

## Page: Global Chrome (Customer in Full Dev UI)

| Tier | Action | Control | Notes |
|------|--------|---------|-------|
| **Primary** (intended) | Start intake | 客户报送 tab content | Delegated |
| **Primary** (competing) | Broker workbench | 办公室工作台 tab | ⚠️ Same visual weight |
| Secondary | View my requests | 我的办理 tab | OK |
| Tertiary | Simulation | 场景仿真 tab | Should not exist for customers |

**Flag:** ⚠️ **Tab bar creates competing primaries** — customer may land wrong tab

**Fix:** Separate customer URL; hide broker/simulation tabs from customer links

---

## Page: Landing / Empty State

| Tier | Action | Control | Notes |
|------|--------|---------|-------|
| **Primary** (intended) | Start add-car | 办理加车报价 | Largest blue button |
| **Primary** (competing) | Talk to human | 联系人工 | ⚠️ Equal size, same row |
| **Primary** (competing) | Structured add-car | 用以上内容发起加车报送 | ⚠️ Inside collapse; still visible label + fields |
| **Primary** (competing) | Free-text submit | 提交报送 (textarea) | Hidden visually below choices |
| Secondary | Other intents | 其他事项 dropdown | OK as menu |
| Tertiary | Examples | 查看示例 toggle | OK |
| Tertiary | Simulation | 场景仿真 text link | Remove for customers |
| Tertiary | Resume case | 用这条记录继续 | OK |

**Flag:** ⚠️⚠️⚠️ **Four primaries** — worst page in customer product

**Fix:** One full-width primary: 「描述您的需求」→ textarea hero + 「发送」; add-car as suggested example only

---

## Page: Add Car — Lane Start (First Turn)

| Tier | Action | Control | Notes |
|------|--------|---------|-------|
| **Primary** | Reply to system | 提交补充 | ✅ |
| Secondary | Read progress | Progress card | OK |
| Tertiary | Change intent | × on tag | OK |

**Flag:** ✅ Pass (once conversation started)

---

## Page: Add Car — Collecting (Pre-Handoff)

| Tier | Action | Control | Notes |
|------|--------|---------|-------|
| **Primary** | Submit next info | 提交补充 | ✅ |
| Secondary | Read gaps | Still-needed tags in rail | OK |
| Secondary | Expand thread | Collapse 展开查看报送对话 | OK |
| Tertiary | Copy case ID | Monospace ID | OK |

**Flag:** ✅ Pass

---

## Page: Add Car — Handoff Pending

| Tier | Action | Control | Notes |
|------|--------|---------|-------|
| **Primary** (intended) | Formal submit to office | 确认提交，开始报价处理 | ✅ |
| **Primary** (competing) | Send phone in chat | 提交补充 (contact reply) | ⚠️ Alert says "先回手机号" |
| Secondary | Optional note | Empty submit allowed | OK |
| Tertiary | WeChat identity | 绑定微信 links | Hide default |

**Flag:** ⚠️ **Two primaries** — chat reply vs confirm button

**Fix:** Single CTA: inline phone field OR one button that accepts empty if phone already in thread

---

## Page: Post-Handoff Confirmation

| Tier | Action | Control | Notes |
|------|--------|---------|-------|
| **Primary** (intended) | Wait for office | (read-only) | Implicit only |
| Secondary | Append same case | 追加到本条记录 | OK collapsed |
| Secondary | New issue | 提交新问题 | OK |
| **Primary** (competing) | View broker workbench | 查看工作台 | ⚠️ Dev/customer leak |
| Tertiary | Expand thread | Collapse | OK |

**Flag:** ⚠️ **Zero explicit primary + dev button competes**

**Fix:** One line: 「已完成。请等待办公室联系您。」+ link 「有补充？」

---

## Page: Generic Intake (Non–Add-Car) Mid-Flow

| Tier | Action | Control | Notes |
|------|--------|---------|-------|
| **Primary** | Submit message | 提交补充 | ✅ |
| Secondary | Read progress | Progress card | OK |
| Tertiary | Intent tag | Closable tag | OK |

**Flag:** ✅ Pass

---

## Page: Remove Car / Upload Docs / Claim (Dropdown Start)

| Tier | Action | Control | Notes |
|------|--------|---------|-------|
| **Primary** | Describe issue | 提交报送 | ✅ after menu click |
| Secondary | Pick different intent | 其他事项 | OK |
| Tertiary | Add-car buttons still visible | Empty state remnants | ⚠️ Before first submit only |

**Flag:** ⚠️ On empty state, dropdown path fights landing buttons

---

## Page: My Requests — List

| Tier | Action | Control | Notes |
|------|--------|---------|-------|
| **Primary** | Select a case | List row click | ✅ |
| Secondary | Refresh | 刷新 | OK |

**Flag:** ✅ Pass

---

## Page: My Requests — Detail Panel

| Tier | Action | Control | Notes |
|------|--------|---------|-------|
| **Primary** | Continue in portal | 去客户报送继续 | ✅ |
| Secondary | Read status | Tags + next step panel | OK |
| Tertiary | Scan field chips | Collected/missing sections | OK |

**Flag:** ✅ Pass — best primary-action discipline in customer UI

---

## Summary Table

| Page | Primary (intended) | Competing primaries | Flag |
|------|-------------------|---------------------|------|
| Global chrome | 客户报送 | 办公室工作台 tab | ⚠️ |
| Landing empty | Start intake | +3 (human, structured, text) | ⚠️⚠️⚠️ |
| Add-car collecting | 提交补充 | — | ✅ |
| Handoff pending | 确认提交 | Chat reply | ⚠️ |
| Post-handoff | Wait | 查看工作台 | ⚠️ |
| Generic mid-flow | 提交补充 | — | ✅ |
| My requests | Select / continue | — | ✅ |

**Pages passing:** 3 / 7 customer states  
**Pages flagged:** 4 / 7

---

## Priority Fixes (UI Only)

1. Landing → one hero textarea + one send button  
2. Handoff pending → merge phone capture into submit step  
3. Post-handoff → explicit wait CTA; remove 查看工作台 from customer view  
4. Customer URL → no broker tab visible

---

*End of P16-N Phase 3 — Primary Action Audit*
