# Repo Audit + Milestone Commit Planning Report

**Sprint:** Repo Audit + Branch / Milestone Commit Planning Sprint  
**Created:** 2026-03-18  
**Scope:** SearchForge → Chen Kui Insurance Unified Entry  
**Execution mode:** Inspect → classify → propose → summarize

---

## 1. Current Repo State

### Branch

| Item | Value |
|------|-------|
| **Current branch** | `crowdstrike-ops-copilot` |
| **Ahead of origin** | 1 commit |
| **Ahead of main** | 6 commits |
| **Remote tracking** | `origin/crowdstrike-ops-copilot` |

### Working Tree

| Category | Count |
|----------|-------|
| **Modified** | 46 files |
| **Untracked** | 360 files |
| **Deleted** | 1 file (`docs/OPERATOR_STEP5B_DISCOVERY_MVP.md`) |

### Recent Commit Pattern (current branch)

```
8849ca5 feat: add one-click demo ingest for auto insurance assistant
1333016 JobHunter: add cache APIs and batch detail UI
166955f feat(jobhunter): implement caching and batch analysis endpoints
44e1f9d update: jobhunter clipper & batch export support
9889027 jobhunter-clipper: improve LinkedIn JD extraction
81f540a jobhunter-clipper: add chrome extension MVP
31572ca add offline eval report for mortage assit  ← main
```

**Observation:** The last 6 commits on `crowdstrike-ops-copilot` are ahead of `main`. The most recent is auto-insurance demo ingest; the prior 5 are JobHunter-focused. The branch name (`crowdstrike-ops-copilot`) does not reflect the current Chen Kui Insurance scope.

### Other Branches

| Branch | Purpose (inferred) |
|--------|---------------------|
| `main` | Canonical; last touched for mortgage eval |
| `develop` | Exists on origin |
| `feat/proxy-dockerhub-bypass` | Proxy / infra |
| `feat/steward-phase-b`, `feat/phase-b` | Steward / phase work |
| `feature/langgraph-integration` | LangGraph |
| `backup/20251108-221444` | Backup |
| `chore/build-cache-setup` | Build cache |

---

## 2. What the Project Has Evolved Into

### Original Scope (SearchForge)

- General RAG platform
- Mortgage assistant demo
- JobHunter (JD analysis, clipper, resume refinement)
- Vitals viewer / ingest
- Retrieval proxy, LangGraph, metrics UI
- Multi-vertical experiments

### Current Expanded Scope (Chen Kui Insurance Unified Entry)

Per `AGENTS.md`, `docs/goals/insurance_paid_pilot_goal.md`, and `docs/PROJECT_DOC_SYSTEM_MAP.md`:

- **Primary:** California auto insurance broker assistant
- **Target:** Chen Kui (陈奎) — first paid pilot
- **In scope:** Broker demo, auto insurance RAG, demo UI, validation scripts, **Unified Intake MVP** (inbox triage)
- **Out of scope:** JobHunter, mortgage, Vitals, Stripe, auth, multi-tenant

### Major Milestone Themes Now Present

| Theme | Evidence |
|-------|----------|
| **State / workflow backbone** | `LIGHTWEIGHT_STATE_MACHINE_BLUEPRINT`, `MATURE_INTAKE_SKELETON`, state field accuracy audits |
| **Scenario package** | `STANDARD_SCENARIO_PACKAGE`, 7 core scenarios, `configs/scenario_logic_center.json` |
| **Scenario Logic Center** | `docs/scenario_logic_center/`, `ScenarioLogicCenterPage.tsx`, recent sprint |
| **Trial package** | `docs/trial/`, `CHEN_KUI_TRIAL_PACK`, trial launch/readiness scripts |
| **Client-aware configuration** | `configs/clients/`, `configs/industries/`, `CLIENT_PACK_FOUNDATION` |
| **Unified Intake MVP** | Inbox triage API, `UnifiedIntakePage.tsx`, `run_inbox_triage_scenarios.py` |
| **UI polish** | Demo page, AddCarRulesPage, ReleaseIdentityBar, simulation components |
| **Deployment / verification** | Cloud Run, Vercel, `restore_8001_readiness.sh`, guardrail scripts |
| **Knowledge / config layer** | `KNOWLEDGE_ARCHITECTURE_AND_CONFIG_LAYER`, `configs/` structure |

---

## 3. Suggested Milestone Commit

### Best Commit Title

```
feat: Chen Kui Insurance Unified Entry — broker demo, trial pack, scenario logic center
```

**Why:** Captures the current product identity, the three main deliverables (demo, trial, scenario center), and is founder-readable.

### Alternatives

1. **`milestone: insurance paid pilot — broker demo, config layer, trial readiness`**  
   Emphasizes the business goal (paid pilot) and readiness.

