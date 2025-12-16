# JobHunter LangSmith Tracing 配置指南

JobHunter 的三个 LangGraph Flow 都已接入 LangSmith tracing。如果设置了环境变量，所有 flow 执行都会自动发送 trace 到 LangSmith。

## 启用 Tracing

### 环境变量配置

JobHunter 的 LangSmith tracing 配置与项目中其他模块（如 mortgage、ops_copilot）保持一致，使用 `LANGCHAIN_*` 环境变量。

在 `.env` 文件或 shell 中设置以下环境变量：

```bash
# LangSmith tracing (推荐，与项目其他模块保持一致)
export LANGCHAIN_TRACING_V2="true"
export LANGCHAIN_API_KEY="YOUR_API_KEY_HERE"
export LANGCHAIN_PROJECT="searchforge-mortgage"  # 或 "jobhunter-local" 等
```

**重要提示：**
- 不要将真实的 API key 提交到代码仓库
- `LANGCHAIN_PROJECT` 用于在 LangSmith UI 中组织 traces
  - 如果 `.env` 中已有 `LANGCHAIN_PROJECT=searchforge-mortgage`（用于 mortgage 模块），JobHunter 会使用相同的 project
  - 如果想为 JobHunter 单独设置 project，可以在当前 shell 临时覆盖：`export LANGCHAIN_PROJECT=jobhunter-local`

### Using a separate LangSmith project for JobHunter

默认情况下，JobHunter 会使用 `.env` 文件中配置的 `LANGCHAIN_PROJECT`（例如 `searchforge-mortgage`），这意味着 JobHunter 的 traces 会与其他模块（如 mortgage）混在一起。

如果希望 JobHunter 的 traces 单独出现在另外一个 project，可以在运行 JobHunter 命令的终端里，先执行：

```bash
export LANGCHAIN_PROJECT=searchforge-jobhunter
```

然后再运行 `jd_explainer_cli` 或 `jd_chat_coach_cli`。

**注意：** 这个 `LANGCHAIN_PROJECT` 只是当前 shell 的覆盖，不会影响其他服务（例如 mortgage）。其他服务会继续使用 `.env` 中的配置。

### Quick start

最简单的方式是使用我们提供的一键运行脚本：

```bash
./experiments/jobhunter/run_jobhunter_with_langsmith.sh
```

这个脚本会自动设置 `LANGCHAIN_PROJECT=searchforge-jobhunter`，并将 traces 发送到 `searchforge-jobhunter` 这个 project。

如果需要指定不同的 JD 文件，可以传递参数：

```bash
./experiments/jobhunter/run_jobhunter_with_langsmith.sh path/to/your/jd.txt
```

### 向后兼容

代码也支持 `LANGSMITH_*` 变量名（优先级低于 `LANGCHAIN_*`）：

```bash
# 兼容写法（不推荐，建议使用 LANGCHAIN_*）
export LANGSMITH_API_KEY="your-api-key"
export LANGSMITH_TRACING="true"
export LANGSMITH_PROJECT="jobhunter-local"
```

### 最小配置

只需要设置这两个环境变量即可启用 tracing：

```bash
export LANGCHAIN_TRACING_V2="true"
export LANGCHAIN_API_KEY="your-api-key"
```

如果没有设置 `LANGCHAIN_PROJECT`，JobHunter 会使用默认值 `jobhunter-local`。

## 测试 Tracing

### 1. CLI 测试

#### JD 分析（Flow 1）

```bash
# 使用 .env 中的默认 project（如 searchforge-mortgage）
python -m experiments.jobhunter.jd_explainer_cli \
  --from-text-file path/to/jd.txt \
  --use-default-profile

# 或临时指定 JobHunter 专用 project
export LANGCHAIN_PROJECT=jobhunter-local
python -m experiments.jobhunter.jd_explainer_cli \
  --from-text-file path/to/jd.txt \
  --use-default-profile
```

#### JD 对话（Flow 2）

