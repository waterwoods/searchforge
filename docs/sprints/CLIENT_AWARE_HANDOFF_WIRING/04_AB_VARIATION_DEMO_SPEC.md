# A/B Variation Demo Spec

**Purpose:** Define how to prove Client A vs Client B variation at the backend/API level.

---

## 1. Proof Path

| Step | Action | Expected |
|------|--------|----------|
| 1 | POST /api/inbox/triage with `{"text": "我想联系客服", "soft_route": "talk_to_agent", "client_id": "demo_broker"}` | `client_reply_draft` contains "客服团队" not "陈奎办公室" |
| 2 | POST /api/inbox/triage with same payload, `client_id`: "chen_kui" | `client_reply_draft` contains "陈奎办公室" or "办公室" |
| 3 | Add-car handoff with demo_broker | `client_reply_draft` contains "客服团队" |
| 4 | Add-car handoff with chen_kui | `client_reply_draft` contains "办公室" |

---

## 2. Exact Prompts That Should Differ

| Scenario | Client A (chen_kui) | Client B (demo_broker) |
|----------|---------------------|------------------------|
| Talk to Agent | "好的，已帮您转给陈奎办公室，他们会尽快联系您。" | "好的，已帮您转给客服团队，他们会尽快联系您。" |
| Add-car handoff | "您说的报价资料已整理好了，办公室会尽快出价，有结果会联系您。" | "您说的报价资料已整理好了，客服团队会尽快出价，有结果会联系您。" |
| Other handoff | "您说的情况已整理好了，办公室会尽快处理，有结果会联系您。" | "您说的情况已整理好了，客服团队会尽快处理，有结果会联系您。" |

---

## 3. What Founder Should Show

1. Open `/workbench/unified-intake?client=demo_broker`
2. Paste "我想联系客服" or click "联系人工"
3. Show `client_reply_draft`: "客服团队"
4. Switch to `?client=chen_kui` (or omit)
5. Same flow → "办公室" or "陈奎办公室"

---

## 4. How to Explain the Reuse Story Simply

> "When you change the client, the handoff messages change too. Not just the UI labels—the actual draft the broker sends to the customer. That's what makes A→B migration lighter: one config folder, different wording."

---

*End of Spec*
