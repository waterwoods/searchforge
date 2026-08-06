# SearchForge Founder One-Pager — 2026-08-05

**Read time:** <5 minutes  
**Freeze:** `accident-story-restricted-pilot-rehearsal-v1` @ `68f16d6`  
**State:** `READY FOR FOUNDER GO/NO-GO` · Chen activation **not** executed · Production/waterwoods **untouched**

---

## 1. What we built

A broker claim system with a **bounded AI assist**: WeChat Mini Program customers describe an accident → LangGraph proposes structured facts and ≤3 missing questions → customer confirms → deterministic Claim workflow + Broker Workbench Brief (original / AI draft / confirmed). Kill switches, deterministic fallback, Postgres metrics, LangSmith redacted traces.

---

## 2. What is validated

| Layer | Proof |
|-------|-------|
| Deterministic Claim + Request More + office accept | Stage 1 Founder phone |
| Known-customer confirm | Stage 2 Founder phone |
| Guided Intake UX (AI visible, not hidden) | Founder PASS tag |
| Safety / fallback / kill switch | Pilot-safety + rehearsal |
| Golden evals 20/20 + QA live synthetic canary 20/20 | LangSmith + canary tags |
| Five-case synthetic office rehearsal | 5/5 local + 5/5 Cloud QA |

---

## 3. What remains unproven

- Real-customer model accuracy  
- Chen office daily adoption  
- Hours saved / willingness to pay  
- Production Accident Story  
- Multi-office scale  

---

## 4. Current commercial opportunity

Sell **restricted pilot learning** to one office: fewer incomplete accident intakes, safer AI use, clearer broker next action — **if** five real cases clear thresholds. Not a Production AI claim. Not a multi-office SaaS launch.

---

## 5. Recommended next AI wedge

**Primary (after real feedback):** Broker-controlled **Request More follow-up drafting** (reuse confirm + Request More + flags + metrics).  
**Secondary experiment:** Read-only office next-action assistant.  
**Postpone:** Inbound triage rewrite, renewal bot, carrier package AI.

---

## 6. Recommended next seven days

1. You decide **GO / HOLD / NO-GO**  
2. If GO: activate Cloud QA allowlist only → ≤5 real cases → pause on metrics  
3. If HOLD/NO-GO: no activation; use week for FDE portfolio + job search  
4. Do **not** build the next wedge or run more synthetic canaries without a decision  
5. Preserve the freeze; no Production/waterwoods  

Detail: `docs/founder/SEARCHFORGE_SEVEN_DAY_HIGH_LEVERAGE_PLAN_V1.md`

---

## 7. Biggest risk

**Premature expansion** — shipping more AI or Production flags before five real cases teach what brokers actually need — wasting the validated safety boundary and founder energy.

Secondary risk: treating synthetic canary success as commercial proof.

---

## 8. Exact Founder decision required next

Open `docs/founder/ACCIDENT_STORY_FIVE_CASE_GO_NO_GO_V1.md` and pick **one**:

| Choice | Meaning |
|--------|---------|
| **GO** | Authorize ≤5 real Chen cases on **Cloud QA only** per activation prep |
| **HOLD** | Demo/synthetic only; do not activate allowlist/LLM for Chen |
| **NO-GO** | Keep/disable AI (`ACCIDENT_STORY_ASSISTANT_ENABLED=0`) and stop |

Until that decision, engineering should **not** activate Chen, deploy Production AI, or start the next wedge build.

---

## Doc map (this review)

| Doc | Path |
|-----|------|
| Reality map | `docs/founder/SEARCHFORGE_CURRENT_REALITY_MAP_2026-08-05.md` |
| Architecture | `docs/architecture/SEARCHFORGE_SYSTEM_AND_AI_MAP_V1.md` |
| Accounts / infra | `docs/operations/SEARCHFORGE_ACCOUNT_AND_INFRASTRUCTURE_INVENTORY_V1.md` |
| Capability catalog | `docs/founder/SEARCHFORGE_REUSABLE_CAPABILITY_CATALOG_V1.md` |
| Business value | `docs/founder/SEARCHFORGE_BUSINESS_VALUE_REVIEW_V1.md` |
| Next wedge | `docs/founder/SEARCHFORGE_NEXT_AI_WEDGE_DECISION_V1.md` |
| FDE case study | `docs/portfolio/SEARCHFORGE_FDE_MASTER_CASE_STUDY_V1.md` |
| 7-day plan | `docs/founder/SEARCHFORGE_SEVEN_DAY_HIGH_LEVERAGE_PLAN_V1.md` |
| This page | `docs/founder/SEARCHFORGE_FOUNDER_ONE_PAGE_2026-08-05.md` |
