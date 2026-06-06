# P16-L Top 20 Trial Risks

**Date:** 2026-06-01  
**Sprint:** P16-L — Real Market Validation  
**Method:** Ranked by Probability × Impact on first payment evidence  
**Scale:** Probability H/M/L · Impact Critical/High/Med/Low

---

## Ranked risks

| Rank | Risk | P | I | Score | Mitigation |
|------|------|---|---|-------|------------|
| **1** | **No real usage** — demo only, zero real WeChat pastes | H | Critical | **P0** | Day 0 mandate real paste; Day 1 ping if empty; invalidates trial if persists |
| **2** | **Broker-stable URL missing** — Preview SSO or Production wrong UX | H | Critical | **P0** | Redeploy Preview + Andy E2E before Day 0; screen-share fallback; never send Production |
| **3** | **Trial forgotten** — no Day 2+ opens without reminder | H | High | **P0** | Book Day 3 + Day 7 upfront; one async ping Day 2; log "Continue tomorrow?" daily |
| **4** | **Founder over-helping** — Andy clicks, defends, rewrites | M | Critical | **P0** | Log Founder assisted? per case; async-only Days 1–6; don't rewrite drafts |
| **5** | **No value moment** — broker doesn't see cancellation urgency win | M | Critical | **P0** | Day 0: demo queue → real cancellation paste; measure minutes together |
| **6** | **Draft quality issue** — 大改 or 没用 on real Chinese threads | M | High | **P1** | Log edit level; count structure value if draft fails; fix-now only post-Day 7 |
| **7** | **Paste fatigue** — "easier to just reply in WeChat" | M | High | **P1** | Focus on urgent scenarios only; don't ask routine messages; track minutes saved |
| **8** | **Wrong workflow expectation** — broker expected sync/OCR/auto-send | M | High | **P1** | One-pager §4 + Day 0 reset; log fit risk if hard no |
| **9** | **No follow-up** — broker never uses 追加客户补充 or reopen | M | Med | **P1** | Day 3 checkpoint explicitly demo follow-up; log Partial if one-shot only |
| **10** | **Trust-breaking triage** — wrong urgency on cancellation | L | Critical | **P1** | Don't defend; log case ID; fix-now or kill; one strike may end trial |
| **11** | **English draft on Chinese paste** | M | Med | **P2** | Set expectation Day 0; broker edits; log friction not deal-breaker unless every case |
| **12** | **Demo card competes with paste** | M | Med | **P2** | Day 0 script: demo first 5 min, then real paste; don't fix UI during trial |
| **13** | **API cold start / timeout** | M | Med | **P2** | Loading copy exists; fallback to demo queue; log outage days separately from abandonment |
| **14** | **Assistant not involved** — blocks $99, not $49 | H | Med | **P2** | Don't push $99; optional assistant observation; lead $49 |
| **15** | **Case persistence doubt** — broker doesn't trust reopen | L | Med | **P2** | Day 3 reopen exercise; screenshot queue with cases |
| **16** | **Invoice details unfilled** | M | Med | **P2** | Andy fills Zelle/Venmo/WeChat before Day 0 |
| **17** | **Andy Preview E2E gap** — deploy ≠ local | M | High | **P1** | 15-min logged walkthrough before broker URL sent |
| **18** | **Over-promising on Day 7** — invoice when gates fail | L | Critical | **P1** | `P16L_PAYMENT_EVIDENCE_MODEL.md` — ≥3 gates or no ask |
| **19** | **Feature request during trial** — "add WeChat sync" | M | Med | **P2** | Log in Q4; defer to P16-L feature freeze; don't build |
| **20** | **Kill without data** — broker ghosts, no log | M | High | **P1** | Minimum Day 3 check-in; partial log better than silence; classify as abandonment |

---

## Risk heat map

```
Impact
  Critical │ 2 URL    4 Over-help   5 No value   10 Triage   18 Over-promise
           │ 1 No real usage
  High     │ 3 Forgot  6 Draft     7 Paste      8 Wrong WF   17 E2E gap   20 Ghost
  Med      │ 9 Follow  11 English  12 Demo      13 API       14 Asst      16 Invoice  19 Feature
  Low      │ 15 Persist
           └─────────────────────────────────────────────────────────────
             Low        Med        High       Probability
```

---

## Top 5 mitigations (do before Day 0)

| # | Action | Closes risk |
|---|--------|-------------|
| 1 | Preview redeploy + Andy E2E log | #2, #17 |
| 2 | Fill invoice payment IDs | #16 |
| 3 | Send packet + book Day 0, 3, 7 | #3, #20 |
| 4 | Day 0 script: real paste required | #1, #5 |
| 5 | Founder intervention rules in trial plan | #4 |

---

## Risks explicitly NOT mitigated by building

| Tempting fix | Why not during P16-L |
|--------------|----------------------|
| WeChat sync | Constitution anti-goal; changes fit hypothesis |
| OCR upload | Same |
| Stripe | Same |
| New UI sprint | Invalidates validation |
| Prompt tuning mid-trial | Confounds evidence |

Fix-now queue **only after Day 7** with logged case IDs.

---

## Early warning signals (Day 1–3)

| Signal | Likely rank | Action |
|--------|-------------|--------|
| Day 1 no open | #3 | One ping; diagnose URL vs forget vs no messages |
| Day 1 open, no paste | #7, #12 | 5-min async: paste one cancellation |
| Draft 大改 on first real case | #6 | Log; continue if structure helped |
| "我直接微信回就行了" | #7, #8 | Focus urgent only; measure minutes on one case |
| Founder assisted on every case | #4 | Step back Days 2–7 |

---

*End of P16-L Top 20 Trial Risks*
