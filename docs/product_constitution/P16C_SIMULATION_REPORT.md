# P16-C Phase 3 — AI Simulation Report

**Date:** 2026-05-31  
**Input:** Live local product_only UI (`c2e3dff`), production baseline browser compare, guardrail PASS, `/readyz` intake_path_ready  
**Method:** Structured persona simulation — first session journey with confusion / abandonment tracking  
**North Star:** Broker understands and trusts product in under 5 minutes without founder translation

---

## Simulation A — New Broker Owner

**Prompt:** *"I received this URL from Andy. I have never seen this product before."*

### Journey

| Time | Observation |
|------|-------------|
| **0:00–0:30** | Opens URL. Lands on **办公室工作台** (not Add-Car portal). Sees 金盾·陈魁团队 branding — assumes it's Chen's office tool, not a generic SaaS signup. |
| **0:30–1:00** | Reads wayfinding: 「经纪人：请在本页粘贴客户消息」. Understands manual paste. **Minor confusion:** header card still says 加车报价 flagship — "Is this for quotes or messages?" |
| **1:00–2:00** | Notices 「练习场景」 panel. Clicks **取消/付款风险** — sample loads in paste box. **Relief:** doesn't need WeChat sync. |
| **2:00–3:00** | Clicks 「加载演示队列」. On local preview: **Network Error / CORS** — queue empty. **Abandonment risk:** "Is it broken?" |
| **3:00–5:00** | If API works: would see cancellation case + 下一步 + draft. On broken deploy: clicks 客户报送 tab — **wrong-path regression** (Add-Car form). |
| **Day 1** | Without founder: can paste + practice if backend reachable. Without demo queue: may not see cancellation value. Pricing/terms absent → "What does this cost?" |
| **Day 7** | Needs ≥3 real cases + draft copied 2×. Front door no longer blocks; **proof of minutes saved** still missing. |

### Confusion points

1. Add-Car tagline on header despite landing on broker tab  
2. Two tabs — 客户报送 still tempts click  
3. CORS/network error = instant "broken product"  
4. Empty queue — no visible filters until cases exist  
5. No pricing on screen (Sprint B scope)

### Abandonment points

1. Demo queue fails (CORS / API down) at ~2 min  
2. Wrong tab (客户报送) if broker explores  
3. First paste 30s wait without warming message (if cold backend)  
4. No visible outcome after 5 min if neither demo nor paste attempted  

### Scores (0–100)

| Horizon | Score | Rationale |
|---------|-------|-----------|
| **First 30 seconds** | **72** | Correct tab + wayfinding = orientation win vs 15 pre-Sprint A |
| **First 5 minutes** | **58** | Practice scenario works; demo queue failure on misconfigured origin caps score |
| **Day 1** | **65** | Usable unsupervised for paste path; demo path unreliable without deploy |
| **Day 7** | **40** | No trial evidence, pricing, or persistence proof — commercial layer unchanged |

---

## Simulation B — Office Assistant

**Prompt:** *"I have 100 unread WeChat messages."*

### Journey

| Time | Observation |
|------|-------------|
| **0:00–0:30** | Same entry as broker — **good** for shared office workflow. Immediately sees paste area, not customer portal. |
| **0:30–1:00** | Scans for queue / priority. Empty queue: 「暂无服务记录」 — **anxiety:** "Where are my 100 messages?" (paste-only model not spelled out loudly enough for volume worker). |
| **1:00–2:00** | Finds 「需今天处理」 filter concept in copy (filters appear when queue populated). Mental model: one message at a time, not inbox sync — **partial mismatch** with "100 unread" expectation. |
| **2:00–3:00** | Uses 「取消/付款风险」 practice → paste → would click 开始整理. Loading copy helps patience. |
| **3:00–5:00** | If triage works: sees urgency + 下一步 on card — **value visible**. Queue scan with broker_next_step previews would help triage 100 messages — **not testable** empty queue. |
| **Day 1** | Could process messages sequentially if trained on paste loop. Missing: prominent 「更新客户新消息」 for follow-ups (Sprint C). |
| **Day 7** | ROI depends on broker also using tool + persistence. Assistant adoption = 2× office ROI per North Star — not proven. |

### First action

