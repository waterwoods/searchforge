# Add-Car Fix-Now / Fix-Next / Acceptable / Defer Spec

## Fix now (completed this sprint)

| Item | Rationale |
|------|-----------|
| `_extract_add_car_vehicle_concrete` branch structure | 宝马/本田/丰田 lines were unreachable after `if not model:`; broke broker vehicle line for common Chinese messages. |
| Add-car before premium in customer_question templates | Mixed “加车 + 便宜吗” incorrectly used premium-review broker guidance first. |
| Short price-sensitivity tack-on on add-car draft (ZH/EN) | Reduces “robot ignored my money worry” without pretending to quote. |
| Correction markers (`不是这辆`, `另一辆`) | Aligns follow-up typing with real Cantonese/Mandarin corrections. |
| ACE01–ACE12 + `run_add_car_edge_case_simulations.py` | Repeatable broker-risk regression pack. |

## Fix next (not this sprint)

- **Full dual-vehicle memory:** when customer describes two complete vehicles without explicit “不是” disambiguation, prefer explicit broker handoff notes listing both strings.
- **Turn-1 lightweight vs mixed-intent:** refine `_is_turn1_lightweight_candidate` when add-car + strong premium markers both fire (currently often OK via full path; monitor LLM on flag).

## Acceptable for broker review

- **Dense multi-question** single bubbles: handoff with full text preserved beats over-constraining the assistant.
- **Exact premium** answers: always office-dependent; acceptable to defer to “office runs numbers.”

## Defer

- OCR / document parsing, carrier rating APIs, CRM case ownership, multi-tenant auth.
