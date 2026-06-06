# P9 Final Audit — Broker Surface Collapse

**Sprint:** P9 BROKER_SURFACE_COLLAPSE  
**Date:** 2026-05-30  
**Plan:** [`P9_BROKER_SURFACE_PLAN.md`](./P9_BROKER_SURFACE_PLAN.md)

---

## TOP_30_BROKER_CONFUSIONS_REMAINING

| # | Confusion | Mitigation |
|---|-----------|------------|
| 1 | `/demo` vs workbench still in ANDY_QUICK_START | Acceptable — one line in BROKER_ONE_PAGER "what to ignore" |
| 2 | Simulation Assistant vs real paste | BROKER_TRIAL_PLAYBOOK Day 1 clarifies order |
| 3 | Customer Entry optional vs required | DEMO_STORY marks optional |
| 4 | Production vs local URL | Founder sends URL in Day 0 |
| 5 | Chinese vs English UI labels | Product is bilingual — no doc fix needed |
| 6 | "Case" vs "ticket" language | CUSTOMER_LANGUAGE_GUIDE |
| 7 | What Human confirmation means | BROKER_ONE_PAGER + playbook |
| 8 | Whether data leaves their office | Single-broker pilot — founder explains |
| 9 | Pricing not in repo | Business decision — placeholder in archived BROKER_PILOT_PACKAGE |
| 10 | Load founder demo queue naming | Could rename UI later — doc explains "sample cases" |
| 11 | 13 vs 10 cases in queue count | Runtime drift — docs say "sample cases" not exact count |
| 12 | Copy case snapshot button | Trial playbook mentions for support |
| 13 | Need an example? button | Self-explanatory in UI |
| 14 | Work now vs Waiting sections | CUSTOMER_LANGUAGE_GUIDE |
| 15 | Premium review vs renewal | Case focus labels in guide |
| 16 | Claim intake scope limits | BROKER_ONE_PAGER "not promising" |
| 17 | Multi-turn context limits | Don't over-promise in DEMO_STORY |
| 18 | Offline during trial | TRIAL_ONE_PATH escalation L3 |
| 19 | Assistant using product | BROKER_TRIAL_PLAYBOOK — same workflow |
| 20 | Where observation log goes | TRIAL_ONE_PATH feedback section |
| 21 | Difference trial vs pilot | TRIAL_ONE_PATH + one-pager |
| 22 | Standard scenario package doc | Engineer doc — broker uses playbook |
| 23 | BROKER_VALUE_VALIDATION_MEETING_PACK | Operator depth — not broker-facing |
| 24 | WeChat copy workflow | Manual copy — stated 3× across P9 docs |
| 25 | Carrier notice formatting | Paste raw — stated in demo story |
| 26 | SR-22 / DMV edge cases | Not lead scenarios — playbook says avoid leading |
| 27 | Mixed English/Chinese notices | Demo story shows example |
| 28 | Status field meanings | Lightweight — broker learns Day 1–3 |
| 29 | Business snapshot counts | DEMO_STORY — not production analytics |
| 30 | configs/clients/chen_kui | Internal — broker never sees |

---

## TOP_20_FOUNDER_CONFUSIONS_REMAINING

| # | Confusion | Mitigation |
|---|-----------|------------|
| 1 | OPERATOR_SURFACE vs FOUNDER_ONE_PATH overlap | Cross-linked; founder reads ONE_PATH first |
| 2 | founder_pre_trial vs trial_launch | ONE_PATH § validate clarifies |
| 3 | BROKER_VALUE_VALIDATION_MEETING_PACK vs DEMO_STORY | Meeting pack = operator depth |
| 4 | 15_MINUTE_ENGINEER_ONBOARDING vs ONE_PATH | Role split in README |
| 5 | SIMPLIFICATION_MASTER_PLAN vs P9 | P9 is customer surface; simplification is engineering |
| 6 | Archived trial specs still linked from old reports | Archive INDEX + banners |
| 7 | FIX_NOW_QUEUE_SPEC archived | Rules folded into TRIAL_ONE_PATH + template |
| 8 | pre_trial_review/ folder | Separate — not daily path |
| 9 | scenario_logic_center/ | Engineer — OPERATOR_IGNORE_LIST |
| 10 | Which 3 docs for Chen Kui | ONE_PAGER, TRIAL_PLAYBOOK, URL |
| 11 | deploy vs demo order | ONE_PATH sections numbered |
| 12 | Node 22 requirement | ONE_PATH links NODE_22_SETUP |
| 13 | summarize_readiness vs trial_launch | ONE_PATH § validate |
| 14 | guardrail vs demo_quick_validate | ANDY_QUICK_START for RAG; guardrail for intake |
| 15 | P8 vs P9 doc relationship | P8 = isolation; P9 = customer surface |
| 16 | BROKER_REPORTS_INDEX archaeology | Historical reports — not daily |
| 17 | UNIFIED_INTAKE_MVP_RUNBOOK | Operator — links updated in future if needed |
| 18 | Multi-agent operating model | Collaboration — not launch path |
| 19 | STANDARD_SCENARIO_PACKAGE | Engineer/business — playbook summarizes 5 scenarios |
| 20 | Git archive paths for moved docs | archive/p9_broker_surface/INDEX |

