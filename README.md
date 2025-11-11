# 代码查询智能体 (Code Lookup Agent)

> 一个由AI驱动的、能够分析、可视化并解释您代码库的智能体。

## Quick Start

1. `docker compose build rag-api`
2. `docker compose up -d rag-api`
3. `curl -sf http://localhost:8000/health/live && curl -sf http://localhost:8000/health/ready`
4. `make smoke`
5. `make export` *(可选，导出依赖快照到 requirements.lock)*
- 生产将 `.env` 中 `ALLOW_ALL_CORS=0`，并把 `CORS_ORIGINS` 设为逗号分隔白名单（例：`https://app.example.com,https://admin.example.com`）。

## 项目概述

代码查询智能体是一个专为开发者设计的智能代码分析工具，旨在解决理解复杂代码库的困难。通过结合AI技术和交互式可视化，它能够帮助开发者、架构师快速理解代码结构、函数关系以及系统架构。

### 目标用户
- **开发者**: 快速理解新接手的代码库
- **架构师**: 分析系统架构和模块依赖关系
- **技术负责人**: 评估代码质量和维护性
- **新团队成员**: 快速上手项目代码结构

## 核心功能

- **🔍 交互式代码图谱可视化**: 实时生成代码依赖关系图，直观展示模块间的连接
- **🤖 AI驱动的架构分析与解释**: 基于OpenAI GPT模型，提供智能的代码分析和解释
- **📊 实时"行动日志"流**: 可视化AI智能体的思考过程，展示完整的分析链路
- **📋 基于证据的分析**: 遵循Vibe Coding原则，确保分析结果的可审计性和透明度
- **⚡ 多种查询模式**: 支持概览、文件分析、函数分析等多种查询类型
- **🔄 流式响应**: 实时展示分析进度，提升用户体验

## 环境与常用命令

- `docker compose build rag-api`
- `make smoke`
- `make test`
- `make export`

## 系统架构

采用现代化的微服务架构设计：

- **后端**: FastAPI + Python 3.8+，提供RESTful API和流式响应
  - **rag-api**: CPU-only 服务（默认），使用 PyTorch CPU 构建，镜像大小 < 400MB
  - **gpu-worker**: 可选的 GPU 加速服务（需显式启用），用于 CUDA 加速的嵌入和重排序
- **前端**: React + Vite，现代化的单页应用界面
- **AI引擎**: OpenAI GPT-4o-mini模型，提供智能代码分析
- **可视化**: Mermaid图表库，生成交互式代码图谱
- **状态管理**: Zustand，轻量级状态管理解决方案

**注意**: rag-api 服务默认使用 CPU-only 模式，无需 GPU。如需 GPU 加速的嵌入和重排序功能，可使用可选的 `gpu-worker` 服务（通过 `make up-gpu` 启用）。

项目基于**Vibe Coding原则**构建，实现透明、可审计的AI智能体，确保每个分析步骤都有明确的证据支撑。

## Agent 工作流程

CodeLookup Agent 采用管道式架构，将用户查询通过多个专业组件进行处理，确保分析结果的准确性和可追溯性。

### 完整流程图

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           CodeLookup Agent 架构流程                              │
└─────────────────────────────────────────────────────────────────────────────────┘

📥 用户输入查询
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           1. Router (路由器)                                    │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ 输入: "#func services.fiqa_api.execute_query"                           │   │
│  │ 处理: 解析查询类型和参数                                                  │   │
│  │ 输出: {"type": "function", "target": "services.fiqa_api.execute_query"} │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           2. Planner (计划生成器)                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ 输入: 结构化查询                                                         │   │
│  │ 处理: 创建执行计划                                                       │   │
│  │ 输出: {                                                               │   │
│  │   "goal": "Explain function execute_query and its neighbors",         │   │
│  │   "steps": [                                                          │   │
│  │     {"tool": "codegraph.get_node_by_fqname", "args": {...}},          │   │
│  │     {"tool": "codegraph.get_neighbors", "args": {...}}                │   │
│  │   ]                                                                   │   │
│  │ }                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           3. Executor (执行引擎)                                │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ 步骤1: codegraph.get_node_by_fqname("services.fiqa_api.execute_query")  │   │
│  │         ↓ 返回函数节点数据                                               │   │
│  │ 步骤2: codegraph.get_neighbors(node_id, max_hops=1)                    │   │
│  │         ↓ 返回邻居节点和边                                               │   │
│  │ 输出: 执行结果 + 节点和边数据                                            │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           4. Judge (结果验证器)                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ 输入: 执行结果                                                           │   │
│  │ 验证: 检查证据完整性 (file, span, snippet)                               │   │
│  │ 输出: {"verdict": "pass", "issues": []} 或 {"verdict": "revise", ...}   │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           5. Explainer (解释生成器)                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ 输入: 验证通过的结果                                                     │   │
│  │ 处理: 调用 OpenAI API 生成分析                                          │   │
│  │ 输出: Markdown 格式的架构分析和解释                                      │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           6. 最终响应                                            │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ {                                                                     │   │
│  │   "success": true,                                                    │   │
│  │   "data": {节点和边数据},                                              │   │
│  │   "explanation": "Markdown 分析",                                      │   │
│  │   "trace": {计划 + 验证结果}                                           │   │
│  │ }                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
    │
    ▼
