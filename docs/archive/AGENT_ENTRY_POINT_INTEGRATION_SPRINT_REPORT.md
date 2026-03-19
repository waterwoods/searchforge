# Agent Entry-Point Integration Sprint Report

**Sprint:** Agent Entry-Point Integration  
**Date:** 2026-03-07  
**Scope:** California Auto Insurance Broker Assistant only

---

## 1. Entry-point issues targeted

| Issue | Why it mattered most |
|-------|----------------------|
| **No single agent entry point** | Cursor/OpenClaw had no obvious “read this first.” Agents would land on README (1100+ lines, mixed broker + generic FIQA) and not know where to start. |
| **Default script path and reading order hidden** | PROJECT_DOC_SYSTEM_MAP existed but was buried in `docs/`. Default commands (run_demo_local.sh, demo_pre_checklist.sh, restore_8001_readiness.sh) and ports (8001 vs 8000) were scattered across multiple docs. |

---

## 2. Changes made

| File | Change | Why it helps |
|------|--------|--------------|
| **AGENTS.md** (new) | Single agent entry point at repo root. Defines: (1) read-first order, (2) default execution path, (3) runtime paths, (4) doc categories, (5) scope guardrail. | Agents have one place to start; no need to guess. |
| **README.md** | Added first line under Broker Demo: “**Agents (Cursor/OpenClaw):** Read [AGENTS.md](AGENTS.md) first — default entry point, reading order, script path.” | Agents see the entry point as soon as they open the repo. |
| **docs/PROJECT_DOC_SYSTEM_MAP.md** | Added “Agent Entry Point” section at top: “Read AGENTS.md first. It defines default reading order, script path, runtime paths, scope guardrail.” | Doc map now routes agents to AGENTS.md before diving into categories. |

---

## 3. Re-test results

| Check | Result |
|-------|--------|
| New agent can enter via intended path | ✅ README → AGENTS.md → PROJECT_DOC_SYSTEM_MAP → goals/quick start |
| Key docs and default paths easy to find | ✅ AGENTS.md lists all four default commands and ports in one place |
| Reading order clearer | ✅ Before: ambiguous. After: 1) PROJECT_DOC_SYSTEM_MAP, 2) insurance_paid_pilot_goal, 3) ANDY_QUICK_START |
| Before vs after | **Before:** Agent lands on README, sees broker section, then generic Quick Start (Docker 8000), unclear which path to use. **After:** Agent sees “Read AGENTS.md first,” gets explicit reading order and script path. |

**Verdict:** Better — one obvious default entry path.

---

## 4. Agent/operator impact

| What Andy no longer has to explain | What agents can now infer |
|-----------------------------------|---------------------------|
| “Read AGENTS.md first” | From README and PROJECT_DOC_SYSTEM_MAP |
| “Default path is 8001, Docker is 8000” | From AGENTS.md §3 and RUNTIME_PATH_STANDARD |
| “Run run_demo_local.sh for demo” | From AGENTS.md §2 |
| “Recovery is restore_8001_readiness.sh” | From AGENTS.md §2 and §3 |
| “Pre-demo: demo_pre_checklist.sh” | From AGENTS.md §2 |
| “Broker scope: no Stripe/auth/multi-tenant” | From AGENTS.md §5 |

**New default agent onboarding path:**
1. Open repo → README Broker section → AGENTS.md
2. Read AGENTS.md (reading order + script path + runtime)
3. Read PROJECT_DOC_SYSTEM_MAP for specific docs
4. Read goal + ANDY_QUICK_START as needed

**New default reading order:** PROJECT_DOC_SYSTEM_MAP → insurance_paid_pilot_goal → ANDY_QUICK_START

**New default script path:** `bash scripts/run_demo_local.sh` (start), `bash scripts/demo_pre_checklist.sh` (pre-demo), `bash scripts/restore_8001_readiness.sh` (recovery)

---

## 5. Remaining blocker(s)

- None for this sprint. AGENTS.md is lightweight; can be extended later if needed.

---

## 6. Recommended next sprint

| Next target | Why |
|-------------|-----|
| **OpenClaw-specific onboarding** | If OpenClaw has a different entry convention (e.g., prompt file, config), add a short “OpenClaw: start here” pointer in AGENTS.md or a dedicated file. |
| **.cursor/rules reinforcement** | Optional: add `.cursor/rules/broker-entry.mdc` with `alwaysApply: true` that says “For broker work, read AGENTS.md first.” Only if agents still skip AGENTS.md in practice. |

---

*Sprint completed. One clear entry path established.*
