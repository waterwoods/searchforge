# P16-Z2.5 Top 20 Mistakes

**Date:** 2026-06-01  
**Sprint:** P16-Z2.5 Product Soul Synthesis  
**Question:** What should never be repeated?

Ranked by damage × recurrence risk.

---

## 1. FP-004 — Sending Preview URL while SSO enabled

**Pattern:** Preview Protection (401 SSO Wall)  
**Damage:** Entire trial dead; Chen Kui cannot open URL  
**Never repeat:** Check `trial_launch_check.sh` and cold curl before any "URL is ready" claim.

---

## 2. Rebuilding existing capability

**Pattern:** Scope creep across sprints  
**Examples:** New conversation microservice, case intelligence microservice, customer portal from scratch  
**Never repeat:** Archaeology first — append API, CustomerEntryTab, OCR sidecar, risk scores already exist.

---

## 3. Starting P17 too early

**Pattern:** Platform/lab expansion before first payment  
**Damage:** Constitution violation; cognitive load; no pilot value  
**Never repeat:** P17 blocked until first paying customer and observation-log-driven scope.

---

## 4. FP-008 — Local PASS declared "shippable"

**Pattern:** Reality Gap (paper score ≠ deployed score)  
**Examples:** P16-J 74 local vs 52 deployed; guardrail PASS while broker never reaches engine  
**Never repeat:** Cold URL test on deployed environment before GO claim.

---

## 5. Overbuilding UI before deploy fixes

**Pattern:** UI complexity creep (FP-007)  
**Examples:** Full P16-M TOP50 sprint planned while SSO still on; customer tab before broker paste proven  
**Never repeat:** FP-004 + append CTA before UI purification sprint.

---

## 6. Commercial docs = payment ready (FP-009)

**Pattern:** Commercial Gap  
**Damage:** P16-K closed; invoice IDs still empty; zero observation log rows  
**Never repeat:** Fill payment IDs and start log row 1 same day docs ship.

---

## 7. Customer-first GTM before broker-first proof

**Pattern:** Wrong wedge order  
**Damage:** P16-N customer entry work while Cap 1 broker path blocked  
**Never repeat:** Chen Kui paste → copy → append before CustomerEntryTab on trial URL.

---

## 8. Guardrail PASS = trial ready

**Pattern:** Compound FP-008  
**Damage:** Cap 2 at 85 locally; broker cold score 12–43 on deployed  
**Never repeat:** Guardrail + cold URL + founder E2E log = minimum deploy gate.

---

## 9. Commit without deploy (FP-005)

**Pattern:** Not Deployed  
**Examples:** P16-O verdict without deploy; Sprint A UI not on Preview  
**Never repeat:** Deploy verification in same sprint as code acceptance.

---

## 10. Inflating scores until follow-up observed

**Pattern:** P16-X explicit warning  
**Damage:** Cap 5/6 scores overstated; unsupervised trial launched prematurely  
**Never repeat:** Cap 5 stays ≤55 until two-turn real case logged.

---

## 11. Building OCR-first primary intake

**Pattern:** Constitution frozen (P16-L)  
**Damage:** Distraction from paste wedge; Vision API exists as sidecar  
**Never repeat:** Paste-first trial; OCR wire on broker upload week 2 only.

---

## 12. Maintaining SimulationAssistant.tsx

**Pattern:** Duplication waste  
**Damage:** Confusion across role simulation sprints; zero usage  
**Never repeat:** ScenarioReplayTab is lab tool; delete orphan.

---

## 13. Feature sprint during trial window

**Pattern:** P16-L explicit NO-GO  
**Damage:** Observation log captures friction; building during trial prevents evidence collection  
**Never repeat:** Observation-log-driven fixes only during 7-day trial.

---

## 14. Email Preview/Production URL to broker unsupervised

**Pattern:** FP-010 Founder Assumption  
**Damage:** Day 0 dead on login wall or wrong UX bundle  
**Never repeat:** Supervised Day 0 only until two-turn case logged.

---

## 15. Adding category buttons before message (customer landing)

**Pattern:** P16-N diagnosis  
**Damage:** 5-second test 33/100; 6 intent choices before describing problem  
**Never repeat:** Message-first, one button, Stripe/Calendly pattern.

---

## 16. English mixed in Chinese office glance

**Pattern:** F-005 friction  
**Damage:** Chen Kui trust break; broker_next_step in English on product_only  
**Never repeat:** Chinese-only glance for trial deploy.

---

## 17. Third demo pack runner / redundant batteries

**Pattern:** Operator path bloat  
**Damage:** Cognitive load; 197 lab scripts  
**Never repeat:** guardrail + p16y battery = canonical QA.

---

## 18. Assuming CORS fix local = Preview fixed (FP-001)

**Pattern:** Deployment Parity Failure  
**Damage:** P16-F.5 partial GO; Preview still broken remotely  
**Never repeat:** Post-deploy CORS hook + cold origin test.

---

## 19. Building Stripe billing in pilot

**Pattern:** Out of scope per constitution  
**Damage:** Engineering weeks for manual Zelle/Venmo/WeChat invoice  
**Never repeat:** Manual invoice + observation log until 3+ paying offices.

---

## 20. Treating copy-as-exit as acceptable product shape

**Pattern:** P16-X single-turn trap  
**Damage:** Cap 5 at 41; users never learn append path  
**Never repeat:** Post-copy continuation sentence is mandatory on every deploy.

---

*End of P16-Z2.5 Top 20 Mistakes*