📤 返回给前端显示
```

### 核心组件说明

#### 🔀 **Router (路由器)**
- **职责**: 解析用户查询，识别查询类型和参数
- **输入**: 原始查询字符串 (`#func`, `#file`, `#overview` 或自然语言)
- **输出**: 结构化查询对象
- **特性**: 支持标签查询和自然语言查询

#### 📋 **Planner (计划生成器)**
- **职责**: 根据查询类型创建详细的执行计划
- **功能**: 
  - 函数分析: 获取目标函数 + 邻居节点
  - 文件分析: 获取文件内所有函数
  - 概览分析: 获取图谱统计信息
- **输出**: 包含目标、步骤和停止条件的执行计划

#### ⚙️ **Executor (执行引擎)**
- **职责**: 按计划执行具体的工具调用
- **工具**: 
  - `codegraph.get_node_by_fqname()` - O(1) 节点查找
  - `codegraph.get_neighbors()` - BFS 邻居遍历
  - `codegraph.get_nodes_by_file()` - 文件节点获取
  - `codegraph.get_graph_stats()` - 图谱统计
- **特性**: 支持步骤间依赖解析

#### ⚖️ **Judge (结果验证器)**
- **职责**: 验证执行结果的证据完整性
- **验证规则**:
  - `file`: 文件路径 (字符串)
  - `span`: 行号范围 `{start: int, end: int}`
  - `snippet`: 代码片段 (字符串)
- **输出**: `pass` 或 `revise` 验证结果

#### 🤖 **Explainer (解释生成器)**
- **职责**: 使用 LLM 生成人类可读的架构分析
- **分析维度**:
  - 架构概览 - 高层设计模式
  - 关键组件 - 重要模块和类
  - 入口点和流程 - 主要执行路径
  - 依赖关系 - 组件间连接
  - 架构模式 - 设计模式识别
  - 复杂度评估 - 代码质量分析
  - 风险分析 - 潜在问题识别
  - 改进建议 - 重构建议

### 数据流向

```
静态数据源 (codegraph.v1.json)
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CodeGraph 工具层                             │
│ • 快速节点查找 (O(1))                                           │
│ • 邻居遍历 (BFS)                                                │
│ • 文件节点获取                                                   │
│ • 图谱统计                                                       │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Agent 处理管道                               │
│ Router → Planner → Executor → Judge → Explainer                │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    前端可视化                                   │
│ • Mermaid 图表渲染                                              │
│ • 节点详情展示                                                   │
│ • AI 分析结果                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 数据基础：离线代码图谱构建

为了实现快速、可靠的代码分析，本智能体不进行实时代码解析。所有分析都基于一份预先构建的、静态的"代码地图"，即 `codegraph.v1.json` 文件。这份"数据地基"是通过一个离线处理流程生成的：

1.  **执行构建脚本**: 我们通过运行核心脚本 `scripts/build_graphs.py` 来启动数据构建流程。
2.  **全量代码扫描**: 该脚本会递归扫描项目中的所有 `.py` 文件。
3.  **提取节点与边**:
    * **节点 (Node)**: 每个Python函数被解析为一个节点，并记录其元数据，包括函数名、文件路径，以及最重要的**证据卡 (Evidence)**——包含函数的完整代码片段及起止行号。
    * **边 (Edge)**: 脚本会分析函数间的调用关系，并将其记录为连接节点的边。
4.  **生成静态图谱**: 所有节点、边以及用于加速查询的索引，最终被序列化并写入单一的 `codegraph.v1.json` 文件中。

这个离线构建的过程，确保了智能体在运行时拥有一个稳定、一致且唯一的"事实之源"，从而保证了所有分析结果的高性能与可追溯性。

### 增量更新代码图谱

当项目代码发生变化时，需要更新 `codegraph.v1.json` 文件以反映最新的代码结构。系统支持增量更新，只处理修改过的文件，提高构建效率。

#### 增量更新流程

```bash
# 1. 添加新文件或修改现有文件
# 2. 运行增量构建
python scripts/build_graphs.py . codegraph.v1.json --incremental

