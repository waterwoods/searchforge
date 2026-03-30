# Correction / update visibility — spec

## Signals (UI-only)

| Signal | Source | Use |
|--------|--------|-----|
| Prior system triage | Previous system message with `triageResult` (portal, simulation, post-handoff thread) | Baseline for diffs |
| New collected field ids | `collected_fields` \ prior `collected_fields` | “本回合新记入” tags |
| Cleared still-needed | In prior `still_needed_fields`, not in current | “本轮起不再标缺” (factual) |
| New still-needed | In current, not in prior | “本轮新增缺项标记” (factual) |
| Correction | `follow_up_type === 'correction'` | Short detection line + absorbed note (no old values) |

## Sections

1. **Latest understood version** — One lead sentence before grouped “系统已收到的要点” when any structured ids exist.
2. **本轮更新 / 更正** — Conditional; may include:
   - 更正：检测短句 + 吸收说明
   - 新记入：蓝色 tags（与更正同时出现时仍展示）
   - 缺项变化：青/橙 tags（集合差，不声称客户原话）
3. **对当前步骤与缺项的含义** — Conditional when prior exists and at least one impact line applies:
   - `handoff_ready` false → true
   - cleared still-needed non-empty
   - added still-needed non-empty
   - correction with no new keys and no still diff and handoff unchanged
   - new keys only, no still diff, no correction, handoff unchanged

## Copy keys

All new strings live in `UiCopy` / `DEFAULT_UI_COPY` (`record_rail_*`) for client-pack override.

## Honesty rule

Do not render old→new field values. Wording states that green tags are the latest understanding.
