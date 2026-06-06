# P16-N Phase 1 — Customer Journey Map

**Date:** 2026-06-01  
**Sprint:** P16-N Customer Entry Simplification (evaluation only — no code)  
**Scope:** All customer-facing surfaces in Unified Intake full dev UI  
**Source:** `CustomerEntryTab.tsx`, `UserCaseListProgressPanel.tsx`, `UnifiedIntakePage.tsx`, `configs/clients/chen_kui/ui_copy.json`

---

## Journey Overview

```
Arrive → Choose intent (?) → Provide info → Submit → Office receives → Confirmation / Status
         ↑ friction cluster here (score ~50)
```

Customer paths share one tab (`客户报送`) plus a secondary tab (`我的办理`). There is no separate route per intent — Add Car, Remove Car, Upload Documents, and Status are **modes inside the same shell**, not distinct pages.

---

## Surface 1 — Global Entry (Chrome + Tabs)

**Route:** `/unified-intake?tab=customer` (full dev UI only; hidden in `product_only` trial)

| Question | Answer |
|----------|--------|
| **What is the user trying to do?** | Find where to send a insurance request to the broker office |
| **Single primary action?** | Switch to 客户报送 tab and start — but tab bar competes with in-tab choices |
| **What distracts them?** | Dark app header duplicate title; tab suffix micro-copy (报送入口·加车优先); brand card tagline about broker paste (trial); 4 tabs including 办公室工作台 and 场景仿真 |

**Entry points:** Direct link, broker-shared URL, resume from 我的办理

---

## Surface 2 — Landing / Empty State

**Component:** `CustomerEntryTab` when `turns.length === 0`

| Question | Answer |
|----------|--------|
| **What is the user trying to do?** | Start a new insurance request (most often: add car quote) |
| **Single primary action?** | Intended: 办理加车报价 — **but** three equal-width buttons + structured form + textarea compete |
| **What distracts them?** | Long hero tagline (2 sentences, pilot scope); 3-step flow track before any action; numbered ①②③ in secondary copy; 办理类型 label; 联系人工 as co-primary button; 其他事项 dropdown; collapsed structured form still visible as panel header; de-emphasized textarea below fold; 场景仿真 link; resume-hint blocks |

**Visible object count:** ~16–18 (target: 8–10)

---

## Surface 3 — Add Car (Primary Path)

**Triggers:** 办理加车报价 button · structured form CTA · free text mentioning add car

| Stage | User goal | Primary action | Distractions |
|-------|-----------|----------------|--------------|
| **3a — Lane start** | Confirm they're doing add-car quote | Continue in conversation | Transaction banner (gradient card); flow step track; intent tag |
| **3b — Collecting** | Answer system questions / fill gaps | 提交补充 | Progress card + AddCarRecordSummaryRail (6+ sections); bubble thread tags; gap alerts stacking; monospace case ID |
| **3c — Handoff pending** | Send record to office queue | 确认提交，开始报价处理 | Alert + button subline + identity strip + contact-only alert — four trust/explanation layers |
| **3d — Post-handoff** | Know it's done; wait for office | Read confirmation | Result card + timestamps + UTC footnote + structured snapshot + flow explanation + append collapse + boundary essay + 查看工作台 |

---

## Surface 4 — Remove Car

**Triggers:** 保单变更 in 其他事项 dropdown · free text ("拿掉一辆车")

| Question | Answer |
|----------|--------|
| **What is the user trying to do?** | Remove a vehicle from policy |
| **Single primary action?** | Describe which vehicle / paste notice — then 提交报送 |
| **What distracts them?** | Empty state pushes Add Car first; no Remove Car-specific headline; generic progress card labels; add-car transaction banner if mis-routed |

**Note:** No dedicated Remove Car screen — same shell as all intents. Professional SaaS would not ask category first; would infer from message.

---

## Surface 5 — Upload Documents

**Triggers:** 上传材料 in dropdown · free text ("补材料")

| Question | Answer |
|----------|--------|
| **What is the user trying to do?** | Send missing documents or confirm upload |
| **Single primary action?** | Describe what they're sending (no file upload in customer UI — text only) |
| **What distracts them?** | Label says 上传材料 but there is no upload control — expectation mismatch; add-car structured fields irrelevant; collected/still-needed field chips use engineer labels |

