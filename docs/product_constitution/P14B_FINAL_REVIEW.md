# P14-B Final Review — Constitution Ratification

**Sprint:** P14-B Constitution Ratification  
**Date:** 2026-05-31  
**Inputs:** P10, P11, P14-A discovery pack, ratified V1 documents (North Star, Capability Map, 7 contracts, Scorecard, Roadmap)  
**Note:** P13 does not exist in repository. P10/P11 are the latest discovery sprints.

---

## 1. Is the North Star Clear?

**Yes.**

One sentence is locked:

> Turn messy California auto insurance customer messages into office-ready service records so brokers handle urgent work faster — with drafts they review before sending.

Supporting clarity:

- **Who pays:** Broker owner at $49–99/month  
- **Wedge:** Cancellation-first (not Add-Car portal)  
- **Loop:** Paste → case → draft → you send  
- **Anti-goals:** 10 items locked for 90 days  

**Residual ambiguity:** Add-Car portal still exists as secondary surface — constitution resolves this as "not sales lead," but UI must align in implementation sprint.

**Verdict:** North Star is clear enough to reject scope creep. Weekly anti-drift tests are actionable.

---

## 2. Are the 7 Capabilities Complete?

**Yes — with explicit merges documented.**

The seven capabilities cover the full paste → pay loop:

| # | Capability | Covers |
|---|------------|--------|
| 1 | Broker Front Door | UX entry, trust, first value |
| 2 | Urgent Message Triage | Engine / classification |
| 3 | Structured Case Record | Case card + draft |
| 4 | Customer Intake Collection | Paste mechanism |
| 5 | Case Lifecycle Management | Queue, reopen, light identity |
| 6 | Trial Conversion | 7-day proof → payment |
| 7 | Founder / Operator Control | Guardrails, deploy, gates |

P14-A proposal's Draft Generation and Customer Identity are **merged** into Capabilities 3 and 5 respectively — scope preserved, count stays 7.

---

## 3. Is Anything Duplicated?

**Minor overlap — intentional, bounded:**

| Overlap | Capabilities | Resolution |
|---------|--------------|------------|
| Default tab / wayfinding | Front Door + Intake Collection | Front Door owns UX path; Intake owns paste mechanism |
| Draft quality | Triage + Case Record | Triage generates; Case Record presents and owns draft UX |
| Demo queue load | Front Door + Intake | Front Door owns first value moment |
| Simulation replacement | Front Door + Founder Control | Front Door implements; Founder Control updates playbook |
| PG/engineer chrome | Front Door + Case Record | Front Door owns hide; Case Record owns case card labels |

**No duplicate capabilities.** Overlaps are dependency edges, not separate products.

---

## 4. Is Anything Missing?

**Not missing from capability model. Missing from repo execution:**

| Gap | Owner | Not a new capability |
|-----|-------|----------------------|
| Pilot terms 1-pager (Chinese) | Founder commercial | Trial Conversion artifact |
| Invoice template | Founder commercial | Trial Conversion artifact |
| Broker UX launch checklist (formal) | Implementation sprint | Founder Control artifact |
| Stale RAG goal doc rewrite | Doc sprint | Founder Control anti-drift |
| Completed Chen Kui trial | Founder execution | Trial Conversion evidence |
| P13 sprint | N/A | Never existed — do not invent |

**Product scope is complete.** Execution artifacts and UI fixes are the gap — correctly deferred to implementation sprints.

---

## 5. What Would Chen Kui Care About?

**Would care (pays for these):**

1. Cancellation / payment failed handled same-day — urgency obvious  
2. 下一步 (Your next move) without re-reading WeChat thread  
3. 已收集 / 还缺 — stops re-asking customer  
4. Editable draft copied to WeChat — saves typing  
5. Cases still there tomorrow (Postgres prod)  
6. Clear price ($49 or $99) and simple invoice at Day 7  
7. 不自动发送 — he controls every message  
8. Assistant can use same workbench — doubles office value  
9. Monday morning queue — nothing urgent buried  
10. Chinese-first labels matching his office language  

**Emotional drivers:** Trust (not beta), speed on urgent messages, not looking foolish in front of clients.

---

## 6. What Would Chen Kui Ignore?

**Would ignore or reject:**

1. PG 镜像 / API URL / 路由/指标 debug tags  
2. SearchForge RAG `/demo` page  
3. Simulation Assistant tab (hidden anyway)  
4. Add-Car customer portal as primary story  
5. English "case" / "Unified Intake" in nav  
6. Engineer filters (镜像异常, 旧识别, 测试, 正式)  
7. Platform/lab architecture  
8. AI/vector/RAG marketing language  
9. $199 tier promises  
10. WeChat sync pitch (would expect it; must set expectation early)  
11. Repo cleanup / sprint archaeology  
12. Multi-office / enterprise features  
13. Perfect OCR / screenshot upload  
14. Auto-send "efficiency"  
15. Stripe self-serve signup flow  

