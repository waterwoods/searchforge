# Six-Day Pilot Release Plan — 2026-08-03

**Status:** Authoritative execution backlog for Mon 2026-08-03 → Sun 2026-08-09  
**Branch baseline:** `stage2/langgraph-accident-story-assistant`  
**North Star:** `docs/product/CASE_BUILDER_NORTH_STAR_2026-08-03.md`  
**Release gates:** `docs/release/PILOT_READY_RELEASE_GATES_V1.md`  
**Master backlog (non-duplicating index):** `docs/roadmap/CASE_BUILDER_MASTER_BACKLOG.md`  
**Constraint:** Production and waterwoods remain untouched unless an explicit Founder release decision is recorded.

### Calendar

| Day | Date | Lane |
|-----|------|------|
| Day 1 | Mon 2026-08-03 | Close LangGraph PR A |
| Day 2 | Tue 2026-08-04 | LangSmith PR B |
| Day 3 | Wed 2026-08-05 | AI Feedback and Business Evidence |
| Day 4 | Thu 2026-08-06 | Pilot Safety Baseline |
| Day 5 | Fri 2026-08-07 | Reusable Delivery Layer |
| Day 6 | Sat 2026-08-08 | Release and Portfolio Package |
| Sunday gate | Sun 2026-08-09 | Final demo + truthful status |

### Verified baseline (do not re-litigate)

| Slice | Status | Evidence |
|-------|--------|----------|
| Stage 1 deterministic workflow | FOUNDER-VALIDATED frozen | `docs/evidence/STAGE1_FOUNDER_VALIDATED_CLOSEOUT.md` · tag `stage1-founder-validated-demo-2026-08-03` · commit `826fa39` |
| Stage 2 known-customer confirm | CLOSED | `docs/evidence/STAGE2_FOUNDER_VALIDATED_CLOSEOUT.md` · commit `8b6ca01` / closeout `f1bb8e0` |
| Real Usage Timing V1 | CLOSED | `docs/metrics/REAL_USAGE_TIMING_V1_CLOSEOUT.md` · commits through `9051f41` |
| LangGraph PR A | Implemented locally; tests green; **not phone-frozen** | code `services/fiqa_api/inbox_triage/accident_story_assistant/` · `tests/test_accident_story_langgraph.py` (13 PASS) · UI wire `31abf61` · case study `docs/portfolio/FDE_CASE_STUDY_LANGGRAPH_V1.md` |
| LangSmith PR B | Not started for Case Builder | Lab helpers only (`services/fiqa_api/observability/langsmith_tracing.py`); no accident-story golden eval gate |

---

## Backlog item schema

Every item uses:

- priority · customer problem · startup/commercial impact · FDE/interview impact  
- estimated effort · dependencies · acceptance criteria · automated test requirement  
- Founder manual action · demo artifact · defer reason (when excluded)

---

## Day 1 — Close LangGraph PR A

### D1-1 — Automated review + Stage regression gate

| Field | Content |
|-------|---------|
| Priority | P0 |
| Customer problem | Prevent AI assist from breaking the frozen intake path brokers already trust. |
| Startup/commercial | Protect Stage 1/2 demo credibility before any Chen walkthrough. |
| FDE/interview | Shows regression discipline around probabilistic features. |
| Effort | 1–2h |
| Dependencies | Existing `tests/test_accident_story_langgraph.py`, Stage 1/2 test suites |
| Acceptance | `pytest tests/test_accident_story_langgraph.py` PASS; Stage 1/2 critical claim tests PASS; propose/confirm never mutate lifecycle in assertions. |
| Automated tests | Required — LangGraph matrix + existing claim regression subset. |
| Founder manual | None unless automated FAIL. |
| Demo artifact | Command transcript / CI log in evidence folder. |
| Defer | — |

### D1-2 — Minimal Founder phone QA (only if necessary)

