# SearchForge 仓库结构勘察报告

> **报告类型**: 代码库结构分析（非重构建议）  
> **生成时间**: 2025-01-XX  
> **范围**: 全仓库扫描

---

## 1️⃣ 高层结构（High-level Structure）

### 顶层目录与文件

| 目录/文件 | 用途说明 |
|----------|---------|
| `services/` | 核心服务层：包含 RAG API、检索代理、GPU Worker 等微服务实现 |
| `modules/` | 功能模块：AutoTuner、RAG、路由、评估等可复用组件 |
| `agents/` | AI 智能体：LabOps 运维智能体、编排器等 |
| `ui/` | 前端应用：React + Vite，包含查询控制台、指标面板、JobHunter 等页面 |
| `engines/` | 向量引擎：支持 Milvus、NetworkX 等后端 |
| `pipeline/` | RAG 管道：查询改写、检索、重排序等流程编排 |
| `eval/` | 评估框架：A/B 测试、成对评估、指标分析 |
| `infra/` | 基础设施：Prometheus、Grafana 监控配置 |
| `scripts/` | 工具脚本：构建、测试、部署、数据准备等 |
| `configs/` | 配置文件：控制策略、路由规则等 YAML 配置 |
| `experiments/` | 实验目录：JobHunter、健康检查等专项实验 |
| `docs/` | 文档：架构说明、实现总结、使用指南 |
| `tests/` | 测试套件：单元测试、集成测试 |
| `clients/` | 客户端库：检索代理客户端等 |
| `tools/` | 工具集：环境切换、清理等运维工具 |
| `docker/` | Docker 配置：基础镜像、多阶段构建 |
| `k8s/` | Kubernetes：部署清单、Playbook |
| `mcp/` | MCP 服务器：Mortgage Programs 等 |
| `knowledge_base/` | 知识库：电商 FAQ、运维手册等 |
| `data/` | 数据目录：数据集、索引文件 |
| `artifacts/` | 产物目录：实验报告、图表、基线数据 |
| `.runs/` | 运行时目录：日志、状态文件、追踪数据 |
| `Makefile` | 构建与运维：一键命令、CI/CD 流程 |
| `docker-compose.yml` | 服务编排：Qdrant、Redis、Milvus、RAG API 等 |
| `pyproject.toml` | Python 项目配置：依赖、测试、代码质量工具 |
| `README.md` | 项目文档：快速开始、架构说明、使用指南 |

---

## 2️⃣ 功能模块（Functional Modules）

### 2.1 RAG（检索增强生成）

**状态**: ✅ **已实现**

**功能**:
- 向量检索（Qdrant/Milvus）
- 查询改写（Query Rewriter）
- 重排序（Reranker）
- PageIndex 分层检索
- CAG 缓存（查询结果缓存）

**入口文件**:
- `pipeline/rag_pipeline.py` - RAG 管道主实现
- `modules/rag/page_index.py` - 分层索引
- `modules/rag/cache.py` - 缓存实现
- `services/fiqa_api/search_core.py` - 搜索核心逻辑

**实现细节**:
- 支持同步/异步查询改写
- 支持混合检索（向量 + BM25）
- 支持 GPU Worker 加速（可选）

---

### 2.2 AutoTuner（自动调参）

**状态**: ✅ **已实现**

**功能**:
- 基于性能指标的参数自动调整
- 多参数联合决策（ef、T、Ncand_max、rerank_mult）
- 记忆系统（甜点发现、EWMA）
- 约束验证（参数范围、滞回带）
- 防震荡机制（冷却期、自适应步长）

**入口文件**:
- `modules/autotuner/brain/` - 核心决策逻辑
- `services/autotuner_router.py` - API 路由
- `services/fiqa_api/autotuner_global.py` - 全局调优器

**实现细节**:
- 纯函数设计（零 I/O、零网络）
- 完整单元测试覆盖（98 个用例）
- 支持策略切换（LatencyFirst、RecallFirst、Balanced）

---

### 2.3 检索代理（Retrieval Proxy）

**状态**: ✅ **已实现**

**功能**:
- Go 语言实现的高性能代理
- 请求路由与负载均衡
- 超时与预算控制
- 缓存管理

