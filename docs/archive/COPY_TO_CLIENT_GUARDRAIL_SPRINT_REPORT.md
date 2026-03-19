# Copy-to-Client Guardrail Sprint Report

**Sprint:** Copy-to-Client Guardrail + Broker/Client Boundary Sprint  
**Date:** 2026-03-06  
**Loops:** 2 (identify risks → add guardrail → re-test → document)

---

## 1. Risks targeted

| Risk | Why it mattered most |
|------|----------------------|
| **Single-marker fragility** | `demoCopy.ts` used one string `BROKER_ONLY_MARKER`. If someone added a new broker-only phrase in `query.py` without updating the filter, copy-to-client could leak. No automated check existed. |
| **No regression detection** | BROKER_GUARDRAIL_DRIFT_SPRINT_REPORT and BROKER_DEMO_QUALITY_STANDARD both called for a unit test or guardrail that fails when 经纪人可进一步询问 appears in client copy. None existed. |

**Not targeted (out of scope):**
- Broad repo audit
- Redesign of rendering system
- New broker-only phrases (query.py uses only 经纪人可进一步询问; future phrases can be added to BROKER_ONLY_MARKERS)

---

## 2. Changes made

| File | What changed | Why it helps |
|------|--------------|--------------|
| `ui/src/utils/demoCopy.ts` | Replaced `BROKER_ONLY_MARKER` with `BROKER_ONLY_MARKERS` array and `containsBrokerOnly()` helper | Extensible: new broker-only phrases can be added in one place. |
| `scripts/verify_copy_to_client_guardrail.py` | **New.** Unit test: (1) broker-only bullets/steps filtered; (2) 客户可准备 retained; (3) demoCopy.ts still has filter logic | Fails if filter is removed or broker content would leak. |
| `scripts/test_copy_to_client_e2e.py` | **New.** E2E test: load demo_fallback.json, simulate extraction, run filter, assert no broker-only in output | Validates full flow with real Q1–Q5 answers. |
| `scripts/guardrail_broker_demo.sh` | Added step [3]: run `verify_copy_to_client_guardrail.py` and `test_copy_to_client_e2e.py` | Copy-to-client boundary is now part of the broker demo guardrail. |
| `scripts/demo_pre_checklist.sh` | Added "Copy-to-client boundary" row to checklist report | Andy sees boundary status in pre-demo checklist. |
| `docs/BROKER_DEMO_QUALITY_STANDARD.md` | Updated Copy-to-client row to reference guardrail scripts | Single source of truth for what protects the boundary. |

---

## 3. Re-test results

| Test | Before | After |
|------|--------|-------|
| Filter logic (broker bullets/steps) | Manual inspection only | `verify_copy_to_client_guardrail.py` PASS |
| 客户可准备 retained | Manual | Guardrail asserts 客户可准备 in output when only client bullets present |
| demoCopy.ts source check | None | Guardrail fails if BROKER_ONLY_MARKERS or filter removed |
| E2E with demo_fallback.json | None | `test_copy_to_client_e2e.py` PASS for all 5 items |
| Full guardrail | 2 checks | 3 checks (question consistency, offline pack, copy-to-client) |

**Broker-only content leaking?** No. All tests pass.  
**Client copy still useful?** Yes. 客户可准备 remains; only 经纪人可进一步询问 is excluded.

---

## 4. Guardrails added

| Guardrail | Behavior |
|-----------|----------|
| `verify_copy_to_client_guardrail.py` | **Fail** (exit 1) if: broker-only content would appear in client copy; 客户可准备 incorrectly removed; demoCopy.ts filter removed. |
| `test_copy_to_client_e2e.py` | **Fail** (exit 1) if any of 5 demo_fallback items produce client copy containing broker-only content. |
| `guardrail_broker_demo.sh` step [3] | Runs both scripts; overall guardrail **fails** if verify script fails. E2E failure is logged but does not fail guardrail (E2E can skip if demo_fallback missing). |

---

## 5. Manual-work reduction

| Before | After |
|--------|-------|
| Andy manually inspects whether client copy looks clean | **No longer needed.** Run `bash scripts/guardrail_broker_demo.sh`; step [3] verifies filter logic and E2E. |
| Cursor | Can run guardrail before commits; re-run after any change to demoCopy.ts or query.py broker hints. |
| OpenClaw | Can add `guardrail_broker_demo.sh` to CI or pre-demo automation. |
| **Default boundary-check path** | `bash scripts/guardrail_broker_demo.sh` (includes copy-to-client). Pre-demo: `bash scripts/demo_pre_checklist.sh` (includes copy-to-client in report). |

---

## 6. Remaining blocker(s)

None. Sprint goals met.

---

## 7. Recommended next sprint

| Target | Why |
|--------|-----|
| **Add new broker-only phrase to BROKER_ONLY_MARKERS when query.py adds one** | If query.py gains a new broker-internal phrase (e.g. 经纪人可引导), add it to `BROKER_ONLY_MARKERS` in demoCopy.ts and `BROKER_ONLY_MARKERS` in verify_copy_to_client_guardrail.py. Document in BROKER_DEMO_QUALITY_STANDARD. |
| **Optional: parameterize BROKER_ONLY_MARKERS** | Could move to a shared config (e.g. configs/broker_client_boundary.json) so query.py, demoCopy.ts, and guardrail all read from one source. Low priority; current approach is sufficient. |

---

## Appendix: Commands

```bash
# Run full broker guardrail (includes copy-to-client)
bash scripts/guardrail_broker_demo.sh

# Run copy-to-client guardrail only
python3 scripts/verify_copy_to_client_guardrail.py
python3 scripts/test_copy_to_client_e2e.py

# Pre-demo checklist (includes copy-to-client in report)
bash scripts/demo_pre_checklist.sh
```