---

## TOP_20_TRIAL_CONFUSIONS_REMAINING

| # | Confusion | Mitigation |
|---|-----------|------------|
| 1 | 7-day vs 1-month pilot | Trial = 7 days; pilot offer = 1 month sentence |
| 2 | FIX_NOW_QUEUE_SPEC archived | Template still live |
| 3 | Trial observation template location | trial/INDEX |
| 4 | Kickoff folder moved | archive/kickoff — optional |
| 5 | REAL_BROKER_TRIAL_PACKAGE_BLUEPRINT archived | TRIAL_ONE_PATH replaces |
| 6 | Metrics spec archived | Success criteria in TRIAL_ONE_PATH |
| 7 | LAST_MILE_RISK spec archived | Failure criteria in TRIAL_ONE_PATH |
| 8 | HANDOFF spec archived | BROKER_TRIAL_PLAYBOOK |
| 9 | Founder final trial notes archived | TRIAL_ONE_PATH Day 0–7 |
| 10 | Trial scope spec archived | ONE_PAGER + playbook scope |
| 11 | Extended SIM4+ timing | Playbook Day 7 optional |
| 12 | results/trial_logs creation | trial_launch_check creates dir |
| 13 | Broker self-serve vs founder-guided | Playbook works both |
| 14 | Production trial without local | TRIAL_ONE_PATH allows prod URL |
| 15 | Observation log language | Chinese/English both fine |
| 16 | When to stop trial early | Failure criteria |
| 17 | Payment timing | Manual — not in product |
| 18 | Data export post-trial | Support/founder — not automated |
| 19 | Second broker trial | Same TRIAL_ONE_PATH |
| 20 | trial_readiness now checks 6 docs not 12 | Scripts updated |

---

## TOP_20_DEMO_CONFUSIONS_REMAINING

| # | Confusion | Mitigation |
|---|-----------|------------|
| 1 | Legacy RAG demo scripts in archive | DEMO_STORY is intake-only |
| 2 | BROKER_MEETING_PACKAGE archived | DEMO_STORY + BROKER_DEMO_FLOW |
| 3 | 5 RAG questions vs 3 intake cases | DEMO_STORY §7 never promise RAG as product |
| 4 | demo_pre_checklist checks RAG too | ANDY_QUICK_START explains both URLs |
| 5 | Offline mode on /demo only | BROKER_DEMO_FLOW backup = Simulation Assistant |
| 6 | warmup_for_demo.sh | Optional — BROKER_DEMO_FLOW |
| 7 | Chen Kui script archived | Folded into DEMO_STORY |
| 8 | Founder demo queue count | "Sample cases" wording |
| 9 | prepare_unified_intake_founder_demo.py | Engineer — not demo doc |
| 10 | Customer Entry first vs workbench first | DEMO_STORY 15-min order |
| 11 | Production demo latency | BROKER_DEMO_FLOW failure table |
| 12 | Value validation meeting pack overlap | Operator doc |
| 13 | POST_DEMO_FLOW archived | BROKER_DEMO_FLOW pre-demo |
| 14 | 2MIN_BEFORE_DEMO | Still valid quick ref |
| 15 | Copy-to-client on /demo | Wrong surface — workbench draft copy |
| 16 | Multiple demo timeboxes | DEMO_STORY 15/5/60 sec |
| 17 | Feedback form in archive | Verbal questions in BROKER_DEMO_FLOW |
| 18 | BROKER_DEMO_QUALITY_STANDARD | Engineer standard — not broker doc |
| 19 | guardrail failure mid-demo | BROKER_DEMO_FLOW — fix before demo |
| 20 | Live validate vs intake guardrail | Founder runs guardrail for intake demo |

---

## WHAT_BECAME_SIMPLER