**入口文件**:
- `services/retrieval_proxy/` - Go 代理实现
- `bin/retrieval-proxy` - 编译产物
- `clients/retrieval_proxy_client.py` - Python 客户端

**实现细节**:
- 端口：7070
- 支持并发控制
- 与 RAG API 集成

---

### 2.4 GPU Worker（GPU 加速服务）

**状态**: ✅ **已实现**

**功能**:
- CUDA 加速的嵌入生成
- 重排序模型推理
- 微批处理
- 并发控制

**入口文件**:
- `services/gpu_worker/main.py` - FastAPI 服务
- `services/fiqa_api/gpu_worker_client.py` - 客户端

**实现细节**:
- 端口：8090
- 支持优雅降级（GPU 不可用时回退 CPU）
- 健康检查端点：`/healthz`, `/ready`, `/meta`

---

### 2.5 LabOps Agent（运维智能体）

**状态**: 🟡 **部分实现**

**功能**:
- 代码库分析
- 运维决策建议
- LLM 驱动的解释生成

**入口文件**:
- `agents/labops/v3/runner_v3.py` - V3 运行器
- `agents/labops/v3/explainers/explainer_llm.py` - LLM 解释器
- `agents/labops/tools/ops_client.py` - 运维客户端

**实现细节**:
- 支持离线降级（LLM 不可用时使用规则解释）
- 缓存机制（≤1 MB）
- 日志记录（≤200 条）

---

### 2.6 Code Lookup Agent（代码查询智能体）

**状态**: ✅ **已实现**

**功能**:
- 代码图谱构建（离线）
- 函数/文件/概览查询
- Mermaid 图表生成
- AI 架构分析

**入口文件**:
- `services/fiqa_api/agent/` - Agent 组件（Router、Planner、Executor、Judge、Explainer）
- `services/fiqa_api/services/code_lookup_service.py` - 服务层
- `scripts/build_graphs.py` - 图谱构建脚本

**实现细节**:
- 基于静态代码图谱（`codegraph.v1.json`）
- 支持增量更新
- 支持流式响应

---

### 2.7 JobHunter（求职助手）

**状态**: 🟡 **部分实现**

**功能**:
- JD（职位描述）分析
- 简历匹配
- LangGraph 工作流

**入口文件**:
- `services/fiqa_api/jobhunter/` - JobHunter 模块
- `ui/src/pages/JobHunterPage.tsx` - 前端页面

**实现细节**:
- 使用 LangGraph 构建工作流
- 集成 LangSmith 追踪

---

### 2.8 E-commerce Agent（电商售后智能体）

**状态**: 🟡 **部分实现**

**功能**:
- 自然语言到意图转换
- RAG 检索
- 响应生成

**入口文件**:
- `services/fiqa_api/ecommerce/` - 电商模块
- `knowledge_base/ecommerce/` - 知识库

---

### 2.9 Control（流量控制）

**状态**: ✅ **已实现**

**功能**:
- 流量整形（Flow Shaping）
- 执行器（批量大小、并发度）
- 策略管理

**入口文件**:
- `modules/control/` - 控制模块
- `services/plugins/control/` - 插件实现

---

### 2.10 Routing（路由）

**状态**: ✅ **已实现**

**功能**:
- 智能路由（Qdrant/Milvus/FAISS）
- 成本感知路由
- 规则引擎

**入口文件**:
- `modules/routing/` - 路由模块
- `services/plugins/routing/` - 插件实现

---

### 2.11 Canary（金丝雀部署）

**状态**: ✅ **已实现**

**功能**:
- A/B 测试框架
- SLO 监控
- 报告生成

**入口文件**:
- `modules/canary/` - Canary 模块

---

### 2.12 Evaluation（评估框架）

**状态**: ✅ **已实现**

**功能**:
- A/B 评估器
- 成对评估
- 指标分析
- 报告生成

**入口文件**:
- `modules/evaluation/` - 评估模块
- `eval/` - 评估脚本

---

### 2.13 Black Swan（黑天鹅测试）

**状态**: ✅ **已实现**

**功能**:
- 压力测试
- 混沌注入
- 报告生成

**入口文件**:
- `services/black_swan/` - Black Swan 模块

