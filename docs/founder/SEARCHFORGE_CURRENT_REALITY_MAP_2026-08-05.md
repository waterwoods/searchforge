# SearchForge Current Reality Map — 2026-08-05

**Authority:** Founder strategic reality SSOT for commercialization prioritization  
**Base freeze:** tag `accident-story-restricted-pilot-rehearsal-v1` @ `68f16d6`  
**Strategy branch:** `strategy/founder-review-2026-08-05` (docs only; does not mutate freeze)  
**Rule:** Classify from code, tests, tags, deploy evidence, or Founder phone packs — never from aspirational docs alone.  
**Production / waterwoods:** untouched by this review.

### Classification legend

| Label | Meaning |
|-------|---------|
| **Implemented + validated** | Product path + automated tests + Founder/manual or release-gate evidence |
| **Implemented + synthetic-only** | Code + tests and/or Cloud QA synthetic canary; no real-customer cases |
| **Partial** | Real code on product path, incomplete UX/ops/metrics proof |
| **Planned only** | Spec/plan/portfolio without matching product proof |
| **Deliberately excluded** | Explicit non-goal for paid pilot / restricted pilot |
| **Legacy / unused** | Present in repo; not required by product_only pilot path |

---

## 1. Milestone truth (reconciled)

| Milestone | Evidence | Classification |
|-----------|----------|----------------|
| Deterministic Claim workflow (intake → Request More → supplement → office accept) | Tag `stage1-founder-validated-demo-2026-08-03` · `docs/evidence/STAGE1_FOUNDER_VALIDATED_CLOSEOUT.md` · commit `826fa39` | **Implemented + validated** |
| Known-customer policy confirm | `docs/evidence/STAGE2_FOUNDER_VALIDATED_CLOSEOUT.md` · `tests/test_policy_context_prefill_confirm.py` | **Implemented + validated** |
| Guided Intake UX (LangGraph visible on Start Claim) | Tag `guided-intake-ux-v1-founder-pass` · `docs/evidence/langgraph-pr-a/GUIDED_INTAKE_FOUNDER_PASS_CLOSEOUT.md` · commit `d749216` | **Implemented + validated** |
| Bounded LangGraph accident-story workflow | `services/fiqa_api/inbox_triage/accident_story_assistant/` · `tests/test_accident_story_langgraph.py` | **Implemented + validated** (phone path for guided UX); LLM accuracy still synthetic |
| LangSmith traces + golden evals | Tag `langsmith-golden-evals-v1` · `docs/evidence/langsmith-pr-b/` · 20/20 `accident_story_v1` | **Implemented + synthetic-only** (eval suite ≠ real-customer accuracy) |
| Pilot safety / kill switch / fallback | Tag `accident-story-pilot-safety-v1` · `tests/test_accident_story_pilot_safety.py` · gates doc | **Implemented + validated** (QA/synthetic failure injection) |
| Cloud QA live-model canary | Tag `accident-story-qa-canary-v1` · `docs/evidence/pilot-canary-pr-d/` · 20/20 live synthetic | **Implemented + synthetic-only** |
| Five-case office rehearsal | Tag `accident-story-restricted-pilot-rehearsal-v1` · scorecard 5/5 local + 5/5 QA | **Implemented + synthetic-only** |
| Chen office activation | `docs/pilot/ACCIDENT_STORY_CHEN_OFFICE_ACTIVATION_PREP_V1.md` status UNEXECUTED | **Planned only** (prep docs; not run) |
| Real-customer pilot accuracy / paid conversion | None | **Planned only** / unproven |
| Production promotion of Accident Story | Explicitly forbidden by freeze/gates | **Deliberately excluded** (until Founder GO + real evidence) |

**Current commercial state:** `READY FOR FOUNDER GO/NO-GO` — not Production Ready, not Chen-activated.

---

## 2. Product surfaces

| Surface | Path / service | Status |
|---------|----------------|--------|
| WeChat Mini Program (customer claim) | `miniapp/` — `start-claim`, `case-status`, `request-item`, photos | **Implemented + validated** (Stage 1/2 + Guided Intake Founder packs) |
| Broker Workbench (Vercel) | `ui/` — document-intake / unified-intake workbench | **Implemented + validated** on Cloud QA Preview; Production alias exists separately |
| FastAPI product API | `services/fiqa_api/` Cloud Run `fiqa-api` / `fiqa-api-qa` | **Implemented + validated** for Claim + Accident Story propose on QA |
| Inbox triage (paste → case) | `inbox_triage/triage.py`, `POST /api/inbox/triage` | **Implemented + partial** for broker paste flows; Accident Story is the guided claim wedge |
| LangGraph Accident Story | `accident_story_assistant/graph.py` + Mini Program guided view | **Implemented + synthetic-only** for live LLM; guided path Founder-validated |
| LangSmith | Project `accident-story-restricted-pilot-v1` (clean) + historical lab debt | **Implemented + synthetic-only** |
| Postgres / Cloud SQL | Instance `caseiq-pilot-pg`; DBs `caseiq` / `caseiq-qa` | **Implemented + validated** as persistence SSOT for pilots |
| GCS media | Bucket `caseiq-wecom-media-qa` (QA) | **Implemented + partial** (claim evidence uploads; not AI story path) |
| Metrics / CaseEvent timing | Durable activity events + `export_accident_story_pilot_metrics.py` | **Implemented + synthetic-only** for Accident Story pilot metrics; Real Usage Timing QA-deployed |
| Feature flags / rollback | `ACCIDENT_STORY_*` in `flags.py` + runbooks | **Implemented + validated** (kill switch rehearsal) |

