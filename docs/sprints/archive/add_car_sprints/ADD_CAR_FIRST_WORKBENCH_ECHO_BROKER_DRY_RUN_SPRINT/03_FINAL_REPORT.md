# ADD-CAR-FIRST WORKBENCH ECHO + BROKER DRY RUN — Final report

## What changed

- **Broker tab chrome**: Secondary label is now Add-Car-first + **与客户报送同一服务记录** (via `portal_tab_office_suffix`), parallel to the customer tab suffix pattern.
- **Workbench hero**: Subtitle and tags explicitly state **同源服务记录**、**加车报价试点旗舰路径**、**不自动对外发送** (`office_workbench_subtitle` + inline tags).
- **Queue & paste cards**: Titles and empty state use **服务记录** language and **与客户报送同源** (`office_workbench_*` keys).
- **Loading / demo copy**: “整理服务记录”、演示路径与 toast 与队列标题一致。
- **Add-car case hint**: Aligned to customer CTA **「办理加车报价」** (removed stale「获取报价 / 加车」).
- **Browser title**: `office_workbench_document_title` — **加车报价试点 · 办公室工作台**.
- **Config**: New `ui_copy` keys in `clientConfig.ts` defaults, `chen_kui/ui_copy.json`, and `config_loader.py` whitelist so API can serve overrides after backend deploy.

## What improved

- Office surface **echoes** the same Add-Car-first and **服务记录** narrative as customer entry.
- **Same-case** feeling: explicit language that portal submissions and pasted messages share one queue concept.
- **Broker scan**: Tab + hero answer “is this the desk view of the portal?” faster.

## Dry-run tested

- **Direct**: `cd ui && npm run build` (success). Code review of `UnifiedIntakePage` broker tab strings and tab bar wiring.
- **Inferred**: UX coherence by reading customer `PILOT_INTRO` + portal copy side-by-side with new workbench strings (no browser session in this run).
- **Not verified**: Live API `GET /api/inbox/client-config` returning new keys against a running server; end-to-end click test in browser.

## What remains

- **Case id** prominence in workbench list cards (optional next): surface `case_id` on queue cards for “同一张单” parity with customer **服务记录编号**.
- **Backend-dependent clients**: Until backend is redeployed, new JSON keys are merged from **frontend defaults** only; deploy backend to serve overrides from `ui_copy.json` per client.

## Recommended next sprint

- **Pilot closure**: One broker walkthrough script + optional queue-card **记录编号** chip for instant “same ticket” recognition.
