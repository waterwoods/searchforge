# Founder Inspection Notes

**Sprint:** Broker Trial Simulation + Fix Queue Hardening Sprint  
**Created:** 2026-03-19

---

## 1. What Founder Should Inspect When Back

1. **Sprint report** — `docs/sprints/BROKER_TRIAL_SIMULATION_FIX_QUEUE_HARDENING/BROKER_TRIAL_SIMULATION_FIX_QUEUE_HARDENING_REPORT.md`
2. **Fix queue** — fix-now / fix-next / defer in report
3. **Strongest flows** — What stayed strong; preserve
4. **Weakest flows** — What to watch in real trial
5. **Applied fixes** — If any; what improved

---

## 2. What Strongest / Weakest Results Matter Most

| Strong | Why |
|--------|-----|
| Cancellation risk | Urgency; first demo case |
| Add-car multi-turn | Revenue; Collected chips |
| Missing document | Operational; "already sent" |
| Append flows | Case continuation |

| Weak | Why |
|------|-----|
| Talk to Agent | Trust-breaking if wrong |
| Vague/short | Real messages are short |
| Mixed intent | Real-world messiness |
| Correction visibility | Broker may miss |

---

## 3. What Founder Should Manually Test First on Vercel

1. Load founder demo queue — cancellation opens first
2. Run SIM1 (Cancellation risk) — 3-turn
3. Run SIM2 (Missing document) — 3-turn; reopen from Recent
4. Run SIM3 (Add-car) — 3-turn; Collected/Still needed
5. Paste "联系人工" — verify routes to talk_to_agent
6. Append flow — add message to existing case; verify context preserved

---

## 4. Redeploy Status

- **Backend:** If triage/config changed — redeploy needed
- **Frontend:** If UI changed — redeploy needed
- **Config:** Static; no env — no redeploy for config-only

---

*End of Founder Inspection Notes*