| Field | Content |
|-------|---------|
| Priority | P0 |
| Customer problem | Customer must see confirm/edit of AI-organized story, not silent overwrite. |
| Startup/commercial | Without one phone proof, cannot claim “demo-ready AI assist.” |
| FDE/interview | Human-in-the-loop gate evidence. |
| Effort | 30–45 min phone if D1-1 green and Cloud QA already has PR A; else deploy QA first (extra 30–60 min). |
| Dependencies | D1-1; Cloud QA `fiqa-api-qa` only |
| Acceptance | One Camry path: propose → customer confirm/edit → Brief shows confirmed vs unconfirmed labels; Stage 1 Request More path still works on a separate case. Skip phone only if Founder accepts automated+Workbench browser proof as sufficient for freeze — record that decision. |
| Automated tests | Not a substitute for phone when UI labels change. |
| Founder manual | Phone or explicit written waiver for phone. |
| Demo artifact | `docs/evidence/langgraph-pr-a/` screenshots + go-no-go note. |
| Defer | Broad UX polish (ledger L3) stays deferred. |

### D1-3 — Verify customer confirmation and Broker labels

| Field | Content |
|-------|---------|
| Priority | P0 |
| Customer problem | Broker must distinguish AI proposal vs customer-confirmed facts. |
| Startup/commercial | Trust — wrong authority label kills office adoption. |
| FDE/interview | Authority states (`ai_proposed` / `customer_confirmed`) as design proof. |
| Effort | 1h |
| Dependencies | D1-1; Workbench Brief wiring (`claim_workbench_display.py`) |
| Acceptance | Unconfirmed proposal never written as authoritative known_facts; confirmed path shows Chinese Brief label per case study; edit overrides AI values. |
| Automated tests | Existing confirm/edit/unconfirmed tests must remain green. |
| Founder manual | Spot-check Brief once. |
| Demo artifact | Before/after Brief screenshot. |
| Defer | Broker `broker_reviewed` deep workflow beyond label. |

### D1-4 — Freeze/tag the slice + 90-second explanation

| Field | Content |
|-------|---------|
| Priority | P0 |
| Customer problem | Stable baseline so later days do not rebuild PR A. |
| Startup/commercial | Clear “what we can demo tomorrow.” |
| FDE/interview | Tagged slice + 90s story. |
| Effort | 45 min |
| Dependencies | D1-1–D1-3 |
| Acceptance | Annotated tag e.g. `langgraph-pr-a-ready-2026-08-03`; short note in portfolio case study updated with tag/commit; 90-second script written. |
| Automated tests | None beyond gate already green. |
| Founder manual | Approve freeze wording (5 min). |
| Demo artifact | Tag + `docs/portfolio/FDE_CASE_STUDY_LANGGRAPH_V1.md` freeze stanza + 90s script. |
| Defer | LangSmith (Day 2). |

---

## Day 2 — LangSmith PR B

### D2-1 — Traces for graph and model calls

| Field | Content |
|-------|---------|
| Priority | P0 |
| Customer problem | When AI misfires, office needs a debuggable trail without reading secrets. |
| Startup/commercial | Faster failure diagnosis during pilot demos. |
| FDE/interview | Production-minded observability for a bounded graph. |
| Effort | 3–4h |
| Dependencies | Day 1 freeze; opt-in env only on QA/local |
| Acceptance | Propose path emits LangSmith (or documented local noop) runs for graph nodes + model calls; disabled by default in prod-like profile; no raw PII/tokens in traced inputs by default (redaction or hashed/truncated policy). |
| Automated tests | Unit/integration: tracing helper no-ops safely when unset; does not break propose. |
| Founder manual | None. |
| Demo artifact | One redacted trace screenshot (QA project). |
| Defer | Full org-wide LangSmith for all legacy graphs. |

### D2-2 — Golden dataset + deterministic evaluators

| Field | Content |
|-------|---------|
| Priority | P0 |
| Customer problem | Stop asking unnecessary questions; catch missing Must Haves. |
| Startup/commercial | Repeatable quality bar before Chen demo. |
| FDE/interview | Eval harness story (dataset + deterministic checks). |
| Effort | 3–4h |
| Dependencies | Existing fixtures under `tests/fixtures/accident_story_langgraph/` |
| Acceptance | Golden dataset registered (LangSmith and/or local JSON SSOT); evaluators for hallucination, missing-fact coverage, unnecessary-question count, injury unknown preservation. |
| Automated tests | Offline regression script/pytest gate required. |
| Founder manual | None. |
| Demo artifact | Dataset list + sample eval table. |
| Defer | Large multilingual corpus. |

