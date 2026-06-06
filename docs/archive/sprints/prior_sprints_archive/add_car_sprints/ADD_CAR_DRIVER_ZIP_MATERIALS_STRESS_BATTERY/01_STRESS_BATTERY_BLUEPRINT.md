# Stress Battery Blueprint — Add-Car Driver / ZIP / Materials-QA

## Purpose

One more **focused, realistic** pass over the Add-Car rule path before broker exposure (Chen Kui Insurance unified entry). Recent sprints improved ZIP extraction, driver micro-phrases, and materials “question vs already sent” guards. This battery checks whether those fixes **survive common Chinese California customer phrasing** and whether failures are **logic** vs **reply polish**.

## Non-goals

- OCR, carrier APIs, frontend redesign, non–Add-Car flows, architecture changes.

## Scope (three pillars)

1. **ZIP** — `邮编95131`, `邮编 95131`, `zip95131`, bare `95131`, second-turn “我的邮编…”.
2. **Driver** — 我自己开 / 我一个人开 / 本人开 / 主要驾驶人是我 / 配偶与子女表述 / 我儿子开.
3. **Materials Q&A** — 要不要发你… vs 材料发你微信了 / registration 发你微信了 / 截图发你了.

## Success definition

Not perfection: **higher confidence** that Add-Car will not break on **small, realistic wording changes** that real WeChat customers use daily.

## Deliverables

| Artifact | Path |
|----------|------|
| Scenario battery | `scenario_battery.json` |
| Runner | `scripts/run_add_car_driver_zip_materials_stress_battery.py` |
| Specs & reports | This folder (`02`–`08`, `FINAL_REPORT.md`) |

## Execution defaults

- `LLM_GENERATION_ENABLED=false` — evaluate **rule / fast-path behavior** only.
- Entry point: `triage_conversation()` with simulated customer turns (same as existing scenario batteries).

## Stakeholders

- **Founder:** skim Final Report + Founder Inspection Notes + 中文总结.
- **Broker:** care about broker_next_step, collected_fields accuracy, and whether the client reply sounds human and on-playbook.