**Expected:** Paste highest-urgency cancellation message → 开始整理.  
**Actual likely:** Click 加载演示队列 first (demo discovery) → error on bad deploy → paste second.

### Understanding

- **Paste workflow:** Understood via wayfinding ✅  
- **100-message inbox:** Not supported — manual one-at-a-time ⚠️  
- **Queue priority:** Designed but not visible empty  

### Perceived value

- **High** if cancellation triage saves re-read time on each paste  
- **Low** if expecting WeChat sync or bulk import  

### Scores (0–100)

| Horizon | Score | Rationale |
|---------|-------|-----------|
| **First 30 seconds** | **70** | Correct tab; volume worker may want inbox metaphor |
| **First 5 minutes** | **62** | Practice path clear; empty queue weak for "100 messages" framing |
| **Day 1** | **60** | Repeat paste viable; no bulk workflow |
| **Day 7** | **55** | Needs measured time savings + follow-up paste prominence |

---

## Simulation C — Chen Kui (Broker Owner)

**Prompt:** *"I only care whether this saves my office time."*

### Journey

| Time | Observation |
|------|-------------|
| **0:00–0:30** | Sees own team name (金盾·陈魁团队). **Trust bump** — not anonymous AI demo. Lands on workbench, not customer portal. |
| **0:30–1:00** | Reads 「不自动对外发送」 — aligns with his control requirement. No PG/API junk — **"maybe production-ready"** signal. |
| **1:00–3:00** | Demo queue or cancellation practice → structured case + draft. **First value moment** if API works. English draft on payment-failed edge case would erode trust (engine gap, not Sprint A). |
| **3:00–5:00** | Asks: "Does this save 30 min/week?" — **cannot answer from UI alone**. Needs 7-day log. Add-Car tab suffix still annoys: "Andy said cancellation-first." |
| **Day 1** | Would trial if Andy supervises kickoff. Unsupervised: ~71 vs 28 pre-Sprint A — **material improvement**. |
| **Day 7** | Pays $49 if one workflow proved ~30 min/week saved. Pays $99 if assistant uses + 2 scenarios + drafts copied. **No payment without observation log.** |

### Trust

| Signal | Effect |
|--------|--------|
| Team branding | + |
| No engineer chrome | + |
| No auto-send | + |
| Network error on demo | −− |
| Add-Car copy mismatch | − |
| No pricing/terms | − |

### Willingness to trial

**Before Sprint A:** Low unsupervised (28/100 P11).  
**After Sprint A:** **Moderate–High with founder kickoff; Low–Moderate URL-only** until Preview deploy verified.

### Willingness to pay

**Unchanged commercially:** Still **No at Day 0**.  
**Conditional at Day 7:** **Maybe $49** if cancellation minutes logged; **Maybe $99** if 2+ scenarios + assistant.

### Scores (0–100)

| Horizon | Score | Rationale |
|---------|-------|-----------|
| **First 30 seconds** | **78** | Trust + orientation vastly improved |
| **First 5 minutes** | **68** | Value path exists; deploy/copy gaps remain |
| **Day 1** | **71** | Matches P11 kickoff+fixes trajectory without founder on screen |
| **Day 7** | **45** | Payment requires proof layer Sprint B + trial — unchanged |

---

## Aggregate Simulation Summary

| Simulation | First 30s | First 5 min | Day 1 | Day 7 |
|------------|-----------|-------------|-------|-------|
| A — New broker owner | 72 | 58 | 65 | 40 |
| B — Office assistant | 70 | 62 | 60 | 55 |
| C — Chen Kui | 78 | 68 | 71 | 45 |
| **Average** | **73** | **63** | **65** | **47** |

**5-minute North Star test (weighted C 50%, A 30%, B 20%):** **64 / 100** — below 70 threshold when deploy friction included; **72 / 100** if demo queue E2E works on Preview.

---

## Simulation Verdict

Sprint A **materially improves first 30 seconds and Day 1 orientation** for all three personas. **5-minute value** depends on backend reachability and demo queue — not yet proven on Vercel Preview. **Day 7 / payment** unchanged — requires trial execution, not UI sprint.

---

*End of P16-C Phase 3 — AI Simulation Report*
