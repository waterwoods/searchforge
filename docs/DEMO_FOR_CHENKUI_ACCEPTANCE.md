# Demo 验收标准文档（给保险经纪人陈奎）

**创建时间**: 2026-02-20  
**目标**: 验证 Auto Insurance RAG Demo 改造是否满足业务演示需求

---

## 一、验收标准

### ✅ 1. 页面展示验收

#### 1.1 页面标题
- [ ] 打开 Demo 页面能看到标题：
  - **"加州汽车保险智能助手（权威来源 Demo）"**

#### 1.2 数据来源说明
- [ ] 页面副标题下方有一行小字：
  - **"数据来源：加州 DMV / 加州保险监管机构 / 主流保险公司官方页面"**

#### 1.3 示例问题
- [ ] 页面显示 3 个可点击的示例问题按钮：
  1. "我刚买了新车，在加州最低需要买哪些保险？"
  2. "如果我出过一次事故，保费一般会涨多少？可以怎么降低？"
  3. "SR-22 是什么？什么情况下需要？"
- [ ] 点击任意示例问题，问题自动填入输入框

#### 1.4 演示模式开关
- [ ] 页面有"演示模式（只使用权威来源）"开关
- [ ] 开关可以正常切换（开启/关闭）

---

### ✅ 2. 功能验收

#### 2.1 示例问题回答质量
- [ ] 点击任意一个示例问题并提交
- [ ] 系统返回可读的答案（非空）
- [ ] 返回结果中包含 ≥ 2 条来源
- [ ] 至少 2 条来源来自 `dmv.ca.gov` 或 `insurance.ca.gov`

#### 2.2 来源展示增强
- [ ] 每条来源显示：
  - 来源 URL（可点击链接）
  - 来源域名（如 `dmv.ca.gov`）
  - 权威来源标识（绿色徽章"权威来源"）
- [ ] 权威来源判断规则：
  - `dmv.ca.gov` → 显示"权威来源"
  - `insurance.ca.gov` → 显示"权威来源"
  - `.gov` 域名 → 显示"权威来源"
  - `geico.com`, `progressive.com`, `statefarm.com` → 显示"权威来源"

#### 2.3 演示模式切换
- [ ] **关闭演示模式**时：
  - 使用原来的 `auto_insurance_v2_clean` collection
  - 返回结果可能包含各种来源（不限于官方）
- [ ] **开启演示模式**时：
  - 使用 `auto_insurance_demo_core` collection
  - 返回结果固定为 top_k=5
  - 返回结果主要来自官方来源（dmv.ca.gov, insurance.ca.gov 等）
- [ ] 切换前后，数据来源明显不同（可通过域名对比验证）

---

### ✅ 3. 技术验收

#### 3.1 后端 API 支持
- [ ] API 支持 `mode=demo` 参数
- [ ] 当 `mode=demo` 时：
  - 强制使用 `auto_insurance_demo_core` collection
  - 返回结果数量固定为 `top_k=5`
- [ ] API 返回字段包含：
  - `answer`（如果有 LLM 生成）
  - `sources[].title`
  - `sources[].url`
  - `sources[].domain`（或可从 URL 解析）

#### 3.2 前端请求
- [ ] 开启演示模式时，请求包含 `mode: "demo"`
- [ ] 关闭演示模式时，请求不包含 `mode` 字段（或 `mode: undefined`）

---

## 二、业务演示话术（3-5 句话）

**给陈奎的演示话术**：

> "这是我们为保险业务定制的智能助手 Demo。系统从加州 DMV、加州保险监管机构等官方来源收集了权威信息，可以快速回答客户关于汽车保险的常见问题。比如客户问'新车需要买哪些保险'，系统会立即从官方页面检索准确信息，并标注来源，确保回答的权威性和可信度。您看，这里显示的都是来自 dmv.ca.gov 和 insurance.ca.gov 的官方来源，客户可以放心使用。"

---

## 三、验收步骤

### 步骤 1: 启动服务
```bash
# 1. 构建 Demo 知识库（一次性）
cd /home/andy/searchforge
python3 scripts/build_demo_core_collection.py --top-n 20

# 2. 启动后端服务
cd services/fiqa_api
# 根据项目启动方式启动后端（如：uvicorn app_main:app --reload）

# 3. 启动前端服务
cd ui
npm run dev
```