```bash
# 使用 .env 中的默认 project
python -m experiments.jobhunter.jd_chat_coach_cli \
  --jd-file path/to/jd.txt \
  --use-default-profile

# 或临时指定 JobHunter 专用 project
export LANGCHAIN_PROJECT=jobhunter-local
python -m experiments.jobhunter.jd_chat_coach_cli \
  --jd-file path/to/jd.txt \
  --use-default-profile
```

### 2. Web API 测试

如果开发服务器或 K8s 环境正在运行：

```bash
# JD 分析
curl -X POST http://localhost:8000/api/jobhunter/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "jd_input": {
      "description": "We are looking for a senior engineer...",
      "title": "Senior Software Engineer",
      "company": "Anthropic"
    },
    "use_default_profile": true
  }'

# JD 对话
curl -X POST http://localhost:8000/api/jobhunter/chat \
  -H "Content-Type: application/json" \
  -d '{
    "jd_summary": { ... },
    "messages": [
      {"role": "user", "content": "这个职位需要哪些核心技能？"}
    ],
    "use_default_profile": true
  }'
```

## 查看 Traces

1. 打开 [LangSmith UI](https://smith.langchain.com/)
2. 选择对应的 project：
   - 如果 `.env` 中设置了 `LANGCHAIN_PROJECT=searchforge-mortgage`，JobHunter 的 traces 会出现在该 project 中
   - 如果想单独查看 JobHunter 的 traces，可以在运行 CLI 前临时设置：`export LANGCHAIN_PROJECT=jobhunter-local`
3. 在 Traces 页面可以看到每次 flow 执行的完整 trace：
   - **Flow 1**: `jobhunter_jd_analysis` - JD 分析和适配度评估
   - **Flow 2**: `jobhunter_jd_chat` - 多轮对话
   - **Flow 3**: `jobhunter_preferences` - 偏好和历史经验分析

每个 trace 包含：
- 完整的 state 流转
- 每个节点的输入/输出
- LLM 调用详情（token 使用、延迟等）
- 错误信息（如果有）

## 技术实现

### 配置辅助函数

所有 tracing 配置通过 `services/fiqa_api/telemetry/langsmith_config.py` 统一管理：

- `is_langsmith_enabled()`: 检查环境变量是否启用 tracing
  - 优先检查 `LANGCHAIN_API_KEY` + `LANGCHAIN_TRACING_V2`
  - 向后兼容 `LANGSMITH_API_KEY` + `LANGSMITH_TRACING`
- `default_langsmith_run_config(flow_name)`: 生成 LangGraph config dict
  - Project 优先级：`LANGCHAIN_PROJECT` > `LANGSMITH_PROJECT` > 默认值 `jobhunter-local`

### Flow 集成

三个 flow 都已集成 tracing：

1. **Flow 1** (`jd_analysis_graph.py`): `run_jd_analysis()` 函数
2. **Flow 2** (`jd_chat_graph.py`): `run_jd_chat_turn()` 函数
3. **Flow 3** (`preferences_graph.py`): `run_preferences_analysis()` 函数

### 行为说明

- **如果环境变量未设置**：所有 flow 正常执行，不发送 trace（完全向后兼容）
- **如果环境变量已设置**：自动发送 trace 到 LangSmith，不影响业务逻辑

## 故障排查

### Tracing 没有出现

1. 检查环境变量是否正确设置：
   ```bash
   echo $LANGCHAIN_API_KEY
   echo $LANGCHAIN_TRACING_V2
   echo $LANGCHAIN_PROJECT
   ```

2. 检查 `langsmith` 包是否已安装：
   ```bash
   pip list | grep langsmith
   ```
   应该看到 `langsmith>=0.1.28`（已在 `requirements.txt` 中）

3. 检查 LangSmith API key 是否有效（可以在 LangSmith UI 中测试）

### 性能影响

- Tracing 是异步的，不会阻塞 flow 执行
- 如果 LangSmith 服务不可用，flow 仍会正常执行（不会失败）

## 相关文档

- [LangGraph Flows 文档](./notes_langgraph_flows.md)
- [LangSmith 官方文档](https://docs.smith.langchain.com/)