# 3. 重启服务（如果需要）
./scripts/start-agent.sh
```

#### 增量更新特性

- **智能检测**: 自动检测文件修改时间，只处理变更的文件
- **节点清理**: 删除修改文件的所有旧节点和相关边
- **索引重建**: 自动更新 `byFqName` 和 `byFilePath` 索引
- **ID连续性**: 保持节点ID计数器的连续性

#### 完全重建

如果增量更新出现问题，可以执行完全重建：

```bash
# 完全重新构建（不使用增量模式）
python scripts/build_graphs.py . codegraph.v1.json
```

#### 验证更新

更新完成后，可以验证图谱是否包含新的函数：

```bash
# 检查特定函数是否存在
grep -i "function_name" codegraph.v1.json

# 查看图谱统计
python -c "
import json
with open('codegraph.v1.json', 'r') as f:
    data = json.load(f)
print(f'Nodes: {len(data[\"nodes\"])}')
print(f'Edges: {len(data[\"edges\"])}')
print(f'Files: {len(data[\"indices\"][\"byFilePath\"])}')
"
```

## 快速上手

### 环境要求

- **Python**: 3.8 或更高版本
- **Node.js**: 16.0 或更高版本
- **包管理器**: npm、yarn 或 pnpm（推荐）

### 1. 克隆项目

```bash
git clone <repository-url>
cd searchforge
```

### 2. 后端设置

#### 安装Python依赖

```bash
pip install -r requirements.txt
```

#### 配置环境变量

**重要：`.env.current` 是服务端点的单一来源**

SearchForge 使用 `.env.current` 作为当前活跃的环境配置文件，这是所有服务端点的单一来源。所有 Docker Compose 命令都会自动加载 `.env.current`。

> Docker 提示：运行容器时若需自定义运行/产物目录，设置 `RUNS_DIR` 与 `ARTIFACTS_DIR` 环境变量并挂载对应路径即可；镜像不再依赖固定的 `/app`。

**环境配置文件说明：**

- `.env.local` - 本地开发环境配置（使用 `localhost` 作为服务地址）
- `.env.remote.template` - 远程环境配置模板（使用 `andy-wsl` 主机名）
- `.env.current` - **当前活跃配置**（由切换脚本自动管理，不应手动编辑）

**切换环境：**

```bash
# 切换到远程环境（带 SLA 检查和自动回滚）
make cutover-remote

# 手动切换到远程环境（无 SLA 检查）
bash tools/switch/switch_to_remote.sh

# 回滚到本地环境
bash tools/switch/rollback_to_local.sh

