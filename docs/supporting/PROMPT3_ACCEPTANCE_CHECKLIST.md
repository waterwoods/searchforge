# Prompt 3 自动验收清单

本文档用于验收 Prompt 3 的所有交付物。

## ✅ 验收标准

### 1. 后端 Demo API 标准化

- [ ] **健康检查端点**
  - [ ] `GET /healthz` 返回 200 OK
  - [ ] 响应格式：`{"ok": true, "status": "healthy", ...}`
  - [ ] `GET /readyz` 返回 200 OK（当服务就绪时）
  - [ ] 响应格式：`{"ok": true, "clients_ready": true, ...}`

- [ ] **查询 API 端点**
  - [ ] `POST /api/query` 端点存在且可访问
  - [ ] 请求格式正确：
    ```json
    {
      "question": "How to file a car insurance claim in California?",
      "top_k": 5
    }
    ```
  - [ ] 响应格式符合要求：
    ```json
    {
      "ok": true,
      "sources": [
        {
          "doc_id": "...",
          "score": 0.52,
          "title": "...",
          "text": "...",
          "source_url": "..."
        }
      ]
    }
    ```
  - [ ] `sources` 数组中的每个对象包含所有必需字段：
    - [ ] `doc_id` (string)
    - [ ] `score` (number, 0-1)
    - [ ] `title` (string)
    - [ ] `text` (string)
    - [ ] `source_url` (string, 可为空)

- [ ] **环境变量配置**
  - [ ] Base URL 从环境变量读取（不硬编码）
  - [ ] 支持 `VITE_API_BASE_URL` 环境变量

---

### 2. 前端 Demo 页面

- [ ] **页面功能**
  - [ ] 输入框可以输入问题（支持中英文）
  - [ ] "Ask" 按钮可以提交查询
  - [ ] 显示 Top-K 命中结果（默认 5 个）
  - [ ] 每个结果显示：
    - [ ] Title（标题）
    - [ ] Text snippet（文本片段）
    - [ ] Score（相似度分数）
    - [ ] Source URL（来源链接，可点击）
  - [ ] 显示请求耗时（ms）
  - [ ] 错误处理（显示错误信息）

- [ ] **API 集成**
  - [ ] 使用 `fetch` 调用后端 `/api/query`
  - [ ] Base URL 从 `import.meta.env.VITE_API_BASE_URL` 读取
  - [ ] 请求格式正确（JSON body）
  - [ ] 响应解析正确

- [ ] **UI/UX**
  - [ ] 页面布局清晰
  - [ ] 响应式设计（可在移动端查看）
  - [ ] 加载状态显示
  - [ ] 错误状态显示

- [ ] **路由配置**
  - [ ] Demo 页面可通过 `/demo` 路由访问
  - [ ] 不需要登录或认证

---

### 3. 本地运行脚本和文档

- [ ] **环境配置文件**
  - [ ] `ui/.env.example` 文件存在
  - [ ] 包含 `VITE_API_BASE_URL` 配置示例

- [ ] **README 文档**
  - [ ] `ui/README.md` 包含 Demo 快速启动指南
  - [ ] 包含以下步骤：
    - [ ] 复制 `.env.example` 到 `.env.local`
    - [ ] 设置 `VITE_API_BASE_URL`
    - [ ] `npm install`
    - [ ] `npm run dev`
    - [ ] 访问 `/demo` 页面
  - [ ] 说明清晰，新手 5 分钟可跑起来

- [ ] **依赖管理**
  - [ ] `package.json` 存在且配置正确
  - [ ] 可以成功运行 `npm install`
  - [ ] 可以成功运行 `npm run dev`

---

### 4. Demo 演示脚本

- [ ] **文档存在**
  - [ ] `docs/DEMO_SCRIPT.md` 文件存在

- [ ] **内容完整性**
  - [ ] 包含 3 个推荐 Demo 问题：
    - [ ] "加州最低汽车保险要求是什么？"
    - [ ] "How to file a car insurance claim?"
    - [ ] "中文用户如何联系保险公司客服？"
  - [ ] 每个问题包含：
    - [ ] 问题文本
    - [ ] 操作步骤
    - [ ] 讲解话术
    - [ ] 预期结果

- [ ] **演示流程**
  - [ ] 健康检查步骤
  - [ ] 查询演示步骤
  - [ ] 命中来源展示
  - [ ] 技术亮点总结

- [ ] **实用性**
  - [ ] 话术可以直接照稿给陈奎 / HR 讲
  - [ ] 时间安排合理（8-10 分钟）

---

### 5. 自动验收清单（本文档）

- [ ] **清单完整性**
  - [ ] 包含所有 5 个任务的验收项
  - [ ] 每个验收项可打勾
  - [ ] 验收标准明确

---

## 🧪 E2E 测试步骤

### 测试 1：健康检查

```bash
# 测试 /healthz
curl -X GET {API_BASE_URL}/healthz
# 预期：200 OK, {"ok": true, ...}

# 测试 /readyz
curl -X GET {API_BASE_URL}/readyz
# 预期：200 OK, {"ok": true, "clients_ready": true, ...}
```

- [ ] `/healthz` 返回 200 OK
- [ ] `/readyz` 返回 200 OK（服务就绪时）

---

### 测试 2：查询 API

```bash
# 测试 /api/query
curl -X POST {API_BASE_URL}/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How to file a car insurance claim in California?",
    "top_k": 5
  }'
```

- [ ] 返回 200 OK
- [ ] 响应包含 `"ok": true`
- [ ] 响应包含 `"sources"` 数组
- [ ] `sources` 数组长度 <= 5
- [ ] 每个 source 包含所有必需字段

---

### 测试 3：前端连接

1. 启动前端：`cd ui && npm run dev`
2. 访问：`http://localhost:5173/demo`
3. 输入问题："加州最低汽车保险要求是什么？"
4. 点击 "Ask" 按钮

- [ ] 页面可以正常加载
- [ ] 可以输入问题
- [ ] 点击按钮后显示加载状态
- [ ] 返回结果并显示在页面上
- [ ] 显示请求耗时
- [ ] 结果包含 title, text, score, source_url

---

### 测试 4：中文查询命中英文资料

1. 在 Demo 页面输入："加州最低汽车保险要求是什么？"
2. 点击 "Ask"

- [ ] 返回结果（即使查询是中文）
- [ ] 结果包含英文内容
- [ ] Score > 0.3（表示相关性）

---

### 测试 5：Demo 文档可用性

1. 打开 `docs/DEMO_SCRIPT.md`
2. 按照文档执行演示

- [ ] 文档内容完整
- [ ] 可以按照文档完成演示
- [ ] 话术可以直接使用

---

## 📊 验收结果

### 总体状态

- [ ] ✅ 所有验收项通过
- [ ] ⚠️ 部分验收项未通过（需修复）
- [ ] ❌ 关键验收项未通过（需重新开发）

### 未通过项记录

（在此记录未通过的验收项及原因）

---

## 🎯 最终验收标准

**必须满足以下所有条件：**

1. ✅ 能在浏览器中访问前端 Demo 页面
2. ✅ 输入问题 → 能看到真实 Qdrant Cloud 的检索结果
3. ✅ Demo 文档可直接照稿给陈奎 / HR 讲
4. ✅ 所有 URL、Key 都来自环境变量（不硬编码）
5. ✅ README 写清楚新手 5 分钟跑起来

---

## 📝 验收记录

**验收日期**：_____________  
**验收人**：_____________  
**备注**：_____________
