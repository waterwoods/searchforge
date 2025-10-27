# 代码查询智能体 (Code Lookup Agent)

> 一个由AI驱动的、能够分析、可视化并解释您代码库的智能体。

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

## 系统架构

采用现代化的微服务架构设计：

- **后端**: FastAPI + Python 3.8+，提供RESTful API和流式响应
- **前端**: React + Vite，现代化的单页应用界面
- **AI引擎**: OpenAI GPT-4o-mini模型，提供智能代码分析
- **可视化**: Mermaid图表库，生成交互式代码图谱
- **状态管理**: Zustand，轻量级状态管理解决方案

项目基于**Vibe Coding原则**构建，实现透明、可审计的AI智能体，确保每个分析步骤都有明确的证据支撑。

### 数据基础：离线代码图谱构建

为了实现快速、可靠的代码分析，本智能体不进行实时代码解析。所有分析都基于一份预先构建的、静态的"代码地图"，即 `codegraph.v1.json` 文件。这份"数据地基"是通过一个离线处理流程生成的：

1.  **执行构建脚本**: 我们通过运行核心脚本 `scripts/build_graphs.py` 来启动数据构建流程。
2.  **全量代码扫描**: 该脚本会递归扫描项目中的所有 `.py` 文件。
3.  **提取节点与边**:
    * **节点 (Node)**: 每个Python函数被解析为一个节点，并记录其元数据，包括函数名、文件路径，以及最重要的**证据卡 (Evidence)**——包含函数的完整代码片段及起止行号。
    * **边 (Edge)**: 脚本会分析函数间的调用关系，并将其记录为连接节点的边。
4.  **生成静态图谱**: 所有节点、边以及用于加速查询的索引，最终被序列化并写入单一的 `codegraph.v1.json` 文件中。

这个离线构建的过程，确保了智能体在运行时拥有一个稳定、一致且唯一的"事实之源"，从而保证了所有分析结果的高性能与可追溯性。

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

复制环境配置文件并设置OpenAI API密钥：

```bash
cp agent_v3.env.example .env
```

编辑 `.env` 文件，添加您的OpenAI API密钥：

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