# Client-Aware Handoff / Triage Wiring Report

## 1. Sprint theme

- **What was chosen:** Wire `client_id` into backend triage/handoff flow; load handoff phrases by client; prove A→B variation at API level.
- **Why now:** UI already varies by client; backend handoff still used Chen-Kui-specific wording. Founder could not yet say "handoff and backend behavior change by client."

---

## 2. Document set created

| Doc | Path |
|-----|------|
| Client-Aware Handoff Blueprint | `docs/sprints/CLIENT_AWARE_HANDOFF_WIRING/01_CLIENT_AWARE_HANDOFF_BLUEPRINT.md` |
| Backend Client Context Wiring Spec | `docs/sprints/CLIENT_AWARE_HANDOFF_WIRING/02_BACKEND_CLIENT_CONTEXT_WIRING_SPEC.md` |
| Client Handoff Phrase Wiring Spec | `docs/sprints/CLIENT_AWARE_HANDOFF_WIRING/03_CLIENT_HANDOFF_PHRASE_WIRING_SPEC.md` |
| A/B Variation Demo Spec | `docs/sprints/CLIENT_AWARE_HANDOFF_WIRING/04_AB_VARIATION_DEMO_SPEC.md` |
| Execution Outline | `docs/sprints/CLIENT_AWARE_HANDOFF_WIRING/05_EXECUTION_OUTLINE.md` |
| Acceptance / Client-Aware Criteria | `docs/sprints/CLIENT_AWARE_HANDOFF_WIRING/06_ACCEPTANCE_CLIENT_AWARE_CRITERIA.md` |
| Founder Inspection Notes | `docs/sprints/CLIENT_AWARE_HANDOFF_WIRING/07_FOUNDER_INSPECTION_NOTES.md` |

---

## 3. Baseline audit

| Area | Before | Classification |
|------|--------|----------------|
| `get_handoff_phrases()` | Hardcoded `configs/clients/chen_kui/` | Too hardcoded |
| `triage_conversation` | No client_id param | High-value to wire |
| TriageRequest | No client_id | High-value to wire |
| Fallback wording | "陈奎办公室" | Chen-Kui-specific |
| demo_broker | No handoff_phrases.json | Configurable but not wired |

**Biggest weakness:** Handoff phrases loaded from fixed chen_kui path; no client_id in triage path.

**Biggest custom-project signal:** "陈奎办公室" in fallbacks and config path.

**Biggest A→B migration barrier:** New client required code/config path change, not just new folder.

---

## 4. 10–20 point breakdown

1. **Current hardcoded areas:** `get_handoff_phrases()` path, fallback "陈奎办公室", triage_conversation no client_id.
2. **client_id selection:** Request body `client_id`, else `CLIENT_ID` env, else `chen_kui`.
3. **Triage outputs client-aware:** `client_reply_draft` for customer_requested_human, add_car, remove_car, other, other_received, other_corrected, other_clarification.
4. **Handoff phrases differ:** customer_requested_human (办公室 vs 客服团队), add_car, remove_car, other variants.
5. **Reassurance copy differs:** Same keys as handoff.
6. **Backend defaults:** When client config missing, fallback to chen_kui; when both missing, generic "办公室" (no 陈奎).
7. **Fallback behavior:** `configs/clients/{client_id}/handoff_phrases.json` → chen_kui → {}.
8. **Too risky now:** Full tenancy, client_id on persisted cases, triage_for_append client-aware.
9. **Remains common:** broker_next_step, client_prep (English internal), classification logic.
10. **A vs B API proof:** POST triage with `client_id=demo_broker` vs `chen_kui` → different `client_reply_draft`.
11. **Validation:** `scripts/test_client_aware_handoff.py`, guardrail step [10].
12. **A→B migration:** New client = new folder + handoff_phrases.json; no code change.
13. **Sales credibility:** Founder can say "handoff and backend behavior change by client."
14. **Maintainability:** Single config file per client for handoff wording.
15. **Tests:** guardrail_inbox_triage.sh, test_client_aware_handoff.py.
16. **Deployment:** Backend redeploy needed; frontend redeploy needed (clientId in triage payload).
17. **Deferred:** add-car-rules API client-aware, triage_for_append, client_id on cases.
18. **Next platformization:** client_id on cases for append; add-car-rules client param.

