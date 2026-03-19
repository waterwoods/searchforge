# Multi-Agent Collaboration Operating Model v1

**Scope:** California Auto Insurance Broker Assistant. Lightweight rules so Cursor, OpenClaw, ChatGPT, and Andy can work with less repeated explanation.

---

## 1. Roles and Responsibilities

| Role | Primary responsibility |
|------|-------------------------|
| **Andy** | Business decisions, broker meetings, scope, prioritization, feedback interpretation |
| **Cursor** | Code edits, refactors, doc updates, local dev, integration with AGENTS.md |
| **OpenClaw** | Scripts, automation, validation, guardrails, discovery, ingest pipelines |
| **ChatGPT** | Ad-hoc research, prompt drafting, brainstorming (no repo writes) |

---

## 2. What Each Role Should NOT Do

| Role | Avoid |
|------|-------|
| **Andy** | Writing runbooks, fixing broken scripts, explaining doc structure repeatedly |
| **Cursor** | Changing scope without goal check; mass rewrites; touching out-of-scope verticals |
| **OpenClaw** | Changing demo flow or success criteria; modifying broker meeting pack |
| **ChatGPT** | Editing repo; assuming it has latest doc state |

---

## 3. Default Short-Loop Collaboration Pattern

1. **Agent enters** → Read `AGENTS.md` → Read `docs/PROJECT_DOC_SYSTEM_MAP.md` → Read relevant goal/standard/runbook
2. **Agent works** → Small inspect→integrate→retest loops; stay in scope
3. **Agent hands off** → Leave clear notes in commit/PR or in the doc changed; no implicit assumptions
4. **Andy reviews** → Business layer only; approve/reject; clarify scope if needed

---

## 4. How Work Is Handed Off

| From → To | Handoff |
|-----------|---------|
| Cursor → OpenClaw | Script paths, env vars, expected outputs in docs or scripts |
| OpenClaw → Cursor | Script behavior, API contracts, file locations |
| Either → Andy | Summary of change + "needs your call" for scope/priority |
| Andy → Either | "Do X; use doc Y; don't do Z" — one clear instruction |

---

## 5. How Docs / Scripts / Guardrails Fit

| Asset | Who maintains | When |
|-------|---------------|------|
| **Primary docs** (AGENTS.md, doc map, meeting pack, goals) | Cursor (with Andy approval for business content) | When structure or clarity changes |
| **Scripts** (demo_pre_checklist, run_demo_local, guardrail_*) | OpenClaw | When automation or validation changes |
| **Guardrails** (drift, copy-to-client) | OpenClaw | When checks or thresholds change |
| **Standards** (quality bar) | Andy + Cursor | When demo bar changes |

---

## 6. What Andy Does at the Business Layer Only

- Decide scope (in/out)
- Prioritize broker demo vs other work
- Interpret broker feedback (value confirmed/partial/weak)
- Approve or reject agent-suggested changes that affect demo flow or success criteria

---

## 7. What Agents Can Do Autonomously (Before Asking Andy)

| Action | Condition |
|--------|-----------|
| Fix broken links, typos, path refs | No scope change |
| Run validation scripts, guardrails | Per existing runbooks |
| Update docs for consistency | Align with goals/standards; no new business rules |
| Add scripts for existing flows | Match current demo/validation behavior |
| Consolidate overlapping docs | Preserve content; clarify primary vs supporting |

**Ask Andy when:** Scope change, new success criteria, new demo flow, broker-facing content changes, or ambiguity about "in/out."

---

## 8. Entry Path for New Agents

1. Read `AGENTS.md`
2. Read `docs/PROJECT_DOC_SYSTEM_MAP.md`
3. Read `docs/MULTI_AGENT_OPERATING_MODEL_V1.md` (this doc)
4. Identify role (Cursor vs OpenClaw vs ChatGPT)
5. Follow default loop (§3)

---

*Full doc map: `docs/PROJECT_DOC_SYSTEM_MAP.md`*
