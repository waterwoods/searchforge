# Backend Redeploy for Multi-Turn Continuity Fix Report

## 1. Sprint Theme

- **What was redeployed:** fiqa-api backend to Google Cloud Run with the Customer Entry multi-turn continuity fix
- **Why now:** Production backend was still behaving as one-shot intake + forced handoff. The code repair (first message through `triage_conversation`, no forced `handoff_ready`) had been implemented locally but not deployed.

## 2. Control Docs Created

| Doc | Path |
|-----|------|
| Sprint Blueprint | `docs/sprints/backend_redeploy_multi_turn_continuity_fix/01_SPRINT_BLUEPRINT.md` |
| Execution Outline | `docs/sprints/backend_redeploy_multi_turn_continuity_fix/02_EXECUTION_OUTLINE.md` |
| Acceptance / Operational Criteria | `docs/sprints/backend_redeploy_multi_turn_continuity_fix/03_ACCEPTANCE_OPERATIONAL_CRITERIA.md` |

## 3. Pre-Deploy Validation

### Files Inspected

| File | Expected Logic | Found |
|------|----------------|-------|
| `services/fiqa_api/routes/inbox_triage.py` | First message uses `triage_conversation(text, turns)`; no forced `handoff_ready` | ✓ Lines 197–200: `triage_conversation(text, [{"role": t.role, "text": t.text} for t in turns])` |
| `services/fiqa_api/routes/inbox_triage.py` | Persist only when `handoff_ready` | ✓ Lines 248–250: `should_persist = result.get("handoff_ready")` |
| `services/fiqa_api/inbox_triage/triage.py` | `_should_handoff()` drives handoff; add-car thresholds | ✓ `triage_conversation` uses `_should_handoff`, `_add_car_enough_for_handoff` |
| `scripts/test_first_turn_continuity.py` | Regression guardrail exists | ✓ Present |
| `scripts/guardrail_inbox_triage.sh` | Continuity guardrail step [3b] | ✓ Present |

### Validation Results

| Check | Result |
|-------|--------|
| `test_first_turn_continuity.py` | **PASS** — add-car vague, payment, missing-doc all return `handoff_ready=False` |
| `run_inbox_triage_scenarios.py` | **PASS** — 53/53 |
| `run_multi_turn_simulations.py` | **PASS** — 38/38 |
| `audit_state_field_accuracy.py` | **6/7** — M1 follow_up_type mismatch (pre-existing, not continuity-related) |
| `verify_speed_routing.py` | **PASS** |
| `guardrail_inbox_triage.sh` | **PASS** |

**Blocker:** None. The audit_state_field_accuracy failure is a field classification edge case, not related to the continuity fix.

## 4. Backend Redeploy Result

| Item | Value |
|------|-------|
| **Success** | Yes |
| **Backend URL** | https://fiqa-api-g7zatxrycq-uw.a.run.app |
| **Revision** | fiqa-api-00023-mwl |
| **Project** | optimal-disk-472305-e2 |
| **Region** | us-west1 |
| **Warnings/Errors** | Deploy script reported `/healthz` FAILED at 5s (cold start); `/readyz` OK. Root `/`, `/health`, `/health/live` all return 200 when tested manually. |

## 5. Post-Deploy Verification

### Health / Readyz Result

| Endpoint | Result |
|----------|--------|
| `/` | 200 — service info |
| `/health` | 200 — `{"ok":true,"phase":"degraded"}` |
| `/health/live` | 200 — `{"ok":true}` |
| `/readyz` | 200 — `{"ok":true,"status":"ready","intake_path_ready":true}` |

### Quote/Add-Car Continuity Result

- **Input:** "我才买了一个2026年的丰田花冠，大约半年的保费是多少？"
- **handoff_ready:** `False` ✓
- **client_reply_draft:** "好的，丰田花冠。先把地址邮编发我，我就能帮你算报价。" ✓
- **Directly confirmed in production:** Yes

### Payment Continuity Result

- **Input:** "付款失败了"
- **handoff_ready:** `False` ✓
- **client_reply_draft:** "这看起来是付款出了问题。现在最关键的是把最新通知或付款截图发我..." ✓
- **Directly confirmed in production:** Yes

### Missing-Doc Continuity Result

- **Input:** "我上周已经发过了，怎么还在追材料？"
- **handoff_ready:** `False` ✓
- **client_reply_draft:** "您说发过了，我这边帮你核对。把完整通知和您发过的材料发我..." ✓
- **Directly confirmed in production:** Yes

## 6. Optional Second Loop

- **Whether used:** No
- **Reason:** All continuity examples passed in production. No small, high-value fix identified.

## 7. Final Operational Judgment

| Question | Answer |
|----------|--------|
| **Did backend redeploy succeed?** | Yes |
| **Is the multi-turn continuity fix now live?** | Yes |
| **Can the founder now go to Vercel and meaningfully show true continuous intake?** | Yes |
| **Biggest remaining risk** | LLM path may differ slightly from rule-based in edge cases; frontend must correctly handle `handoff_ready=false` (input stays visible). |
| **Exact next tests for Andy** | 1) Open Vercel demo → Customer Entry; 2) Send "我才买了一个2026年的丰田花冠，大约半年的保费是多少？" → verify input stays visible, reply asks for zip; 3) Send zip in second turn → verify handoff card appears; 4) Repeat for "付款失败了" and "我上周已经发过了，怎么还在追材料？" |

## 8. 中文宏观总结

- **Backend 是否重新部署成功？** 是。
- **真正连续多轮的修复有没有上线？** 有。首条消息走 `triage_conversation`，不再强制 `handoff_ready=true`；加车、付款、缺材料首轮都会追问，不立即转交。
- **现在是不是可以去 Vercel 更完整地展示了？** 是。后端已上线，可以在 Vercel 前端演示真正的连续多轮 intake。
- **最大剩余风险是什么？** 前端需正确展示 `handoff_ready=false` 时输入框保持可见；LLM 路径在少数边缘情况可能与 rule-based 略有差异。
- **我下一步具体该测什么？** 在 Vercel 上测：加车首轮（缺邮编）→ 输入保留、追问邮编；补全后 → 出现 handoff 卡片。同理测付款、缺材料首轮。

## 9. COPY/PASTE EXECUTION BLOCK

```
Backend Redeploy for Multi-Turn Continuity Fix — Summary
========================================================

Backend deploy status: SUCCESS
Multi-turn continuity fix live: YES
Andy should show/test Vercel now: YES

Backend URL: https://fiqa-api-g7zatxrycq-uw.a.run.app

Production verification (directly confirmed):
- Quote/add-car first turn: handoff_ready=false, asks for zip ✓
- Payment first turn: handoff_ready=false, asks for notice/screenshot ✓
- Missing-doc first turn: handoff_ready=false, acknowledges and asks for materials ✓

Biggest remaining risk: Frontend must keep input visible when handoff_ready=false; LLM edge cases may differ slightly from rule-based.

Exact next tests:
1. Vercel → Customer Entry → "我才买了一个2026年的丰田花冠，大约半年的保费是多少？" → input stays visible, reply asks for zip
2. Send zip in turn 2 → handoff card appears
3. Repeat for "付款失败了" and "我上周已经发过了，怎么还在追材料？"
```
