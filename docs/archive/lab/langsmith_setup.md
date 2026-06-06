# LangSmith Tracing 设置指南

## 获取 LANGCHAIN_API_KEY

### 步骤 1: 注册/登录 LangSmith

1. 访问 [LangSmith 官网](https://smith.langchain.com/)
2. 点击右上角 **"Sign in"** 或 **"Get Started"**
3. 使用 GitHub 或 Google 账号登录，或创建新账号

### 步骤 2: 创建 API Key

1. 登录后，点击右上角头像图标
2. 在下拉菜单中选择 **"Settings"**
3. 在左侧菜单中点击 **"API Keys"**
4. 点击 **"Create API Key"** 按钮
5. 输入一个描述性的名称（例如：`searchforge-dev` 或 `searchforge-prod`）
6. 点击 **"Create"**
7. **重要**：立即复制显示的 API Key（格式类似 `ls-xxxxx...`），因为它只会显示一次！

### 步骤 3: 设置环境变量

#### 方式 1: 在项目根目录的 `.env` 文件中添加

在项目根目录（`/home/andy/searchforge/.env`）中添加以下内容：

```bash
# LangSmith Tracing (可选 - 非侵入式)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls-your-api-key-here
LANGCHAIN_PROJECT=searchforge-mortgage
```

如果要同时启用 Mortgage 和 Ops 的 tracing，可以使用不同的 project 名称：

```bash
# LangSmith Tracing
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls-your-api-key-here

# Mortgage 部分使用这个 project
LANGCHAIN_PROJECT=searchforge-mortgage

# Ops 部分可以在代码中单独设置，或使用同一个 project
# 注意：如果两个都用同一个 project，traces 会混在一起
```

#### 方式 2: 在终端中临时设置（仅当前会话有效）

```bash
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=ls-your-api-key-here
export LANGCHAIN_PROJECT=searchforge-mortgage

# 然后运行你的脚本
python experiments/single_home_graph_scenarios_smoke.py
```

### 步骤 4: 验证设置

运行任何一个 smoke test，检查是否有 traces 发送到 LangSmith：

```bash
# Mortgage 示例
python experiments/single_home_graph_scenarios_smoke.py

# Ops 示例
python experiments/ops_copilot_demo.py --scenario degraded
```

### 步骤 5: 在 LangSmith UI 中查看 Traces

1. 访问 [LangSmith 控制台](https://smith.langchain.com/)
2. 在左侧菜单选择 **"Traces"** 或 **"Projects"**
3. 选择你设置的 project 名称（例如：`searchforge-mortgage`）
4. 你应该能看到：
   - **顶层 trace**：`single_home_graph_run` 或 `system_health_graph_run`
   - **嵌套的 LLM trace**：`mortgage_llm_explanation` 或 `ops_llm_explanation`

## 重要提示

- **API Key 是私密信息**：不要提交到 Git 仓库，确保 `.env` 文件在 `.gitignore` 中
- **非侵入式**：如果不设置环境变量，tracing 完全不会启用，不会有任何性能影响
- **异常安全**：即使 langsmith 包未安装或 API key 无效，也不会影响程序执行

## 故障排查

### 问题：看不到 traces 在 LangSmith UI 中

1. **检查环境变量是否设置**：
   ```bash
   echo $LANGCHAIN_TRACING_V2
   echo $LANGCHAIN_API_KEY
   ```

2. **检查 API Key 是否正确**：确保 key 以 `ls-` 开头

3. **检查项目名称**：在 LangSmith UI 中查看是否有对应的 project

4. **检查日志**：运行脚本时查看是否有 LangSmith 相关的警告或错误信息

### 问题：tracing 影响性能

如果担心性能影响，可以：
- 完全禁用：删除或注释掉环境变量
- 选择性启用：只在需要调试时临时设置环境变量

## Cloud Run 配置

如果你的应用已经部署到 Cloud Run，需要在那里也配置环境变量：

### 方式 1: 通过 Google Cloud Console（推荐）

1. 访问 [Cloud Run Console](https://console.cloud.google.com/run)
2. 找到你的服务（例如：`mortgage-agent-api`）
3. 点击服务名称进入详情页
4. 点击 **"EDIT & DEPLOY NEW REVISION"**
5. 展开 **"Variables & Secrets"** 部分
6. 在 **"Environment Variables"** 中添加：

   ```
   LANGCHAIN_TRACING_V2 = true
   LANGCHAIN_API_KEY = ls-your-service-key-here
   LANGCHAIN_PROJECT = searchforge-mortgage-prod
   ```

7. 点击 **"DEPLOY"** 部署新版本

### 方式 2: 通过 gcloud CLI

```bash
gcloud run services update YOUR_SERVICE_NAME \
  --region us-west1 \
  --update-env-vars \
    LANGCHAIN_TRACING_V2=true,\
    LANGCHAIN_API_KEY=ls-your-service-key-here,\
    LANGCHAIN_PROJECT=searchforge-mortgage-prod
```

### 在 Cloud Run 中配置（快速方式）

使用 gcloud CLI 直接设置环境变量：

```bash
# 替换 YOUR_SERVICE_NAME 为你的 Cloud Run 服务名
# 替换 YOUR_REGION 为你的 region（如 us-west1）

gcloud run services update YOUR_SERVICE_NAME \
  --region YOUR_REGION \
  --update-env-vars \
    LANGCHAIN_TRACING_V2=true,\
    LANGCHAIN_API_KEY=ls-your-api-key-here,\
    LANGCHAIN_PROJECT=searchforge-mortgage-prod
```

**示例**（如果你的服务名是 `mortgage-agent-api`，region 是 `us-west1`）：

```bash
gcloud run services update mortgage-agent-api \
  --region us-west1 \
  --update-env-vars \
    LANGCHAIN_TRACING_V2=true,\
    LANGCHAIN_API_KEY=ls-your-api-key-here,\
    LANGCHAIN_PROJECT=searchforge-mortgage-prod
```

### 使用 Secret Manager（更安全，推荐用于生产）

对于 API Key，建议使用 Google Secret Manager：

1. **创建 Secret**：
   ```bash
   echo -n "ls-your-service-key-here" | gcloud secrets create langchain-api-key \
     --data-file=- \
     --replication-policy="automatic"
   ```

2. **给 Cloud Run 服务账号权限**：
   ```bash
   PROJECT_ID=$(gcloud config get-value project)
   SERVICE_ACCOUNT="YOUR_SERVICE_ACCOUNT@${PROJECT_ID}.iam.gserviceaccount.com"
   
   gcloud secrets add-iam-policy-binding langchain-api-key \
     --member="serviceAccount:${SERVICE_ACCOUNT}" \
     --role="roles/secretmanager.secretAccessor"
   ```

3. **在 Cloud Run 中引用 Secret**：
   - 在 Console 的 "Variables & Secrets" 中
   - 点击 **"Reference a secret"**
   - Secret: `langchain-api-key`
   - Version: `latest`
   - Variable name: `LANGCHAIN_API_KEY`

### 创建 Service Key（用于生产环境）

如果是为 Cloud Run 创建，建议选择 **Service Key**：

1. 在 LangSmith 中创建 API Key 时选择 **"Service Key"**
2. 这样更适合生产环境，可以单独管理权限

## 参考链接

- [LangSmith 官方文档](https://docs.smith.langchain.com/)
- [LangSmith API Keys 管理](https://smith.langchain.com/settings)
- [Cloud Run 环境变量配置](https://cloud.google.com/run/docs/configuring/environment-variables)

