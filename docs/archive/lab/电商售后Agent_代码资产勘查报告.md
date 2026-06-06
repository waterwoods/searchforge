# 电商售后 Agent 代码资产勘查报告

> **Phase 0 勘查结果** - 为新电商售后客服 Agent 项目盘点可复用组件

---

## 一、现有 AI Agent / Workflow 清单

### 1.1 Mortgage Assistant（房贷助手）

**位置**: `services/fiqa_api/mortgage/`

**核心文件**:
- `graphs/single_home_graph.py` - LangGraph 工作流（StateGraph）
- `mortgage_agent_runtime.py` - 核心运行时逻辑
- `nl_to_stress_request.py` - 自然语言到结构化请求的转换
- `schemas.py` - Pydantic 数据模型（请求/响应）
- `tools/rates_tool.py` - 利率查询工具示例
- `demo_scenarios.py` - 演示场景数据

**工作流特点**:
- 使用 LangGraph `StateGraph` 编排多步骤流程
- 节点：`stress_check` → `safety_upgrade` → `mortgage_programs` → `strategy_lab` → `llm_explanation`
- 条件路由：根据 `stress_band` 决定是否执行 `safety_upgrade`
- 支持自然语言输入（NLU）和结构化输入
- 集成 MCP Server 调用外部服务（房贷项目查询）

**场景**: 房贷压力测试、风险评估、方案推荐

---

### 1.2 Ops Copilot（运维/SRE 辅助）

**位置**: `services/fiqa_api/ops_copilot/`

**核心文件**:
- `graphs/system_health_graph.py` - LangGraph 系统健康检查工作流
- `react_planner.py` - ReAct 风格规划器（LLM 决策工具调用）
- `tools.py` - 工具注册表（health_check, safety_upgrade, strategy_lab）
- `ops_runtime.py` - 核心运行时逻辑
- `ops_rag_retriever.py` - RAG 检索器（查询运维知识库）
- `semantic_tools.py` - 语义工具（日志查询、runbook、事件摘要）
- `schemas.py` - 数据模型
- `input_validation.py` - 输入验证

**工作流特点**:
- LangGraph 工作流：`health_check` → `safety_upgrade` → `strategy_lab` → `rag_context` → `action_plan` → `llm_explanation`
- ReAct Planner：LLM 决策下一步工具调用（max 3 steps）
- 工具层：标准化的工具注册表（`TOOL_REGISTRY`）
- RAG 集成：从 `ops_kb` 向量库检索相关知识
- 语义工具：查询日志、获取 runbook、总结事件

**场景**: 系统健康检查、故障诊断、配置优化建议

---

### 1.3 LabOps Agent（实验编排 Agent）

**位置**: `agents/labops/`

**核心文件**:
- `agent_runner.py` (V1) - 规则基础版本
- `v2/agent_runner_v2.py` - 带规则解释器
- `v3/runner_v3.py` - LLM 解释器 + 代码导航
- `tools/ops_client.py` - API 客户端
- `policies/decision.py` - 决策规则引擎

**工作流特点**:
- 流程：`Plan → Execute → Judge → Apply → Report`
- 无 LangGraph，纯 Python 类实现
- 决策引擎：基于规则的 PASS/EDGE/FAIL 判断
- 历史记录：JSONL 格式的不可变审计日志

**场景**: 自动化实验编排、性能测试决策

---

### 1.4 Code Graph Agent（代码分析 Agent）

**位置**: `services/fiqa_api/agent/`

**核心文件**:
- `router.py` - 路由分类器
- `planner.py` - 计划生成器
- `executor.py` - 执行器（调用工具）
- `judge.py` - 结果验证器（证据完整性检查）
- `vibe_validator.py` - Vibe Coding 验证器

**工作流特点**:
- 架构：Router → Planner → Executor → Judge
- 工具：`CodeGraph` 工具（代码图查询）
- 验证：Judge 检查证据字段（file, span, snippet）

**场景**: 代码库查询、函数依赖分析

---

## 二、可复用骨干模块

### 2.1 工作流 / Graph

#### ✅ **LangGraph StateGraph 模板**

**文件**: 
- `services/fiqa_api/mortgage/graphs/single_home_graph.py`
- `services/fiqa_api/ops_copilot/graphs/system_health_graph.py`

**复用建议**: **几乎可直接复用结构**

