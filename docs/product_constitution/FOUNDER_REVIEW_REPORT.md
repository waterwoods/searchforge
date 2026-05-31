# Founder Review Report — P14-A Constitution Discovery

**Date:** 2026-05-31  
**Audience:** Andy (founder)  
**Inputs:** Full P14-A discovery pack (7 documents), P8–P11 audits, converged SSOT docs

---

## 1. What Surprised Us?

1. **The constitution mostly already exists** — P10/P11 did heavy lifting; P14-A is consolidation, not invention.
2. **P12 and P13 do not exist** — mission brief referenced sprints that were never committed.
3. **Core promise is remarkably stable** — 10+ docs agree on paste → case → draft → you send despite repo chaos.
4. **The triage engine is ahead of GTM** — P10 one-liner still holds: "triage engine is trial-ready; broker front door is not."
5. **Stale RAG-era goals still live in START HERE hierarchy** — `insurance_paid_pilot_goal.md` can mislead agents reading AGENTS.md path.
6. **Master outline Add-Car-first wedge directly contradicts payment evidence** — P11 is explicit Chen Kui pays for cancellation minutes, not Add-Car portal.
7. **~70% constitution / ~30% conflict resolution** — not a greenfield strategy exercise.

---

## 2. What Did We Discover Already Existed?

| Discovery | Where it lived |
|-----------|----------------|
| Customer-facing product truth | P11 `CURRENT_PRODUCT_TRUTH.md` |
| Trial Day 0–7 single path | `TRIAL_ONE_PATH.md` |
| Founder canonical ops | `FOUNDER_ONE_PATH.md` |
| 6-field triage output model | `standards/BROKER_INBOX_TRIAGE_STANDARD.md` |
| Payment viability at $49–99 | P11 final audit + payment blockers |
| 50+ broker friction points catalogued | P10 friction audit + P11 TOP_50 |
| Doc authority hierarchy | `PROJECT_DOC_SYSTEM_MAP.md` |
| Deployment hard requirements | `CURRENT_PRODUCT_SHAPE.md` |
| Anti-goals (no sync, no auto-send, no CRM) | Repeated across 8+ docs |
| Chen Kui persona + client pack | configs/clients/chen_kui, P9 plan |

---

## 3. What Product Truths Were Hidden?

1. **Two products in one UI** — Broker Workbench (what we sell) vs Customer Entry Add-Car portal (what UI defaults to).
2. **Two products in one repo** — Unified Intake workbench vs SearchForge RAG `/demo` (still in goals/onboarding path).
3. **Script PASS creates false launch confidence** — operator-ready ≠ broker-ready (28/100 unsupervised Day 1).
4. **Simulation Assistant is a ghost requirement** — playbook mandates it; product-only UI hides it.
5. **Competitive moat is case structure, not drafts** — P11 competitive audit; ChatGPT pressure on draft-only value.
6. **Assistant adoption is a hidden multiplier** — broker-only use caps ROI; not in trial SSOT explicitly.
7. **Pricing exists internally ($99 anchor) but not in broker one-pager** — commercial gap, not product gap.

---

## 4. What Conflicts Exist?

**P0 (6):** Add-Car vs cancellation wedge; Customer Entry vs Workbench default; RAG vs workbench product; Simulation required vs hidden; pricing absent; script PASS vs UX ready.

**P1 (8):** Platform vs SaaS; identity in/out of scope; demo vs paid deploy modes; broker vs customer user; scenario counts; trial vs pilot wording; assistant role; OCR scope.

**Full detail:** `CONSTITUTION_CONFLICT_REPORT.md`

**Resolved in constitution proposal:** Cancellation-first GTM; workbench default; RAG demoted; light identity only; $49/$99 published; two-gate launch.

---

## 5. What Would Industry-Leading SaaS Companies Do?

| Practice | Our status | Recommendation |
|----------|------------|----------------|
| **Single product SSOT** | Split across 15+ docs | Approve V1 constitution; update START HERE |
| **Default UX = core value** | Wrong tab default | Ship tab default Week 1 (P11 plan) |
| **Pricing on marketing page** | Missing from one-pager | Add $49/$99 this week |
| **Onboarding checklist** | Strong founder path | Add broker UX gate beside script gate |
| **Activation metric** | Qualitative only | Add "minutes saved" field to observation log |
| **Kill stale docs** | RAG goals still active | Rewrite or deprecate with banner |
| **One wedge for v1** | Add-Car + cancellation split | Pick cancellation-first (evidence-weighted) |
| **Trial → paid conversion kit** | Partial | Create terms + invoice template |
| **Hide engineer UI** | PG/API visible | Product-only chrome purge |
| **Don't ship before first user proof** | P11 aligned | 7-day trial before features |

Industry leaders would **not** run an unsupervised trial today. They would ship 3 UI fixes, deploy prod, supervised kickoff, then measure.

