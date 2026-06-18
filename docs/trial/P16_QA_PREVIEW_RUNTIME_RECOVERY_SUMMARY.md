# P16 QA Preview Runtime Recovery Summary

**Sprint:** P16-QA-PREVIEW-ROUTER-RUNTIME-RECOVERY  
**Date:** 2026-06-07  
**For:** Andy (founder)

---

## 1. What broke? / 出了什么问题？

QA Preview 打开客户 tab 时，React Router 在运行时抛错：

> `[ble] is not a <Route> component`

页面空白或红屏，Customer First 界面完全无法显示。

---

## 2. Why Preview deployed but page crashed? / 为什么部署成功但页面崩溃？

- **Vercel 构建**只检查 TypeScript/打包，不会在构建时运行 React Router 的子路由校验。
- 问题代码在 `App.tsx`：非 product-only 分支使用了 `<LabRoutes />` 作为 `<Route>` 的子节点。
- 上一次 Preview **没有**设置 `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1`，运行时走了 lab 分支 → 触发崩溃。
- `ble` 是打包后 `LabRoutes` 函数的混淆名。

---

## 3. Was backend involved? / 和后端有关吗？

**没有。** 纯前端 React Router 配置问题。Cloud Run / Postgres 未参与此次崩溃。

---

## 4. Was customer data involved? / 和客户数据有关吗？

**没有。** 路由在页面挂载阶段就失败，尚未发起 phone lookup 或读写 case 数据。

---

## 5. What was fixed? / 修了什么？

**一行最小修复**（`ui/src/App.tsx`）：

- 之前：`<LabRoutes />`（React 把它当作普通组件，不是 Route）
- 之后：`{LabRoutes()}`（直接展开 Fragment + Route 子节点）

新 Preview 部署时同时加上：

- `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1`
- `VITE_UNIFIED_INTAKE_SUPERVISED_DEMO=1`
- `VITE_API_BASE_URL=https://fiqa-api-g7zatxrycq-uw.a.run.app`

---

## 6. Which Preview URL is safe now? / 现在用哪个 Preview？

| | URL |
|---|-----|
| **安全 Preview（新）** | https://ui-rj27hhjeh-andys-projects-1f411b73.vercel.app/workbench/unified-intake?tab=customer |
| **别名（同一部署）** | https://ui-waterwoods-andys-projects-1f411b73.vercel.app/workbench/unified-intake?tab=customer |
| **勿用（旧/坏）** | https://ui-emtvr6y44-andys-projects-1f411b73.vercel.app/... |

Deployment: `dpl_BXKreBJjZXVvABKnLXaUjfUkoxbW` · Bundle: `index-CMdMnAqV.js`

---

## 7. What should Andy open? / Andy 应该打开什么？

打开 **客户报送** tab：

https://ui-waterwoods-andys-projects-1f411b73.vercel.app/workbench/unified-intake?tab=customer

应看到：Add-Car Request · 手机号 · 姓名（选填）· Continue 按钮。三个 tab 均可切换，无红屏。

**可选后续：** 在 Vercel Preview 环境变量中配置 `VITE_UNIFIED_INTAKE_INTAKE_API_KEY`，以便 Continue 后能连上 Cloud Run 做 phone lookup（当前缺 key 会提示无法验证手机号，但不崩溃）。

---

## Related docs

- Root cause: `docs/trial/P16_QA_ROUTER_RUNTIME_ROOT_CAUSE.md`
- Local verification: `docs/trial/P16_QA_ROUTER_LOCAL_VERIFICATION.md`
- Deploy report: `docs/trial/P16_QA_ROUTER_DEPLOY_REPORT.md`
- Live certification: `docs/trial/P16_QA_ROUTER_LIVE_CERTIFICATION.md`

---

FINAL_SAFE_QA_PREVIEW_URL:
https://ui-waterwoods-andys-projects-1f411b73.vercel.app/workbench/unified-intake?tab=customer

VERDICT:
CONDITIONAL GO

---

*End of P16 QA Preview Runtime Recovery Summary*