**关键模式**:
```python
# 1. 定义 TypedDict State
class GraphState(TypedDict, total=False):
    request: RequestModel
    intermediate_result: Optional[Result]
    agent_steps: List[AgentStep]
    errors: List[str]

# 2. 定义节点函数
def _node_function(state: GraphState) -> Dict[str, Any]:
    # 执行逻辑，返回状态更新
    return {"intermediate_result": result}

# 3. 定义条件路由
def _router_function(state: GraphState) -> str:
    # 返回下一个节点名称
    return "next_node"

# 4. 构建图
graph = StateGraph(GraphState)
graph.add_node("node1", _node_function)
graph.add_conditional_edges("node1", _router_function, {"path1": "node2", "path2": END})
graph.set_entry_point("node1")
compiled = graph.compile()
```

**电商改造**:
- State 改为：`order_id`, `conversation_history`, `intent_classification`, `order_query_result`, `refund_calculation`, `rag_context`, `action_plan`
- 节点：`classify_intent` → `query_order` → `calculate_compensation` → `retrieve_policy` → `create_ticket` → `generate_response`

---

#### ✅ **ReAct Planner 模式**

**文件**: `services/fiqa_api/ops_copilot/react_planner.py`

**复用建议**: **需要改动少量字段**

**关键模式**:
- LLM 决策下一步工具调用（JSON 格式：`{"tool": "...", "reason": "..."}`）
- 工具注册表（`TOOL_REGISTRY`）管理可用工具
- 优雅降级：LLM 失败时回退到确定性流程
- 最大步数限制（max_steps=3）

**电商改造**:
- 工具改为：`query_order`, `calculate_refund`, `check_return_policy`, `create_return_ticket`, `create_refund_ticket`, `escalate_to_human`
- LLM Prompt 改为电商场景（订单、售后规则）

---

### 2.2 工具（Tools）

#### ✅ **工具注册表模式**

**文件**: `services/fiqa_api/ops_copilot/tools.py`

**复用建议**: **几乎可直接复用结构**

**关键模式**:
```python
@dataclass
class Tool:
    name: str
    description: str
    callable: Callable
    allowed_in_bands: Optional[List[str]] = None

TOOL_REGISTRY: Dict[str, Tool] = {
    "tool_name": Tool(
        name="tool_name",
        description="...",
        callable=tool_function,
    ),
}

def tool_function(input: InputModel) -> OutputModel:
    """工具函数，包含清晰的文档说明何时使用/不使用"""
    return result
```

**电商改造**:
- 定义工具：`query_order`, `calculate_refund_amount`, `check_return_eligibility`, `create_return_request`, `create_refund_request`, `escalate_case`
- 每个工具返回结构化结果（Pydantic 模型）

---

#### ✅ **工具示例：利率查询**

**文件**: `services/fiqa_api/mortgage/tools/rates_tool.py`

**复用建议**: **仅能参考结构**

**关键模式**:
- Mock 数据实现（可替换为真实 API）
- 状态/类型参数化查询
- 清晰的函数文档

**电商改造**:
- 创建 `order_tool.py`: `query_order_by_id(order_id)`, `get_order_status(order_id)`
- 创建 `refund_tool.py`: `calculate_refund_amount(order_id, items)`, `check_refund_policy(order_id)`
- 创建 `ticket_tool.py`: `create_return_ticket(order_id, reason)`, `create_refund_ticket(order_id, amount)`

---

### 2.3 RAG（检索增强生成）

#### ✅ **向量检索器**

**文件**: 
- `services/fiqa_api/ops_copilot/ops_rag_retriever.py`
- `modules/search/vector_search.py`
- `modules/rag/page_index.py`

**复用建议**: **几乎可直接复用**

**关键组件**:
1. **VectorSearch 类** (`modules/search/vector_search.py`)
   - 使用 Qdrant 作为向量库
   - SentenceTransformer 做 embedding
   - 支持 metadata 过滤

2. **RAG Retriever 封装** (`ops_rag_retriever.py`)
   - 查询构建（service_name + symptom）
   - 结果格式化（text, score, source_file, metadata）
   - 优雅降级（Qdrant 不可用时返回空列表）