---

### 2.14 Prompt Lab（提示词实验室）

**状态**: ✅ **已实现**

**功能**:
- 查询改写
- 多 Provider 支持（OpenAI、Mock）
- 合约验证

**入口文件**:
- `modules/prompt_lab/` - Prompt Lab 模块

---

## 3️⃣ 数据流（Data Flow）

### 3.1 RAG 查询流程

```
用户查询 (Query)
    ↓
[可选] 查询改写 (Query Rewriter)
    ├─ 缓存检查 (CAG Cache)
    ├─ LLM 改写 (OpenAI/Mock)
    └─ 异步/同步模式
    ↓
[可选] PageIndex 分层检索
    ├─ 章节级检索
    └─ 段落级检索
    ↓
向量检索 (Qdrant/Milvus/FAISS)
    ├─ 嵌入生成 (SBERT/GPU Worker)
    ├─ 向量搜索
    └─ [可选] BM25 混合检索
    ↓
[可选] 重排序 (Reranker)
    ├─ GPU Worker (CUDA)
    └─ CPU Fallback
    ↓
结果返回 (Results + Metadata)
```

### 3.2 AutoTuner 调优流程

```
性能指标采集 (Metrics)
    ├─ P95 延迟
    ├─ Recall@10
    ├─ QPS
    └─ 成本
    ↓
决策引擎 (Decider)
    ├─ 约束验证
    ├─ 记忆查询（甜点）
    └─ 动作生成
    ↓
参数应用 (Apply)
    ├─ 范围裁剪
    └─ 滞回检查
    ↓
配置更新 (Config Update)
    ↓
下一轮采集 (Next Iteration)
```

### 3.3 Code Lookup Agent 流程

```
用户查询 (#func / #file / #overview)
    ↓
Router（路由解析）
    ↓
Planner（计划生成）
    ↓
Executor（执行工具调用）
    ├─ codegraph.get_node_by_fqname()
    ├─ codegraph.get_neighbors()
    └─ codegraph.get_graph_stats()
    ↓
Judge（结果验证）
    ├─ 证据完整性检查
    └─ 验证通过/修订
    ↓
Explainer（解释生成）
    ├─ LLM 分析（OpenAI）
    └─ Markdown 输出
    ↓
前端可视化（Mermaid 图表）
```

### 3.4 存储与持久化

```
向量数据 → Qdrant（持久化到磁盘）
    └─ 集合：fiqa, airbnb_la_demo 等

缓存数据 → Redis（可选）
    ├─ 查询结果缓存
    └─ Black Swan 状态

实验数据 → 文件系统
    ├─ .runs/（运行时数据）
    ├─ artifacts/（实验报告）
    └─ baselines/（基线数据）

代码图谱 → codegraph.v1.json（静态文件）
```

---

## 4️⃣ Agent / AI 相关组件

### 4.1 LLM 调用

| 组件 | 模型 | 用途 | 状态 |
|------|------|------|------|
| Code Lookup Explainer | gpt-4o-mini | 代码架构分析 | ✅ 已集成 |
| LabOps Agent V3 | gpt-4o-mini | 运维决策解释 | ✅ 已集成 |
| Query Rewriter | gpt-4o-mini | 查询改写 | ✅ 已集成 |
| JobHunter JD Analyzer | gpt-4o-mini | JD 分析 | ✅ 已集成 |
| E-commerce Intent | gpt-4o-mini | 意图识别 | ✅ 已集成 |

**配置**:
- 环境变量：`OPENAI_API_KEY`
- 超时：`OPENAI_TIMEOUT_MS`（默认 60000ms）
- 支持 Azure OpenAI（`AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`）

---

### 4.2 嵌入模型（Embeddings）

| 组件 | 模型 | 后端 | 状态 |
|------|------|------|------|
| 向量检索 | sentence-transformers/all-MiniLM-L6-v2 | SBERT/GPU Worker | ✅ 已集成 |
| 语义缓存 | sentence-transformers/all-MiniLM-L6-v2 | SBERT | ✅ 已集成 |

**配置**:
- 环境变量：`EMBEDDING_BACKEND`（SBERT/FASTEMBED）
- GPU Worker：`WORKER_URLS=http://gpu-worker:8090`

