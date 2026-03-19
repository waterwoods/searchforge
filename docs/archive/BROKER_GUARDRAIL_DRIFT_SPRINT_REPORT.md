# Broker Guardrail + Drift Prevention Sprint Report

## 1. Risks targeted

| Risk | Why it mattered | Current repo check | Still missing (before sprint) |
|------|-----------------|--------------------|-------------------------------|
| **Offline pack workflow drift** | When demo_quick_validate fails, snapshot never runs. Offline pack can become stale. If demo_fallback.json is missing, DEFAULT_FALLBACK_ITEMS had no workflow hints. | demo_pre_checklist reports workflow X/5 | No fail on drift; DEFAULT_FALLBACK lacked hints |
| **Validation vs snapshot question drift** | If someone adds Q6 to broker_regression but not snapshot (or vice versa), offline pack and validation diverge silently. | None | No consistency check |
| **Pre-demo path confusion** | Operator might run checklist without knowing it can fail on drift. No single "am I demo-ready?" gate. | demo_pre_checklist reports status | No --strict; no guardrail script |
| **DEFAULT_FALLBACK quality** | When JSON missing or &lt;3 items, DemoPage uses DEFAULT_FALLBACK_ITEMS. Those lacked 客户可准备 + 经纪人可进一步询问. | None | Offline fallback degraded when JSON missing |

**Top 4 addressed:** (1) Offline pack + DEFAULT_FALLBACK workflow alignment, (2) Question consistency guardrail, (3) Pre-demo --strict mode, (4) Single guardrail script.

## 2. Standards/docs created or updated

| File | What it defines | Why useful |
|------|-----------------|------------|
| `docs/BROKER_DEMO_QUALITY_STANDARD.md` | Core scenario coverage (Q1–Q5), workflow-helper expectations, offline pack alignment, copy-to-client cleanliness, pre-demo validation, regression/drift definitions, fail vs tolerate | Single source of truth for "what must be true before demo" |
| `docs/BROKER_DEMO_DRIFT_GUARDRAIL.md` | Guardrail scripts, what each checks, default pre-demo path, when to run, simulated drift examples | Operator and Cursor/OpenClaw know how to catch drift |
| `docs/BROKER_DEMO_OPERATOR_RUNBOOK.md` | Updated: guardrail as step 1, --strict for checklist, Key Paths table | Runbook now points to guardrail first |

## 3. Guardrails implemented

| Script/change | Protects | Fail/Warn |
|---------------|----------|-----------|
| `scripts/guardrail_broker_demo.sh` | (1) broker_regression and snapshot have same 5 questions; (2) demo_fallback.json exists with 5 items; (3) 5 items have 客户可准备 + 经纪人可进一步询问 | **Fail** (exit 1) |
| `scripts/demo_pre_checklist.sh --strict` | Workflow hints ≥ 5, offline pack ≥ 5 items, demo_fallback.json exists | **Fail** (exit 1) when --strict |
| `ui/src/pages/DemoPage.tsx` DEFAULT_FALLBACK_ITEMS | Offline fallback when JSON missing: all 5 now include 客户可准备 + 经纪人可进一步询问 | N/A (improves worst-case quality) |

## 4. Re-test results

| Test | Result |
|------|--------|
| `bash scripts/guardrail_broker_demo.sh` (healthy state) | PASS – question consistency OK, 5 items, 5/5 workflow hints |
| `bash scripts/demo_pre_checklist.sh --strict` (healthy state) | PASS – STRICT: All checks passed |
| Simulated drift: `demo_fallback.json` removed | Guardrail FAIL: "demo_fallback.json not found" |
| DEFAULT_FALLBACK_ITEMS | All 5 now have workflow hints; copy-to-client filter unchanged |

**Confidence:** Guardrail catches missing offline pack and question drift without backend. --strict catches workflow-hint drift. DEFAULT_FALLBACK ensures worst-case offline path still has broker value.

## 5. Manual-work reduction

| Before | After |
|--------|-------|
| Andy manually checks offline pack has workflow hints | `guardrail_broker_demo.sh` or `demo_pre_checklist.sh --strict` fails if not |
| Andy remembers to run snapshot after validate | Guardrail fails if offline pack drifts; operator knows to run demo_quick_validate |
| Andy wonders if broker_regression and snapshot match | Guardrail checks question consistency |
| DEFAULT_FALLBACK used when JSON missing → no workflow hints | DEFAULT_FALLBACK now has hints; offline path stays broker-useful |

**Cursor can now:** Run `guardrail_broker_demo.sh` to verify no drift before suggesting changes. Run `demo_pre_checklist.sh --strict` for pre-demo gate.

**OpenClaw can now:** Run guardrail in CI or scheduled check; fail build if drift detected.

**Default pre-demo guardrail path:**
```bash
bash scripts/guardrail_broker_demo.sh && bash scripts/demo_pre_checklist.sh
```
Use `--strict` on checklist to fail on workflow drift.

## 6. Future extraction note

| Reusable | California/broker-specific |
|----------|----------------------------|
| Guardrail pattern (question consistency, offline pack checks) | Q1–Q5 questions, 客户可准备/经纪人可进一步询问 strings |
| BROKER_DEMO_QUALITY_STANDARD structure | Scenario coverage table, workflow-helper expectations |
| Pre-demo gate flow (guardrail → checklist → validate) | Broker demo scripts, demo_fallback.json path |
| DEFAULT_FALLBACK with workflow hints | California auto insurance content |

**Later:** Broker quality standard template, guardrail pack, validation pack could be parameterized by region/vertical. Copy-to-client filter (BROKER_ONLY_MARKER) could become configurable.

## 7. Remaining blocker(s)

- None. Guardrail and --strict work. Backend 503 during live validate is environmental (Qdrant/LLM); offline path and guardrail do not require backend.

## 8. Recommended next sprint

**Single best next target:** Add a copy-to-client guardrail (unit test or small script) that verifies `buildCopyTextClientReady` excludes content containing 经纪人可进一步询问.

**Why:** Current filter is string-based. If someone adds a new broker-only phrase in query.py without updating BROKER_ONLY_MARKER, copy-to-client could leak. A test with a sample answer containing the marker would catch regressions.