### D2-3 — Optional limited LLM judge + offline gate + failure evidence

| Field | Content |
|-------|---------|
| Priority | P1 |
| Customer problem | Catch semantic nonsense deterministic rules miss. |
| Startup/commercial | Higher confidence before live demo; not a sales claim. |
| FDE/interview | Shows judge used sparingly with deterministic primary gate. |
| Effort | 2–3h |
| Dependencies | D2-2 |
| Acceptance | Offline gate fails on known bad fixtures; failure evidence saved; LLM judge optional and clearly labeled non-blocking unless Founder flips it to blocking. |
| Automated tests | Gate script exit non-zero on planted failures. |
| Founder manual | Decide blocking vs advisory for judge (5 min). |
| Demo artifact | `docs/evidence/langsmith-pr-b/` failure + pass runs. |
| Defer | Continuous online eval in Production. |

---

## Day 3 — AI Feedback and Business Evidence

### D3-1 — Accept / Edit / Reject instrumentation

| Field | Content |
|-------|---------|
| Priority | P0 |
| Customer problem | Learn whether AI proposals help or waste customer/broker time. |
| Startup/commercial | First honest AI quality signal for pilot conversations. |
| FDE/interview | HITL feedback loop evidence. |
| Effort | 3–4h |
| Dependencies | Confirm API authority transitions; metrics store patterns from Timing V1 |
| Acceptance | Durable events for accept / edit / reject (or equivalent outcomes already implied by confirm+edits+dismiss); `changed_fields` recorded; never invent rates without events. |
| Automated tests | Record + export tests; idempotency; read paths do not stamp. |
| Founder manual | None. |
| Demo artifact | One case with accept and one with edit in export. |
| Defer | Broker-side free-text AI critique UI. |

### D3-2 — Follow-up count, fallback rate, latency/cost where available

| Field | Content |
|-------|---------|
| Priority | P1 |
| Customer problem | Measure supplement pressure and AI reliability. |
| Startup/commercial | Supports “fewer loops” hypothesis without fabricating ROI. |
| FDE/interview | Metrics beyond vanity dashboards. |
| Effort | 2–3h |
| Dependencies | D3-1; Timing V1 exporter |
| Acceptance | Exporter columns/notes for follow-up question count, deterministic fallback rate, model latency; cost only if provider metadata exists — else `unsupported:…`. |
| Automated tests | Exporter unit tests for new fields + unsupported honesty. |
| Founder manual | None. |
| Demo artifact | Updated `CASE_VALUE_METRICS_QA_REPORT.md` section. |
| Defer | Dollar ROI / time-saved claims. |

### D3-3 — Truthful QA metrics report

| Field | Content |
|-------|---------|
| Priority | P0 |
| Customer problem | Founder needs numbers that will not embarrass him with 陈总. |
| Startup/commercial | Credibility over hype. |
| FDE/interview | “What we can and cannot claim” paragraph. |
| Effort | 1–2h |
| Dependencies | D3-1, D3-2 |
| Acceptance | Small QA report with sample n, unsupported list, no customer-savings claims. |
| Automated tests | Optional snapshot of export summary. |
| Founder manual | Read once (10 min). |
| Demo artifact | `docs/metrics/AI_FEEDBACK_QA_REPORT_V1.md` |
| Defer | Investor-grade analytics product. |

---

## Day 4 — Pilot Safety Baseline

### D4-1 — PII minimization + role/tenant boundary audit

