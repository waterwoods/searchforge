# ADD-CAR TASK-FIRST / LESS-CHAT FINAL POLISH — Final report

## What changed

- **Post-handoff thread block:** Heading, secondary hint, and collapse label moved to **configurable copy** (`portal_post_handoff_*`) with defaults that say **备查 / 主记录在受理结果卡**, not “继续聊.”
- **Result card path:** Section dividers for **next step** and **closure body** are config-driven (`portal_post_handoff_next_section_label`, `portal_post_handoff_closure_section_label`) so labels read **办公室已接手** and **同条记录，非新聊天** instead of generic “跟进 / 给客户.”
- **Copy:** Stronger **办公室已收到** + **不必在微信或电话里重复** (`handoff_closure_processing_add_car`); **本条服务记录** replaces **本对话** (`handoff_new_issue_hint`); pre-handoff thread title reframed as **报送过程（输入留痕）**; closure sublabel clarifies **系统草案，办公室会据此核对**; result-card hint stresses **编号为当前业务记录，气泡仅供备查.**
- **Typography:** Add-Car handoff **closure paragraph** body reduced from **15px → 13px** so it reads as **supporting office statement**, not the main “chat message.”
- **Backend allowlist:** New keys whitelisted in `config_loader.get_ui_copy()` so Chen Kui (and other clients) can override via `ui_copy.json`.

## What improved

- **Task hierarchy:** Primary anchor is explicitly the **record card + number**; thread is **optional audit.**
- **Office-owned next step:** Section title and processing line align on **record received / office handling.**
- **No-repeat confidence:** Explicit **入口已写明 → 不必重复** language.

## What remains (explicitly out of this sprint)

- **FLOW** still fundamentally turn-based; true “non-chat interaction model” needs a larger product pass.
- **HANDOFF** engine behavior (echo length, `already_sent`, etc.) per scorecard — not addressed here.
- **Workbench parity** (queue cards vs customer result card) — runner-up from scorecard, not this sprint.
- **Pilot ops truth** (persistence, auth) unchanged.

## Recommended next action

Bias to **pilot conversations and broker dry-runs**; schedule **reply-behavior polish** or **workbench parity** only if a real pilot blocker appears.

## Sprint timing

- **Start:** 2026-03-27 (sprint execution)
- **End:** 2026-03-27 (same session)
- **Elapsed:** ~15–25 minutes (implementation + `npm run build` + docs)
