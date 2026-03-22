# Add-Car Edge-Case Scenario Pack (ACE01–ACE12)

**Source:** `configs/customer_entry_multi_turn_simulations.json`  
**Runner:** `PYTHONPATH=. python3 scripts/run_add_car_edge_case_simulations.py`

Each scenario includes: user sequence, expected automation behavior, broker-facing intent, and failure modes.

| ID | Theme | User sequence (summary) | Expected behavior | Broker should receive | Failure if |
|----|-------|-------------------------|-------------------|----------------------|------------|
| ACE01 | Zip first + doc side Q | 邮编 → garaging 是什么 → full vehicle | Progressive add-car; clarify doc; then quote-ready | Add-car thread + doc explanation context | Routed to renewal review or generic “send policy” |
| ACE02 | 便宜吗 + add-car | 加车 Camry 便宜吗 → zip+delivery+driver | Add-car templates, not premium-review first | Add-car broker_next_step | Premium-review client_prep on new car |
| ACE03 | Materials after ready | 加车 → full quote → 材料发微信 | Handoff when quote-ready; T3 materials tone | Quote case + “client says sent” | Ignores materials or cold handoff |
| ACE04 | Another vehicle | Full X5 thread → 不是这辆 是 X3 | Correction hint; summary prefers corrected model | Updated vehicle context | Summary stuck on X5 only |
| ACE05 | Hesitation + spouse | vague model → 可能下周+zip → 老婆开 | Delivery + driver markers across turns | Quote-ready handoff | Stuck asking duplicate delivery |
| ACE06 | Ballpark ask | 大概多少钱 → full slots | Price tack-on + collection | Natural draft + slots | Pure deflection w/o next ask |
| ACE07 | Zip + side premium | zip+加车 → 区间 → Lexus complete | Add-car path preserved | Consistent add-car summary | Switches to renewal playbook |
| ACE08 | Dense bubble | RAV4+zip+delivery+driver+timing questions | Quote-ready handoff turn 1 | Single-turn case | Over-questions or unclear |
| ACE09 | 宝马中文 | 宝马 X3 一单 | Vehicle concrete includes Chinese make | Summary shows 宝马/X3 | Empty or wrong vehicle line |
| ACE10 | Vague opener | 想加一台车 → structured fill | Two-turn quote-ready | Clear progression | Robotic or wrong category |
| ACE11 | Driver correction | Full quote T1 → 说错了老婆开 | Handoff T1; T2 correction ok | Correction note in summary | Drops driver change signal |
| ACE12 | Registration sent | Quote-ready T1 → reg 发微信 | Materials / sent follow-up | Verify path | Blocks on redundant asks |

**Minimum coverage vs sprint prompt:** partial + pause-style multi-turn (ACE01, ACE05), correction (ACE04, ACE11), side question (ACE01, ACE07), materials-sent (ACE03, ACE12), contact-late (covered by existing MT49/MT50), mixed vehicle (ACE04, ACE09), vague→structured (ACE10), price (ACE02, ACE06, ACE07), zip-only first (ACE07), multi-mini-questions (ACE08), driver relationship (ACE05, ACE11).
