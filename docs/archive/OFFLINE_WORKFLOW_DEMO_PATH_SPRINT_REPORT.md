# Offline Workflow Alignment + Demo Path Unification Report

## 1. Issue targeted

**Offline alignment:** `demo_fallback.json` for Q1, Q2, Q3, Q5 lacked workflow-helper content (客户可准备, 经纪人可进一步询问). Only Q4 had it. Offline mode felt like a lower-quality fallback.

**Demo path confusion:** Docs and scripts mixed 8000 (Docker) and 8001 (run_demo_local) without a single clear default. Andy had to remember which path to use.

**Why they mattered:** Offline mode is the fallback when backend/Qdrant fails mid-demo. If offline answers lacked workflow hints, the demo would regress. Port confusion increased manual checking and mental load.

## 2. Changes made

| File | Change |
|------|--------|
| `ui/src/assets/demo_fallback.json` | Appended workflow hints (客户可准备 + 经纪人可进一步询问) to Q1, Q2, Q3, Q5 answers. Q4 already had them. |
| `docs/ANDY_2MIN_BEFORE_DEMO.md` | Added one-line demo path: `run_demo_local.sh` → 8001; Docker → 8000. |
| `scripts/run_demo_local.sh` | Header comment: default demo path 8001; Docker uses 8000. |
| `scripts/demo_quick_validate.sh` | Clarified port comment: 8001 = run_demo_local, 8000 = Docker. |
| `scripts/snapshot_demo_answers.py` | Docstring: demo path 8001, Docker 8000. |
| `scripts/demo_pre_checklist.sh` | Added workflow-hint check: reports "Workflow hints: X/5" and adds row to checklist. |

**Why it helps:** Offline Q1–Q5 now match live workflow-helper behavior. Pre-demo checklist catches stale offline pack. One default path (8001) is documented everywhere.

## 3. Re-test results

| Test | Result |
|------|--------|
| Offline pack workflow hints | 5/5 (客户可准备 + 经纪人可进一步询问 in all Q1–Q5) |
| demo_pre_checklist.sh | Reports "Workflow hints: 5/5" and "✅ Aligned" |
| Copy-to-client | demoCopy.ts filters 经纪人可进一步询问; 客户可准备 remains client-useful |
| DemoPage rendering | Splits on **客户可准备**, renders broker block under "经纪人工作流" |

**Before vs after:**
- Offline alignment: **Before** Q1,Q2,Q3,Q5 missing hints. **After** all 5 aligned.
- Operator clarity: **Before** mixed 8000/8001. **After** one default (8001) documented in ANDY_2MIN, run_demo_local, demo_quick_validate, snapshot_demo_answers.

## 4. Operator impact

- **Andy no longer needs to:** Remember which port to use for demo (8001 = default). Manually verify offline pack has workflow hints (checklist does it).
- **Cursor can now:** Re-run `demo_pre_checklist.sh` to validate offline pack alignment; re-run `demo_quick_validate.sh` for live validation.
- **Default demo path:** `bash scripts/run_demo_local.sh` → backend 8001, UI 5173.
- **Default fallback path:** Offline mode — click the 5 recommended questions; answers now include workflow hints.

## 5. Remaining blocker(s)

- Live validation (broker_regression_all5) may fail with 503 if Qdrant Cloud is paused or backend dependencies are down. Offline mode remains reliable.
- If using Docker (8000) for demo, set `VITE_API_PROXY_TARGET=http://127.0.0.1:8000` when running UI.

## 6. Recommended next sprint

**Single best next target:** Ensure `demo_quick_validate.sh` (on PASS) always refreshes `demo_fallback.json` via `snapshot_demo_answers.py` — it already does. Consider adding a pre-commit or CI check that runs `demo_pre_checklist.sh` and fails if workflow hints < 5/5, so offline pack cannot drift without notice.

**Why:** Automated guardrail prevents future drift when new workflow hints are added to query.py but snapshot is not re-run.

---

## Light future-readiness note

Without heavy refactoring, this sprint suggests:

- **Fallback pack:** `demo_fallback.json` is the canonical offline pack; keep it aligned via `demo_quick_validate.sh` (on PASS) or manual `snapshot_demo_answers.py`.
- **Workflow pack:** The broker hint pattern (客户可准备 + 经纪人可进一步询问) could later become a `workflow_pack` or `scenario_pack` with per-scenario templates, shared by both live and offline paths.
- **Runtime profile:** "Demo" profile = run_demo_local (8001); "Docker" profile = 8000. Scripts accept `--port` to switch.
- **Common demo orchestration base:** `run_demo_local.sh` + `demo_prep_one_command.sh` + `demo_pre_checklist.sh` form a coherent chain; consider a single `make demo` target that runs prep + checklist + launcher.

Documentation only. No heavy architecture changes.