### 步骤 2: 打开 Demo 页面
1. 浏览器访问前端地址（通常是 `http://localhost:5173` 或类似）
2. 导航到 Demo 页面

### 步骤 3: 验证页面展示
- [ ] 检查标题是否为"加州汽车保险智能助手（权威来源 Demo）"
- [ ] 检查是否有数据来源说明
- [ ] 检查是否有 3 个示例问题按钮
- [ ] 检查是否有"演示模式"开关

### 步骤 4: 测试示例问题
1. 点击第一个示例问题："我刚买了新车，在加州最低需要买哪些保险？"
2. 点击"Ask"按钮
3. 验证：
   - [ ] 返回了可读答案
   - [ ] 返回了 ≥ 2 条来源
   - [ ] 至少 2 条来源来自 `dmv.ca.gov` 或 `insurance.ca.gov`
   - [ ] 来源显示域名和"权威来源"标识

### 步骤 5: 测试演示模式切换
1. **关闭演示模式**，提交一个问题
2. 记录返回的来源域名
3. **开启演示模式**，提交相同问题
4. 验证：
   - [ ] 返回结果数量为 5 条
   - [ ] 来源域名与关闭模式时不同
   - [ ] 主要来源为官方域名（dmv.ca.gov, insurance.ca.gov）

---

## 四、30 秒 Demo 操作步骤（给陈奎演示用）

1. **打开页面**（3秒）
   - 展示页面标题："加州汽车保险智能助手（权威来源 Demo）"
   - 指出数据来源说明："数据来源：加州 DMV / 加州保险监管机构 / 主流保险公司官方页面"

2. **演示示例问题**（10秒）
   - 点击第一个示例问题："我刚买了新车，在加州最低需要买哪些保险？"
   - 点击"Ask"按钮
   - 等待结果返回

3. **展示结果**（10秒）
   - 展示返回的答案
   - 指出来源："看，这些都是来自 dmv.ca.gov 和 insurance.ca.gov 的官方来源"
   - 指出"权威来源"标识："每个来源都标注了'权威来源'，确保信息可信"

4. **演示模式切换**（7秒）
   - 开启"演示模式"开关
   - 再次提交问题
   - 对比："开启演示模式后，系统只使用我们精选的权威来源，确保回答更准确"

---

## 五、已知问题和限制

### 当前限制
1. Demo collection 只包含 Top 20 个页面，覆盖范围有限
2. 如果某些官方页面无法访问，可能影响结果质量
3. 演示模式固定返回 5 条结果，无法调整

### 未来改进建议
1. 扩展 Demo collection 到 50-100 个高质量页面
2. 增加更多保险公司官方页面（USAA, Liberty Mutual 等）
3. 支持自定义 top_k（在演示模式下）

---

## 六、文件清单

### 修改的文件
1. `scripts/build_demo_core_collection.py` - 新建：构建 Demo 知识库脚本
2. `services/fiqa_api/services/search_core.py` - 修改：添加 demo_auto_insurance 映射
3. `services/fiqa_api/routes/query.py` - 修改：支持 mode=demo 参数
4. `ui/src/pages/DemoPage.tsx` - 修改：前端页面改造
5. `ui/src/pages/DemoPage.css` - 修改：新增样式支持
6. `docs/DEMO_FOR_CHENKUI_ACCEPTANCE.md` - 新建：本验收文档

### 新增的 Collection
- `auto_insurance_demo_core` - Demo 专用知识库

---

## 七、本地启动命令

### 一次性构建 Demo 知识库
```bash
cd /home/andy/searchforge
python3 scripts/build_demo_core_collection.py --top-n 20
```

### 启动后端服务
```bash
cd /home/andy/searchforge/services/fiqa_api
# 根据项目配置启动（例如：uvicorn app_main:app --reload --port 8000）
```

### 启动前端服务
```bash
cd /home/andy/searchforge/ui
npm run dev
```

### 访问 Demo 页面
- 前端地址：`http://localhost:5173`（或根据 Vite 配置的端口）
- 导航到 Demo 页面

---

**验收完成标志**：所有 ✅ 项都已勾选，30 秒 Demo 可以流畅演示。
