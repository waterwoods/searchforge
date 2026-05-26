# FAQ Corpus Productization — Acceptance / SLA Criteria

**Sprint:** FAQ Corpus Productization

---

## Minimum Requirements

| Criterion | Minimum |
|----------|---------|
| **Productized question types** | 5–8 |
| **Simulation Assistant scenarios** | 5–8 new or materially improved |
| **FAQ handling matrix** | One doc with customer asks → office says → still need → route |
| **Founder showcase** | One block per selected type in final output |

---

## What Counts as "High-Value"

- **Frequency:** Appears often in real broker inbox
- **Business relevance:** Affects retention, payment, or policy change
- **Pilot usefulness:** Founder can demo or explain to small client
- **Routing clarity:** Clear FAST / LLM / human_confirmation
- **Scenario usefulness:** Supports 2–3 turn Simulation Assistant flow

---

## What Counts as "Usable in Product"

- Scenario passes `run_inbox_triage_scenarios.py` or `run_simulation_assistant_scenarios.py`
- Routing logic correctly classifies and routes
- Handling matrix is broker-readable (not internal-only)
- Founder example shows: customer asks → system responds → still need → route

---

## What Counts as Too Generic or Too Weak

- Generic fallback reply ("请提供更多信息", "Could you provide more context")
- Wrong category (e.g. premium_too_high classified as renewal_reminder)
- Missing urgency (critical → medium)
- Scenario with no realistic customer phrasing
- Handling matrix entry with no actionable "office says" or "still need"

---

## What Must Be Shown to Founder at End

1. **Selected top 5–8 question types** with one-line rationale each
2. **Founder showcase** for each: customer asks → system responds → still need → route → why this helps
3. **Best FAST candidates** and **biggest human-confirmation categories**
4. **Strongest scenario additions**
5. **Single best next move** after this sprint