**电商改造**:
- 创建 `ecommerce_rag_retriever.py`
- 查询构建：`order_id` + `issue_type`（退货/退款/换货）
- 知识库集合：`ecommerce_kb`（包含退货政策、FAQ、处理流程）
- 检索策略：先检索订单相关文档，再检索通用政策

---

#### ✅ **RAG Pipeline**

**文件**: `pipeline/rag_pipeline.py`

**复用建议**: **需要改动少量字段**

**关键功能**:
- 查询改写（Query Rewriter）
- 向量搜索 + BM25 混合检索
- Reranker（可选）
- 缓存（CAG Cache）

**电商改造**:
- 配置改为电商知识库集合名
- 查询改写 prompt 改为电商场景
- 保持混合检索和缓存机制

---

#### ✅ **知识库索引构建**

**文件**: 
- `experiments/build_ops_kb_index.py`
- `services/fiqa_api/ops_copilot/ops_rag_index.py`

**复用建议**: **需要改动少量字段**

**关键模式**:
- 从 Markdown 文件加载文档
- 分块（chunking）
- 提取 metadata（service_hint, symptom_hint）
- 向量化并写入 Qdrant

**电商改造**:
- 创建 `build_ecommerce_kb_index.py`
- 输入：`knowledge_base/ecommerce/` 目录下的 Markdown 文件
- Metadata：`order_type`, `issue_type`, `policy_type`
- 输出：`ecommerce_kb` 集合

---

### 2.4 评估 / Guardrail

#### ✅ **输入验证**

**文件**: 
- `services/fiqa_api/ops_copilot/input_validation.py`
- `services/fiqa_api/mortgage/input_validation.py`

**复用建议**: **几乎可直接复用结构**

**关键模式**:
- 硬错误检查（负数、超出范围、空值）
- 返回错误列表（空列表 = 通过）
- Pydantic 模型验证

**电商改造**:
- 创建 `ecommerce_input_validation.py`
- 验证：`order_id` 格式、`refund_amount` 范围、`return_reason` 枚举值

---

#### ✅ **Judge / 结果验证器**

**文件**: `services/fiqa_api/agent/judge.py`

**复用建议**: **仅能参考结构**

**关键模式**:
- 证据完整性检查（required fields: file, span, snippet）
- Vibe Coding 验证器（启发式评分）
- 返回 verdict: "pass" / "revise" / "fail"

**电商改造**:
- 创建 `ecommerce_judge.py`
- 验证：订单查询结果完整性、退款计算合理性、工单创建成功
- 证据字段改为：`order_data`, `calculation_details`, `ticket_id`

---

#### ✅ **离线评估脚本**

**文件**: 
- `experiments/offline_ops_agent_eval.py`
- `experiments/offline_ops_rag_eval.py`
- `experiments/ops_copilot_llm_eval.py`

**复用建议**: **需要改动少量字段**

**关键模式**:
- 合成数据生成（realistic distributions）
- 批量运行 Agent
- 统计指标计算（准确率、召回率、F1）
- 无 LLM 调用（纯 Python，快速）

**电商改造**:
- 创建 `offline_ecommerce_agent_eval.py`
- 合成数据：订单状态分布、问题类型分布、对话历史
- 指标：意图分类准确率、退款计算准确率、工单创建成功率

---

#### ✅ **Guardrails 框架**

**文件**: 
- `services/guardrails/__init__.py`
- `modules/demo_pack/guardrails.py`
- `services/black_swan/guards.py`

**复用建议**: **仅能参考结构**

**当前状态**:
- 大部分是 no-op 实现（占位符）
- `demo_pack/guardrails.py` 有实际规则（参数范围检查）

**电商改造**:
- 创建 `ecommerce_guardrails.py`
- 规则：退款金额不能超过订单总额、退货时间窗口检查、重复退款检测

---

### 2.5 数据模型 / Schemas

#### ✅ **Pydantic 模型模板**

**文件**: 
- `services/fiqa_api/mortgage/schemas.py`
- `services/fiqa_api/ops_copilot/schemas.py`

**复用建议**: **几乎可直接复用结构**

**关键模式**:
- Request/Response 模型分离
- AgentStep 追踪（step_id, status, timestamp, duration_ms）
- 嵌套模型（中间结果、最终输出）

