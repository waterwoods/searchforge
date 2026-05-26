# Safe Reduction Baseline Checkpoint

**Created:** 2026-05-26 03:46 local (20260526-0346)  
**Purpose:** Trusted, recoverable Git checkpoint before simplification/reduction work.  
**Operator:** Cursor agent (checkpoint-only; no business-logic changes)

---

## Phase 0 — Current Git Inventory (pre-checkpoint)

| Item | Value |
|------|-------|
| **Branch (before checkpoint)** | `sprint/scoped-broker-identity-office-operational-safety` |
| **Stash count** | 16 (`stash@{0}` … `stash@{15}`) |

### Recent history (pre-checkpoint)

```
f14f755 sprint: pilot SaaS survivability — deployment drift warnings + SSOT
0c2ed6d productize: validate workbench queue and continue frontend decoupling
…
```

### Modified tracked files (40)

```
 M AGENTS.md
 M configs/demo.env.example
 M docs/DEPLOYMENT_READINESS.md
 M docs/PROJECT_DOC_SYSTEM_MAP.md
 M docs/runbooks/DEPLOYMENT_PLAYBOOK.md
 M docs/sprints/PILOT_SAAS_SURVIVABILITY_OFFICE_TRUST_HARDENING_SPRINT.md
 M scripts/check_unified_intake_prod_posture.sh
 M scripts/deploy_and_verify_cloud_run.sh
 M scripts/deploy_rag_demo.sh
 M scripts/support_deployment_manifest_smoke.py
 M scripts/trial_readiness_check.sh
 M services/fiqa_api/analytics/triage_funnel.py
 M services/fiqa_api/app_main.py
 M services/fiqa_api/db/schema/stage1_service_record.sql
 M services/fiqa_api/db/service_record_repository.py
 M services/fiqa_api/db/service_record_settings.py
 M services/fiqa_api/deployment_profile.py
 M services/fiqa_api/inbox_triage/active_vehicle_resolver.py
 M services/fiqa_api/inbox_triage/case_lifecycle.py
 M services/fiqa_api/inbox_triage/case_store.py
 M services/fiqa_api/inbox_triage/case_truth_repository.py
 M services/fiqa_api/inbox_triage/session_repository.py
 M services/fiqa_api/inbox_triage/session_store.py
 M services/fiqa_api/routes/analytics_dashboard.py
 M services/fiqa_api/routes/inbox_triage.py
 M tests/test_case_binding.py
 M tests/test_case_routing.py
 M tests/test_case_truth_repository.py
 M tests/test_deployment_profile.py
 M tests/test_intake_session_persistence.py
 M tests/test_minimal_analytics.py
 M tests/test_new_issue_append_enforcement.py
 M tests/test_support_export_gate.py
 M ui/src/api/inboxTriage.ts
 M ui/src/api/triageResultContract.ts
 M ui/src/components/intake/caseLifecycleDisplay.ts
 M ui/src/components/layout/AppSider.tsx
 M ui/src/features/intake/utils/intakePure.ts
 M ui/src/pages/UnifiedIntakePage.tsx
 M ui/src/vite-env.d.ts
```

**Diff stat (tracked only):** 40 files changed, 2264 insertions(+), 2026 deletions(-)

### Untracked files (pre-checkpoint, 86 paths)

- 8 top-level planning docs under `docs/`
- 38 new sprint/planning docs under `docs/sprints/`
- 11 new scripts under `scripts/`
- 14 new/expanded source files under `services/fiqa_api/`
- 13 new test files under `tests/`
- 1 new UI config: `ui/src/config/productSurface.ts`
- 37 generated artifacts under `results/` (excluded from commit; see Phase 5)

### Stash list (unchanged — not popped/applied)

