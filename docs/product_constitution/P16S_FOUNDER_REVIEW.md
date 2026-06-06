# P16-S Phase 9 — Founder Review

**Date:** 2026-06-01  
**Sprint:** P16-S Failure Pattern Library + Post Sprint Health Check  
**Perspective:** Andy (founder) — honest post-mortem across P16-A through P16-R

---

## 1. What are our biggest recurring mistakes?

### Mistake A — Validating localhost, shipping confidence

We repeatedly closed sprints with guardrail PASS and local product_only success while Preview returned 401 SSO and Production showed a 41-day-old Add-Car UI. P16-J scored 74; P16-O scored 78 — both locally. P16-Q reality scored 64. **The engine worked; distribution did not.**

### Mistake B — Treating deploy as someone else's problem

Sprint definition of done was "code merged" not "broker can open URL." P16-O improved customer UX locally but did not reach Preview until P16-R — an entire sprint's value invisible externally. CLI-only Vercel deploys without dashboard env persistence made every redeploy a regression lottery.

### Mistake C — Re-diagnosing the same infrastructure failures

CORS blocked Preview for weeks (P16-F through P16-G). Preview SSO blocked trial for 8+ sprints (P16-E through P16-R). Each new sprint rediscovered these instead of fixing them once at the gate. **Whack-a-mole CORS** on every new Preview hash compounded the pain.

### Mistake D — Deferring 15-minute tasks that block 7-day trials

Andy authenticated Preview E2E log: cited since P16-C, still unchecked at P16-R. Invoice payment IDs: 10-minute task, empty across P16-K, L, Q, R. **Small founder tasks blocked commercial validation more than missing features.**

### Mistake E — Building UI before deleting UI

P16-H, M, N, O added improvements while demo card competed with paste, trust copy repeated 3×, and customer landing failed the 5-second test. Constitution said simplicity; sprints added surfaces. **Complexity creep without deletion discipline.**

---

## 2. Which mistake cost the most time?

**Local PASS → false deploy confidence (Mistake A + B combined).**

Estimated **~95 hours** on deploy/CORS/Preview re-work plus **~35 hours** on P16-Q/R reality re-validation sprints that existed only because we skipped cold-URL checks at sprint close.

Single most expensive incident: **CORS misdiagnosis P16-F through P16-G** (~25–30 hours) where Network Error was treated as product bug while guardrail passed locally.

Second: **P16-O local sprint without deploy** (~16 hours sprint + full Q revalidation).

Third: **Production frozen 41 days** — not hours of work, but **6 weeks of calendar trial delay**.

---

## 3. Which mistake blocked trial progress?

**Preview SSO (FP-004)** — #1 blocker.

Chen Kui cold score 12/100. Cannot send URL. Day 0 dead at link open. Every role simulation (Role C, Assistant, Skeptical Broker) failed at step 1.

**Compound blockers (all must clear for trial):**

| Blocker | Effect |
|---------|--------|
| Preview 401 | Cannot open product |
| Production wrong UI | Wrong link in any old doc kills trust |
| No E2E log | Founder cannot certify |
| Empty invoice IDs | Day 7 payment impossible |
| Zero trial days completed | No payment proof |

**Trial has been blocked at the front door, not the engine room.**

---

## 4. Which mistake almost caused false confidence?

### Incident 1 — P16-O "shippable" customer UX

Local 78/100. Verdict implied customer path ready. Preview lacked `请把您的需求发给我们`. P16-Q headline: **"P16-O lied by omission."** Founder could have sent customer link thinking UX was fixed.

### Incident 2 — P16-J acceptance scorecard 74

Ignored deploy entirely. Guardrail + localhost UI → "acceptance PASS." Preview still SSO-blocked with wrong bundle.

### Incident 3 — P16-F.5 partial GO after local CORS understanding

Founder Control dropped but sprint proceeded. Preview still broken for weeks after.

### Incident 4 — P16-K "commercial pack closed"

Docs existed; payment IDs empty; zero observation log entries. Could have reached Day 7 and had nothing to send.

**Pattern:** Any sprint verdict without cold-URL evidence creates false confidence risk.

---

## 5. What should never happen again?

| # | Never again | Prevention |
|---|-------------|------------|
| 1 | Sprint GO verdict with Preview returning 401 to cold curl | POST_SPRINT_HEALTH_CHECK P1 |
| 2 | UI sprint close without deployed bundle grep | FP-005, `--markers` in runner |
| 3 | "Trial ready" when only guardrail + localhost pass | REALITY_VALIDATION_CHECKLIST |
| 4 | CORS fix without `.env.cloudrun` sync | Environment C2 |
| 5 | Production >7 days behind Preview without documented defer | FP-013 alarm |
| 6 | Commercial sprint close with `[Andy Zelle` placeholders | CM2 grep |
| 7 | Capability score up locally without deployed proof | Constitution Enforcement Q8 |
| 8 | Starting next product sprint (P17) before parity checklist complete | P16-R gate |
| 9 | Sending broker URL Andy has not opened in incognito | Founder Q1 |
| 10 | Feature additions without TOP50 deletion execution | FP-007 |

---

## Founder commitment (operational)

What Andy must do differently:

1. **15 minutes:** Cold-open Preview in incognito before any "ready" statement.
2. **10 minutes:** Fill invoice payment IDs before any payment conversation.
3. **Zero:** Screen-share localhost as substitute for URL trial.
4. **Hand-off rule:** Broker clicks; Andy observes during trial week.

What the system must do (P16-S deliverables):

1. POST_SPRINT_HEALTH_CHECK mandatory — no exceptions.
2. FAILURE_PATTERN_LIBRARY as incident lookup.
3. `post_sprint_check.sh` when implemented — run before verdict.

---

## Emotional truth

The product is **better than it looks on the URL**. That is the most dangerous state for a founder-led trial. Brokers judge the link, not the localhost. P16-S exists so the next sprint closes the gap **before** Andy sees it, not after Chen Kui bounces.

---

*End of P16-S Phase 9 — Founder Review*
