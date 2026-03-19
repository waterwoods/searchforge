# Demo UI 强化验收报告

**日期**: 2026-02-21  
**目标**: 前端 Demo 强化，最小可跑

---

## 一、交付物清单

| 文件 | 状态 |
|------|------|
| `ui/src/pages/DemoPage.tsx` | ✅ 已改 |
| `ui/src/pages/DemoPage.css` | ✅ 已改 |
| `ui/src/utils/demoCopy.ts` | ✅ 新增 |
| `docs/DEMO_UI_ENHANCEMENT_REPORT.md` | ✅ 本报告 |

---

## 二、实现摘要

### Step A — 现有 Demo 页面确认

- **路由**: `/demo`，独立于 AppLayout（`ui/src/App.tsx` 第 105 行）
- **API**: `POST /api/query`，支持 `mode`、`translation_mode`、`top_k`
- **响应**: `sources` 含 `source_url`、`url`、`domain`、`title_zh`、`text_zh`

### Step B — 中文业务 Demo 体验

- **页面标题**: 加州汽车保险智能助手（给陈奎 Demo）
- **三个示例问题**（点击自动填入并发送）:
  1. 我刚买了新车，在加州最低需要买哪些汽车保险？
  2. 如果我没有保险或者保险中断，会有什么后果？怎么恢复车辆注册？
  3. 客户想省钱：哪些因素会影响保费？有哪些常见折扣/优惠？
- **默认参数**: `mode="demo"`、`translation_mode="auto"`、`top_k=5`
- **演示模式**: 默认 ON，关闭时 `mode` 不传
- **引用卡片**: domain + 可点击 url + 徽章（GOV / INSURER / OTHER）
- **复制按钮**: 复制【问题】【答案】【引用】纯文本格式

### Step C — 系统状态条

- **Backend**: `GET /healthz`，成功绿色 Connected，失败红色 Disconnected
- **Translation**: 根据最后一次 query 的 `translation_applied` 或 `text_zh` 显示 ON/OFF/Unknown
- **Citations**: sources 中 ≥2 条且含 url+domain 显示 OK，否则 Missing

### Step D — 样式

- 状态条、按钮区、来源卡片、徽章样式均在 `DemoPage.css` 中
- 未改动全局 CSS

---

## 三、验收结果

### 3.1 本地验证（2026-02-21）

| 检查项 | 结果 |
|--------|------|
| 前端启动 | ✅ `npm run dev` 正常 |
| 后端 8001 | ✅ `curl http://127.0.0.1:8001/healthz` 返回 200 |
| 示例问题点击 | ✅ 三个按钮点击后自动发送请求 |
| 引用卡片 | ✅ 显示 domain、可点击 url、GOV/INSURER/OTHER 徽章 |
| 复制按钮 | ✅ 复制【问题】【答案】【引用】纯文本 |
| 状态条 | ✅ Backend / Translation / Citations 显示正确 |

### 3.2 API 响应示例

```json
{
  "ok": true,
  "translation_applied": true,
  "sources": [
    {
      "doc_id": "...",
      "title": "Liability Car Insurance Coverage | USAA",
      "title_zh": "责任车保险",
      "text_zh": "责任汽车保险是什么? ...",
      "source_url": "https://www.usaa.com/inet/wc/liability-auto-insurance/",
      "domain": "www.usaa.com",
      "score": 0.73
    }
  ]
}
```

---

## 四、启动命令合集

### 后端（端口 8001）

```bash
cd /home/andy/searchforge
# 加载环境变量（如 .env 或 .env.cloudrun）
set -a && source .env.cloudrun && set +a
# 启动后端
TRANSLATION_ENABLED=1 TRANSLATION_PROVIDER=argos python3 -m uvicorn services.fiqa_api.app_main:app --host 0.0.0.0 --port 8001
```

或使用 dev_local（需指定端口）:

```bash
BACKEND_PORT=8001 ./scripts/dev_local.sh
```

### 前端

```bash
cd /home/andy/searchforge/ui
npm run dev
```

### 一键启动（后端 8001 + 前端）

```bash
cd /home/andy/searchforge
set -a && source .env.cloudrun 2>/dev/null || true && set +a
TRANSLATION_ENABLED=1 TRANSLATION_PROVIDER=argos python3 -m uvicorn services.fiqa_api.app_main:app --host 0.0.0.0 --port 8001 &
sleep 5
cd ui && npm run dev
```

---

## 五、Demo 演示步骤（30 秒版）

1. **打开页面**: 浏览器访问 `http://localhost:5173/demo`
2. **确认状态条**: Backend 绿色 Connected，Translation 执行一次查询后显示 ON
3. **点击示例问题**: 任选三个中文问题之一，点击后自动发送
4. **查看结果**: 答案区 + 引用卡片（domain、url、GOV/INSURER 徽章）
5. **复制给客户**: 点击「复制给微信/客户」，粘贴到微信/文档即可

---

## 六、配置说明

- **后端端口**: 默认 8001（Vite proxy 与 API_BASE_URL 均指向 8001）
- **使用 8000**: 设置 `VITE_API_PROXY_TARGET=http://127.0.0.1:8000` 并 `VITE_API_BASE_URL=http://127.0.0.1:8000` 后重启前端