---

## 5. Iteration loop 1

**What was fixed:** client_id wired into triage path; `get_handoff_phrases(client_id)`; `triage_conversation(client_id=...)`; TriageRequest.client_id; route passes client_id.

**Why these fixes:** Highest-value slice: make handoff phrases loadable by client.

**What became more reusable:** Handoff phrases now loaded from `configs/clients/{client_id}/`.

**What did not improve:** add-car-rules, triage_for_append still use default.

**Worth it:** Yes — core path now client-aware.

---

## 6. Iteration loop 2

**What was fixed:** Created `configs/clients/demo_broker/handoff_phrases.json`; frontend passes clientId to triageMessage; fallback "陈奎办公室" → "办公室".

**Why these fixes:** Prove A/B variation; reduce Chen-Kui-specific fallback.

**What improved vs loop 1:** Real A/B demo; demo_broker returns "客服团队" in drafts.

**What remained weak:** why_still_chasing, handoff_suffix, other_corrected still hardcode "办公室".

**Worth it:** Yes — founder can demonstrate variation.

---

## 7. Iteration loop 3

**What was fixed:** Added "联系客服" to talk_to_agent markers; `scripts/test_client_aware_handoff.py`; guardrail step [10].

**Why these fixes:** demo_broker starter "我想联系客服" must trigger talk_to_agent; automated proof.

**What improved vs loop 2:** Robust A/B test; guardrail enforces client-aware behavior.

**What remained weak:** Same as loop 2.

**Worth it:** Yes — demo and validation hardened.

---

## 8. Optional loop 4

**Used:** No.

**Reason:** Core handoff paths client-aware; remaining hardcoding is edge cases (why_still_chasing, etc.). Stopping is correct — scope was "smallest useful path that proves the concept."

---

## 9. Validation summary

| Check | Result |
|-------|--------|
| `run_inbox_triage_scenarios.py` | 64/64 passed |
| `guardrail_inbox_triage.sh` | PASS |
| `test_client_aware_handoff.py` | PASS |
| Multi-turn simulations | 41 strong |
| Simulation Assistant | 27 normal |

**Limitations:** API test (step 3) skipped when no server; add-car-rules not client-aware.

---

## 10. Deployment / release judgment

| Component | Redeploy needed |
|-----------|-----------------|
| Backend | Yes — config_loader, triage, route changed |
| Frontend | Yes — triageMessage(clientId), useClientConfig clientId |

**Founder can inspect:** After redeploy, use `?client=demo_broker` vs default; paste "我想联系客服" → draft should say "客服团队."

---

## 11. Founder showcase

| Example | Client A (chen_kui) | Client B (demo_broker) | Why better |
|---------|---------------------|------------------------|------------|
| Talk to Agent | "已帮您转给陈奎办公室" | "已帮您转给客服团队" | Handoff wording matches client branding |
| Add-car handoff | "办公室会尽快出价" | "客服团队会尽快出价" | Same |
| Other handoff | "办公室会尽快处理" | "客服团队会尽快处理" | Same |

**Reuse:** New client = new folder + handoff_phrases.json. No code change.

**Selling:** "When you change the client, the handoff messages change too—not just the UI labels."

---

## 12. Final judgment

- **Biggest gain:** Backend handoff phrases now client-aware; A→B migration materially lighter.
- **Biggest remaining weakness:** why_still_chasing, handoff_suffix, other_corrected still hardcode "办公室"; add-car-rules not client-aware.
- **A→B migration easier:** Yes — one config folder per client.
- **Best next step:** Add client_id to persisted cases for append flow; optionally add client param to add-car-rules API.

---

## 13. Iteration log

