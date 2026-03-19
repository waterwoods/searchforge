# Runtime Path Standardization Sprint Report

## 1. Inconsistencies targeted

| Issue | Why it mattered |
|-------|-----------------|
| **ANDY_QUICK_START.md** had no path or recovery info | First file Andy reads; he had to infer ports from other docs |
| **e2e_zh_demo_check.sh** defaulted to 8000 while comment said 8001 | Demo validation script sent requests to wrong port when run without `--port` |
| **dev_local.sh** used 8000 with no context | Could imply 8000 is "normal" for local dev; broker demo uses 8001 |
| **ANDY_2MIN_BEFORE_DEMO.md** lacked explicit recovery path | Recovery action was only in ANDY_IF_SOMETHING_GOES_WRONG |
| **BROKER_DEMO_OPERATOR_RUNBOOK.md** had no runtime path section | Runbook didn't state default/alternate/recovery |
| **BROKER_DEMO_CHECKLIST.md** had no path or recovery row | Checklist didn't remind operator of recovery when live fails |
| **No single canonical doc** for path rules | Principle scattered; easy to drift |

## 2. Changes made

| File | Change |
|------|--------|
| `docs/RUNTIME_PATH_STANDARD.md` | **New.** Single source of truth: default 8001, Docker 8000, recovery `restore_8001_readiness.sh` |
| `docs/ANDY_QUICK_START.md` | Added runtime path line at top; added embedding_warming recovery in "If live fails" |
| `docs/ANDY_2MIN_BEFORE_DEMO.md` | Added recovery path inline: `restore_8001_readiness.sh` when 503 embedding_warming |
| `docs/BROKER_DEMO_OPERATOR_RUNBOOK.md` | Added "Runtime Path" table (default 8001, Docker 8000, recovery) + link to standard |
| `docs/BROKER_DEMO_CHECKLIST.md` | Added runtime path line; added 503 embedding_warming recovery row under "If Live Fails" |
| `scripts/e2e_zh_demo_check.sh` | Changed default `PORT` from 8000 to 8001; added comment |
| `scripts/dev_local.sh` | Added header: 8000 = this script; broker demo = run_demo_local.sh on 8001 |
| `scripts/demo_pre_checklist.sh` | Added header comment referencing RUNTIME_PATH_STANDARD |
| `scripts/restore_8001_readiness.sh` | Added echo line pointing to RUNTIME_PATH_STANDARD.md at end |
| `scripts/guardrail_broker_demo.sh` | Added [4] Runtime path check: run_demo_local + demo_pre_checklist use 8001; standard doc exists |

## 3. Re-test results

| Check | Result |
|-------|--------|
| 8001 clearly default path | ✅ ANDY_QUICK_START, ANDY_2MIN, runbook, checklist, RUNTIME_PATH_STANDARD all state 8001 |
| 8000 clearly alternate/Docker | ✅ RUNTIME_PATH_STANDARD, dev_local, runbook, ANDY_2MIN state 8000 = Docker |
| Recovery path documented | ✅ ANDY_QUICK_START, ANDY_2MIN, checklist, runbook, RUNTIME_PATH_STANDARD all mention `restore_8001_readiness.sh` |
| Guardrail passes | ✅ `bash scripts/guardrail_broker_demo.sh` → PASS (including [4] Runtime path) |
| e2e_zh_demo_check default | ✅ Now 8001 (was 8000) |

**Before vs after:** Before = mixed 8000/8001, recovery only in ANDY_IF_SOMETHING_GOES_WRONG. After = one canonical doc, all operator-facing docs reference it, guardrail enforces key scripts.

## 4. Guardrail added

| What | Protects | How |
|------|----------|-----|
| `guardrail_broker_demo.sh` [4] | Accidental change of default path in broker scripts | Greps run_demo_local.sh and demo_pre_checklist.sh for 8001; verifies RUNTIME_PATH_STANDARD.md exists. Runs on every `demo_pre_checklist.sh`. |

## 5. Operator impact

| Before | After |
|--------|-------|
| Andy had to remember which port for demo | **Default path = 8001.** One rule. |
| Recovery action buried in troubleshooting doc | **Recovery = `bash scripts/restore_8001_readiness.sh`** — in quick start, 2min checklist, runbook, checklist |
| e2e_zh_demo_check defaulted to wrong port | Default 8001; use `--port 8000` only when using Docker |
| dev_local vs run_demo_local unclear | dev_local header: "broker demo = run_demo_local.sh on 8001" |

**New default operating rule:** Use `run_demo_local.sh` for broker demo → backend 8001. If 503 embedding_warming → `restore_8001_readiness.sh`. Docker = 8000, validation scripts accept `--port 8000`.

## 6. Remaining blocker(s)

None. Sprint complete.

## 7. Recommended next sprint

**Topic:** Demo prep automation (e.g., one-command "demo ready" that starts backend + UI + runs checklist).

**Why:** Runtime path is now standardized. Next highest operator friction is manual sequencing of run_demo_local + demo_pre_checklist + opening browser. A single "demo ready" flow could reduce that.
