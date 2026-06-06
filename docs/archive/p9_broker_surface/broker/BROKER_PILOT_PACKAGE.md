> **HISTORICAL / ARCHIVE — P9 Broker Surface Collapse (2026-05-30)**
> **Read instead:** [`docs/BROKER_ONE_PAGER.md`](../../../BROKER_ONE_PAGER.md), [`docs/BROKER_DEMO_FLOW.md`](../../../BROKER_DEMO_FLOW.md), [`docs/BROKER_TRIAL_PLAYBOOK.md`](../../../BROKER_TRIAL_PLAYBOOK.md)

# Broker Pilot Package

**Phase**: Broker Pilot Core  
**Target user**: California auto insurance broker (e.g., 陈魁)  
**Goal**: Turn demo into pilot-worthy product for first paid trial

---

## 1. Pilot scope (v1)

### Included

| Item | Description |
|------|--------------|
| **5 recommended questions** | 新车投保、注册恢复、合规查询、省钱/折扣、理赔流程 |
| **Answer structure** | 简短结论 → 官方依据 → 下一步建议 → 可直接转发给客户 |
| **Copy-to-client** | One-click copy, WeChat-ready format, client-friendly tone |
| **Offline fallback** | Preset answers when backend down; demo always works |
| **Scenario tags** | 新车投保、注册恢复、合规查询、省钱/折扣、理赔流程 |
| **Local + offline paths** | Live Qdrant or preset JSON; no Cloud dependency for demo |

### Not included (v1)

| Item | Reason |
|------|--------|
| Stripe / payment integration | Manual Zelle/Venmo/WeChat for first pilot |
| Multi-tenant auth | Single broker |
| LLM answer generation | Retrieval + extraction sufficient; LLM optional |
| China / Europe regions | California only |
| Agent workflows | Retrieval-only sufficient |

---

## 2. Broker onboarding (3 steps)

1. **Access**: Open `http://localhost:5173/demo` (or deployed URL)
2. **Try**: Click 5 recommended questions; copy answer to WeChat
3. **Ask**: Type any California auto insurance question in Chinese or English

---

## 3. Demo-to-pilot transition

| Before pilot | After pilot |
|--------------|-------------|
| Demo mode, free | Same product; broker pays manually |
| No terms | One-pager terms in email |
| No support SLA | WeChat/email support |
| Manual deploy | Same; no change |

---

## 4. Proposal-ready pricing placeholder

**Suggested wording for broker proposal:**

> 加州汽车保险经纪助手 — 试用方案  
> 
> - **试用期**: 1 个月  
> - **费用**: $XX/月（可协商）  
> - **包含**: 5 类常见问题快速答复、官方来源链接、可直接转发客户的话术  
> - **支付**: Zelle / Venmo / 微信  
> - **支持**: 微信 / 邮件

*Replace $XX with actual amount. No payment integration in v1.*

---

## 5. Key file paths

| Purpose | Path |
|---------|------|
| Demo UI | `ui/src/pages/DemoPage.tsx` |
| Copy-to-client logic | `ui/src/utils/demoCopy.ts` |
| Offline fallback data | `ui/src/assets/demo_fallback.json` |
| Snapshot script (refresh offline pack) | `scripts/snapshot_demo_answers.py` |
| Query API (demo mode) | `services/fiqa_api/routes/query.py` |
| Business rules | `docs/business_rules/insurance_broker_pilot_rules.md` |

---

*End of pilot package*
