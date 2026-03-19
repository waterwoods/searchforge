# Client Variation Demo Spec

**Sprint:** Client Configuration Wiring Sprint  
**Created:** 2026-03-18

---

## 1. How to Prove Client A vs Client B Variation

1. **URL:** `?client=chen_kui` vs `?client=demo_broker`
2. **Observe:** Header title, tab labels, welcome message, quick-start buttons, handoff success message

---

## 2. Exact Screens That Should Look Different

| Screen | Chen Kui | Demo Broker |
|--------|----------|-------------|
| Header | 保险经纪人智能助手 | 保险经纪助手 Demo |
| Tab label | 办公室工作台 — 办公室 | 客服团队工作台 — 客服团队 |
| Welcome | 您的消息会直接转给办公室 | 您的消息会直接转给客服团队 |
| Talk to agent button | 我想联系陈奎办公室 | 我想联系客服 |
| Handoff success | 办公室会尽快处理，有结果会联系您。 | 客服团队会尽快处理，有结果会联系您。 |

---

## 3. What Founder Should Show

1. Open `/workbench/unified-intake` — default Chen Kui
2. Open `/workbench/unified-intake?client=demo_broker` — different branding
3. Say: "Same product, different client config. New broker = new folder, no code change."

---

## 4. Simple Reuse Story

> "We have one base. One industry template (insurance). Multiple client configs. To add a new broker, we create a folder in configs/clients/<broker_id>/ with their ui_copy and handoff phrases. No code change."
