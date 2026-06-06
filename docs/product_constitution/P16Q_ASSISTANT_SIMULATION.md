# P16-Q Phase 5 — Assistant Simulation

**Date:** 2026-06-01  
**Persona:** Office assistant — 50+ WeChat threads/day; executes broker instructions; no technical patience  
**Method:** Broker workbench code path + P16-I UX + deploy reality  
**Needs:** Quick triage · draft · follow-up · continuity

---

## Need 1 — Quick triage

**Goal:** Sort what needs action today without re-reading every thread.

| Feature | Reality |
|---------|---------|
| Queue with urgency | ✅ Works locally — filters 需今天处理 / 24小时内 |
| Cancellation same-day signal | ✅ Visible on cards |
| Open queue from phone | ⚠️ **Not validated** — no mobile test this sprint |
| Open queue from Preview URL | ❌ **401 SSO** — assistant cannot onboard alone |

**Assistant time-to-orient:** ~45s locally · **∞** on Preview (blocked).

**Friction:** Empty queue until broker loads demo or pastes — assistant arriving cold sees "nothing here."

---

## Need 2 — Draft

**Goal:** Copy-ready reply to paste back into WeChat.

| Feature | Reality |
|---------|---------|
| 复制客户草稿 single primary | ✅ product_only |
| Draft quality Chinese threads | ⚠️ Mixed English output on some pastes |
| Find draft on long case | ⚠️ Scroll required |
| Trust 不自动发送 | ✅ Reduces fear of auto-reply |

**Friction:** Still faster to type 3-line WeChat reply for **routine** messages — tool wins on **complex** cancellation/missing-doc only.

---

## Need 3 — Follow-up

**Goal:** Track waiting on client; append new customer message; set next contact.

| Feature | Reality |
|---------|---------|
| 追加客户补充 (promoted) | ✅ Near glance |
| Follow-up plan fields (waiting_on, next_contact_by) | ⚠️ Lower in detail panel — hunt required |
| Follow-up paste templates | ⚠️ Exists but not primary CTA |
| WeChat reminder integration | ❌ None |

**Friction:** Two places for "what's next" — card `broker_next_step` vs follow-up plan section.

---

## Need 4 — Continuity

**Goal:** Pick up yesterday's case; know what's still open.

| Feature | Reality |
|---------|---------|
| Case persistence | ✅ API/local |
| Reopen from queue | ✅ |
| Stable URL tomorrow | ❌ Preview SSO / Production wrong |
| Customer append → office sees update | ✅ API path — if broker monitors queue |

**Friction:** Without daily URL reliability, assistant rebuilds mental model in WeChat instead.

---

## Adoption probability

| Scenario | Probability |
|----------|-------------|
| Chen Kui **mandates** + stable URL + 15-min training | **55%** Month 1 |
| Chen Kui mentions as optional | **20%** |
| Preview URL sent to assistant | **5%** — login wall |
| Mandate + Production URL | **10%** — wrong UI, loses trust |

### **Adoption probability (trial reality): 22 / 100**

(P16-G was 50/100 assuming CORS fixed + mandate — **deploy access cuts that in half**.)

---

## Assistant scorecard

| Dimension | Score |
|-----------|-------|
| Triage speed (when in app) | **72** |
| Draft utility | **65** |
| Follow-up workflow | **58** |
| Continuity / URL | **25** |
| Mobile / WeChat fit | **30** |
| **Overall assistant** | **50 / 100** |

---

## Verdict

Assistant **will not adopt** without broker mandate **and** a URL that loads on first tap. Tool is **$99-tier evidence**, not $49-tier. Do not bundle assistant success into Week 1 trial metrics.

---

*End of P16-Q Phase 5 — Assistant Simulation*