2. **`feat: broker assistant — Unified Intake MVP, scenario package, trial pack`**  
   Emphasizes product features over client name.

### Why This Milestone Name Fits

- Aligns with `AGENTS.md` and `docs/goals/insurance_paid_pilot_goal.md`
- Reflects the accumulated work: config layer, scenario logic center, trial docs, Unified Intake, demo polish
- Distinct from prior JobHunter/mortgage commits
- Suitable as a single “state of the project” snapshot

---

## 4. Suggested Branch Strategy

### Model

| Branch | Role |
|--------|------|
| **main** | Relatively stable; merge when a milestone is ready |
| **chen-kui-insurance** (or keep current) | Working branch for broker/insurance work |
| **Feature branches** | Only for large, isolated efforts (e.g. `feat/unified-intake-v2`) |

### Why This Is Simple and Sane

- One primary working branch for the current theme
- `main` stays as the integration target
- No need for many long-lived branches
- Branch name `chen-kui-insurance` would better reflect scope than `crowdstrike-ops-copilot`; renaming is optional and can be done when convenient

### Optional Rename

If you want the branch name to match the product:

```bash
git branch -m crowdstrike-ops-copilot chen-kui-insurance
# Then: git push origin chen-kui-insurance
# And update remote tracking / delete old remote branch if desired
```

---

## 5. Safe Next Git Steps

### What to Stage

**Include:**

- `AGENTS.md`, `README.md`, `Makefile`, `requirements.txt`, `docker-compose.yml`, `.dockerignore`, `.env.example`, `.gitignore`
- `configs/` (README, clients, common, industries, scenario_logic_center.json, broker/inbox/scenario configs)
- `docs/` (goals, trial, scenario_logic_center, runbooks, guardrails, standards, PROJECT_DOC_SYSTEM_MAP, STANDARD_SCENARIO_PACKAGE, key sprint reports)
- `scripts/` (run_demo_local, demo_pre_checklist, restore_8001_readiness, guardrail_inbox_triage, trial_*, founder_pre_trial, run_inbox_triage_scenarios, etc.)
- `services/fiqa_api/` (inbox_triage, health, routes, search, translation, qdrant_adapter)
- `ui/` (UnifiedIntakePage, ScenarioLogicCenterPage, AddCarRulesPage, inboxTriage API, config, layout)
- `knowledge/` (if it belongs to the broker demo)

### What to Leave Out (for now)

- `scripts/.pids/*` — runtime PIDs
- `services/fiqa_api/jobhunter/jobhunter_cache.sqlite3` — local cache
- `tmp/` — temporary artifacts
- `experiments/jobhunter/*` — JobHunter experiments (out of scope)
- `~/` — stray file if present
- Large reports that are purely historical (consider `docs/archive/` later)

### Suggested Commit Order

**Option A — Single milestone commit**

1. Stage the “include” set above (excluding the “leave out” set)
2. Commit with: `feat: Chen Kui Insurance Unified Entry — broker demo, trial pack, scenario logic center`
3. Push to the working branch

**Option B — Two commits (if you prefer separation)**

1. **Commit 1:** Config + docs  
   - `configs/`, `docs/`, `AGENTS.md`, `README.md`  
   - Message: `docs: Chen Kui broker config layer, trial pack, scenario logic center`

2. **Commit 2:** Code + scripts  
   - `services/`, `ui/`, `scripts/`, root infra files  
   - Message: `feat: broker demo, Unified Intake, scenario center UI, validation scripts`

---

## 6. Founder-Friendly Summary

### Where the Repo Stands Now

- You’re on `crowdstrike-ops-copilot`, which is 6 commits ahead of `main`.
- There are **46 modified** and **360 untracked** files.
- The product has shifted from general SearchForge (mortgage, JobHunter, Vitals) to **Chen Kui Insurance Unified Entry** — a California auto insurance broker assistant aimed at a first paid pilot.
- The broker work (config layer, trial pack, scenario logic center, Unified Intake, demo polish) is mostly in modified/untracked state and not yet captured in a clear milestone commit.

### Why It Needs Cleanup

- The branch name doesn’t match the product.
- `main` is behind and doesn’t reflect the broker focus.
- A large amount of work is uncommitted; a milestone commit would create a clear snapshot and make it easier to reason about the current state.

### What Git Structure Makes Sense Now

1. **One milestone commit** that captures the Chen Kui broker work (config, docs, code, scripts).
2. **A simple branch model:** `main` for stability, one working branch for broker/insurance.
3. **Optional branch rename** from `crowdstrike-ops-copilot` to `chen-kui-insurance` when convenient.
4. **No destructive changes** — no force-push, no history rewrite unless you explicitly decide to do so.

---

*Report generated by Repo Audit + Milestone Commit Planning Sprint. No Git changes were made automatically.*
