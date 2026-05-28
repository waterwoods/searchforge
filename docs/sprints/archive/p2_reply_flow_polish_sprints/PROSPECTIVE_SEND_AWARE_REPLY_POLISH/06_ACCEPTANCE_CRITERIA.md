# Acceptance Criteria

- [ ] Prospective-send phrases receive a **short affirmative office lead** before the next Add-Car ask or handoff line.
- [ ] `follow_up_type` remains **`new_info`** (not `already_sent`) for 要不要…发 / 我先发给你看看行吗-style messages.
- [ ] True **already_sent** paths unchanged: `材料发你微信了`, `截图发你了`, `registration 发你微信了`, etc.
- [ ] No regression in `bash scripts/guardrail_inbox_triage.sh`.
- [ ] No regression in Add-Car batteries: scenario battery, ADZM stress battery, edge-case simulations.
- [ ] `要不要发你` does **not** trigger the turn-2 “materials sent → skip driver ask” shortcut via false `发你` substring match.
