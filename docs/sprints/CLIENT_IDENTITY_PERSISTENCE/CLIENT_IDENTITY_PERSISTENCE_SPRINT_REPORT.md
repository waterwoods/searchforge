# Client Identity Persistence + End-to-End Client-Aware Flow Report

## 1. Sprint theme

- **What was chosen:** Persist `client_id` on cases; wire append/follow-up and reopen to use case client context; prove end-to-end A→B lifecycle variation.
- **Why now:** Client-aware handoff was wired at entry; lifecycle (append, reopen) still used env default. Founder could not yet say "Client A stays Client A through the whole flow."

---

## 2. Document set created

| Doc | Path |
|-----|------|
| Client Identity Persistence Blueprint | `docs/sprints/CLIENT_IDENTITY_PERSISTENCE/01_CLIENT_IDENTITY_PERSISTENCE_BLUEPRINT.md` |
| Case Lifecycle Client Context Spec | `docs/sprints/CLIENT_IDENTITY_PERSISTENCE/02_CASE_LIFECYCLE_CLIENT_CONTEXT_SPEC.md` |
| Append / Follow-Up Client-Aware Spec | `docs/sprints/CLIENT_IDENTITY_PERSISTENCE/03_APPEND_FOLLOWUP_CLIENT_AWARE_SPEC.md` |
| A/B End-to-End Variation Demo Spec | `docs/sprints/CLIENT_IDENTITY_PERSISTENCE/04_AB_END_TO_END_VARIATION_DEMO_SPEC.md` |
| Execution Outline | `docs/sprints/CLIENT_IDENTITY_PERSISTENCE/05_EXECUTION_OUTLINE.md` |
| Acceptance / Lifecycle Client-Aware Criteria | `docs/sprints/CLIENT_IDENTITY_PERSISTENCE/06_ACCEPTANCE_LIFECYCLE_CLIENT_AWARE_CRITERIA.md` |
| Founder Inspection Notes | `docs/sprints/CLIENT_IDENTITY_PERSISTENCE/07_FOUNDER_INSPECTION_NOTES.md` |

---

## 3. Baseline audit

| Area | Before | Classification |
|------|--------|----------------|
| Case persistence | No client_id | High-value to wire |
| save_case | Ignores client | High-value to wire |
| triage_for_append | Uses get_active_client_id() | High-value to wire |
| append_case_message route | No client context | High-value to wire |
| Workbench reopen | Append uses URL/env | Partially wired |

**Biggest weakness:** client_id not persisted on cases; append used env default.

**Biggest custom-project signal:** Append handoff wording depended on current URL or env, not case origin.

**Biggest A→B migration barrier:** Case created for Client A could produce Client B wording on append if URL switched.

---

## 4. 10–20 point breakdown

1. **client_id enters:** TriageRequest.client_id; frontend useClientConfig(); URL ?client=
2. **client_id was lost at:** save_case (not stored); triage_for_append (no param); append route (no case.client_id)
3. **client_id now persisted:** save_case(client_id=...); case["client_id"]
4. **Case fields updated:** client_id on case; _normalize_case preserves it
5. **Append discovers client:** case.get("client_id") → request.client_id → get_active_client_id()
6. **Reopen uses client:** Case has client_id; append uses it; no URL dependency
7. **Handoff outputs stay client-aware:** triage_for_append(client_id=...) → triage_conversation
8. **Backend defaults:** get_active_client_id() when case and request empty
9. **Fallback if client config missing:** Same as triage: chen_kui → generic
10. **Deferred:** add-car-rules client param; full tenancy
11. **A→B proof:** Create chen_kui case, append with ?client=demo_broker → draft stays 办公室
12. **Reuse:** New client = new folder; case remembers client through lifecycle
13. **Sales credibility:** "Case remembers which client it belongs to"
14. **Maintainability:** Single source of truth (case.client_id)
15. **Tests:** test_client_identity_append.py; guardrail step [11]
16. **Deployment:** Backend redeploy; frontend redeploy (appendFollowUpMessage clientId)
17. **Deferred:** add-car-rules client param; full multi-tenant
18. **Next platformization:** add-car-rules client param when Rules Center needs multi-client

---

## 5. Iteration loop 1

**What lifecycle problems were fixed:** client_id not persisted on cases; case creation ignored client.

**Why these fixes were chosen:** Highest-value slice; case is source of truth for append.

**What became more reusable:** Cases now carry client identity; append can discover it.

**What did not improve:** Append flow still used env default (fixed in loop 2).

**Worth it:** Yes — foundation for lifecycle continuity.

---

## 6. Iteration loop 2

**What lifecycle problems were fixed:** triage_for_append used env default; append route did not pass case.client_id.

**Why these fixes were chosen:** Append must use case client for handoff wording.

**What improved vs loop 1:** Append flow now client-aware; reopen preserves context.

**What still remained weak:** Legacy cases without client_id (mitigated by request fallback + backfill).

**Worth it:** Yes — end-to-end continuity achieved.

---

## 7. Iteration loop 3

**What end-to-end client-aware problems were fixed:** Verification script; guardrail step; founder inspection notes.

**Why these fixes were chosen:** Prove A/B variation; automated regression.

**What improved vs loop 2:** Guardrail enforces client identity persistence; founder can inspect.

**What still remained weak:** add-car-rules not client-aware; some hardcoded fallbacks.

**Worth it:** Yes — demonstrable proof.

---

## 8. Optional loop 4

**Whether used:** No.

**Reason:** Core lifecycle continuity achieved; add-car-rules and other refinements are lower priority.

---