```
stash@{0}:  On frontend-phase1-extract: pre-frontend-phase1-5
stash@{1}:  On final-mainline-convergence: pre-frontend-phase1
stash@{2}:  On resolver-final-convergence: pre-doc-finalize-ci
stash@{3}:  On resolver-takeover-final: pre-master-blueprint-audit
stash@{4}:  On active-fix-final-20260426-2106: pre-case-io-decouple
stash@{5}:  On assist-decouple-final-20260426-2036: pre-final-active-fix
stash@{6}:  On live-latency-20260426-0724: pre-latency-sprint
stash@{7}:  On live-latency-20260426-0724: pre-latency-sprint
stash@{8}:  On prod-parity-latency-20260426-0104: pre-pg-truth-pipeline
stash@{9}:  On pg-llm-live-chaos-20260425-2138: pre-ambiguity-clarify-sprint
stash@{10}: On active-vehicle-resolver-20260425-1916: pre-pg-multivehicle
stash@{11}: On llm-chaos-validation-0114: pre-entity-checkout-untracked
stash@{12}: On llm-chaos-validation-0114: pre-active-vehicle-resolver
stash@{13}: On add-car-scenario-hardening-20260424-0037: pre-long-evolution
stash@{14}: On 20260420-v2: pre-long-auto-evolution-sprint
stash@{15}: On 20260420-v2: pre-deploy: stash local WIP (not in deploy)
```

---

## Phase 1 — File Classification

| Class | Description | Count / examples |
|-------|-------------|------------------|
| **A — Intentional source** | Modified + new application code, tests, deploy scripts | 40 modified + 39 new source/test/script files |
| **B — Sprint / planning docs** | `docs/*.md`, `docs/sprints/*.md` | 8 + 38 = 46 doc files |
| **C — Generated results / logs** | `results/*.json`, `results/*.md`, `results/.lockin_start_ts` | 37 files (local benchmark/regression output) |
| **D — Env / secret-risk** | `.env`, `.env.cloudrun`, `ui/.env.local` etc. | Present on disk; **all ignored by `.gitignore`**; not staged |
| **E — Temporary** | None in changed/untracked set | — |
| **F — Large files** | Models, data, Qdrant WAL, logs (>5M) | Ignored (`data/`, `models/`, `.qdrant/`, `logs/`, `cache/`) |
| **G — Unknown / review** | None blocking checkpoint | — |

**Sprint doc inventory:** `find docs/sprints -maxdepth 2 -type f | wc -l` → **1009** files total in tree (includes pre-existing sprint subdirs).

---

## Phase 2 — SECRET_RISK_REPORT

Searched changed/untracked files for: `OPENAI_API_KEY`, `SERVICE_RECORD_DATABASE_URL`, `DATABASE_URL`, `PRIVATE_KEY`, `SECRET`, `TOKEN`, `API_KEY`, `BEARER`, `PASSWORD`, `QDRANT_API_KEY`, `GCP`, `GOOGLE_APPLICATION_CREDENTIALS`.

### Safe to commit

| File | Key / pattern | Notes |
|------|---------------|-------|
| `configs/demo.env.example` | `OPENAI_API_KEY`, `DATABASE_URL`, `SECRET`, etc. | Commented placeholders only (`USER:PASS@HOST`) |
| `scripts/deploy_rag_demo.sh` | `QDRANT_API_KEY`, `OPENAI_API_KEY` | Shell variable references / placeholders |
| `tests/test_validate_pilot_deploy_env.py` | `SERVICE_RECORD_DATABASE_URL` | Fake test value `postgresql://u:p@h/db` |
| All other matched files | Env var **names** in docs/tests/scripts | Documentation and validation logic only |

### Should not commit

| File | Key | Status |
|------|-----|--------|
| `.env` | Multiple | Ignored; real local secrets |
| `.env.cloudrun` | `SERVICE_RECORD_DATABASE_URL` | Ignored; contains real Neon credentials (`npg_***REDACTED***`) |
| `.env.current`, `.env.bandit`, `ui/.env`, `ui/.env.local` | Various | Ignored |

### Needs redaction

None in staged/committed files.

### Unknown

None blocking checkpoint.

**No actual secret values were committed.** Real credentials exist only in ignored `.env*` files on disk.

---

## Phase 3 — GITIGNORE_REVIEW

| Pattern | Covered? | Rule |
|---------|----------|------|
| `.env` | Yes | `.gitignore:5:.env` |
| `.env.*` | Yes | `.gitignore:6:.env.*` |
| `*.log` | Yes | line 60 |
| `results/` | **Added this checkpoint** | line 22 (was missing; caused 37 untracked result files) |
| `node_modules/` | Yes | line 40 |
| `dist/` | Yes | line 31 |
| `build/` | Yes | line 30 |
| `.DS_Store` | Yes | line 58 (`*.DS_Store`) |
| Service account JSON | Partial | No explicit `*.json` service-account rule; `data/` and local cred paths ignored |
| Private key files | Partial | No explicit `*.pem` rule; no private keys in changed set |

