# P16-K Payment Readiness Audit

**Date:** 2026-06-01  
**Sprint:** P16-K — Commercial Pack  
**Persona:** Chen Kui (陈魁) — California auto broker owner  
**Product score (input):** ~74/100 (Sprint A accepted)  
**Authority:** `NORTH_STAR_V1.md` §8–9, `CAPABILITY_06_TRIAL_CONVERSION.md`

---

## Question 1 — "Why should I pay $49?"

### The honest answer today (before trial)

> 如果你一周里有 3–5 条紧急客户消息（取消通知、缺文件、付款失败），这个工具帮你：不用反复读微信、不用从头写回复。粘贴 → 看到「今天要处理什么、已经有什么、还缺什么、草稿回复」→ 你改一下复制到微信。  
> **$49/月 ≈ 不到一个助理一小时的钱。** 如果取消或缺文件这一类消息，每周能省 30 分钟以上，就值。

### Strength assessment: **Medium — conditional**

| Element | Status | Notes |
|---------|--------|-------|
| Value story (minutes on urgent messages) | ✅ Strong | North Star §8; cancellation-first wedge is credible |
| Price anchor ("less than 1 hr assistant") | ✅ Strong | Simple, broker-native framing |
| Proof on **his** real cases | ❌ Missing | Zero logged "worked" lines with minutes saved |
| Pricing visible before Day 7 | ⚠️ Fixed in P16-K | Was absent from v1 one-pager |
| Stable broker URL without founder | ❌ Missing | Preview SSO; Production frozen pre–Sprint A |
| Invoice + terms in hand | ⚠️ Fixed in P16-K | Templates created this sprint |

### Gaps blocking a confident $49 ask

| # | Gap | Severity |
|---|-----|----------|
| 1 | No completed 7-day trial with ≥1 real case + minutes saved | **P0** |
| 2 | No supervised Day 0 with first successful paste on Chen Kui's device | **P0** |
| 3 | Andy has not logged authenticated Preview E2E | **P0** |
| 4 | Production / Preview URL not broker-stable (SSO wall) | **P0** |
| 5 | Draft quality unproven on his real Chinese WeChat threads | **P1** |

---

## Question 2 — "Why should I pay $99?"

### The honest answer today (before trial)

> $99 是给整个办公室用的标准版：不只你一个人，助理也能用。取消、缺文件、加车报价至少两类场景都跑顺；队列帮你排「今天要处理」；草稿复制改两次以上，助理不用每条消息都问你。  
> **$99/月 = 一个办公室每天少花 10–15 分钟在重复读消息和写回复上。**

### Strength assessment: **Weak — not yet defensible**

| Element | Status | Notes |
|---------|--------|-------|
| Office-wide ROI story | ⚠️ Partial | Logical but unproven |
| Assistant adoption path | ❌ Missing | No assistant training script; Vercel login blocks assistant |
| 2+ scenarios worked | ❌ Missing | No trial evidence |
| Draft copied ≥2× with edits | ❌ Missing | Behavioral gate not met |
| Case persistence across sessions | ⚠️ Partial | API-proven; broker has not verified on prod URL |
| $99 vs $49 tier differentiation | ⚠️ Fixed in P16-K | Now documented; not yet tested in Day 7 conversation |

### Gaps blocking a confident $99 ask

| # | Gap | Severity |
|---|-----|----------|
| 1 | All $49 gaps above | **P0** |
| 2 | No assistant onboarding (15-min script) | **P1** |
| 3 | No evidence of 2+ scenario types on real cases | **P0** |
| 4 | No office-wide usage (assistant opened workbench) | **P1** |
| 5 | Tier choice feels arbitrary without trial data | **P1** |

---

## Payment readiness summary

| Price | Can Andy ask today? | Can Andy ask after Day 0? | Can Andy ask after Day 7? |
|-------|---------------------|---------------------------|---------------------------|
| **$49** | **No** — no proof, unstable URL | **Maybe** — if first paste works + terms sent | **Yes, if** ≥1 worked line + 30 min/week saved |
| **$99** | **No** | **No** — need multi-scenario proof | **Maybe** — if 2+ scenarios + assistant interest |

---

## What P16-K closes vs what remains

### Closed this sprint (commercial layer)

- $49 / $99 pricing on broker one-pager v2  
- 1-page pilot terms (Chinese)  
- Invoice templates ($49 / $99)  
- Observation log v2 with minutes-saved fields  
- Day 0 script + Day 7 payment checklist  
- Payment forecast + commercial scorecard  

### Still open (proof + deploy layer — not P16-K scope)

- Supervised Chen Kui 7-day trial  
- Preview redeploy + Andy authenticated E2E  
- Production promote with Sprint A bundle  
- First "worked" line with minutes saved  
- Testimonial quote  

---

## Verdict

**The $49 story is now tellable. It is not yet payable.**  
Chen Kui will not pay for a promise — he will pay for one week where cancellation or missing-doc saved him measurable time on real WeChat messages.

**The $99 story remains aspirational until assistant adoption and multi-scenario proof exist.**

---

*End of P16-K Payment Readiness Audit*
