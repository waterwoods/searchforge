# Auto Insurance FAQ Intake Corpus — Execution Outline

**Theme:** Build high-value real-world intake corpus for auto insurance

---

## Workstreams

| # | Workstream | Owner | Deliverable |
|---|------------|-------|-------------|
| 1 | Research | Research worker | 20–30 realistic question patterns from public sources |
| 2 | Structure | Classification worker | Corpus with handling framework per type |
| 3 | Routing | Product logic worker | FAST / LLM / human-confirm classification |
| 4 | Critique | Simulation reviewer | Realism assessment, weak/strong items |
| 5 | Final | Product critic | Integration recommendation, scenario list |

---

## Source Strategy

| Source | Use |
|--------|-----|
| Chinese-language public web | 华人新车报价、保费、常见问题 |
| North America Chinese | 加州保险、SR-22、DMV |
| English public web | New car quote, payment failed, hit-and-run, SR-22, cancellation |
| Existing configs | Broker longtail, inbox_triage_scenarios, customer_entry_reply_strategy |

---

## Classification Strategy

- **Per question type:** topic, intent, missing info, safe response, trust boundary
- **Routing:** FAST (rule-first), LLM (mixed/unclear), human (quotes, policy changes, VIN-sensitive)

---

## Likely Loop Count

2–3 loops. Loop 3 only if clear gain from refinement.

---

## Sequence

1. Control docs — Blueprint, Outline, Acceptance
2. Research — Collect 20–30 question patterns
3. Structure — Build corpus with handling framework
4. Classify — Routing matrix
5. Loop 1 — Evaluate, identify weak/strong
6. Loop 2 — Refine, remove weak, sharpen
7. Optional Loop 3 — Top 5 refinement; only if worthwhile
8. Final — Report, integration recommendation, scenario list
