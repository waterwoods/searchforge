# UI Smoke Instructions – Steward Chat

## Startup

1. **Backend** – start the orchestrate/experiment backend (fill in the actual command for your environment):
   ```bash
   # TODO: start backend service (uvicorn / docker-compose / make target)
   ```
2. **Frontend** – launch Vite dev server from the `ui` workspace:
   ```bash
   cd ui
   npm run dev
   ```

## Manual Verification

1. Open the steward dashboard: <http://localhost:5173/rag-lab/steward>.
2. Switch到 **Chat** 页签，输入并发送 `hello`。
3. 在浏览器 Network 面板确认：
   - `POST /orchestrate/run` 返回 `200/202`，响应体包含 `job_id`。
   - 之后每 ~2 秒触发 `GET /orchestrate/status?job_id=...`（实际已由 Vite 代理重写为 `/api/experiment/status`）。
4. 在 UI 右侧观察：
   - 发送后出现用户消息与“运行中…”提示。
   - 轮询返回的日志 / 摘要会持续追加到列表。
   - 最终展示 `SUCCEEDED` 或 `FAILED` 结束状态。
5. 点击 **Stop** 按钮，确认后续轮询立即终止（Network 不再生成新的 status 请求）。

> 若后端暂未实现 `preset=chat`，也应返回 4xx/5xx，并在界面上显示可读的错误信息。