---

## Surface 6 — Other Intents (Claim, Payment/Bill, Talk to Agent)

| Intent | Entry | Primary action | Distractions |
|--------|-------|----------------|--------------|
| **报事故** | Dropdown | Describe accident | Buried in 其他事项; add-car hero copy |
| **付款 / 账单** | Dropdown | Paste payment notice | Constitution cancellation wedge — should be message-first, not 4th in menu |
| **联系人工** | Equal button | Start human handoff message | Competes visually with 办理加车报价 |

---

## Surface 7 — Active Conversation (Generic / Non–Add-Car)

**Component:** `CustomerEntryTab` mid-flow, non–add-car lane

| Question | Answer |
|----------|--------|
| **What is the user trying to do?** | Continue explaining their issue |
| **Single primary action?** | 提交补充 |
| **What distracts them?** | Full chat thread with bubble labels; progress card below thread (wrong order for scan); category tags; quote-ready status jargon; lifecycle tags on bubbles |

---

## Surface 8 — Status / My Requests

**Component:** `UserCaseListProgressPanel` (`我的办理` tab)

| Question | Answer |
|----------|--------|
| **What is the user trying to do?** | Check progress on submitted requests |
| **Single primary action?** | Select a record → read next step → 去客户报送继续 |
| **What distracts them?** | Two-column master-detail on desktop (OK); formal + updated timestamps without footnote (good); field chip groups mirror broker rail — dense for customer; empty state sends user back to confusing landing |

---

## Surface 9 — Post-Handoff Confirmation

**Component:** Green result card after `formalSubmissionComplete`

| Question | Answer |
|----------|--------|
| **What is the user trying to do?** | Confirm submission succeeded; know what happens next |
| **Single primary action?** | Wait for office contact (implicit — **not stated as one CTA**) |
| **What distracts them?** | AddCarFlowExplanation; duplicate broker_next_step blocks; UTC timing truth note; structured snapshot panel; thread collapse; append collapse; boundary hint essay; 查看工作台 + 提交新问题 as dual primaries |

**P16-M score here:** 83/100 (best customer screen — still over-built)

---

## Surface 10 — Other Entry Points

| Entry | Purpose | Customer clarity |
|-------|---------|------------------|
| Resume hint (single in-progress case) | Continue add-car | Good — but small link under hero noise |
| Resume hint (multi case) | Pick case in 我的办理 | OK |
| 不确定如何描述？查看示例 | Example fill | Should be inline placeholder, not toggle |
| Light identity / WeChat strip | Optional binding | Low value v1; adds links at handoff moment |
| Error Alert | API failure | OK |

---

## Journey Friction Map

| Step | Screen | Severity | Issue |
|------|--------|----------|-------|
| 1 | Empty landing | **Critical** | Category-before-message; 3 competing primaries |
| 2 | First keystroke | High | Textarea de-emphasized; placeholder says "don't use me for add-car" |
| 3 | Mid-flow add-car | Medium | Record rail reads like broker tool |
| 4 | Handoff pending | Medium | Two-step mental model (回手机 vs 确认提交) |
| 5 | Confirmation | Low–Medium | Success clear but append/boundary UI overload |
| 6 | Status tab | Low | Usable; empty state loops to bad landing |

---

## Screen Inventory Summary

| Screen | File | Est. visible objects | One-task? |
|--------|------|---------------------|-----------|
| Global chrome | UnifiedIntakePage | 6–8 | ❌ |
| Landing empty | CustomerEntryTab | 16–18 | ❌ |
| Add-car collecting | CustomerEntryTab | 25–35 | ⚠️ |
| Add-car handoff pending | CustomerEntryTab | 20–28 | ⚠️ |
| Post-handoff result | CustomerEntryTab | 18–24 | ⚠️ |
| Generic mid-flow | CustomerEntryTab | 15–22 | ✅ |
| My Requests list | UserCaseListProgressPanel | 10–14 | ✅ |
| My Requests detail | UserCaseListProgressPanel | 12–16 | ✅ |

---

*End of P16-N Phase 1 — Customer Journey Map*
