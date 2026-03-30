# Simulation battery & failure map

## Realistic phrasing groups

### Web-grounded patterns (themes only; no long quotes)

From public Chinese-language guides / forums on US/CA auto insurance: customers ask about **VIN / registration / what to prepare**, **comparing carriers**, **using an agent when English is hard**, and **what documents matter**—often mixed with English terms (“quote”, “DMV”, “coverage”).

### Synthesized realistic patterns (repo + grounded usage)

- **Straightforward add-car**: 加一台 + 年份车型 + zip + 提车 + 谁开.
- **材料先发**: 要不要先发 registration / 驾照 / 微信发你.
- **VIN 未到**: 车行还没给 / 可以先报吗 + 车型年份.
- **多驾驶人 / 配偶**: 老婆也会开、要不要她的驾照、quote 怎么报.
- **改口日期**: 刚才说错了、提车改成周五.
- **比价 / coverage**: 上次报的价太贵、别的 company、调 coverage.
- **已发资料**: dec page / registration 已发微信、还要什么.
- **极简开场**: 单字「加车」+ 按钮路径.
- **中英混写**: quote / pick up / zip / VIN 还没拿到.

## Scenario battery (buckets A–I)

| Bucket | Example user message(s) | Ideal understanding | Useful office-style reply |
|--------|-------------------------|---------------------|-------------------------|
| A Straightforward | 加一台 2024 Tesla… zip… 下周五提车… 主要我开 | Full add-car slots → quote-ready | Handoff or confirm contact |
| B Material question | 明天提车，要不要先发 registration… | materials_send + need vehicle zip | 先发可以 + 补年份车型邮编 |
| C Missing VIN | VIN 车行还要两天… 可以先报吗… 车型年份都有 | Add-car; VIN pending, not “has VIN” | 可先报 + 要 zip/提车/驾驶人 |
| D Multi-driver | 老婆也会开… quote 怎么报… 要她驾照吗 | Add-car + additional drivers | 说明列驾驶人/驾照，不要走缺材料追件模板 |
| E Correction | 说错了，提车是下周五不是明天 | Preserve new delivery date | Ack + continue slots |
| F Price / re-shop | 上次报的价太贵… company / coverage | Stay on quote thread, not renewal bill review | Ack price concern + office re-quote / options |
| G Already sent | dec page+registration 已发微信，还要什么 | already_sent + add-car context | 核对 + 列仍缺字段 |
| H Continuation | (turn 2) VIN 到了再发你可以吗 | Same case, materials question | Short confirm + handoff when ready |
| I Ambiguous minimal | 加车 | add_car intent, collect slots | Progressive ask |

## Failure categories (used in audit)

- `intent_misroute` — wrong issue_category or wrong template family.
- `field_false_positive` — e.g. VIN collected when customer said VIN not available.
- `field_drop` — key slots missing after clear statement.
- `generic_unclear` — “内容不完整”类回复对明确加车语境.
- `empty_polite` — acknowledges but no next step / no case value.
- `wrong_next_step` — renewal/doc chase template on add-car quote thread.

## Acceptance criteria (sprint-level)

- Battery run on **rule path** documented with pass/partial/fail.
- Guardrail: `bash scripts/guardrail_inbox_triage.sh` **PASS** after any code change.
- Fixes limited to **high-ROI** routing/extraction; no case_store/config_loader/app_main churn.

## What we changed after this map (high level)

- VIN negatives: whitespace-tolerant + dealer-delay phrasing.
- `markers.json`: 可以先报 / 先报吗 / 报的价 / 上次报的价.
- Classification: multi-driver + quote wording before missing_document.
- `_is_add_vehicle_request`: multi-driver quote question; quote-price pushback branch.
