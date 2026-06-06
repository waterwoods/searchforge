# UI 白屏修复报告

**日期**: 2026-02-21  
**目标**: 定位并修复 `/demo` 白屏问题

---

## 一、根因判断

| 检查项 | 结果 |
|--------|------|
| Build 错误 | **PASS** - `npm run build` 无 TS/导入错误 |
| 路由未命中 | **待验证** - 已加顶层 `/demo` 路由 + smoke 组件 |
| 运行时崩溃 | **待验证** - 已加 ErrorBoundary 捕获 |

**当前结论**: Build 正常。白屏更可能来自：
1. **路由未命中**：`/demo` 被 `path="/"` 的父路由“吃掉”，未渲染顶层 demo 路由
2. **DemoPage 运行时崩溃**：组件内 hooks、antd、fetch 等抛错
3. **主题/样式**：暗色主题导致内容不可见

---

## 二、关键证据

### /tmp/ui_build.log 摘要
```
✓ 6280 modules transformed.
✓ built in 21.40s
```
无错误。

### /tmp/ui_dev.log 摘要
```
VITE v7.2.2  ready in 146 ms
➜  Local:   http://localhost:5175/
```
`GET /demo` 返回 200。

---

## 三、已做改动

### 新增文件
- `ui/src/pages/DemoRouteSmoke.tsx` - 最小 smoke 组件（无 antd）
- `ui/src/components/ErrorBoundary.tsx` - 捕获运行时错误并显示 message + stack

### 修改文件
- `ui/src/main.tsx` - 用 ErrorBoundary 包住 `<BrowserRouter><App /></BrowserRouter>`
- `ui/src/App.tsx`:
  - 新增**顶层路由** `<Route path="/demo" element={...} />`（与 `path="/"` 平级）
  - `/demo` 直接渲染 DemoPage，不经过 AppLayout
  - 用 ConfigProvider 亮色主题 + 白底 div 包裹 DemoPage

### AppLayout 检查
- `ui/src/components/layout/AppLayout.tsx` 已包含 `<Outlet />`
- 子路由 `path="demo"` 已从 AppLayout 内移除，改为顶层 `/demo`

---

## 四、验收步骤

### 1. 启动
```bash
cd ~/searchforge/ui
npm run dev
```
（端口可能是 5173/5174/5175，视占用情况）

### 2. 访问
打开 `http://localhost:5173/demo`（或实际端口）

### 3. 预期结果

| 情况 | 预期 |
|------|------|
| 白屏 + 无 ErrorBoundary | 路由或根级崩溃，需看 Console |
| 红字错误（ErrorBoundary） | 运行时崩溃，按 stack 修 |
| 看到 “Demo route smoke OK” | 路由命中，可切回 DemoPage 排查 |
| 看到 Demo 标题/内容 | 修复成功 |

### 4. Smoke 测试（若 DemoPage 仍白屏）
在 `App.tsx` 中临时把 `/demo` 的 element 改为 `<DemoRouteSmoke />`：
```tsx
<Route path="/demo" element={<DemoRouteSmoke />} />
```
若此时能看到 “Demo route smoke OK”，则问题在 DemoPage；否则在 Router/App 根级。

---

## 五、最终改动文件列表

| 文件 | 操作 |
|------|------|
| `ui/src/pages/DemoRouteSmoke.tsx` | 新增 |
| `ui/src/components/ErrorBoundary.tsx` | 新增 |
| `ui/src/main.tsx` | 修改（ErrorBoundary） |
| `ui/src/App.tsx` | 修改（顶层 /demo 路由） |
| `docs/UI_WHITESCREEN_FIX.md` | 新增（本报告） |

---

## 六、后续排查建议

1. **F12 → Console**：查看是否有红色报错
2. **F12 → Network**：确认 `/demo` 请求返回 200
3. **F12 → Elements**：检查 `#root` 下是否有 Demo 相关 DOM
4. 若 ErrorBoundary 显示错误：按 stack 定位并修复对应文件
