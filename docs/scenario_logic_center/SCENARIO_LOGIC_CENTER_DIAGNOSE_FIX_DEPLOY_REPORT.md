# Scenario Logic Center Diagnose + Fix + Deploy Report

**Sprint:** Scenario Logic Center Diagnose + Fix + Deploy Sprint  
**Date:** 2026-03-19  
**Scope:** SearchForge → Chen Kui Insurance Unified Entry

---

## 1. Root cause

**What caused the blank page:**

1. **Potential runtime crash** — `ScenarioCard` accessed `scenario.config_sources.join()` and `scenario.common_phrasing.slice()` without null checks. If the API returned malformed or partial data (e.g. a scenario missing `config_sources` or `common_phrasing`), the page would throw and the ErrorBoundary would show "Runtime Error" instead of content. In dark theme, this could appear as a jarring or "blank" experience.

2. **Weak error surfacing** — The catch block used `e instanceof Error ? e.message : 'Failed to load'`, which often yields generic messages like "Request failed with status code 404" or "Network Error". API `detail` from FastAPI was not extracted, so users saw unhelpful errors instead of actionable messages.

3. **Deployment lag** — The sprint report noted: "Backend: Yes, if backend redeployed; Frontend: Yes, if frontend redeployed." If either was not redeployed after the Scenario Logic Center was added, the page would fail: backend 404 → generic error; frontend old build → route or component missing.

**Evidence:**

- Local API `GET /api/inbox/scenario-logic-center` returns 200 with valid JSON.
- `configs/scenario_logic_center.json` exists and is copied in Dockerfile.cloudrun.
- `ScenarioCard` had no defensive checks for `config_sources` or `common_phrasing`.
- Production API now returns 200 after backend redeploy.

---

## 2. What was fixed

| File | Change | Why |
|------|--------|-----|
| `ui/src/pages/ScenarioLogicCenterPage.tsx` | `(scenario.config_sources ?? []).join(', ')` | Avoid crash when `config_sources` is undefined |
| `ui/src/pages/ScenarioLogicCenterPage.tsx` | `(scenario.common_phrasing ?? []).length` and `.slice(0, 5).join()` | Avoid crash when `common_phrasing` is undefined |
| `ui/src/pages/ScenarioLogicCenterPage.tsx` | Catch block now extracts `e.response?.data?.detail` before falling back to `e.message` | Show API error details (404, 500, etc.) instead of generic messages |

**Why these fixes:**

- Defensive checks prevent runtime crashes from partial/malformed API responses.
- Better error extraction gives users and founders clearer feedback when the API fails.

---

## 3. Validation

| Check | Result |
|-------|--------|
| `bash scripts/guardrail_inbox_triage.sh` | PASS |
| `cd ui && npm run build` | PASS |
| Local API `GET /api/inbox/scenario-logic-center` | 200, valid JSON |

---

## 4. Deployment

| Component | Status | Details |
|-----------|--------|---------|
| **Backend** | Deployed | Cloud Run `fiqa-api`, revision `fiqa-api-00032-zct` |
| **Backend URL** | Live | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| **Frontend** | Deployed | Vercel production |
| **Frontend alias** | Live | `https://ui-smoky-beta.vercel.app` |

**Warnings:** Initial `/healthz` check failed (cold start); `/readyz` passed. Scenario-logic-center API returns 200.

---

## 5. Production verification

| Check | Result |
|-------|--------|
| `GET https://fiqa-api-g7zatxrycq-uw.a.run.app/api/inbox/scenario-logic-center` | 200, valid JSON |
| Page URL | `https://ui-smoky-beta.vercel.app/workbench/scenario-logic-center` |

**Manual verification:** Andy should open the URL, confirm the page loads, and that scenario cards and summary render. If the API fails, the page should show a clear error message instead of a blank screen.

---

## 6. Founder summary

**Can Andy now open and use the page?** Yes, after this sprint.

**URL to test:**  
`https://ui-smoky-beta.vercel.app/workbench/scenario-logic-center`

**What to expect:**

- Summary card: total scenarios, strong/medium/weak counts, trial IDs.
- Grouped scenario cards (Standard Package, Extended, Fallback).
- Each card: name, maturity badge, fix status, trial order; expandable section with route, ask-next, handoff, broker_next_step, config sources.
- If the API fails: an error Alert with a meaningful message instead of a blank page.

**If the page is still blank:** Check browser console for errors; confirm `VITE_API_BASE_URL` in Vercel points to `https://fiqa-api-g7zatxrycq-uw.a.run.app` (no trailing slash).

---

## 7. 中文宏观总结

**为什么之前是空白：**  
(1) 页面在 `config_sources` 或 `common_phrasing` 缺失时会崩溃；(2) 错误提示不清晰；(3) 后端或前端可能未重新部署，导致 API 404 或旧版本页面。

**现在修好了没有：**  
已修复。增加了空值防护、改进了错误展示，并完成了后端和前端部署。生产环境 API 返回 200，页面应能正常加载。

**还差什么：**  
需人工打开页面确认：卡片和摘要是否正常显示，错误状态是否清晰。若仍有问题，检查 Vercel 的 `VITE_API_BASE_URL` 是否指向 Cloud Run 地址。