**电商改造**:
```python
class EcommerceAgentRequest(BaseModel):
    order_id: str
    conversation_history: List[Dict[str, str]]
    user_message: str

class OrderQueryResult(BaseModel):
    order_id: str
    status: str
    items: List[OrderItem]
    total_amount: float
    created_at: datetime

class RefundCalculation(BaseModel):
    eligible_amount: float
    reason: str
    policy_reference: str

class EcommerceAgentResponse(BaseModel):
    intent: str  # return/refund/exchange/replace
    order_info: OrderQueryResult
    refund_calculation: Optional[RefundCalculation]
    ticket_id: Optional[str]
    agent_steps: List[AgentStep]
    narrative: Optional[str]
```

---

## 三、现有数据与配置

### 3.1 演示场景数据

#### ✅ **Mortgage Demo Scenarios**

**文件**: `services/fiqa_api/mortgage/demo_scenarios.py`

**内容**:
- 3-4 个高度区分的场景预设
- 每个场景包含：请求参数、期望结果、预期路径

**电商改造**:
- 创建 `ecommerce_demo_scenarios.py`
- 场景：
  1. **退货场景**：订单已收货，7 天内，商品完好
  2. **退款场景**：订单未发货，用户取消
  3. **换货场景**：商品有质量问题，用户要求换货
  4. **补寄场景**：商品丢失，用户要求补寄

---

### 3.2 知识库文档

#### ✅ **Ops Knowledge Base**

**位置**: `knowledge_base/`

**文件**:
- `runbooks.md` - 运维手册（症状检测、诊断步骤、修复操作）
- `incidents.md` - 事件记录
- `configs.md` - 配置说明
- `lessons_learned.md` - 经验总结

**格式**:
- Markdown 格式
- Metadata 标签：`[service=...][symptom=...]`
- 结构化内容：症状检测、步骤、操作

**电商改造**:
- 创建 `knowledge_base/ecommerce/` 目录
- 文件：
  - `return_policy.md` - 退货政策（时间窗口、条件、流程）
  - `refund_policy.md` - 退款政策（金额计算、到账时间）
  - `exchange_policy.md` - 换货政策
  - `faq.md` - 常见问题
  - `order_status_guide.md` - 订单状态说明

---

### 3.3 评估数据

#### ✅ **合成数据生成器**

**文件**: `experiments/offline_ops_agent_eval.py`

**内容**:
- 合成系统快照生成器（realistic distributions）
- 场景类型分布（healthy_like, cpu_bound, latency_spike 等）

**电商改造**:
- 创建 `generate_ecommerce_test_data.py`
- 生成：
  - 订单数据（不同状态、金额、时间）
  - 对话历史（不同意图、长度）
  - 问题类型分布（退货 40%、退款 30%、换货 20%、补寄 10%）

---

### 3.4 配置示例

#### ✅ **YAML 配置文件**

**位置**: `configs/`

**示例**:
- `demo_*.yaml` - 各种演示配置
- `presets/*.yaml` - 预设配置

**电商改造**:
- 创建 `configs/demo_ecommerce_agent.yaml`
- 配置项：
  - RAG 集合名：`ecommerce_kb`
  - 工具列表
  - LLM 模型选择
  - 最大步数

---

## 四、新电商 Agent 的缺口 & 下一步建议

### 4.1 最高优先级缺口

#### 🔴 **缺口 1: 订单 Schema + 核心工具**

**现状**: 
- 有工具注册表模式（`ops_copilot/tools.py`）
- 有工具示例（`mortgage/tools/rates_tool.py`）
- **缺少**：订单查询、退款计算、工单创建工具

**建议**:
1. 创建 `services/fiqa_api/ecommerce/tools/` 目录
2. 实现工具：
   - `order_tool.py`: `query_order(order_id)`, `get_order_status(order_id)`
   - `refund_tool.py`: `calculate_refund_amount(order_id, items, reason)`, `check_refund_eligibility(order_id)`
   - `ticket_tool.py`: `create_return_ticket(order_id, items, reason)`, `create_refund_ticket(order_id, amount)`
3. 定义订单 Schema（Pydantic 模型）：
   - `Order`, `OrderItem`, `OrderStatus`
   - `RefundCalculation`, `ReturnRequest`

**优先级**: ⭐⭐⭐⭐⭐

---

#### 🔴 **缺口 2: 电商知识库（RAG 文档）**

