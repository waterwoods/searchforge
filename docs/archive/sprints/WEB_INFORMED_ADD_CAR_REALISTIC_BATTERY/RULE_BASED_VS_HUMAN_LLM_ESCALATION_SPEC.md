# Rule-Based Sufficiency vs Human / LLM Escalation Spec

Use this table when prioritizing fixes: **A** = rule coverage, **B** = human confirmation, **C** = future LLM assist.

| Scenario | Classification | Primary bucket | Action |
|----------|----------------|----------------|--------|
| WIRC-001 | Acceptable | B (minor) | **B:** Broker confirms exact trim / customer name-phone. Optional **A:** richer make/model in broker summary. |
| WIRC-002 | Strong | rule-based good enough | **A** only if copy tuning desired. |
| WIRC-003 | Strong | rule-based good enough | — |
| WIRC-004 | Trust-breaking | **A** + **B** + **C** | **A:** Tighten markers so “先发截图行吗” ≠ already sent; separate prospective-send reply. **B:** Broker confirms what was actually received. **C:** Small LLM or classifier for **intent** (ask vs assert) if rules stay brittle. |
| WIRC-005 | Strong | rule-based good enough | — |
| WIRC-006 | Weak | **A** + **B** | **A:** Align `handoff_ready` / `quote_ready_status` with driver completeness rules. **B:** Until fixed, broker treats handoff flag skeptically when driver missing. |
| WIRC-007 | Acceptable | B | **B:** Confirm corrected vehicle (trim, hybrid) in carrier UI. Optional **A:** summary shows full corrected string. |
| WIRC-008 | Weak | **A** + **B** | **A:** Add **Altima** / broaden model patterns. **B:** Broker sanity-checks model if rules miss. |
| WIRC-009 | Strong | rule-based good enough | — |
| WIRC-010 | Weak | **A** + **C** | **A:** Route ZIP/materials **shopping questions** to a short **add-car primer** (“可以，先给年份车型…”）instead of **unclear** notice template. **C:** If many multi-intent opens exist, LLM **routing** only (not full rewrite). |

## Definitions

- **A. Rule coverage gap** — Fix via lexicon, regex, intent guard, template split, or gating logic in `triage.py` / configs.  
- **B. Human confirmation** — Rules may fire, but broker should verify before binding or CRM commit.  
- **C. Candidate for future LLM assist** — Ambiguity is **semantic** (“可以吗” vs “发了”) or **multi-intent** enough that deterministic rules multiply edge cases; LLM should be **narrow** (classify or extract), not a full conversational replacement.  
