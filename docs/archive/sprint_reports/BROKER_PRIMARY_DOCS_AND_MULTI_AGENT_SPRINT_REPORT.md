# Broker Primary Docs Consolidation + Multi-Agent Model Report

**Sprint:** Broker Primary Docs Consolidation + Multi-Agent Collaboration Operating Model v1  
**Date:** 2026-03-07  
**Scope:** California Auto Insurance Broker Assistant only

---

## 1. Broker doc issues targeted

| Issue | Why it mattered most |
|-------|----------------------|
| **Broken reference** — `docs/runbooks/BROKER_VALUE_VALIDATION_MEETING_PACK.md` referenced everywhere but did not exist (removed in prior cleanup) | Every "before broker meeting" path pointed to a missing file; agents and Andy could not find the primary runbook |
| **Overlap** — BROKER_MEETING_PACKAGE, BROKER_DEMO_OPERATOR_RUNBOOK, BROKER_DEMO_SCRIPT_15MIN, BROKER_DEMO_CHECKLIST all overlap | Unclear which doc to read first; repeated content across 4+ files |
| **No explicit primary vs supporting** | Hard to tell what to read first vs what to ignore most of the time |
| **No multi-agent model** | Andy had to repeatedly explain who does what, default loop, when to ask vs act autonomously |

---

## 2. Broker doc changes made

| File | Change |
|------|--------|
| `docs/runbooks/BROKER_VALUE_VALIDATION_MEETING_PACK.md` | **Created.** Single primary runbook: agenda, question order, opening/fallback/closing scripts, success criteria (§6), next-step logic (§7), pre-meeting checklist |
| `docs/BROKER_DEMO_CHECKLIST.md` | Added one-line pointer: "→ Primary runbook: docs/runbooks/BROKER_VALUE_VALIDATION_MEETING_PACK.md" |
| `docs/PROJECT_DOC_SYSTEM_MAP.md` | Added "Primary vs Supporting" table; added MULTI_AGENT_OPERATING_MODEL_V1 to PRIMARY; fixed Quality bar / Drift paths (docs/ root) |
| `AGENTS.md` | Added §5 Multi-Agent Collaboration with link to operating model |

**Why it helps:** The meeting pack now exists and is the single source of truth. Primary vs supporting is explicit. Broken links are fixed.

---

## 3. Multi-agent model created

| Item | Detail |
|------|--------|
| **Where** | `docs/MULTI_AGENT_OPERATING_MODEL_V1.md` |
| **Roles** | Andy (business), Cursor (code/docs), OpenClaw (scripts/automation), ChatGPT (research, no repo writes) |
| **Key loop** | Enter → Read AGENTS.md + doc map + operating model → Work in small inspect→integrate→retest loops → Hand off with clear notes |
| **Autonomous actions** | Fix broken links, run validation, update docs for consistency, consolidate overlapping docs (preserve content) |
| **Ask Andy when** | Scope change, new success criteria, new demo flow, broker-facing content changes |

**Why it helps:** Agents know their role, default loop, and when to act vs ask. Andy spends less time explaining.

---

## 4. Entry-path integration

| Entry | How operating model is exposed |
|-------|-------------------------------|
| `AGENTS.md` | §5 Multi-Agent Collaboration → `docs/MULTI_AGENT_OPERATING_MODEL_V1.md` |
| `docs/PROJECT_DOC_SYSTEM_MAP.md` | Agent Entry Point section + PRIMARY table both link to operating model |

**Reduces repeated explanation:** Yes. A new agent can find the model from AGENTS.md or the doc map without Andy pointing it out.

---

## 5. Clarity result

| Aspect | Before | After |
|--------|--------|-------|
| **Broker primary runbook** | Missing (broken ref) | Exists at `docs/runbooks/BROKER_VALUE_VALIDATION_MEETING_PACK.md` |
| **Primary vs supporting** | Implicit, scattered | Explicit table in doc map |
| **Multi-agent model** | None | Documented, linked from AGENTS.md and doc map |
| **Agent entry path** | Read docs, unclear role | Read AGENTS.md → doc map → operating model → identify role |

**Result:** Better. Broker docs are clearer; collaboration model is discoverable; agent knows where to start, what to read, what role to play, and the default working loop.

---

## 6. Remaining confusion

- **Standards/guardrails paths** — Doc map references `docs/standards/` and `docs/guardrails/` but BROKER_DEMO_QUALITY_STANDARD and BROKER_DEMO_DRIFT_GUARDRAIL live in `docs/` root. "Primary for Daily Use" now uses correct paths; category folders may need alignment later.
- **Supporting doc overlap** — BROKER_MEETING_PACKAGE, BROKER_DEMO_OPERATOR_RUNBOOK, BROKER_DEMO_SCRIPT_15MIN still overlap. They now clearly point to the meeting pack as primary; full consolidation deferred.

---

## 7. Recommended next step

**One clear next step:** Before the next broker demo, run `bash scripts/demo_pre_checklist.sh` and open `docs/runbooks/BROKER_VALUE_VALIDATION_MEETING_PACK.md`. Confirm the flow feels clear and that an agent entering via AGENTS.md can complete the loop without asking Andy.

---

*End of report*
