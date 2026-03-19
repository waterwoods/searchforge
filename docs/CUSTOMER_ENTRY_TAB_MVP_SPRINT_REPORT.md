# Customer Entry Tab MVP Sprint Report

**Sprint:** Customer Entry Tab MVP  
**Date:** 2026-03-09

---

## 1. Stages completed

| Stage | Status | Notes |
|-------|--------|------|
| Stage 1 — Customer Entry Tab Structure | ✅ Completed | Tab A (Customer Entry) + Tab B (Broker Workbench). Customer Entry is default. |
| Stage 2 — Customer-side flow design | ✅ Completed | Customer enters message → triage → first-pass response → case saved → "查看工作台" to broker |
| Stage 3 — 4 highest-value scenes | ✅ Completed | Payment failed, English notice confusion, missing document, add car/premium — all covered by existing triage + CUSTOMER_ENTRY_EXAMPLES |
| Stage 4 — Connect to broker workbench | ✅ Completed | Same triage API, persist_case=true, case appears in Recent cases; "查看工作台" switches tab and opens case |
| Stage 5 — MVP demo readiness | ✅ Completed | Docs updated; validation scripts pass |

---

## 2. Product changes made

### Stage 1–2: UI structure and customer flow

| File | Change |
|------|--------|
| `ui/src/pages/UnifiedIntakePage.tsx` | Added `CustomerEntryTab` component; wrapped page in `Tabs` with Customer Entry (default) and Broker Workbench; added `CUSTOMER_ENTRY_EXAMPLES` for 4 priority scenes |

### Stage 3–4: Connection and examples

| File | Change |
|------|--------|
| `ui/src/pages/UnifiedIntakePage.tsx` | Customer Entry uses same `triageMessage(..., true)` API; `onSwitchToBroker(caseId)` passes case to broker tab; `BrokerWorkbenchTab` accepts `initialCaseId` and opens that case when switching |

### Stage 5: Documentation

| File | Change |
|------|--------|
| `docs/CHEN_KUI_FOUNDER_DEMO_SCRIPT.md` | Added "Two surfaces" section; Step 1 = Customer Entry demo; renumbered steps |
| `docs/UNIFIED_INTAKE_DEMO_READINESS.md` | Added Customer Entry as default tab; updated "What Will Be Shown" |
| `docs/runbooks/UNIFIED_INTAKE_MVP_RUNBOOK.md` | Added Tabs, Customer flow, Broker flow to UI Entry Point table |

---

## 3. Customer experience design

**What the customer sees first:**
- Title: 客户入口
- One short sentence: 请描述您的问题或粘贴收到的通知内容，我们会尽快帮您处理。
- One main input box (placeholder: 请在此输入或粘贴您的问题、通知内容或截图文字...)
- One main CTA: 提交
- Optional: 需要示例？ with 4 example links (Payment failed, English notice confusion, Missing document, Add car / premium)

**How they interact:**
1. Paste or type their message
2. Click 提交
3. See a first-pass response: `client_reply_draft` (short, natural, Chen Kui–style)
4. See urgency note if critical/high
5. See "Chen Kui's office will review this and follow up" when manual follow-up needed
6. See "请准备：..." when client prep is relevant
7. Can click 查看工作台 to switch to broker tab (for demo) or 提交新问题 to start over

**How this differs from broker workbench:**
- No founder demo snapshot, no broker jargon, no case status/urgency tags
- No "Your next move", "Copy client draft", "Recent broker cases"
- Simple, calm, customer-facing language only

---

## 4. Broker-side continuity

- **Same API:** Customer Entry calls `POST /api/inbox/triage` with `persist_case: true`, same as broker paste flow.
- **Same case store:** Case is saved to the same local JSON store; appears in Recent broker cases.
- **Switch flow:** "查看工作台" sets `brokerInitialCaseId` and switches to Broker tab; `BrokerWorkbenchTab` opens that case when recent cases load.
- **Consistency:** Urgency, category, broker_next_step, client_prep, client_reply_draft, manual_followup_needed — all identical. Broker sees the full case card.

---

## 5. Validation summary

| Check | Result | Protects |
|-------|--------|----------|
| `npm run build` | ✅ Pass | Frontend compiles |
| `run_inbox_triage_scenarios.py` | ✅ 28/28 | Category, urgency, escalation |
| `run_chen_kui_proxy_calibration.py` | ✅ 12/12 | Draft style |
| `guardrail_inbox_triage.sh` | ✅ Pass | Scenario pack, API, persistence |
| `test_inbox_triage_api.py` | ✅ 12/12 | API behavior |
| `unified_intake_smoke_check.sh` | ✅ Pass | Full guardrail + manual steps |

