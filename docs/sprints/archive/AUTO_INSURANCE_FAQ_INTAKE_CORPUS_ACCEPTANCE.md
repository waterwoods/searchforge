# Auto Insurance FAQ Intake Corpus — Acceptance / SLA Criteria

---

## Minimum Corpus

| Criterion | Target |
|----------|--------|
| Useful question types | ≥20 |
| Realistic user phrasing | ≥1 per type; ≥2 for top 10 types |
| Handling framework | All types have: clarify, safe response, trust boundary |

---

## Realism

| Criterion | Target |
|----------|--------|
| Realistic question | Sounds like real customer voice; not generic FAQ |
| Source diversity | Mix of Chinese + English; public sources |
| High-frequency | Prioritize common patterns (new car, payment, missing doc, etc.) |

---

## Handling Framework

| Criterion | Target |
|----------|--------|
| Useful framework | Office knows what to clarify, what to ask, what not to overpromise |
| Routing classification | Clear FAST / LLM / human-confirm for each type |

---

## Routing Classification

| Criterion | Target |
|----------|--------|
| FAST | Obvious patterns; rule-safe; clear markers |
| LLM | Mixed intent, vague, unclear category |
| Human confirmation | Quotes with dollars, policy changes, VIN/driver/garaging sensitive |

---

## Weak / Too Generic

| Criterion | Target |
|----------|--------|
| Avoid | Generic "How much is insurance?" without context |
| Avoid | Overly formal FAQ answers |
| Avoid | Items that don't map to product operating model |

---

## Product Integration

| Criterion | Target |
|----------|--------|
| Scenario recommendation | 5–8 types for Simulation Assistant |
| Turn 1 routing | Which items strengthen lightweight routing |
| Handoff clarity | Which items improve case handoff docs |
