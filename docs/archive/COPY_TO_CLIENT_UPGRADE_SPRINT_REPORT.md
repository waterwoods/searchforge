# Multi-Agent Guided Product Execution Report

**Sprint:** Client-Ready Copy Upgrade Sprint  
**Date:** 2026-03-07  
**Duration:** ~25 min closed loop

---

## 1. Weakness targeted

**Copy-to-client structure:** The 客户可准备 (what client should prepare) content was mixed into bullets and steps under "建议您：", making it less clear and less natural for client-facing messages. The broker had to mentally separate "what you need to bring" from "what you should do" when pasting into WeChat.

**Why it mattered most:** A broker sends copy to clients to reduce typing and explanation. If the client sees "建议您：1. 客户可准备：车辆信息、驾照..." the phrasing feels broker-internal ("客户" = client, but the client is reading it). A dedicated "您可准备" (what you can prepare) section is more natural and actionable for the recipient.

---

## 2. Changes made

| File | Change |
|------|--------|
| `ui/src/utils/demoCopy.ts` | Extract 客户可准备 from bullets/steps; surface as dedicated **您可准备** section before 建议您; use client-facing tone |
| `scripts/verify_copy_to_client_guardrail.py` | Replicate new logic in sim; Test 2 now asserts 您可准备 + prep content retained |
| `scripts/test_copy_to_client_e2e.py` | Update build_client_copy to match demoCopy.ts (您可准备 section) |
| `docs/BROKER_DEMO_QUALITY_STANDARD.md` | Document 您可准备 section in Copy-to-Client Cleanliness |

**Before (example Q1):**
```
【可直接转发给客户】

加州最低责任险：人身伤害 15,000/30,000，财产损失 5,000

• 建议加保碰撞险和综合险保护新车
• 可向多家保险公司询价比较

建议您：
1. 客户可准备：车辆信息、驾照、VIN（如有）
2. 确认加州最低责任险要求
...
```

**After (example Q1):**
```
【可直接转发给客户】

加州最低责任险：人身伤害 15,000/30,000，财产损失 5,000

• 建议加保碰撞险和综合险保护新车
• 可向多家保险公司询价比较

您可准备：
车辆信息、驾照、VIN（如有）

建议您：
1. 确认加州最低责任险要求
...
```

---

## 3. Re-test results

| Test | Result |
|------|--------|
| `verify_copy_to_client_guardrail.py` | PASS |
| `test_copy_to_client_e2e.py` | PASS |
| `guardrail_broker_demo.sh` | PASS |

**Before vs after:** Better — 客户可准备 is now a dedicated 您可准备 section; broker-only content still excluded; structure clearer for client.

---

## 4. Business impact

- **Broker usefulness:** Client copy now clearly separates "what to prepare" from "what to do next." Less mental editing before sending.
- **Repetitive work:** Broker no longer needs to manually rewrite "客户可准备" as "您可准备" or reorder content.
- **Economic value:** Cleaner, more natural client messages → higher likelihood of broker adoption and paid pilot conversion.

---

## 5. Multi-agent execution quality

- **Doc system:** BROKER_WORKFLOW_DEPTH_SPRINT_REPORT explicitly recommended "客户可准备 surfaced as dedicated 您可准备 section" — doc-first worked.
- **Smooth:** Guardrails (verify_copy_to_client_guardrail, test_copy_to_client_e2e) caught regressions; small inspect→improve→retest loop.
- **Weak:** E2E extraction heuristic differs from buildHighlights; some scenarios (e.g. Q2 with many steps) may not surface 客户可准备 if extraction slices it out. Live UI with buildHighlights may behave better due to scenario fallbacks.

---

## 6. Manual-work reduction

- **Andy no longer needs to:** Manually change "客户可准备" to "您可准备" or reorder copy before pasting to clients.
- **Cursor can now:** Run `guardrail_broker_demo.sh` to validate copy-to-client structure; guardrail asserts 您可准备 surfaced.
- **OpenClaw can now:** Use same guardrail for automated validation; test_copy_to_client_e2e validates full flow.

---

## 7. Remaining blocker(s)

None. Optional: improve buildHighlights extraction so 客户可准备 is prioritized when many steps exist (e.g. Q2), ensuring 您可准备 appears in more scenarios.

---

## 8. Recommended next sprint

**Target:** Improve buildHighlights extraction to prioritize 客户可准备 when present in answer, so 您可准备 appears even when step list is long (e.g. Q2 suspension scenario).

**Why:** Current heuristic takes first 5 steps; 客户可准备 may be 6th. A small tweak (e.g. always include 客户可准备 line in extraction when present) would increase coverage.
