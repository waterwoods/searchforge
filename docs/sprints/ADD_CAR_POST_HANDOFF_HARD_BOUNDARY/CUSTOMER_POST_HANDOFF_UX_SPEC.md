# Customer Post-Handoff UX Spec — Add-Car

## Principles

1. **Optimize for boundaries**, not more chat volume.  
2. **One closed request** + optional **same-lane supplement** + explicit **new-request** escape hatch.  
3. **Amazon-style**: status visible, next action obvious.

## Handoff closure card (customer entry)

When `handoff_ready` and last turn is system:

- **Status chip** (add-car): `handoff_status_badge_add_car` — e.g. “已提交 · 办公室处理中”.
- **Headline + processing copy** from `ui_copy` (`handoff_closure_*`).
- **Office reply** bubble (last system content).
- **Reroute hint** (`handoff_new_issue_hint`) — emphasizes 工单式 “提交新问题” for unrelated topics.

## Same-request lane (only when `case_id` exists)

Collapsed by default (`Collapse`):

- **Title** (`handoff_same_request_panel_title`): e.g. “还要继续补充本次加车？（同一服务记录）”.
- **Intro** (`handoff_same_request_panel_intro`): lists allowed intents; forbids unrelated topics here.
- **Action**: `POST .../append-message` via existing API — appends to **same** case.

## Toasts after append

- `new_issue` → warning: prefer 「提交新问题」next time.  
- `borderline` → info: office may confirm scope.  
- Else → success.

## Primary CTAs

- **查看工作台** (primary solid)  
- **提交新问题** (primary ghost) — visually paired as the “new ticket” path.

## Copy source

`configs/clients/chen_kui/ui_copy.json` (served through `/api/inbox/client-config`).
