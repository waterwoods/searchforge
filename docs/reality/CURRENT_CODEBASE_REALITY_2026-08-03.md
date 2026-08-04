# Current Codebase Reality — 2026-08-03

**Status:** Authoritative capability classification SSOT  
**Branch / HEAD at write:** `stage2/langgraph-accident-story-assistant` @ `942fe68` (planning) over product tip `31abf61`  
**Cloud QA (observed):** `fiqa-api-qa-00054-l2s` · `https://fiqa-api-qa-g7zatxrycq-uw.a.run.app`  
**Production / waterwoods:** untouched by this audit  
**Rule:** Classify from code, tests, evidence, commit, tag, or live probe — not from design aspirations.

### Classification legend (exactly one per capability)

| Label | Meaning |
|-------|---------|
| IMPLEMENTED | Code exists on the product path |
| AUTOMATED TESTED | Focused automated tests pass on current branch |
| QA DEPLOYED | Live on Cloud QA service (probe or deploy evidence) |
| FOUNDER PHONE VALIDATED | Founder phone path completed with evidence pack |
| DOCUMENTED ONLY | Spec/plan/portfolio text without matching product proof |
| LAB ONLY | Exists under lab/experiments; not product_only dependency |
| DEFERRED | Explicitly out of this release |

A capability may satisfy multiple layers; the **row status** is the highest *completed* layer that is still honest (e.g. FOUNDER PHONE VALIDATED implies lower layers).

---

## Capability matrix

| Capability | Status | Proof |
|------------|--------|-------|
| Deterministic Claim workflow (intake → Request More → supplement → ack → office accept) | **FOUNDER PHONE VALIDATED** | Tag `stage1-founder-validated-demo-2026-08-03` · commit `826fa39` · `docs/evidence/STAGE1_FOUNDER_VALIDATED_CLOSEOUT.md` · case `case_4e5adf36c637` · tests e.g. `tests/test_happy_path_office_materials_accept.py`, `tests/test_broker_supplement_review_ack.py`, `tests/test_p20_send_request_command_service.py` |
| One Active Case | **AUTOMATED TESTED** (+ QA used in phone paths) | `docs/product/p0_one_active_case_identity_foundation.md` · Decision Log D-001 · server bind via `mp_customer_active_case` / demo-invite isolation · Stage 2 phone isolated identity `wx_qaiso_*` |
| Known-customer confirmation | **FOUNDER PHONE VALIDATED** | `docs/evidence/STAGE2_FOUNDER_VALIDATED_CLOSEOUT.md` · commit `8b6ca01` · case `case_09ad6254614a` · `tests/test_policy_context_prefill_confirm.py` · scenario `chen_camry_stage2_phone` |
| Request More + supplement review | **FOUNDER PHONE VALIDATED** | Stage 1 closeout VIN path · `tests/test_p20_send_request_command_service.py` · `tests/test_broker_supplement_review_ack.py` |
| Office acceptance | **FOUNDER PHONE VALIDATED** | Stage 1 closeout · `tests/test_happy_path_office_materials_accept.py` · open-Request-More accept block (commit `91b20af`) |
| Timeline and projections | **FOUNDER PHONE VALIDATED** | Stage 1/2 evidence timeline exports · `claim_workbench_display.py` Brief · constitution projection used in phone packs |
| Timing instrumentation (Real Usage Timing V1) | **QA DEPLOYED** + **AUTOMATED TESTED** | `docs/metrics/REAL_USAGE_TIMING_V1_CLOSEOUT.md` · commits `a7f7bf7`…`9051f41` · integrity pack `docs/evidence/real-usage-timing-v1/20260803T234426Z-integrity/` · `tests/test_case_activity_events.py`, `tests/test_export_case_value_metrics.py` · **not** a Founder phone product feature |
| LangGraph accident-story assistant | **QA DEPLOYED** + **AUTOMATED TESTED** | Code `services/fiqa_api/inbox_triage/accident_story_assistant/` · UI `miniapp/pages/start-claim/*` · commits `277e327`, `31abf61` · `tests/test_accident_story_langgraph.py` (13 PASS) · live QA `POST /api/h5/customer/accident-story/propose` → 200 on `fiqa-api-qa-00054-l2s` · Brief labels in `claim_workbench_display.py` · **FOUNDER PHONE VALIDATED: not yet** |
| LangSmith (Case Builder eval/tracing) | **LAB ONLY** / **DEFERRED** for product gate | Lab helpers `services/fiqa_api/observability/langsmith_tracing.py`, `telemetry/langsmith_config.py` · archive/lab docs · **no** Case Builder golden eval gate closed · PR B not started |
| AI Accept / Edit / Reject metrics | **DOCUMENTED ONLY** (gap) | Exporter note `unsupported:ai_accept_edit_reject_rates_no_events` in `tools/export_case_value_metrics.py` · Metrics closeout unsupported list · confirm API exists but rates not instrumented |
| MCP Broker tools (Case Builder) | **LAB ONLY** | `mcp/README.md` LAB ONLY · mortgage MCP under lab graphs · **not** mounted for product_only Case Builder |
| Security / RBAC / tenant isolation | **AUTOMATED TESTED** (partial) + **QA DEPLOYED** (pilot keys) | Paid-pilot keys in `CURRENT_PRODUCT_SHAPE.md` · Track C evidence `docs/evidence/p20_track_c_qa_reset_and_tenant_boundary_2026_07_12.md` · demo-invite office/scenario isolation tests · `tests/test_demo_invite_foundation.py` · full multi-tenant IAM **DEFERRED** |
| Privacy and retention policy | **DOCUMENTED ONLY** | No Founder-approved consent/retention packet for Case Builder yet · Day-4 plan item · metrics forbid accident text in activity events |
| Production release status | **DEFERRED** | No Production promotion authorized · closeouts explicitly exclude Production/waterwoods · gates forbid `PRODUCTION READY` without full proof |

---

## Live probes (2026-08-03)

| Probe | Result |
|-------|--------|
| `GET {QA}/health/live` | 200 |
| `POST {QA}/api/h5/customer/accident-story/propose` (valid body) | 200; `lifecycle_mutated=false`; missing location/injury → ≤2 follow-ups; `raw_story` preserved |
| Production targeted by this work | No |

---

## Automated review snapshot (this hardening loop)

Critical suite (LangGraph + Stage 2 policy + Request More/ack/accept + metrics + demo invite): **PASS** (`pytest` exit 0).  
Optional note: `tests/test_case_office_access.py::test_case_get_no_enforcement_legacy_open` failed with 401 in this environment (auth posture) — **not** used as LangGraph freeze evidence.

Broker Brief label unit proof (local): confirmed → `客户已确认（AI 辅助整理）`; unconfirmed → `AI 提议（未确认，不可当作事实）`.

---

## Explicit non-claims

- Not Production ready  
- Not real-customer / paid-pilot validated  
- Not verified ROI / time-saved  
- Not legal/compliance certified  
- LangSmith Case Builder gate not implemented  
- MCP Broker product tools not implemented  
