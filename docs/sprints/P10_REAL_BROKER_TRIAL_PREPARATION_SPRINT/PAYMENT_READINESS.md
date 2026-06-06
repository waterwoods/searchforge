# Payment Readiness — TOP 20 Blockers to First $99/Month

**Scenario:** Chen Kui says: *"I will pay $99/month if this saves me time."*

**Scope:** Manual payment (Zelle/Venmo/WeChat) acceptable per paid-pilot goal. No Stripe required for v1.

---

| # | Blocker | Why it blocks payment | Fix |
|---|---------|----------------------|-----|
| 1 | **No proven time savings on real cases** | Paying for hope, not evidence | Complete 7-day trial with 3+ real cases + logged time saved |
| 2 | **Production URL not stable** | Won't pay for localhost or broken Vercel | deploy_paid_pilot + Vercel prod verified weekly |
| 3 | **Cases lost on refresh / multi-device** | Trust killer | Postgres-primary prod deploy; no JSON fallback |
| 4 | **Draft quality inconsistent** | "Still faster to type in WeChat" | Fix-now queue from trial; tune chen_kui client pack |
| 5 | **Manual paste feels like extra work** | No sync = no savings unless triage is clearly faster | Win on cancellation + missing doc speed; measure |
| 6 | **No simple invoice / receipt** | Business need for records | PDF or WeChat invoice template ($99/mo pilot) |
| 7 | **No written pilot terms** | What happens to data, cancel policy, support hours | 1-page pilot agreement (Chinese) |
| 8 | **UI engineer artifacts (PG, API URL)** | "This isn't finished" | Product-only UI cleanup |
| 9 | **Wrong first screen (Customer Entry)** | Never reaches value | Broker tab default |
| 10 | **Downtime during business hours** | Can't rely on it Monday | intake_core readiness + monitoring + founder response SLA |
| 11 | **No onboarding call completed** | Chen Kui needs 30-min walkthrough once | Founder Day 0 kickoff (in playbook) |
| 12 | **Add-car vs cancellation expectation mismatch** | Pays for triage; UI sells Add-Car portal | Align product story or segment pricing by workflow |
| 13 | **Assistant can't use without training** | Office adoption = 1 user only | 15-min assistant training script |
| 14 | **No testimonial / reference** | Social proof for next broker | Capture quote at Day 7 if positive |
| 15 | **Pricing not on one-pager** | "How much after trial?" unanswered | Add $99/mo pilot line to BROKER_ONE_PAGER |
| 16 | **Data retention unclear post-trial** | Fear of losing cases | State retention in pilot terms |
| 17 | **No API key / access boundary** | Security concern for office | Document: founder manages keys; broker uses UI only |
| 18 | **Mobile UX weak** | Brokers live on phone | Accept for v1 OR flag desktop-only in terms |
| 19 | **Cancellation path not demo-ready on prod** | Primary pain = payment notices | Ensure demo queue + real paste work on prod |
| 20 | **Founder-dependent support** | Can't pay if only one person can fix it | Document L1 responses; 24h response commitment |

---

## What Chen Kui needs to say yes (minimum)

1. Used it on **real** messages for a week  
2. At least **one** scenario (cancellation or missing doc) clearly saved time  
3. **Stable URL** + cases persist  
4. **$99 invoice** + 1-page terms  
5. Knows how to get help within **24 hours**

---

## What's already OK for v1 payment

- Manual payment (no Stripe)  
- Single broker (no multi-tenant)  
- No OAuth/SSO  
- Coarse API keys (founder-managed)  
- Copy-to-WeChat workflow (no auto-send)

---

*End of payment readiness*