---

## 7. What Should NOT Be Built Next?

**Constitution-locked — do not build:**

1. Stripe / billing portal  
2. WeChat or email sync  
3. CRM / carrier APIs  
4. Multi-tenant / OAuth  
5. OCR as primary intake  
6. Platform SKU / workflow engine  
7. $199 tier  
8. New features before 7-day trial evidence  
9. Repo cleanup / lab isolation during trial month  
10. RAG `/demo` as paid product surface  
11. Auto-send  
12. P12/P13 strategy sprints  
13. New issue categories beyond trial fix-now  
14. Mobile-first redesign (optional P3 only)  
15. Second broker outreach before first testimonial  

---

## 8. What Should Be Built Next?

**First implementation sprint: Week 1 Broker Front Door + Trust**

Priority order (P11 evidence-ranked):

1. Default 办公室工作台 tab  
2. Hide engineer chrome (API, PG, debug)  
3. Wayfinding banner  
4. Auto-open cancellation after demo queue  
5. Loading states (paste + demo queue)  
6. Inline 3 practice scenarios  
7. Prod deploy + `/readyz`  
8. Broker UX launch checklist  
9. Pricing + terms + invoice on one-pager  
10. Founder dry-run → Chen Kui Day 0 kickoff  

Then: **7-day supervised trial with observation log — no new features.**

---

## 9. What Are the Top 20 Risks?

| # | Risk | Capability | Mitigation |
|---|------|------------|------------|
| 1 | Broker opens wrong tab — never sees cancellation | Front Door | Default workbench tab |
| 2 | Expects WeChat sync — paste feels like extra work | Intake Collection | Explicit paste copy + wedge demo |
| 3 | Production not validated — cases lost | Founder Control | Deploy + `/readyz` before Day 0 |
| 4 | Draft wrong on real messages — won't pay | Case Record | Fix-now from trial log only |
| 5 | Playbook Simulation path broken | Front Door + Founder | Inline scenarios; update playbook |
| 6 | Founder unavailable during outage | Founder Control | L1 doc + 24h SLA in terms |
| 7 | Add-Car vs cancellation story split | Front Door + Intake | Cancellation-first GTM locked |
| 8 | Engineer UI chrome — "beta / not for me" | Front Door | product_only chrome purge |
| 9 | No logged time savings at Day 7 | Trial Conversion | Observation log + minutes field |
| 10 | ChatGPT "good enough" for drafts | Case Record + Triage | Sell case structure + queue |
| 11 | Script PASS creates false launch confidence | Founder Control | Two-gate: script + UX checklist |
| 12 | Pricing not on one-pager | Trial Conversion | $49/$99 on BROKER_ONE_PAGER |
| 13 | No pilot terms — data/cancel unclear | Trial Conversion | 1-page Chinese agreement |
| 14 | Single-founder support bottleneck | Founder Control | Case snapshot + L1 doc |
| 15 | Assistant doesn't adopt — caps ROI | Lifecycle | 15-min training script |
| 16 | 503/warming on first paste | Triage + Founder | Loading copy + recovery runbook |
| 17 | Stale RAG goals mislead agents | Founder Control | Deprecate insurance_paid_pilot_goal |
| 18 | Demo queue 30s load — "broken" | Front Door | Progress indicator |
| 19 | Data retention fear post-trial | Trial Conversion | State in pilot terms |
| 20 | Building features before payment proof | All | Constitution evolution gate |

---

## 10. Final Verdict

### Constitution ratification: **APPROVED**

The Unified Intake V1 Constitution is **locked**. Discovery is complete (P10, P11, P14-A). P13 does not exist and was not invented.

| Dimension | Status |
|-----------|--------|
| North Star | Clear and testable |
| 7 capabilities | Complete; merges documented |
| Contracts | Defined with scores, gaps, anti-scope |
| Overall product | **60/100** today → **80/100** target after Week 1 + trial |
| Revenue path | Conditional GO — supervised trial after UI fixes |

**One-line verdict (P11 unchanged, now constitution-backed):**

> **The triage engine can earn $99/month; the broker front door must earn trust first.**

**Next action:** Execute **Sprint 1 — Broker Front Door + Trust** (implementation). No coding in P14-B — coding begins in the sprint derived from this constitution.

**Founder decision still required:**

- [ ] Adopt V1 constitution as product SSOT (supersedes P14-A proposal status)  
- [ ] Confirm cancellation-first wedge on BROKER_ONE_PAGER  
- [ ] Confirm $49/$99 published before Day 0  
- [ ] Schedule Chen Kui trial after Week 1 implementation sprint  

---

*End of P14-B Final Review*