| Field | Content |
|-------|---------|
| Priority | P0 |
| Customer problem | Customer evidence must not leak across offices or strangers. |
| Startup/commercial | Hard gate before any external pilot talk. |
| FDE/interview | Security-minded FDE posture. |
| Effort | 3–4h |
| Dependencies | Track C evidence baseline; demo invite isolation tests |
| Acceptance | Written audit of customer/broker/support keys, case access, invite isolation; PII fields listed with storage justification; traces/metrics rechecked for raw story leakage. |
| Automated tests | Re-run tenant/invite isolation tests; add gaps only if audit finds holes. |
| Founder manual | Sign audit summary (10 min). |
| Demo artifact | `docs/release/PILOT_SAFETY_AUDIT_2026-08-06.md` |
| Defer | Formal SOC2 / legal cert. |

### D4-2 — Sensitive-action audit log + consent/retention draft

| Field | Content |
|-------|---------|
| Priority | P0 |
| Customer problem | Office needs accountability for accept / Request More / AI confirm. |
| Startup/commercial | Pilot conversation readiness with 陈总. |
| FDE/interview | Auditability story. |
| Effort | 2–3h |
| Dependencies | Existing Timeline / office actions |
| Acceptance | Inventory of sensitive actions and where logged; draft customer consent + retention policy (1–2 pages, Chinese+English bullets OK); gaps listed honestly. |
| Automated tests | None required beyond proving logs exist for listed actions. |
| Founder manual | Approve draft language intent (15 min). |
| Demo artifact | `docs/release/PILOT_CONSENT_RETENTION_DRAFT_V1.md` |
| Defer | Lawyer-certified policy. |

### D4-3 — Model failure fallback + feature flag/rollback + checklist

| Field | Content |
|-------|---------|
| Priority | P0 |
| Customer problem | AI outage must not stop intake. |
| Startup/commercial | Demo resilience. |
| FDE/interview | Fallback/control plane story. |
| Effort | 2–3h |
| Dependencies | Day 1 graph fallback path |
| Acceptance | Documented flag to disable LLM path; timeout/invalid JSON → deterministic extractor; rollback steps for QA revision; pilot checklist references gates doc. |
| Automated tests | Existing timeout/invalid JSON tests remain; flag off test. |
| Founder manual | None. |
| Demo artifact | Checklist section in `PILOT_READY_RELEASE_GATES_V1.md` filled. |
| Defer | Multi-region HA. |

---

## Day 5 — Reusable Delivery Layer

### D5-1 — Three read-only MCP Broker tools + one write/draft tool

| Field | Content |
|-------|---------|
| Priority | P1 |
| Customer problem | Future office tooling without giving agents silent write power. |
| Startup/commercial | Second-office delivery story; not sold as the product. |
| FDE/interview | MCP with human confirmation boundary. |
| Effort | 4–5h |
| Dependencies | Existing case read APIs; lab `mcp/` isolation pattern |
| Acceptance | Tools: e.g. `get_case_brief`, `get_timeline`, `get_missing_items` (read-only); one `draft_request_more` (or similar) that **cannot** mutate without Broker confirm path; product_only does not require MCP. |
| Automated tests | Tool unit tests + “write tool does not persist without confirm” test. |
| Founder manual | None. |
| Demo artifact | `mcp/case_builder_broker/` README + sample tool list. |
| Defer | Large MCP platform / IDE marketplace publish. |

### D5-2 — Office configuration template + fixture/demo reset + second-office checklist

| Field | Content |
|-------|---------|
| Priority | P1 |
| Customer problem | New office setup should not require tribal knowledge. |
| Startup/commercial | Reduces Founder time per office. |
| FDE/interview | Delivery playbook evidence. |
| Effort | 2–3h |
| Dependencies | Client pack patterns; Prepare Demo / Fast Lane assets |
| Acceptance | Template for office config; safe QA reset instructions; second-office setup checklist (env, keys, invite scenario, Workbench URL). |
| Automated tests | Reuse demo invite / reset tests where they exist. |
| Founder manual | Walk checklist once dry (15 min). |
| Demo artifact | `docs/runbooks/SECOND_OFFICE_SETUP_CHECKLIST_V1.md` |
| Defer | Full multi-tenant admin UI. |

---

## Day 6 — Release and Portfolio Package

### D6-1 — One-click Chen demo + three scenarios