---

## 6. What Should Andy Approve?

1. **`UNIFIED_INTAKE_V1_CONSTITUTION_PROPOSAL.md`** as product constitution SSOT  
2. **Cancellation-first wedge** overriding Add-Car-first GTM in master outline  
3. **$49 starter / $99 standard** pricing on BROKER_ONE_PAGER  
4. **Two-gate trial launch:** script PASS + broker UX checklist  
5. **90-day anti-goals list** (no Stripe, sync, CRM, platform)  
6. **Rewrite schedule** for `insurance_paid_pilot_goal.md` + `insurance_broker_pilot_rules.md`  
7. **P11 Week 1 UI plan** as first implementation sprint after constitution  
8. **Supervised Chen Kui trial** as validation path (conditional GO from P10/P11)  

---

## 7. What Should Andy Reject?

1. **Reject** unsupervised "here's the URL" trial before UI fixes  
2. **Reject** $199 tier until enterprise features exist  
3. **Reject** Add-Car portal as primary sales story for Chen Kui  
4. **Reject** repo cleanup / lab isolation during trial month  
5. **Reject** new features before 7-day trial evidence  
6. **Reject** using `/demo` RAG as paid product demo  
7. **Reject** treating master outline Add-Car-first as current GTM without amendment  
8. **Reject** creating P12/P13 strategy sprints before first payment  

---

## 8. What Should NOT Be Built?

See constitution §7. Summary:

- Stripe, sync, OCR, CRM, multi-tenant, auto-send, platform SKU, $199 tier, Simulation tab dependency, new scenarios beyond fix-now queue.

---

## 9. What Should Be Built in the Next 14 Days?

From P10/P11 highest-ROI (evidence-ranked):

| Day | Deliverable |
|-----|-------------|
| 1–2 | Default **办公室工作台** tab for trial URL |
| 2–3 | Hide PG/API/debug chrome in product-only UI |
| 3–4 | `validate_pilot_deploy_env.py` PASS + `deploy_paid_pilot.sh` + `/readyz` probe |
| 4 | Update BROKER_ONE_PAGER: **$49/$99**, 加载演示队列 label |
| 5 | Update TRIAL_ONE_PATH + playbook: remove Simulation dependency |
| 5–6 | Auto-open cancellation after demo queue load |
| 6–7 | Inline 3 practice scenarios in workbench |
| 7 | Pilot terms 1-pager (Chinese) + invoice template |
| 8 | Founder dry-run with observation log |
| 9–10 | Chen Kui Day 0 kickoff (30 min) |
| 10–14 | Trial Days 1–7; no new features |

**Not in 14 days:** Constitution is docs-only this sprint; UI fixes are next sprint.

---

## 10. Is the Repository Converging Toward a $49–99 Broker SaaS?

### Score: **62 / 100**

| Dimension | Score | Reasoning |
|-----------|-------|-----------|
| Product core (engine) | **85** | Guardrail passes; 6-field model; scenarios validated |
| Product surface (UX) | **35** | Wrong tab; engineer chrome; hidden Simulation |
| Commercial readiness | **45** | Price internal only; no terms/invoice in repo |
| Documentation convergence | **70** | P9–P11 collapsed paths; constitution gap closing |
| Deployment readiness | **55** | CURRENT_PRODUCT_SHAPE strong; prod validation incomplete |
| Trial process | **75** | TRIAL_ONE_PATH mature; UX gate missing |
| Anti-scope discipline | **65** | SIMPLIFICATION + P11 clear; stale RAG goals remain |
| Payment evidence | **25** | No completed trial; no testimonial; no logged ROI |

### Detailed Reasoning

**Why not higher:** P11 already scored unsupervised Day 1 at 28/100 and Day 7 at 35/100. The repo has converged **documentation and operator paths** (P8→P9→P10→P11) but not **broker-first UX or commercial packaging**. The engine can earn $99/month; the front door cannot yet earn trust unsupervised.

**Why not lower:** Unlike typical pre-PMF repos, this one has: explicit anti-goals, guardrail regression, paid-pilot env validators, collapsed founder/trial paths, and two rigorous audits (P10/P11) that agree on diagnosis and fixes. The constitution was discoverable — not inventable.

**Path to 80+:** Week 1 UI fixes + prod deploy + supervised Chen Kui trial + one "worked" log line + Day 7 payment conversation.

**Path to 90+:** First payment received + testimonial + second broker trial.

---

## Founder Decision Request

| Decision | Options |
|----------|---------|
| Adopt V1 constitution as SSOT? | Approve / Revise / Reject |
| GTM wedge | Cancellation-first (recommended) / Add-Car-first / Dual |
| Trial start | After UI fixes (recommended) / Immediate supervised / Delay |
| Pricing | $49+$99 (recommended) / $99 only / Other |

---

*End of founder review report*