**现状**:
- 有 RAG 检索器（`ops_rag_retriever.py`）
- 有知识库索引构建脚本（`build_ops_kb_index.py`）
- 有知识库文档示例（`knowledge_base/runbooks.md`）
- **缺少**：电商退货/退款政策文档

**建议**:
1. 创建 `knowledge_base/ecommerce/` 目录
2. 编写 Markdown 文档：
   - `return_policy.md` - 退货政策（7 天无理由、15 天质量问题等）
   - `refund_policy.md` - 退款政策（金额计算、到账时间）
   - `exchange_policy.md` - 换货政策
   - `faq.md` - 常见问题（"退货多久到账？"、"换货需要运费吗？"）
3. 创建索引构建脚本：`experiments/build_ecommerce_kb_index.py`
4. 创建检索器：`services/fiqa_api/ecommerce/ecommerce_rag_retriever.py`

**优先级**: ⭐⭐⭐⭐⭐

---

#### 🔴 **缺口 3: 电商 Agent LangGraph 工作流**

**现状**:
- 有 LangGraph 模板（`single_home_graph.py`, `system_health_graph.py`）
- 有 ReAct Planner（`react_planner.py`）
- **缺少**：电商场景的图定义

**建议**:
1. 创建 `services/fiqa_api/ecommerce/graphs/ecommerce_agent_graph.py`
2. 定义 State：
   ```python
   class EcommerceAgentState(TypedDict, total=False):
       request: EcommerceAgentRequest
       intent: Optional[str]
       order_info: Optional[OrderQueryResult]
       refund_calculation: Optional[RefundCalculation]
       rag_context: Optional[List[RagSnippet]]
       ticket_id: Optional[str]
       agent_steps: List[AgentStep]
   ```
3. 定义节点：
   - `classify_intent` - 意图分类（退货/退款/换货/补寄）
   - `query_order` - 查询订单信息
   - `calculate_compensation` - 计算退款/补偿金额
   - `retrieve_policy` - RAG 检索政策文档
   - `create_ticket` - 创建工单
   - `generate_response` - LLM 生成回复
4. 条件路由：根据意图和订单状态决定路径

**优先级**: ⭐⭐⭐⭐⭐

---

#### 🟡 **缺口 4: 意图分类与 NLU**

**现状**:
- 有 NLU 示例（`mortgage/nl_to_stress_request.py`）
- **缺少**：电商场景的意图分类器

**建议**:
1. 创建 `services/fiqa_api/ecommerce/nl_to_intent.py`
2. 实现：
   - LLM-based 意图分类（退货/退款/换货/补寄/其他）
   - 实体提取（订单号、商品、原因）
   - 结构化输出（Pydantic 模型）
3. 可选：训练分类模型（如果数据充足）

**优先级**: ⭐⭐⭐⭐

---

#### 🟡 **缺口 5: 防幻觉 / 质量评估最小脚本**

**现状**:
- 有 Judge 验证器（`agent/judge.py`）
- 有离线评估脚本（`offline_ops_agent_eval.py`）
- **缺少**：电商场景的质量评估

**建议**:
1. 创建 `experiments/offline_ecommerce_agent_eval.py`
2. 评估维度：
   - 意图分类准确率
   - 订单查询正确性
   - 退款计算准确性（与标准答案对比）
   - 工单创建成功率
   - LLM 回复相关性（可选：LLM-as-judge）
3. 创建 `services/fiqa_api/ecommerce/ecommerce_judge.py`
   - 验证订单数据完整性
   - 验证退款计算合理性（金额 ≤ 订单总额）
   - 验证工单创建成功

**优先级**: ⭐⭐⭐⭐

---

### 4.2 次要优先级缺口

#### 🟢 **缺口 6: Guardrails 规则**

**建议**: 创建 `services/fiqa_api/ecommerce/guardrails.py`
- 规则：退款金额检查、时间窗口检查、重复操作检测

**优先级**: ⭐⭐⭐

---

#### 🟢 **缺口 7: 演示数据与测试用例**

**建议**: 
- 创建 `services/fiqa_api/ecommerce/demo_scenarios.py`（类似 mortgage）
- 创建 `experiments/ecommerce_agent_smoke.py`（冒烟测试）

**优先级**: ⭐⭐⭐

---

#### 🟢 **缺口 8: API 路由与集成**