# 查看当前目标
make whoami
```

**SLA Gate 和自动回滚：**

SearchForge 提供了带 SLA（Service Level Agreement）检查的安全切换机制，确保切换到远程环境后性能不会显著下降。

**SLA 标准：**
- **P95 延迟**：不超过基线值的 110%（允许 10% 的性能降级），即 `p95 ≤ baseline*1.10`
- **错误率**：不超过 1%，即 `error_rate ≤ 0.01`

**Smoke 测试特性：**
- **预热机制**：默认排除前 10 个请求（warmup）以确保稳定的指标
- **严格超时**：每个请求的超时时间可配置（默认 3 秒），超时和异常都被视为错误
- **错误计数**：所有非 2xx 状态码、超时和异常都被计为错误

**使用方法：**

1. **创建基线（首次使用前）：**
   ```bash
   # 为本地环境创建基线
   make baseline-save-local
   
   # 为远程环境创建基线
   make baseline-save-remote
   
   # 或根据当前目标自动选择（本地或远程）
   make baseline-save
   ```
   这些命令会运行 200 个请求（并发 10，预热 20，超时 3 秒）并保存性能基线：
   - 本地基线：`artifacts/sla/baseline.local.json`
   - 远程基线：`artifacts/sla/baseline.remote.json`

2. **执行安全切换：**
   ```bash
   # 使用默认参数（N=150, C=10, WARMUP=10, TIMEOUT=3）
   make cutover-remote
   
   # 或自定义参数
   N=150 C=10 WARMUP=10 TIMEOUT=3 make cutover-remote
   ```
   这个过程会：
   - 刷新主机名映射（确保远程主机名可解析）
   - 冻结本地写入服务
   - 验证远程服务健康状态
   - 切换到远程配置并停止本地容器
   - 运行 smoke 测试（默认 150 个请求，并发 10，预热 10，超时 3 秒）
   - 根据目标环境选择对应的基线进行比较（远程使用 `baseline.remote.json`，本地使用 `baseline.local.json`）
   - 如果基线不存在，自动创建（bootstrap 模式）
   - 如果 SLA 检查失败，自动回滚到本地环境

3. **更新基线（当性能改善后）：**
   ```bash
   # 重新运行基线测试以更新基准
   make baseline-save-local    # 更新本地基线
   make baseline-save-remote   # 更新远程基线
   ```

**SLA 检查失败时的行为：**

如果 P95 延迟超过基线 110% 或错误率超过 1%，系统会：
- 自动回滚到本地配置（通过 trap 机制确保原子性）
- 启动本地容器
- 调用 `rollback_to_local.sh` 脚本确保本地服务健康
- 记录失败原因到 manifest 文件（`artifacts/sla/manifests/<timestamp>.json`）
- 退出码为 1

**Manifest 文件：**

每次 cutover 操作都会生成一个 manifest 文件，包含：
- 时间戳和 ISO 时间戳
- Git SHA
- 目标环境（target）
- 基线文件名（baseline_name）
- 测试结果（PASS/ROLLBACK）
- 测试参数（N, C, WARMUP, TIMEOUT）
- 性能指标（P50, P95, 平均延迟，错误率）
- 完整 metrics 对象
- 基线数据（如果存在）
- 失败原因（如果回滚）

所有 manifest 文件保存在 `artifacts/sla/manifests/` 目录中，可用于追踪和分析切换历史。

**配置远程主机名：**

如果 MagicDNS 未启用，需要将远程主机名添加到 `/etc/hosts`：

```bash
# 添加以下行到 /etc/hosts
# 格式: <IP地址>  <主机名>
100.67.88.114  andy-wsl
```

## Ops Checklist

- **Environment notes**
  - `/etc/hosts` keeps `andy-wsl` → current IP (presently `100.67.88.114`) as a fallback when Tailscale is unavailable.
  - `/etc/wsl.conf` must contain:

    ```
    [boot]
    systemd=true
    ```

    After editing run `wsl.exe --shutdown` in Windows PowerShell and re-open the distro.
  - After any WSL reset, re-run `sudo systemctl enable --now ssh` and `sudo tailscale up --ssh --hostname=andy-wsl` on the remote to restore services.
- Bootstrap SSH by running `scripts/setup_ssh_client.sh` locally, `scripts/setup_ssh_server.sh` remotely, and confirm with `scripts/verify_ssh.sh`.
- Optional hardening: enable Tailscale SSH via `scripts/setup_tailscale_ssh.sh` and pin the host fingerprint (`ssh-keyscan -H andy-wsl >> ~/.ssh/known_hosts`).

**手动配置：**

复制环境配置文件并设置OpenAI API密钥：

```bash
cp agent_v3.env.example .env.local
cp .env.local .env.current  # 初始化 .env.current
```

编辑 `.env.current` 文件，添加您的OpenAI API密钥：

```bash
# OpenAI API配置
OPENAI_API_KEY=sk-your-api-key-here

# 可选：指定模型（默认：gpt-4o-mini）
LLM_MODEL=gpt-4o-mini

