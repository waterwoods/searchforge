# Founder inspection notes (acceptance-style)

Use this when clicking through **Workbench → Unified Intake** with `?client=chen_kui` (or default client).

## Directly verified (this sprint)

- [x] `cd ui && npm run build` completes with exit code 0.

## Manual UI checklist (recommended next)

1. **Identity**: Top strip shows team name + `portal_brand_tagline` (not generic “统一入口” only).
2. **Service purpose**: Hero shows **客户统一受理与报送** + one paragraph on 报送 → 记录 → 办公室.
3. **First action**: Empty state headline tells user to **选办理类型** or **填写报送**; buttons labeled **办理加车报价** etc.
4. **Transaction**: Start add-car flow — blue **当前办理：加车报价** ribbon appears; input area shows **当前办理** chip.
5. **Thread**: Section title **本条办理过程与办公室整理**; bubbles say **您的报送** / **办公室整理回复**.
6. **Progress card**: Non–add-car title **当前受理进度**; note **状态随报送更新**.
7. **Input**: First submit **提交报送**; follow-up **提交补充**; placeholders mention 报送.
8. **Handoff**: Green card shows **办公室办理摘要** label above draft text.
9. **Tabs**: **客户报送 — 受理入口** reads as portal, not “客户聊天”.

## Inferred (not browser-tested in this run)

- Visual regression on narrow mobile width.
- Avatar load failure fallback text still **陈魁** (unchanged).

## Caveats

- **Bubble layout** is still message-thread geometry (inherent chat affordance); this sprint **did not** replace it with a form wizard.
- Some **internal tags** (e.g. English confirmation hints) remain for broker/debug clarity.