---

## 6. Business value impact

- **Reduces repeated customer calls/messages:** Customer gets a useful first response immediately.
- **Reduces confusion from English notices:** Triage + draft in Chinese when input is Chinese.
- **Reduces simple repetitive work:** First-pass explanation and routing.
- **Surfaces high-risk cases faster:** Urgent cases get "This needs urgent attention" and broker follow-up note.
- **Helps office handle more customers:** One simple front door; broker workbench stays intact.

---

## 7. Remaining blocker(s)

1. **Customer Entry uses dark theme:** Same as rest of app; may want lighter theme for customer-facing tab in future.
2. **No customer identity:** Case is anonymous; no linking to policy/customer (deferred).
3. **Demo-only:** No real inbox sync, auth, or production deployment for customer entry.

---

## 8. Recommended next step

**One clear next step:** Run a live demo with Chen Kui: show Customer Entry first (paste payment-failed message), then Broker Workbench. Gather feedback on whether the customer-facing wording and flow feel right.

---

## 9. 中文或中英混合宏观总结

**这次主要做了什么：**
- 新增了「客户入口」标签页，作为默认首页
- 客户可以在这里粘贴或输入问题，系统自动分类并给出第一轮回复
- 回复会保存为 case，进入后台工作台

**客户入口现在是什么样子：**
- 一个标题「客户入口」
- 一句引导语
- 一个大输入框
- 一个「提交」按钮
- 提交后显示简短、自然的回复，以及「陈奎办公室会跟进」等说明

**后台工作台怎么配合：**
- 客户提交的 case 会出现在 Recent broker cases
- 点击「查看工作台」会切换到 Broker 标签并打开该 case
- 经纪人可以照常处理：改状态、加备注、复制 draft 等

**有没有困难或限制：**
- 目前是 demo 环境，没有真实 inbox、登录、客户身份
- 客户入口和后台共用同一套 triage API，没有额外后端改动

**现在最适合怎么展示：**
- 先展示客户入口：粘贴「客户问：这个英文 notice 说 payment failed，我现在怎么办？」
- 点击提交，看第一轮回复
- 点击「查看工作台」，切换到 Broker 标签，看 case 和后续处理

---

## 10. 如何打开前端 / 后端

| Item | Value |
|------|-------|
| **Start demo** | `bash scripts/run_demo_local.sh` |
| **Frontend URL** | http://localhost:5173/workbench/unified-intake |
| **Backend URL** | http://localhost:8001 (default) |
| **Tab entry** | 客户入口 = default; Broker Workbench = second tab |
| **Port caveats** | If 5173 is taken, Vite may use 5174; if 8001 is occupied, use `restore_8001_readiness.sh` or run backend on 8002 |

---

## 11. Customer-to-Broker walkthrough simulation

**Step 1 — Customer enters a messy message**

Customer goes to 客户入口 tab. Pastes:

```text
客户问：这个英文 notice 说 payment failed，我现在怎么办？
```

Clicks **提交**.

**Step 2 — System responds on customer side**

Customer sees:
- Main response (client_reply_draft): 这看起来是付款出了问题。请把最新通知或付款截图发我，我先帮你确认；如果还没付，今天尽快处理，避免停保。
- Urgency tag: This needs attention soon.
- Follow-up note: Chen Kui's office will review this and follow up with you.
- 请准备：Updated payment method details, payment confirmation, or the best number to reach them today.

**Step 3 — Broker side receives/opens the case**

Customer clicks **查看工作台**. Tab switches to Broker Workbench. The case auto-opens (or appears in Recent cases). Broker sees:
- Urgency: HIGH
- Category: Payment / lapse risk
- Your next move: Confirm whether the payment actually failed...
- Client prep, draft, etc.

**Step 4 — Broker continues the work**

Broker can:
- Change status (Reviewing, Waiting client, Done)
- Save follow-up (waiting_on, next_contact_by)
- Add broker note
- Copy client draft and send via WeChat/email

**Step 5 — Value becomes visible**

- Customer got an immediate, useful response
- Case is in the broker queue, not lost
- Broker has structured next step and draft
- One product, two surfaces: customer speaks first, broker continues