### Minimal patch applied

```diff
 # Generated artifacts, data, and logs
+results/
 .runs/
```

**Rationale:** `results/` held local benchmark JSON/MD artifacts not intended for version control. Narrow, obvious safety fix.

---

## Phase 4 — Safety Branch

| Item | Value |
|------|-------|
| **Checkpoint branch** | `checkpoint/before-simplification-execution-20260526-0346` |
| **Created from** | `sprint/scoped-broker-identity-office-operational-safety` @ `f14f755` |

---

## Phase 5 — Commit Strategy

**Chosen: Strategy A — clean baseline commit**

**Why:**

- All WIP is intentional sprint work (scoped broker identity / office operational safety + SaaS foundation docs).
- No secrets detected in files to be committed.
- `results/` clearly generated — excluded deliberately (not blind `git add -A`).
- 16 stashes left untouched per rules.

**Excluded from commit:**

- All `results/` artifacts (37 files) — now gitignored
- All `.env*` files — already gitignored
- Stashes — not applied

---

## Phase 6 — Baseline Commit

| Item | Value |
|------|-------|
| **Commit** | `307585770b388430db0a672fc91c3d1aa4a1eb9b` |
| **Message** | `checkpoint: pre-reduction safe restore point` |
| **Files committed** | 126 |
| **Stat** | 22510 insertions(+), 2969 deletions(-) |
| **Tag** | `checkpoint/pre-reduction-safe-restore-point-20260526-0346` |

---

## Phase 7 — Recovery Verification

Post-commit:

```
git status --short   → clean (0 untracked)
git log --oneline -3 → 3075857 checkpoint: pre-reduction safe restore point
                       f14f755 sprint: pilot SaaS survivability …
                       0c2ed6d productize: validate workbench queue …
git tag --list "checkpoint/pre-reduction-safe-restore-point*"
                       → checkpoint/pre-reduction-safe-restore-point-20260526-0346
```

### Rollback instructions

**Return to checkpoint branch:**

```bash
git switch checkpoint/before-simplification-execution-20260526-0346
```

**Inspect checkpoint:**

```bash
git show --stat checkpoint/pre-reduction-safe-restore-point-20260526-0346
# or
git show --stat 307585770b388430db0a672fc91c3d1aa4a1eb9b
```

**Start reduction work from checkpoint:**

```bash
git switch -c reduction/batch-1 checkpoint/before-simplification-execution-20260526-0346
```

**Hard reset to checkpoint (destructive — discards later commits on current branch):**

```bash
git reset --hard checkpoint/pre-reduction-safe-restore-point-20260526-0346
```

> **Warning:** Only use `git reset --hard` after confirming no uncommitted work is needed. Stashes (`stash@{0}`–`stash@{15}`) are separate and unaffected.

---

## Phase 8 — Final Summary

| # | Item | Value |
|---|------|-------|
| 1 | Branch before checkpoint | `sprint/scoped-broker-identity-office-operational-safety` |
| 2 | Checkpoint branch | `checkpoint/before-simplification-execution-20260526-0346` |
| 3 | Strategy | **A — clean baseline commit** |
| 4 | Commit hash | `307585770b388430db0a672fc91c3d1aa4a1eb9b` |
| 5 | Tag | `checkpoint/pre-reduction-safe-restore-point-20260526-0346` |
| 6 | Files committed | 126 (source, tests, scripts, sprint/planning docs, `.gitignore` patch) |
| 7 | Intentionally not committed | 37 `results/` artifacts; all `.env*` local files; 16 stashes |
| 8 | Secret risk | **Low** — real creds only in ignored env files; committed files use placeholders/tests |
| 9 | `.gitignore` change | Added `results/` |
| 10 | Remaining dirty files | **None** (working tree clean) |
| 11 | Stash count | 16 (unchanged) |
| 12 | Rollback | See Phase 7 commands above |
| 13 | Safe to start Batch 1? | **Yes** — tag + branch + clean tree |

### FINAL_ONE_LINE

**Yes — we now have a trustworthy rollback point before reduction work** (`checkpoint/pre-reduction-safe-restore-point-20260526-0346` @ `3075857`, clean working tree, secrets excluded, WIP captured).
