# Trial Execution — 18-Point Breakdown

**Sprint:** Founder / Broker Trial Execution Sprint  
**Created:** 2026-03-20

1. **Why this trial matters now** — Bones exist; integration + trust is the bottleneck.  
2. **Customer-side testing** — Quick starts, first reply tone, multi-turn Add-Car, human handoff, mixed messages.  
3. **Workbench-side testing** — Queue scan, case open, `broker_next_step`, quote-ready/contact/materials signals, append/activity.  
4. **Page backbone success** — Intake hub reads as a formal customer front door, not a dev console.  
5. **Flow backbone success** — Scenarios progress without dead ends; reroute feels helpful.  
6. **State backbone success** — Quote-ready / almost-ready / need-more and follow-up fields match broker language.  
7. **Handoff backbone success** — Office packet is scan-friendly: summary + next action + collected/still-needed.  
8. **Trust-breaking issue** — Wrong urgency, fake “saved,” generic next step on a primary path, client sees internal jargon.  
9. **Acceptable-for-trial issue** — Extra click, minor template variance, broker would still act correctly.  
10. **Fix-now** — High trust impact + small safe change (e.g. validation lie, persistence guardrail, critical wording).  
11. **Fix-next** — Noticeable friction; schedule after first broker conversations.  
12. **Defer** — OCR, rating APIs, CRM, multi-channel inbox, enterprise workflow.  
13. **Most improves broker trust** — Concrete `broker_next_step` + correct urgency on risk.  
14. **Most improves commercial believability** — Client-facing copy and quote-ready clarity on Add-Car.  
15. **Most reduces rework** — Structured collected/still-needed + materials/already-sent handling.  
16. **Simulations / flows needed** — Guardrail packs + multi-turn + broker stress + handoff timing + Simulation Assistant.  
17. **Founder manual inspection** — Customer tab 5 min, workbench scan, open Add-Car + payment + missing-doc cases.  
18. **“Ready for broker review”** — Guardrail green, no unowned trust-breaker, flagship paths demo without apology.

---

*End of breakdown*
