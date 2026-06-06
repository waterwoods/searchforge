# Human Front Door + Talk-to-Agent — UX / Interaction Design Spec

**Sprint:** Human Front Door + Talk-to-Agent Sprint  
**Created:** 2026-03-15

---

## 1. First Screen Experience

### Headline
- **Primary:** "今天有什么可以帮您？" (What can we help you with today?)
- **Secondary:** "您可以选择下面的主题，或直接在下方输入您的问题。如需人工协助，可点击「联系人工」。"
- **Rationale:** Keeps existing warmth; adds explicit mention of human path.

### Welcome Card (when turns.length === 0)
- One clear headline
- One line explaining: buttons OR free text
- **New:** One line reassuring: "如需人工协助，可点击「联系人工」" — surfaces the human path immediately

### Buttons
- **6 buttons** (not 5): 报价, 变更, 事故, 付款, 材料, **联系人工**
- "联系人工" is always visible, same prominence as others
- Labels: customer language, not internal terms

### Free Text
- Placeholder: "请在此输入或粘贴您的问题、通知内容或截图文字..."
- Visible, inviting; user can type without clicking first

### Examples
- "需要示例？" → **"不确定说什么？点这里看示例"** (Not sure what to say? See examples)
- Surface more prominently; reduce "tucked away" feel

---

## 2. Reassurance Copy

### During Intake
- System replies: "好的，宝马X5。" — acknowledge first
- "先把年份和地址邮编发我" — one ask at a time
- **Never:** "内容不够完整" or "请提供更多信息" when intent is clear

### Office Follow-Up Language
- "办公室会尽快处理，有结果会联系您。"
- "您的消息会直接转给办公室，我们会尽快处理。"
- "如需，办公室会主动联系您。"

### Trust Boundary
- No false promises (e.g., no premium numbers without broker)
- "需要办公室确认" when human confirmation required
- "已整理成 case，办公室会尽快跟进。"

---

## 3. Talk to Agent — Where and How

### Where It Appears
- **Button set:** 6th button, always visible
- **Fallback area:** Optional secondary link below input: "想直接联系办公室？点这里"

### How It Behaves
- Click "联系人工" → sends starter message "我想联系陈奎办公室"
- Backend returns `handoff_ready=true`, `broker_next_step="Customer requested human contact"`
- System reply: "好的，已帮您转给陈奎办公室，他们会尽快联系您。"
- No multi-turn intake; immediate handoff

### What It Says (Customer)
- Button label: "联系人工"
- Optional sublabel: "联系陈奎办公室"
- Handoff message: "好的，已帮您转给陈奎办公室，他们会尽快联系您。"

### What Broker Sees
- `broker_next_step`: "Customer requested human contact. Call or message back promptly."
- `conversation_summary`: "Customer requested to speak with office / 客户要求联系人工"

---

## 4. Customer-Facing vs Office-Facing Language

| Context | Customer-Facing | Office-Facing |
|---------|-----------------|----------------|
| Intent | "报价" / "付款" | `add_car`, `cancellation_warning` |
| Collected | "年份、车型、邮编" | `year`, `make_model`, `zip` |
| Still needed | "提车日期" | `delivery_date` |
| Handoff | "办公室会尽快处理" | `broker_next_step`, `client_reply_draft` |

**Rule:** Customer Entry tab uses customer-facing language. Broker Workbench can use technical labels for power users.

---

## 5. Business-Readable Case Summary

### During Intake (Customer Entry)
- **Title:** "Case Summary" → **"已收集信息"** or keep "Case Summary" with humanized content
- **Intent:** "主题 / Intent: add_car" → **"主题：新车报价"**
- **Collected:** "year, make_model, zip" → **"已收集：年份、车型、邮编"**
- **Still needed:** "delivery_date, primary_driver" → **"还需：提车日期、主驾信息"**

### Humanize Mapping (examples)
| Raw | Humanized (ZH) | Humanized (EN) |
|-----|----------------|----------------|
| year | 年份 | Year |
| make_model | 车型 | Make/Model |
| zip | 邮编 | ZIP |
| delivery_date | 提车日期 | Delivery date |
| primary_driver | 主驾信息 | Primary driver |
| vin | 车架号 | VIN |
| notice_present | 有通知 | Notice present |
| customer_says_sent_X | 客户说已发 X | Client says sent X |

### Handoff Card
- "办公室会尽快处理，有结果会联系您。"
- "已整理成 case，办公室会尽快跟进。"
- "如有需要，办公室会主动联系您。"

---

## 6. Trust Boundary Wording

| Scenario | Wording |
|----------|---------|
| Not auto-send | "办公室会尽快处理" (not "已发送") |
| Office follow-up | "有结果会联系您" |
| Human confirmation | "需要办公室确认" / "Human confirmation recommended" |
| Uncertainty | "这段内容还不够完整。把完整通知再发我一下，我帮你确认下一步。" |

---

*See also: Product Blueprint, Talk-to-Agent Policy, Execution Outline*
