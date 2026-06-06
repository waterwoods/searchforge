# Source-Grounded Scenario Design Spec

## Grounding inputs (conceptual)

1. **Official / industry-style add-car data needs**  
   Typical quote/add-car asks include: **VIN** (or sufficient vehicle identity), **plate** (sometimes), **year / make / model**, sometimes **mileage / condition**, **garaging / ZIP**, **named operators / household drivers**. Scenarios use this to make **office-realistic** slot combinations and missing-slot patterns.

2. **California price sensitivity (realistic customer concerns)**  
   Premium drivers customers worry about in conversation include: **ZIP / territory**, **driving history**, **experience**, **vehicle age and type**, **mileage**. Scenarios use this for phrasing like **大概多少钱**, **这个邮编会不会贵一点**, without pretending the system can quote exact dollars in rules.

3. **Public discussion patterns (fragmented chat)**  
   Threads often show: **price asked early**, **only one of several requested items answered**, **offers to send screenshots / registration / VIN**, **logistics mixed with quote**. Scenarios **WIRC-002–010** deliberately include these shapes.

## Caveat (required)

These scenarios are **web-informed realistic simulations**. They are **not** claims about how “all Chinese-speaking California customers” behave, and **not** statistically validated sampling.

## Category coverage (required mix)

| # | Scenario ID | Coverage |
|---|-------------|----------|
| 1 | WIRC-001 | Clean direct add-car quote request |
| 2 | WIRC-002 | Price-first + completion in turn 2 |
| 3 | WIRC-003 | Partial answer, fragment later |
| 4 | WIRC-004 | Screenshot / VIN / registration timing question |
| 5 | WIRC-005 | ZIP late (second turn) |
| 6 | WIRC-006 | Driver info late |
| 7 | WIRC-007 | Vehicle change / correction |
| 8 | WIRC-008 | Uncertain delivery timing |
| 9 | WIRC-009 | Chinese + English vehicle naming |
|10 | WIRC-010 | Side concern (ZIP price, WeChat/materials) before add-car core |

## Strong Chinese / Chinese-American practical phrasing (≥3)

- **WIRC-002:** 大概多少钱；英文不太好；告诉我还差什么  
- **WIRC-004:** 还没正式registration；先发截图/VIN可以吗  
- **WIRC-010:** 邮编会不会保费贵；WeChat 发截图  

## Messy / realistic friction (≥2)

- **WIRC-002, 003, 007, 010:** multi-turn, topic shift, correction, or split slots  

## Expected good behavior (generic)

- Stay on **add-car / quote collection** unless a true safety or human-request override applies.  
- **Merge** customer turns for slot filling.  
- **Customer-facing** replies: short, office-realistic, not accusatory.  
- **Broker-facing** summary and next step: aligned with collected vs still-needed fields.  

## Failure modes to watch

- Wrong **issue_category** or template (e.g. “notice incomplete” on a normal question).  
- **False** “already sent materials” when the customer only **asked** about sending.  
- **Premature handoff** when mandatory add-car slots are still empty.  
- **Missed make/model** despite clear English model names in the same message.  
