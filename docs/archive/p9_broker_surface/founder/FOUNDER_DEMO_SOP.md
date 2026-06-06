> **HISTORICAL / ARCHIVE — P9 Broker Surface Collapse (2026-05-30)**
> **Read instead:** [`docs/FOUNDER_ONE_PATH.md`](../../../FOUNDER_ONE_PATH.md)

# Founder Demo SOP — Unified Intake / Chen Kui Trial

> **Superseded for launch flow:** [`FOUNDER_LAUNCH_PATH.md`](./FOUNDER_LAUNCH_PATH.md) — use that for canonical founder path. This SOP remains for Chen Kui–specific demo depth.

**Purpose:** One repeatable SOP for demo day. Use this for Chen Kui or small-client prospect.  
**Created:** 2026-03-14 — Founder Demo SOP + Real Trial Feedback Sprint

---

## Pre-Demo (5–10 min before)

### 1. Warmup

```bash
bash scripts/demo_pre_checklist.sh
```

- **"Use Live path"** or **"Ready for Live Demo"** → proceed
- **"Use Offline path"** → use Simulation Assistant or founder demo queue (no live API needed)

### 2. Start demo (if not running)

```bash
bash scripts/run_demo_local.sh
```

Wait for "Demo ready". Backend: 8001. Frontend: 5173.

### 3. Optional: warm backend 2–3 min before

```bash
bash scripts/warmup_for_demo.sh
```

### 4. Guardrail (recommended)

```bash
bash scripts/guardrail_inbox_triage.sh
```

Must PASS before demo.

---

## URL to Open

**Primary:** http://localhost:5173/workbench/unified-intake  
**Production (if deployed):** https://ui-smoky-beta.vercel.app/workbench/unified-intake

---

## First 30–60 Seconds (What to Say)

**Say (Chinese or English):**

> "这是一个加州汽车保险经纪助手。客户发来messy消息——微信、截图、通知——系统会整理成一个结构化case：有 urgency、下一步动作、收集了什么、还缺什么、草稿回复。你确认后再发，**不自动发送**。经纪保持控制。"

**Or shorter:**

> "把messy消息变成结构化case，有下一步、草稿回复。你确认后再发，不自动发送。"

**Do:** Open the URL. Point to Customer Entry tab. Say: "客户从这里发消息进来。"

---

## Which Path to Show First

**Primary path:** Broker Workbench → Load founder demo queue → Cancellation risk first

1. Click **Load founder demo queue** (seeds 13 demo-safe cases)
2. Cancellation-risk case auto-opens
3. Point to: Case focus, Your next move, Same-day action, Broker action required
4. Point to: Human confirmation recommended (when visible)
5. Then: Reopen Missing document case → show waiting on, next contact
6. Then: Reopen Add-car quote → show Collected / Still needed chips

**Backup path:** Simulation Assistant → SIM1, SIM2, SIM3

1. Click **Simulation Assistant** (side panel)
2. Run **SIM1 Cancellation risk** (3-turn)
3. Run **SIM2 Missing document** (3-turn)
4. Run **SIM3 Add-car quote (Chinese)** (3-turn)
5. Point to: Collected, Still needed, Human confirmation per turn

---

## Top 3 Scenarios (Strongest)

| # | Scenario | Why |
|---|----------|-----|
| 1 | **Cancellation risk** (SIM1) | Urgency, same-day action; most obvious "must act" value |
| 2 | **Missing document** (SIM2) | Operational follow-up; "client says already sent" — real office pain |
| 3 | **Add-car quote (Chinese)** (SIM3) | Revenue, multi-turn, Collected chips; handoff at turn 3 |

**Order:** Always start with Cancellation risk.

---

## What to Emphasize

- **One inbound message → one structured case** — no manual triage
- **Broker stays in control** — nothing auto-sent; human confirmation
- **Collected / Still needed** — shows what AI extracted and what is missing
- **Your next move** — one dominant operational sentence
- **Case focus** — Add car quote, Premium review, Claim intake, Missing document, Payment/cancellation risk

---

## What NOT to Overclaim

Do **not** say:

- "It is connected to email or WeChat."
- "It reads image uploads."
- "It automatically sends replies."
- "It manages full CRM or carrier integration."
- "It perfectly handles every multilingual message."

---

## If Turn 1 Is Slow

**Say:** "有时第一轮会慢一点，我们继续看第二轮。"

**Do:** Proceed to Turn 2. If API fails, switch to Simulation Assistant: "我们用预设场景演示同样的流程。"

**Offline fallback:** Use Simulation Assistant only (no live API). All 23 scenarios run locally.

---

## What to Say About "不自动发送" and Human Confirmation

**Say explicitly:**

> "系统会生成草稿回复，但**不自动发送**。你确认、修改后再发。当AI从对话里收集了敏感信息——比如付款状态、VIN、驾照——会显示「Human confirmation recommended」，提醒你核对。"

**Point to:** The gold "Human confirmation recommended" badge when it appears.

---

## Post-Demo: Feedback Questions

Ask 3–5 of these:

1. **Which scenario felt most useful to your office?**
2. **Which part still feels risky or not trustworthy?**
3. **Would this save you or your assistant time?**
4. **What would you want it to do next?**
5. **What would you be willing to try first in a pilot?**

---

## One-Sentence Pilot Offer

> 试用一个月：帮你把客户发来的messy消息整理成结构化case，有下一步动作、收集了什么、还缺什么、草稿回复。你确认后再发，不自动发送。

---

## Quick Reference

| Item | Value |
|------|-------|
| URL | http://localhost:5173/workbench/unified-intake |
| Primary path | Load founder demo queue → Cancellation risk → Missing doc → Add-car |
| Backup path | Simulation Assistant → SIM1, SIM2, SIM3 |
| Top 3 scenarios | SIM1, SIM2, SIM3 |
| Pre-demo | `bash scripts/demo_pre_checklist.sh` |
| Guardrail | `bash scripts/guardrail_inbox_triage.sh` |

---

*See: `docs/CHEN_KUI_TRIAL_PACK.md`, `docs/UNIFIED_INTAKE_DEMO_READINESS.md`, `docs/runbooks/BROKER_VALUE_VALIDATION_MEETING_PACK.md`*
