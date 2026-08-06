# SearchForge Reusable Capability Catalog V1

**Date:** 2026-08-05  
**Purpose:** Inventory platform assets already built — reuse before rewrite.  
**Evidence bar:** code path + test and/or Founder/QA evidence. Docs alone do not count.

**Maturity scale:** `Founder-validated` · `QA-synthetic` · `Automated-only` · `Partial` · `Lab`

---

## Catalog (16 capabilities)

| # | Capability | What it does | Evidence | Business problem solved | Reusable across | Maturity | Missing proof |
|---|------------|--------------|----------|-------------------------|-----------------|----------|---------------|
| 1 | Message → structured draft case | Turns free text into structured fields without owning lifecycle | `accident_story_assistant/` · Mini Program guided view · Stage1/Guided packs | Customers cannot fill insurance forms from chaos stories | Claim intake; future WeChat paste; renewal notes | Founder-validated (UX) / QA-synthetic (LLM) | Real-customer edit rates |
| 2 | Known-customer lookup + prefill confirm | Loads policy context; customer confirms before use | Stage2 closeout · `tests/test_policy_context_prefill_confirm.py` | Wrong-vehicle / wrong-policy mistakes | Claim, endorsement, renewal | Founder-validated | Multi-office CRM depth |
| 3 | One-active-case routing | Prevents stranded/duplicate active cases per customer identity | `mp_customer_active_case` · demo-invite isolation tests · phone packs | Duplicate cases / stuck sessions | Any customer Mini Program workflow | Founder-validated | Broad production traffic |
| 4 | Request More / customer continuation | Broker asks; customer completes; read-after-write | Stage1 VIN path · `tests/test_p20_send_request_command_service.py` | WeChat chase for missing docs | Docs, photos, VIN, future AI-suggested asks | Founder-validated | AI-drafted request copy |
| 5 | Customer-confirmed AI facts | Facts authoritative only after confirm stamp | Guided Intake · Brief labels · confirm events | Brokers treating AI draft as truth | Any AI extraction wedge | Founder-validated | Real office adherence metrics |
| 6 | Original / AI proposal / confirmed separation | Three-layer Brief truth model | `tests/test_accident_story_broker_brief_layers.py` · scorecard | Auditability; dispute reduction | All AI-assisted intake | QA-synthetic + unit | Real broker training outcomes |
| 7 | Bounded LangGraph orchestration | Propose→normalize→extract→validate→≤3 Q; no lifecycle mutation | `graph.py` · `tests/test_accident_story_langgraph.py` | Contained AI without agent sprawl | Adjacent assistive workflows | Automated + Guided Founder UX | Second workflow graph reuse demo |
| 8 | Deterministic fallback | Timeout/invalid/kill → manual intake usable | `guardrails.py` · pilot-safety tests · case 5 rehearsal | AI outage must not stop office | All LLM features | QA-synthetic | Multi-day live outage drill |
| 9 | PII-safe tracing | Redacted traces; suppress raw story; clean pilot project | langsmith-pr-b · freeze cleanup evidence | Compliance / portfolio safety | Any traced AI node | QA-synthetic | Long-run retention policy sign-off |
| 10 | Golden datasets + evaluators | Offline `accident_story_v1` 20/20 | `evaluators.py` · `run_accident_story_langsmith_eval.py` | Regression before enable | New AI wedges need parallel goldens | Automated | Real-case golden expansion |
| 11 | Feature flags + kill switches | Instant disable + office allowlist + LLM/tracing gates | `flags.py` · runbooks · rehearsal kill-switch PASS | Safe pilot / rollback | Every new AI surface | QA-synthetic | Prod runbook rehearsal (forbidden until GO) |
| 12 | Durable metrics | Postgres events for proposals, fallbacks, latency, completion | `durable_events.py` · export scripts · canary packs | Measure pilot without screenshots | Timing + AI quality gates | QA-synthetic | Real five-case metric pack |
| 13 | Broker next-action projection | Workbench shows clear next action | Claim projections · five-case scorecard “next_action=yes” | Office queue clarity | All case types | Founder-validated (claim) / synthetic (AI cases) | AI-suggested next action |
| 14 | Timeline + auditability | CaseEvent trail for customer/broker actions | Stage1/2 evidence exports · constitution projections | Trust, training, disputes | Compliance-sensitive offices | Founder-validated | External auditor review |
| 15 | Pilot release gates | Explicit PASS vocabulary; no false “Production Ready” | `ACCIDENT_STORY_RESTRICTED_PILOT_GATES_V1.md` · rehearsal closeout | Prevent premature launch | Future wedges | Process validated | Real GO execution |
| 16 | Coarse intake/support API keys + product_only surface | Perimeter for pilot SaaS without full IAM | `CURRENT_PRODUCT_SHAPE.md` · validate_pilot_deploy_env | Safe enough single-office pilot | Paid pilot packaging | Partial (not full RBAC) | OAuth/SSO (excluded) |

---

## Platform pattern (reuse recipe)

For any new AI wedge, reuse this stack in order:

1. Deterministic system of record + commands  
2. Bounded graph or pure functions for proposals  
3. Human confirmation before authority  
4. Three-layer display (original / proposal / confirmed)  
5. Kill switch + deterministic fallback  
6. Golden eval + redacted traces  
7. Durable metrics + release gate vocabulary  

Do **not** start with a new agent framework or Production flag flip.

---

## Explicit non-capabilities (do not catalog as shipped)

| Item | Why excluded |
|------|--------------|
| Coverage / liability AI advice | Deliberately excluded from pilot box |
| Carrier claim submit automation | Not built; high compliance risk |
| MCP Broker Case Builder tools | Lab only |
| Verified time-saved ROI dollars | No real-office measurement yet |
| Multi-tenant enterprise IAM | Partial / deferred |

---

## Count

**Reusable capabilities evidenced above: 16**  
**Highest-leverage reuse targets for next wedge:** #4 Request More continuation, #5–7 confirm + LangGraph pattern, #8–12 safety/eval/metrics stack, #13 next-action projection.
