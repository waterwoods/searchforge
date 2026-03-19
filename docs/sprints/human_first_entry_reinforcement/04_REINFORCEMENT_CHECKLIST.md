# Human-First Entry Flow Reinforcement — Checklist

**Sprint**: Human-First Entry Flow Reinforcement + Redeploy  
**Created**: 2026-03-15

---

## Priority 1: Answer-First / Next-Missing-Info

- [ ] Toyota Corolla quote: system acknowledges and asks for zip (or next missing)
- [ ] Payment failed notice: system acknowledges and asks for notice/screenshot
- [ ] Missing doc chase ("发过了"): system acknowledges and offers to verify
- [ ] Claim / hit-and-run: system acknowledges and asks for plate/photos
- [ ] No generic "内容不够完整" when intent is clear
- [ ] Asks 1–2 next things max, not 5+ at once

---

## Priority 2: Quick-Start Buttons as Real Starters

- [ ] Click "获取报价" with empty input → first quote reply
- [ ] Click "报事故" with empty input → first claim reply
- [ ] Click "付款 / 账单" with empty input → first payment reply
- [ ] Click "上传材料" with empty input → first missing-doc reply
- [ ] Click "保单变更" with empty input → first remove-car reply
- [ ] User feels "the system is helping me" after click

---

## Priority 3: Live Case Summary

- [ ] Summary card visible during intake (before handoff)
- [ ] Shows intent (主题)
- [ ] Shows collected fields (已收集)
- [ ] Shows still needed (还需)
- [ ] Updates after each turn
- [ ] Feels like real-time structured intake

---

## Priority 4: Startup Latency

- [ ] Perceived speed acceptable or cause documented
- [ ] Cold vs warm path distinguished
- [ ] LLM vs rule path distinguished
- [ ] Visible feedback during load ("正在整理 case...")
- [ ] Recommendation for next optimization (if any)

---

## Pre-Redeploy

- [ ] `run_inbox_triage_scenarios.py` — pass
- [ ] `guardrail_inbox_triage.sh` — pass
- [ ] `npm run build` — success
- [ ] No regressions in existing flows

---

*Use this checklist to explicitly verify each priority before claiming sprint success.*