---

## 3. Capability matrix (condensed)

### Implemented and validated

- Deterministic Claim lifecycle commands and projections (CreateClaim, Request More, supplement ack, office accept blocking while open Request More)
- One-active-case / invite isolation for phone QA
- Known-customer policy context confirm
- Mini Program Start Claim guided path showing AI draft + ≤3 follow-ups + customer confirm
- Broker Brief layers: 客户原始描述 / AI整理草稿 / 客户已确认事实
- Kill switch → manual intake remains usable
- Release gates scripts and Founder Go/No-Go packet

### Implemented but synthetic-only

- Live OpenAI extraction on Cloud QA allowlist `qa_canary_synth`
- LangSmith golden dataset `accident_story_v1` (20/20)
- Five-case restricted rehearsal (local + QA)
- Durable Accident Story pilot metrics exporters
- Clean LangSmith pilot project (new traces); 8 immutable historical bare-node runs = cleanup debt

### Partially implemented

- AI accept/edit/reject rate metrics (confirm API exists; exporter notes unsupported rates)
- Multi-office tenant IAM / full RBAC (coarse API keys + office isolation tests; not full SaaS IAM)
- Privacy/retention as operational policy (consent copy exists; no long-running retention certification)
- GCS / photo evidence AI understanding (upload path exists; not bounded LangGraph understanding wedge)
- Inbox triage LLM assist quality for non-claim add-car chaos (large engine; not the Accident Story gate)

### Planned only

- Chen office allowlist activation on QA
- ≤5 real customer cases + scorecard from real traffic
- Paid pilot conversion / pricing close
- Production Accident Story enablement
- MCP broker product tools for Case Builder

### Deliberately excluded (current pilot box)

- AI coverage advice, liability judgment, carrier claim submit/close, payment
- Production / waterwoods mutation from restricted-pilot work
- Multi-tenant OAuth/SSO
- Stripe / billing automation
- Unbounded agent autonomy over Claim lifecycle

### Legacy / unused / lab

- `platform_full` lab routers, RAG `/api/query`, AutoTuner, GPU worker, Metrics Hub
- JSON case files as prod persistence (forbidden when PG-primary)
- Mortgage / jobhunter / ecommerce / airport MVP Cloud Run siblings (same GCP project; not broker product)
- Archived sprint docs (~992) under `docs/archive/` / historical `docs/sprints/`
- Neon as case store (explicitly rejected; Cloud SQL only)

---

## 4. Stale claims corrected

| Stale claim (older docs) | Current truth |
|--------------------------|---------------|
| LangSmith Case Builder gate “not started” (`CURRENT_CODEBASE_REALITY_2026-08-03`) | Closed for Accident Story: tag `langsmith-golden-evals-v1`, 20/20 golden + redaction |
| LangGraph “Founder phone not yet” (Aug 3 reality) | Guided Intake Founder PASS frozen (`guided-intake-ux-v1-founder-pass`) |
| “PILOT READY” = Production Ready | False — vocabulary is DEMO / PILOT WITH RESTRICTIONS only |
| Five-case rehearsal = real office activation | False — synthetic office `qa_canary_synth`; Chen prep UNEXECUTED |
| Unified Intake one-pager = full current claim architecture | Partial — Claim Mini Program + Accident Story supersede older paste-only map for the guided wedge |

---

## 5. Git / freeze references

| Ref | Role |
|-----|------|
| Branch `stage2/restricted-pilot-rehearsal-launch` @ `68f16d6` | Freeze tip |
| Tag `accident-story-restricted-pilot-rehearsal-v1` | Rehearsal + Go/No-Go freeze |
| Tag `accident-story-qa-canary-v1` | Live synthetic canary |
| Tag `accident-story-pilot-safety-v1` | Safety/fallback |
| Tag `langsmith-golden-evals-v1` | Tracing + golden |
| Tag `guided-intake-ux-v1-founder-pass` | Customer-visible guided UX |
| Tag `stage1-founder-validated-demo-2026-08-03` | Deterministic claim phone |

---

## 6. What this map is not

- Not a deploy authorization  
- Not a Production readiness certificate  
- Not proof of real-customer model accuracy or willingness to pay  

**Next Founder action:** GO / HOLD / NO-GO on `docs/founder/ACCIDENT_STORY_FIVE_CASE_GO_NO_GO_V1.md`.