---

### 4.3 重排序模型（Reranker）

| 组件 | 模型 | 后端 | 状态 |
|------|------|------|------|
| 重排序 | cross-encoder/ms-marco-MiniLM-L-12-v2 | GPU Worker | ✅ 已集成 |

---

### 4.4 检索器（Retrievers）

| 组件 | 类型 | 状态 |
|------|------|------|
| 向量检索 | Qdrant/Milvus/FAISS | ✅ 已实现 |
| BM25 检索 | BM25Okapi | ✅ 已实现 |
| 混合检索 | RRF Fusion | ✅ 已实现 |

---

### 4.5 RAG 组件

| 组件 | 功能 | 状态 |
|------|------|------|
| PageIndex | 分层检索（章节+段落） | ✅ 已实现 |
| CAG Cache | 查询结果缓存 | ✅ 已实现 |
| Query Rewriter | 查询改写 | ✅ 已实现 |

---

## 5️⃣ 基础设施与外部依赖

### 5.1 云服务

| 服务 | 用途 | 状态 |
|------|------|------|
| OpenAI API | LLM 调用 | ✅ 已集成 |
| Azure OpenAI | LLM 调用（可选） | ✅ 已集成 |
| LangSmith | 追踪与监控 | ✅ 已集成（可选） |
| Langfuse | 追踪与监控 | ✅ 已集成（可选） |

---

### 5.2 向量数据库

| 数据库 | 用途 | 端口 | 状态 |
|--------|------|------|------|
| Qdrant | 主向量数据库 | 6333/6334 | ✅ 已部署 |
| Milvus | 备选向量数据库 | 19530 | ✅ 已部署（可选） |
| FAISS | 内存向量索引 | N/A | ✅ 已实现（可选） |

**配置**:
- Qdrant：`QDRANT_HOST`, `QDRANT_PORT`
- Milvus：`MILVUS_HOST`, `MILVUS_PORT`

---

### 5.3 数据库与消息队列

| 组件 | 用途 | 端口 | 状态 |
|------|------|------|------|
| Redis | 缓存、状态存储 | 6379 | ✅ 已部署 |
| SQLite | LangGraph Checkpoint | N/A | ✅ 已集成 |

**配置**:
- Redis：`REDIS_HOST`, `REDIS_PORT`
- SQLite：自动创建（LangGraph）

---

### 5.4 环境变量与密钥

#### 必需环境变量

| 变量名 | 用途 | 示例 |
|--------|------|------|
| `OPENAI_API_KEY` | OpenAI API 密钥 | `sk-...` |
| `QDRANT_HOST` | Qdrant 主机 | `localhost` |
| `QDRANT_PORT` | Qdrant 端口 | `6333` |

#### 可选环境变量

| 变量名 | 用途 | 默认值 |
|--------|------|--------|
| `EMBEDDING_BACKEND` | 嵌入后端 | `SBERT` |
| `WORKER_URLS` | GPU Worker URL | `http://gpu-worker:8090` |
| `REDIS_HOST` | Redis 主机 | `localhost` |
| `REDIS_PORT` | Redis 端口 | `6379` |
| `MILVUS_HOST` | Milvus 主机 | `milvus-standalone` |
| `MILVUS_PORT` | Milvus 端口 | `19530` |
| `OBS_ENABLED` | 可观测性开关 | `0` |
| `LANGFUSE_HOST` | Langfuse 主机 | N/A |
| `LANGFUSE_PUBLIC_KEY` | Langfuse 公钥 | N/A |
| `LANGFUSE_SECRET_KEY` | Langfuse 密钥 | N/A |
| `AUTOTUNER_TOKENS` | AutoTuner 认证令牌 | N/A |
| `AUTOTUNER_RPS` | AutoTuner 速率限制 | `0` |

#### 配置文件

- `.env.current` - 当前活跃配置（单一真源）
- `.env.local` - 本地开发配置
- `.env.remote.template` - 远程环境模板

---

## 6️⃣ 已完成 vs 未完成

### ✅ DONE（已完成）

