# JobHunter Graph Trace 工程视图实现总结

## 概述

在 JobHunter 页面上实现了一个最小可用的 graph trace 工程视图，用于展示 JD 分析过程中 LangGraph 节点的执行情况。该视图仅面向工程师使用，不影响普通用户的体验。

## 实现步骤

### Step 1: 勘查 Mortgage graph/trace 视图

**发现：**
- Mortgage Assistant 在 `MortgageAssistantPage.tsx` 中有一个 "Agent Steps" Tab
- 使用 `response.agent_steps` 数组展示步骤
- 每个步骤包含：`step_name`, `status`, `duration_ms`, `timestamp`, `inputs`, `outputs`, `error`
- 后端使用 `_record_step()` 函数手动记录每个步骤

**总结：**
- Mortgage graph view 使用 Table 组件展示步骤列表
- 数据来自 API 响应的 `agent_steps` 字段
- 数据结构：`List[AgentStep]`，每个 AgentStep 包含状态、耗时、输入输出等信息

### Step 2: 设计 JobHunter 最小 Graph Trace 视图

**设计决策：**
- 展示节点列表：`check_constraints`, `interpret_jd`, `lifecycle_reflection`, `spotlight_story`, `evidence_align`, `analyze_fit`
- 每个节点显示：节点名、状态（成功/失败）、耗时
- 放在 JobHunter 页面的 Tabs 中，新增 "Engineering" Tab
- 默认不激活，不影响普通用户

### Step 3: 后端数据准备

**实现：**
1. **schemas.py**: 
   - 添加 `GraphStep` 模型（包含 name, status, started_at, finished_at, duration_ms, extra_info）
   - 在 `JDAnalysisState` 中添加 `graph_steps: Optional[List[GraphStep]]` 字段

2. **jd_analysis_graph.py**:
   - 添加 `_record_graph_step()` 辅助函数
   - 在所有节点函数中添加步骤追踪：
     - `node_check_constraints`
     - `node_interpret_jd`
     - `node_lifecycle_reflection` (包装器)
     - `node_spotlight_story` (包装器)
     - `node_attach_evidence`
     - `node_analyze_fit`
   - 在 `run_jd_analysis()` 中初始化 `graph_steps` 列表并确保返回

3. **routes/jobhunter.py**:
   - 在 `JDAnalysisResponse` 中添加 `graph_steps: Optional[List[dict]]` 字段
   - 在 `analyze_jd()` 函数中提取并返回 `graph_steps`

### Step 4: 前端集成

**实现：**
1. **JobHunterPage.tsx**:
   - 添加 `GraphStep` 接口定义
   - 在 `JDAnalysisResponse` 接口中添加 `graph_steps?: GraphStep[]` 字段
   - 在 Tabs 组件中添加 "Engineering" Tab
   - 使用 List 组件展示 graph steps，包括：
     - 节点名（monospace 字体）
     - 状态标签（success/error/processing）
     - 耗时（格式化显示）
     - 开始时间
     - 额外信息（如果有）

## 文件改动清单

### 后端文件
- `services/fiqa_api/jobhunter/schemas.py`: 添加 GraphStep 模型和 JDAnalysisState.graph_steps
- `services/fiqa_api/jobhunter/graphs/jd_analysis_graph.py`: 添加步骤追踪逻辑
- `services/fiqa_api/routes/jobhunter.py`: 更新 API 响应模型

### 前端文件
- `ui/src/pages/JobHunterPage.tsx`: 添加 Engineering Tab 和 graph trace 展示

## 使用方式

1. 在 JobHunter 页面输入 JD 描述
2. 点击 "Analyze JD" 按钮
3. 分析完成后，点击右侧栏的 "Engineering" Tab
4. 查看 graph trace，包括：
   - 每个节点的执行顺序
   - 节点状态（completed/failed/in_progress）
   - 每个节点的耗时
   - 开始和结束时间戳
   - 额外信息（如果有错误或跳过原因）

## 当前展示内容

JobHunter graph trace 目前展示了：
- **节点列表**：按执行顺序展示所有 LangGraph 节点
- **状态信息**：每个节点的执行状态（成功/失败/进行中）
- **耗时统计**：每个节点的执行时间（毫秒或秒）
- **时间戳**：节点开始执行的时间

## 未来可扩展功能

1. **链接到 LangSmith**：添加 LangSmith trace URL 链接，方便查看详细的 trace 信息
2. **更详细的 timing 信息**：展示节点之间的等待时间、总耗时等
3. **可视化 graph 执行流程**：使用图形库（如 D3、dagre）展示节点之间的连接关系
4. **节点输入输出预览**：类似 Mortgage 的 expandable row，展示节点的输入输出（需要控制数据大小）
5. **性能分析**：识别最耗时的节点，提供优化建议

## 注意事项

- 所有新增字段都是可选的，保持向后兼容
- 工程视图默认不激活，不影响普通用户
- 步骤追踪对性能影响很小（仅记录元数据）
- 如果 graph_steps 为空或不存在，会显示友好的提示信息

## 测试建议

1. 运行后端：`make dev-api`（或相应的启动命令）
2. 运行前端：`make ui`
3. 在浏览器打开 `/jobhunter`
4. 粘贴一个 JD，点击 "Analyze JD"
5. 确认：
   - 正常看到 Summary / Fit Analysis
   - 点击 "Engineering" Tab 能看到节点列表
   - 每个节点显示正确的状态和耗时
