# First-time clarity + realistic Add-Car intake spec

## First-time user clarity goals

1. **Page purpose:** User understands this is a formal insurance intake + office handoff portal, not a casual chatbot that binds coverage.
2. **Add-Car as primary path:** Visually and in copy, Add-Car is the default flagship path without hiding other types.
3. **Three entry modes:** User understands they may: tap「办理加车报价」, type/paste a sentence in the input, or use the structured Add-Car card.
4. **After submit:** User understands the system organizes a case record and the **office** reviews, quotes, and follows up (not autonomous binding).

## Add-Car entry guidance goals

- Empty-state headline + secondary text carry the above without requiring expansion panels.
- Structured card hint clarifies it is **optional** and alternative to the other two modes.
- Primary button styling for Add-Car when no intent is selected reinforces the default path.

## Realistic Chinese-like scenario coverage (battery)

| ID | Theme | Example focus |
|----|--------|-----------------|
| R1 | Simple direct | Year/model, zip, 明天, 我自己开 |
| R2 | Office-style question | 要不要先发你行驶证 / 购车文件, 主要我本人开 |
| R3 | Date correction | 不是明天… 这个周五提车 |
| R4 | Repeated / corrected calendar date | 3月8号 → 3月10号, BMW X5 |
| R5 | Mixed Chinese + English | quote, zip, this Friday pick up, VIN question |
| R6 | Incomplete materials | VIN还没拿到, 可以先报吗, 我跟老婆都可能开 |
| R7 | Supplement / sent / pending | 已经发过了 / 还没发 / 等等发你 VIN |

## Key extraction risks and desired handling

- **Delivery:** Recognize 周五/Friday, `pickup`, and `M月D号` when tied to 提/拿/pick.
- **Driver:** Map 主要我本人开, 本人开, spouse / 都可能开 to driver / additional-driver signals.
- **Materials:** Surface prospective-send questions and “not ready yet” claims in `collected_fields` where possible for broker visibility.

## Acceptance criteria

1. Empty-state copy in `configs/clients/chen_kui/ui_copy.json` (and TS defaults) describes three entry modes and office handoff in plain language.
2. Add-Car quick-start button is primary when no other intent is selected.
3. Under `LLM_GENERATION_ENABLED=0`, `scripts/run_add_car_realistic_intake_scenarios.py` runs all R1–R7 without crashing and prints structured fields for inspection.
4. `bash scripts/guardrail_inbox_triage.sh` passes after changes.

## “Good enough” for this sprint

Noticeable clarity gain for first-time users and measurable improvement on delivery/driver/material **flags** for the battery messages—not full natural-language date normalization (last wins) unless already present elsewhere.
