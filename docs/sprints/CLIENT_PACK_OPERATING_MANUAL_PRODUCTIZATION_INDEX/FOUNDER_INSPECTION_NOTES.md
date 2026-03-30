# Founder Inspection Notes

Raw observations from the documentation audit (March 2025). Use with the structured guides in this folder.

---

## What is already productized

- **Clear three-tier config model:** industry JSON + client JSON + common JSON, implemented in one loader module.  
- **Explicit no-cross-client-fallback** stance for key client-only structures (reduces accidental broker bleed).  
- **Heavy automated regression:** `guardrail_inbox_triage.sh` bundles scenarios, multi-turn, adversarial, boundary, and **A/B client isolation** scripts.  
- **Second broker drill pack exists:** `configs/clients/socal_precision/` for isolation testing.  
- **UI pulls `ui_copy` from API** with typed merge in `clientConfig.ts`.

---

## What remains code-bound or easy to misunderstand

- **`triage.py` is very large** — behavior and wording can be intertwined; founders may assume “it’s all config” when some tails still default in code.  
- **Frontend `DEFAULT_UI_COPY` is Chen-flavored** — if `ui_copy.json` is thin, the product still “looks like Chen Kui” until filled out.  
- **`CLIENT_ID` is env-driven** — no in-app broker switch for production multi-tenant; each deployment/instance is one active client unless you build orchestration.  
- **Common `soft_route_inbox.json`** — global; per-broker soft-route divergence may need future product decision.

---

## Strengths (commercial / operator lens)

- **Hot-plug story is real:** new broker folder + env + tests is a credible onboarding path.  
- **Isolation tests are a differentiator** — many teams skip cross-tenant copy tests; you have them in guardrail.  
- **Demo + workbench in one UI** — good founder narrative.

---

## Risks (remaining)

- **Engine complexity vs config surface** — migration docs must keep saying “configs first.”  
- **LLM vs rule mode** — production behavior can diverge from `LLM_GENERATION_ENABLED=0` CI; founders should know which mode trials use.  
- **Case store is file JSON** — appropriate for demo; not a statement about production scale.

---

## Suggested “first glance” in repo (5 minutes)

1. `configs/clients/chen_kui/ui_copy.json`  
2. `configs/clients/chen_kui/handoff_phrases.json`  
3. `scripts/guardrail_inbox_triage.sh` (list of steps)  

---

*Judgment consolidated in [FINAL_REPORT.md](./FINAL_REPORT.md).*
