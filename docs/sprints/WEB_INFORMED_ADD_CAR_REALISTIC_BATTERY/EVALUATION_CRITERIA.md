# Evaluation Criteria

## Per-scenario dimensions

For each scenario, the battery run is judged on:

1. **Playbook** — Did the system stay on the correct **Add-Car / new quote** collection path (vs unrelated templates)?  
2. **Field extraction** — Did `collected_fields` / `still_needed_fields` match what a broker would infer from the customer text (merged across turns)?  
3. **Customer-facing reply** — Does `client_reply_draft` make sense, match tone (ZH), and avoid false claims?  
4. **Broker-facing result** — Do `broker_next_step` and summary align with slots and urgency?  
5. **Demo acceptability** — Would a broker cringe if this appeared in a live pilot chat?  
6. **Sufficiency** — For this scenario, is **rule-based** handling enough, or is **human confirmation** / **future LLM assist** clearly better?

## Classification scale

| Label | Meaning |
|-------|---------|
| **Strong** | Correct path, extraction and replies aligned; broker-ready. |
| **Acceptable** | Minor gaps (e.g. truncated make in broker line) but no customer-facing lie; broker can correct in one glance. |
| **Weak** | Wrong gating, wrong template, or contradictory asks; recoverable but embarrassing or confusing. |
| **Trust-breaking** | Customer-facing text **misstates facts** (e.g. “you already sent” when they did not) or steers to the wrong workflow in a way that undermines trust. |

## Escalation labels (orthogonal)

Each scenario also gets one primary label:

- **rule-based good enough** — Deterministic path is adequate with optional copy polish.  
- **better with human confirmation** — Rules can proceed, but broker should verify (materials, spouse driver, ambiguous send intent).  
- **candidate for future LLM assist** — Intent or nuance is brittle for pure rules (multi-intent paragraphs, “can I send X?” vs “I sent X”).  

## Environment

- **`LLM_GENERATION_ENABLED=false`** so results reflect the **rule brain** only.  
- Full JSON for the evaluated run: `battery_run_results.json` in this folder.  