## 9. Validation summary

| Check | Result |
|-------|--------|
| guardrail_inbox_triage.sh | PASS |
| run_inbox_triage_scenarios.py | PASS |
| run_multi_turn_simulations.py | PASS |
| verify_inbox_case_persistence.py | PASS |
| test_client_identity_append.py | PASS |

**Limitations:** Legacy cases without client_id use request or env fallback; no backfill on read.

---

## 10. Deployment / release judgment

- **Backend:** Redeploy needed (case_store, triage, routes changed)
- **Frontend:** Redeploy needed (appendFollowUpMessage, BrokerWorkbenchTab clientId)
- **Founder can inspect:** Yes — create case ?client=chen_kui, append with ?client=demo_broker open; draft stays 办公室

---

## 11. Founder showcase

| Example | Client A (chen_kui) | Client B (demo_broker) | Why better |
|---------|---------------------|------------------------|------------|
| Case creation | case.client_id = "chen_kui" | case.client_id = "demo_broker" | Persisted |
| Append (same URL) | Draft: 办公室 | Draft: 客服团队 | Correct |
| Append (URL switched) | Case A + ?client=demo_broker → draft: 办公室 | Case B + ?client=chen_kui → draft: 客服团队 | Case wins |
| Reopen | Case remembers client | Case remembers client | Lifecycle-deep |

**Why this helps reuse:** Same base product; client identity survives full flow.

**Why this helps selling:** "Case remembers which client it belongs to; append uses that, not the current page."

---

## 12. Final judgment

- **Biggest gain:** End-to-end client-aware continuity; case.client_id survives append/reopen.
- **Biggest remaining weakness:** add-car-rules not client-aware; legacy cases rely on fallback.
- **A→B migration meaningfully easier:** Yes — founder can explain lifecycle-deep variation.
- **Best next step:** Add client param to add-car-rules when Rules Center needs multi-client.

---

## 13. Iteration log

| Loop | What changed | Better vs prior | Did not improve | Worth it | Next step |
|------|--------------|-----------------|-----------------|----------|-----------|
| 1 | save_case(client_id); route passes it | Case has client_id | Append still env | Yes | Wire append |
| 2 | triage_for_append(client_id); route passes case.client_id | Append client-aware | Legacy cases | Yes | Verification |
| 3 | test_client_identity_append.py; guardrail [11] | Automated proof | add-car-rules | Yes | Deploy |

---

## 14. 中文宏观总结

**为什么现在做 end-to-end client-aware flow：** 入口已按 client 区分，但 case 创建、append、reopen 仍用 env 默认，导致 Client A 的 case 在 append 时可能变成 Client B 的措辞。

**主要方法/技术：** 在 case 上持久化 client_id；save_case 写入；triage_for_append 接受 client_id；append 路由从 case 读取并传入；前端 append 时传 clientId（legacy 回退）。

**这轮最大提升：** case 记住 client，append/reopen 全程使用 case.client_id，不再依赖当前 URL。

**还差什么：** add-car-rules 未按 client 区分；部分 legacy case 无 client_id 需 fallback。

**下一步最该做：** 当 Rules Center 需要多 client 时，为 add-car-rules 增加 client 参数。

---

## 15. COPY/PASTE FOUNDER BLOCK

**Biggest lifecycle client-aware improvement:** Case now stores client_id; append and reopen use it. Client A stays Client A through the whole flow, even if you switch ?client= in the URL.

**Biggest remaining weakness:** add-car-rules API not client-aware; legacy cases without client_id use URL/env fallback.

**More sellable/reusable:** Yes. Founder can say "case remembers which client it belongs to."

**Redeploy needed:** Yes — backend and frontend.

**What Andy should inspect next:** Create case with ?client=chen_kui, then open ?client=demo_broker, append "好的，收到" to that case. Draft should still say 办公室 (chen_kui), not 客服团队.

---

## 16. REQUIRED CROSS-WINDOW BLOCK

**Current client-reuse maturity:** Lifecycle-deep. client_id persisted on cases; append/reopen use case.client_id. Entry, persistence, append, reopen all client-aware.

**Biggest improvements:** save_case(client_id); triage_for_append(client_id); append route passes case.client_id; append_follow_up_message backfills client_id for legacy.

**Biggest remaining weaknesses:** add-car-rules not client-aware; legacy cases without client_id.

**Direction correct:** Yes. Minimal scope; no tenancy; proves A→B lifecycle variation.

**Best next recommendation:** Add client param to add-car-rules when Rules Center needs multi-client.

**Current IT technical backbone:** FastAPI backend (fiqa_api); React + Ant Design frontend; JSON case store (data/unified_intake_cases.json); configs/clients/{client_id}/; triage_conversation + triage_for_append.

---

## 17. REQUIRED SHORT OVERVIEW

### 为什么做这件事

入口已按 client 区分，但 case 创建、append、reopen 仍用 env 默认，导致 Client A 的 case 在 append 时可能变成 Client B 的措辞。需要让 client 身份贯穿全生命周期。

### 主要用了什么方法/技术

在 case 上持久化 client_id；save_case 写入；triage_for_append 接受 client_id；append 路由从 case 读取并传入；前端 append 时传 clientId（legacy 回退）；append_follow_up_message 对 legacy case 回填 client_id。

### 这轮最大的提升

case 记住 client，append/reopen 全程使用 case.client_id，不再依赖当前 URL。Client A 的 case 在 append 时保持 Client A 的措辞。

### 现在还差什么

add-car-rules 未按 client 区分；部分 legacy case 无 client_id 需 fallback。
