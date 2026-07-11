# P19M-1B — Native Task Home UX and Interaction Audit

**Date:** 2026-07-11  
**Branch:** `sprint/p16-trust-layer`  
**Scope:** Mini Program Task Home interaction polish only — no backend/schema/deploy.

---

## 1. Safety (pre-change)

| Check | Result |
|-------|--------|
| Branch | `sprint/p16-trust-layer` ✓ |
| Pre-existing tracked changes (P19M-1A DevTools) | `entry.ts`, `project.config.json`, `taskLaunchContext.ts`, `config.ts` — **preserved, not included in this commit** |
| `config.local.ts` | Gitignored — not touched |
| Token / openid | Not committed |

---

## 2. Before findings

### What was clickable

- Blue primary CTA (`onPrimaryAction`) → correct destination page
- Secondary text button「查看全部资料」→ modal summary
- Disclaimer tap → modal (added in this sprint)

### What was NOT clickable (problem)

-「还缺」missing list — plain orange text rows, no tap handler
-「已收到」summary — correctly informational
- Meta row (事故经过 / 照片) — informational duplicate of missing list
-「下一步」text — informational

### What should be clickable

| Item | Destination | Status |
|------|-------------|--------|
| 事故经过 | `/pages/story/story` | ACTIONABLE_NOW |
| 是否受伤 / 事故时间 / 事故地点 / 您的车辆 | `/pages/basics/basics` | ACTIONABLE_NOW |
| 事故照片 | `/pages/photos/photos` | ACTIONABLE_NOW |
| 对方信息 / 对方车牌 / 是否报警 | — | DISPLAY_ONLY_PROTOTYPE |

### Primary CTA dead-route bug (fixed)

`resolveNextAction` fallback returned `route: /pages/task-home/task-home` — primary button did nothing on some backend states. Now routes to first actionable missing page or review.

---

## 3. Interaction map

```
Task Home
├── [informational] status pill, title, subtitle, progress
├── [informational] 已收到 list
├── [actionable rows] 还需补充 → story | basics | photos
├── [informational] 下一步 text
├── [primary CTA] one blue button (backend-derived)
└── [secondary] 查看全部资料 → modal
```

### Primary CTA mapping (backend wins)

| State | CTA | Route |
|-------|-----|-------|
| Story missing | 填写事故经过 | story |
| Basics missing | 继续补充资料 | basics |
| Photos &lt; 2 | 添加事故照片 | photos |
| Review ready | 检查并提交 | review |
| Submitted | 查看提交结果 | receipt |
| broker_needs_more_info | 补充陈总需要的资料 | first missing route |
| broker_done | 查看完成状态 | receipt |

---

## 4. Files changed (P19M-1B only)

| File | Change |
|------|--------|
| `miniapp/utils/taskMapping.ts` | `resolveMissingItemNav`, `buildSupplementRows`, `firstActionableMissingRoute`, CTA fixes |
| `miniapp/pages/task-home/task-home.ts` | Supplement rows, row tap navigation, navigating guard |
| `miniapp/pages/task-home/task-home.wxml` | Native task-row layout |
| `miniapp/pages/task-home/task-home.wxss` | Row styles, tap targets |
| `miniapp/app.wxss` | Button pressed/loading states |
| `tests/test_p19m1_mini_program_logic.py` | Mapping + CTA tests |

---

## 5. Pages audited

| Page | Verdict |
|------|---------|
| entry | Works — bootstrap + error retry |
| task-home | **Fixed** — clickable supplement rows, no dead primary CTA |
| story | Works — save → navigateBack, Task Home refreshes onShow |
| basics | Works — save → navigateBack |
| photos | Works — server refresh onShow |
| review | Works — submit gated by `canSubmit` |
| receipt | Works — view status / supplement photos |
| error | Works — retry to entry |

---

## 6. Tests

```bash
PYTHONPATH=. python3 -m pytest \
  tests/test_p19m1_mini_program_logic.py \
  tests/test_h5_claim_intake_form.py \
  tests/test_p19h3i_claim_task_dashboard_always_return_h5.py \
  tests/test_p19h3h_append_first_split_later.py \
  -q
```

New tests cover: missing-item → destination, CTA routes, completed items omitted, unsupported items non-actionable, submitted/broker_done/needs_more_info CTAs, no task-home dead route.

---

## 7. Founder manual checklist (DevTools — not pre-marked PASS)

- [ ] Task Home looks like one task app
- [ ] Exactly one main blue CTA
- [ ] 事故经过 row opens story page
- [ ] 时间/地点/受伤 row opens basics page where supported
- [ ] 照片 row opens photo page
- [ ] Save returns and refreshes Task Home
- [ ] Completed item changes from missing to received
- [ ] No dead or fake clickable controls
- [ ] Review CTA appears only when backend permits
- [ ] No console application errors

**Screenshots needed from Founder:** Task Home after compile; any row tap failure.

---

## 8. Remaining limits

- 对方信息 / 是否报警 — prototype has no edit page; shown as non-clickable with hint
- Review page missing list remains informational (edit via footer buttons)
- P19M-1A DevTools config changes remain uncommitted locally
- No deploy / publish / backend change

---

## 9. DevTools console notes

Expected harmless: WeChat base-library deprecation warnings.  
Application errors to watch: tap handler missing, navigation failures, stale bindings — none introduced by this change set.
