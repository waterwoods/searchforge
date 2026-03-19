# Final Readiness Risk Sweep Report

**Sprint:** Final Readiness Risk Sweep Sprint  
**Date:** 2026-03-07  
**Scope:** California Auto Insurance Broker Assistant only

---

## 1. Risks selected

| Risk | Why it mattered |
|------|-----------------|
| **Offline fallback copy drift (3 vs 5 questions)** | `run_demo_local.sh` and `demo_prepare_tomorrow.sh` said "3 sample questions" while broker demo has 5. Operator could look for 3 clickable items, miss 2, and think demo is broken. High confusion during fallback. |
| **Copy-to-client E2E marker gap** | `test_copy_to_client_e2e.py` only checked `经纪人可进一步询问`, not `经纪人下一步`. Both are broker-only in `demoCopy.ts`. E2E could pass while `经纪人下一步` leaked to client copy. |
| **No guardrail against 3/5 drift** | If someone reverted or changed run_demo_local to "3 sample questions", nothing would catch it. |
| **Stale docs (business rules)** | `insurance_broker_pilot_rules.md` R4 said "3 sample questions", inconsistent with actual 5. |

---

## 2. Changes made

| File | Change | Why it helps |
|------|--------|--------------|
| `scripts/run_demo_local.sh` | "3 sample questions" → "5 sample questions" (2 places: backend-fail note + Mode line) | Operator sees correct count when backend fails; no confusion during Offline mode. |
| `scripts/demo_prepare_tomorrow.sh` | "3 sample questions" → "5 sample questions" | Prep script matches actual demo behavior. |
| `scripts/test_copy_to_client_e2e.py` | Added `经纪人下一步` to `BROKER_ONLY_MARKERS` | E2E now filters both broker-only markers; no false-negative on copy-to-client. |
| `scripts/guardrail_broker_demo.sh` | New [5] check: fail if `run_demo_local.sh` contains "3 sample questions" | Prevents future drift; demo_pre_checklist will fail if someone reverts. |
| `ui/src/pages/DemoPage.css` | Comment: "3 sample questions" → "5 sample questions" | Codebase consistency. |
| `docs/business_rules/insurance_broker_pilot_rules.md` | R4: "3 sample questions" → "5 sample questions" | Rules match actual behavior. |

---

## 3. Re-test results

| Test | Result | Before vs after |
|------|--------|-----------------|
| `guardrail_broker_demo.sh` | PASS | Before: [4] checks. After: [5] checks; new [5] passes. |
| `verify_copy_to_client_guardrail.py` | PASS | Same; no regression. |
| `test_copy_to_client_e2e.py` | PASS | Same; now also filters `经纪人下一步`. |
| `demo_pre_checklist.sh` | PASS | Guardrail [0] passes; new [5] included. |
| Live broker regression | Not run | Backend was up; regression runs as part of demo_pre_checklist. |

**Summary:** All guardrails pass. No regression. Copy-to-client coverage improved.

---

## 4. Guardrail coverage check

| Area | Protection | Status |
|------|------------|--------|
| Q1–Q5 question consistency | broker_regression vs snapshot grep | ✅ Well protected |
| Offline pack (5 items, workflow hints) | guardrail [2] | ✅ Well protected |
| Copy-to-client (broker-only excluded) | verify_copy_to_client_guardrail + test_copy_to_client_e2e | ✅ Improved (both markers) |
| Runtime path (8001 default) | guardrail [4] | ✅ Well protected |
| Offline fallback copy (5 not 3) | guardrail [5] (new) | ✅ Now protected |

**Weakest remaining:** Long-tail (LT03/LT04) is not in guardrail. Snapshot/offline pack only covers Q1–Q5. LT03/LT04 are validated by `broker_regression_all5.py --longtail` but not in demo_fallback.json. **Decision:** No new guardrail for long-tail now; it's an enhancement path, not a readiness risk for the core 5-question demo.

**Verdict:** Current guardrails sufficient. One small high-value guardrail added: [5] offline fallback copy check.

---

## 5. Operator impact

| What Andy no longer needs to manually worry about | What Cursor/OpenClaw can now handle |
|---------------------------------------------------|-------------------------------------|
| "Is it 3 or 5 sample questions?" | Guardrail [5] fails if run_demo_local says "3". |
| "Did copy-to-client filter 经纪人下一步?" | test_copy_to_client_e2e now checks both markers. |
| Reverting 3→5 by mistake | Guardrail catches it on next demo_pre_checklist. |

**Default safe operating path:**
1. Before demo: `bash scripts/demo_pre_checklist.sh`
2. Start: `bash scripts/run_demo_local.sh`
3. If 503 embedding_warming: `bash scripts/restore_8001_readiness.sh`
4. If backend down mid-demo: Refresh, click **5** sample questions (Offline mode)

---

## 6. Remaining blocker(s)

None for broker demo readiness. Known non-blockers:
- Qdrant Cloud 503 when cluster paused → use `restore_8001_readiness.sh` or Offline mode
- Long-tail (SR-22, proof) not in offline pack → use Live path when backend up

---

## 7. Recommended next step for tomorrow

**Run `bash scripts/demo_pre_checklist.sh` before the next broker meeting.** If it passes (guardrail + validation), use Live path. If backend is down, use Offline path with the 5 sample questions. No new feature work; maintain current readiness.
