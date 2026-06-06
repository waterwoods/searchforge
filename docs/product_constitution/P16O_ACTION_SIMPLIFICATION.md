# P16-O Phase 3 — Action Simplification

**Date:** 2026-06-01  
**Rule:** One page = one action

---

## Removed or Hidden

| Element | Class | Where |
|---------|-------|-------|
| Three-button quick-start row | Delete | Empty landing |
| ①②③ portal_empty_secondary | Delete | Copy |
| 办理类型 label | Delete | Empty landing |
| 推荐主路径 badge | Delete | Was on add-car button |
| 场景仿真 links | Delete | CustomerEntryTab empty + active hero |
| Pilot intro Alert (scope essay) | Hide | UnifiedIntakePage |
| Tab suffixes (customer, my_requests, simulation) | Delete | UnifiedIntakePage |
| AddCarFlowExplanation | Delete | Post-handoff |
| UTC timing truth footnote | Delete | Post-handoff |
| 查看工作台 button | Delete | Post-handoff |
| Transaction gradient banner | Delete | Mid-flow add-car |
| Example toggle card | Delete | Input area |
| Light identity / WeChat strip | Hide | Handoff pending |
| Handoff button subline essay | Delete | Input area |
| Category-before-message instruction | Delete | Input area |
| Intent tag closable row | Delete | Input area |
| Duplicate handoff gap alerts | Merge | Max 1 primary alert |

---

## Kept (Secondary / Footer)

| Element | Role |
|---------|------|
| 逐项填写加车信息 | Opt-in structured path |
| 更多类型 | Dropdown for edge intents |
| 需要人工？ | Footer link → talk_to_agent starter |
| 提交新问题 | Post-handoff secondary |
| 追加到本条记录 | Post-handoff collapse |

---

## One Primary Per Screen

| Screen | Primary action |
|--------|----------------|
| Empty landing | 发送给办公室 |
| Mid-flow | 提交补充 / 确认提交 |
| Handoff pending | 确认提交，开始报价处理 |
| Post-handoff | Wait (implicit) + 提交新问题 secondary |
| My requests | Read status → 去客户报送继续 |

---

*End of P16-O Phase 3 — Action Simplification*
