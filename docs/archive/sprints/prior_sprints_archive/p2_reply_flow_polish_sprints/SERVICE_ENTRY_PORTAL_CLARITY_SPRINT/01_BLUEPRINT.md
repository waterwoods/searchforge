# SERVICE_ENTRY_PORTAL_CLARITY_SPRINT — Blueprint

## Mission

Refine **Unified Intake** customer-facing UI so it reads as a **formal business service-entry portal** (统一受理 / 报送 / 办公室跟进), not a generic **AI chat demo**.

## Execution loops (document-driven)

1. **Audit** — Inspect `UnifiedIntakePage.tsx`, `clientConfig.ts`, `configs/clients/*/ui_copy.json`, branded header.
2. **UX structure** — Lock section order: identity → service line → entry paths → transaction → input → thread → progress → closure/record/next step.
3. **Copy hierarchy** — Define Chinese labels favoring 报送 / 办理 / 记录 / 跟进 / 当前办理 / 办公室; avoid 聊天 / 对话 / 助手 overuse.
4. **Low-risk implementation** — Config-driven strings + label/structure tweaks only; **no triage logic changes**.
5. **Validation** — `cd ui && npm run build`; founder-style checklist.
6. **Summarize** — `08_FINAL_REPORT.md` + user-facing report.

## Success criteria (founder-readable)

| # | Criterion |
|---|-----------|
| 1 | Page states **who it is for** (brand strip + service line). |
| 2 | Page states **what service** (受理 / 报送 → 记录 → 办公室). |
| 3 | **First action** is obvious (办理类型 buttons + 提交报送). |
| 4 | **Current transaction** is visible (加车 ribbon + 当前办理 tags + progress card). |
| 5 | **Recorded state** reads as case-style (已记录项 / 办公室办理摘要 / 跟进 timing). |
| 6 | **Next step** is explicit (办公室跟进 / 提交新问题 / 追加到本条记录). |

## Non-goals

Backend architecture, OCR, carrier APIs, workflow engines, framework swaps, broad visual experiments, new verticals.

## Time budget

Target 45–90 minutes; this sprint stayed within **display + copy + config** scope.