# 可选：设置超时时间（默认：8.0秒）
LLM_TIMEOUT=8.0
```

**注意**: 如果没有API密钥，系统会自动降级为基于规则的代码分析模式，仍可正常使用。

### 3. 前端设置

```bash
cd code-lookup-frontend
npm install  # 或使用 yarn/pnpm
```

### 4. 运行应用

使用提供的启动脚本一键启动前后端服务：

```bash
# 在项目根目录执行
./scripts/start-agent.sh
```

启动脚本会自动：
- 启动后端服务（端口8001）
- 启动前端服务（端口5173）
- 处理端口冲突
- 显示服务状态和访问地址

### 5. 访问应用

打开浏览器访问：http://localhost:5173

## 使用方法

### 查询语法

代码查询智能体支持多种查询方式：

#### 1. 概览查询
```bash
#overview
# 或使用自然语言
"show me an overview of the repository"
"what is this codebase about"
```

#### 2. 文件分析
```bash
#file src/api/routes.py
# 或使用自然语言
"analyze the file at services/main.py"
"examine the code at src/utils.py"
```

#### 3. 函数分析
```bash
#func my_app.utils.clean_data
# 或使用自然语言
"analyze the function process_data"
"examine the method validate_input"
```

### 功能特性

- **智能路由**: 自动识别查询类型并分发给相应的处理模块
- **计划生成**: AI智能体制定分析计划，确保分析的完整性
- **执行引擎**: 基于代码图谱执行具体的分析任务
- **结果验证**: 通过Judge模块验证分析结果的准确性和完整性
- **解释生成**: 使用LLM生成人类可读的分析解释

### 实时监控

应用提供完整的执行跟踪功能：
- **步骤可视化**: 实时显示AI智能体的执行步骤
- **成本监控**: 显示API调用成本和token使用情况
- **错误处理**: 智能错误恢复和降级机制

## API接口

### 主要端点

- `POST /v1/query`: 执行代码分析查询
- `GET /v1/stream`: 流式查询执行（实时事件）
- `GET /v1/supported-queries`: 获取支持的查询类型
- `GET /health`: 健康检查

### 示例请求

```bash
curl -X POST "http://localhost:8001/v1/query" \
     -H "Content-Type: application/json" \
     -d '{"query": "#overview"}'
```

## 项目结构

```
searchforge/
├── services/fiqa_api/          # 后端API服务
│   ├── agent/                 # AI智能体组件
│   │   ├── router.py         # 查询路由器
│   │   ├── planner.py        # 计划生成器
│   │   ├── executor.py       # 执行引擎
│   │   ├── judge.py          # 结果验证器
│   │   └── explainer.py      # 解释生成器
│   ├── tools/                # 工具模块
│   └── main.py               # FastAPI应用入口
├── code-lookup-frontend/      # 前端React应用
│   ├── src/
│   │   ├── components/       # React组件
│   │   └── App.jsx          # 主应用组件
│   └── package.json         # 前端依赖配置
├── scripts/
│   └── start-agent.sh       # 启动脚本
├── codegraph.v1.json       # 代码图谱数据
└── requirements.txt         # Python依赖
```

## 未来规划

### 短期目标
- **多语言支持**: 扩展对TypeScript、Go、Java等语言的支持
- **性能优化**: 优化大代码库的分析性能
- **UI增强**: 改进可视化界面和交互体验

### 中期目标
- **CI/CD集成**: 与GitHub Actions、GitLab CI等集成
- **团队协作**: 支持多用户协作和分享功能
- **插件系统**: 支持自定义分析插件

### 长期愿景
- **企业级部署**: 支持私有化部署和权限管理
- **智能建议**: 基于代码分析提供重构建议
- **学习模式**: 从用户行为中学习，提供个性化分析

## 仓库清理 (Repository Cleanup)

项目提供了安全的、可回滚的清理工具，用于归档未使用的脚本、测试和文档，同时保持运行时路径完整。

### 白名单（必须保留）
- **代码**: `services/`, `ui/`, `core/`, `configs/`
- **运维**: `docker-compose*.yml`, `Makefile`, `tools/switch/`, `migration_*.sh`
- **文档**: `README.md`（保留）；其他文档可归档

### 使用方法

#### 1. 审计（Dry-Run）
```bash
make cleanup-audit
```
这会生成 `artifacts/cleanup/candidates.txt`，列出可归档的文件，**不会修改任何文件**。

#### 2. 应用清理
```bash
make cleanup-apply
```
将候选文件移动到 `archive/` 目录（使用 `git mv`，可回滚）。会显示清理前后的仓库大小。

#### 3. 恢复归档
```bash
make cleanup-restore
```
将 `archive/` 中的文件恢复到原始位置。

### 安全保证
- ✅ 使用 `git mv` 而非删除（可回滚）
- ✅ 永远不会触及白名单中的文件
- ✅ 不会破坏 `docker compose up`、`make restart`、`make ui`
- ✅ `archive/` 目录被 `.gitignore` 忽略

### 工作原理
清理工具会识别：
- 未在 `Makefile`、`tools/**/*.sh`、`docker-compose*.yml` 中引用的 `.sh` 脚本
- 大型测试和文档文件（`tests/`、`.md` 文件）

这些文件会被移动到 `archive/` 目录，保留目录结构，可通过 `make cleanup-restore` 完全恢复。

### 清理 Git 历史（高级操作）

⚠️ **警告**: 此操作会重写 Git 历史，不可逆！

如果 Git 历史中包含大型文件（如 `artifacts/`, `mlruns/`, `qdrant_storage/`, `*.ipynb`, `*.rdb`, `*.snapshot`），可以使用 `git-filter-repo` 从历史中移除它们：

```bash
# 需要明确确认
I_KNOW_WHAT_IM_DOING=1 make cleanup-history
```

此操作将：
1. 创建备份标签 `pre-slim-YYYYMMDD`
2. 从 Git 历史中移除指定路径
3. 运行 `git gc` 清理仓库
4. 显示清理前后的仓库大小对比

#### 清理后的操作

**1. 验证更改**
```bash
git log --all --oneline | head -10
docker compose build  # 确保构建仍然正常
```

**2. Force-Push 到远程（危险操作）**
```bash
# ⚠️ 这会重写远程历史，所有协作者必须重新克隆
git push origin --force --all
git push origin --force --tags
```

**3. 通知所有协作者重新克隆**
所有协作者必须：
```bash
# 1. 备份当前工作
git stash  # 或提交到临时分支

