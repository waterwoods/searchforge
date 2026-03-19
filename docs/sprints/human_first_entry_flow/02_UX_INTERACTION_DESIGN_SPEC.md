# Human-First Entry Flow — UX / Interaction Design Spec

**Sprint**: Human-First Entry Flow + Startup Latency Audit  
**Created**: 2026-03-15

---

## 1. What Happens When User Clicks a Button

| Step | Behavior |
|------|----------|
| 1 | User clicks "获取报价" (or any quick-start button) |
| 2 | **If input is empty**: System immediately submits a starter message for that intent and fetches the first reply |
| 3 | **If input has text**: User must click Submit; button provides soft_route hint |
| 4 | First system reply acknowledges intent and asks only the next missing field |

**Starter messages per button** (minimal, trigger the right flow):

| Button | Starter message (Chinese) |
|--------|---------------------------|
| 获取报价 | 我想加新车报价 |
| 保单变更 | 我想从保单拿掉一辆车 |
| 报事故 | 刚出事故了 |
| 付款 / 账单 | 付款有问题 |
| 上传材料 / 联系客服 | 有材料要补 |

---

## 2. What Happens When User Types Directly

| Step | Behavior |
|------|----------|
| 1 | User types in the text area (no button selected) |
| 2 | User clicks Submit |
| 3 | Triage infers intent from text |
| 4 | System replies: acknowledge intent first, then ask only next missing field |

---

## 3. What the First Response Should Look Like

| Intent | Good first response (Chinese) |
|--------|-------------------------------|
| Quote | "好的，我来帮您看新车报价。先把年份和车型发我，我就能帮你算。" |
| Claim | "刚出事故一定很着急，先别慌。先把事故经过、对方信息和照片发我，我帮你确认下一步怎么报案。" |
| Payment | "这看起来是付款出了问题。把最新通知或付款截图发我，我先帮你确认；如果还没付，今天尽快处理。" |
| Missing doc | "现在文件里还缺资料。请把资料再发我一次；如果你之前已经发过，也跟我说一声，我这边帮你核对。" |
| Remove car | "好的，可以处理。把卖车日期、车辆信息和是否已经过户发我，我先帮你确认。" |

**Never**: "内容不够完整" or "请提供更多信息" when intent is clear.

---

## 4. How Selected Topic Is Shown

- When user has selected a button and turns exist: show "当前主题：获取报价" (or equivalent) as a closable tag
- When rerouting occurs: show reroute message, then clear button selection
- User can always type to override; free text is highest-priority truth

---

## 5. How the Live Summary Should Appear

| Location | Content |
|----------|---------|
| Customer-side (during intake) | Collapsible or inline "Case Summary" card: Intent, What we understood, Key collected fields, What is still missing |
| Office-side (Broker Workbench) | Same summary in case card; already partially exists via conversation_summary |

**Update timing**: After each system reply, summary reflects latest collected_fields, still_needed_fields, and issue_category.

---

## 6. How Customer-Side vs Office-Side Relate

| Surface | Purpose |
|---------|---------|
| Customer Entry | Intake; welcome + buttons + free text; live summary draft |
| Broker Workbench | Triage queue; case cards with conversation_summary, broker_next_step, client_reply_draft |

The live summary on the customer side mirrors what the office will see, building trust.

---

## 7. If the System Is Uncertain

- Be honest: "这段内容还不够完整。把完整通知或前后内容再发我一下，我帮你确认下一步。"
- Say office/human confirmation is needed when appropriate
- Do not bluff or guess

---

*See also: Product Blueprint, Execution Outline, Acceptance/SLA Criteria*