| Before | After |
|--------|-------|
| 5+ broker-facing docs in `docs/` root | 3: ONE_PAGER, DEMO_FLOW, TRIAL_PLAYBOOK |
| CHEN_KUI_* + FOUNDER_DEMO_SOP + FOUNDER_LAUNCH_PATH | FOUNDER_ONE_PATH |
| 17 trial specs + 7 kickoff specs | TRIAL_ONE_PATH + 2 templates |
| Scattered demo scripts/docs | DEMO_STORY (one narrative) |
| Engineer terms in broker path | CUSTOMER_LANGUAGE_GUIDE |
| trial_readiness checks 12 files | 6 P9 docs |
| trial_launch checks 6 scattered trial specs | 6 canonical P9 paths |

**Archived:** 35 files → `docs/archive/p9_broker_surface/` (all bannered, git mv)

---

## WHAT_BECAME_MORE_SELLABLE

- **One-sentence value** repeated consistently across one-pager, demo story, trial path
- **5 core scenarios** table — broker sees office fit immediately
- **Explicit "not promising"** list — trust through honesty
- **7-day trial** with clear success/failure criteria
- **Pilot offer sentence** in Chinese — copy-paste ready
- **Why pay** table on one-pager — problem → outcome mapping

---

## WHAT_BECAME_MORE_DEMOABLE

- **THE_15_MINUTE_DEMO**, **THE_5_MINUTE_DEMO**, **THE_60_SECOND_DEMO** in one file
- **Cancellation first** — consistent demo order everywhere
- **Backup path** documented (Simulation Assistant)
- **BROKER_DEMO_FLOW** — checklist format for founders
- **What NOT to say** — repeated in demo story + demo flow

---

## WHAT_BECAME_MORE_TRIALABLE

- **Day 0 / 1 / 3 / 7** structure in TRIAL_ONE_PATH
- **BROKER_TRIAL_PLAYBOOK** — broker self-serve readable
- **Observation log + fix-now template** — only templates kept live
- **Support escalation L1–L4** in TRIAL_ONE_PATH
- **trial_launch_check** prints P9 doc paths

---

## WHAT_FOUNDERS_SHOULD_IGNORE

- `docs/archive/p9_broker_surface/` (unless debugging history)
- `docs/archive/sprints/` sprint archaeology
- Pre-P9 founder/trial specs (archived)
- Kickoff blueprint folder (archived)
- BROKER_REPORTS_INDEX for daily ops
- ~470 scripts — see OPERATOR_SURFACE (~10 matter)
- platform language — use CUSTOMER_LANGUAGE_GUIDE when talking to brokers

---

## WHAT_BROKERS_SHOULD_IGNORE

- Entire `docs/` tree except ONE_PAGER + TRIAL_PLAYBOOK (founder sends these)
- `/demo` page, Simulation Assistant IDs, Load founder demo queue internals
- Backend status, Qdrant, deployment, guardrails
- Repo, scripts, configs/clients/

---

## WHAT_SUPPORT_SHOULD_IGNORE

- Sprint reports, P7/P8/P9 plans (unless escalated to engineering)
- Trial spec archaeology
- Lab stack, platform_full, AutoTuner
- Broker demo RAG wedge unless explicitly in scope

**Support should read:** SUPPORT_TRUTH_MAP + CUSTOMER_LANGUAGE_GUIDE

---

## THE_3_DOCS_THAT_MATTER_TO_CUSTOMERS

1. [`BROKER_ONE_PAGER.md`](./BROKER_ONE_PAGER.md) — what, why, try, support
2. [`BROKER_TRIAL_PLAYBOOK.md`](./BROKER_TRIAL_PLAYBOOK.md) — 7-day trial
3. [`BROKER_DEMO_FLOW.md`](./BROKER_DEMO_FLOW.md) — if live demo scheduled

---

## THE_3_DOCS_THAT_MATTER_TO_FOUNDERS

1. [`FOUNDER_ONE_PATH.md`](./FOUNDER_ONE_PATH.md) — everything operational
2. [`TRIAL_ONE_PATH.md`](./TRIAL_ONE_PATH.md) — trial week
3. [`DEMO_STORY.md`](./DEMO_STORY.md) — demo narrative

---

## FINAL_VERDICT

**PASS** — Chen Kui can understand what it is, why he would pay, how to try it, and how to get support within 15 minutes using BROKER_ONE_PAGER alone. Founder has one path (FOUNDER_ONE_PATH). Demo and trial each have one story/path. 35 overlapping docs archived with banners. Launch scripts updated to verify P9 surface. No runtime, API, deploy, or auth code changed.

---

## FINAL_ONE_LINE

**P9 collapsed the broker-visible surface to three customer docs, three founder docs, and one language guide — everything else is archived, bannered, and pointed home.**

---

*End of P9 final audit*
