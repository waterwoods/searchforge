# ADD-CAR INDUSTRIAL SCORECARD V1 — Final report

## Summary of scores

| Dimension | Score |
|-----------|-------|
| PAGE | 4 / 5 |
| FLOW | 3 / 5 |
| STATE | 3 / 5 |
| HANDOFF | 3 / 5 |

**One-line summary:** Add-Car has **strong page-level pilot framing and handoff *copy***; the remaining gap is **task-shaped flow** and **human-credible continuation** (engine replies + parity across office surface).

## Biggest blockers

1. **Conversation-first UX** — Even with a flow track and transaction ribbon, the experience is still **chat-thread centric**, which caps FLOW maturity.
2. **Handoff “feel” vs configuration** — UI strings are broker-grade; **draft behavior** (echo length, `already_sent`, edge routing) can still undermine trust (simulation audit).
3. **Office-side parity** — Customer closure emphasizes **服务记录编号** and status strip; workbench queue cards **could show the same** for instant same-case recognition (echo sprint + result-card sprint follow-ups).
4. **Pilot operations truth** — `PROJECT_TRUTH_SWITCH.md`: JSON persistence, limited auth/PII story, and **LLM path not guardrail-equivalent**—these cap how “industrial” the product can honestly claim to be.

## Recommended next sprint (highest value)

**Add-Car reply polish + handoff behavior hardening** (extends `ADD_CAR_REALISTIC_NA_CHINESE_SIMULATION_AUDIT_SPRINT` / `ADD_CAR_REPLY_POLISH_ALREADY_SENT_LLM_SPOTCHECK_SPRINT` themes): shorten acknowledgements, fix awkward stitching, improve `already_sent` when context is complete, optional LLM spot-check. **Why:** Directly raises **HANDOFF** and perceived **FLOW** without a page rewrite; highest commercial leverage per “does the customer feel received?”

**Runner-up:** **Workbench state parity** — case ID chip + status strip on queue cards (raises **STATE** and broker confidence).

**Runner-up:** **Pilot ops + E2E smoke** — one broker dry-run script, guardrail gate, live 8001 smoke (raises **pilot readiness** without new features).

## Founder-readable takeaway

Add-Car is **past “fragile demo”** for the rule path: the **portal composition and closure narrative** are serious. It is **not yet “mature SMB SaaS”** because the interaction is still chat-shaped, engine replies need polish, and ops/persistence are explicitly pilot-tier. The **smart next investment** is making **post-send conversation** feel as credible as the **pre-send page**.

## Sprint timing

- **Start:** 2026-03-27 (scorecard assessment session)
- **End:** 2026-03-27 (same session)
- **Elapsed:** ~45–75 minutes (reading code + sprint reports + writing three docs)
