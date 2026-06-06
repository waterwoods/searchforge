# TOP 20 Blockers to Payment — P11

**Scenario:** Chen Kui completes 7-day trial. Evaluate willingness to pay at **$49**, **$99**, and **$199/month**.  
**Payment method:** Manual invoice (Zelle/Venmo/WeChat) — no Stripe required for v1.

---

## Price sensitivity summary

| Price | Would Chen Kui pay? | Why |
|-------|---------------------|-----|
| **$49/mo** | **Maybe yes** — if one workflow clearly saved time | Low risk; "less than one hour of assistant time" |
| **$99/mo** | **Conditional yes** — default pilot anchor in docs | Needs proof on cancellation or missing doc; current P10 target |
| **$199/mo** | **Unlikely no** — unless multi-user + SLA + sync | No enterprise features to justify 2×; feels like unfinished CRM |

**Missing proof at any price:** Logged time savings on **real** messages, stable prod URL, cases that persist, draft used with edits at least twice.

---

## TOP 20 Blockers to Payment

| # | Blocker | Why it blocks | Fix |
|---|---------|---------------|-----|
| 1 | **No proven time savings on real cases** | Paying for hope | 7-day log: ≥3 real cases + "worked" lines |
| 2 | **Production URL not stable** | Won't pay for localhost | deploy_paid_pilot + weekly `/readyz` probe |
| 3 | **Cases lost on refresh** | Trust killer | Postgres-primary prod; no JSON fallback |
| 4 | **Draft quality inconsistent** | Faster to type in WeChat | Fix-now queue; chen_kui client pack tuning |
| 5 | **Manual paste feels like extra work** | No sync = no savings unless triage wins | Win cancellation speed; measure minutes |
| 6 | **Wrong first screen** | Never reached value → won't pay | Broker tab default |
| 7 | **Engineer UI artifacts** | "Beta / not for me" | Hide PG, API URL, debug tags |
| 8 | **No simple invoice / receipt** | Can't expense | PDF / WeChat invoice at $49/$99 tier |
| 9 | **No written pilot terms** | Data, cancel, support unclear | 1-page Chinese agreement |
| 10 | **Pricing not on one-pager** | "How much?" unanswered | Publish tier; recommend $99 pilot |
| 11 | **Downtime during business hours** | Can't rely Monday | intake_core + founder response SLA |
| 12 | **No onboarding call** | Needs 30-min walkthrough once | Day 0 kickoff in TRIAL_ONE_PATH |
| 13 | **Add-car vs cancellation mismatch** | Pays for triage; UI sells Add-Car | Align story or segment pricing |
| 14 | **Assistant can't adopt** | Single-user tool only | 15-min assistant training script |
| 15 | **No testimonial / reference** | Social proof for next broker | Capture Day 7 quote |
| 16 | **Data retention unclear post-trial** | Fear of losing cases | State in pilot terms |
| 17 | **Mobile UX weak** | Phone-first office | Desktop-only in terms OR mobile paste fix |
| 18 | **$199 expectations** | Expects WeChat sync + CRM at high tier | Don't offer $199 until features exist |
| 19 | **Founder-only support** | "What if broken?" | L1 doc + 24h response commitment |
| 20 | **ChatGPT free alternative** | "Why pay for drafts?" | Show case structure + queue + insurance scenarios |

---

## Price tier recommendation

| Tier | Position | Include | Chen Kui likelihood |
|------|----------|---------|---------------------|
| **$49/mo** | Starter pilot | Workbench, 1 office, founder support, manual invoice | Pay if cancellation saved 30+ min/week |
| **$99/mo** | Standard pilot (current anchor) | Same + priority support + case retention | Pay if 2+ scenarios worked + assistant uses it |
| **$199/mo** | **Do not sell yet** | Implies sync/SLA/multi-user — not built | Would churn in 30 days |

---

## What proof is missing before any payment

1. **Quantitative:** "Saved ~X minutes on cancellation case on [date]" — even one line  
2. **Behavioral:** Opened workbench ≥4 of 7 days; copied draft ≥2 times  
3. **Infrastructure:** Prod URL live; cases persist across sessions  
4. **Commercial:** Invoice + 1-page terms in broker's hands  
5. **Qualitative:** Day 7 answer "Would this save time?" = yes with specific example  

---

## What's already OK for v1 payment (any tier)

- Manual payment (no Stripe)  
- Single broker (no multi-tenant)  
- Copy-to-WeChat workflow  
- Coarse API keys (founder-managed)  
- No OAuth/SSO  

---

*End of payment blockers*