# 2. 删除本地仓库
cd ..
rm -rf searchforge

# 3. 重新克隆
git clone <repository-url> searchforge
cd searchforge

# 4. 恢复工作（如果有）
git stash pop  # 或合并临时分支
```

⚠️ **重要提示**:
- 此操作会影响所有协作者
- 必须提前通知团队
- 确保所有重要工作已提交/备份
- 备份标签可用于恢复（如果需要）

### 创建干净的仓库快照（无历史）

如果需要创建一个全新的干净仓库（不包含 Git 历史），可以使用：

```bash
# 需要提供新仓库 URL
NEW_REPO_URL=https://github.com/user/repo.git make create-clean-repo
```

此操作将：
1. 创建 `../searchforge-clean` 目录（排除大文件和生成文件）
2. 初始化新的 Git 仓库并推送到新远程
3. 切换服务器（andy-wsl）到新远程
4. 构建并启动服务
5. 执行健康检查

**排除的内容**:
- `.git`, `.venv`, `node_modules`, `__pycache__`
- `artifacts/`, `mlruns/`, `qdrant_storage/`
- `*.rdb`, `*.snapshot`, `dist/`, `.vite`
- 其他临时文件和缓存

**验收标准**:
- 干净仓库大小 ≤ 300-400 MB
- 健康检查通过（HTTP 200）
- Docker 构建成功（≤ 2 分钟）
- 旧仓库保持不变（未修改）

**回滚方法**:
如果需要回滚到旧仓库：
```bash
ssh andy-wsl 'cd ~/searchforge && \
  git remote set-url origin <OLD_REPO_URL> && \
  git fetch && \
  git reset --hard origin/<old-branch> && \
  docker compose up -d'
```

## 贡献指南

我们欢迎社区贡献！请查看以下资源：

- 提交Issue报告问题或建议功能
- Fork项目并提交Pull Request
- 遵循项目的代码规范和测试要求

## 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 支持

如果您在使用过程中遇到问题，请：

1. 查看本文档的快速上手部分
2. 检查环境配置是否正确
3. 查看项目的Issue页面
4. 提交新的Issue描述您的问题

---

**代码查询智能体** - 让代码理解变得简单而智能 🚀