| Loop | What changed | Better vs prior | Not improved | Worth it | Next |
|------|--------------|-----------------|--------------|----------|------|
| 1 | client_id in triage, get_handoff_phrases(client_id) | Core path client-aware | add-car-rules, append | Yes | Create demo_broker config |
| 2 | demo_broker handoff_phrases, frontend clientId, fallback | A/B proof, less Chen-Kui | Edge-case hardcoding | Yes | Harden demo, tests |
| 3 | "联系客服" marker, test script, guardrail step | Robust validation | Same | Yes | Stop |

---

## 14. 中文宏观总结

- **为什么现在做 client-aware handoff wiring：** UI 已按 client 变化，但后端 handoff 仍用陈奎专用措辞；创始人无法完整说「handoff 和 backend 行为也按 client 变化」。
- **主要方法/技术：** 在 TriageRequest 和 triage_conversation 中传入 client_id；config_loader 按 client_id 加载 handoff_phrases；前端从 ClientConfigContext 取 clientId 传给 triage API。
- **这轮最大提升：** 后端 handoff 措辞可按 client 配置；A→B 迁移只需新增 config 文件夹，无需改代码。
- **还差什么：** why_still_chasing 等少数边缘路径仍硬编码「办公室」；add-car-rules API 未按 client 区分。
- **下一步最该做：** 在 case 上持久化 client_id，供 append 流程使用；或为 add-car-rules 增加 client 参数。

---

## 15. COPY/PASTE FOUNDER BLOCK

**Biggest client-aware handoff improvement:** Backend handoff phrases now load by client. Chen Kui gets "办公室/陈奎办公室"; demo_broker gets "客服团队." Same triage logic, different config.

**Biggest remaining weakness:** A few edge-case strings (e.g. "为什么还在追" reply) still hardcode "办公室." Add-car-rules API uses default client.

**More sellable/reusable:** Yes. New client = new folder + handoff_phrases.json. No code change.

**Redeploy needed:** Yes — backend and frontend.

**What Andy should inspect next:** Open `/workbench/unified-intake?client=demo_broker`, paste "我想联系客服", confirm draft says "客服团队." Switch to `?client=chen_kui` (or omit), same flow, confirm "办公室" or "陈奎办公室."

---

## 16. REQUIRED CROSS-WINDOW BLOCK

**Current client-reuse maturity:** Backend handoff phrases now client-aware. UI copy and handoff drafts both vary by client. No tenancy/auth.

**Biggest improvements:** client_id in triage path; get_handoff_phrases(client_id); demo_broker handoff_phrases.json; frontend passes clientId; A/B test in guardrail.

**Biggest remaining weaknesses:** why_still_chasing/handoff_suffix/other_corrected hardcode "办公室"; add-car-rules not client-aware; client_id not on cases.

**Direction correct:** Yes. Smallest useful path that proves concept.

**Best next recommendation:** Persist client_id on cases for append; add client param to add-car-rules when Rules Center needs multi-client.

**Current IT backbone:** FastAPI backend (Cloud Run), React/Vite frontend (Vercel), configs in repo (configs/clients/{id}/), no DB for cases (JSON file).

---

## 17. REQUIRED SHORT OVERVIEW

### 为什么做这件事

UI 已按 client 变化，但后端 triage/handoff 仍用陈奎专用措辞。创始人无法完整说「handoff 和 backend 行为也按 client 变化」。需要把 client 配置延伸到后端 handoff 路径。

### 主要用了什么方法/技术

- TriageRequest 增加 client_id；triage_conversation 增加 client_id 参数
- config_loader.get_handoff_phrases(client_id) 从 configs/clients/{id}/ 加载
- 前端 useClientConfig().clientId 传给 triageMessage
- demo_broker handoff_phrases.json 使用「客服团队」替代「办公室」

### 这轮最大的提升

后端 handoff 措辞可按 client 配置；A→B 迁移只需新增 config 文件夹，无需改代码；创始人可演示 Client A 与 Client B 在 handoff 上的真实差异。

### 现在还差什么

少数边缘路径（如 why_still_chasing）仍硬编码「办公室」；add-car-rules API 未按 client 区分；case 上未持久化 client_id。
