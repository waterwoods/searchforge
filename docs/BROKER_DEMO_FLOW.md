# Broker Demo Flow

**Purpose:** Step-by-step demo for founders showing Unified Intake to a broker.  
**Story:** [`DEMO_STORY.md`](./DEMO_STORY.md)  
**Broker summary:** [`BROKER_ONE_PAGER.md`](./BROKER_ONE_PAGER.md)

---

## Before the demo (5 min)

```bash
bash scripts/demo_pre_checklist.sh
bash scripts/guardrail_inbox_triage.sh    # must PASS
bash scripts/run_demo_local.sh            # if not already running
```

**Open:** http://localhost:5173/workbench/unified-intake  
**Production (if deployed):** https://ui-smoky-beta.vercel.app/workbench/unified-intake

---

## Opening (1 min)

**Say (Chinese or English):**

> 这是一个加州汽车保险经纪助手。客户发来 messy 消息——微信、通知、截图描述——系统整理成一个结构化 case：有 urgency、下一步动作、收集了什么、还缺什么、草稿回复。你确认后再发，**不自动发送**。

**Do:** Open workbench. Point to **Customer Entry** (optional) and **Broker Workbench** tabs.

---

## Demo sequence (12 min)

| # | Step | Time | What to show |
|---|------|------|--------------|
| 1 | **Load founder demo queue** | 1 min | 13 sample cases; cancellation opens first |
| 2 | **Cancellation risk** | 3 min | Case focus, Your next move, Same-day action, Broker action required |
| 3 | **Missing document** | 3 min | Reopen from Recent cases; waiting on client; verify receipt |
| 4 | **Add-car quote** | 3 min | Collected / Still needed chips; multi-turn handoff |
| 5 | **Human confirmation** | 1 min | Gold badge when AI collected data to verify |
| 6 | **Optional: Customer Entry** | 1 min | Paste messy message → first response → case in workbench |

**Backup if live API slow:** Simulation Assistant → run Cancellation, Missing doc, Add-car scenarios.

---

## What to emphasize

- One messy message → one structured case
- Broker stays in control — no auto-send
- Collected / Still needed at a glance
- Your next move — one operational sentence
- Follow-up continuity — reopen, paste new message, resume

---

## What NOT to say

- "Connected to WeChat or email"
- "Reads image uploads"
- "Automatically sends replies"
- "Full CRM or carrier integration"
- "Handles every multilingual edge case perfectly"

---

## If something fails

| Issue | Action |
|-------|--------|
| 503 / embedding_warming | `bash scripts/restore_8001_readiness.sh` |
| Live triage slow | "第一轮可能慢一点" → proceed or switch to Simulation Assistant |
| API down | Use Simulation Assistant only — same flow, preset scenarios |

**Say:** "Let me show the same flow with our practice scenarios."

---

## Closing (2 min)

**Ask 3–5 questions:**

1. Which scenario felt most useful to your office?
2. Which part still feels risky or not trustworthy?
3. Would this save you or your assistant time?
4. What would you want it to do next?
5. What would you be willing to try first in a pilot?

**One-sentence pilot offer:**

> 试用一周：帮你把客户发来的 messy 消息整理成结构化 case，有下一步动作、收集了什么、还缺什么、草稿回复。你确认后再发，不自动发送。

---

## Post-demo follow-up

**Send within 24 hours:**

> 感谢今天的时间。Unified Intake 帮你把客户消息整理成结构化 case，你确认后再发。  
> 试用链接：[URL]  
> 一页说明：BROKER_ONE_PAGER  
> 有问题随时微信/邮件我。

---

## Quick reference

| Item | Value |
|------|-------|
| URL | `/workbench/unified-intake` |
| First action | Load founder demo queue |
| Top 3 cases | Cancellation → Missing doc → Add-car |
| Pre-demo | `demo_pre_checklist.sh` + `guardrail_inbox_triage.sh` |
| Full narrative | [`DEMO_STORY.md`](./DEMO_STORY.md) |

*End of broker demo flow*
