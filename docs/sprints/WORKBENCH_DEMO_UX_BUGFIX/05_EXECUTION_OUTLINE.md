# Execution Outline

**Sprint:** Workbench Demo UX + Visual Bug Fix Sprint

---

## 1. Workstreams

| # | Workstream | Owner | Scope |
|---|------------|-------|-------|
| 1 | Demo queue interaction | Frontend | handleLoadFounderQueue; feedback; toasts; error |
| 2 | Visual readability | Frontend | Theme; card contrast; tags; text |
| 3 | Final usability | Frontend | Scroll hint; empty state; selected state |

---

## 2. Implementation Order

1. **Loop 1:** Demo queue — feedback, Chinese toasts, error visibility, scroll hint
2. **Loop 2:** Visual — light theme for workbench; card contrast
3. **Loop 3:** Final — one more clarity improvement (e.g. loaded indicator, section heading)

---

## 3. Test Plan

- `cd ui && npm run build` after each loop
- Manual: click 加载演示队列; verify feedback; verify cards readable
- Optional: `bash scripts/demo_pre_checklist.sh` if backend up

---

## 4. Loop Plan

| Loop | Focus | Exit criteria |
|------|-------|---------------|
| 1 | Queue interaction | Founder understands load result |
| 2 | Visual contrast | Cards readable without highlight |
| 3 | Final hardening | One more clarity improvement |
