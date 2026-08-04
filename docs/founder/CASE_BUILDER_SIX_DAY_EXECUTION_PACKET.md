# Case Builder — Six-Day Execution Packet

**For:** Founder print / desk reference  
**Window:** Mon 2026-08-03 → Sun 2026-08-09  
**Environment:** Cloud QA only · Production & waterwoods untouched  
**Full detail:** `docs/roadmap/SIX_DAY_PILOT_RELEASE_PLAN_2026-08-03.md`

---

## Page 1 — Problem, promise, reality, claims

### Customer problem

Chinese-speaking customers and small broker offices still run accidents through phone calls, scattered WeChat messages, repeated document asks, unclear ownership, and weak case continuity.

### North Star (what we sell)

Help the office: recognize a known customer → reuse confirmed vehicle/policy context → collect accident story & evidence → find real gaps → Request More → Broker confirms every important step → one Active Case, Timeline, and next action → measure timing and AI quality.

**Do not sell:** LangGraph, LangSmith, or MCP.

### Current product reality (honest)

| Area | Status |
|------|--------|
| Stage 1 Claim path (Request More → office accept) | Founder phone validated (frozen) |
| Stage 2 known-customer confirm | Founder phone validated (closed) |
| Timing metrics V1 | Closed on QA (honest, small-n) |
| LangGraph accident-story assist | Code + tests + on QA · **phone freeze pending** |
| LangSmith Case Builder eval | Not started |
| AI accept/edit/reject rates | Not implemented yet |
| MCP Broker tools | Lab only · not this week’s P0 |
| Production release | Not authorized |

### What you can / cannot claim

| Can say | Cannot say |
|---------|------------|
| Founder-demonstrable on Cloud QA | Production ready |
| Truthful V1 / supervised soft-pilot talk (with restrictions) | Real-customer validated |
| AI proposes; humans confirm | Autonomous claim filing AI |
| We measure timing honestly | Proven ROI / minutes saved |
| Eval & safety work this week | Legal/compliance certified |

---

## Page 2 — Six-day schedule & Founder actions

| Day | Date | Focus | Exit gate | Founder action |
|-----|------|-------|-----------|----------------|
| 1 | Mon 8/3 | Freeze LangGraph PR A | Auto green + phone result | ≤5 min phone QA (below) |
| 2 | Tue 8/4 | LangSmith traces + golden eval | Offline eval gate green | None (optional judge later) |
| 3 | Wed 8/5 | AI feedback + latency metrics | Events export; no ROI claims | Read 1-page metrics note |
| 4 | Thu 8/6 | Pilot safety baseline | Audit + fallback checklist | Sign audit / consent draft intent (~15 min) |
| 5 | Fri 8/7 | One-click demo + portfolio draft | Chen path works | Run one-click once; skim pitches |
| 6 | Sat 8/8 | Portfolio polish | Evidence index complete | Approve public wording |
| Sun | 8/9 | Final gate | Truthful label + demo clip | One E2E walkthrough; pick label |

**P0 before any MCP:** LangGraph freeze → LangSmith eval → AI metrics → safety → demo/portfolio → Sunday gate.  
**MCP = P1 only after P0s.** Optional LLM judge / polish / cost cleanup = P2.

**Daily habit:** Capture one evidence artifact every day (do not wait for Saturday).

---

## Page 3 — Workflow & how modules connect

### Complete product workflow

Customer entry → known-customer context → accident story → **AI proposal** → customer confirmation → completeness check → Broker review → Request More (if needed) → customer supplement → office acceptance → Timeline / metrics

### Modules (customer value in one line)

| Module | Role | Customer / office value |
|--------|------|-------------------------|
| Deterministic Claim workflow | Backbone | Repeatable office process |
| Timeline & projections | One truth | Customer & Broker see the same case |
| Known-customer confirm | Prefill gate | Fewer unnecessary uploads |
| LangGraph | Story organizer | Faster structured Must Haves |
| LangSmith | Flight recorder + quizzes | Catch bad AI before brokers see it |
| Metrics | Honest clocks | Learn where cases stall |
| HITL feedback | Accept / edit / reject | AI improves without guessing |
| Safety & audit | Boundaries | Soft pilot talk without reckless risk |
| Model fallback | Safety net | Form still works if AI fails |
| MCP (later) | Delivery tools | Second-office leverage — not the sale |

**Control law:** AI never changes Claim lifecycle. Unconfirmed proposals are not facts.

---

## Page 4 — Stories & Sunday checklist

### Three-minute customer story (陈总)

“After an accident, your customer opens one task—not a chat scavenger hunt. If they are a known customer, they confirm the car and policy instead of re-uploading everything. They tell the story once; the system organizes it and asks only the missing pieces. Your office sees one case, one timeline, and one next action—Request More when needed, then accept when materials are ready. We are not filing with the carrier or deciding liability. We are making the office-ready case faster and clearer.”

### Three-minute FDE interview story

“We shipped a deterministic claim workflow first and Founder-validated it on phone. Then known-customer confirm. Then honest timing metrics that never invent broker-open events. Only after that did we add a bounded LangGraph assistant that proposes structured accident facts—humans must confirm; the graph never mutates lifecycle; invalid model output falls back to rules. This week we add LangSmith evals, Accept/Edit/Reject metrics, and a pilot safety baseline. We sell fewer loops and clearer ownership—not a multi-agent platform.”

### Sunday release checklist

- [ ] Critical automated tests green  
- [ ] One Founder E2E walkthrough on QA  
- [ ] Fix only P0 blockers  
- [ ] Short demo recorded  
- [ ] QA cost-saving scale restored  
- [ ] Evidence index updated  
- [ ] Label chosen: `DEMO READY` / `PILOT READY WITH RESTRICTIONS` / `NOT PILOT READY`  
- [ ] Production & waterwoods still untouched  

**Print tip:** Sized for ~4 pages.

| Format | Path | Notes |
|--------|------|-------|
| Markdown | `docs/founder/CASE_BUILDER_SIX_DAY_EXECUTION_PACKET.md` | Source |
| PDF | `docs/founder/CASE_BUILDER_SIX_DAY_EXECUTION_PACKET.pdf` | Latin-safe fonts (host lacked CJK); fine for English tables |
| HTML | `docs/founder/CASE_BUILDER_SIX_DAY_EXECUTION_PACKET.html` | **Preferred for Chinese** — open in browser → Print |

Local mirrors (gitignored): `artifacts/founder/*`