| Field | Content |
|-------|---------|
| Priority | P0 |
| Customer problem | Founder must run a clean demo without Cursor. |
| Startup/commercial | Chen meeting readiness. |
| FDE/interview | End-to-end demo reliability. |
| Effort | 3–4h |
| Dependencies | Days 1–4; Prepare Demo panel / Fast Lane |
| Acceptance | One-click (or single script) issues Chen invite + reset; scenarios documented: (1) complete case, (2) missing-information / Request More, (3) AI failure/fallback. |
| Automated tests | Fast Lane / invite smoke green. |
| Founder manual | Run one-click once. |
| Demo artifact | Operator card + scenario script. |
| Defer | Public self-serve signup. |

### D6-2 — Architecture diagram + customer one-pager + pitches

| Field | Content |
|-------|---------|
| Priority | P0 |
| Customer problem | 陈总 understands value in plain language. |
| Startup/commercial | Sales narrative without jargon. |
| FDE/interview | 3-min customer pitch + 3-min FDE story. |
| Effort | 3h |
| Dependencies | Learning map |
| Acceptance | Architecture diagram; customer one-page; 3-min customer pitch; 3-min FDE interview story — all jargon-light on customer side. |
| Automated tests | None. |
| Founder manual | Rehearse pitches once (20 min). |
| Demo artifact | Files under `docs/portfolio/` + update `docs/BROKER_ONE_PAGER.md` only if consistent. |
| Defer | Video production studio polish. |

### D6-3 — README / portfolio landing + release tag + evidence index

| Field | Content |
|-------|---------|
| Priority | P0 |
| Customer problem | Continuity for Founder after the week. |
| Startup/commercial | Portfolio-ready package. |
| FDE/interview | Single landing page for reviewers. |
| Effort | 2h |
| Dependencies | D6-1, D6-2 |
| Acceptance | Portfolio README; release tag for Sunday candidate; evidence index linking Stage1/2/Metrics/LangGraph/LangSmith/Safety. |
| Automated tests | None. |
| Founder manual | Approve public wording (no overclaim). |
| Demo artifact | `docs/portfolio/README.md` + evidence index. |
| Defer | Public GitHub marketing site. |

---

## Sunday final gate — 2026-08-09

| ID | Item | Priority | Acceptance |
|----|------|----------|------------|
| S-1 | Run all critical automated tests | P0 | LangGraph + Timing integrity + Stage claim critical + invite isolation PASS |
| S-2 | One end-to-end Founder walkthrough | P0 | Complete Camry path on Cloud QA with AI confirm + Brief labels |
| S-3 | Fix only P0 blockers | P0 | No feature creep; P1 logged to master backlog |
| S-4 | Record short demo | P0 | ≤3 min screen recording or phone capture |
| S-5 | Restore cost-saving infrastructure | P0 | QA minScale=0 / maxScale=2 (or current cost-saving default) |
| S-6 | Publish truthful release status | P0 | Label per gates doc: `DEMO READY` / `PILOT READY WITH RESTRICTIONS` / `NOT PILOT READY` — never `PRODUCTION READY` without full proof |

---

## Explicitly excluded this week (defer reasons)

| Item | Defer reason |
|------|--------------|
| Quoting / coverage / liability | North Star exclusion; legal risk |
| Autonomous claim filing | North Star exclusion |
| General CRM | Out of wedge |
| Open-ended chatbot / multi-agent rewrite | Complexity not proven necessary |
| Production / waterwoods deploy | Safety constraint until explicit decision |
| Unsupported ROI (“saves X minutes”) | Metrics V1 explicitly unsupported |
| Full legal/compliance certification | Day 4 draft only |
| UX ledger L3 copy polish | Non-blocking; Stage 2 accepted |
| Large MCP platform rewrite | Day 5 is thin tools only |

---

## Daily stop rule

- Max three automated loops per day-lane objective (P20 Production Loop).  
- Stop on PASS for that day’s P0s; do not auto-start next day’s P1s.  
- Three failed loops with unresolved P0 → mark day **BLOCKED** and escalate to Founder.