**建议**:
- 创建 `services/fiqa_api/routes/ecommerce_agent.py`
- 集成到 `app_main.py`
- 定义 REST API 端点：`POST /api/ecommerce/agent`

**优先级**: ⭐⭐

---

## 五、复用优先级总结

### 可直接复用（几乎无需改动）

1. ✅ **LangGraph StateGraph 模板** - 直接复制结构，改 State 和节点
2. ✅ **工具注册表模式** - 直接复制，改工具名称和函数
3. ✅ **VectorSearch / RAG Retriever** - 直接使用，改集合名
4. ✅ **Pydantic Schema 模板** - 直接复制结构，改字段名
5. ✅ **输入验证模式** - 直接复制，改验证规则

### 需要改动少量字段

1. 🔧 **ReAct Planner** - 改工具列表和 LLM Prompt
2. 🔧 **RAG Pipeline** - 改集合名和查询改写 prompt
3. 🔧 **知识库索引构建** - 改输入目录和 metadata 提取
4. 🔧 **离线评估脚本** - 改数据生成器和评估指标

### 仅能参考结构

1. 📖 **Judge 验证器** - 参考证据检查模式，改验证字段
2. 📖 **Guardrails** - 参考规则定义模式，改具体规则
3. 📖 **NLU 模块** - 参考 mortgage 的 NLU，改意图分类逻辑

---

## 六、Phase 1 最小设计建议

### 6.1 最小可行产品（MVP）

**目标**: 实现一个能处理"退货"和"退款"两种意图的最小 Agent

**组件清单**:

1. **数据模型** (1-2 天)
   - `ecommerce/schemas.py` - 订单、退款、请求/响应模型
   - `ecommerce/demo_scenarios.py` - 2-3 个测试场景

2. **核心工具** (2-3 天)
   - `ecommerce/tools/order_tool.py` - Mock 订单查询
   - `ecommerce/tools/refund_tool.py` - 退款计算（简单规则）
   - `ecommerce/tools/ticket_tool.py` - Mock 工单创建

3. **RAG 知识库** (1-2 天)
   - `knowledge_base/ecommerce/return_policy.md` - 退货政策（1 页）
   - `knowledge_base/ecommerce/refund_policy.md` - 退款政策（1 页）
   - `experiments/build_ecommerce_kb_index.py` - 索引构建脚本

4. **LangGraph 工作流** (2-3 天)
   - `ecommerce/graphs/ecommerce_agent_graph.py` - 最小图（3-4 个节点）
   - 节点：`classify_intent` → `query_order` → `calculate_refund` → `retrieve_policy` → `generate_response`

5. **意图分类** (1-2 天)
   - `ecommerce/nl_to_intent.py` - LLM-based 意图分类（简单 prompt）

6. **API 集成** (1 天)
   - `routes/ecommerce_agent.py` - REST 端点
   - 集成到 `app_main.py`

**总计**: 约 8-13 天（1 人）

---

### 6.2 扩展功能（Phase 2+）

- 换货和补寄意图
- 真实订单系统集成（替换 Mock 工具）
- 更复杂的退款计算规则
- LLM-as-judge 质量评估
- 对话历史管理（多轮对话）
- Guardrails 规则完善

---

## 附录：关键文件路径速查

### LangGraph 工作流
- `services/fiqa_api/mortgage/graphs/single_home_graph.py`
- `services/fiqa_api/ops_copilot/graphs/system_health_graph.py`

### 工具定义
- `services/fiqa_api/ops_copilot/tools.py`
- `services/fiqa_api/mortgage/tools/rates_tool.py`

### RAG
- `services/fiqa_api/ops_copilot/ops_rag_retriever.py`
- `modules/search/vector_search.py`
- `pipeline/rag_pipeline.py`

### 评估
- `experiments/offline_ops_agent_eval.py`
- `services/fiqa_api/agent/judge.py`

### 数据模型
- `services/fiqa_api/mortgage/schemas.py`
- `services/fiqa_api/ops_copilot/schemas.py`

### 知识库
- `knowledge_base/runbooks.md`
- `experiments/build_ops_kb_index.py`

---

**报告生成时间**: 2024-01-XX  
**勘查范围**: 全代码库（LangChain/LangGraph/Agent/RAG/Eval/Guardrail）  
**下一步**: 根据此报告制定 Phase 1 详细设计文档