#### 核心功能
- ✅ RAG 检索管道（向量检索、重排序、查询改写）
- ✅ AutoTuner 自动调参（决策引擎、记忆系统、约束验证）
- ✅ 检索代理（Go 语言实现）
- ✅ GPU Worker（CUDA 加速）
- ✅ Code Lookup Agent（代码图谱分析）
- ✅ 向量数据库集成（Qdrant、Milvus、FAISS）
- ✅ 混合检索（向量 + BM25）
- ✅ PageIndex 分层检索
- ✅ CAG 缓存系统

#### 评估与测试
- ✅ A/B 测试框架
- ✅ 成对评估
- ✅ 指标分析
- ✅ Black Swan 压力测试
- ✅ 单元测试套件（98+ 用例）

#### 运维与监控
- ✅ 健康检查端点
- ✅ 可观测性集成（LangSmith、Langfuse）
- ✅ Prometheus/Grafana 配置
- ✅ 环境切换工具（本地/远程）
- ✅ SLA 检查与自动回滚

#### 前端
- ✅ React + Vite 应用
- ✅ 查询控制台
- ✅ Metrics Hub（指标面板）
- ✅ JobHunter 页面
- ✅ Code Lookup 可视化

#### 基础设施
- ✅ Docker Compose 编排
- ✅ Kubernetes 部署清单
- ✅ Makefile 自动化
- ✅ CI/CD 流程

---

### ❌ NOT DONE / 不明确（未完成或占位）

#### 部分实现
- 🟡 LabOps Agent（V3 运行器已实现，但部分功能待完善）
- 🟡 JobHunter（核心功能已实现，但前端集成待完善）
- 🟡 E-commerce Agent（基础功能已实现，但生产就绪度待评估）

#### 占位/计划中
- ❓ 多语言支持（TypeScript、Go、Java 等代码分析）
- ❓ CI/CD 集成（GitHub Actions、GitLab CI）
- ❓ 团队协作功能（多用户、分享）
- ❓ 插件系统（自定义分析插件）
- ❓ 企业级部署（权限管理、私有化部署）

#### 文档/测试
- 🟡 部分模块缺少完整文档
- 🟡 部分实验脚本缺少使用说明
- 🟡 部分 API 端点缺少 OpenAPI 文档

#### 已知限制
- ⚠️ Code Lookup Agent 依赖静态代码图谱（需手动构建）
- ⚠️ GPU Worker 需要显式启用（默认 CPU 模式）
- ⚠️ 部分功能需要外部服务（OpenAI API、LangSmith）

---

## 7️⃣ 关键发现

### 架构特点
1. **微服务架构**：RAG API、GPU Worker、检索代理分离部署
2. **模块化设计**：功能模块高度解耦，易于扩展
3. **多后端支持**：向量数据库支持 Qdrant、Milvus、FAISS
4. **优雅降级**：GPU 不可用时回退 CPU，Redis 不可用时使用内存

### 技术栈
- **后端**：FastAPI + Python 3.11
- **前端**：React + Vite + TypeScript
- **向量数据库**：Qdrant（主）、Milvus（备）
- **缓存**：Redis（可选）
- **LLM**：OpenAI GPT-4o-mini
- **嵌入模型**：sentence-transformers/all-MiniLM-L6-v2
- **重排序**：cross-encoder/ms-marco-MiniLM-L-12-v2

### 数据流向
1. **查询** → 改写 → 检索 → 重排序 → 返回
2. **指标采集** → 决策 → 参数调整 → 配置更新
3. **代码查询** → 图谱查找 → 验证 → 解释生成

### 依赖关系
- **必需**：Qdrant、OpenAI API（可选，有降级）
- **可选**：Redis、GPU Worker、Milvus、LangSmith

---

## 8️⃣ 总结

SearchForge 是一个**功能完整**的 RAG 检索系统，核心功能（RAG、AutoTuner、检索代理）已实现并投入生产使用。系统采用微服务架构，支持多后端、优雅降级，具备完整的评估与监控能力。

**主要优势**：
- 核心功能完整且稳定
- 架构设计合理，易于扩展
- 测试覆盖充分
- 文档相对完善

**待完善项**：
- 部分 Agent 功能需要完善
- 部分实验脚本需要文档
- 企业级功能（权限、多租户）待开发

---

**报告结束**
